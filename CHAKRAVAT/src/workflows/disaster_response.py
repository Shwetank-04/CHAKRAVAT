"""CHAKRAVAT Operational Workflow: Disaster Response Engine.

Provides regional risk assessment, incident stream triage (verified vs pending reports),
and interactive response task dispatch management.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

try:
    import streamlit as st
except ImportError:
    st = None  # type: ignore

from src.ui.state import INITIAL_RESPONSE_TASKS, _get_store, init_session_state
from src.workflows.reports import get_community_reports, get_reports_kpis
from src.workflows.shelters import get_shelters_kpis

VALID_TASK_PRIORITIES: Tuple[str, ...] = ("Critical", "High", "Medium", "Low")
VALID_TASK_STATUSES: Tuple[str, ...] = ("Todo", "In-Progress", "Completed")

# Safe Inland Evacuation Muster Zones
SAFE_EVACUATION_ZONES = [
    {
        "zone_name": "Bhubaneswar - Khordha High Ridge",
        "state": "Odisha",
        "elevation_m": 45,
        "distance_from_coast_km": 60,
        "capacity": 25000,
        "facilities": ["AIIMS Medical Campus", "State Police Reserve Staging Hub", "Helipad Transit"],
    },
    {
        "zone_name": "Kharagpur - Midnapore Inland Complex",
        "state": "West Bengal",
        "elevation_m": 38,
        "distance_from_coast_km": 75,
        "capacity": 18000,
        "facilities": ["Railway Staging Yard", "District Hospital Reserve", "Civil Defense Depot"],
    },
    {
        "zone_name": "Anakapalle Inland Relief Corridor",
        "state": "Andhra Pradesh",
        "elevation_m": 32,
        "distance_from_coast_km": 35,
        "capacity": 15000,
        "facilities": ["Highway Logistics Terminal", "Emergency Water Distribution Unit"],
    },
    {
        "zone_name": "Rajkot Elevated Plateau Muster Center",
        "state": "Gujarat",
        "elevation_m": 128,
        "distance_from_coast_km": 85,
        "capacity": 22000,
        "facilities": ["Regional Emergency Operations Center", "State Disaster Warehouse"],
    },
]


@dataclass
class ResponseTaskRecord:
    """Canonical data model for an operational disaster response task."""
    id: str
    title: str
    priority: str = "High"
    agency: str = "NDRF Battalion"
    district: str = "Puri"
    status: str = "Todo"
    assignee: str = "Duty Commander"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _now_utc_str() -> str:
    """Return formatted UTC timestamp."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _normalize_status(status_str: str) -> str:
    """Normalize status aliases (e.g. Open -> Todo, Resolved -> Completed)."""
    s = (status_str or "").strip().lower()
    if s in ("todo", "open", "pending", "new"):
        return "Todo"
    elif s in ("in-progress", "in_progress", "in progress", "active"):
        return "In-Progress"
    elif s in ("completed", "resolved", "done", "closed"):
        return "Completed"
    return "Todo"


def ensure_tasks_initialized() -> List[Dict[str, Any]]:
    """Ensure st.session_state has response tasks initialized."""
    init_session_state()
    store = _get_store()
    if "response_tasks" not in store or not isinstance(store["response_tasks"], list):
        import copy
        # Normalize initial tasks to standard Todo / In-Progress / Completed
        tasks = copy.deepcopy(INITIAL_RESPONSE_TASKS)
        for t in tasks:
            t["status"] = _normalize_status(t.get("status", "Todo"))
        store["response_tasks"] = tasks
    else:
        for t in store["response_tasks"]:
            t["status"] = _normalize_status(t.get("status", "Todo"))
    return store["response_tasks"]


def get_response_tasks(
    status_filter: Optional[str] = None,
    priority_filter: Optional[str] = None,
    district_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieve response tasks matching optional filters."""
    tasks = ensure_tasks_initialized()
    filtered: List[Dict[str, Any]] = []

    for t in tasks:
        t_status = _normalize_status(t.get("status", "Todo"))
        if status_filter and status_filter.lower() != "all":
            if _normalize_status(status_filter).lower() != t_status.lower():
                continue
        if priority_filter and priority_filter.lower() != "all":
            if t.get("priority", "").lower() != priority_filter.lower():
                continue
        if district_filter and district_filter.lower() != "all":
            if t.get("district", "").lower() != district_filter.lower():
                continue
        filtered.append(t)

    return filtered


def create_response_task(
    title: str,
    priority: str = "High",
    agency: str = "NDRF Battalion",
    district: str = "Puri",
    assignee: str = "Field Commander",
    status: str = "Todo",
) -> Dict[str, Any]:
    """Create a new operational disaster response task."""
    store = _get_store()
    tasks = ensure_tasks_initialized()
    now_utc = _now_utc_str()

    counter = len(tasks) + 101
    task_id = f"TSK-{counter:03d}"

    clean_priority = priority.strip().title()
    if clean_priority not in VALID_TASK_PRIORITIES:
        clean_priority = "High"

    clean_status = _normalize_status(status)

    new_task = ResponseTaskRecord(
        id=task_id,
        title=title.strip(),
        priority=clean_priority,
        agency=agency.strip() or "NDRF Field Team",
        district=district.strip() or "Coastal Sector",
        status=clean_status,
        assignee=assignee.strip() or "Duty Officer",
        created_at=now_utc,
        updated_at=now_utc,
    ).to_dict()

    tasks.append(new_task)
    return new_task


def update_task_status(
    task_id: str,
    new_status: str,
    assignee: Optional[str] = None,
) -> bool:
    """Transition a response task's status or reassign officer."""
    tasks = ensure_tasks_initialized()
    now_utc = _now_utc_str()
    clean_status = _normalize_status(new_status)

    for t in tasks:
        if t.get("id") == task_id:
            t["status"] = clean_status
            if assignee:
                t["assignee"] = assignee.strip()
            t["updated_at"] = now_utc
            return True

    return False


def get_response_kpis() -> Dict[str, Any]:
    """Compute comprehensive disaster response KPIs combining tasks, triage, and shelters."""
    tasks = ensure_tasks_initialized()
    total_tasks = len(tasks)
    todo = sum(1 for t in tasks if _normalize_status(t.get("status")) == "Todo")
    in_progress = sum(1 for t in tasks if _normalize_status(t.get("status")) == "In-Progress")
    completed = sum(1 for t in tasks if _normalize_status(t.get("status")) == "Completed")
    critical_high = sum(1 for t in tasks if t.get("priority") in ("Critical", "High") and _normalize_status(t.get("status")) != "Completed")

    reports_kpis = get_reports_kpis()
    shelters_kpis = get_shelters_kpis()

    return {
        "total_tasks": total_tasks,
        "tasks_todo": todo,
        "tasks_in_progress": in_progress,
        "tasks_completed": completed,
        "tasks_critical_high": critical_high,
        "verified_reports_count": reports_kpis.get("verified", 0),
        "pending_triage_count": reports_kpis.get("unverified_total", 0),
        "total_sheltered": shelters_kpis.get("total_occupancy", 0),
        "total_capacity": shelters_kpis.get("total_capacity", 0),
        "shelter_utilization_pct": shelters_kpis.get("overall_utilization_pct", 0.0),
    }


def get_triage_streams() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Return split triage streams: (actionable_verified_incidents, pending_citizen_reports)."""
    verified = get_community_reports(status_filter="Verified")
    all_reports = get_community_reports()
    pending = [r for r in all_reports if r.get("status") in ("Submitted", "Under Review", "Needs More Info")]
    return verified, pending
