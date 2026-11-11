"""CHAKRAVAT Deterministic Session State Management.

Maintains in-memory application state for alerts, community reports,
shelters, response tasks, active storms, and navigation routing.
"""

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import streamlit as st

# Authoritative Section Navigation List
SECTIONS: List[str] = [
    "(A) Cyclone Intelligence Overview",
    "(B) Interactive Map & Track Intelligence",
    "(C) Prediction & Model Evaluation",
    "(D) Data Sources & Data Quality",
    "(E) Alerts & Human Review",
    "(F) Community Reports",
    "(G) Shelter Directory",
    "(H) Disaster Response",
    "(I) About & Methodology",
]

# Section key lookup helper
SECTION_KEY_MAP: Dict[str, str] = {
    "a": SECTIONS[0],
    "overview": SECTIONS[0],
    "b": SECTIONS[1],
    "map": SECTIONS[1],
    "c": SECTIONS[2],
    "prediction": SECTIONS[2],
    "d": SECTIONS[3],
    "data": SECTIONS[3],
    "data_sources": SECTIONS[3],
    "e": SECTIONS[4],
    "alerts": SECTIONS[4],
    "f": SECTIONS[5],
    "community": SECTIONS[5],
    "reports": SECTIONS[5],
    "g": SECTIONS[6],
    "shelters": SECTIONS[6],
    "h": SECTIONS[7],
    "response": SECTIONS[7],
    "i": SECTIONS[8],
    "about": SECTIONS[8],
    "methodology": SECTIONS[8],
}

# Seed storms metadata
BENCHMARK_STORMS: Dict[str, str] = {
    "NIO_2017_01": "Cyclone OCKHI (2017) — Extremely Severe",
    "NIO_2018_01": "Cyclone TITLI (2018) — Very Severe",
    "2019117N12089": "Cyclone FANI (2019) — Extremely Severe",
    "2020137N10086": "Cyclone AMPHAN (2020) — Super Cyclone",
    "2021134N11072": "Cyclone TAUKTAE (2021) — Extremely Severe",
    "2021144N16090": "Cyclone YAAS (2021) — Very Severe",
    "NIO_2022_01": "Cyclone ASANI (2022) — Very Severe",
    "2023157N13066": "Cyclone BIPARJOY (2023) — Extremely Severe",
}

# Canonical storm registry.
# The app historically juggled three identifier styles (IBTrACS id, bundled-CSV id and bare
# storm name), which caused the sidebar, overview, map and prediction views to disagree about
# which storm was "active". Everything now funnels through ``canonical_storm_id``.
STORM_CATALOG: Dict[str, Dict[str, str]] = {
    "NIO_2017_01": {"name": "OCKHI", "csv_id": "NIO_2017_01"},
    "NIO_2018_01": {"name": "TITLI", "csv_id": "NIO_2018_01"},
    "2019117N12089": {"name": "FANI", "csv_id": "NIO_2019_01B"},
    "2020137N10086": {"name": "AMPHAN", "csv_id": "NIO_2020_01B"},
    "2021134N11072": {"name": "TAUKTAE", "csv_id": "NIO_2021_01A"},
    "2021144N16090": {"name": "YAAS", "csv_id": "NIO_2021_02B"},
    "NIO_2022_01": {"name": "ASANI", "csv_id": "NIO_2022_01"},
    "2023157N13066": {"name": "BIPARJOY", "csv_id": "NIO_2023_02A"},
}
DEFAULT_STORM_ID: str = "2019117N12089"


def canonical_storm_id(value: Any) -> str:
    """Resolve an IBTrACS id, bundled-CSV id (suffix optional), storm name or display label.

    Unknown values fall back to the default benchmark storm so callers never crash.
    """
    text = str(value or "").strip().upper()
    if not text:
        return DEFAULT_STORM_ID
    for sid, meta in STORM_CATALOG.items():
        csv_id = meta["csv_id"].upper()
        if text in (sid.upper(), csv_id, meta["name"]):
            return sid
        if len(text) >= 10 and csv_id.startswith(text):  # "NIO_2019_01" -> "NIO_2019_01B"
            return sid
    for sid, meta in STORM_CATALOG.items():  # e.g. "CYCLONE FANI (2019) - ..."
        if meta["name"] in text:
            return sid
    return DEFAULT_STORM_ID


def storm_name_for(value: Any) -> str:
    """Return the upper-case storm name (e.g. ``FANI``) for any identifier style."""
    return STORM_CATALOG[canonical_storm_id(value)]["name"]


