"""CHAKRAVAT View: Section E - Alerts & Human Review.

Features:
- Operational threat advisory bulletins with severity and evidence
- Responsive card grid honoring strict <=3 columns whitespace rule
- Interactive reviewer control panel (Approve, Reject, Request Changes)
- Immutable chronological audit history log
- Dynamic session state updates and CSV export
"""

from __future__ import annotations

import html
from typing import Any, Dict, List
import streamlit as st

from src.ui.components import (
    cv_markdown,
    audit_timeline,
    grid_row,
    metric_card,
    render_empty_state,
    section_header,
    severity_badge,
    status_badge,
)
from src.workflows.alerts import (
    VALID_SEVERITIES,
    VALID_STATUSES,
    create_alert,
    export_alerts_csv,
    get_alerts,
    get_alerts_kpis,
    review_alert,
)


def render() -> None:
    """Render Section E: Alerts & Human Review."""
    section_header(
        title="(E) Alerts & Human Review",
        subtitle="Operational threat advisory bulletins and authorized forecaster review lifecycle",
        badge_label="Operational",
        badge_type="normal",
    )

    # 1. Top KPI Summary Metrics (Strict <= 3 columns)
    kpis = get_alerts_kpis()
    c1, c2, c3 = grid_row(3)
    with c1:
        metric_card(
            label="Total Threat Bulletins",
            value=kpis["total"],
            help_text="Active & historical operational records",
        )
    with c2:
        pending_badge = "Action Required" if kpis["pending"] > 0 else "All Cleared"
        pending_sev = "warning" if kpis["pending"] > 0 else "verified"
        metric_card(
            label="Pending Forecaster Review",
            value=kpis["pending"],
            badge_text=pending_badge,
            badge_severity=pending_sev,
            help_text="Awaiting duty officer authorization",
        )
    with c3:
        metric_card(
            label="Approved & Active Alerts",
            value=kpis["approved"],
            badge_text="Operational",
            badge_severity="verified",
            help_text="Validated bulletins broadcast to stakeholders",
        )

    cv_markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # 2. Draft New Threat Alert (Form)
    with st.expander("➕ Draft New Operational Threat Alert", expanded=False):
        cv_markdown(
            "<p style='color: #94A3B8; font-size: 0.875rem; margin-bottom: 1rem;'>"
            "Draft a new coastal meteorological advisory or navigation warning. New alerts initialize in "
            "<code>Pending</code> status and require human review approval before official dissemination."
            "</p>",
            unsafe_allow_html=True,
        )

        with st.form("create_alert_form", clear_on_submit=True):
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                severity_input = st.selectbox(
                    "Threat Severity Level *",
                    list(VALID_SEVERITIES),
                    index=1,
                    help="Official IMD/CHAKRAVAT threat classification tier",
                )
                region_input = st.text_input(
                    "Target Coastal Region / District *",
                    value="Puri & Jagatsinghpur Coastal Belt (Odisha)",
                    help="Specific coastal stretch or maritime sector impacted",
                )
                headline_input = st.text_input(
                    "Advisory Headline *",
                    value="Severe Coastal Gale & Storm Surge Warning",
                    help="Concise public bulletin title",
                )
            with f_col2:
                valid_until_input = st.text_input(
                    "Validity Window (UTC) *",
                    value="2026-11-06 18:00 UTC",
                    help="Expiration timestamp of the bulletin",
                )
                issued_by_input = st.text_input(
                    "Originating Office / Forecaster Desk *",
                    value="Duty Forecaster — NIO Marine Unit",
                    help="Identifier of forecaster or triggering system",
                )

            desc_input = st.text_area(
                "Bulletin Description & Operational Threat *",
                value="Squally wind speeds 90-110 km/h gusting to 125 km/h. Coastal tidal surge of 1.2m expected along low-lying embankments. Fishing operations suspended.",
                height=100,
            )
            evidence_input = st.text_area(
                "Meteorological Evidence & Objective Guidance *",
                value="Central pressure 962 hPa; numerical persistence indicates landfall within 24h. Doppler radar composite reflectivity > 48 dBZ.",
                height=80,
            )

            submitted = st.form_submit_button("Publish Alert for Review", width="stretch")
            if submitted:
                if not headline_input.strip() or not region_input.strip() or not desc_input.strip():
                    st.error("Please provide Headline, Target Region, and Bulletin Description.")
                else:
                    new_alert = create_alert(
                        severity=severity_input,
                        region=region_input,
                        headline=headline_input,
                        description=desc_input,
                        evidence=evidence_input,
                        valid_until=valid_until_input,
                        issued_by=issued_by_input,
                    )
                    st.success(f"Threat Alert {new_alert['id']} drafted successfully in 'Pending' status.")
                    st.rerun()

    cv_markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

    # 3. Filtering Controls & CSV Export Bar (Strict <= 3 columns)
    flt_col1, flt_col2, flt_col3 = grid_row(3)
    with flt_col1:
        status_filter = st.selectbox(
            "Filter by Review Status",
            ["All"] + list(VALID_STATUSES),
            index=0,
            key="alert_status_filter_select",
        )
    with flt_col2:
        severity_filter = st.selectbox(
            "Filter by Severity Tier",
            ["All"] + list(VALID_SEVERITIES),
            index=0,
            key="alert_severity_filter_select",
        )
    with flt_col3:
        cv_markdown("<div style='height: 1.7rem;'></div>", unsafe_allow_html=True)
        csv_data = export_alerts_csv()
        st.download_button(
            label="📥 Export Alerts to CSV",
            data=csv_data,
            file_name="chakravat_alerts_export.csv",
            mime="text/csv",
            width="stretch",
        )

    # 4. Filtered Alerts Display (Strict <= 3 cards per row)
    filtered_alerts = get_alerts(status_filter=status_filter, severity_filter=severity_filter)

    if not filtered_alerts:
        render_empty_state(
            title="No Threat Bulletins Found",
            message=f"No operational alerts match status '{status_filter}' and severity '{severity_filter}'.",
            icon="🔔",
        )
        return

    cv_markdown(
        f"<div style='color: #94A3B8; font-size: 0.8125rem; margin-bottom: 0.75rem;'>"
        f"Displaying <strong>{len(filtered_alerts)}</strong> operational alert bulletin(s) "
        f"(Max 3 cards per row)"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Chunk into rows of at most 3 cards
    chunk_size = 3
    chunks = [filtered_alerts[i:i + chunk_size] for i in range(0, len(filtered_alerts), chunk_size)]

    for row_idx, chunk in enumerate(chunks):
        cols = grid_row(3)
        for col_idx, alert in enumerate(chunk):
            with cols[col_idx]:
                _render_alert_card(alert)


def _render_alert_card(alert: Dict[str, Any]) -> None:
    """Render a single high-legibility alert card with review actions and audit log."""
    alert_id = alert.get("id", "ALT-000")
    severity = alert.get("severity", "Warning")
    status = alert.get("status", "Pending")
    headline = html.escape(alert.get("headline", "Threat Bulletin"))
    region = html.escape(alert.get("region", "Coastal Sector"))
    desc = html.escape(alert.get("description", ""))
    evidence = html.escape(alert.get("evidence", ""))
    valid_until = html.escape(alert.get("valid_until", "-"))
    created_at = html.escape(alert.get("created_at", "-"))
    issued_by = html.escape(alert.get("issued_by", "Duty Desk"))
    comments = html.escape(alert.get("reviewer_comments", ""))
    audit_history = alert.get("audit_history", [])

    # HTML Card Container
    reviewer_note_html = ""
    if comments:
        reviewer_note_html = f"""
        <div style="margin-top: 0.5rem; padding: 0.5rem 0.75rem; background: rgba(56, 189, 248, 0.08); border-left: 3px solid #38BDF8; border-radius: 4px; font-size: 0.8125rem;">
            <strong style="color: #38BDF8;">Reviewer Note:</strong> {comments}
        </div>
        """

    card_html = f"""
    <div class="cv-card" style="margin-bottom: 1rem; border-color: #2C4056;">
        <div class="cv-card-header">
            <div>
                <span class="cv-mono" style="font-weight: 700; color: #F1F5F9; font-size: 0.9375rem;">{alert_id}</span>
                <span style="margin-left: 0.5rem;">{severity_badge(severity)}</span>
            </div>
            <div>{status_badge(status)}</div>
        </div>
        <div class="cv-card-body">
            <div style="font-size: 1rem; font-weight: 600; color: #F1F5F9; margin-bottom: 0.35rem;">{headline}</div>
            <div style="color: #38BDF8; font-size: 0.8125rem; font-weight: 500; margin-bottom: 0.6rem;">📍 {region}</div>
            <p style="margin-bottom: 0.5rem; color: #CBD5E1; font-size: 0.84rem; line-height: 1.45;">{desc}</p>
            <div style="font-size: 0.78rem; color: #94A3B8; background: #101820; padding: 0.4rem 0.6rem; border-radius: 4px; margin-bottom: 0.5rem;">
                <strong style="color: #CBD5E1;">Meteorological Basis:</strong> {evidence}
            </div>
            <div style="font-size: 0.75rem; color: #94A3B8; display: flex; justify-content: space-between; border-top: 1px solid #1E2D3B; padding-top: 0.4rem;">
                <span>Valid: <strong style="color: #F1F5F9;">{valid_until}</strong></span>
                <span>By: {issued_by}</span>
            </div>
            {reviewer_note_html}
        </div>
    </div>
    """
    cv_markdown(card_html, unsafe_allow_html=True)

    # Reviewer Action Panel (Streamlit interactive controls)
    with st.expander(f"⚙️ Review Actions & Audit Trail ({len(audit_history)})", expanded=False):
        cv_markdown(
            "<div style='font-size: 0.8125rem; color: #94A3B8; margin-bottom: 0.5rem;'>"
            "Authorized Reviewer Control Desk:"
            "</div>",
            unsafe_allow_html=True,
        )

        rev_actor = st.text_input(
            "Reviewer Name & Designation",
            value="Dr. S. Patnaik (Lead Duty Forecaster)",
            key=f"actor_input_{alert_id}",
        )
        rev_notes = st.text_input(
            "Reviewer Notes / Instructions",
            value="",
            placeholder="Add operational notes or justification...",
            key=f"notes_input_{alert_id}",
        )

        btn_c1, btn_c2, btn_c3 = st.columns(3)
        with btn_c1:
            if st.button("✅ Approve", key=f"btn_app_{alert_id}", width="stretch"):
                review_alert(alert_id, action="Approve", actor=rev_actor, notes=rev_notes)
                st.success(f"{alert_id} Approved")
                st.rerun()
        with btn_c2:
            if st.button("❌ Reject", key=f"btn_rej_{alert_id}", width="stretch"):
                if not rev_notes.strip():
                    st.warning("Please provide a reviewer note before rejecting.")
                else:
                    review_alert(alert_id, action="Reject", actor=rev_actor, notes=rev_notes)
                    st.error(f"{alert_id} Rejected")
                    st.rerun()
        with btn_c3:
            if st.button("🔄 Request Changes", key=f"btn_chg_{alert_id}", width="stretch"):
                if not rev_notes.strip():
                    st.warning("Please provide revision instructions.")
                else:
                    review_alert(alert_id, action="Request Changes", actor=rev_actor, notes=rev_notes)
                    st.info(f"{alert_id} status changed to 'Changes Requested'")
                    st.rerun()

        cv_markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)
        cv_markdown("<strong style='font-size: 0.8125rem; color: #CBD5E1;'>Chronological Audit Log:</strong>", unsafe_allow_html=True)
        audit_timeline(audit_history)
