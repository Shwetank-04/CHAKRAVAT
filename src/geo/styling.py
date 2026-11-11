"""CHAKRAVAT Geospatial Styling & Meteorological Scales.

Authoritative North Indian Ocean (NIO) geographic boundaries,
Plotly offline cartographic dark palette tokens (#101820),
and India Meteorological Department (IMD) 8-tier category color scales.
"""

from typing import Any, Dict, Final, List, Optional, Union

# ---------------------------------------------------------------------------
# 1. North Indian Ocean (NIO) Geographic Boundaries & Off-grid Basemap Styles
# ---------------------------------------------------------------------------

GEO_BOUNDS: Final[Dict[str, Any]] = {
    "center": {"lat": 15.25, "lon": 75.0},   # midpoint of the two ranges below (was 80E, which shifted the view east)
    "lataxis_range": [2.0, 28.5],    # 2°N (Equator / Sri Lanka) to 28.5°N (Bengal / Gujarat)
    "lonaxis_range": [52.0, 98.0],   # 52°E (Arabian Sea / Gulf of Aden) to 98°E (Andaman / Myanmar)
    "projection_type": "mercator",
    "theme_palette": {
        "bg_color": "#101820",        # Deep navy/charcoal base
        "ocean_color": "#0a1118",     # Deep oceanic abyss
        "land_color": "#16222f",      # Dark slate landmass
        "coastline_color": "#385170", # Muted teal-blue coastline
        "country_color": "#233342",   # Subtle territorial borders
        "grid_color": "#1b2836",      # Coordinate latitude/longitude graticule
        "lake_color": "#0a1118",      # Water bodies match ocean
        "river_color": "#1b2836",     # Muted inland waterways
        "text_color": "#F1F5F9",      # High-contrast readable typography
        "card_bg": "#17222D",         # Dark surface card container
        "border_color": "#2C4056",    # Slate component outline
    },
}

# ---------------------------------------------------------------------------
# 2. IMD 8-Tier Cyclone Intensity Scale & Visual Encoding
# ---------------------------------------------------------------------------

IMD_CATEGORIES: Final[Dict[str, Dict[str, Any]]] = {
    "LPA": {
        "code": "LPA",
        "name": "Low Pressure Area",
        "min_kts": 0.0,
        "max_kts": 16.9,
        "min_kmh": 0.0,
        "max_kmh": 31.0,
        "color": "#94A3B8",           # Slate Grey
        "symbol": "circle",
        "size": 7,
        "description": "Well-marked low pressure area with sustained winds < 17 kts",
    },
    "D": {
        "code": "D",
        "name": "Depression",
        "min_kts": 17.0,
        "max_kts": 27.9,
        "min_kmh": 31.0,
        "max_kmh": 49.0,
        "color": "#4FC3F7",           # Light Cyan / Sky Blue
        "symbol": "circle",
        "size": 8,
        "description": "Depression with sustained winds 17–27 kts (31–49 km/h)",
    },
    "DD": {
        "code": "DD",
        "name": "Deep Depression",
        "min_kts": 28.0,
        "max_kts": 33.9,
        "min_kmh": 50.0,
        "max_kmh": 61.0,
        "color": "#29B6F6",           # Vibrant Azure
        "symbol": "circle",
        "size": 9,
        "description": "Deep depression with sustained winds 28–33 kts (50–61 km/h)",
    },
    "CS": {
        "code": "CS",
        "name": "Cyclonic Storm",
        "min_kts": 34.0,
        "max_kts": 47.9,
        "min_kmh": 62.0,
        "max_kmh": 88.0,
        "color": "#00E5FF",           # Electric Turquoise
        "symbol": "circle",
        "size": 10,
        "description": "Cyclonic storm with sustained winds 34–47 kts (62–88 km/h)",
    },
    "SCS": {
        "code": "SCS",
        "name": "Severe Cyclonic Storm",
        "min_kts": 48.0,
        "max_kts": 63.9,
        "min_kmh": 89.0,
        "max_kmh": 117.0,
        "color": "#FFD54F",           # Warning Amber
        "symbol": "diamond",
        "size": 11,
        "description": "Severe cyclonic storm with sustained winds 48–63 kts (89–117 km/h)",
    },
    "VSCS": {
        "code": "VSCS",
        "name": "Very Severe Cyclonic Storm",
        "min_kts": 64.0,
        "max_kts": 89.9,
        "min_kmh": 118.0,
        "max_kmh": 165.0,
        "color": "#FF9100",           # Alert Orange
        "symbol": "diamond",
        "size": 12,
        "description": "Very severe cyclonic storm with sustained winds 64–89 kts (118–165 km/h)",
    },
    "ESCS": {
        "code": "ESCS",
        "name": "Extremely Severe Cyclonic Storm",
        "min_kts": 90.0,
        "max_kts": 119.9,
        "min_kmh": 166.0,
        "max_kmh": 221.0,
        "color": "#FF3D00",           # Danger Crimson
        "symbol": "square",
        "size": 14,
        "description": "Extremely severe cyclonic storm with sustained winds 90–119 kts (166–221 km/h)",
    },
    "SuCS": {
        "code": "SuCS",
        "name": "Super Cyclonic Storm",
        "min_kts": 120.0,
        "max_kts": 250.0,
        "min_kmh": 222.0,
        "max_kmh": 460.0,
        "color": "#D500F9",           # Extreme Magenta / Violet
        "symbol": "star",
        "size": 16,
        "description": "Catastrophic super cyclonic storm with sustained winds >= 120 kts (>= 222 km/h)",
    },
}

