"""
user_config.py
----------------
Loads user-specific configuration (name, contact info, default summary,
job positions, templates, optional LLM key) from ``user_config.json`` at
the project root.

Why this exists
~~~~~~~~~~~~~~~
The first version of ApplyCraft hardcoded one person's name, summary,
and job history. That made the tool unusable for anyone else. This
module is the single place every other module asks "who is the user?"
so the rest of the code stays generic.

Resolution order
~~~~~~~~~~~~~~~~
1. ``user_config.json`` next to the project root (created by the first-run
   wizard, or hand-edited from ``user_config.example.json``).
2. Built-in safe defaults so the app still opens if the file is missing
   (the GUI will then prompt the user to run setup).
"""

from __future__ import annotations

import copy
import json
import os
import sys
import threading
from typing import Any, Dict, Optional


# --------------------------------------------------------------------------
# Built-in defaults
# --------------------------------------------------------------------------
# These are intentionally generic placeholders. They keep the app runnable
# even if the user has not configured anything yet. The settings panel /
# first-run wizard is what populates real values.

DEFAULT_CONFIG: Dict[str, Any] = {
    "name": "Your Name",
    "filename_slug": "Your_Name",   # used for output filenames
    "email": "",
    "phone": "",
    "location": "",                 # used in the "currently in X" line
    "default_summary": (
        "Briefly describe your professional background here. This text "
        "fills the Summary section of the CV when nothing else is typed."
    ),
    "default_cover_letter_body": (
        "Use this space for a default cover letter body. Mention what "
        "draws you to [Company Name] and frame two or three concrete "
        "themes from your work that map onto the role."
    ),
    "relocation_line": "",          # e.g. "EU citizen, no visa required..."
    "show_relocation_line": False,
    "job_positions": {
        # Display name -> list of default bullets
        "EXAMPLE COMPANY – Role Title": [
            "Replace these bullets with real achievements from this role.",
            "Each bullet should be a concrete outcome, not a duty.",
            "Quantify wherever possible (%, $, time saved, users, etc).",
        ]
    },
    "templates": {
        # Friendly name -> path (relative to project root or absolute)
        "Template 1": "templates/CV_Template_1.docx",
        "Template 2": "templates/CV_Template_2.docx",
    },
    "cover_letter_template": "templates/Cover_Letter_Template.docx",
    "country_keywords": {
        # Used by stats_manager to auto-detect country from filenames.
        # Add city/country pairs you commonly apply to.
        "Denmark":     ["Denmark", "Copenhagen", "Aarhus", "Odense", "Aalborg"],
        "Sweden":      ["Sweden", "Stockholm", "Gothenburg", "Malmo", "Uppsala"],
        "UK":          ["UK", "London", "Manchester", "Birmingham",
                        "Edinburgh", "Glasgow", "Leeds", "Bristol", "Liverpool"],
        "Spain":       ["Spain", "Madrid", "Barcelona", "Valencia",
                        "Seville", "Malaga", "Bilbao", "Alicante", "Palma"],
        "Ireland":     ["Ireland", "Dublin", "Cork", "Galway",
                        "Limerick", "Waterford", "Dundalk", "Drogheda", "Swords"],
        "Norway":      ["Norway", "Oslo", "Bergen", "Trondheim", "Stavanger"],
        "Finland":     ["Finland", "Helsinki", "Espoo", "Tampere", "Vantaa", "Oulu"],
        "Netherlands": ["Netherlands", "Amsterdam", "Rotterdam", "Utrecht",
                        "Eindhoven", "Den Haag", "The Hague"],
    },
    "llm": {
        # Which ranking backend to use. All except "openai" stay local.
        #   "sentence_transformers"  - on-device embeddings (the local LLM).
        #                              Falls back to TF-IDF if not installed.
        #   "local"                  - pure-Python TF-IDF (zero deps)
        #   "ollama"                 - local Ollama daemon on localhost
        #   "openai"                 - paid cloud (data leaves the machine)
        #
        # Default is sentence_transformers — the app gracefully falls back to
        # TF-IDF on the first run if it isn't installed yet, and the GUI
        # has a one-click "Install Local LLM" button for the user.
        "provider": "sentence_transformers",
        "model": "",
        "api_key": "",
        "host": "http://localhost:11434",
    },
}


# --------------------------------------------------------------------------
# Path resolution
# --------------------------------------------------------------------------

def _project_root() -> str:
    """Return the project root (the folder that contains ``helpers/``)."""
    try:
        # PyInstaller bundle support
        base = sys._MEIPASS  # type: ignore[attr-defined]
    except Exception:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return base


