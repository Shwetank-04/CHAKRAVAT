"""CHAKRAVAT Operational Workflow: Community Reports Engine.

Manages crowdsourced citizen incident reports with strict 5-state verification lifecycle:
Submitted -> Under Review -> Verified / Rejected / Needs More Info.
Ensures unverified reports are clearly tagged and auditable.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import io
from typing import Any, Dict, List, Optional, Tuple

try:
    import streamlit as st
except ImportError:
    st = None  # type: ignore

from src.ui.state import INITIAL_REPORTS, _get_store, init_session_state

VALID_REPORT_CATEGORIES: Tuple[str, ...] = (
    "Flooding",
    "Wind Damage",
    "Storm Surge",
    "Structural",
    "Infrastructure",
    "Power / Grid",
    "Road Blocked",
    "Other",
)

VALID_REPORT_STATUSES: Tuple[str, ...] = (
    "Submitted",
    "Under Review",
    "Verified",
    "Rejected",
    "Needs More Info",
)


@dataclass
class ReportAuditEntry:
    """Audit log entry for a status transition on a community report."""
    timestamp: str
    reviewer: str
    previous_status: str
    new_status: str
    notes: str

    def to_dict(self) -> Dict[str, str]:
        """Serialize with both the workflow keys and the keys audit_timeline() renders."""
        d = asdict(self)
        d.update({
            "actor": self.reviewer,
            "action": self.new_status,
            "note": self.notes,
        })
        return d


@dataclass
class CommunityReportRecord:
    """Canonical data model for a citizen disaster observation report."""
    id: str
    category: str
    district: str
    location_detail: str
    incident_time: str
    description: str
    severity: str = "Medium"
    has_photo: bool = False
    status: str = "Submitted"
    is_verified: bool = False
    submitted_by: str = "Citizen Volunteer"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    reviewer_notes: str = ""
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    audit_log: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _now_utc_str() -> str:
    """Return formatted UTC timestamp."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def ensure_reports_initialized() -> List[Dict[str, Any]]:
    """Ensure st.session_state has community reports initialized."""
    init_session_state()
    store = _get_store()
    if "community_reports" not in store or not isinstance(store["community_reports"], list):
        import copy
        store["community_reports"] = copy.deepcopy(INITIAL_REPORTS)
    return store["community_reports"]


