"""
core/jd_ranker.py
------------------
Job-Description-aware ranking of CV bullets.

Given a pasted job description and the user's bullet inventory (i.e.
``user_config.job_positions()``) this module returns:

1. A ranked list of bullets with relevance score in [0.0, 1.0].
2. An overall *fit score* — a single number that says "how well does
   your inventory cover what this JD asks for?".

Four scoring backends are supported, all chosen via ``user_config.llm``::

    "provider": "local"               (default — pure-Python TF-IDF, no deps)
    "provider": "sentence_transformers" (local embeddings, pip install)
    "provider": "ollama"              (local LLM server on localhost:11434)
    "provider": "openai"              (paid cloud — opt-in only)

Crucially, the first three are **fully local**. The ``sentence_transformers``
and ``ollama`` paths exist precisely so the ranker can use a real
embedding model without giving up ApplyCraft's local-first promise. No
data leaves the user's machine.

If a configured backend is unavailable (e.g. sentence-transformers not
installed, Ollama not running), the module gracefully falls back to the
pure-Python ranker and logs a warning. The app keeps working.

Public API
~~~~~~~~~~

>>> from core.jd_ranker import rank_bullets, compute_fit_score
>>> ranked = rank_bullets(jd_text)
>>> fit = compute_fit_score(jd_text, ranked)
>>> fit["fit_score"], fit["strong_matches"], fit["backend"]

"""

from __future__ import annotations

import math
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

# Path bootstrap for ``helpers.user_config``.
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from helpers import user_config          # noqa: E402
from helpers.logger import logger        # noqa: E402


# --------------------------------------------------------------------------
# Stopwords + token utilities (used by the TF-IDF backend and by keyword-
# overlap signals on top of every backend).
# --------------------------------------------------------------------------

_STOPWORDS = frozenset("""
a about above after again against all am an and any are aren't as at be
because been before being below between both but by can can't cannot could
couldn't did didn't do does doesn't doing don't down during each few for
from further had hadn't has hasn't have haven't having he he'd he'll he's
her here here's hers herself him himself his how how's i i'd i'll i'm i've
if in into is isn't it it's its itself let's me more most mustn't my
myself no nor not of off on once only or other ought our ours ourselves
out over own same shan't she she'd she'll she's should shouldn't so some
such than that that's the their theirs them themselves then there there's
these they they'd they'll they're they've this those through to too under
until up very was wasn't we we'd we'll we're we've were weren't what
what's when when's where where's which while who who's whom why why's
with won't would wouldn't you you'd you'll you're you've your yours
yourself yourselves
also will may within across including via etc whilst per onto upon among
""".split())

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9\+\-#\.]*")


def _tokenize(text: str) -> List[str]:
    """Lowercase, keep alphanum + a few tech-stack-friendly chars (C#, .NET)."""
    return [tok.lower() for tok in _WORD_RE.findall(text or "")]


def _content_tokens(text: str) -> List[str]:
    """Tokenize and drop short / stop words."""
    return [t for t in _tokenize(text) if len(t) > 2 and t not in _STOPWORDS]


# --------------------------------------------------------------------------
# Result type
# --------------------------------------------------------------------------

@dataclass
class BulletScore:
    """A single bullet's relevance score against a JD.

    Attributes
    ----------
    job_title : str
        The job heading the bullet belongs to.
    bullet : str
        The bullet text itself.
    score : float
        Relevance score in [0.0, 1.0]. Higher is better.
    matched_keywords : list[str]
        JD content words that also appear in the bullet — used to explain
        the score in the UI.
    """
    job_title: str
    bullet: str
    score: float
    matched_keywords: List[str]


# --------------------------------------------------------------------------
# TF-IDF helpers (always available, no deps)
# --------------------------------------------------------------------------

def _build_tfidf(documents: List[List[str]]) -> Tuple[List[Dict[str, float]], Dict[str, float]]:
    n_docs = len(documents)
    if n_docs == 0:
        return [], {}
    df: Counter = Counter()
    for tokens in documents:
        for term in set(tokens):
            df[term] += 1
    idf: Dict[str, float] = {
        term: math.log((n_docs + 1) / (count + 1)) + 1.0
        for term, count in df.items()
    }
    vectors: List[Dict[str, float]] = []
    for tokens in documents:
        if not tokens:
            vectors.append({})
            continue
        tf = Counter(tokens)
        max_tf = max(tf.values())
        vec = {
            term: (0.5 + 0.5 * (count / max_tf)) * idf.get(term, 1.0)
            for term, count in tf.items()
        }
        vectors.append(vec)
    return vectors, idf


