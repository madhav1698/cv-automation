import os
import json
import sqlite3
import threading
import sys
from datetime import datetime

# Set up paths for internal imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from helpers.logger import logger

COUNTRY_MAP = {
    "Denmark": ["Denmark", "Copenhagen", "Aarhus", "Odense", "Aalborg"],
    "Sweden": ["Sweden", "Stockholm", "Gothenburg", "Malmo", "Uppsala"],
    "UK": ["UK", "London", "Manchester", "Birmingham", "Edinburgh", "Glasgow", "Leeds", "Bristol", "Liverpool"],
    "Spain": ["Spain", "Madrid", "Barcelona", "Valencia", "Seville", "Malaga", "Bilbao", "Alicante", "Palma"],
    "Ireland": ["Ireland", "Dublin", "Cork", "Galway", "Limerick", "Waterford", "Dundalk", "Drogheda", "Swords"],
    "Norway": ["Norway", "Oslo", "Bergen", "Trondheim", "Stavanger"],
    "Finland": ["Finland", "Helsinki", "Espoo", "Tampere", "Vantaa", "Oulu"],
    "Netherlands": ["Netherlands", "Amsterdam", "Rotterdam", "Utrecht", "Eindhoven", "Den Haag", "The Hague"]
}


class StatsManager:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.outputs_dir = os.path.join(base_dir, "outputs")
        self.stats_file = os.path.join(base_dir, "application_stats.json")
        self.deleted_file = os.path.join(base_dir, "application_deleted.json")
        self.db_file = os.path.join(base_dir, "application_stats.db")
        self._db_lock = threading.RLock()

        self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
        self._migrate_from_json_if_needed()

        self._deleted_ids = self._load_deleted_ids_from_db()
        self.stats = self._load_stats_from_db()

        # Keep the legacy JSON files as mirrors for backward compatibility.
        self._write_json_mirror()

    def close(self):
        with self._db_lock:
            try:
                self.conn.close()
            except Exception as e:
                logger.error(f"Error closing StatsManager database connection: {e}")

    def __del__(self):
        self.close()

    def _init_db(self):
        with self._db_lock:
            with self.conn:
                self.conn.execute("PRAGMA journal_mode=WAL")
                self.conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS applications (
                        app_id TEXT PRIMARY KEY,
                        date TEXT NOT NULL,
                        company TEXT NOT NULL,
                        folder_name TEXT NOT NULL,
                        country TEXT DEFAULT 'Unknown',
                        country_manual INTEGER DEFAULT 0,
                        role_title TEXT DEFAULT '',
                        status TEXT DEFAULT 'Unknown',
                        status_manual INTEGER DEFAULT 0,
                        manual INTEGER DEFAULT 0,
                        cv_found INTEGER DEFAULT 0,
                        last_updated TEXT NOT NULL
                    )
                    """
                )
                self.conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS deleted_ids (
                        app_id TEXT PRIMARY KEY
                    )
                    """
                )
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_app_date ON applications(date)")
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_app_status ON applications(status)")
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_app_country ON applications(country)")

    def _load_deleted_ids_from_legacy_json(self):
        if os.path.exists(self.deleted_file):
            try:
                with open(self.deleted_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, list):
                    return set(str(x) for x in data)
                if isinstance(data, dict) and isinstance(data.get('deleted_ids'), list):
                    return set(str(x) for x in data.get('deleted_ids'))
            except Exception as e:
                logger.error(f"Error loading deleted IDs from legacy JSON: {e}")
                return set()
        return set()

    def _load_stats_from_legacy_json(self):
        if not os.path.exists(self.stats_file):
            return {}
        try:
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f) or {}
        except Exception as e:
            logger.error(f"Error loading stats from legacy JSON: {e}")
            return {}

        needs_fix = False
        for _, data in stats.items():
            if 'last_updated' not in data:
                data['last_updated'] = "2000-01-01 00:00:00"
                needs_fix = True
            if 'folder_name' not in data:
                data['folder_name'] = data.get('company', '').replace(' ', '_')
                needs_fix = True
            if 'role_title' not in data:
                data['role_title'] = ""
                needs_fix = True
            if 'status_manual' not in data:
                data['status_manual'] = False
                needs_fix = True
            if 'country_manual' not in data:
                data['country_manual'] = False
                needs_fix = True
            if 'manual' not in data:
                data['manual'] = False
                needs_fix = True
            if 'cv_found' not in data:
                data['cv_found'] = False
                needs_fix = True

        if needs_fix:
            try:
                with open(self.stats_file, 'w', encoding='utf-8') as f:
                    json.dump(stats, f, indent=4)
            except Exception as e:
                logger.error(f"Error fixing legacy stats JSON: {e}")

        return stats

    def _migrate_from_json_if_needed(self):
        with self._db_lock:
            count = self.conn.execute("SELECT COUNT(*) AS c FROM applications").fetchone()["c"]
        if count > 0:
            return

        legacy_stats = self._load_stats_from_legacy_json()
        legacy_deleted = self._load_deleted_ids_from_legacy_json()

        if not legacy_stats and not legacy_deleted:
            return

        with self._db_lock:
            with self.conn:
                for app_id in legacy_deleted:
                    self.conn.execute(
                        "INSERT OR IGNORE INTO deleted_ids(app_id) VALUES (?)",
                        (str(app_id),)
                    )

                for app_id, data in legacy_stats.items():
                    if str(app_id) in legacy_deleted:
                        continue
                    self._upsert_application_row(str(app_id), data, commit=False)

    def _row_to_dict(self, row):
        return {
            "date": row["date"],
            "company": row["company"],
            "folder_name": row["folder_name"],
            "country": row["country"],
            "country_manual": bool(row["country_manual"]),
            "role_title": row["role_title"] or "",
            "status": row["status"],
            "status_manual": bool(row["status_manual"]),
            "manual": bool(row["manual"]),
            "cv_found": bool(row["cv_found"]),
            "last_updated": row["last_updated"]
        }

    def _load_deleted_ids_from_db(self):
        with self._db_lock:
            rows = self.conn.execute("SELECT app_id FROM deleted_ids").fetchall()
        return set(str(r["app_id"]) for r in rows)

    def _load_stats_from_db(self):
        with self._db_lock:
            rows = self.conn.execute(
                "SELECT * FROM applications WHERE app_id NOT IN (SELECT app_id FROM deleted_ids)"
            ).fetchall()
        return {str(r["app_id"]): self._row_to_dict(r) for r in rows}

    def _upsert_application_row(self, app_id, data, commit=True):
        values = (
            app_id,
            data.get("date", ""),
            data.get("company", "").replace("_", " "),
            data.get("folder_name", data.get("company", "").replace(" ", "_")),
            data.get("country", "Unknown") or "Unknown",
            1 if data.get("country_manual", False) else 0,
            data.get("role_title", "") or "",
            data.get("status", "Unknown") or "Unknown",
            1 if data.get("status_manual", False) else 0,
            1 if data.get("manual", False) else 0,
            1 if data.get("cv_found", False) else 0,
            data.get("last_updated", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )

        if commit:
            with self._db_lock:
                with self.conn:
                    self.conn.execute(
                        """
                        INSERT INTO applications (
                            app_id, date, company, folder_name, country, country_manual,
                            role_title, status, status_manual, manual, cv_found, last_updated
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(app_id) DO UPDATE SET
                            date=excluded.date,
                            company=excluded.company,
                            folder_name=excluded.folder_name,
                            country=excluded.country,
                            country_manual=excluded.country_manual,
                            role_title=excluded.role_title,
                            status=excluded.status,
                            status_manual=excluded.status_manual,
                            manual=excluded.manual,
                            cv_found=excluded.cv_found,
                            last_updated=excluded.last_updated
                        """,
                        values
                    )
        else:
            with self._db_lock:
                self.conn.execute(
                    """
                    INSERT INTO applications (
                        app_id, date, company, folder_name, country, country_manual,
                        role_title, status, status_manual, manual, cv_found, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(app_id) DO UPDATE SET
                        date=excluded.date,
                        company=excluded.company,
                        folder_name=excluded.folder_name,
                        country=excluded.country,
                        country_manual=excluded.country_manual,
                        role_title=excluded.role_title,
                        status=excluded.status,
                        status_manual=excluded.status_manual,
                        manual=excluded.manual,
                        cv_found=excluded.cv_found,
                        last_updated=excluded.last_updated
                    """,
                    values
                )

    def _write_json_mirror(self):
        # JSON mirrors keep old tooling/scripts working while SQLite is the source of truth.
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=4)
        except Exception as e:
            logger.error(f"Error writing stats JSON mirror: {e}")

        try:
            with open(self.deleted_file, 'w', encoding='utf-8') as f:
                json.dump({"deleted_ids": sorted(self._deleted_ids)}, f, indent=4)
        except Exception as e:
            logger.error(f"Error writing deleted items JSON mirror: {e}")

    def _refresh_cache_from_db(self):
        self._deleted_ids = self._load_deleted_ids_from_db()
        self.stats = self._load_stats_from_db()

    def _save_stats(self):
        # Persist in-memory cache to DB. Used by legacy code paths.
        with self._db_lock:
            with self.conn:
                for app_id, data in self.stats.items():
                    if app_id in self._deleted_ids:
                        continue
                    self._upsert_application_row(app_id, data, commit=False)
                for app_id in self._deleted_ids:
                    self.conn.execute("INSERT OR IGNORE INTO deleted_ids(app_id) VALUES (?)", (app_id,))
                    self.conn.execute("DELETE FROM applications WHERE app_id = ?", (app_id,))

        self._refresh_cache_from_db()
        self._write_json_mirror()

    def add_application(self, date_str, company, country, status="Unknown", manual=False, role_title=""):
        """Explicitly adds an application to the stats, avoiding the need for a full scan."""
        app_id = self._build_app_id(date_str, company)

        entry = {
            "date": date_str,
            "company": company.replace("_", " "),
            "folder_name": company.replace(" ", "_"),
            "country": country or "Unknown",
            "country_manual": bool(manual),
            "role_title": role_title or "",
            "status": status or "Unknown",
            "status_manual": bool(manual),
            "manual": bool(manual),
            "cv_found": self.stats.get(app_id, {}).get("cv_found", False),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        with self._db_lock:
            with self.conn:
                self._upsert_application_row(app_id, entry, commit=False)
                self.conn.execute("DELETE FROM deleted_ids WHERE app_id = ?", (app_id,))

        self._refresh_cache_from_db()
        self._write_json_mirror()
        return app_id

    def _build_app_id(self, date_str, company):
        company_clean = "".join(c for c in company.replace(" ", "_") if c.isalnum() or c in ("_", "-"))
        return f"{date_str}_{company_clean}"

    def _build_folder_name(self, company):
        return (company or "").replace(" ", "_")

    def rename_application(self, app_id, new_date, new_company):
        """Rename the application identity (app_id) when date/company are edited."""
        self._refresh_cache_from_db()
        if app_id not in self.stats:
            return False, app_id

        current = dict(self.stats[app_id])
        target_date = new_date or current.get("date", "")
        target_company = (new_company or current.get("company", "")).replace("_", " ")
        new_app_id = self._build_app_id(target_date, target_company)

        # If the ID remains unchanged, only patch values and save.
        if new_app_id == app_id:
            old_company = current.get("company", "")
            old_folder_default = self._build_folder_name(old_company)
            current["date"] = target_date
            current["company"] = target_company
            if current.get("folder_name", old_folder_default) == old_folder_default:
                current["folder_name"] = self._build_folder_name(target_company)
            current["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.stats[app_id] = current
            self._save_stats()
            return True, app_id

        if new_app_id in self.stats:
            return False, app_id

        old_company = current.get("company", "")
        old_folder_default = self._build_folder_name(old_company)
        if current.get("folder_name", old_folder_default) == old_folder_default:
            current["folder_name"] = self._build_folder_name(target_company)

        current["date"] = target_date
        current["company"] = target_company
        current["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self._db_lock:
            with self.conn:
                self._upsert_application_row(new_app_id, current, commit=False)
                self.conn.execute("DELETE FROM applications WHERE app_id = ?", (app_id,))
                self.conn.execute("DELETE FROM deleted_ids WHERE app_id = ?", (app_id,))
                self.conn.execute("DELETE FROM deleted_ids WHERE app_id = ?", (new_app_id,))

        self._refresh_cache_from_db()
        self._write_json_mirror()
        return True, new_app_id

    def get_stats(self):
        """Returns the currently loaded/cached stats without scanning disk."""
        self._refresh_cache_from_db()
        return self.stats

    def scan_outputs(self):
        """Forces a full scan of the outputs directory to find new applications."""
        self._refresh_cache_from_db()

        if not os.path.exists(self.outputs_dir):
            return self.stats

        updated = False

        # First, validate existing entries and remove deleted ones
        to_remove = []
        for app_id, data in self.stats.items():
            date_folder = data.get('date', '')
            folder_name = data.get('folder_name', data.get('company', '').replace(' ', '_'))
            expected_path = os.path.join(self.outputs_dir, date_folder, folder_name)
            has_manual_edits = bool(
                data.get('manual')
                or data.get('country_manual')
                or data.get('status_manual')
                or (data.get('role_title') or '').strip()
            )

            if not os.path.exists(expected_path) and not has_manual_edits:
                to_remove.append(app_id)
                continue

            # Only try to scan files if the folder actually exists
            if os.path.isdir(expected_path):
                try:
                    files = os.listdir(expected_path)
                    
                    cv_found = any("CV" in f and f.endswith(".pdf") for f in files)
                    current_cv_found = data.get('cv_found', False)
                    if current_cv_found != cv_found:
                        data['cv_found'] = cv_found
                        data['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        updated = True

                    if not data.get('country_manual', False):
                        current_country = data.get('country', 'Unknown')
                        if current_country == "Unknown" or not current_country:
                            found_country = "Unknown"
                            for filename in files:
                                if "CV" in filename and filename.endswith(".pdf"):
                                    suffix = (
                                        filename.replace("Madhav_Manohar_Gopal_CV_", "")
                                        .replace(".pdf", "")
                                        .replace("_", " ")
                                        .lower()
                                    )
                                    for country_name, keywords in COUNTRY_MAP.items():
                                        if any(kw.lower() in suffix for kw in keywords):
                                            found_country = country_name
                                            break
                                    if found_country != "Unknown":
                                        break

                            if found_country != "Unknown" and found_country != current_country:
                                data['country'] = found_country
                                data['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                updated = True
                except Exception as e:
                    logger.warning(f"Error listing folder {expected_path}: {e}")
            else:
                # If folder doesn't exist but we're keeping the record (manual/edited),
                # we just ensure cv_found is False if not manually set.
                if not has_manual_edits and data.get('cv_found'):
                     data['cv_found'] = False
                     updated = True

        for app_id in to_remove:
            self.delete_application(app_id)
            updated = True

        # Scan for new entries
        try:
            folders = os.listdir(self.outputs_dir)
        except Exception as e:
            logger.error(f"Error scanning outputs root: {e}")
            if updated:
                self._save_stats()
            return self.stats

        for date_folder in folders:
            if '-' not in date_folder:
                continue

            date_path = os.path.join(self.outputs_dir, date_folder)
            if not os.path.isdir(date_path):
                continue

            try:
                companies = os.listdir(date_path)
            except Exception as e:
                logger.warning(f"Error listing date folder {date_path}: {e}")
                continue

            for company_folder in companies:
                app_id = f"{date_folder}_{company_folder}"
                if app_id in self._deleted_ids or app_id in self.stats:
                    continue

                company_path = os.path.join(date_path, company_folder)
                if not os.path.isdir(company_path):
                    continue

                cv_found = False
                country = "Unknown"
                try:
                    files = os.listdir(company_path)
                    files.sort(reverse=True)
                    for filename in files:
                        if "CV" in filename and filename.endswith(".pdf"):
                            cv_found = True
                            suffix = (
                                filename.replace("Madhav_Manohar_Gopal_CV_", "")
                                .replace(".pdf", "")
                                .replace("_", " ")
                                .lower()
                            )
                            for country_name, keywords in COUNTRY_MAP.items():
                                if any(kw.lower() in suffix for kw in keywords):
                                    country = country_name
                                    break
                            break
                except Exception as e:
                    logger.warning(f"Error processing files in {company_path}: {e}")

                try:
                    folder_ctime = os.path.getctime(company_path)
                    creation_timestamp = datetime.fromtimestamp(folder_ctime).strftime("%Y-%m-%d %H:%M:%S")
                except Exception as e:
                    logger.debug(f"Could not get ctime for {company_path}: {e}")
                    creation_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                self.stats[app_id] = {
                    "date": date_folder,
                    "company": company_folder.replace("_", " "),
                    "folder_name": company_folder,
                    "country": country,
                    "country_manual": False,
                    "role_title": "",
                    "status": "Unknown",
                    "status_manual": False,
                    "manual": False,
                    "cv_found": cv_found,
                    "last_updated": creation_timestamp
                }
                updated = True

        if updated:
            self._save_stats()
        else:
            self._write_json_mirror()

        return self.stats

    def update_field(self, app_id, field, value):
        self._refresh_cache_from_db()
        if app_id not in self.stats:
            return False

        self.stats[app_id][field] = value
        if field == "country":
            self.stats[app_id]['country_manual'] = True
        if field == "status":
            self.stats[app_id]['status_manual'] = True
        self.stats[app_id]['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self._save_stats()
        return True

    def update_status(self, app_id, value):
        # Compatibility wrapper used by unit tests/legacy callers.
        return self.update_field(app_id, "status", value)

    def delete_application(self, app_id):
        """Delete an application record from stats."""
        with self._db_lock:
            with self.conn:
                self.conn.execute("INSERT OR IGNORE INTO deleted_ids(app_id) VALUES (?)", (app_id,))
                self.conn.execute("DELETE FROM applications WHERE app_id = ?", (app_id,))

        self._refresh_cache_from_db()
        self._write_json_mirror()
        return True

    def get_summary(self):
        self._refresh_cache_from_db()
        total = len(self.stats)
        by_status = {}
        for app in self.stats.values():
            status = app.get("status", "Unknown")
            by_status[status] = by_status.get(status, 0) + 1
        return {
            "total": total,
            "by_status": by_status
        }