def get_community_reports(
    status_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
    district_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieve community reports with optional multi-attribute filtering."""
    reports = ensure_reports_initialized()
    filtered: List[Dict[str, Any]] = []

    for rep in reports:
        if status_filter and status_filter.lower() != "all":
            if rep.get("status", "").lower() != status_filter.lower():
                continue
        if category_filter and category_filter.lower() != "all":
            if rep.get("category", "").lower() != category_filter.lower():
                continue
        if district_filter and district_filter.lower() != "all":
            if rep.get("district", "").lower() != district_filter.lower():
                continue
        filtered.append(rep)

    return filtered


def get_report_by_id(report_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single community report by its unique ID."""
    reports = ensure_reports_initialized()
    for rep in reports:
        if rep.get("id") == report_id:
            return rep
    return None


def submit_community_report(
    category: str,
    district: str,
    description: str,
    incident_time: Optional[str] = None,
    location_detail: str = "",
    severity: str = "Medium",
    has_photo: bool = False,
    submitted_by: str = "Citizen Volunteer",
) -> Dict[str, Any]:
    """Submit a new crowdsourced incident report."""
    store = _get_store()
    ensure_reports_initialized()
    now_utc = _now_utc_str()

    counter = store.get("report_counter", len(store["community_reports"]) + 101)
    store["report_counter"] = counter + 1
    report_id = f"REP-2026-{counter:03d}"

    clean_category = category.strip()
    if clean_category not in VALID_REPORT_CATEGORIES:
        clean_category = "Flooding"

    clean_time = incident_time.strip() if incident_time else now_utc

    initial_audit = ReportAuditEntry(
        timestamp=now_utc,
        reviewer="System Intake",
        previous_status="None",
        new_status="Submitted",
        notes=f"Citizen report submitted by {submitted_by.strip() or 'Citizen Observer'}",
    ).to_dict()

    new_report = CommunityReportRecord(
        id=report_id,
        category=clean_category,
        district=district.strip() or "Coastal Sector",
        location_detail=location_detail.strip() or "Reported location",
        incident_time=clean_time,
        description=description.strip(),
        severity=severity.strip().title(),
        has_photo=bool(has_photo),
        status="Submitted",
        is_verified=False,
        submitted_by=submitted_by.strip() or "Citizen Volunteer",
        timestamp=now_utc,
        reviewer_notes="",
        reviewed_by=None,
        reviewed_at=None,
        audit_log=[initial_audit],
    ).to_dict()

    store["community_reports"].append(new_report)
    return new_report


def update_report_review(
    report_id: str,
    new_status: str,
    reviewer: str = "Disaster Review Desk",
    notes: str = "",
) -> bool:
    """Review and transition a community report across the 5-state lifecycle."""
    reports = ensure_reports_initialized()
    now_utc = _now_utc_str()

    # Normalize new status
    clean_status = new_status.strip().title()
    if clean_status == "Under_Review" or clean_status == "Under-Review":
        clean_status = "Under Review"
    elif clean_status == "Needs_More_Info" or clean_status == "Needs-More-Info":
        clean_status = "Needs More Info"

    if clean_status not in VALID_REPORT_STATUSES:
        return False

    for rep in reports:
        if rep.get("id") == report_id:
            prev_status = rep.get("status", "Submitted")
            rep["status"] = clean_status
            if notes.strip():
                rep["reviewer_notes"] = notes.strip()
            rep["reviewed_by"] = reviewer.strip() or "Disaster Response Officer"
            rep["reviewed_at"] = now_utc
            rep["is_verified"] = (clean_status == "Verified")

            audit_entry = ReportAuditEntry(
                timestamp=now_utc,
                reviewer=reviewer.strip() or "Disaster Response Officer",
                previous_status=prev_status,
                new_status=clean_status,
                notes=notes.strip() or f"Status transitioned to {clean_status}",
            ).to_dict()

            if "audit_log" not in rep or not isinstance(rep["audit_log"], list):
                rep["audit_log"] = []
            rep["audit_log"].append(audit_entry)
            return True

    return False


def get_reports_kpis() -> Dict[str, int]:
    """Compute summary counts across community report verification states."""
    reports = ensure_reports_initialized()
    total = len(reports)
    submitted = sum(1 for r in reports if r.get("status") == "Submitted")
    under_review = sum(1 for r in reports if r.get("status") == "Under Review")
    verified = sum(1 for r in reports if r.get("status") == "Verified")
    rejected = sum(1 for r in reports if r.get("status") == "Rejected")
    needs_info = sum(1 for r in reports if r.get("status") == "Needs More Info")

    return {
        "total": total,
        "submitted": submitted,
        "under_review": under_review,
        "verified": verified,
        "rejected": rejected,
        "needs_info": needs_info,
        "unverified_total": submitted + under_review + needs_info,
    }


def export_reports_csv() -> str:
    """Export all community reports into RFC 4180 CSV format."""
    reports = ensure_reports_initialized()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "category", "district", "location_detail", "incident_time",
        "description", "severity", "has_photo", "status", "is_verified",
        "submitted_by", "timestamp", "reviewer_notes", "reviewed_by", "reviewed_at"
    ])
    for r in reports:
        writer.writerow([
            r.get("id", ""),
            r.get("category", ""),
            r.get("district", ""),
            r.get("location_detail", ""),
            r.get("incident_time", ""),
            r.get("description", ""),
            r.get("severity", ""),
            r.get("has_photo", False),
            r.get("status", ""),
            r.get("is_verified", False),
            r.get("submitted_by", ""),
            r.get("timestamp", ""),
            r.get("reviewer_notes", ""),
            r.get("reviewed_by", ""),
            r.get("reviewed_at", ""),
        ])
    return output.getvalue()