def _vectorise_query(tokens: Iterable[str], idf: Dict[str, float]) -> Dict[str, float]:
    tokens = list(tokens)
    if not tokens:
        return {}
    tf = Counter(tokens)
    max_tf = max(tf.values())
    return {
        term: (0.5 + 0.5 * (count / max_tf)) * idf.get(term, 1.0)
        for term, count in tf.items()
    }


def _cosine_sparse(a: Dict[str, float], b: Dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    if len(a) > len(b):
        a, b = b, a
    dot = sum(weight * b.get(term, 0.0) for term, weight in a.items())
    if dot == 0.0:
        return 0.0
    norm_a = math.sqrt(sum(w * w for w in a.values()))
    norm_b = math.sqrt(sum(w * w for w in b.values()))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def _cosine_dense(a: List[float], b: List[float]) -> float:
    if not a or not b:
        return 0.0
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (math.sqrt(na) * math.sqrt(nb))


# --------------------------------------------------------------------------
# Backend: pure-Python TF-IDF (default)
# --------------------------------------------------------------------------

def _local_rank(
    jd_text: str,
    flat: List[Tuple[str, str, List[str]]],
) -> List[BulletScore]:
    jd_tokens = _content_tokens(jd_text)
    if not jd_tokens or not flat:
        return []

    docs = [b_tokens for _, _, b_tokens in flat]
    vectors, idf = _build_tfidf(docs)
    jd_vector = _vectorise_query(jd_tokens, idf)
    jd_set = set(jd_tokens)

    results: List[BulletScore] = []
    for (job, bullet, b_tokens), vec in zip(flat, vectors):
        cosine = _cosine_sparse(jd_vector, vec)
        b_set = set(b_tokens)
        overlap = len(jd_set & b_set)
        coverage = overlap / max(len(b_set), 1)
        # Blend cosine and coverage. Cosine rewards rare-term hits;
        # coverage rewards bullets that touch many JD themes.
        score = 0.65 * cosine + 0.35 * coverage
        score = max(0.0, min(1.0, score))
        matched_sorted = sorted(jd_set & b_set, key=lambda t: -idf.get(t, 1.0))
        results.append(BulletScore(job, bullet, score, matched_sorted[:10]))

    results.sort(key=lambda r: r.score, reverse=True)
    return results


# --------------------------------------------------------------------------
# Backend: sentence-transformers (local embeddings)
# --------------------------------------------------------------------------
# Uses the user's chosen model (default: all-MiniLM-L6-v2, ~80 MB).
# Runs entirely on-device; first run downloads weights into the user's HF
# cache (~/.cache/huggingface), subsequent runs are instant.

_st_model_cache: Dict[str, Any] = {}


def _load_sentence_transformer(model_name: str):
    """Lazy-load and cache a sentence-transformers model.

    Returns ``None`` if the package isn't installed.
    """
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
    except Exception as e:
        logger.warning(
            "sentence-transformers not installed. Install with "
            "`pip install sentence-transformers` to enable local-embedding "
            f"ranking. ({e})"
        )
        return None

    if model_name in _st_model_cache:
        return _st_model_cache[model_name]
    try:
        model = SentenceTransformer(model_name)
    except Exception as e:
        logger.warning(f"Failed to load sentence-transformer '{model_name}': {e}")
        return None
    _st_model_cache[model_name] = model
    return model


def _rank_with_sentence_transformers(
    jd_text: str,
    flat: List[Tuple[str, str, List[str]]],
    model_name: str,
) -> Optional[List[BulletScore]]:
    model = _load_sentence_transformer(model_name or "all-MiniLM-L6-v2")
    if model is None:
        return None

    try:
        texts = [jd_text] + [bullet for _, bullet, _ in flat]
        embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    except Exception as e:
        logger.warning(f"sentence-transformers embed call failed: {e}")
        return None

    # `embeddings` is a numpy array; convert each row to a list.
    try:
        jd_vec = embeddings[0].tolist()
    except AttributeError:
        jd_vec = list(embeddings[0])

    jd_tokens = set(_content_tokens(jd_text))

    results: List[BulletScore] = []
    for (job, bullet, b_tokens), vec in zip(flat, embeddings[1:]):
        try:
            v = vec.tolist()
        except AttributeError:
            v = list(vec)
        # Normalised vectors -> dot product *is* cosine similarity, in [-1, 1].
        sim = _cosine_dense(jd_vec, v)
        sim_01 = (sim + 1.0) / 2.0
        matched = sorted(jd_tokens & set(b_tokens))[:10]
        results.append(BulletScore(job, bullet, sim_01, matched))

    results.sort(key=lambda r: r.score, reverse=True)
    return results


# --------------------------------------------------------------------------
# Backend: Ollama (local LLM server)
# --------------------------------------------------------------------------
# Ollama (https://ollama.com) is a popular way to run LLMs locally. It
# exposes an HTTP API on localhost:11434. We use the /api/embed endpoint
# for embedding-based ranking when the user has set
# ``llm.provider = "ollama"``. Default embedding model is
# nomic-embed-text — small (~270MB), fast, MIT licensed.

def _ollama_embed_batch(
    inputs: List[str],
    model: str,
    host: str,
) -> Optional[List[List[float]]]:
    """Call Ollama's /api/embed and return one vector per input.

    Returns ``None`` if Ollama is not reachable.
    """
    import json
    import urllib.request
    import urllib.error

    url = host.rstrip("/") + "/api/embed"
    body = json.dumps({"model": model, "input": inputs}).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        logger.warning(
            f"Ollama unreachable at {host} — is the daemon running? ({e}). "
            "Falling back to local TF-IDF."
        )
        return None
    except Exception as e:
        logger.warning(f"Ollama embedding call failed: {e}")
        return None

    vectors = payload.get("embeddings") or payload.get("data")
    if not vectors:
        logger.warning(f"Ollama returned no embeddings: {payload}")
        return None
    return vectors


def _rank_with_ollama(
    jd_text: str,
    flat: List[Tuple[str, str, List[str]]],
    model: str,
    host: str,
) -> Optional[List[BulletScore]]:
    if not flat:
        return []
    inputs = [jd_text] + [bullet for _, bullet, _ in flat]
    vectors = _ollama_embed_batch(inputs, model or "nomic-embed-text", host or "http://localhost:11434")
    if vectors is None or len(vectors) != len(inputs):
        return None

    jd_vec = vectors[0]
    jd_tokens = set(_content_tokens(jd_text))

    results: List[BulletScore] = []
    for (job, bullet, b_tokens), v in zip(flat, vectors[1:]):
        sim = _cosine_dense(jd_vec, v)
        # Ollama embeddings aren't guaranteed normalised; squash to [0,1].
        sim_01 = (sim + 1.0) / 2.0
        matched = sorted(jd_tokens & set(b_tokens))[:10]
        results.append(BulletScore(job, bullet, sim_01, matched))

    results.sort(key=lambda r: r.score, reverse=True)
    return results


# --------------------------------------------------------------------------
# Backend: OpenAI (opt-in, paid)
# --------------------------------------------------------------------------

def _rank_with_openai(
    jd_text: str,
    flat: List[Tuple[str, str, List[str]]],
    model: str,
    api_key: str,
) -> Optional[List[BulletScore]]:
    import json
    import urllib.request

    if not flat:
        return []
    inputs = [jd_text] + [bullet for _, bullet, _ in flat]
    body = json.dumps({
        "input": inputs,
        "model": model or "text-embedding-3-small",
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/embeddings", data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        logger.warning(f"OpenAI embedding call failed: {e}")
        return None

    data = payload.get("data") or []
    if len(data) != len(inputs):
        return None
    vectors = [item["embedding"] for item in data]

    jd_vec = vectors[0]
    jd_tokens = set(_content_tokens(jd_text))

    results: List[BulletScore] = []
    for (job, bullet, b_tokens), v in zip(flat, vectors[1:]):
        sim = _cosine_dense(jd_vec, v)
        sim_01 = (sim + 1.0) / 2.0
        matched = sorted(jd_tokens & set(b_tokens))[:10]
        results.append(BulletScore(job, bullet, sim_01, matched))

    results.sort(key=lambda r: r.score, reverse=True)
    return results


# --------------------------------------------------------------------------
# Backend selection
# --------------------------------------------------------------------------

def _resolve_backend(force_local: bool) -> Tuple[str, Dict[str, Any]]:
    """Decide which backend to try first based on user_config + ``force_local``."""
    if force_local:
        return "local", {}

    cfg = user_config.llm_config() or {}
    provider = (cfg.get("provider") or "local").lower()
    return provider, cfg


# --------------------------------------------------------------------------
# Public entry points
# --------------------------------------------------------------------------

# Stash which backend actually produced the most recent ranking, so the
# UI / fit-score function can label it. (Backends can be silently
# downgraded if e.g. sentence-transformers isn't installed.)
_LAST_BACKEND_USED = "local TF-IDF"


def rank_bullets(
    jd_text: str,
    inventory: Optional[Dict[str, List[str]]] = None,
    *,
    force_local: bool = False,
) -> List[BulletScore]:
    """Rank bullets against a JD using the configured backend.

    Parameters
    ----------
    jd_text : str
        Pasted job description.
    inventory : dict[str, list[str]], optional
        Job-title -> bullets. Defaults to ``user_config.job_positions()``.
    force_local : bool
        If True, skip every backend except the dependency-free TF-IDF
        ranker. Useful for tests and for the "Force local" UI toggle.
    """
    global _LAST_BACKEND_USED

    if inventory is None:
        inventory = user_config.job_positions() or {}
    if not jd_text or not jd_text.strip() or not inventory:
        _LAST_BACKEND_USED = "local TF-IDF"
        return []

    # Pre-tokenise the inventory once — every backend uses it for keyword
    # match annotations even when scoring with embeddings.
    flat: List[Tuple[str, str, List[str]]] = []
    for job, bullets in inventory.items():
        for bullet in bullets:
            flat.append((job, bullet, _content_tokens(bullet)))

    provider, cfg = _resolve_backend(force_local)

    if provider == "sentence_transformers":
        model = cfg.get("model") or "all-MiniLM-L6-v2"
        ranked = _rank_with_sentence_transformers(jd_text, flat, model)
        if ranked is not None:
            _LAST_BACKEND_USED = f"sentence-transformers ({model})"
            return ranked
        logger.info("sentence-transformers unavailable; falling back to local TF-IDF.")

    elif provider == "ollama":
        model = cfg.get("model") or "nomic-embed-text"
        host = cfg.get("host") or "http://localhost:11434"
        ranked = _rank_with_ollama(jd_text, flat, model, host)
        if ranked is not None:
            _LAST_BACKEND_USED = f"ollama ({model})"
            return ranked
        logger.info("Ollama unavailable; falling back to local TF-IDF.")

    elif provider == "openai":
        api_key = cfg.get("api_key") or ""
        model = cfg.get("model") or "text-embedding-3-small"
        if api_key:
            ranked = _rank_with_openai(jd_text, flat, model, api_key)
            if ranked is not None:
                _LAST_BACKEND_USED = f"openai ({model})"
                return ranked
        logger.info("OpenAI backend not usable; falling back to local TF-IDF.")

    _LAST_BACKEND_USED = "local TF-IDF"
    return _local_rank(jd_text, flat)


def compute_fit_score(
    jd_text: str,
    ranked: List[BulletScore],
    *,
    strong_threshold: float = 0.55,
) -> Dict[str, Any]:
    """Aggregate "how well does the user's inventory cover this JD?".

    Returns a dict with::

        {
          "fit_score": 0.62,        # 0..1
          "strong_matches": 4,      # bullets above ``strong_threshold``
          "considered": 25,         # total bullets ranked
          "keyword_coverage": 0.71, # share of JD keywords any bullet covers
          "backend": "ollama (nomic-embed-text)"
        }

    The score blends three signals:

    * **Best-bullet score** — how strong is your single best bullet?
    * **Top-N average** — how strong are your top 5 bullets on average?
    * **Keyword coverage** — what share of the JD's content words does
      *any* bullet in the inventory mention at least once?

    None of these alone is enough: a CV could have one great bullet but
    miss most of the JD themes (low coverage), or it could mention all
    the keywords shallowly (low semantic match).
    """
    if not ranked:
        return {
            "fit_score": 0.0,
            "strong_matches": 0,
            "considered": 0,
            "keyword_coverage": 0.0,
            "backend": _LAST_BACKEND_USED,
        }

    scores = [r.score for r in ranked]
    best = scores[0] if scores else 0.0
    top_n = scores[:5]
    top_avg = sum(top_n) / max(len(top_n), 1)
    strong = sum(1 for s in scores if s >= strong_threshold)

    jd_keywords = set(_content_tokens(jd_text))
    if jd_keywords:
        covered = set()
        for r in ranked:
            for kw in r.matched_keywords:
                covered.add(kw)
        keyword_coverage = len(covered) / len(jd_keywords)
    else:
        keyword_coverage = 0.0

    # Weighted aggregate. Best-bullet matters most (it's what the recruiter
    # actually sees at the top of the CV), top-N average smooths out
    # outliers, keyword coverage catches "did you address the role at all?".
    fit = 0.45 * best + 0.30 * top_avg + 0.25 * keyword_coverage
    fit = max(0.0, min(1.0, fit))

    return {
        "fit_score": fit,
        "strong_matches": strong,
        "considered": len(ranked),
        "keyword_coverage": keyword_coverage,
        "backend": _LAST_BACKEND_USED,
    }


def top_bullets_per_job(
    ranked: List[BulletScore],
    per_job_cap: int = 5,
) -> Dict[str, List[BulletScore]]:
    """Bucket the flat ranking by job, keeping the top N within each job."""
    buckets: Dict[str, List[BulletScore]] = {}
    for item in ranked:
        bucket = buckets.setdefault(item.job_title, [])
        if len(bucket) < per_job_cap:
            bucket.append(item)
    return buckets


# --------------------------------------------------------------------------
# Diagnostics — used by the GUI to show backend status / install hints
# --------------------------------------------------------------------------

def backend_status() -> Dict[str, Any]:
    """Probe the environment and report which backends are currently ready.

    Returns a dict like::

        {
          "configured": "sentence_transformers",
          "local_llm_installed": True,        # sentence-transformers importable
          "ollama_reachable": False,          # http://localhost:11434 responds
          "openai_key_set": False,
          "active": "sentence_transformers (all-MiniLM-L6-v2)"
                                              # the backend that will actually run
        }

    Used by the GUI to decide whether to show an "Install Local LLM" button
    and to tell the user up-front what's about to happen if they click
    "Rank Against JD".
    """
    cfg = user_config.llm_config() or {}
    configured = (cfg.get("provider") or "local").lower()

    # Probe sentence-transformers.
    local_llm_installed = False
    try:
        import importlib
        importlib.import_module("sentence_transformers")
        local_llm_installed = True
    except Exception:
        local_llm_installed = False

    # Probe Ollama.
    ollama_reachable = False
    try:
        import urllib.request
        host = (cfg.get("host") or "http://localhost:11434").rstrip("/")
        req = urllib.request.Request(host + "/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            ollama_reachable = resp.status == 200
    except Exception:
        ollama_reachable = False

    openai_key_set = bool(cfg.get("api_key"))

    # Decide which backend will actually run if the user clicks Rank now.
    if configured == "sentence_transformers" and local_llm_installed:
        active = f"sentence-transformers ({cfg.get('model') or 'all-MiniLM-L6-v2'})"
    elif configured == "ollama" and ollama_reachable:
        active = f"ollama ({cfg.get('model') or 'nomic-embed-text'})"
    elif configured == "openai" and openai_key_set:
        active = f"openai ({cfg.get('model') or 'text-embedding-3-small'})"
    else:
        active = "local TF-IDF (fallback)"

    return {
        "configured": configured,
        "local_llm_installed": local_llm_installed,
        "ollama_reachable": ollama_reachable,
        "openai_key_set": openai_key_set,
        "active": active,
    }


if __name__ == "__main__":
    # Tiny smoke test against the configured inventory.
    sample_jd = (
        "We are hiring a Data Analyst to build and maintain Power BI "
        "dashboards, work with stakeholders, automate ETL in Python and "
        "SQL, and improve data quality across the organisation."
    )
    inv = user_config.job_positions()
    if not inv:
        print("No bullets configured in user_config.json — nothing to rank.")
        sys.exit(0)

    ranked = rank_bullets(sample_jd, inv)
    fit = compute_fit_score(sample_jd, ranked)
    print(f"Backend used: {fit['backend']}")
    print(f"Overall fit:  {fit['fit_score']*100:.0f}%")
    print(f"Strong matches: {fit['strong_matches']} / {fit['considered']}\n")
    for r in ranked[:10]:
        print(f"  [{r.score*100:>3.0f}%] {r.job_title}")
        print(f"         {r.bullet}")
        if r.matched_keywords:
            print(f"         matched: {', '.join(r.matched_keywords)}")
        print()