# Seed Alerts (North Indian Ocean operational context)
INITIAL_ALERTS: List[Dict[str, Any]] = [
    {
        "id": "ALT-2026-001",
        "severity": "Warning",
        "region": "Puri & Jagatsinghpur Coastal Belt (Odisha)",
        "headline": "Severe Storm Surge & Coastal Gale Threat",
        "description": "Peak sustained winds exceeding 135 km/h with 1.5-2.0m tidal surge expected during next 24 hours.",
        "evidence": "Central pressure estimated at 962 hPa; numerical persistence indicates landfall trajectory near Puri.",
        "valid_until": "2026-11-06 18:00 UTC",
        "status": "Pending",
        "issued_by": "Automated Trigger (Numerical Persistence)",
        "created_at": "2026-11-05 04:00 UTC",
        "reviewer_comments": "",
        "audit_history": [
            {
                "timestamp": "2026-11-05 04:00 UTC",
                "actor": "System Rule Engine",
                "action": "Created Draft Alert",
                "note": "Automated trigger: 24h projected landfall within 50km coastal buffer.",
            }
        ],
    },
    {
        "id": "ALT-2026-002",
        "severity": "Watch",
        "region": "Kendrapara & Balasore Coastal Sectors (Odisha)",
        "headline": "Coastal Gale Watch (80-95 km/h)",
        "description": "Squally winds and heavy rainfall squalls associated with outer spiral bands.",
        "evidence": "Doppler radar echo reflectivity > 45 dBZ approaching coastline.",
        "valid_until": "2026-11-07 00:00 UTC",
        "status": "Approved",
        "issued_by": "Senior Coastal Forecaster",
        "created_at": "2026-11-04 18:00 UTC",
        "reviewer_comments": "Verified against Paradip Doppler radar feed. Issued for public watch.",
        "audit_history": [
            {
                "timestamp": "2026-11-04 18:00 UTC",
                "actor": "Senior Coastal Forecaster",
                "action": "Created Draft Alert",
                "note": "Initial watch bulletin drafted.",
            },
            {
                "timestamp": "2026-11-04 18:30 UTC",
                "actor": "Lead Meteorological Officer",
                "action": "Approved",
                "note": "Concurred with Doppler radar returns. Public watch bulletin broadcast.",
            },
        ],
    },
    {
        "id": "ALT-2026-003",
        "severity": "Extreme",
        "region": "West-Central & Northwest Bay of Bengal",
        "headline": "Extreme Marine & Deep-Sea Navigation Warning",
        "description": "Phenomenal sea state, wave heights 6.0m to 9.5m. Total suspension of all fishing and offshore operations.",
        "evidence": "Synoptic buoy readings 23091 and 23093 reporting wave heights > 7.2m.",
        "valid_until": "2026-11-07 12:00 UTC",
        "status": "Approved",
        "issued_by": "Maritime Operations Center",
        "created_at": "2026-11-04 12:00 UTC",
        "reviewer_comments": "Mandatory Coast Guard broadcast active.",
        "audit_history": [
            {
                "timestamp": "2026-11-04 12:00 UTC",
                "actor": "Maritime Operations Center",
                "action": "Created Draft Alert",
                "note": "Buoy network triggered extreme sea state threshold.",
            },
            {
                "timestamp": "2026-11-04 12:15 UTC",
                "actor": "Port Authority Reviewer",
                "action": "Approved",
                "note": "Flag 4 hoisted across Paradip and Dhamra ports.",
            },
        ],
    },
]

