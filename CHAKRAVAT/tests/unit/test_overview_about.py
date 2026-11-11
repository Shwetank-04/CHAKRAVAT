"""Unit tests for Section A (Cyclone Intelligence Overview) and Section I (About & Methodology).

Validates:
- Syntax and compilation of section_overview.py and section_about.py.
- Export of callable render() functions.
- Mandated scientific disclaimer texts.
- Synoptic basin summary elements (Bay of Bengal & Arabian Sea).
- Active storm spotlight metrics (stage, peak wind, central pressure, distance to coast).
- Operational status strip dynamic metric calculation.
- Benchmark historical storm library selection (Fani, Amphan, Biparjoy).
- Comprehensive methodology documentation (storm-level splits, persistence/CLIPER baselines,
  Haversine Great-Circle error, empirical 70th-percentile cones).
- Scientific limitations and IMD statutory warning authority charter.
- Layout whitespace constraint compliance (<= 3 cards/row).
"""

import inspect
import os
import py_compile
import re
import unittest
from unittest.mock import patch, MagicMock

import src.views.section_overview as section_overview
import src.views.section_about as section_about
from src.ui.state import (
    init_session_state,
    reset_session_state,
    get_active_storm_id,
    set_active_storm_id,
    get_alerts,
    get_community_reports,
    get_shelters,
)


class TestOverviewAndAboutSyntaxAndImports(unittest.TestCase):
    """Verify clean syntax, compilation, and exports."""

    def test_section_overview_compiles(self):
        file_path = inspect.getfile(section_overview)
        compiled = py_compile.compile(file_path)
        self.assertIsNotNone(compiled)

    def test_section_about_compiles(self):
        file_path = inspect.getfile(section_about)
        compiled = py_compile.compile(file_path)
        self.assertIsNotNone(compiled)

    def test_render_callables_exist(self):
        self.assertTrue(callable(getattr(section_overview, "render", None)))
        self.assertTrue(callable(getattr(section_about, "render", None)))


class TestSectionOverviewContentAndIntegrity(unittest.TestCase):
    """Verify Section A content against dispatch specifications."""

    def setUp(self):
        file_path = inspect.getfile(section_overview)
        with open(file_path, "r", encoding="utf-8") as f:
            self.code = f.read()

    def test_mandatory_statutory_disclaimer_present(self):
        """Must include prominent statutory experimental disclaimer."""
        self.assertIn("EXPERIMENTAL DECISION-SUPPORT PROTOTYPE", self.code)
        self.assertIn("NOT AN OFFICIAL METEOROLOGICAL SERVICE", self.code)
        self.assertIn("IMD", self.code)
        self.assertIn("RSMC New Delhi", self.code)

    def test_synoptic_basin_summary_present(self):
        """Must include synoptic status for both Bay of Bengal and Arabian Sea."""
        self.assertIn("Bay of Bengal", self.code)
        self.assertIn("Arabian Sea", self.code)
        self.assertIn("BOB", self.code)
        self.assertIn("AS", self.code)

    def test_active_cyclone_spotlight_cards_present(self):
        """Spotlight shows intensity class, peak wind/pressure and lifetime, all derived from data."""
        self.assertIn("Peak Intensity Class", self.code)
        self.assertIn("Peak Wind", self.code)
        self.assertIn("Storm Lifetime", self.code)

    def test_quick_operational_status_strip_present(self):
        """Must display active alerts, verified reports, and shelter counts."""
        self.assertIn("Active Coastal Alerts", self.code)
        self.assertIn("Verified Field Reports", self.code)
        self.assertIn("Available Relief Shelters", self.code)
        self.assertIn("get_alerts()", self.code)
        self.assertIn("get_community_reports()", self.code)
        self.assertIn("get_shelters()", self.code)

    def test_mission_tracks_link_to_every_section(self):
        """Track cards must offer a jump to Map, Forecast Lab, Alerts and Shelters (via callbacks)."""
        for label in ("Storm Map", "Forecast Lab", "Alert Workflow", "Shelter Directory"):
            self.assertIn(label, self.code)
        self.assertIn("on_click=_goto", self.code)

    def test_historical_storm_library_covers_every_storm_with_correct_facts(self):
        """Every selectable storm resolves to itself (the old code fell back to FANI) with dataset facts."""
        from src.ui.state import STORM_CATALOG, BENCHMARK_STORMS
        from src.views.section_overview import STORM_METADATA, _resolve_storm_meta
        self.assertEqual(set(STORM_METADATA), set(STORM_CATALOG))
        for sid, cat in STORM_CATALOG.items():
            self.assertEqual(_resolve_storm_meta(sid)["name"], cat["name"])
            self.assertEqual(_resolve_storm_meta(cat["csv_id"])["name"], cat["name"])
        for sid in BENCHMARK_STORMS:
            self.assertIn(sid, STORM_CATALOG)
        # Overview numbers must agree with the track data the Map uses.
        from src.geo.tracks import load_cyclone_tracks_from_csv
        for name, track in load_cyclone_tracks_from_csv().items():
            meta = next(m for m in STORM_METADATA.values() if m["name"] == name)
            self.assertEqual(meta["peak_wind_kts"], round(track.peak_wind_kts))
            self.assertEqual(meta["min_pressure_hpa"], round(track.min_pressure_mb))
        self.assertIn("set_active_storm_id", self.code)

    def test_whitespace_columns_discipline(self):
        """Layout constraint: <= 3 cards/columns per row."""
        # Find all grid_row calls
        grid_calls = re.findall(r"grid_row\((\d+)\)", self.code)
        for num_str in grid_calls:
            self.assertLessEqual(int(num_str), 3, f"grid_row({num_str}) violates <= 3 columns constraint")


