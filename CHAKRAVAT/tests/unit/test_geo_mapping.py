"""Unit tests for CHAKRAVAT Geospatial Intelligence & Mapping (Milestone M4).

Validates styling tokens, IMD category classifications, track parsing from CSV,
geodesic calculations, Plotly Scattergeo basemap generation, and Section B view.
"""

import pytest
import plotly.graph_objects as go
from unittest.mock import patch, MagicMock

from src.geo.styling import (
    GEO_BOUNDS,
    IMD_CATEGORIES,
    STORM_COLOR_PALETTE,
    classify_imd_category,
    get_category_color,
    get_category_style,
    get_storm_color,
    get_imd_legend_items,
)
from src.geo.tracks import (
    CycloneTrack,
    CycloneWaypoint,
    haversine_distance_km,
    load_cyclone_tracks_from_csv,
    build_track_summary,
    format_hovercard_html,
)
from src.geo.map_engine import (
    create_north_indian_ocean_map,
    build_multi_storm_figure,
    build_single_storm_figure,
)
import src.views.section_map as section_map


class TestGeoStyling:
    """Verifies geographic bounds and IMD 8-tier styling tokens."""

    def test_geo_bounds_configuration(self):
        assert "center" in GEO_BOUNDS
        assert GEO_BOUNDS["lataxis_range"] == [2.0, 28.5]
        assert GEO_BOUNDS["lonaxis_range"] == [52.0, 98.0]
        # center must be the midpoint of the ranges (it was 80E vs a 75E midpoint, shifting the view)
        assert GEO_BOUNDS["center"]["lat"] == sum(GEO_BOUNDS["lataxis_range"]) / 2
        assert GEO_BOUNDS["center"]["lon"] == sum(GEO_BOUNDS["lonaxis_range"]) / 2
        assert GEO_BOUNDS["projection_type"] == "mercator"

        palette = GEO_BOUNDS["theme_palette"]
        assert palette["bg_color"] == "#101820"
        assert palette["ocean_color"] == "#0a1118"
        assert palette["land_color"] == "#16222f"
        assert palette["coastline_color"] == "#385170"

    def test_imd_categories_completeness(self):
        expected_codes = ["LPA", "D", "DD", "CS", "SCS", "VSCS", "ESCS", "SuCS"]
        for code in expected_codes:
            assert code in IMD_CATEGORIES
            cat = IMD_CATEGORIES[code]
            assert "name" in cat
            assert "min_kts" in cat
            assert "max_kts" in cat
            assert "color" in cat
            assert "symbol" in cat
            assert "size" in cat
            assert cat["color"].startswith("#")

    def test_classify_imd_category(self):
        assert classify_imd_category(10.0) == "LPA"
        assert classify_imd_category(20.0) == "D"
        assert classify_imd_category(30.0) == "DD"
        assert classify_imd_category(40.0) == "CS"
        assert classify_imd_category(55.0) == "SCS"
        assert classify_imd_category(75.0) == "VSCS"
        assert classify_imd_category(100.0) == "ESCS"
        assert classify_imd_category(140.0) == "SuCS"

    def test_get_category_style_and_color(self):
        # By string name
        style_cs = get_category_style("Cyclonic Storm")
        assert style_cs["code"] == "CS"
        assert get_category_color("Cyclonic Storm") == "#00E5FF"

        # By code
        style_sucs = get_category_style("SuCS")
        assert style_sucs["name"] == "Super Cyclonic Storm"
        assert style_sucs["color"] == "#D500F9"

        # By numeric wind speed
        assert get_category_color(115.0) == "#FF3D00"  # ESCS
        assert get_category_color(130.0) == "#D500F9"  # SuCS

    def test_storm_colors(self):
        assert get_storm_color("BIPARJOY") == "#FF3D00"
        assert get_storm_color("AMPHAN") == "#D500F9"
        assert get_storm_color("FANI") == "#00E5FF"
        assert get_storm_color("UNKNOWN_STORM").startswith("#")

    def test_legend_items_order(self):
        items = get_imd_legend_items()
        assert len(items) == 7
        codes = [item["code"] for item in items]
        assert codes == ["D", "DD", "CS", "SCS", "VSCS", "ESCS", "SuCS"]