# Seed Community Reports
INITIAL_REPORTS: List[Dict[str, Any]] = [
    {
        "id": "REP-2026-101",
        "category": "Flooding",
        "district": "Puri",
        "location_detail": "Pentakota Fishermen Colony, Marine Drive",
        "description": "Seawater breach across beach embankment; coastal road inundated 0.5m with debris.",
        "severity": "High",
        "status": "Verified",
        "is_verified": True,
        "has_photo": True,
        "timestamp": "2026-11-05 03:30 UTC",
        "reviewer_notes": "Ground verification confirmed by Puri Fire & Rescue Station 1.",
        "reviewed_by": "Inspector P. Mohanty",
        "reviewed_at": "2026-11-05 04:10 UTC",
    },
    {
        "id": "REP-2026-102",
        "category": "Wind Damage",
        "district": "Jagatsinghpur",
        "location_detail": "Paradeep Port approach road near Lockgate",
        "description": "Two high-tension electricity poles collapsed across road, blocking inbound relief trucks.",
        "severity": "Critical",
        "status": "Under Review",
        "is_verified": False,
        "has_photo": True,
        "timestamp": "2026-11-05 04:15 UTC",
        "reviewer_notes": "OPTCL transmission repair crew dispatched for on-site assessment.",
        "reviewed_by": "Disaster Response Desk",
        "reviewed_at": "2026-11-05 04:25 UTC",
    },
    {
        "id": "REP-2026-103",
        "category": "Storm Surge",
        "district": "Ganjam",
        "location_detail": "Gopalpur on Sea Beach Promenade",
        "description": "Wave runup cresting over seawall onto tourist promenade. No casualties or breach yet.",
        "severity": "Medium",
        "status": "Submitted",
        "is_verified": False,
        "has_photo": False,
        "timestamp": "2026-11-05 05:00 UTC",
        "reviewer_notes": "",
        "reviewed_by": None,
        "reviewed_at": None,
    },
    {
        "id": "REP-2026-104",
        "category": "Road Blocked",
        "district": "Balasore",
        "location_detail": "Chandipur Coastal Highway (SH-19)",
        "description": "Large banyan tree fallen across both lanes near Mile 4; evacuation buses halted.",
        "severity": "High",
        "status": "Submitted",
        "is_verified": False,
        "has_photo": False,
        "timestamp": "2026-11-05 05:20 UTC",
        "reviewer_notes": "",
        "reviewed_by": None,
        "reviewed_at": None,
    },
]

def _backfill_seed_reports(reports: List[Dict[str, Any]]) -> None:
    """Give seed reports the same fields live submissions have (incident_time, observer, audit trail)."""
    for r in reports:
        r.setdefault("incident_time", r.get("timestamp", "-"))
        r.setdefault("submitted_by", "Citizen Observer")
        if "audit_log" not in r:
            log = [{
                "timestamp": r.get("timestamp", "-"), "actor": "System Intake", "action": "Report Submitted",
                "note": f"Citizen report submitted by {r['submitted_by']}",
                "reviewer": "System Intake", "previous_status": "None", "new_status": "Submitted", "notes": "",
            }]
            if r.get("reviewed_by"):
                log.append({
                    "timestamp": r.get("reviewed_at") or r.get("timestamp", "-"), "actor": r["reviewed_by"],
                    "action": r["status"], "note": r.get("reviewer_notes") or f"Status set to {r['status']}",
                    "reviewer": r["reviewed_by"], "previous_status": "Submitted", "new_status": r["status"],
                    "notes": r.get("reviewer_notes", ""),
                })
            r["audit_log"] = log


_backfill_seed_reports(INITIAL_REPORTS)