def config_path() -> str:
    """Absolute path to the user config JSON file."""
    return os.path.join(_project_root(), "user_config.json")


def example_path() -> str:
    """Absolute path to the example config JSON file (shipped with repo)."""
    return os.path.join(_project_root(), "user_config.example.json")


# --------------------------------------------------------------------------
# Load / save
# --------------------------------------------------------------------------

_lock = threading.RLock()
_cache: Optional[Dict[str, Any]] = None


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Merge ``override`` into a deep copy of ``base`` (override wins)."""
    out = copy.deepcopy(base)
    for key, val in (override or {}).items():
        if (
            key in out
            and isinstance(out[key], dict)
            and isinstance(val, dict)
        ):
            out[key] = _deep_merge(out[key], val)
        else:
            out[key] = val
    return out


def load(force_reload: bool = False) -> Dict[str, Any]:
    """Return the merged user config (defaults + on-disk overrides).

    Uses a process-wide cache so repeated calls are cheap.
    Pass ``force_reload=True`` after writing to refresh.
    """
    global _cache
    with _lock:
        if _cache is not None and not force_reload:
            return _cache

        path = config_path()
        on_disk: Dict[str, Any] = {}
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    on_disk = json.load(f) or {}
            except Exception:
                # Corrupt file -> ignore, fall back to defaults.
                on_disk = {}

        _cache = _deep_merge(DEFAULT_CONFIG, on_disk)
        return _cache


def save(cfg: Dict[str, Any]) -> None:
    """Persist ``cfg`` to disk and refresh the cache."""
    global _cache
    with _lock:
        path = config_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # Only write the keys that differ from defaults to keep the file
        # readable, but for simplicity we write the full merged config.
        merged = _deep_merge(DEFAULT_CONFIG, cfg)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2, ensure_ascii=False)
        _cache = merged


def is_first_run() -> bool:
    """True if the user has not created ``user_config.json`` yet."""
    return not os.path.exists(config_path())


# --------------------------------------------------------------------------
# Convenience accessors used across the codebase
# --------------------------------------------------------------------------

def name() -> str:
    return load().get("name") or DEFAULT_CONFIG["name"]


def filename_slug() -> str:
    """Underscore-joined name used in output filenames.

    Falls back to a slugified version of ``name()`` if not explicitly set.
    """
    cfg = load()
    slug = cfg.get("filename_slug")
    if slug:
        return slug
    return (cfg.get("name") or "User").strip().replace(" ", "_")


def default_summary() -> str:
    return load().get("default_summary") or DEFAULT_CONFIG["default_summary"]


def default_cover_letter_body() -> str:
    return (
        load().get("default_cover_letter_body")
        or DEFAULT_CONFIG["default_cover_letter_body"]
    )


def job_positions() -> Dict[str, list]:
    """Mapping of job title -> list of default bullets."""
    return load().get("job_positions") or DEFAULT_CONFIG["job_positions"]


def templates() -> Dict[str, str]:
    """Mapping of template friendly-name -> path (absolute or project-relative)."""
    return load().get("templates") or DEFAULT_CONFIG["templates"]


def resolved_template_paths() -> Dict[str, str]:
    """Same as :func:`templates` but every path is resolved to absolute."""
    root = _project_root()
    out: Dict[str, str] = {}
    for label, path in templates().items():
        out[label] = path if os.path.isabs(path) else os.path.join(root, path)
    return out


def cover_letter_template() -> str:
    cfg = load()
    path = cfg.get("cover_letter_template") or DEFAULT_CONFIG["cover_letter_template"]
    if not os.path.isabs(path):
        path = os.path.join(_project_root(), path)
    return path


def location() -> str:
    return load().get("location") or ""


def relocation_line(current_location: Optional[str] = None) -> str:
    """Return the line shown after the Summary, e.g. visa/relocation status.

    ``{location}`` in the template string is replaced with the location passed
    in (or, if not, the configured default).
    """
    cfg = load()
    if not cfg.get("show_relocation_line"):
        return ""
    template = cfg.get("relocation_line") or ""
    loc = current_location or cfg.get("location") or ""
    return template.replace("{location}", loc).strip()


def country_keywords() -> Dict[str, list]:
    return load().get("country_keywords") or DEFAULT_CONFIG["country_keywords"]


def llm_config() -> Dict[str, Any]:
    return load().get("llm") or DEFAULT_CONFIG["llm"]