class TestCycloneTracks:
    """Verifies track parsing, waypoint models, telemetry and distances."""

    def test_haversine_distance(self):
        # Distance between Mumbai (18.92°N, 72.83°E) and Chennai (13.08°N, 80.27°E) ~1030 km
        dist = haversine_distance_km(18.92, 72.83, 13.08, 80.27)
        assert 1000 <= dist <= 1100

        # Zero distance
        assert haversine_distance_km(15.0, 80.0, 15.0, 80.0) == 0.0

    def test_load_sample_csv(self):
        tracks = load_cyclone_tracks_from_csv("data/nio_cyclones_sample.csv")
        assert len(tracks) == 8

        # Required benchmark storms
        assert "FANI" in tracks
        assert "AMPHAN" in tracks
        assert "BIPARJOY" in tracks
        assert "TAUKTAE" in tracks
        assert "YAAS" in tracks
        assert "TITLI" in tracks
        assert "OCKHI" in tracks
        assert "ASANI" in tracks

    def test_fani_track_telemetry(self):
        tracks = load_cyclone_tracks_from_csv("data/nio_cyclones_sample.csv")
        fani = tracks["FANI"]

        assert fani.storm_name == "FANI"
        assert "BOB" in fani.basin
        assert fani.basin_full_name == "Bay of Bengal"
        assert len(fani.waypoints) == 11
        assert fani.peak_wind_kts == 140.0
        assert fani.peak_wind_kmh == 259.3
        assert fani.min_pressure_mb == 932.0
        assert fani.max_category_code == "SuCS"
        assert fani.total_distance_km > 1000.0

        # Check landfall waypoint detection
        lf = fani.landfall_waypoint
        assert lf is not None
        assert lf.dist_coast_km <= 50.0

    def test_biparjoy_track_telemetry(self):
        tracks = load_cyclone_tracks_from_csv("data/nio_cyclones_sample.csv")
        biparjoy = tracks["BIPARJOY"]

        assert biparjoy.storm_name == "BIPARJOY"
        assert "AS" in biparjoy.basin
        assert biparjoy.basin_full_name == "Arabian Sea"
        assert biparjoy.peak_wind_kts == 115.0
        assert biparjoy.min_pressure_mb == 952.0
        assert biparjoy.max_category_code == "ESCS"

    def test_track_summary_builder(self):
        tracks = load_cyclone_tracks_from_csv("data/nio_cyclones_sample.csv")
        amphan = tracks["AMPHAN"]
        summary = build_track_summary(amphan)

        assert summary["storm_name"] == "AMPHAN"
        assert summary["basin"] == "Bay of Bengal"
        assert summary["peak_wind_kts"] == 140.0
        assert summary["min_pressure_mb"] == 932.0
        assert summary["max_category_code"] == "SuCS"
        assert summary["total_fixes"] == 11
        assert "Landfall" in summary["landfall_summary"] or "°N" in summary["landfall_summary"]

    def test_hovercard_html_content(self):
        tracks = load_cyclone_tracks_from_csv("data/nio_cyclones_sample.csv")
        wp = tracks["FANI"].waypoints[5]
        html = format_hovercard_html("FANI", wp, "Bay of Bengal")

        assert "CYCLONE FANI" in html
        assert "Bay of Bengal" in html
        assert str(wp.timestamp_utc) in html
        assert "kts" in html
        assert "hPa" in html


class TestMapEngine:
    """Verifies offline Plotly Scattergeo basemap generation."""

    def test_create_north_indian_ocean_map(self):
        fig = create_north_indian_ocean_map(title="Test Basemap", height=600)
        assert isinstance(fig, go.Figure)

        # Confirm geo properties match dark theme
        layout_geo = fig.layout.geo
        assert layout_geo.showland is True
        assert layout_geo.landcolor == "#16222f"
        assert layout_geo.showocean is True
        assert layout_geo.oceancolor == "#0a1118"
        assert layout_geo.coastlinecolor == "#385170"
        assert layout_geo.bgcolor == "#101820"
        assert fig.layout.paper_bgcolor == "#101820"

    def test_build_multi_storm_figure(self):
        tracks = load_cyclone_tracks_from_csv("data/nio_cyclones_sample.csv")
        fig = build_multi_storm_figure(tracks, show_lines=True, show_markers=True, show_landfalls=True)

        assert isinstance(fig, go.Figure)
        # Should contain ambient labels + line traces + marker traces + landfall traces
        assert len(fig.data) >= 16

        # Check legend entries exist for storms
        storm_traces = [t for t in fig.data if t.showlegend and t.name and ("BOB" in t.name or "AS" in t.name)]
        assert len(storm_traces) == 8

    def test_build_single_storm_figure(self):
        tracks = load_cyclone_tracks_from_csv("data/nio_cyclones_sample.csv")
        fani = tracks["FANI"]

        # Full track
        fig = build_single_storm_figure(fani, up_to_step=None, show_lines=True, show_markers=True)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 4  # Basemap labels + trajectory + category markers + beacon

        # Scrubber partial step
        fig_step = build_single_storm_figure(fani, up_to_step=3)
        assert isinstance(fig_step, go.Figure)
        # Current position beacon should match waypoint 3
        beacon = [t for t in fig_step.data if t.name == "Current Position"][0]
        assert beacon.lat[0] == fani.waypoints[3].lat
        assert beacon.lon[0] == fani.waypoints[3].lon


class TestSectionMapView:
    """Verifies that section_map.render executes cleanly without unhandled exceptions."""

    def test_section_map_render(self):
        # Mock streamlit widgets
        with patch("streamlit.selectbox", return_value="ALL_STORMS"), \
             patch("streamlit.checkbox", return_value=True), \
             patch("streamlit.plotly_chart") as mock_plotly, \
             patch("streamlit.dataframe") as mock_df, \
             patch("streamlit.markdown"), \
             patch("streamlit.columns", side_effect=lambda n: [MagicMock() for _ in range(n if isinstance(n, int) else len(n))]), \
             patch("streamlit.container", return_value=MagicMock()), \
             patch("streamlit.expander", return_value=MagicMock()):

            # Call render
            section_map.render()
            assert mock_plotly.called
            assert mock_df.called
