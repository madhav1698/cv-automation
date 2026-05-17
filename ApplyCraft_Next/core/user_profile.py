import json
import os
import re
from dataclasses import asdict, dataclass


@dataclass
class UserProfile:
    full_name: str = "Candidate"
    current_location: str = ""
    template_1: str = "templates/Madhav_Manohar Gopal_CV.docx"
    template_2: str = "templates/Madhav_Manohar_Gopal_CV_2.docx"

    @property
    def slug(self) -> str:
        """Safe filename slug for candidate-specific output names."""
        slug = re.sub(r"[^A-Za-z0-9_-]+", "_", (self.full_name or "Candidate").strip())
        slug = re.sub(r"_+", "_", slug).strip("_")
        return slug or "Candidate"


class UserProfileStore:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.path = os.path.join(base_dir, "user_profile.json")

    def load(self) -> UserProfile:
        defaults = asdict(UserProfile())

        if not os.path.exists(self.path):
            profile = UserProfile(**defaults)
            self.save(profile)
            return profile

        with open(self.path, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        # Only accept known keys to avoid crashes on stale/invalid profile files.
        filtered = {k: loaded.get(k, v) for k, v in defaults.items()} if isinstance(loaded, dict) else defaults
        return UserProfile(**filtered)

    def save(self, profile: UserProfile):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(asdict(profile), f, indent=2)
