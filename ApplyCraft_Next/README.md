# ApplyCraft

**Local-first CV & Cover Letter automation with built-in application tracking and JD-aware bullet ranking.**

ApplyCraft turns a single master `.docx` template + a personal "bullet inventory" into tailored CV and cover letter pairs for every job you apply to, and tracks every application from sent to outcome. Everything runs on your machine. Nothing is uploaded.

---

## What it does

| Feature | What you get |
|---|---|
| **Tailored CVs**   | Edit your per-job bullet text and headline in the UI, click Generate, get a date-stamped `.docx` + `.pdf` with your formatting preserved. |
| **Cover letters**  | Fill in company, city, country, hiring manager, body — out comes a formatted cover letter that matches your CV. |
| **JD-aware ranking** | Paste a job description and ApplyCraft scores every bullet in your inventory against it. Pick the top matches; auto-apply the top 5 per role. **Runs locally** — choose pure-Python TF-IDF, on-device embeddings, or a local Ollama daemon. |
| **Fit score**      | A single percentage answering "how well does my inventory cover what this JD asks for?" — based on best-bullet score, top-5 average, and JD keyword coverage. |
| **Application tracker** | SQLite + JSON-mirror DB of every application, with a Sankey funnel, conversion charts, country breakdown, stale/stalled radar, hotkey status updates, and CSV export. |
| **Local-first**    | Zero cloud accounts, zero telemetry. No data leaves your laptop unless *you* configure the OpenAI backend explicitly. |

---

## Install

You need Python 3.10+ and (on Windows) Microsoft Word installed for the PDF export step.

```bash
git clone <this repo>
cd ApplyCraft_Next
python setup_applycraft.py
```

The setup script creates a `venv/`, installs the dependencies, copies `user_config.example.json` to `user_config.json`, and asks for your name and location. Pass `--non-interactive` (or `-y`) to skip the wizard and edit the JSON by hand.

After setup, launch with the platform-appropriate script:

- **Windows:** double-click `launch_applycraft.bat`
- **macOS / Linux:** `./launch_applycraft.sh`

Or run directly:

```bash
venv/Scripts/python core/cv_generator_gui.py    # Windows
venv/bin/python core/cv_generator_gui.py        # macOS/Linux
```

---

## First-time setup, in detail

1. **Drop your master CV templates** into `templates/` as `.docx` files. ApplyCraft preserves the formatting of these templates — fonts, spacing, tables, headers — and only replaces the bullet text. Use a placeholder paragraph for your professional summary (any paragraph the app can find by a marker phrase works; see `core/update_cv.py` `_paragraph_has_marker`).

2. **Edit `user_config.json`** — at minimum, set:
   - `name`, `filename_slug`, `email`, `location`
   - `job_positions`: a dict of `"COMPANY – Role"` -> list of default bullets. Each key becomes a section heading in the CV and a tab in the Builder. These are also the bullets the JD ranker scores against.
   - `templates`: friendly name -> path of each template you dropped into `templates/`.
   - Optional: `relocation_line` if you want a bolded "EU citizen…" / "Authorised to work…" line under your summary.

