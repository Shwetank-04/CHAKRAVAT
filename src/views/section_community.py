"""CHAKRAVAT View: Section F - Community Reports.

Features:
- Crowdsourced field incident report intake
- Mandatory prominent warning banner: ⚠️ UNVERIFIED CITIZEN REPORT - PENDING VERIFICATION
- 5-state lifecycle: Submitted -> Under Review -> Verified / Rejected / Needs More Info
- Reviewer control panel with status transition triggers and notes
- Responsive card grid (<=3 per row) and CSV export
"""

from __future__ import annotations

from datetime import datetime, timezone
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
    unverified_report_banner,
)
from src.workflows.reports import (
    VALID_REPORT_CATEGORIES,
    VALID_REPORT_STATUSES,
    export_reports_csv,
    get_community_reports,
    get_reports_kpis,
    submit_community_report,
    update_report_review,
)


def render() -> None:
    """Render Section F: Community Reports."""
    section_header(
        title="(F) Community Reports",
        subtitle="Crowdsourced citizen field observations, ground truth verification & field damage triage",
        badge_label="Crowdsourced",
        badge_type="advisory",
    )

    _show_flash()

    # 1. Mandatory Prominent Warning Banner
    unverified_report_banner(
        "<strong>⚠️ UNVERIFIED CITIZEN REPORT - PENDING VERIFICATION</strong><br>"
        "All crowdsourced incident reports are user-submitted field observations and remain strictly unverified "
        "until authenticated by authorized emergency responders or meteorologists. Treat unverified damage and flood "
        "reports as preliminary situational indicators only."
    )

    # 2. KPI Summary Metrics (Strict <= 3 columns)
    kpis = get_reports_kpis()
    c1, c2, c3 = grid_row(3)
    with c1:
        metric_card(
            label="Total Submissions",
            value=kpis["total"],
            help_text="All citizen reports ingested",
        )
    with c2:
        unverified_text = f"{kpis['unverified_total']} Unconfirmed" if kpis["unverified_total"] > 0 else "All Triage Done"
        unverified_sev = "warning" if kpis["unverified_total"] > 0 else "verified"
        metric_card(
            label="Pending Verification",
            value=kpis["unverified_total"],
            badge_text=unverified_text,
            badge_severity=unverified_sev,
            help_text="Submitted or under review",
        )
    with c3:
        metric_card(
            label="Verified Incidents",
            value=kpis["verified"],
            badge_text="Ground Truth",
            badge_severity="verified",
            help_text="Officially confirmed by field personnel",
        )

    cv_markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # 3. Submission Form for Citizen Reports
    with st.expander("📝 Submit Ground Incident Report", expanded=False):
        cv_markdown(
            "<p style='color: #94A3B8; font-size: 0.875rem; margin-bottom: 1rem;'>"
            "Report local coastal inundation, structural damage, fallen transmission lines, or storm surge. "
            "Submissions immediately enter <code>Submitted</code> status with mandatory unverified labeling."
            "</p>",
            unsafe_allow_html=True,
        )

        nonce = st.session_state.get("report_form_nonce", 0)
        with st.form(f"citizen_report_form_{nonce}", clear_on_submit=False):
            f1, f2 = st.columns(2)
            with f1:
                category_input = st.selectbox(
                    "Hazard / Damage Category *",
                    list(VALID_REPORT_CATEGORIES),
                    index=0,
                    key=f"rf_cat_{nonce}",
                )
                district_input = st.selectbox(
                    "Coastal District *",
                    [
                        "Puri", "Jagatsinghpur", "Kendrapara", "Balasore", "Ganjam", "Bhadrak",
                        "Purba Medinipur", "South 24 Parganas", "North 24 Parganas",
                        "Visakhapatnam", "Srikakulam", "Vizianagaram",
                        "Porbandar", "Kutch", "Jamnagar", "Gir Somnath", "Other Coastal District",
                    ],
                    index=0,
                    key=f"rf_dist_{nonce}",
                )
                location_detail = st.text_input(
                    "Specific Landmark / Ward / Village *",
                    placeholder="e.g., Ward 4 near sea dyke breach, Marine Drive",
                    key=f"rf_loc_{nonce}",
                )
            with f2:
                now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                incident_time = st.text_input("Incident Observation Time (UTC) *", value=now_str, key=f"rf_time_{nonce}")
                severity_input = st.selectbox("Observed Hazard Severity *", ["Low", "Medium", "High", "Critical"], index=1, key=f"rf_sev_{nonce}")
                submitter_name = st.text_input("Reported By (Observer / Volunteer)", value="Local Community Volunteer", key=f"rf_by_{nonce}")

            desc_input = st.text_area(
                "Incident Description & Ground Impact *",
                placeholder="Describe observed water depth, wind destruction, blocked evacuation roads, or human distress...",
                height=100,
                key=f"rf_desc_{nonce}",
            )
            has_photo_input = st.checkbox("📸 Photo Evidence Attached / Verified On-Site", value=False, key=f"rf_photo_{nonce}")

            submitted = st.form_submit_button("Submit Citizen Incident Report", width="stretch")
            if submitted:
                if not desc_input.strip() or not location_detail.strip():
                    st.error("Please provide specific Landmark/Location and Incident Description.")
                else:
                    new_rep = submit_community_report(
                        category=category_input,
                        district=district_input,
                        location_detail=location_detail,
                        description=desc_input,
                        incident_time=incident_time,
                        severity=severity_input,
                        has_photo=has_photo_input,
                        submitted_by=submitter_name,
                    )
                    st.session_state["report_form_nonce"] = nonce + 1
                    st.session_state["community_flash"] = (
                        "success",
                        f"Report {new_rep['id']} submitted! Tagged as 'UNVERIFIED CITIZEN REPORT - PENDING VERIFICATION'.",
                    )
                    st.rerun()

    cv_markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

    # 4. Filters & CSV Export Bar (Strict <= 3 columns)
    flt_c1, flt_c2, flt_c3 = grid_row(3)
    with flt_c1:
        status_flt = st.selectbox(
            "Filter by Lifecycle Status",
            ["All"] + list(VALID_REPORT_STATUSES),
            index=0,
            key="rep_status_filter_select",
        )
    with flt_c2:
        category_flt = st.selectbox(
            "Filter by Incident Category",
            ["All"] + list(VALID_REPORT_CATEGORIES),
            index=0,
            key="rep_category_filter_select",
        )
    with flt_c3:
        cv_markdown("<div style='height: 1.7rem;'></div>", unsafe_allow_html=True)
        csv_data = export_reports_csv()
        st.download_button(
            label="📥 Export Reports to CSV",
            data=csv_data,
            file_name="chakravat_community_reports.csv",
            mime="text/csv",
            width="stretch",
        )

    # 5. Display Reports in Responsive Cards (Strict <= 3 per row)
    reports = get_community_reports(status_filter=status_flt, category_filter=category_flt)

    if not reports:
        render_empty_state(
            title="No Community Reports Found",
            message=f"No field reports match status '{status_flt}' and category '{category_flt}'.",
            icon="📋",
        )
        return

    cv_markdown(
        f"<div style='color: #94A3B8; font-size: 0.8125rem; margin-bottom: 0.75rem;'>"
        f"Displaying <strong>{len(reports)}</strong> crowdsourced community report(s) "
        f"(Max 3 cards per row)"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Chunk into rows of at most 3 cards
    chunk_size = 3
    chunks = [reports[i:i + chunk_size] for i in range(0, len(reports), chunk_size)]

    for row_idx, chunk in enumerate(chunks):
        cols = grid_row(3)
        for col_idx, rep in enumerate(chunk):
            with cols[col_idx]:
                _render_report_card(rep)


def _flash(kind: str, message: str) -> None:
    """Queue a status message that survives the st.rerun() that follows every action."""
    st.session_state["community_flash"] = (kind, message)


def _show_flash() -> None:
    kind, message = st.session_state.pop("community_flash", (None, None))
    if message:
        {"success": st.success, "warning": st.warning, "error": st.error}.get(kind, st.info)(message)


def _render_report_card(rep: Dict[str, Any]) -> None:
    """Render an individual community report card with verification banner and actions."""
    rep_id = rep.get("id", "REP-000")
    cat = html.escape(rep.get("category", "Incident"))
    dist = html.escape(rep.get("district", "Coastal"))
    loc = html.escape(rep.get("location_detail", ""))
    desc = html.escape(rep.get("description", ""))
    sev = rep.get("severity", "Medium")
    status = rep.get("status", "Submitted")
    is_verified = rep.get("is_verified", False)
    has_photo = rep.get("has_photo", False)
    incident_time = html.escape(rep.get("incident_time", "-"))
    sub_by = html.escape(rep.get("submitted_by", "Citizen Observer"))
    notes = html.escape(rep.get("reviewer_notes", ""))
    reviewed_by = html.escape(rep.get("reviewed_by") or "")
    audit_log = rep.get("audit_log", [])

    # Prominent Header Banner based on verification state
    if is_verified or status.lower() == "verified":
        banner_html = """
        <div style="background: rgba(52, 211, 153, 0.12); border-left: 3px solid #34D399; padding: 0.35rem 0.6rem; border-radius: 4px; font-size: 0.75rem; color: #34D399; font-weight: 600; margin-bottom: 0.5rem;">
            ✅ OFFICIAL VERIFIED INCIDENT — Field Authenticated
        </div>
        """
        card_border = "#34D399"
    elif status.lower() == "rejected":
        banner_html = """
        <div style="background: rgba(248, 113, 113, 0.12); border-left: 3px solid #F87171; padding: 0.35rem 0.6rem; border-radius: 4px; font-size: 0.75rem; color: #F87171; font-weight: 600; margin-bottom: 0.5rem;">
            ❌ DISCARDED / UNCONFIRMED REPORT
        </div>
        """
        card_border = "#2C4056"
    else:
        banner_html = """
        <div style="background: rgba(251, 191, 36, 0.12); border-left: 3px solid #FBBF24; padding: 0.35rem 0.6rem; border-radius: 4px; font-size: 0.75rem; color: #FBBF24; font-weight: 600; margin-bottom: 0.5rem;">
            ⚠️ UNVERIFIED CITIZEN REPORT - PENDING VERIFICATION
        </div>
        """
        card_border = "#FBBF24"

    photo_badge = '<span class="cv-badge cv-badge-verified">📸 Photo Attached</span>' if has_photo else '<span class="cv-badge cv-badge-muted">No Photo</span>'

    reviewer_note_html = ""
    if notes:
        reviewer_note_html = f"""
        <div style="margin-top: 0.5rem; padding: 0.45rem 0.65rem; background: rgba(56, 189, 248, 0.08); border-left: 3px solid #38BDF8; border-radius: 4px; font-size: 0.78rem;">
            <strong style="color: #38BDF8;">Reviewer Note ({reviewed_by or 'Desk'}):</strong> {notes}
        </div>
        """

    card_html = f"""
    <div class="cv-card" style="margin-bottom: 1rem; border-color: {card_border};">
        {banner_html}
        <div class="cv-card-header" style="margin-bottom: 0.5rem;">
            <div>
                <span class="cv-mono" style="font-weight: 700; color: #F1F5F9; font-size: 0.9375rem;">{rep_id}</span>
                <span style="margin-left: 0.4rem;">{severity_badge(sev)}</span>
            </div>
            <div>{status_badge(status)}</div>
        </div>
        <div class="cv-card-body">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                <span style="font-weight: 600; color: #F1F5F9; font-size: 0.95rem;">{cat}</span>
                {photo_badge}
            </div>
            <div style="color: #38BDF8; font-size: 0.8125rem; font-weight: 500; margin-bottom: 0.5rem;">📍 {dist} — {loc}</div>
            <p style="margin-bottom: 0.5rem; color: #CBD5E1; font-size: 0.84rem; line-height: 1.45;">{desc}</p>
            <div style="font-size: 0.75rem; color: #94A3B8; display: flex; justify-content: space-between; border-top: 1px solid #1E2D3B; padding-top: 0.4rem;">
                <span>Time: <strong style="color: #F1F5F9;">{incident_time}</strong></span>
                <span>By: {sub_by}</span>
            </div>
            {reviewer_note_html}
        </div>
    </div>
    """
    cv_markdown(card_html, unsafe_allow_html=True)

    # Reviewer Triage Control Panel
    with st.expander(f"⚙️ Triage & Verification Panel ({len(audit_log)})", expanded=False):
        cv_markdown(
            "<div style='font-size: 0.8125rem; color: #94A3B8; margin-bottom: 0.5rem;'>"
            "Field Verification & Operational Action Desk:"
            "</div>",
            unsafe_allow_html=True,
        )

        reviewer_name = st.text_input(
            "Reviewer Officer",
            value="Inspector P. Mohanty (Disaster Response Desk)",
            key=f"rep_rev_officer_{rep_id}",
        )
        reviewer_notes = st.text_input(
            "Verification Findings / Action Notes",
            value="",
            placeholder="Ground truth confirmation details...",
            key=f"rep_rev_notes_{rep_id}",
        )

        b1, b2 = st.columns(2)
        with b1:
            if st.button("🔍 Mark Under Review", key=f"btn_ur_{rep_id}", width="stretch"):
                update_report_review(rep_id, "Under Review", reviewer_name, reviewer_notes)
                _flash("info", f"{rep_id} marked Under Review")
                st.rerun()
            if st.button("✅ Verify Incident", key=f"btn_ver_{rep_id}", width="stretch"):
                update_report_review(rep_id, "Verified", reviewer_name, reviewer_notes)
                _flash("success", f"{rep_id} Officially Verified!")
                st.rerun()
        with b2:
            if st.button("❓ Needs More Info", key=f"btn_nmi_{rep_id}", width="stretch"):
                if not reviewer_notes.strip():
                    st.warning("Please specify what information is needed.")
                else:
                    update_report_review(rep_id, "Needs More Info", reviewer_name, reviewer_notes)
                    _flash("warning", f"{rep_id} marked Needs More Info")
                    st.rerun()
            if st.button("❌ Reject Report", key=f"btn_rej_rep_{rep_id}", width="stretch"):
                if not reviewer_notes.strip():
                    st.warning("Please provide rationale for rejecting.")
                else:
                    update_report_review(rep_id, "Rejected", reviewer_name, reviewer_notes)
                    _flash("error", f"{rep_id} Rejected")
                    st.rerun()

        if audit_log:
            cv_markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
            cv_markdown("<strong style='font-size: 0.8125rem; color: #CBD5E1;'>Verification History:</strong>", unsafe_allow_html=True)
            audit_timeline(audit_log)