# Seed Shelters (>=7 illustrative records)
INITIAL_SHELTERS: List[Dict[str, Any]] = [
    {
        "id": "SHL-OD-001",
        "name": "Pentakota Multipurpose Cyclone Shelter",
        "district": "Puri",
        "state": "Odisha",
        "latitude": 19.798,
        "longitude": 85.834,
        "capacity": 1500,
        "occupancy": 420,
        "contact_phone": "+91 6752 222100",
        "is_accessible": True,
        "features": ["Diesel Generator", "Medical First Aid Post", "Potable Water Tank", "Ramp Access"],
        "last_verified": "2026-11-04",
        "source_label": "Illustrative Demo Dataset (OSDMA Simulation)",
    },
    {
        "id": "SHL-OD-002",
        "name": "Astaranga Coastal High School Shelter",
        "district": "Puri",
        "state": "Odisha",
        "latitude": 19.985,
        "longitude": 86.265,
        "capacity": 1200,
        "occupancy": 850,
        "contact_phone": "+91 6752 238201",
        "is_accessible": True,
        "features": ["Diesel Generator", "Potable Water Tank", "Sanitation Block"],
        "last_verified": "2026-11-03",
        "source_label": "Illustrative Demo Dataset (OSDMA Simulation)",
    },
    {
        "id": "SHL-OD-003",
        "name": "Paradeep Port Coastal Relief Center",
        "district": "Jagatsinghpur",
        "state": "Odisha",
        "latitude": 20.316,
        "longitude": 86.611,
        "capacity": 2000,
        "occupancy": 1750,
        "contact_phone": "+91 6722 221055",
        "is_accessible": True,
        "features": ["Emergency Power", "Doctor On-Duty", "Community Kitchen", "Helipad Vicinity"],
        "last_verified": "2026-11-04",
        "source_label": "Illustrative Demo Dataset (OSDMA Simulation)",
    },
    {
        "id": "SHL-OD-004",
        "name": "Ersama Block Multipurpose Shelter",
        "district": "Jagatsinghpur",
        "state": "Odisha",
        "latitude": 20.183,
        "longitude": 86.452,
        "capacity": 1000,
        "occupancy": 310,
        "contact_phone": "+91 6722 245112",
        "is_accessible": False,
        "features": ["Solar Hybrid Lighting", "Deep Tube Well"],
        "last_verified": "2026-11-02",
        "source_label": "Illustrative Demo Dataset (OSDMA Simulation)",
    },
    {
        "id": "SHL-OD-005",
        "name": "Chandipur High School Relief Center",
        "district": "Balasore",
        "state": "Odisha",
        "latitude": 21.467,
        "longitude": 87.017,
        "capacity": 800,
        "occupancy": 120,
        "contact_phone": "+91 6782 272300",
        "is_accessible": True,
        "features": ["Potable Water Tank", "Ramp Access", "Emergency Radio"],
        "last_verified": "2026-11-04",
        "source_label": "Illustrative Demo Dataset (OSDMA Simulation)",
    },
    {
        "id": "SHL-WB-006",
        "name": "Digha Multipurpose Cyclone Shelter",
        "district": "Purba Medinipur",
        "state": "West Bengal",
        "latitude": 21.626,
        "longitude": 87.523,
        "capacity": 1800,
        "occupancy": 650,
        "contact_phone": "+91 3220 266100",
        "is_accessible": True,
        "features": ["Diesel Generator", "Medical First Aid Post", "Potable Water", "Wheelchair Access"],
        "last_verified": "2026-11-04",
        "source_label": "Illustrative Demo Dataset (WB-DM Simulation)",
    },
    {
        "id": "SHL-GJ-007",
        "name": "Mandvi Coastal Evacuation Shelter",
        "district": "Kutch",
        "state": "Gujarat",
        "latitude": 22.833,
        "longitude": 69.355,
        "capacity": 1400,
        "occupancy": 200,
        "contact_phone": "+91 2834 222040",
        "is_accessible": True,
        "features": ["Diesel Generator", "Potable Water Tank", "Emergency Medicines"],
        "last_verified": "2026-11-01",
        "source_label": "Illustrative Demo Dataset (GSDMA Simulation)",
    },
]

# Seed Response Tasks
INITIAL_RESPONSE_TASKS: List[Dict[str, Any]] = [
    {
        "id": "TSK-101",
        "title": "Pre-position 4th NDRF Battalion inflatable boats at Pentakota",
        "agency": "NDRF",
        "district": "Puri",
        "priority": "High",
        "status": "In Progress",
        "assignee": "Inspector S. Patnaik",
        "updated_at": "2026-11-05 04:30 UTC",
    },
    {
        "id": "TSK-102",
        "title": "Clear uprooted electricity poles on Paradeep Port approach road",
        "agency": "OPTCL / SDRF",
        "district": "Jagatsinghpur",
        "priority": "Critical",
        "status": "Open",
        "assignee": "Rapid Restorations Team 2",
        "updated_at": "2026-11-05 04:20 UTC",
    },
    {
        "id": "TSK-103",
        "title": "Replenish emergency dry rations and water purification tablets at Ersama Shelter",
        "agency": "District Civil Supplies",
        "district": "Jagatsinghpur",
        "priority": "Medium",
        "status": "In Progress",
        "assignee": "Logistics Officer M. Das",
        "updated_at": "2026-11-05 03:00 UTC",
    },
    {
        "id": "TSK-104",
        "title": "Deploy mobile medical unit with antivenom and trauma kits to Chandipur",
        "agency": "State Health Dept",
        "district": "Balasore",
        "priority": "High",
        "status": "Open",
        "assignee": "Dr. R. Mishra",
        "updated_at": "2026-11-05 05:00 UTC",
    },
    {
        "id": "TSK-105",
        "title": "Issue coastal broadcast notice to all mechanized trawlers in Bay of Bengal",
        "agency": "Coast Guard / Fisheries",
        "district": "Regional Maritime",
        "priority": "Critical",
        "status": "Resolved",
        "assignee": "Commander K. Roy",
        "updated_at": "2026-11-04 14:00 UTC",
    },
]

