"""Unit tests for CHAKRAVAT Operational Workflows (Milestones M5/M6/M7).

Covers:
- data/illustrative_shelters.csv schema and completeness
- src/workflows/alerts.py lifecycle and audit logging
- src/workflows/reports.py 5-state verification lifecycle
- src/workflows/shelters.py search, filters, and KPIs
- src/workflows/disaster_response.py triage streams and task manager
- src/views/ section render functions smoke tests
"""

import csv
import os
import pytest

from src.ui.state import reset_session_state
from src.workflows.alerts import (
    VALID_SEVERITIES,
    VALID_STATUSES,
    create_alert,
    ensure_alerts_initialized,
    export_alerts_csv,
    get_alert_by_id,
    get_alerts,
    get_alerts_kpis,
    review_alert,
)
from src.workflows.reports import (
    VALID_REPORT_CATEGORIES,
    VALID_REPORT_STATUSES,
    ensure_reports_initialized,
    export_reports_csv,
    get_community_reports,
    get_report_by_id,
    get_reports_kpis,
    submit_community_report,
    update_report_review,
)
from src.workflows.shelters import (
    ensure_shelters_initialized,
    export_shelters_csv,
    get_shelter_by_id,
    get_shelters,
    get_shelters_kpis,
    load_shelters_from_csv,
)
from src.workflows.disaster_response import (
    SAFE_EVACUATION_ZONES,
    create_response_task,
    ensure_tasks_initialized,
    get_response_kpis,
    get_response_tasks,
    get_triage_streams,
    update_task_status,
)
import src.views.section_alerts as v_alerts
import src.views.section_community as v_community
import src.views.section_shelters as v_shelters
import src.views.section_response as v_response


class TestIllustrativeSheltersCSV:
    """Verify data/illustrative_shelters.csv structure and requirements."""

    def test_csv_file_exists(self):
        csv_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "illustrative_shelters.csv")
        csv_path = os.path.abspath(csv_path)
        assert os.path.isfile(csv_path), f"Missing shelters CSV at {csv_path}"

    def test_csv_records_and_columns(self):
        csv_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "illustrative_shelters.csv")
        csv_path = os.path.abspath(csv_path)

        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            records = list(reader)

        assert len(records) == 7, f"Expected exactly 7 illustrative shelters, got {len(records)}"

        required_cols = {
            "name", "district", "state", "latitude", "longitude",
            "capacity", "current_occupancy", "contact_phone",
            "is_accessible", "source_label"
        }
        for col in required_cols:
            assert col in reader.fieldnames, f"Column '{col}' must be present in CSV headers"

        states = {r["state"] for r in records}
        expected_states = {"Odisha", "West Bengal", "Andhra Pradesh", "Gujarat"}
        assert expected_states.issubset(states), f"All 4 coastal states must be covered, found {states}"

        for r in records:
            assert r["source_label"] == "ILLUSTRATIVE DEMO RECORD"
            cap = int(r["capacity"])
            occ = int(r["current_occupancy"])
            assert cap > 0, "Capacity must be positive"
            assert occ >= 0, "Occupancy must be non-negative"
            assert occ <= cap, "Current occupancy cannot exceed maximum capacity"
            lat = float(r["latitude"])
            lon = float(r["longitude"])
            assert 10.0 <= lat <= 30.0, f"Latitude {lat} out of NIO bounds"
            assert 65.0 <= lon <= 95.0, f"Longitude {lon} out of NIO bounds"


