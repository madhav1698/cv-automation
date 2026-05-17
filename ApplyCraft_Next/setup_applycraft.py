"""
setup_applycraft.py
--------------------
First-run setup helper for ApplyCraft.

Run this once after cloning:

    python setup_applycraft.py

What it does (in order):

1. Verifies you're on Python 3.10 or newer.
2. Creates a ``venv/`` virtual environment if one doesn't already exist.
3. Installs the dependencies listed in ``requirements.txt`` into the venv.
4. Copies ``user_config.example.json`` -> ``user_config.json`` if missing,
   so the app has a working config on first launch.
5. Asks for the user's name + filename slug + location and writes them
   into ``user_config.json`` so the app is usable immediately. (Optional —
   you can skip and edit the JSON by hand later.)

This script never reaches the network beyond pip. No telemetry.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / "venv"
REQ_FILE = ROOT / "requirements.txt"
EXAMPLE_CFG = ROOT / "user_config.example.json"
USER_CFG = ROOT / "user_config.json"

MIN_PY = (3, 10)


def _check_python() -> None:
    if sys.version_info < MIN_PY:
        sys.exit(
            f"ApplyCraft requires Python {MIN_PY[0]}.{MIN_PY[1]}+. "
            f"You're on {sys.version.split()[0]}."
        )


def _venv_python() -> Path:
    """Path to the Python interpreter *inside* the venv we'll create."""
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def _create_venv() -> None:
    if VENV_DIR.exists() and _venv_python().exists():
        print(f"[ok]    venv already exists at {VENV_DIR}")
        return
    print(f"[step]  creating venv at {VENV_DIR} ...")
    venv.create(VENV_DIR, with_pip=True, clear=False)
    print(f"[ok]    venv created")


def _install_deps() -> None:
    py = _venv_python()
    if not py.exists():
        sys.exit(f"[fatal] expected venv python at {py} but it isn't there")
    if not REQ_FILE.exists():
        sys.exit(f"[fatal] {REQ_FILE} not found")

    print("[step]  upgrading pip inside the venv ...")
    subprocess.check_call([str(py), "-m", "pip", "install", "--upgrade", "pip"])

    print(f"[step]  installing requirements from {REQ_FILE} ...")
    subprocess.check_call([str(py), "-m", "pip", "install", "-r", str(REQ_FILE)])
    print("[ok]    dependencies installed")


def _seed_user_config() -> dict:
    """Create ``user_config.json`` from the example if it's missing.

    Returns the loaded config dict so we can offer to edit it interactively.
    """
    if USER_CFG.exists():
        print(f"[ok]    user_config.json already exists — leaving it alone")
        with USER_CFG.open("r", encoding="utf-8") as f:
            return json.load(f)

    if not EXAMPLE_CFG.exists():
        sys.exit(f"[fatal] {EXAMPLE_CFG} not found; can't seed user_config.json")

    shutil.copy(EXAMPLE_CFG, USER_CFG)
    print(f"[ok]    created {USER_CFG.name} from the example")
    with USER_CFG.open("r", encoding="utf-8") as f:
        return json.load(f)


def _strip_example_comments(cfg: dict) -> dict:
    """Remove ``_comment_*`` keys from the seeded config."""
    return {k: v for k, v in cfg.items() if not k.startswith("_comment_")}


def _prompt_user_details(cfg: dict) -> dict:
    """Tiny interactive wizard. Skippable: just hit Enter on every prompt."""
    print()
    print("Optional: enter your details now. Press Enter to skip any field.")
    print("You can always edit user_config.json later.")
    print()

    def _ask(prompt: str, default: str) -> str:
        suffix = f" [{default}]" if default else ""
        try:
            val = input(f"  {prompt}{suffix}: ").strip()
        except EOFError:
            val = ""
        return val or default

    cfg["name"] = _ask("Your full name", cfg.get("name", ""))
    cfg["filename_slug"] = _ask(
        "Filename slug (used in output filenames, e.g. Jane_Doe)",
        cfg.get("filename_slug") or cfg["name"].replace(" ", "_"),
    )
    cfg["email"] = _ask("Email", cfg.get("email", ""))
    cfg["location"] = _ask("Current city", cfg.get("location", ""))

    backend = _ask(
        "Bullet-ranker backend (local | sentence_transformers | ollama | openai)",
        cfg.get("llm", {}).get("provider", "local"),
    )
    cfg.setdefault("llm", {})["provider"] = backend

    return cfg


def _save_user_config(cfg: dict) -> None:
    cfg = _strip_example_comments(cfg)
    with USER_CFG.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    print(f"[ok]    saved {USER_CFG.name}")


def _print_next_steps() -> None:
    py = _venv_python()
    print()
    print("Next steps")
    print("----------")
    if os.name == "nt":
        print(f"  1. Drop your master CV templates into {ROOT / 'templates'}/.")
        print(f"     Edit user_config.json -> templates so the filenames match.")
        print(f"  2. Launch the app:")
        print(f"     \"{py}\" core\\cv_generator_gui.py")
        print(f"     ...or double-click launch_applycraft.bat")
    else:
        print(f"  1. Drop your master CV templates into {ROOT / 'templates'}/.")
        print(f"     Edit user_config.json -> templates so the filenames match.")
        print(f"  2. Launch the app:")
        print(f"     {py} core/cv_generator_gui.py")
        print(f"     ...or run ./launch_applycraft.sh")
    print()


def main() -> None:
    print("ApplyCraft setup")
    print("================")
    _check_python()
    _create_venv()
    _install_deps()
    cfg = _seed_user_config()

    do_wizard = True
    if len(sys.argv) > 1 and sys.argv[1] in ("-y", "--non-interactive"):
        do_wizard = False

    if do_wizard:
        try:
            cfg = _prompt_user_details(cfg)
        except KeyboardInterrupt:
            print("\n[skip]  wizard cancelled — you can edit user_config.json by hand")
        else:
            _save_user_config(cfg)
    else:
        print("[skip]  --non-interactive: edit user_config.json by hand later")

    _print_next_steps()


if __name__ == "__main__":
    main()
