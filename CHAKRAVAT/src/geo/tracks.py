"""CHAKRAVAT Cyclone Tracks & Waypoint Telemetry.

Processes raw synoptic fixes into structured tracks, calculates
meteorological extrema, computes geodesic distances, and builds
rich multi-line telemetry hovercards.
"""

from dataclasses import dataclass, field
from datetime import datetime
import math
import os
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd

from src.geo.styling import (
    classify_imd_category,
    get_category_color,
    get_category_style,
    get_storm_color,
)


@dataclass
class CycloneWaypoint:
    """A single synoptic observation fix along a cyclone trajectory."""

    timestamp_utc: str
    lat: float
    lon: float
    wind_kts: float
    wind_kmh: float
    pressure_mb: float
    category: str
    category_code: str
    category_color: str
    movement_dir_deg: Optional[float] = None
    movement_speed_kph: Optional[float] = None
    dist_coast_km: Optional[float] = None
    data_source: str = "IBTrACS"
    is_landfall: bool = False
    hover_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert waypoint to flat dictionary."""
        return {
            "timestamp_utc": self.timestamp_utc,
            "lat": self.lat,
            "lon": self.lon,
            "wind_kts": self.wind_kts,
            "wind_kmh": self.wind_kmh,
            "pressure_mb": self.pressure_mb,
            "category": self.category,
            "category_code": self.category_code,
            "category_color": self.category_color,
            "movement_dir_deg": self.movement_dir_deg,
            "movement_speed_kph": self.movement_speed_kph,
            "dist_coast_km": self.dist_coast_km,
            "data_source": self.data_source,
            "is_landfall": self.is_landfall,
        }


@dataclass
class CycloneTrack:
    """Full chronological trajectory and telemetry for a tropical cyclone."""

    storm_id: str
    storm_name: str
    basin: str  # 'AS' (Arabian Sea) or 'BOB' (Bay of Bengal)
    waypoints: List[CycloneWaypoint] = field(default_factory=list)
    signature_color: str = "#00E5FF"

    @property
    def peak_wind_kts(self) -> float:
        """Maximum sustained wind speed in knots."""
        if not self.waypoints:
            return 0.0
        return max(wp.wind_kts for wp in self.waypoints)

    @property
    def peak_wind_kmh(self) -> float:
        """Maximum sustained wind speed in km/h."""
        return round(self.peak_wind_kts * 1.852, 1)

    @property
    def min_pressure_mb(self) -> float:
        """Minimum central pressure in millibars / hPa."""
        if not self.waypoints:
            return 1010.0
        return min(wp.pressure_mb for wp in self.waypoints)

    @property
    def max_category_code(self) -> str:
        """Peak IMD category code."""
        return classify_imd_category(self.peak_wind_kts)

    @property
    def max_category_name(self) -> str:
        """Peak IMD category formal name."""
        return get_category_style(self.max_category_code)["name"]

    @property
    def landfall_waypoint(self) -> Optional[CycloneWaypoint]:
        """Identifies designated landfall waypoint."""
        for wp in self.waypoints:
            if wp.is_landfall:
                return wp
        # Fallback: find point with lowest dist_coast_km among mature fixes
        if self.waypoints:
            sorted_by_coast = sorted(
                [wp for wp in self.waypoints if wp.dist_coast_km is not None and wp.dist_coast_km <= 50],
                key=lambda w: w.dist_coast_km or 9999.0,
            )
            if sorted_by_coast:
                return sorted_by_coast[0]
        return None

    @property
    def start_time(self) -> str:
        """Earliest observation timestamp."""
        return self.waypoints[0].timestamp_utc if self.waypoints else "-"

    @property
    def end_time(self) -> str:
        """Latest observation timestamp."""
        return self.waypoints[-1].timestamp_utc if self.waypoints else "-"

    @property
    def total_distance_km(self) -> float:
        """Cumulative geodesic distance traveled along the track."""
        if len(self.waypoints) < 2:
            return 0.0
        total = 0.0
        for i in range(len(self.waypoints) - 1):
            w1, w2 = self.waypoints[i], self.waypoints[i + 1]
            total += haversine_distance_km(w1.lat, w1.lon, w2.lat, w2.lon)
        return round(total, 1)

    @property
    def basin_full_name(self) -> str:
        """Full English name for the cyclogenesis basin."""
        b = (self.basin or "").strip().upper()
        if "BOB" in b or "BAY" in b:
            return "Bay of Bengal"
        elif "AS" in b or "ARAB" in b:
            return "Arabian Sea"
        return self.basin or "North Indian Ocean"


# ---------------------------------------------------------------------------
# Geodesic Calculation & Hovercard Formatter
# ---------------------------------------------------------------------------

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points on Earth in km."""
    r = 6371.0  # Earth's mean radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def format_hovercard_html(
    storm_name: str,
    wp: CycloneWaypoint,
    basin_name: str = "North Indian Ocean",
) -> str:
    """Construct a high-legibility, dark-theme HTML tooltip card for Plotly hover.
    
    Adheres strictly to the #101820 design system and clear typography.
    """
    lat_str = f"{abs(wp.lat):.2f}°{'N' if wp.lat >= 0 else 'S'}"
    lon_str = f"{abs(wp.lon):.2f}°{'E' if wp.lon >= 0 else 'W'}"
    category_badge_color = wp.category_color

    landfall_line = ""
    if wp.is_landfall:
        landfall_line = (
            "<div style='background: rgba(248,113,113,0.25); border: 1px solid #F87171; "
            "color: #F87171; font-weight: 700; text-align: center; border-radius: 3px; "
            "padding: 2px 4px; margin-top: 4px; font-size: 11px;'>★ OFFICIAL LANDFALL FIX</div>"
        )

    coast_dist_str = f"{wp.dist_coast_km:.0f} km" if wp.dist_coast_km is not None else "N/A"
    speed_str = f"{wp.movement_speed_kph:.0f} km/h" if wp.movement_speed_kph is not None else "N/A"
    heading_str = f"{wp.movement_dir_deg:.0f}°" if wp.movement_dir_deg is not None else "N/A"

    html_content = (
        f"<div style='font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, monospace; "
        f"font-size: 12px; line-height: 1.45; color: #F1F5F9; min-width: 220px;'>"
        f"<div style='font-weight: 700; font-size: 13px; color: #38BDF8; "
        f"border-bottom: 1px solid #2C4056; padding-bottom: 3px; margin-bottom: 4px;'>"
        f"CYCLONE {storm_name.upper()} • {basin_name}</div>"
        f"<div style='display: flex; justify-content: space-between; margin-bottom: 2px;'>"
        f"<span style='color: #94A3B8;'>Classification:</span>"
        f"<span style='color: {category_badge_color}; font-weight: 600;'>{wp.category}</span></div>"
        f"<div style='display: flex; justify-content: space-between; margin-bottom: 2px;'>"
        f"<span style='color: #94A3B8;'>Timestamp (UTC):</span>"
        f"<span style='font-family: monospace; font-weight: 500;'>{wp.timestamp_utc}</span></div>"
        f"<div style='display: flex; justify-content: space-between; margin-bottom: 2px;'>"
        f"<span style='color: #94A3B8;'>Coordinates:</span>"
        f"<span style='font-family: monospace;'>{lat_str}, {lon_str}</span></div>"
        f"<div style='display: flex; justify-content: space-between; margin-bottom: 2px;'>"
        f"<span style='color: #94A3B8;'>Sustained Wind:</span>"
        f"<span style='font-weight: 600; color: #F1F5F9;'>{wp.wind_kts:.0f} kts ({wp.wind_kmh:.0f} km/h)</span></div>"
        f"<div style='display: flex; justify-content: space-between; margin-bottom: 2px;'>"
        f"<span style='color: #94A3B8;'>Central Pressure:</span>"
        f"<span style='font-weight: 600; color: #38BDF8;'>{wp.pressure_mb:.0f} hPa</span></div>"
        f"<div style='display: flex; justify-content: space-between; margin-bottom: 2px;'>"
        f"<span style='color: #94A3B8;'>Coast Distance:</span>"
        f"<span>{coast_dist_str}</span></div>"
        f"<div style='display: flex; justify-content: space-between; margin-bottom: 2px;'>"
        f"<span style='color: #94A3B8;'>Forward Motion:</span>"
        f"<span>{speed_str} @ {heading_str}</span></div>"
        f"{landfall_line}"
        f"</div>"
    )
    return html_content


