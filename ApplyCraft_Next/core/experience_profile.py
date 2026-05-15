import copy
import json
import os
import re
from typing import Dict, List, Tuple

from core.config import JOB_POSITIONS, SUMMARY_TEXT
from helpers.logger import logger

PROFILE_VERSION = 2
PROFILE_DIR = os.path.join(os.path.expanduser("~"), ".applycraft_next")
PROFILE_PATH = os.path.join(PROFILE_DIR, "profile.json")

DATE_PATTERN = re.compile(
    r"(?i)\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\b.*\d{2,4}"
    r"|\b\d{4}\s?[-\u2013\u2014]\s?(Present|\d{4}|\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b)"
    r"|^Present$|^\d{4}$"
)

BULLET_PREFIXES = ("-", "*", "\u2022", "\u00b7", "\u2023", "\u25e6")
DEFAULT_RELOCATION_VISA_LINE = (
    "EU citizen, no visa required to work in EU. Currently in Stockholm, willing to relocate."
)


def _split_legacy_job_title(job_title: str) -> Tuple[str, str]:
    if not job_title:
        return "", ""
    parts = re.split(r"\s+[^\w\s]+\s+", job_title, maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    for delimiter in (" - ", " | ", " \u2013 ", " \u2014 ", " : "):
        if delimiter in job_title:
            left, right = job_title.split(delimiter, 1)
            return left.strip(), right.strip()
    return job_title.strip(), ""


def _slugify(value: str) -> str:
    token = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return token or "experience"


def default_candidate_profile() -> Dict:
    return {
        "name": "Your Name",
        "email": "",
        "linkedin": "",
        "location": "",
        "relocation_visa_line": DEFAULT_RELOCATION_VISA_LINE,
        "show_relocation_visa_line": False,
    }


def _default_experience_entries() -> List[Dict]:
    entries: List[Dict] = []
    for index, (legacy_key, bullets) in enumerate(JOB_POSITIONS.items(), start=1):
        company, title = _split_legacy_job_title(legacy_key)
        anchor_key = f"exp_{index}_{_slugify(company)}"
        aliases = [company]
        short_company = company.split(",")[0].strip()
        if short_company and short_company != company:
            aliases.append(short_company)
        entries.append(
            {
                "anchor_key": anchor_key,
                "legacy_key": legacy_key,
                "company": company,
                "title": title,
                "date_range": "",
                "location": "",
                "headline": "",
                "aliases": aliases,
                "bullets": list(bullets),
                "include_in_cv": True,
            }
        )
    return entries


def default_profile() -> Dict:
    return {
        "profile_version": PROFILE_VERSION,
        "summary": SUMMARY_TEXT,
        "candidate": default_candidate_profile(),
        "experiences": _default_experience_entries(),
    }


def _normalize_candidate(raw_candidate: Dict) -> Dict:
    defaults = default_candidate_profile()
    candidate = raw_candidate if isinstance(raw_candidate, dict) else {}
    return {
        "name": str(candidate.get("name", defaults["name"])).strip() or defaults["name"],
        "email": str(candidate.get("email", defaults["email"])).strip(),
        "linkedin": str(candidate.get("linkedin", defaults["linkedin"])).strip(),
        "location": str(candidate.get("location", defaults["location"])).strip(),
        "relocation_visa_line": str(
            candidate.get("relocation_visa_line", defaults["relocation_visa_line"])
        ).strip()
        or defaults["relocation_visa_line"],
        "show_relocation_visa_line": bool(
            candidate.get("show_relocation_visa_line", defaults["show_relocation_visa_line"])
        ),
    }


def _ensure_aliases(entry: Dict) -> List[str]:
    aliases_raw = entry.get("aliases", [])
    aliases = [str(x).strip() for x in aliases_raw if str(x).strip()] if isinstance(aliases_raw, list) else []
    if aliases:
        return aliases

    company = str(entry.get("company", "")).strip()
    short_company = company.split(",")[0].strip() if company else ""
    generated = [company, short_company]
    deduped = []
    seen = set()
    for alias in generated:
        norm = normalize_for_match(alias)
        if norm and norm not in seen:
            seen.add(norm)
            deduped.append(alias)
    return deduped


def _migrate_legacy_profile(raw: Dict) -> Dict:
    if not isinstance(raw, dict):
        return default_profile()

    migrated = copy.deepcopy(raw)
    migrated["profile_version"] = PROFILE_VERSION
    migrated.setdefault("candidate", {})

    experiences = migrated.get("experiences")
    if isinstance(experiences, list):
        for entry in experiences:
            if not isinstance(entry, dict):
                continue
            entry.setdefault("date_range", "")
            entry.setdefault("location", "")
            entry.setdefault("headline", str(entry.get("headline", "")).strip())
            entry.setdefault("include_in_cv", True)
            entry["aliases"] = _ensure_aliases(entry)

    return migrated


def _ensure_profile_shape(profile: Dict) -> Dict:
    fallback = default_profile()
    if not isinstance(profile, dict):
        return fallback

    normalized = copy.deepcopy(profile)
    normalized["profile_version"] = PROFILE_VERSION
    normalized["summary"] = str(normalized.get("summary", fallback["summary"])).strip() or fallback["summary"]
    normalized["candidate"] = _normalize_candidate(normalized.get("candidate", {}))

    experiences = normalized.get("experiences")
    if not isinstance(experiences, list) or not experiences:
        normalized["experiences"] = fallback["experiences"]
        return normalized

    valid_entries: List[Dict] = []
    existing_anchors = set()
    for index, entry in enumerate(experiences, start=1):
        if not isinstance(entry, dict):
            continue

        company = str(entry.get("company", "")).strip()
        title = str(entry.get("title", "")).strip()
        date_range = str(entry.get("date_range", "")).strip()
        location = str(entry.get("location", "")).strip()
        aliases = _ensure_aliases(entry)
        bullets_raw = entry.get("bullets", [])
        bullets = [str(x).strip() for x in bullets_raw if str(x).strip()] if isinstance(bullets_raw, list) else []
        legacy_key = str(entry.get("legacy_key", "")).strip()
        anchor_key = str(entry.get("anchor_key", "")).strip()

        if not anchor_key:
            anchor_key = f"exp_{index}_{_slugify(company or title)}"
        if anchor_key in existing_anchors:
            anchor_key = f"{anchor_key}_{index}"
        existing_anchors.add(anchor_key)

        valid_entries.append(
            {
                "anchor_key": anchor_key,
                "legacy_key": legacy_key,
                "company": company,
                "title": title,
                "date_range": date_range,
                "location": location,
                "headline": str(entry.get("headline", "")).strip(),
                "aliases": aliases,
                "bullets": bullets,
                "include_in_cv": bool(entry.get("include_in_cv", True)),
            }
        )

    normalized["experiences"] = valid_entries or fallback["experiences"]
    return normalized


def get_profile_path() -> str:
    return PROFILE_PATH


def load_profile() -> Dict:
    path = get_profile_path()
    if not os.path.exists(path):
        profile = default_profile()
        save_profile(profile)
        return profile

    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except Exception as exc:
        logger.warning(f"Profile load failed, recreating defaults: {exc}")
        profile = default_profile()
        save_profile(profile)
        return profile

    migrated = _migrate_legacy_profile(raw)
    normalized = _ensure_profile_shape(migrated)
    if normalized != raw:
        save_profile(normalized)
    return normalized


def save_profile(profile: Dict) -> None:
    normalized = _ensure_profile_shape(profile)
    os.makedirs(PROFILE_DIR, exist_ok=True)
    with open(PROFILE_PATH, "w", encoding="utf-8") as handle:
        json.dump(normalized, handle, indent=2, ensure_ascii=False)


def normalize_for_match(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "", (value or "")).upper()


def build_entry_tokens(entry: Dict) -> List[str]:
    tokens = []
    for key in ("company", "title", "location"):
        text = str(entry.get(key, "")).strip()
        if text:
            tokens.append(text)

    aliases = entry.get("aliases", [])
    if isinstance(aliases, list):
        tokens.extend(str(alias).strip() for alias in aliases if str(alias).strip())

    unique = []
    seen = set()
    for token in tokens:
        norm = normalize_for_match(token)
        if norm and norm not in seen:
            seen.add(norm)
            unique.append(token)
    return unique


def auto_sort_experience_lines(raw_text: str, experiences: List[Dict]) -> Tuple[Dict[str, List[str]], List[str]]:
    lines = [line.strip() for line in (raw_text or "").splitlines() if line.strip()]
    if not lines:
        return {}, []

    matchers = []
    for entry in experiences:
        tokens = build_entry_tokens(entry)
        normalized_tokens = [normalize_for_match(token) for token in tokens]
        normalized_tokens = [token for token in normalized_tokens if token]
        anchor_key = str(entry.get("anchor_key", "")).strip()
        if normalized_tokens and anchor_key:
            matchers.append((anchor_key, normalized_tokens))

    bullets_by_anchor: Dict[str, List[str]] = {}
    unmatched: List[str] = []
    current_anchor = None

    for line in lines:
        norm_line = normalize_for_match(line)
        matched_anchor = None
        matched_strength = 0

        if len(line) < 180:
            for anchor_key, tokens in matchers:
                for token in tokens:
                    if token and token in norm_line and len(token) > matched_strength:
                        matched_anchor = anchor_key
                        matched_strength = len(token)

        if matched_anchor:
            current_anchor = matched_anchor
            bullets_by_anchor.setdefault(current_anchor, [])
            continue

        if DATE_PATTERN.search(line) and len(line) < 70:
            continue

        clean_line = line
        while clean_line and clean_line[0] in BULLET_PREFIXES:
            clean_line = clean_line[1:].strip()
        if not clean_line:
            continue

        if current_anchor:
            bullets_by_anchor.setdefault(current_anchor, []).append(clean_line)
        else:
            unmatched.append(clean_line)

    return bullets_by_anchor, unmatched
