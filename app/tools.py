import json
import logging
from datetime import datetime
from typing import Literal

from langchain_core.tools import tool
from provider_repository import ProviderRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

repo = ProviderRepository()
repo.load()


def make_tools():
    @tool("get_provider_info")
    def get_provider_info(name: str) -> str:
        """Find provider by exact name (e.g., 'Grey, Meredith', 'House, Gregory'). Returns JSON string."""
        logger.info(f"Tool call: get_provider_info(name='{name}')")
        provider = repo.search_by_name(name)
        if not provider:
            return json.dumps({"error": f"Provider '{name}' not found"})
        logger.info(f"Found provider '{name}'")
        return json.dumps({"provider": provider})

    @tool("search_specialty")
    def search_specialty(specialty: str) -> str:
        """Find providers by exact specialty (e.g., 'Orthopedics', 'Primary Care', 'Surgery'). Returns JSON string."""
        logger.info(f"Tool call: search_specialty(specialty='{specialty}')")
        providers = repo.search_by_specialty(specialty)
        logger.info(f"Found {len(providers)} providers for specialty '{specialty}'")
        return json.dumps({"providers": [item.name for item in providers]})

    @tool("provider_availability")
    def provider_availability(provider_name: str) -> str:
        """Get all availability information for a given provider by exact name (e.g., 'Grey, Meredith'). Returns JSON string."""
        logger.info(
            f"Tool call: provider_availability(provider_name='{provider_name}')"
        )
        availability = repo.get_provider_availability(provider_name)
        logger.info(
            f"Found {len(availability)} availability windows for {provider_name}"
        )
        return json.dumps({"provider": provider_name, "availability": availability})

    @tool("specialty_availability")
    def specialty_availability(specialty: str) -> str:
        """Get all availability information for all providers of a given exact specialty (e.g., 'Orthopedics', 'Primary Care'). Returns JSON string."""
        logger.info(f"Tool call: specialty_availability(specialty='{specialty}')")
        availability = repo.get_specialty_availability(specialty)
        logger.info(f"Found {len(availability)} availability windows for {specialty}")
        return json.dumps({"specialty": specialty, "availability": availability})

    @tool("get_current_date")
    def get_current_date() -> str:
        """Get the current date in ISO format"""
        logger.info("Tool call: get_current_date()")
        return datetime.now().strftime("%Y-%m-%d")

    @tool("get_day_of_week")
    def get_day_of_week(date: str) -> str:
        """Get the day of the week for a given date (ISO format)"""
        logger.info(f"Tool call: get_day_of_week(date='{date}')")
        try:
            return datetime.fromisoformat(date).strftime("%A")
        except ValueError:
            raise ValueError("Invalid date format")

    @tool("get_accepted_insurances")
    def get_accepted_insurances() -> str:
        """Get a list of accepted insurances for the hospital"""
        logger.info("Tool call: get_accepted_insurances()")
        return "Accepted insurances: Medicaid, UnitedHealth Care, Blue Cross Blue Shield of North Carolina, Aetna, Cigna"

    @tool("get_self_pay_rates")
    def get_self_pay_rates() -> str:
        """Get a list of self-pay rates for the hospital by specialty (for when insurance is not available)"""
        logger.info("Tool call: get_self_pay_rates()")
        return "Self-pay rates: Primary Care: $150, Orthopedics: $300, Surgery: $1000"

    @tool("book_appointment")
    def book_appointment(
        patient_name: str,
        provider_name: str,
        location: str,
        date: str,
        time: str,
        appointment_type: Literal["NEW", "ESTABLISHED"] = None,
    ) -> str:
        """Book an appointment (only called once user confirms proposed appointment details given by system)"""
        logger.info(
            f"Tool call: book_appointment(patient_name='{patient_name}', provider_name='{provider_name}', location='{location}', date='{date}', time='{time}', appointment_type='{appointment_type}')"
        )
        try:

            # Validate provider name
            p = repo.search_by_name(provider_name)
            if not p:
                return json.dumps({"success": False, "error": "Provider not found, please try again"})

            # Schedule the appointment (mock implementation)
            if appointment_type == "ESTABLISHED":
                duration = 15
                arrival = "10 minutes early"
            else:
                appointment_type = "NEW"
                duration = 30
                arrival = "30 minutes early"
            logger.info(
                f"Successfully scheduled {appointment_type} appointment for patient {patient_name} with {provider_name}"
            )

            return json.dumps(
                {
                    "success": True,
                    "appointment": {
                        "patient_name": patient_name,
                        "provider_name": provider_name,
                        "location": location,
                        "date": date,
                        "time": time,
                        "type": appointment_type,
                        "duration_minutes": duration,
                        "arrival_instruction": f"Please arrive {arrival}",
                    },
                }
            )

        except Exception as e:
            logger.error(f"Error scheduling appointment: {e}")
            return json.dumps({"success": False, "error": str(e)})

    return [
        get_provider_info,
        search_specialty,
        provider_availability,
        specialty_availability,
        book_appointment,
        get_current_date,
        get_day_of_week,
        get_accepted_insurances,
        get_self_pay_rates,
    ]


tools = make_tools()
