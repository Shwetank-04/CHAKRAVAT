"""CHAKRAVAT Geospatial Intelligence & Mapping Module.

North Indian Ocean cyclone tracking, IMD classification styling,
and offline Plotly Scattergeo mapping engine.
"""

from src.geo.styling import (
    GEO_BOUNDS,
    IMD_CATEGORIES,
    STORM_COLOR_PALETTE,
    get_category_color,
    get_category_style,
    classify_imd_category,
)
from src.geo.tracks import (
    CycloneTrack,
    CycloneWaypoint,
    load_cyclone_tracks_from_csv,
    build_track_summary,
    format_hovercard_html,
)
from src.geo.map_engine import (
    create_north_indian_ocean_map,
    build_single_storm_figure,
    build_multi_storm_figure,
)

__all__ = [
    "GEO_BOUNDS",
    "IMD_CATEGORIES",
    "STORM_COLOR_PALETTE",
    "get_category_color",
    "get_category_style",
    "classify_imd_category",
    "CycloneTrack",
    "CycloneWaypoint",
    "load_cyclone_tracks_from_csv",
    "build_track_summary",
    "format_hovercard_html",
    "create_north_indian_ocean_map",
    "build_single_storm_figure",
    "build_multi_storm_figure",
]