# ---------------------------------------------------------------------------
# Track Dataset Loader
# ---------------------------------------------------------------------------

def load_cyclone_tracks_from_csv(csv_path: Optional[str] = None) -> Dict[str, CycloneTrack]:
    """Load and parse historical cyclone best-track records from CSV.
    
    Robust fallback across default paths (`data/nio_cyclones_sample.csv`).
    Groups fixes by storm, sorts chronologically, flags landfall, and builds hovercards.
    """
    candidate_paths = [
        csv_path,
        "data/nio_cyclones_sample.csv",
        "c:/Users/pc/OneDrive/Desktop/CHAKRAVAT/data/nio_cyclones_sample.csv",
        "../data/nio_cyclones_sample.csv",
    ]
    resolved_path: Optional[str] = None
    for p in candidate_paths:
        if p and os.path.exists(p):
            resolved_path = p
            break

    if not resolved_path:
        raise FileNotFoundError(
            f"Could not locate cyclone dataset at any candidate path: {candidate_paths}"
        )

    df = pd.read_csv(resolved_path)

    # Normalize column names
    df.columns = [c.strip().lower() for c in df.columns]

    tracks: Dict[str, CycloneTrack] = {}

    # Group records by storm_id or name
    storm_groups = df.groupby("name", sort=False)

    for storm_name, group in storm_groups:
        # Sort chronologically by timestamp
        group = group.sort_values(by="timestamp_utc")

        storm_name_str = str(storm_name).strip().upper()
        first_row = group.iloc[0]
        storm_id_str = str(first_row.get("storm_id", f"NIO_{storm_name_str}")).strip()
        basin_str = str(first_row.get("basin", "BOB")).strip().upper()

        signature_color = get_storm_color(storm_name_str)

        waypoints: List[CycloneWaypoint] = []
        raw_waypoints_data: List[Dict[str, Any]] = group.to_dict(orient="records")

        # Determine which waypoint is landfall (lowest dist_coast_km among mature fixes)
        min_coast_dist = float("inf")
        landfall_idx = -1
        for idx, row in enumerate(raw_waypoints_data):
            d = row.get("dist_coast_km")
            w = float(row.get("wind_kts", 0.0))
            if d is not None and not pd.isna(d):
                dist_val = float(d)
                # Consider as candidate if near coast (<= 50km) and strong
                if dist_val < min_coast_dist and dist_val <= 60 and w >= 40:
                    min_coast_dist = dist_val
                    landfall_idx = idx

        for idx, row in enumerate(raw_waypoints_data):
            ts = str(row.get("timestamp_utc", ""))
            lat = float(row.get("lat", 0.0))
            lon = float(row.get("lon", 0.0))
            wind_kts = float(row.get("wind_kts", 0.0))
            wind_kmh = round(wind_kts * 1.852, 1)
            pressure_mb = float(row.get("pressure_mb", 1010.0))

            cat_raw = str(row.get("category", "")).strip()
            cat_style = get_category_style(cat_raw if cat_raw else wind_kts)
            cat_name = cat_style["name"]
            cat_code = cat_style["code"]
            cat_color = cat_style["color"]

            mv_dir = row.get("movement_dir_deg")
            mv_spd = row.get("movement_speed_kph")
            mv_dir_f = float(mv_dir) if mv_dir is not None and not pd.isna(mv_dir) else None
            mv_spd_f = float(mv_spd) if mv_spd is not None and not pd.isna(mv_spd) else None

            dst = row.get("dist_coast_km")
            dst_f = float(dst) if dst is not None and not pd.isna(dst) else None

            data_src = str(row.get("data_source", "IBTrACS"))
            is_lf = (idx == landfall_idx)

            wp = CycloneWaypoint(
                timestamp_utc=ts,
                lat=lat,
                lon=lon,
                wind_kts=wind_kts,
                wind_kmh=wind_kmh,
                pressure_mb=pressure_mb,
                category=cat_name,
                category_code=cat_code,
                category_color=cat_color,
                movement_dir_deg=mv_dir_f,
                movement_speed_kph=mv_spd_f,
                dist_coast_km=dst_f,
                data_source=data_src,
                is_landfall=is_lf,
            )
            basin_full = "Arabian Sea" if "AS" in basin_str else "Bay of Bengal"
            wp.hover_text = format_hovercard_html(storm_name_str, wp, basin_full)
            waypoints.append(wp)

        track = CycloneTrack(
            storm_id=storm_id_str,
            storm_name=storm_name_str,
            basin=basin_str,
            waypoints=waypoints,
            signature_color=signature_color,
        )
        tracks[storm_name_str] = track

    return tracks


def build_track_summary(track: CycloneTrack) -> Dict[str, Any]:
    """Extract telemetry summary statistics for card displays and metrics."""
    lf = track.landfall_waypoint
    lf_str = (
        f"{lf.lat:.2f}°N, {lf.lon:.2f}°E ({lf.timestamp_utc[:10]})"
        if lf else "Maritime / Non-coastal"
    )

    return {
        "storm_name": track.storm_name,
        "storm_id": track.storm_id,
        "basin": track.basin_full_name,
        "peak_wind_kts": track.peak_wind_kts,
        "peak_wind_kmh": track.peak_wind_kmh,
        "min_pressure_mb": track.min_pressure_mb,
        "max_category": track.max_category_name,
        "max_category_code": track.max_category_code,
        "start_time": track.start_time,
        "end_time": track.end_time,
        "total_fixes": len(track.waypoints),
        "total_distance_km": track.total_distance_km,
        "landfall_summary": lf_str,
        "signature_color": track.signature_color,
    }