class TestSectionAboutContentAndIntegrity(unittest.TestCase):
    """Verify Section I content against scientific methodology specifications."""

    def setUp(self):
        file_path = inspect.getfile(section_about)
        with open(file_path, "r", encoding="utf-8") as f:
            self.code = f.read()

    def test_data_provenance_and_attribution(self):
        """Must document IMD Best Track, IBTrACS v04, and WMO standards."""
        self.assertIn("IMD RSMC New Delhi", self.code)
        self.assertIn("IBTrACS v04", self.code)
        self.assertIn("World Meteorological Organization", self.code)
        self.assertIn("WMO", self.code)

    def test_storm_level_splitting_explanation(self):
        """Must document storm-level grouping to prevent autocorrelation leakage."""
        self.assertIn("Storm-Level", self.code)
        self.assertIn("Autocorrelation Leakage", self.code)
        self.assertIn("Group", self.code)

    def test_persistence_and_cliper_baselines(self):
        """Must explain Linear Persistence and CLIPER reference baselines."""
        self.assertIn("Linear Persistence", self.code)
        self.assertIn("CLIPER", self.code)

    def test_dynamic_haversine_error_calculation(self):
        """Must explain Great-Circle Haversine error formula."""
        self.assertIn("Haversine", self.code)
        self.assertIn("Great-Circle", self.code)
        self.assertTrue("6,371" in self.code or "6371" in self.code)

    def test_empirical_70th_percentile_uncertainty_cones(self):
        """Must contrast empirical 70th-percentile cones against arbitrary geometric cones."""
        self.assertTrue("70th percentile" in self.code or "70%" in self.code)
        self.assertIn("arbitrary", self.code)

    def test_scientific_limitations_and_failure_modes(self):
        """Must detail Rapid Intensification, Landfall decay, and data-limited states."""
        self.assertIn("Rapid Intensification", self.code)
        self.assertTrue("Landfall Topography Friction" in self.code or "Landfall" in self.code)
        self.assertIn("DATA-LIMITED", self.code)

    def test_statutory_imd_warning_authority(self):
        """Must explicitly state IMD's sole statutory authority under Disaster Management Act (2005)."""
        self.assertIn("Disaster Management Act, 2005", self.code)
        self.assertTrue("sole" in self.code or "statutory" in self.code)

    def test_whitespace_columns_discipline(self):
        """Layout constraint: <= 3 cards/columns per row."""
        grid_calls = re.findall(r"grid_row\((\d+)\)", self.code)
        for num_str in grid_calls:
            self.assertLessEqual(int(num_str), 3, f"grid_row({num_str}) violates <= 3 columns constraint")


class TestRenderExecutionUnderStreamlit(unittest.TestCase):
    """Test render execution with mocked Streamlit calls to guarantee zero exceptions."""

    def setUp(self):
        reset_session_state()

    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    @patch("streamlit.button")
    @patch("streamlit.tabs")
    def test_render_overview_executes_without_exception(self, mock_tabs, mock_button, mock_columns, mock_markdown):
        mock_button.return_value = False
        mock_columns.side_effect = lambda spec: [MagicMock() for _ in (spec if isinstance(spec, list) else range(spec))]
        mock_tabs.side_effect = lambda tab_names: [MagicMock() for _ in tab_names]

        # Should complete without error
        try:
            section_overview.render()
        except Exception as e:
            self.fail(f"section_overview.render() raised unexpected exception: {e}")

    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    @patch("streamlit.button")
    @patch("streamlit.tabs")
    def test_render_about_executes_without_exception(self, mock_tabs, mock_button, mock_columns, mock_markdown):
        mock_button.return_value = False
        mock_columns.side_effect = lambda spec: [MagicMock() for _ in (spec if isinstance(spec, list) else range(spec))]
        mock_tabs.side_effect = lambda tab_names: [MagicMock() for _ in tab_names]

        # Should complete without error
        try:
            section_about.render()
        except Exception as e:
            self.fail(f"section_about.render() raised unexpected exception: {e}")


if __name__ == "__main__":
    unittest.main()