3. **Pick a JD-ranking backend** (optional). The default `"local"` mode requires nothing. For better quality:
   - `"sentence_transformers"`: run `pip install sentence-transformers` once. First rank downloads ~80MB; everything after is instant and offline.
   - `"ollama"`: install [Ollama](https://ollama.com), then `ollama pull nomic-embed-text`. Set `provider: "ollama"`.
   - `"openai"`: paid, cloud, opt-in only. Your JD text is sent to OpenAI.

---

## Daily usage

The UI has five panels in the left sidebar:

- **Experience (CV)** — your bullet inventory, broken into one card per job. The top card holds template selector, company, country, role title, current location, and the professional summary. Each role card has an optional headline and a textbox of bullet points. Edits stream into the live preview.
- **Cover Letter** — recipient block + body. The body honours the `[Company Name]` placeholder which is auto-substituted at generation time.
- **Smart Import** — two tools:
  - *Smart Bullet Parser*: paste an existing CV's raw text; the parser detects role headings and routes bullets into the right job cards.
  - *JD-Aware Bullet Ranking*: paste a job description; press **Rank Against JD**. You get a fit-score percentage, the top-20 ranked bullets with the matched keywords, and an **Apply Top 5 / Job** button that pre-fills the CV builder.
- **Audit & Stats** — every application, sortable/filterable, with a Sankey funnel and conversion charts. Hotkeys: `U` (Unknown), `I` (In Process), `F` (Followed Up), `R` (Rejected).
- **Settings** — template paths and a few config switches.

Across every panel, **Ctrl+G** generates the currently-selected document(s) into `outputs/<date>/<company>/`.

---

## How the JD ranker works

The ranker is in `core/jd_ranker.py`. It takes the pasted JD and your bullet inventory and returns one `BulletScore(job_title, bullet, score, matched_keywords)` per bullet, sorted high-to-low.

Four backends, all selectable via `user_config.llm.provider`:

### `"local"` — pure-Python TF-IDF (default)

No dependencies, no install, no model download. Builds a TF-IDF index across all bullets, vectorises the JD against the same vocabulary, and scores each bullet as:

```
score = 0.65 * cosine_similarity(JD_tfidf, bullet_tfidf)
      + 0.35 * (|JD_terms ∩ bullet_terms| / |bullet_terms|)
```

Cosine rewards rare-term overlap (mentions of "dbt" or "Snowflake" matter more than "data"). The second term rewards *coverage* — bullets that touch many JD themes, even via common words. Blending them avoids the trap of cosine-only systems that over-reward bullets with a single rare jargon match.

Fast (<100ms for hundreds of bullets), zero quality cliff if the JD and your bullets share vocabulary, but blind to synonyms ("dashboards" vs "BI reports").

### `"sentence_transformers"` — local embeddings

Loads a [sentence-transformers](https://www.sbert.net/) model (default `all-MiniLM-L6-v2`, ~80MB) and computes cosine similarity between the JD embedding and each bullet embedding. The model runs entirely on-device — first call downloads weights into the HuggingFace cache, every subsequent call is offline.

This is the sweet-spot recommendation: ~80MB of disk, ~1 second per rank on a modern laptop, much better synonym handling than TF-IDF, no API key, no network after first download.

### `"ollama"` — local LLM server

Calls `http://localhost:11434/api/embed` on an [Ollama](https://ollama.com) daemon you run yourself. Default model `nomic-embed-text` (~270MB, MIT-licensed). If you already use Ollama for other things, this is the highest-quality local option.

### `"openai"` — paid cloud

Calls `text-embedding-3-small` via OpenAI's API using your key. Highest quality but your JD text leaves your machine. Opt-in only.

### What if my chosen backend isn't available?

If `sentence_transformers` isn't installed, or Ollama isn't running, the module logs a warning and **falls back to `local`** so the app keeps working. You'll see which backend was actually used in the fit-score line: e.g. `backend: sentence-transformers (all-MiniLM-L6-v2)` vs `backend: local TF-IDF`.

### Fit score — the single number

`compute_fit_score` blends three signals into one percentage:

```
fit = 0.45 * best_bullet_score
    + 0.30 * mean(top_5_bullet_scores)
    + 0.25 * (|JD keywords any bullet covers| / |JD keywords|)
```

The intuition: a recruiter reads your strongest bullets first (45% weight on the best one), they form an impression from your top section as a whole (30% weight on the top-5 average), and the JD's themes need to be addressed somewhere on the page (25% weight on keyword coverage). A CV with one great bullet but no breadth scores below a CV with five solid bullets that each cover a JD theme.

---

## Architecture

```
ApplyCraft_Next/
├── core/
│   ├── cv_generator_gui.py     # ── Main Tk/CustomTkinter app
│   ├── cv_service.py           # ── Orchestrates docx + pdf + stats writes
│   ├── update_cv.py            # ── python-docx surgery: bullets, summary, headlines
│   ├── generate_cover_letter.py# ── Cover-letter docx renderer
│   ├── jd_ranker.py            # ── JD-aware ranking + fit score (4 backends)
│   ├── stats_manager.py        # ── SQLite + JSON-mirror application tracker
│   ├── application_audit.py    # ── Audit panel (table, filters, hotkeys)
│   ├── audit_graph.py          # ── Velocity / volume charts
│   ├── audit_sankey.py         # ── Conversion-funnel Sankey
│   ├── audit_intel.py          # ── Stale/stalled radar + market panel
│   ├── audit_dialogs.py        # ── Edit / notes / status modals
│   └── config.py               # ── Design tokens + back-compat re-exports
├── helpers/
│   ├── user_config.py          # ── Single source of truth: who is the user?
│   └── logger.py               # ── Rotating file + console logger
├── template_intelligence/      # ── Experimental: learn template structure
├── templates/                  # ── Your master .docx files
├── outputs/                    # ── Generated CVs + cover letters (gitignored)
├── logs/                       # ── Daily log files (gitignored)
├── user_config.example.json    # ── Ships with repo; copy to user_config.json
├── user_config.json            # ── YOUR config (gitignored, never committed)
├── requirements.txt
├── setup_applycraft.py         # ── First-run setup wizard
├── launch_applycraft.bat       # ── Windows launcher
└── launch_applycraft.sh        # ── macOS / Linux launcher
```

<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
### Data flow for a single "Generate Both" click

1. **GUI** (`cv_generator_gui.py`) collects company, country, role title, current location, the summary, every per-job headline + bullets, and the cover letter fields.
2. It calls `CVGeneratorService.generate_both(...)` in `core/cv_service.py` on a background thread so the UI stays responsive.
3. `cv_service` builds the output paths from `user_config.filename_slug()` + the date + company, then calls:
   - `update_cv.update_cv_bullets(...)` — opens the chosen template with `python-docx`, finds the summary paragraph by matching a configurable marker, rewrites it with your text + relocation line, then walks the body looking for bullet paragraphs and table-headed roles. Bullets are replaced / added / removed to match the new count *without* losing the template's list formatting (it deep-copies the original bullet's XML for new entries).
   - `update_cv.convert_to_pdf(...)` — first tries `docx2pdf`, then `comtypes.client` (Word automation) as fallback. Removes trailing blank pages with PyPDF2.
   - `generate_cover_letter.generate_cover_letter(...)` — builds a clean docx from scratch in `python-docx`, applies justified body paragraphs, signs with `user_config.name()`.
4. `cv_service` then calls `stats_manager.add_application(...)`, which upserts a row into SQLite (`application_stats.db`) *and* mirrors the entry to `application_stats.json` so old shell scripts still work.
5. The audit panel sees the new row on its next refresh.

### How the bullet replacement preserves formatting

This is the heart of why the tool produces good CVs — most JSON-to-PDF generators flatten formatting. `update_cv` keeps it:

- Each template uses a per-role *table* (or a heading-followed-by-bullets layout) to mark where each job's bullets go. The function builds a `table_to_job` map by matching the cell text against the company name part of each `JOB_POSITIONS` key.
- For each job, it gathers all existing bullet paragraphs in the role's block. Then:
  - If the new bullet count matches the old count, it clears each paragraph's runs and writes the new text — keeping the paragraph's numbering, indent, font, and spacing exactly as designed.
  - If there are more new bullets than old, it `copy.deepcopy`s the last bullet's XML element and inserts the copies before writing the new text, so the new bullets inherit the same list style.
  - If there are fewer, it removes the trailing paragraph elements from the parent XML.
- Optional per-role *headlines* (italic one-liners) are inserted as a new paragraph immediately after the role's header element.

### Application tracker

`stats_manager.py` is the persistence layer. Notable decisions:

- **SQLite is the source of truth.** WAL mode is enabled so the GUI can read while a background scan writes. `application_stats.json` is regenerated on every save as a human-inspectable mirror; if you delete the DB it's reconstructed from the JSON, and vice versa.
- **Country auto-detection** uses `user_config.country_keywords()` against the generated CV filename's suffix. So a file named `Jane_Doe_CV_Acme_Stockholm.pdf` is tagged "Sweden". Manual edits set `country_manual=True`, after which scans never overwrite them.
- **Status normalisation** consolidates dozens of historical free-text statuses ("Initial Interview", "Task", "Currently Interviewing") into the four canonical buckets the funnel uses (Unknown, In Process, Followed Up, Rejected\*) plus Offer/Accepted. Rejected is split into (Initial), (Post-Interview), (Post-Task) so the funnel can show where you're losing applications.

### Audit dashboard

`application_audit.py` (the panel) + the three viz modules:

- `audit_graph.py` — line/bar charts of applications-per-week, status-over-time.
- `audit_sankey.py` — the conversion funnel: Sent → In Process → Rejected/Offer at each stage. This is the panel that tells you *where* you're losing.
- `audit_intel.py` — "Action Radar": applications stale (>14 days) and stalled (>30 days), grouped by country and status. This is the daily-decision panel.

Hotkeys (`U`/`I`/`F`/`R`) work on whichever row(s) the user has selected. CSV export covers whatever filter set is currently applied.
=======
### 4. First Run Profile
On first launch, ApplyCraft creates `user_profile.json` locally (pre-filled with bundled template defaults).

Use it to set:
- `full_name` (used in output filenames and cover letter signature)
- `template_1` and `template_2` paths (relative to project root)

This keeps generation identity and templates user-specific while remaining fully local-first.

>>>>>>> theirs

### 4. First Run Profile
On first launch, ApplyCraft creates `user_profile.json` locally (pre-filled with bundled template defaults).

Use it to set:
- `full_name` (used in output filenames and cover letter signature)
- `template_1` and `template_2` paths (relative to project root)

This keeps generation identity and templates user-specific while remaining fully local-first.


### 4. First Run Profile
On first launch, ApplyCraft creates `user_profile.json` locally (pre-filled with bundled template defaults).

Use it to set:
- `full_name` (used in output filenames and cover letter signature)
- `template_1` and `template_2` paths (relative to project root)

This keeps generation identity and templates user-specific while remaining fully local-first.


### 4. First Run Profile
On first launch, ApplyCraft creates `user_profile.json` locally (pre-filled with bundled template defaults).

Use it to set:
- `full_name` (used in output filenames and cover letter signature)
- `template_1` and `template_2` paths (relative to project root)

This keeps generation identity and templates user-specific while remaining fully local-first.


### 4. First Run Profile
On first launch, ApplyCraft creates `user_profile.json` locally (pre-filled with bundled template defaults).

Use it to set:
- `full_name` (used in output filenames and cover letter signature)
- `template_1` and `template_2` paths (relative to project root)

This keeps generation identity and templates user-specific while remaining fully local-first.


### 4. First Run Profile
On first launch, ApplyCraft creates `user_profile.json` locally (pre-filled with bundled template defaults).

Use it to set:
- `full_name` (used in output filenames and cover letter signature)
- `template_1` and `template_2` paths (relative to project root)

This keeps generation identity and templates user-specific while remaining fully local-first.


=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
### 4. First Run Profile
On first launch, ApplyCraft creates `user_profile.json` locally (pre-filled with bundled template defaults).

Use it to set:
- `full_name` (used in output filenames and cover letter signature)
- `template_1` and `template_2` paths (relative to project root)

This keeps generation identity and templates user-specific while remaining fully local-first.


---

## Privacy

ApplyCraft is local-first by design:

- **Nothing is uploaded** by default. The pure-Python ranker, the sentence-transformers backend, and the Ollama backend all stay on your machine.
- **No accounts, no telemetry.** There is no analytics SDK, no crash reporter, no anonymous usage stats.
- **Your data lives in your folder.** `user_config.json`, `application_stats.json`, `application_stats.db`, `outputs/`, and `logs/` are all in the project folder and are all `.gitignore`d. Move the folder, move your job-hunt history.
- **The one exception:** if *you* set `llm.provider = "openai"` and supply an API key, your pasted JD text is sent to OpenAI when you press "Rank Against JD". The other three backends never make a network call.

---

## Reading guide for the codebase

If you want to extend ApplyCraft, here's the recommended reading order:

1. `helpers/user_config.py` — the only place that knows who you are. Add new config keys here.
2. `core/jd_ranker.py` — self-contained module with a 4-way backend switch. Drop a new `_rank_with_X` function and wire it into `rank_bullets` to add a backend.
3. `core/update_cv.py` — the template surgery. The pattern for finding/replacing content is in `update_cv_bullets`; it's worth reading in full before touching template logic.
4. `core/cv_generator_gui.py` — the UI. Long but linear: `__init__` lays out the sidebar + main grid; each `setup_*_panel` builds a single tab; each `_start_gen` / `_run_generation` pair handles a click.
5. `core/stats_manager.py` — boring but important. Read top-to-bottom; the SQLite schema is small.
6. `core/application_audit.py` and the `audit_*` modules — the dashboard. Each viz is self-contained, so you can swap one without touching the others.

---

## License

MIT.