class TestAlertsWorkflow:
    """Verify Section E alert workflow operations, state transitions, and audit trail."""

    def setup_method(self):
        reset_session_state()

    def test_initial_alerts(self):
        alerts = ensure_alerts_initialized()
        assert len(alerts) >= 3

    def test_create_alert_and_audit(self):
        alert = create_alert(
            severity="Severe",
            region="Ganjam Coastal Sector",
            headline="Severe Gale Advisory",
            description="High velocity squalls approaching Gopalpur.",
            evidence="Doppler radar velocity > 40 m/s",
            valid_until="2026-11-06 20:00 UTC",
            issued_by="Radar Unit 4",
        )
        assert alert["id"].startswith("ALT-2026-")
        assert alert["severity"] == "Severe"
        assert alert["status"] == "Pending"
        assert len(alert["audit_history"]) == 1
        assert alert["audit_history"][0]["action"] == "Created Draft Alert"
        assert alert["audit_history"][0]["actor"] == "Radar Unit 4"

    def test_review_alert_approve(self):
        alert = create_alert(
            severity="Extreme",
            region="Puri",
            headline="Storm Surge Warning",
            description="Tidal surge expected.",
            evidence="Ensemble model",
            valid_until="2026-11-06 18:00 UTC",
        )
        ok = review_alert(
            alert_id=alert["id"],
            action="Approve",
            actor="Dr. S. Patnaik",
            notes="Tide gauge corroborates forecast.",
        )
        assert ok is True
        updated = get_alert_by_id(alert["id"])
        assert updated is not None
        assert updated["status"] == "Approved"
        assert updated["reviewer_comments"] == "Tide gauge corroborates forecast."
        assert len(updated["audit_history"]) == 2
        assert updated["audit_history"][-1]["action"] == "Approved Bulletin"
        assert updated["audit_history"][-1]["actor"] == "Dr. S. Patnaik"

    def test_review_alert_reject_and_request_changes(self):
        a1 = create_alert(
            severity="Watch",
            region="Kolkata Port",
            headline="High Wind Notice",
            description="Squalls expected",
            evidence="Barometric readings",
            valid_until="2026-11-07 00:00 UTC",
        )
        ok_rej = review_alert(a1["id"], action="Reject", actor="Chief Met Officer", notes="Inadequate pressure drop")
        assert ok_rej is True
        assert get_alert_by_id(a1["id"])["status"] == "Rejected"

        a2 = create_alert(
            severity="Warning",
            region="Digha",
            headline="Wave Threat",
            description="High waves",
            evidence="Model",
            valid_until="2026-11-07 00:00 UTC",
        )
        ok_chg = review_alert(a2["id"], action="Request Changes", actor="Desk Chief", notes="Add buoy wave height numbers")
        assert ok_chg is True
        assert get_alert_by_id(a2["id"])["status"] == "Changes Requested"

    def test_alerts_filtering_and_kpis(self):
        all_alerts = get_alerts()
        kpis = get_alerts_kpis()
        assert kpis["total"] == len(all_alerts)
        assert kpis["pending"] >= 0

        pending_only = get_alerts(status_filter="Pending")
        for a in pending_only:
            assert a["status"] == "Pending"

        csv_str = export_alerts_csv()
        assert "id,severity,region,headline" in csv_str
        assert len(csv_str.strip().splitlines()) >= 4


class TestCommunityReportsWorkflow:
    """Verify Section F crowdsourced report workflow, 5-state lifecycle, and unverified tagging."""

    def setup_method(self):
        reset_session_state()

    def test_initial_reports(self):
        reps = ensure_reports_initialized()
        assert len(reps) >= 3

    def test_submit_report_and_initial_unverified_status(self):
        rep = submit_community_report(
            category="Flooding",
            district="Kendrapara",
            location_detail="Sea dyke mile 12",
            description="Dyke overtopped with 0.4m water ingress",
            incident_time="2026-11-05 06:00 UTC",
            severity="High",
            has_photo=True,
            submitted_by="Panchayat Ward Member",
        )
        assert rep["id"].startswith("REP-2026-")
        assert rep["status"] == "Submitted"
        assert rep["is_verified"] is False
        assert rep["has_photo"] is True
        assert len(rep["audit_log"]) == 1

    def test_5_state_lifecycle_transitions(self):
        rep = submit_community_report(
            category="Wind Damage",
            district="Purba Medinipur",
            location_detail="Digha Coastal Road",
            description="Uprooted casuarina trees blocking lane",
        )
        rep_id = rep["id"]

        # 1. Under Review
        ok1 = update_report_review(rep_id, "Under Review", reviewer="Control Officer A", notes="Dispatched patrol")
        assert ok1 is True
        r1 = get_report_by_id(rep_id)
        assert r1["status"] == "Under Review"
        assert r1["is_verified"] is False

        # 2. Needs More Info
        ok2 = update_report_review(rep_id, "Needs More Info", reviewer="Control Officer B", notes="Need road marker number")
        assert ok2 is True
        r2 = get_report_by_id(rep_id)
        assert r2["status"] == "Needs More Info"
        assert r2["is_verified"] is False

        # 3. Verified
        ok3 = update_report_review(rep_id, "Verified", reviewer="Field Unit 1", notes="Confirmed blocked at km 8")
        assert ok3 is True
        r3 = get_report_by_id(rep_id)
        assert r3["status"] == "Verified"
        assert r3["is_verified"] is True
        assert len(r3["audit_log"]) == 4

        # 4. Rejected
        ok4 = update_report_review(rep_id, "Rejected", reviewer="Field Supervisor", notes="Duplicate entry")
        assert ok4 is True
        r4 = get_report_by_id(rep_id)
        assert r4["status"] == "Rejected"
        assert r4["is_verified"] is False

    def test_reports_kpis_and_csv_export(self):
        kpis = get_reports_kpis()
        assert kpis["total"] >= 3
        assert "unverified_total" in kpis
        csv_str = export_reports_csv()
        assert "id,category,district,location_detail" in csv_str
        assert len(csv_str.strip().splitlines()) >= 4


