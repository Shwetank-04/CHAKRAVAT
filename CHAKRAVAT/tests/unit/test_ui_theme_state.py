"""Unit tests for CHAKRAVAT Design System, UI Components, Theme, and State Management.

Covers Milestone M1 requirements and acceptance criteria.
"""

import os
import py_compile
import tomllib
import pytest

from src.ui.theme import (
    COLOR_TOKENS,
    SEVERITY_COLORS,
    STATUS_COLORS,
    get_theme_css,
    inject_custom_theme,
)
from src.ui.components import (
    status_badge,
    severity_badge,
    grid_row,
)
from src.ui.state import (
    SECTIONS,
    BENCHMARK_STORMS,
    init_session_state,
    reset_session_state,
    get_current_section,
    set_current_section,
    get_active_storm_id,
    set_active_storm_id,
    get_alerts,
    add_alert,
    update_alert_status,
    get_community_reports,
    add_community_report,
    update_report_status,
    get_shelters,
    get_response_tasks,
    update_task_status,
)
import src.views as views


class TestThemeAndConfig:
    """Verify dark palette tokens, Streamlit config, and CSS overrides."""

    def test_theme_color_tokens(self):
        """Confirm core palette tokens match specifications."""
        assert COLOR_TOKENS["bg_base"] == "#101820", "Base background must be #101820"
        assert COLOR_TOKENS["surface_card"] == "#17222D", "Card surface must be #17222D"
        assert COLOR_TOKENS["border_default"] == "#2C4056", "Default border must be #2C4056"
        assert COLOR_TOKENS["accent_primary"] == "#38BDF8", "Primary accent must be #38BDF8 (Sky Blue)"
        assert COLOR_TOKENS["text_primary"] == "#F1F5F9", "Primary text must be #F1F5F9"

    def test_streamlit_config_toml(self):
        """.streamlit/config.toml must match the required dark theme tokens."""
        config_path = os.path.join(os.path.dirname(__file__), "..", "..", ".streamlit", "config.toml")
        config_path = os.path.abspath(config_path)
        assert os.path.isfile(config_path), f"Missing config.toml at {config_path}"

        with open(config_path, "rb") as f:
            cfg = tomllib.load(f)

        theme = cfg.get("theme", {})
        assert theme.get("base") == "dark"
        assert theme.get("primaryColor") == "#38BDF8"
        assert theme.get("backgroundColor") == "#101820"
        assert theme.get("secondaryBackgroundColor") == "#17222D"
        assert theme.get("textColor") == "#F1F5F9"

    def test_css_rules_and_offline_fonts(self):
        """Injected CSS must override Streamlit DOM, define custom classes, and avoid external CDNs."""
        css = get_theme_css()

        # Offline resilience: no external CDN imports
        assert "http://" not in css, "CSS must not reference unencrypted external CDNs"
        assert "https://" not in css, "CSS must not reference external CDNs or Google Fonts"
        assert "fonts.googleapis.com" not in css

        # System font stack
        assert "-apple-system" in css
        assert "Segoe UI" in css

        # DOM overrides
        assert ".stApp" in css
        assert "#101820" in css
        assert "div[data-testid=\"stMetric\"]" in css
        assert "#17222D" in css
        assert ".block-container" in css

        # Custom UI classes
        assert ".cv-card" in css
        assert ".cv-badge" in css
        assert ".cv-disclaimer-banner" in css
        assert ".cv-state-box" in css
        assert ".cv-metric-card" in css

    def test_inject_custom_theme_safe_execution(self):
        """inject_custom_theme() must execute cleanly even outside active Streamlit runtime."""
        inject_custom_theme()  # Should not raise exception


class TestUIComponents:
    """Verify shared components and layout rules."""

    def test_status_badge_generation(self):
        """status_badge() must return styled HTML spans for each workflow state."""
        b_pending = status_badge("Pending")
        assert "PENDING" in b_pending
        assert "cv-badge" in b_pending

        b_approved = status_badge("Approved")
        assert "APPROVED" in b_approved
        assert "#34D399" in b_approved

        b_verified = status_badge("Verified")
        assert "VERIFIED" in b_verified

        b_rejected = status_badge("Rejected")
        assert "REJECTED" in b_rejected
        assert "#F87171" in b_rejected

    def test_severity_badge_generation(self):
        """severity_badge() must return styled HTML spans for severity tiers."""
        b_watch = severity_badge("Watch")
        assert "WATCH" in b_watch

        b_warning = severity_badge("Warning")
        assert "WARNING" in b_warning

        b_extreme = severity_badge("Extreme")
        assert "EXTREME" in b_extreme
        assert "#F87171" in b_extreme

    def test_whitespace_discipline_max_three_columns(self):
        """grid_row() must strictly prohibit more than 3 columns per row."""
        with pytest.raises(ValueError, match="Maximum allowed side-by-side columns is 3"):
            grid_row(4)

        with pytest.raises(ValueError, match="Maximum allowed side-by-side columns is 3"):
            grid_row(5)

        with pytest.raises(ValueError):
            grid_row(0)


