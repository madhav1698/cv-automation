# Testing Documentation 🧪

This document explains the tests we have run to make sure the CV Automation tool works perfectly. We used three different types of tests to check every part of the system.

## 1. Unit Testing (The Building Blocks)
**File:** `tests/test_stats_manager_unit.py`

These tests check the "brain" of the application tracking system (`StatsManager`). We make sure that:
* **Adding Apps:** When you apply for a job, the system saves the company name and country correctly.
* **Saving Status:** If you change a status (like from "Applied" to "Interview"), it remembers it.
* **Math Check:** The summary (total applications, total rejections) adds up correctly.

**Status:** ✅ All 3 tests passed.

## 2. Integration Testing (The Real Deal)
**Files:** `tests/test_flexible.py` and `tests/test_job_aware.py`

These tests run the actual CV generation process using a real template.
* **Flexible Bullets:** We checked that if you want to use 3 bullets for one job and 7 for another, the tool adds/removes lines in Word without breaking the layout.
* **Job Matching:** We made sure the tool finds the right spot in your CV for each specific company.

**Status:** ✅ Successfully generated test CVs in the `outputs/` folder.

## 3. Logic Verification (The "Smart" Test)
**Files:** `tests/verify_fix.py` and `tests/reproduce_issue.py`

These tests check the logic used to "read" job titles.
* **Smart Matching:** We tested if the tool can recognize a company name even if we use different symbols (like `|` instead of `-` or `:`).
* **Fix Check:** We compared the "old" way of finding jobs with our "new" smart way to prove it is more reliable.

**Status:** ✅ Proved that the tool is now much better at recognizing job titles.

---

### How to run tests yourself:
If you want to run these tests again, you can use these commands in your terminal:

```powershell
# Run the core logic tests
$env:PYTHONPATH = ".;core"; python tests/test_stats_manager_unit.py

# Run the CV generation tests
$env:PYTHONPATH = "core"; python tests/test_flexible.py
$env:PYTHONPATH = "core"; python tests/test_job_aware.py
```
