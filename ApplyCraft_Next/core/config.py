"""
core/config.py
---------------
Bridges UI / generation modules to the user-supplied configuration.

Previously this file hardcoded one person's CV. Now the only hardcoded
values are the visual design tokens; everything user-specific (summary,
job positions, default cover letter, etc.) is pulled from
``helpers.user_config`` which reads ``user_config.json``.

Backwards-compatible: existing imports of ``SUMMARY_TEXT``,
``JOB_POSITIONS``, ``DEFAULT_CL_BODY`` still work — they are populated
at import time from the user's config.
"""

from __future__ import annotations

import os
import sys

import customtkinter as ctk  # noqa: F401 -- kept for import-side effects elsewhere

# Make the project root importable so ``from helpers...`` works whether
# this module is loaded as ``core.config`` or run directly.
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from helpers import user_config  # noqa: E402


# --------------------------------------------------------------------------
# UI design tokens (intentionally hardcoded — these are theme constants,
# not user data).
# --------------------------------------------------------------------------
DESIGN_TOKENS = {
    "bg":            ("#F9FAFB", "#0B0F14"),
    "sidebar":       ("#FFFFFF", "#111622"),
    "preview_bg":    ("#F1F5F9", "#080B10"),
    "input_bg":      ("#FFFFFF", "#1A202C"),
    "accent":        "#6366F1",
    "accent_soft":   ("#EEF2FF", "#1E2235"),
    "text":          ("#111827", "#F3F4F6"),
    "text_muted":    ("#6B7280", "#9CA3AF"),
    "border":        ("#E5E7EB", "#1F2937"),
    "success":       "#10B981",
    "card":          ("#FFFFFF", "#161D29"),
}


# --------------------------------------------------------------------------
# Legacy module-level constants — populated from user_config.
# These remain so existing code that does ``from core.config import
# JOB_POSITIONS`` keeps working without edits.
# --------------------------------------------------------------------------
SUMMARY_TEXT = user_config.default_summary()
DEFAULT_CL_BODY = user_config.default_cover_letter_body()
JOB_POSITIONS = user_config.job_positions()


def refresh_from_user_config() -> None:
    """Re-read user_config.json and refresh the legacy module-level names.

    Call this after the settings panel writes a new config so importers
    that captured the names at import time can re-sync. Note: code paths
    that always call ``user_config.X()`` directly are immune to staleness
    and should be preferred for new code.
    """
    global SUMMARY_TEXT, DEFAULT_CL_BODY, JOB_POSITIONS
    user_config.load(force_reload=True)
    SUMMARY_TEXT = user_config.default_summary()
    DEFAULT_CL_BODY = user_config.default_cover_letter_body()
    JOB_POSITIONS = user_config.job_positions()


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def get_resource_path(relative_path: str) -> str:
    """Get absolute path to a resource, working both in dev and in PyInstaller."""
    try:
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except Exception:
        base_path = _project_root
    return os.path.join(base_path, relative_path)
