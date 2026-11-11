"""CHAKRAVAT Operational Workflow: Alerts & Human Review Engine.

Manages coastal alerts, meteorological threat advisories, and the operational
human-in-the-loop review lifecycle (Pending -> Approved / Rejected / Changes Requested)
with immutable timestamped audit trails.
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

from src.ui.state import INITIAL_ALERTS, _get_store, init_session_state

VALID_SEVERITIES: Tuple[str, ...] = ("Watch", "Warning", "Severe", "Extreme")
VALID_STATUSES: Tuple[str, ...] = ("Pending", "Approved", "Rejected", "Changes Requested")


@dataclass
class AlertAuditEntry:
    """Represents a single immutable entry in the alert review audit trail."""
    timestamp: str
    actor: str
    action: str
    note: str

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


@dataclass
class AlertRecord:
    """Canonical data model for a coastal cyclone alert."""
    id: str
    severity: str
    region: str
    headline: str
    description: str
    evidence: str
    valid_until: str
    status: str = "Pending"
    issued_by: str = "Forecaster Duty Desk"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    reviewer_comments: str = ""
    audit_history: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _now_utc_str() -> str:
    """Return formatted UTC timestamp."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def ensure_alerts_initialized() -> List[Dict[str, Any]]:
    """Ensure st.session_state has alerts initialized."""
    init_session_state()
    store = _get_store()
    if "alerts" not in store or not isinstance(store["alerts"], list):
        import copy
        store["alerts"] = copy.deepcopy(INITIAL_ALERTS)
    return store["alerts"]


def get_alerts(
    status_filter: Optional[str] = None,
    severity_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieve all alerts matching optional status and severity filters."""
    alerts = ensure_alerts_initialized()
    filtered: List[Dict[str, Any]] = []

    for alert in alerts:
        if status_filter and status_filter.lower() != "all":
            if alert.get("status", "").lower() != status_filter.lower():
                continue
        if severity_filter and severity_filter.lower() != "all":
            if alert.get("severity", "").lower() != severity_filter.lower():
                continue
        filtered.append(alert)

    return filtered


def get_alert_by_id(alert_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single alert by its unique identifier."""
    alerts = ensure_alerts_initialized()
    for alert in alerts:
        if alert.get("id") == alert_id:
            return alert
    return None


def create_alert(
    severity: str,
    region: str,
    headline: str,
    description: str,
    evidence: str,
    valid_until: str,
    issued_by: str = "Forecaster Duty Desk",
) -> Dict[str, Any]:
    """Create a new operational alert and append to session state with audit trail."""
    clean_severity = severity.strip().title()
    if clean_severity not in VALID_SEVERITIES:
        # Default fallback if slightly off
        clean_severity = "Warning" if "warn" in clean_severity.lower() else "Severe"

    store = _get_store()
    ensure_alerts_initialized()
    counter = store.get("alert_counter", len(store["alerts"]) + 1)
    store["alert_counter"] = counter + 1

    alert_id = f"ALT-2026-{counter:03d}"
    now_utc = _now_utc_str()

    initial_audit = AlertAuditEntry(
        timestamp=now_utc,
        actor=issued_by.strip() or "Forecaster Duty Desk",
        action="Created Draft Alert",
        note=f"Initial draft bulletin issued for {region}: {headline}",
    ).to_dict()

    new_alert = AlertRecord(
        id=alert_id,
        severity=clean_severity,
        region=region.strip() or "North Indian Ocean Coastal Zone",
        headline=headline.strip(),
        description=description.strip(),
        evidence=evidence.strip(),
        valid_until=valid_until.strip(),
        status="Pending",
        issued_by=issued_by.strip() or "Forecaster Duty Desk",
        created_at=now_utc,
        reviewer_comments="",
        audit_history=[initial_audit],
    ).to_dict()

    store["alerts"].append(new_alert)
    return new_alert


def review_alert(
    alert_id: str,
    action: str,
    actor: str = "Lead Duty Forecaster",
    notes: str = "",
) -> bool:
    """Execute a human-in-the-loop review action on an alert."""
    alerts = ensure_alerts_initialized()
    now_utc = _now_utc_str()
    actor_name = actor.strip() or "Lead Reviewer"

    # Normalize action
    action_clean = action.strip().lower()
    if "approve" in action_clean:
        new_status = "Approved"
        action_name = "Approved Bulletin"
    elif "reject" in action_clean:
        new_status = "Rejected"
        action_name = "Rejected Bulletin"
    elif "change" in action_clean or "request" in action_clean:
        new_status = "Changes Requested"
        action_name = "Changes Requested"
    elif action in VALID_STATUSES:
        new_status = action
        action_name = f"Marked {action}"
    else:
        new_status = "Pending"
        action_name = "Updated Bulletin"

    for alert in alerts:
        if alert.get("id") == alert_id:
            alert["status"] = new_status
            alert["reviewer_comments"] = notes.strip()

            audit_entry = AlertAuditEntry(
                timestamp=now_utc,
                actor=actor_name,
                action=action_name,
                note=notes.strip() or f"Status transitioned to {new_status}",
            ).to_dict()

            if "audit_history" not in alert or not isinstance(alert["audit_history"], list):
                alert["audit_history"] = []
            alert["audit_history"].append(audit_entry)
            return True

    return False


def get_alerts_kpis() -> Dict[str, int]:
    """Compute summary KPIs across active alerts."""
    alerts = ensure_alerts_initialized()
    total = len(alerts)
    pending = sum(1 for a in alerts if a.get("status") == "Pending")
    approved = sum(1 for a in alerts if a.get("status") == "Approved")
    rejected = sum(1 for a in alerts if a.get("status") == "Rejected")
    changes_req = sum(1 for a in alerts if a.get("status") == "Changes Requested")
    extreme_count = sum(1 for a in alerts if a.get("severity") in ("Severe", "Extreme") and a.get("status") != "Rejected")

    return {
        "total": total,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "changes_requested": changes_req,
        "extreme_or_severe": extreme_count,
    }


def export_alerts_csv() -> str:
    """Export all alerts into RFC 4180 CSV format."""
    alerts = ensure_alerts_initialized()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "severity", "region", "headline", "description",
        "evidence", "valid_until", "status", "issued_by",
        "created_at", "reviewer_comments", "audit_entries_count"
    ])
    for a in alerts:
        writer.writerow([
            a.get("id", ""),
            a.get("severity", ""),
            a.get("region", ""),
            a.get("headline", ""),
            a.get("description", ""),
            a.get("evidence", ""),
            a.get("valid_until", ""),
            a.get("status", ""),
            a.get("issued_by", ""),
            a.get("created_at", ""),
            a.get("reviewer_comments", ""),
            len(a.get("audit_history", [])),
        ])
    return output.getvalue()
