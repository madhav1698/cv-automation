import os
import json
from datetime import datetime

class StatsManager:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.outputs_dir = os.path.join(base_dir, "outputs")
        self.stats_file = os.path.join(base_dir, "application_stats.json")
        self.stats = self._load_stats()

    def _load_stats(self):
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r') as f:
                    stats = json.load(f)
                
                # Migrate old entries: add last_updated if missing
                needs_save = False
                for app_id, data in stats.items():
                    if 'last_updated' not in data:
                        # Use a very old timestamp for legacy entries so they appear last
                        data['last_updated'] = "2000-01-01 00:00:00"
                        needs_save = True
                
                if needs_save:
                    with open(self.stats_file, 'w') as f:
                        json.dump(stats, f, indent=4)
                
                return stats
            except:
                return {}
        return {}

    def _save_stats(self):
        with open(self.stats_file, 'w') as f:
            json.dump(self.stats, f, indent=4)

    def add_application(self, date_str, company, country, status="Unknown"):
        """Explicitly adds an application to the stats, avoiding the need for a full scan."""
        company_clean = "".join(c for c in company.replace(" ", "_") if c.isalnum() or c in ("_", "-"))
        app_id = f"{date_str}_{company_clean}"
        
        self.stats[app_id] = {
            "date": date_str,
            "company": company.replace("_", " "),
            "country": country,
            "status": status,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self._save_stats()
        return app_id

    def get_stats(self):
        """Returns the currently loaded/cached stats without scanning disk."""
        return self.stats

    def scan_outputs(self):
        """Forces a full scan of the outputs directory to find new applications."""
        if not os.path.exists(self.outputs_dir):
            return self.stats

        updated = False
        
        # First, validate existing entries and remove deleted ones
        to_remove = []
        for app_id, data in self.stats.items():
            date_folder = data.get('date', '')
            company = data.get('company', '').replace(' ', '_')
            
            # Check if the folder still exists
            expected_path = os.path.join(self.outputs_dir, date_folder, company)
            if not os.path.exists(expected_path):
                to_remove.append(app_id)
            else:
                # ALWAYS refresh timestamp from filesystem to fix any corrupted timestamps
                try:
                    folder_ctime = os.path.getctime(expected_path)
                    correct_timestamp = datetime.fromtimestamp(folder_ctime).strftime("%Y-%m-%d %H:%M:%S")
                    if data.get('last_updated') != correct_timestamp:
                        data['last_updated'] = correct_timestamp
                        updated = True
                except:
                    pass
        
        # Remove deleted entries
        for app_id in to_remove:
            del self.stats[app_id]
            updated = True
        
        # Now scan for new entries
        try:
            folders = os.listdir(self.outputs_dir)
        except:
            if updated:
                self._save_stats()
            return self.stats

        for date_folder in folders:
            if '-' not in date_folder: continue
            
            date_path = os.path.join(self.outputs_dir, date_folder)
            if not os.path.isdir(date_path): continue

            try:
                companies = os.listdir(date_path)
            except: continue

            for company_folder in companies:
                app_id = f"{date_folder}_{company_folder}"
                if app_id in self.stats:
                    continue
                
                company_path = os.path.join(date_path, company_folder)
                if not os.path.isdir(company_path): continue

                country = "Unknown"
                try:
                    files = os.listdir(company_path)
                    for filename in files:
                        if filename.startswith("Madhav_Manohar_Gopal_CV_") and filename.endswith(".pdf"):
                            parts = filename.replace("Madhav_Manohar_Gopal_CV_", "").replace(".pdf", "").split("_")
                            if len(parts) > 1:
                                potential_country = parts[-1]
                                if potential_country.lower() != company_folder.lower():
                                    country = potential_country.replace("_", " ")
                except:
                    pass

                # Get folder creation time from filesystem
                try:
                    folder_ctime = os.path.getctime(company_path)
                    creation_timestamp = datetime.fromtimestamp(folder_ctime).strftime("%Y-%m-%d %H:%M:%S")
                except:
                    creation_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                self.stats[app_id] = {
                    "date": date_folder,
                    "company": company_folder.replace("_", " "),
                    "country": country,
                    "status": "Unknown",
                    "last_updated": creation_timestamp  # Use folder creation time
                }
                updated = True
        
        if updated:
            self._save_stats()
        
        return self.stats

    def update_status(self, app_id, new_status):
        if app_id in self.stats:
            self.stats[app_id]["status"] = new_status
            # Don't update last_updated - keep original folder creation time for sorting
            self._save_stats()
            return True
        return False

    def get_summary(self):
        total = len(self.stats)
        by_status = {}
        for app in self.stats.values():
            status = app["status"]
            by_status[status] = by_status.get(status, 0) + 1
        return {
            "total": total,
            "by_status": by_status
        }
