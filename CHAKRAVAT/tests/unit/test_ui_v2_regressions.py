"""Regression tests for bugs found during the UI v2 overhaul (each test names the bug it guards)."""

import os
import re
import unittest

from streamlit.testing.v1 import AppTest

from src.ui import effects, hero
from src.ui.components import section_header, severity_badge
from src.ui.state import (
    BENCHMARK_STORMS, SECTIONS, STORM_CATALOG, canonical_storm_id, storm_name_for,
)

APP = os.path.join(os.path.dirname(__file__), "..", "..", "app.py")


def _app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=120)
    at.run()
    return at


def _btn(at: AppTest, key: str):
    return next(b for b in at.button if b.key == key)


class TestStormIdentity(unittest.TestCase):
    def test_all_identifier_styles_resolve(self):
        """BUG: IBTrACS id / CSV id / name were never reconciled, so views disagreed on the storm."""
        for sid, meta in STORM_CATALOG.items():
            for alias in (sid, meta["csv_id"], meta["csv_id"].rstrip("AB"), meta["name"], meta["name"].lower()):
                self.assertEqual(canonical_storm_id(alias), sid, alias)
        self.assertEqual(storm_name_for("NIO_2021_01"), "TAUKTAE")

    def test_unknown_falls_back_safely(self):
        self.assertIn(canonical_storm_id("garbage"), STORM_CATALOG)
        self.assertIn(canonical_storm_id(None), STORM_CATALOG)

    def test_library_matches_catalog(self):
        """BUG: only 3 of 5 storms had metadata; Tauktae/Yaas silently showed Fani."""
        self.assertEqual(set(BENCHMARK_STORMS), set(STORM_CATALOG))


class TestBadges(unittest.TestCase):
    def test_label_override_keeps_severity_colour(self):
        """BUG: custom badge labels were looked up as severities and rendered grey."""
        warn = severity_badge("warning")
        custom = severity_badge("warning", label="Action required")
        self.assertIn("ACTION REQUIRED", custom)
        colour = re.search(r"color: ([^;]+);", warn).group(1)
        self.assertIn(colour, custom)

    def test_section_header_badge_is_opt_in(self):
        """BUG: every header showed a stray 'NORMAL' badge even when none was requested."""
        import inspect
        src = inspect.getsource(section_header)
        self.assertIn("if badge_label else", src)


class TestScriptSafety(unittest.TestCase):
    def test_inline_scripts_survive_sanitiser(self):
        """BUG: DOMPurify deletes <script> text containing '<' + word char (e.g. 'i<N'): the hero
        animation silently never ran. Keep a space after every '<' inside inline scripts."""
        for source in (effects.EFFECTS_JS, hero._HERO_SCRIPT):
            for m in re.finditer(r"<script>(.*?)</script>", source, re.S):
                self.assertEqual(re.findall(r"<[\w/!]", m.group(1)), [])


class TestInteractionsDoNotCrash(unittest.TestCase):
    def test_tour_walks_all_steps(self):
        """BUG: tour + shortcut buttons wrote the nav widget's key after creation -> exception."""
        at = _app()
        _btn(at, "hero_tour").click().run()
        self.assertFalse(at.exception)
        for _ in range(4):
            _btn(at, "tour_next").click().run()
            self.assertFalse(at.exception)
        self.assertIsNone(at.session_state["tour_step"])

    def test_track_cards_navigate(self):
        for key in ("trkbtn_map", "trkbtn_c", "trkbtn_e", "trkbtn_g"):
            at = _app()
            _btn(at, key).click().run()
            self.assertFalse(at.exception, key)

    def test_map_transport_buttons(self):
        """BUG: timeline buttons assigned the slider's session key after it existed -> exception."""
        at = _app()
        at.radio(key="nav_radio_selection").set_value(SECTIONS[1]).run()
        for key in ("btn_gen_FANI", "btn_next_FANI", "btn_peak_FANI", "btn_prev_FANI", "btn_play_FANI"):
            _btn(at, key).click().run()
            self.assertFalse(at.exception, key)

    def test_storm_selection_is_shared_across_views(self):
        """BUG: map ignored the sidebar choice and the overview showed Fani for every storm."""
        for sid, meta in STORM_CATALOG.items():
            at = _app()
            _btn(at, f"btn_select_storm_{meta['name']}").click().run()
            at.radio(key="nav_radio_selection").set_value(SECTIONS[1]).run()
            self.assertEqual(at.selectbox(key="sec_b_storm_selector").value, meta["name"])
            at.radio(key="nav_radio_selection").set_value(SECTIONS[2]).run()
            self.assertEqual(at.selectbox(key="pred_storm_selector").value, meta["name"])

    def test_every_section_renders(self):
        for section in SECTIONS:
            at = _app()
            at.radio(key="nav_radio_selection").set_value(section).run()
            self.assertFalse(at.exception, section)


class TestOfflineAssets(unittest.TestCase):
    def test_basemap_geometry_is_bundled(self):
        """BUG: Plotly fetched asia_50m.json from cdn.plot.ly -> blank map when offline."""
        root = os.path.join(os.path.dirname(__file__), "..", "..")
        self.assertTrue(os.path.exists(os.path.join(root, "static", "topojson", "asia_50m.json")))
        with open(os.path.join(root, ".streamlit", "config.toml")) as fh:
            self.assertIn("enableStaticServing = true", fh.read())
        from src.geo.map_engine import geo_chart_config
        self.assertIn("/app/static/topojson/", geo_chart_config()["topojsonURL"])


if __name__ == "__main__":
    unittest.main()
