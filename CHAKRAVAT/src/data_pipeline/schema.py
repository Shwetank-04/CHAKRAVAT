"""
Canonical Data Schema & Meteorological Constants for CHAKRAVAT.
Fulfills Requirements R3 & R5 with strict North Indian Ocean (NIO) domain rules.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List

# North Indian Ocean (NIO) Domain Bounds
MIN_LATITUDE = 0.0
MAX_LATITUDE = 35.0
MIN_LONGITUDE = 50.0
MAX_LONGITUDE = 105.0

# Physical Parameter Bounds
MIN_WIND_SPEED_KTS = 0.1
MAX_WIND_SPEED_KTS = 200.0
MIN_CENTRAL_PRESSURE_HPA = 850.0
MAX_CENTRAL_PRESSURE_HPA = 1035.0
ENVIRONMENTAL_PRESSURE_HPA = 1010.0

# IMD 8-Tier Classification Scale (RSMC New Delhi standard)
IMD_CATEGORIES: Dict[str, Dict[str, Any]] = {
    "LPA": {
        "code": "LPA",
        "name": "Low Pressure Area",
        "min_kts": 0.0,
        "max_kts": 16.9,
        "min_kmh": 0.0,
        "max_kmh": 31.0,
        "color": "#718096",
        "description": "Well-marked low pressure with winds < 17 kts",
    },
    "D": {
        "code": "D",
        "name": "Depression",
        "min_kts": 17.0,
        "max_kts": 27.9,
        "min_kmh": 31.0,
        "max_kmh": 49.0,
        "color": "#4299E1",
        "description": "Depression with sustained winds 17–27 kts",
    },
    "DD": {
        "code": "DD",
        "name": "Deep Depression",
        "min_kts": 28.0,
        "max_kts": 33.9,
        "min_kmh": 50.0,
        "max_kmh": 61.0,
        "color": "#38B2AC",
        "description": "Deep depression with sustained winds 28–33 kts",
    },
    "CS": {
        "code": "CS",
        "name": "Cyclonic Storm",
        "min_kts": 34.0,
        "max_kts": 47.9,
        "min_kmh": 62.0,
        "max_kmh": 88.0,
        "color": "#ECC94B",
        "description": "Cyclonic storm with sustained winds 34–47 kts",
    },
    "SCS": {
        "code": "SCS",
        "name": "Severe Cyclonic Storm",
        "min_kts": 48.0,
        "max_kts": 63.9,
        "min_kmh": 89.0,
        "max_kmh": 117.0,
        "color": "#ED8936",
        "description": "Severe cyclonic storm with sustained winds 48–63 kts",
    },
    "VSCS": {
        "code": "VSCS",
        "name": "Very Severe Cyclonic Storm",
        "min_kts": 64.0,
        "max_kts": 89.9,
        "min_kmh": 118.0,
        "max_kmh": 166.0,
        "color": "#E53E3E",
        "description": "Very severe cyclonic storm with sustained winds 64–89 kts",
    },
    "ESCS": {
        "code": "ESCS",
        "name": "Extremely Severe Cyclonic Storm",
        "min_kts": 90.0,
        "max_kts": 119.9,
        "min_kmh": 167.0,
        "max_kmh": 221.0,
        "color": "#9B2C2C",
        "description": "Extremely severe cyclonic storm with sustained winds 90–119 kts",
    },
    "SuCS": {
        "code": "SuCS",
        "name": "Super Cyclonic Storm",
        "min_kts": 120.0,
        "max_kts": 999.0,
        "min_kmh": 222.0,
        "max_kmh": 999.0,
        "color": "#805AD5",
        "description": "Catastrophic super cyclonic storm with sustained winds >= 120 kts",
    },
}


def classify_imd_intensity(wind_speed_kts: float) -> str:
    """Classifies wind speed (in knots) into the authoritative IMD intensity tier."""
    if wind_speed_kts < 17.0:
        return "LPA"
    elif wind_speed_kts < 28.0:
        return "D"
    elif wind_speed_kts < 34.0:
        return "DD"
    elif wind_speed_kts < 48.0:
        return "CS"
    elif wind_speed_kts < 64.0:
        return "SCS"
    elif wind_speed_kts < 90.0:
        return "VSCS"
    elif wind_speed_kts < 120.0:
        return "ESCS"
    else:
        return "SuCS"


@dataclass(frozen=True)
class CycloneFix:
    """
    Immutable representation of an authentic synoptic cyclone observation fix.
    Conforms to the 18 canonical columns of IBTrACS v04 / IMD RSMC New Delhi.
    """
    record_id: str
    storm_id: str
    storm_name: str
    iso_time: str
    basin: str
    latitude: float
    longitude: float
    wind_speed_kts: float
    wind_speed_kmh: float
    central_pressure_hpa: float
    pressure_drop_hpa: float
    nature_code: str
    imd_category: str
    translation_speed_kts: float
    translation_heading_deg: float
    is_landfall: bool
    data_source: str
    quality_flag: str

    def validate(self) -> List[str]:
        """Validates meteorological and geographic constraints. Returns list of error messages."""
        errors: List[str] = []

        if not (MIN_LATITUDE <= self.latitude <= MAX_LATITUDE):
            errors.append(f"Latitude {self.latitude:.2f}° outside NIO bounds [{MIN_LATITUDE}, {MAX_LATITUDE}]")

        if not (MIN_LONGITUDE <= self.longitude <= MAX_LONGITUDE):
            errors.append(f"Longitude {self.longitude:.2f}° outside NIO bounds [{MIN_LONGITUDE}, {MAX_LONGITUDE}]")

        if self.wind_speed_kts <= 0:
            errors.append(f"Wind speed {self.wind_speed_kts} kts must be strictly positive")

        if not (MIN_CENTRAL_PRESSURE_HPA <= self.central_pressure_hpa <= MAX_CENTRAL_PRESSURE_HPA):
            errors.append(
                f"Central pressure {self.central_pressure_hpa} hPa outside physical bounds [{MIN_CENTRAL_PRESSURE_HPA}, {MAX_CENTRAL_PRESSURE_HPA}]"
            )

        return errors

    @property
    def is_valid(self) -> bool:
        return len(self.validate()) == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "storm_id": self.storm_id,
            "storm_name": self.storm_name,
            "iso_time": self.iso_time,
            "basin": self.basin,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "wind_speed_kts": self.wind_speed_kts,
            "wind_speed_kmh": self.wind_speed_kmh,
            "central_pressure_hpa": self.central_pressure_hpa,
            "pressure_drop_hpa": self.pressure_drop_hpa,
            "nature_code": self.nature_code,
            "imd_category": self.imd_category,
            "translation_speed_kts": self.translation_speed_kts,
            "translation_heading_deg": self.translation_heading_deg,
            "is_landfall": self.is_landfall,
            "data_source": self.data_source,
            "quality_flag": self.quality_flag,
        }
