import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import Levenshtein as levenshtein

from models import Department, Provider

class ProviderRepository:
    def __init__(self):
        self.json_path = Path(__file__).parent / "data" / "providers.json"
        self.providers: List[Provider] = []

    def load(self):
        data = json.loads(self.json_path.read_text(encoding="utf-8"))
        providers = []
        for item in data:
            depts = [Department(**d) for d in item.get("departments", [])]
            providers.append(
                Provider(
                    name=item.get("name", ""),
                    certification=item.get("certification"),
                    specialty=item.get("specialty"),
                    departments=depts,
                )
            )
        self.providers = providers

    def search_by_specialty(self, specialty: str) -> List[Provider]:
        target = specialty.strip().lower()
        return [p for p in self.providers if (p.specialty or "").lower() == target]

    def search_by_name(self, name: str) -> Optional[Provider]:
        target = name.strip().lower()
        for p in self.providers:
            if p.name.strip().lower() == target:
                return p
            else:
                # Search by name via Levenshtein ratio and return closest match
                ratios = [(p, levenshtein.ratio(name, p.name)) for p in self.providers]
                ratios.sort(key=lambda x: x[1], reverse=True)
                if ratios[0][1] >= 0.4:
                    return ratios[0][0]
        return None

    def get_provider_availability(self, provider_name: str) -> List[Dict[str, Any]]:
        provider = self.search_by_name(provider_name)
        if not provider:
            return []
        availability = []
        for dept in provider.departments:
            availability.append(
                {
                    "location": dept.name,
                    "days_available": dept.days,
                    "hours_available": dept.hours,
                }
            )
        return availability

    def get_specialty_availability(self, specialty: str) -> List[Dict[str, Any]]:
        providers = self.search_by_specialty(specialty)
        if not providers:
            return []
        availability = []
        for p in providers:
            for dept in p.departments:
                availability.append(
                    {
                        "provider": p.name,
                        "location": dept.name,
                        "days_available": dept.days,
                        "hours_available": dept.hours,
                    }
                )
        return availability

    def get_provider_availability_on_day(
        self, provider_name: str, day_of_week: str
    ) -> List[Dict[str, Any]]:
        provider = self.search_by_name(provider_name)
        if not provider:
            return []
        availability = []
        for dept in provider.departments:
            if day_of_week in dept.days:
                availability.append(
                    {"location": dept.name, "hours_available": dept.hours}
                )
        return availability

    def get_specialty_availability_on_day(
        self, specialty: str, day_of_week: str
    ) -> List[Dict[str, Any]]:
        providers = self.search_by_specialty(specialty)
        if not providers:
            return []
        availability = []
        for p in providers:
            for dept in p.departments:
                if day_of_week in dept.days:
                    availability.append(
                        {
                            "provider": p.name,
                            "location": dept.name,
                            "hours_available": dept.hours,
                        }
                    )
        return availability