# Fallback store when running outside Streamlit runtime (e.g. unit tests)
_FALLBACK_STORE: Dict[str, Any] = {}


def _get_store() -> Any:
    """Retrieve the active store (st.session_state or fallback dictionary)."""
    try:
        # Check if st.session_state is initialized and available
        _ = st.session_state
        return st.session_state
    except Exception:
        global _FALLBACK_STORE
        return _FALLBACK_STORE


def init_session_state(force_reset: bool = False) -> None:
    """Deterministically initialize session state keys if not already present."""
    store = _get_store()

    if force_reset or not store.get("initialized", False):
        store["initialized"] = True
        store["current_section"] = SECTIONS[0]
        store["selected_storm_id"] = "2019117N12089"  # Cyclone FANI
        store["alerts"] = deepcopy(INITIAL_ALERTS)
        store["community_reports"] = deepcopy(INITIAL_REPORTS)
        store["shelters"] = deepcopy(INITIAL_SHELTERS)
        store["response_tasks"] = deepcopy(INITIAL_RESPONSE_TASKS)
        store["alert_counter"] = len(INITIAL_ALERTS) + 1
        store["report_counter"] = len(INITIAL_REPORTS) + 101


def reset_session_state() -> None:
    """Reset all session state variables back to factory demo defaults."""
    init_session_state(force_reset=True)


def get_current_section() -> str:
    """Return the currently selected section name."""
    store = _get_store()
    init_session_state()
    return store.get("current_section", SECTIONS[0])


def set_current_section(section: str) -> None:
    """Set the currently active section (accepts letter key, nickname, or full string)."""
    store = _get_store()
    init_session_state()
    cleaned = (section or "").strip().lower()
    target = SECTION_KEY_MAP.get(cleaned, section)
    resolved = target if target in SECTIONS else section
    store["current_section"] = resolved
    # The nav widget owns ``nav_radio_selection``. Writing it after the widget has been created
    # raises StreamlitAPIException (this crashed every shortcut/tour button). The nav bar re-syncs
    # itself from ``current_section`` before it is instantiated, so a failed write is harmless.
    try:
        store["nav_radio_selection"] = resolved
    except Exception:
        pass


def get_active_storm_id() -> str:
    """Return the currently selected storm ID."""
    store = _get_store()
    init_session_state()
    return canonical_storm_id(store.get("selected_storm_id", DEFAULT_STORM_ID))


def set_active_storm_id(storm_id: str) -> None:
    """Set the currently selected storm ID."""
    store = _get_store()
    init_session_state()
    store["selected_storm_id"] = canonical_storm_id(storm_id)


# Alert Management Workflow
def get_alerts() -> List[Dict[str, Any]]:
    """Return the list of all alerts in session state."""
    store = _get_store()
    init_session_state()
    return store.get("alerts", [])


def add_alert(
    region: str,
    severity: str,
    headline: str,
    description: str,
    evidence: str,
    valid_until: str,
    issued_by: str = "Forecaster Desk",
) -> Dict[str, Any]:
    """Create and append a new alert with timestamp and audit history."""
    store = _get_store()
    init_session_state()
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    counter = store.get("alert_counter", 10)
    store["alert_counter"] = counter + 1
    alert_id = f"ALT-2026-{counter:03d}"

    new_alert: Dict[str, Any] = {
        "id": alert_id,
        "region": region,
        "severity": severity,
        "headline": headline,
        "description": description,
        "evidence": evidence,
        "valid_until": valid_until,
        "status": "Pending",
        "issued_by": issued_by,
        "created_at": now_utc,
        "reviewer_comments": "",
        "audit_history": [
            {
                "timestamp": now_utc,
                "actor": issued_by,
                "action": "Created Draft Alert",
                "note": f"Initial bulletin draft: {headline}",
            }
        ],
    }

    store["alerts"].append(new_alert)
    return new_alert


def update_alert_status(
    alert_id: str,
    new_status: str,
    actor: str = "Lead Reviewer",
    notes: str = "",
) -> bool:
    """Update alert review status and append to audit trail."""
    store = _get_store()
    init_session_state()
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    for alert in store.get("alerts", []):
        if alert.get("id") == alert_id:
            alert["status"] = new_status
            alert["reviewer_comments"] = notes
            alert.setdefault("audit_history", []).append({
                "timestamp": now_utc,
                "actor": actor,
                "action": new_status,
                "note": notes or f"Status transitioned to {new_status}",
            })
            return True
    return False


