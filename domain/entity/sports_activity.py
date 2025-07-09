from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SportsActivity:
    id: int
    user_id: int
    activity_name: str
    activity_type: str
    skills_req: str
    date: str  # or use datetime if parsed
    location: str
    max_pax: int
    user_id_list_join: Optional[str] = field(default=None)

    # --- Getters ---
    def get_id(self):
        return self.id

    def get_user_id(self):
        return self.user_id

    def get_activity_name(self):
        return self.activity_name

    def get_activity_type(self):
        return self.activity_type

    def get_skills_req(self):
        return self.skills_req

    def get_date(self):
        return self.date

    def get_location(self):
        return self.location

    def get_max_pax(self):
        return self.max_pax

    def get_user_id_list_join(self):
        return self.user_id_list_join

    # --- Setters ---
    def set_user_id(self, user_id: int):
        self.user_id = user_id

    def set_activity_name(self, activity_name: str):
        self.activity_name = activity_name

    def set_activity_type(self, activity_type: str):
        self.activity_type = activity_type

    def set_skills_req(self, skills_req: str):
        self.skills_req = skills_req

    def set_date(self, date: str):
        self.date = date

    def set_location(self, location: str):
        self.location = location

    def set_max_pax(self, max_pax: int):
        self.max_pax = max_pax

    def set_user_id_list_join(self, user_id):
        existing = self.user_id_list_join or ""
        ids = existing.split(",") if existing else []

        if str(user_id) not in ids:
            ids.append(str(user_id))
        self.user_id_list_join = ",".join(filter(None, ids))
