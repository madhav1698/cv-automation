import os
import json
from datetime import datetime

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
        self.stats = self._load_stats()

    def _load_stats(self):
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
                
                # Migrate old entries
                needs_save = False
                for app_id, data in stats.items():
                    updated_entry = False
                    if 'last_updated' not in data:
                        data['last_updated'] = "2000-01-01 00:00:00"
                        updated_entry = True
                    
                    if 'folder_name' not in data:
                        # Derive folder name from company if missing
                        data['folder_name'] = data.get('company', '').replace(' ', '_')
                        updated_entry = True
                    
                    if updated_entry:
                        needs_save = True
                
                if needs_save:
                    self.stats = stats # Need to set self.stats before calling _save_stats if we used it, but here we return it
                    self._save_stats()
                
                return stats
            except:
                return {}
        return {}

    def _save_stats(self):
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=4)

    def add_application(self, date_str, company, country, status="Unknown"):
        """Explicitly adds an application to the stats, avoiding the need for a full scan."""
        company_clean = "".join(c for c in company.replace(" ", "_") if c.isalnum() or c in ("_", "-"))
        app_id = f"{date_str}_{company_clean}"
        
        self.stats[app_id] = {
            "date": date_str,
            "company": company.replace("_", " "),
            "folder_name": company.replace(" ", "_"), # Store original folder name
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
            # Use folder_name if available, fallback to company
            folder_name = data.get('folder_name', data.get('company', '').replace(' ', '_'))
            
            # Check if the folder still exists
            expected_path = os.path.join(self.outputs_dir, date_folder, folder_name)
            if not os.path.exists(expected_path):
                to_remove.append(app_id)
            else:
                # Refresh data from filesystem, but DON'T overwrite manual edits
                try:
                    # Sync CV existence (this is factual)
                    files = os.listdir(expected_path)
                    cv_found = any("CV" in f and f.endswith(".pdf") for f in files)
                    
                    if data.get('cv_found') != cv_found:
                        data['cv_found'] = cv_found
                        updated = True

                    # Try to detect country ONLY if currently Unknown
                    if data.get('country') == "Unknown" or not data.get('country'):
                        found_country = "Unknown"
                        for filename in files:
                            if "CV" in filename and filename.endswith(".pdf"):
                                suffix = filename.replace("Madhav_Manohar_Gopal_CV_", "").replace(".pdf", "").replace("_", " ").lower()
                                for country_name, keywords in COUNTRY_MAP.items():
                                    if any(kw.lower() in suffix for kw in keywords):
                                        found_country = country_name
                                        break
                                if found_country != "Unknown": break
                        
                        if found_country != "Unknown":
                            data['country'] = found_country
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

                cv_found = False
                country = "Unknown"
                try:
                    files = os.listdir(company_path)
                    # Sort files so we prioritize PDF over docx if both exist
                    files.sort(reverse=True) 
                    
                    for filename in files:
                        if "CV" in filename and filename.endswith(".pdf"):
                            cv_found = True
                            suffix = filename.replace("Madhav_Manohar_Gopal_CV_", "").replace(".pdf", "").replace("_", " ").lower()
                            
                            for country_name, keywords in COUNTRY_MAP.items():
                                match_found = False
                                for kw in keywords:
                                    if kw.lower() in suffix:
                                        country = country_name
                                        match_found = True
                                        break
                                if match_found: break
                            break
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
                    "folder_name": company_folder, # Store the actual folder name
                    "country": country,
                    "status": "Unknown",
                    "cv_found": cv_found,
                    "last_updated": creation_timestamp  # Use folder creation time
                }
                updated = True
        
        if updated:
            self._save_stats()
        
        return self.stats

    def update_field(self, app_id, field, value):
        if app_id in self.stats:
            self.stats[app_id][field] = value
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