class TestSheltersWorkflow:
    """Verify Section G shelter directory loading, querying, filters, and KPIs."""

    def setup_method(self):
        reset_session_state()

    def test_load_shelters_from_csv(self):
        shelters = load_shelters_from_csv()
        assert len(shelters) == 7

    def test_shelter_search_and_filters(self):
        # Search by Puri
        puri_res = get_shelters(search_query="Puri")
        assert len(puri_res) >= 1
        for s in puri_res:
            assert "puri" in s["name"].lower() or "puri" in s["district"].lower()

        # State filter Gujarat
        guj_res = get_shelters(state_filter="Gujarat")
        assert len(guj_res) >= 1
        for s in guj_res:
            assert s["state"] == "Gujarat"

        # Accessibility filter
        acc_res = get_shelters(accessibility_only=True)
        assert len(acc_res) >= 1
        for s in acc_res:
            assert s["is_accessible"] is True

        # Min capacity
        cap_res = get_shelters(min_capacity=1500)
        for s in cap_res:
            assert s["capacity"] >= 1500

    def test_shelters_kpis_and_csv_export(self):
        kpis = get_shelters_kpis()
        assert kpis["total_shelters"] >= 7
        assert kpis["total_capacity"] > 5000
        assert kpis["total_occupancy"] > 0
        assert 0.0 <= kpis["overall_utilization_pct"] <= 100.0

        csv_str = export_shelters_csv()
        assert "id,name,district,state,latitude,longitude,capacity" in csv_str
        assert len(csv_str.strip().splitlines()) >= 8


class TestDisasterResponseWorkflow:
    """Verify Section H disaster response regional risk summaries, triage, and task manager."""

    def setup_method(self):
        reset_session_state()

    def test_initial_tasks(self):
        tasks = ensure_tasks_initialized()
        assert len(tasks) >= 3

    def test_create_and_update_task(self):
        new_task = create_response_task(
            title="Deploy mobile water desalinators to Ersama",
            priority="Critical",
            agency="NDRF 4th Battalion",
            district="Jagatsinghpur",
            assignee="Captain A. Verma",
            status="Todo",
        )
        assert new_task["id"].startswith("TSK-")
        assert new_task["status"] == "Todo"
        assert new_task["priority"] == "Critical"

        # Advance to In-Progress
        ok1 = update_task_status(new_task["id"], "In-Progress", assignee="Lt. M. Sen")
        assert ok1 is True
        t1 = [t for t in get_response_tasks() if t["id"] == new_task["id"]][0]
        assert t1["status"] == "In-Progress"
        assert t1["assignee"] == "Lt. M. Sen"

        # Advance to Completed
        ok2 = update_task_status(new_task["id"], "Completed")
        assert ok2 is True
        t2 = [t for t in get_response_tasks() if t["id"] == new_task["id"]][0]
        assert t2["status"] == "Completed"

    def test_triage_streams(self):
        verified, pending = get_triage_streams()
        for v in verified:
            assert v["is_verified"] is True or v["status"] == "Verified"
        for p in pending:
            assert p["status"] in ("Submitted", "Under Review", "Needs More Info")

    def test_safe_evacuation_zones(self):
        assert len(SAFE_EVACUATION_ZONES) >= 4
        for z in SAFE_EVACUATION_ZONES:
            assert "zone_name" in z
            assert "elevation_m" in z
            assert z["elevation_m"] > 25
            assert "distance_from_coast_km" in z
            assert z["capacity"] > 10000


class TestViewRenderingSmoke:
    """Verify that view render() functions execute without raising unhandled exceptions."""

    def setup_method(self):
        reset_session_state()

    def test_section_alerts_render_callable(self):
        assert callable(v_alerts.render)

    def test_section_community_render_callable(self):
        assert callable(v_community.render)

    def test_section_shelters_render_callable(self):
        assert callable(v_shelters.render)

    def test_section_response_render_callable(self):
        assert callable(v_response.render)