class TestSessionStateAndWorkflows:
    """Verify session state initialization and mutation workflows."""

    def setup_method(self):
        reset_session_state()

    def test_sections_inventory(self):
        """Confirm all 9 sections (A through I) are registered."""
        assert len(SECTIONS) == 9
        expected_prefixes = ["(A)", "(B)", "(C)", "(D)", "(E)", "(F)", "(G)", "(H)", "(I)"]
        for prefix, sec in zip(expected_prefixes, SECTIONS):
            assert sec.startswith(prefix), f"Section {sec} should start with {prefix}"

    def test_navigation_routing(self):
        """Test getting and setting active navigation sections."""
        assert get_current_section() == SECTIONS[0]
        set_current_section("b")
        assert get_current_section() == SECTIONS[1]
        set_current_section("prediction")
        assert get_current_section() == SECTIONS[2]
        set_current_section(SECTIONS[4])
        assert get_current_section() == SECTIONS[4]

    def test_storm_selection(self):
        """Test storm selection accessors and benchmark storms."""
        assert get_active_storm_id() == "2019117N12089"  # Cyclone FANI default
        assert len(BENCHMARK_STORMS) >= 5
        set_active_storm_id("2020137N10086")
        assert get_active_storm_id() == "2020137N10086"

    def test_alert_lifecycle_and_audit_history(self):
        """Test alert creation, review status transitions, and timestamped audit logs."""
        initial_alerts = get_alerts()
        assert len(initial_alerts) >= 3

        # Create new draft alert
        new_alert = add_alert(
            region="Balasore Coast",
            severity="Warning",
            headline="Severe Coastal Gale Notice",
            description="Winds exceeding 100 km/h expected.",
            evidence="Doppler radar velocity scan",
            valid_until="2026-11-06 12:00 UTC",
            issued_by="Forecaster Test",
        )
        assert new_alert["id"].startswith("ALT-2026-")
        assert new_alert["status"] == "Pending"
        assert len(new_alert["audit_history"]) == 1
        assert new_alert["audit_history"][0]["action"] == "Created Draft Alert"

        # Transition status to Approved
        success = update_alert_status(
            alert_id=new_alert["id"],
            new_status="Approved",
            actor="Lead Forecaster Officer",
            notes="Ground barometric check passed.",
        )
        assert success is True

        # Verify updated state & audit trail
        all_alerts = get_alerts()
        matching = [a for a in all_alerts if a["id"] == new_alert["id"]][0]
        assert matching["status"] == "Approved"
        assert matching["reviewer_comments"] == "Ground barometric check passed."
        assert len(matching["audit_history"]) == 2
        assert matching["audit_history"][-1]["action"] == "Approved"
        assert matching["audit_history"][-1]["actor"] == "Lead Forecaster Officer"
        assert "timestamp" in matching["audit_history"][-1]

    def test_community_reports_workflow(self):
        """Test crowdsourced report submission and review/verification lifecycle."""
        initial_reports = get_community_reports()
        assert len(initial_reports) >= 3

        # Submit new report
        rep = add_community_report(
            category="Flooding",
            district="Puri",
            location_detail="Pentakota Pier",
            description="Sea surge inundation reaching 0.5m",
            severity="High",
            has_photo=True,
        )
        assert rep["id"].startswith("REP-2026-")
        assert rep["status"] == "Submitted"
        assert rep["is_verified"] is False

        # Transition to Verified
        verified_ok = update_report_status(
            report_id=rep["id"],
            new_status="Verified",
            reviewer="Puri Disaster Desk",
            notes="Confirmed by on-site fire services unit.",
        )
        assert verified_ok is True

        all_reps = get_community_reports()
        matching = [r for r in all_reps if r["id"] == rep["id"]][0]
        assert matching["status"] == "Verified"
        assert matching["is_verified"] is True
        assert matching["reviewed_by"] == "Puri Disaster Desk"
        assert matching["reviewed_at"] is not None

    def test_shelter_directory_filters(self):
        """Verify shelter directory querying, mandatory fields, and illustrative source labels."""
        shelters = get_shelters()
        assert len(shelters) >= 5, "Must bundle at least 5 illustrative shelters"

        for s in shelters:
            assert "id" in s
            assert "name" in s
            assert "district" in s
            assert "capacity" in s
            assert s["capacity"] > 0
            assert "contact_phone" in s
            assert "source_label" in s
            assert "Illustrative" in s["source_label"] or "Simulation" in s["source_label"]

        # Filter by Puri district
        puri_shelters = get_shelters(district_filter="Puri")
        assert len(puri_shelters) >= 1
        for s in puri_shelters:
            assert s["district"] == "Puri"

        # Filter by accessibility
        accessible_shelters = get_shelters(accessibility_only=True)
        assert len(accessible_shelters) >= 1
        for s in accessible_shelters:
            assert s["is_accessible"] is True

    def test_response_tasks_management(self):
        """Test response tasks retrieval and progression."""
        tasks = get_response_tasks()
        assert len(tasks) >= 3

        task_id = tasks[0]["id"]
        updated = update_task_status(task_id, new_status="In Progress", assignee="Rapid Rescue Team Alpha")
        assert updated is True

        matching = [t for t in get_response_tasks() if t["id"] == task_id][0]
        assert matching["status"] == "In Progress"
        assert matching["assignee"] == "Rapid Rescue Team Alpha"


class TestApplicationShellAndViews:
    """Verify app.py compilation and views modular export."""

    def test_app_py_syntax_and_compilation(self):
        """app.py must be valid Python that compiles without syntax errors."""
        app_path = os.path.join(os.path.dirname(__file__), "..", "..", "app.py")
        app_path = os.path.abspath(app_path)
        assert os.path.isfile(app_path)
        compiled = py_compile.compile(app_path)
        assert compiled is not None

    def test_modular_views_render_functions(self):
        """Every section view module must expose a callable render() function."""
        render_funcs = [
            views.render_overview,
            views.render_map,
            views.render_prediction,
            views.render_data_sources,
            views.render_alerts,
            views.render_community,
            views.render_shelters,
            views.render_response,
            views.render_about,
        ]
        assert len(render_funcs) == 9
        for fn in render_funcs:
            assert callable(fn), f"View function {fn} must be callable"
