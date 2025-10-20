from kmd_institution_client.client import KMDInstitutionClient
from typing import Optional
import re

class IndmeldelserClient:
    def __init__(self, kmd_client: KMDInstitutionClient, brugerid: str | None) -> None:
        self.client = kmd_client
        self.brugerid = brugerid

    

    def find_indmeldelser(self, institution: dict, udmeldelsesdato_fra: Optional[str] = None, udmeldelsesdato_til: Optional[str] = None) -> Optional[dict]:
        endpoint = "https://institution.kmd.dk/api/bookings/search"
        
        # Formater datoer
        if udmeldelsesdato_fra:
            udmeldelsesdato_fra = self._formater_date(udmeldelsesdato_fra)
        if udmeldelsesdato_til:
            udmeldelsesdato_til = self._formater_date(udmeldelsesdato_til)
        
        body = {
            "ageGroups": [],
            "fromDate": None,
            "institutionsAndGroups": [{
                "groupInstitutions": None,
                "institution": institution,
                "isActive": True
            }],
            "modules": [],
            "municipalityId": self.brugerid,
            "periodSearchType": 1,
            "relativeDateDays": 100,
            "relativeDateType": 2,
            "showDeleted": False,
            "showInModules": False,
            "showInAgeGroups": False,
            "toDate": None,
            "includeInstitutionsActiveInSelectedYear": False,
            "year": 0,
            "institutionSearchType": 19,
            "moduleSearchType": 1,
            "additionsAndDeductions": [],
            "bookingId": 0,
            "childAge": {
                "ageFrom": None,
                "agePerDate": None,
                "ageTo": None,
                "birthDateFrom": None,
                "birthDateTo": None,
                "childAgeSearchType": 0
            },
            "conditions": [],
            "includeActiveOffers": False,
            "includeBookings": True,
            "includeCompletedOffers": False,
            "includeEnrollmentsWithoutEnrollmentInNextAgeGroup": False,
            "includeEnrollmentsWithoutWishInNextAgeGroup": False,
            "includeExceededOffers": False,
            "includeInstitutionsMunicipality": True,
            "includeResidenceMunicipality": True,
            "includeSimulatedWishes": False,
            "schoolDistricts": [],
            "grades": [],
            "showOnlyActiveEnrollments": False,
            "sortBy": 0,
            "subsidy": {
                "endDateFrom": None,
                "endDateTo": None,
                "socialPedagogical": False,
                "startDateFrom": None,
                "startDateTo": None,
                "treatment": False
            },
            "withdrawalDateFrom": udmeldelsesdato_fra,
            "withdrawalDateTo": udmeldelsesdato_til
        }

        response = self.client.post(endpoint, json=body)
        return response.json()
    

    def _formater_date(self, date_str: str) -> str:
        """
        Format date string to YYYY-MM-DDTHH:MM:SS format.
        Supports multiple input formats and converts them automatically.
        
        :param date_str: Date string to format
        :return: Properly formatted date string in YYYY-MM-DDTHH:MM:SS format
        :raises ValueError: If date format cannot be parsed
        """
        if not date_str:
            return date_str
            
        # Already in correct format YYYY-MM-DDTHH:MM:SS
        full_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$'
        if re.match(full_pattern, date_str):
            return date_str
        
        # YYYY-MM-DD format - add time
        iso_date_pattern = r'^\d{4}-\d{2}-\d{2}$'
        if re.match(iso_date_pattern, date_str):
            return f"{date_str}T00:00:00"
        
        # DD-MM-YYYY format - convert to YYYY-MM-DD and add time
        dd_mm_yyyy_pattern = r'^(\d{2})-(\d{2})-(\d{4})$'
        match = re.match(dd_mm_yyyy_pattern, date_str)
        if match:
            day, month, year = match.groups()
            return f"{year}-{month}-{day}T00:00:00"
        
        # DD/MM/YYYY format - convert to YYYY-MM-DD and add time
        dd_mm_yyyy_slash_pattern = r'^(\d{2})/(\d{2})/(\d{4})$'
        match = re.match(dd_mm_yyyy_slash_pattern, date_str)
        if match:
            day, month, year = match.groups()
            return f"{year}-{month}-{day}T00:00:00"
            
        raise ValueError(f"Date '{date_str}' format not recognized. Supported formats: YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY, YYYY-MM-DDTHH:MM:SS")