# Community Reports Workflow
def get_community_reports() -> List[Dict[str, Any]]:
    """Return all community reports in session state."""
    store = _get_store()
    init_session_state()
    return store.get("community_reports", [])


def add_community_report(
    category: str,
    district: str,
    location_detail: str,
    description: str,
    severity: str = "Medium",
    has_photo: bool = False,
) -> Dict[str, Any]:
    """Submit a crowdsourced community incident report."""
    store = _get_store()
    init_session_state()
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    counter = store.get("report_counter", 105)
    store["report_counter"] = counter + 1
    report_id = f"REP-2026-{counter:03d}"

    new_report: Dict[str, Any] = {
        "id": report_id,
        "category": category,
        "district": district,
        "location_detail": location_detail,
        "description": description,
        "severity": severity,
        "status": "Submitted",
        "is_verified": False,
        "has_photo": has_photo,
        "timestamp": now_utc,
        "reviewer_notes": "",
        "reviewed_by": None,
        "reviewed_at": None,
    }

    store["community_reports"].append(new_report)
    return new_report


def update_report_status(
    report_id: str,
    new_status: str,
    reviewer: str = "Disaster Review Desk",
    notes: str = "",
) -> bool:
    """Review and transition a community report status."""
    store = _get_store()
    init_session_state()
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    for report in store.get("community_reports", []):
        if report.get("id") == report_id:
            report["status"] = new_status
            report["reviewer_notes"] = notes
            report["reviewed_by"] = reviewer
            report["reviewed_at"] = now_utc
            report["is_verified"] = (new_status.strip().lower() == "verified")
            return True
    return False


# Shelter Directory Accessors
def get_shelters(
    district_filter: Optional[str] = None,
    accessibility_only: bool = False,
) -> List[Dict[str, Any]]:
    """Retrieve shelter records with optional filtering."""
    store = _get_store()
    init_session_state()
    shelters = store.get("shelters", [])

    filtered = []
    for shl in shelters:
        if district_filter and district_filter != "All" and shl.get("district") != district_filter:
            continue
        if accessibility_only and not shl.get("is_accessible", False):
            continue
        filtered.append(shl)
    return filtered


# Response Tasks Accessors
def get_response_tasks(status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve emergency response task items."""
    store = _get_store()
    init_session_state()
    tasks = store.get("response_tasks", [])
    if status_filter and status_filter != "All":
        return [t for t in tasks if t.get("status") == status_filter]
    return tasks


def update_task_status(
    task_id: str,
    new_status: str,
    assignee: Optional[str] = None,
) -> bool:
    """Update the status or assignee of an operational task."""
    store = _get_store()
    init_session_state()
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    for task in store.get("response_tasks", []):
        if task.get("id") == task_id:
            task["status"] = new_status
            if assignee:
                task["assignee"] = assignee
            task["updated_at"] = now_utc
            return True
    return False


# ---------------------------------------------------------------------------
# Guided tour (replaces the old one-shot "judge tour" buttons)
# ---------------------------------------------------------------------------
TOUR_STEPS: List[Dict[str, str]] = [
    {"section": SECTIONS[0], "title": "Overview", "tip": "Basin situation, readiness metrics and the 5-storm benchmark library. Pick a storm to drive the whole app."},
    {"section": SECTIONS[1], "title": "Storm Map", "tip": "Hit Play to replay the storm fix-by-fix, or drag the scrubber. Hover any fix for telemetry."},
    {"section": SECTIONS[2], "title": "ML Engine", "tip": "Storm-level splits, persistence baselines and honest held-out errors. No leakage, no inflated scores."},
    {"section": SECTIONS[4], "title": "Alert Workflow", "tip": "Human-in-the-loop review: draft, approve or reject a bulletin and watch the audit trail update."},
]


def get_tour_step() -> Optional[int]:
    """Return the active tour step index, or None when the tour is not running."""
    return _get_store().get("tour_step")


def start_tour() -> None:
    go_to_tour_step(0)


def go_to_tour_step(step: int) -> None:
    """Jump to a tour step (clamped). Safe to use as an ``on_click`` callback."""
    store = _get_store()
    step = max(0, min(int(step), len(TOUR_STEPS) - 1))
    store["tour_step"] = step
    set_current_section(TOUR_STEPS[step]["section"])


def end_tour() -> None:
    _get_store()["tour_step"] = None