# Alias map for tolerant lookup
_CATEGORY_ALIAS_MAP: Final[Dict[str, str]] = {
    "lpa": "LPA",
    "low pressure": "LPA",
    "low pressure area": "LPA",
    "d": "D",
    "depression": "D",
    "dd": "DD",
    "deep depression": "DD",
    "cs": "CS",
    "cyclonic storm": "CS",
    "scs": "SCS",
    "severe cyclonic storm": "SCS",
    "vscs": "VSCS",
    "very severe cyclonic storm": "VSCS",
    "escs": "ESCS",
    "extremely severe cyclonic storm": "ESCS",
    "sucs": "SuCS",
    "super cyclonic storm": "SuCS",
    "super cyclone": "SuCS",
}

# ---------------------------------------------------------------------------
# 3. Storm Distinct Colors (Multi-storm comparative overview)
# ---------------------------------------------------------------------------

STORM_COLOR_PALETTE: Final[Dict[str, str]] = {
    "BIPARJOY": "#FF3D00",  # Coral Crimson
    "AMPHAN": "#D500F9",    # Magenta Violet
    "FANI": "#00E5FF",      # Electric Cyan
    "TAUKTAE": "#FF9100",   # Amber Orange
    "YAAS": "#A78BFA",      # Lavender Violet
    "TITLI": "#FFD54F",     # Sun Amber
    "OCKHI": "#4FC3F7",     # Sky Blue
    "ASANI": "#34D399",     # Mint Emerald
}

_FALLBACK_STORM_COLORS: Final[List[str]] = [
    "#00E5FF", "#D500F9", "#FF9100", "#FF3D00",
    "#34D399", "#A78BFA", "#FFD54F", "#4FC3F7",
]


# ---------------------------------------------------------------------------
# 4. Helper Functions
# ---------------------------------------------------------------------------

def classify_imd_category(wind_kts: float) -> str:
    """Classify wind speed in knots into canonical IMD category code."""
    if wind_kts < 17.0:
        return "LPA"
    elif wind_kts < 28.0:
        return "D"
    elif wind_kts < 34.0:
        return "DD"
    elif wind_kts < 48.0:
        return "CS"
    elif wind_kts < 64.0:
        return "SCS"
    elif wind_kts < 90.0:
        return "VSCS"
    elif wind_kts < 120.0:
        return "ESCS"
    else:
        return "SuCS"


def get_category_style(category_or_wind: Union[str, float, int]) -> Dict[str, Any]:
    """Retrieve full category styling dict given a name, code, or wind speed."""
    if isinstance(category_or_wind, (int, float)):
        code = classify_imd_category(float(category_or_wind))
        return IMD_CATEGORIES[code]

    raw_str = str(category_or_wind).strip().lower()
    code = _CATEGORY_ALIAS_MAP.get(raw_str, "CS")
    return IMD_CATEGORIES.get(code, IMD_CATEGORIES["CS"])


def get_category_color(category_or_wind: Union[str, float, int]) -> str:
    """Retrieve hex color code for category or wind speed."""
    return get_category_style(category_or_wind)["color"]


def get_storm_color(storm_name_or_id: str) -> str:
    """Retrieve distinct signature color for a storm, with deterministic hash fallback."""
    clean_name = storm_name_or_id.strip().upper()
    for key, color in STORM_COLOR_PALETTE.items():
        if key in clean_name:
            return color
    idx = abs(hash(storm_name_or_id)) % len(_FALLBACK_STORM_COLORS)
    return _FALLBACK_STORM_COLORS[idx]


def get_imd_legend_items() -> List[Dict[str, Any]]:
    """Return an ordered list of IMD categories for legend displays."""
    order = ["D", "DD", "CS", "SCS", "VSCS", "ESCS", "SuCS"]
    return [IMD_CATEGORIES[code] for code in order]
