"""CHAKRAVAT View: Section H - Disaster Response.

Features:
- Regional risk summary cards (Strict <= 3 cards/row)
- Incident stream triage comparing verified incidents vs pending citizen reports
- Direct conversion from verified incidents to response dispatch tasks
- Interactive disaster response task manager with live status transitions
- Designated safe muster zones and inland evacuation corridors
"""

from __future__ import annotations

import html
from typing import Any, Dict, List
import streamlit as st

from src.ui.components import (
    cv_markdown,
    card_container,
    grid_row,
    metric_card,
    render_empty_state,
    section_header,
    severity_badge,
    status_badge,
)
from src.workflows.disaster_response import (
    SAFE_EVACUATION_ZONES,
    VALID_TASK_PRIORITIES,
    VALID_TASK_STATUSES,
    create_response_task,
    get_response_kpis,
    get_response_tasks,
    get_triage_streams,
    update_task_status,
)


def render() -> None:
    """Render Section H: Disaster Response."""
    section_header(
        title="(H) Disaster Response",
        subtitle="Regional risk assessment, ground truth incident triage & emergency task dispatch",
        badge_label="Operations",
        badge_type="extreme",
    )

    # 1. Regional Risk Summary Cards (Strict <= 3 per row)
    kpis = get_response_kpis()
    c1, c2, c3 = grid_row(3)
    with c1:
        metric_card(
            label="Highest Risk Coastal Zone",
            value="Puri — Jagatsinghpur",
            badge_text="Extreme Surge Threat",
            badge_severity="extreme",
            help_text="Projected tidal surge > 1.5m & winds > 135 km/h",
        )
    with c2:
        metric_card(
            label="Evacuation & Shelters",
            value=f"{kpis['total_sheltered']:,}",
            unit="Evacuees",
            delta=f"{kpis['shelter_utilization_pct']}% of {kpis['total_capacity']:,} Capacity",
            delta_type="neutral",
            help_text="Across designated coastal safe havens",
        )
    with c3:
        metric_card(
            label="Incident Triage Stream",
            value=f"{kpis['verified_reports_count']}",
            unit="Verified",
            delta=f"{kpis['pending_triage_count']} Pending Citizen Triage",
            delta_type="neutral",
            badge_text="Ground Truth Active",
            badge_severity="warning" if kpis['pending_triage_count'] > 0 else "verified",
            help_text="Field authenticated vs citizen queue",
        )

    cv_markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

    # 2. Tabs: Triage Stream, Task Dispatch, and Evacuation Corridors
    tab_tasks, tab_triage, tab_corridors = st.tabs([
        "📋 Response Task Manager",
        "⚡ Incident Triage Stream",
        "🛡️ Safe Zones & Evacuation Corridors",
    ])

    # ---------------- TAB 1: RESPONSE TASK MANAGER ----------------
    with tab_tasks:
        _render_response_tasks_tab(kpis)

    # ---------------- TAB 2: TRIAGE STREAM ----------------
    with tab_triage:
        _render_triage_stream_tab()

    # ---------------- TAB 3: SAFE ZONES & CORRIDORS ----------------
    with tab_corridors:
        _render_safe_zones_tab()


def _render_response_tasks_tab(kpis: Dict[str, Any]) -> None:
    """Render interactive response task manager with dispatch form and status transitions."""
    cv_markdown(
        "<div style='font-size: 0.875rem; color: #CBD5E1; margin-bottom: 0.75rem;'>"
        "Coordinate inter-agency emergency deployment across NDRF, SDRF, Fire Services, and District Authorities."
        "</div>",
        unsafe_allow_html=True,
    )

    # Dispatch New Task Form
    with st.expander("➕ Dispatch New Operational Response Task", expanded=False):
        with st.form("dispatch_task_form", clear_on_submit=True):
            f1, f2 = st.columns(2)
            with f1:
                task_title = st.text_input(
                    "Task Title & Objective *",
                    value="Pre-position rubber inflatable rescue boats at Pentakota",
                )
                agency_input = st.selectbox(
                    "Lead Assigned Agency *",
                    [
                        "4th Battalion NDRF",
                        "Odisha Fire & Disaster Response",
                        "State Disaster Response Force (SDRF)",
                        "OPTCL Power Restoration Crew",
                        "District Civil Supplies & Logistics",
                        "Indian Coast Guard Air Station",
                        "State Public Health & Medical Unit",
                    ],
                    index=0,
                )
                district_input = st.selectbox(
                    "Target District *",
                    ["Puri", "Jagatsinghpur", "Kendrapara", "Balasore", "Ganjam", "Purba Medinipur", "Porbandar", "Regional Maritime"],
                    index=0,
                )
            with f2:
                priority_input = st.selectbox("Priority Level *", list(VALID_TASK_PRIORITIES), index=1)
                assignee_input = st.text_input("Lead Field Officer / Assignee *", value="Inspector S. Patnaik")
                initial_status = st.selectbox("Initial Status", list(VALID_TASK_STATUSES), index=0)

            submitted = st.form_submit_button("Dispatch Operational Task", width="stretch")
            if submitted:
                if not task_title.strip():
                    st.error("Please enter a valid task title.")
                else:
                    new_task = create_response_task(
                        title=task_title,
                        priority=priority_input,
                        agency=agency_input,
                        district=district_input,
                        assignee=assignee_input,
                        status=initial_status,
                    )
                    st.success(f"Task {new_task['id']} dispatched successfully!")
                    st.rerun()

    cv_markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # Task Filters (Strict <= 3 columns)
    flt_col1, flt_col2, flt_col3 = grid_row(3)
    with flt_col1:
        status_flt = st.selectbox(
            "Filter Task Status",
            ["All"] + list(VALID_TASK_STATUSES),
            index=0,
            key="resp_status_flt_select",
        )
    with flt_col2:
        prio_flt = st.selectbox(
            "Filter Task Priority",
            ["All"] + list(VALID_TASK_PRIORITIES),
            index=0,
            key="resp_prio_flt_select",
        )
    with flt_col3:
        cv_markdown("<div style='height: 1.7rem;'></div>", unsafe_allow_html=True)
        cv_markdown(
            f"<div style='font-size: 0.8125rem; color: #94A3B8; text-align: right; padding-top: 0.4rem;'>"
            f"Active: <strong style='color: #FBBF24;'>{kpis['tasks_in_progress']} In-Progress</strong> | "
            f"<strong style='color: #34D399;'>{kpis['tasks_completed']} Completed</strong>"
            f"</div>",
            unsafe_allow_html=True,
        )

    tasks = get_response_tasks(status_filter=status_flt, priority_filter=prio_flt)

    if not tasks:
        render_empty_state(
            title="No Matching Response Tasks",
            message=f"No operational tasks match status '{status_flt}' and priority '{prio_flt}'.",
            icon="📋",
        )
        return

    cv_markdown(
        f"<div style='color: #94A3B8; font-size: 0.8125rem; margin-bottom: 0.75rem;'>"
        f"Displaying <strong>{len(tasks)}</strong> response task(s) "
        f"(Max 3 cards per row)"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Chunk tasks into rows of at most 3
    chunk_size = 3
    chunks = [tasks[i:i + chunk_size] for i in range(0, len(tasks), chunk_size)]

    for row_idx, chunk in enumerate(chunks):
        cols = grid_row(len(chunk))
        for col_idx, task in enumerate(chunk):
            with cols[col_idx]:
                _render_task_card(task)


def _render_task_card(task: Dict[str, Any]) -> None:
    """Render an individual operational task card with status transition buttons."""
    task_id = html.escape(task.get("id", "TSK-000"))
    title = html.escape(task.get("title", "Response Task"))
    priority = task.get("priority", "High")
    status = task.get("status", "Todo")
    agency = html.escape(task.get("agency", "Disaster Unit"))
    dist = html.escape(task.get("district", "District"))
    assignee = html.escape(task.get("assignee", "Officer"))
    updated_at = html.escape(task.get("updated_at", "-"))

    prio_color = "#F87171" if priority in ("Critical", "High") else "#FBBF24"

    card_html = f"""
    <div class="cv-card" style="margin-bottom: 1rem; border-color: #2C4056;">
        <div class="cv-card-header" style="margin-bottom: 0.35rem;">
            <div>
                <span class="cv-mono" style="font-weight: 700; color: #F1F5F9; font-size: 0.875rem;">{task_id}</span>
                <span style="margin-left: 0.4rem;">{severity_badge(priority)}</span>
            </div>
            <div>{status_badge(status)}</div>
        </div>
        <div class="cv-card-body">
            <div style="font-size: 0.95rem; font-weight: 600; color: #F1F5F9; margin-bottom: 0.35rem; min-height: 2.8rem;">
                {title}
            </div>
            <div style="font-size: 0.8125rem; color: #38BDF8; margin-bottom: 0.25rem;">
                🏢 <strong>{agency}</strong>
            </div>
            <div style="font-size: 0.8125rem; color: #CBD5E1; margin-bottom: 0.5rem;">
                📍 {dist} &nbsp;|&nbsp; 👤 {assignee}
            </div>
            <div style="font-size: 0.72rem; color: #94A3B8; border-top: 1px solid #1E2D3B; padding-top: 0.35rem;">
                Updated: <span class="cv-mono">{updated_at}</span>
            </div>
        </div>
    </div>
    """
    cv_markdown(card_html, unsafe_allow_html=True)

    # Interactive Status Controls
    btn_c1, btn_c2, btn_c3 = st.columns(3)
    with btn_c1:
        if st.button("📝 Todo", key=f"btn_todo_{task_id}", disabled=(status == "Todo"), width="stretch"):
            update_task_status(task_id, "Todo")
            st.rerun()
    with btn_c2:
        if st.button("⚡ Active", key=f"btn_act_{task_id}", disabled=(status == "In-Progress"), width="stretch"):
            update_task_status(task_id, "In-Progress")
            st.rerun()
    with btn_c3:
        if st.button("✅ Done", key=f"btn_done_{task_id}", disabled=(status == "Completed"), width="stretch"):
            update_task_status(task_id, "Completed")
            st.rerun()


def _render_triage_stream_tab() -> None:
    """Render dual-stream triage view comparing verified incidents vs pending reports."""
    cv_markdown(
        "<div style='font-size: 0.875rem; color: #CBD5E1; margin-bottom: 1rem;'>"
        "Compare field-verified ground truth incidents requiring dispatch against unverified crowdsourced reports awaiting triage."
        "</div>",
        unsafe_allow_html=True,
    )

    verified_incidents, pending_reports = get_triage_streams()

    col_v, col_p = st.columns(2)

    with col_v:
        cv_markdown(
            f"<div style='border-bottom: 2px solid #34D399; padding-bottom: 0.35rem; margin-bottom: 0.75rem;'>"
            f"<strong style='color: #34D399; font-size: 1rem;'>✅ Verified Incidents ({len(verified_incidents)})</strong><br>"
            f"<span style='color: #94A3B8; font-size: 0.75rem;'>Actionable ground truth ready for emergency response dispatch</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

        if not verified_incidents:
            render_empty_state("No Verified Incidents", "All verified incidents have been dispatched or cleared.", icon="🛡️")
        else:
            for rep in verified_incidents:
                _render_verified_triage_item(rep)

    with col_p:
        cv_markdown(
            f"<div style='border-bottom: 2px solid #FBBF24; padding-bottom: 0.35rem; margin-bottom: 0.75rem;'>"
            f"<strong style='color: #FBBF24; font-size: 1rem;'>⚠️ Pending Triage Queue ({len(pending_reports)})</strong><br>"
            f"<span style='color: #94A3B8; font-size: 0.75rem;'>Unverified citizen observations awaiting field authentication</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

        if not pending_reports:
            render_empty_state("Triage Queue Empty", "No unverified reports awaiting field triage.", icon="✨")
        else:
            for rep in pending_reports:
                _render_pending_triage_item(rep)


def _render_verified_triage_item(rep: Dict[str, Any]) -> None:
    """Render an actionable verified incident with one-click response dispatch."""
    rep_id = rep.get("id", "REP-000")
    cat = html.escape(rep.get("category", "Hazard"))
    dist = html.escape(rep.get("district", "Coastal"))
    loc = html.escape(rep.get("location_detail", ""))
    desc = html.escape(rep.get("description", ""))
    time_str = html.escape(rep.get("incident_time", "-"))
    notes = html.escape(rep.get("reviewer_notes", ""))

    item_html = f"""
    <div class="cv-card" style="margin-bottom: 0.75rem; border-left: 4px solid #34D399; padding: 0.85rem 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.25rem;">
            <span class="cv-mono" style="font-weight: 700; color: #F1F5F9; font-size: 0.875rem;">{rep_id}</span>
            <span class="cv-badge cv-badge-verified">{cat}</span>
        </div>
        <div style="font-weight: 600; color: #38BDF8; font-size: 0.875rem; margin-bottom: 0.25rem;">📍 {dist} — {loc}</div>
        <div style="color: #CBD5E1; font-size: 0.8125rem; margin-bottom: 0.35rem; line-height: 1.4;">{desc}</div>
        <div style="font-size: 0.75rem; color: #34D399; margin-bottom: 0.35rem;">
            <strong>Verification Note:</strong> {notes or 'Confirmed by field patrol'}
        </div>
    </div>
    """
    cv_markdown(item_html, unsafe_allow_html=True)

    # One-Click Dispatch Action Button
    with st.expander(f"⚡ Fast-Dispatch Task for {rep_id}", expanded=False):
        agency = st.text_input("Dispatch Agency", value="NDRF / Fire Rescue", key=f"triage_agency_{rep_id}")
        officer = st.text_input("Lead Officer", value="Patrol Commander", key=f"triage_officer_{rep_id}")
        if st.button("🚀 Confirm Dispatch", key=f"triage_btn_{rep_id}", width="stretch"):
            create_response_task(
                title=f"Resolve {cat}: {loc} ({dist})",
                priority="High",
                agency=agency,
                district=dist,
                assignee=officer,
                status="In-Progress",
            )
            st.success(f"Response task dispatched for {rep_id}!")
            st.rerun()


def _render_pending_triage_item(rep: Dict[str, Any]) -> None:
    """Render an unverified incoming citizen report."""
    rep_id = rep.get("id", "REP-000")
    cat = html.escape(rep.get("category", "Hazard"))
    dist = html.escape(rep.get("district", "Coastal"))
    loc = html.escape(rep.get("location_detail", ""))
    desc = html.escape(rep.get("description", ""))
    status = rep.get("status", "Submitted")

    item_html = f"""
    <div class="cv-card" style="margin-bottom: 0.75rem; border-left: 4px solid #FBBF24; padding: 0.85rem 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.25rem;">
            <span class="cv-mono" style="font-weight: 700; color: #F1F5F9; font-size: 0.875rem;">{rep_id}</span>
            {status_badge(status)}
        </div>
        <div style="font-weight: 600; color: #FBBF24; font-size: 0.875rem; margin-bottom: 0.25rem;">⚠️ {cat} — {dist} ({loc})</div>
        <div style="color: #CBD5E1; font-size: 0.8125rem; line-height: 1.4;">{desc}</div>
        <div style="font-size: 0.72rem; color: #94A3B8; margin-top: 0.35rem;">
            <em>Unverified Citizen Report — Go to Section F to verify or discard</em>
        </div>
    </div>
    """
    cv_markdown(item_html, unsafe_allow_html=True)


def _render_safe_zones_tab() -> None:
    """Render designated inland high-ground safe muster zones and corridors."""
    cv_markdown(
        "<div style='font-size: 0.875rem; color: #CBD5E1; margin-bottom: 1rem;'>"
        "Pre-surveyed inland high-elevation safe muster hubs situated beyond the 50km coastal tidal surge buffer zone."
        "</div>",
        unsafe_allow_html=True,
    )

    chunk_size = 2
    chunks = [SAFE_EVACUATION_ZONES[i:i + chunk_size] for i in range(0, len(SAFE_EVACUATION_ZONES), chunk_size)]

    for chunk in chunks:
        cols = st.columns(len(chunk))
        for idx, zone in enumerate(chunk):
            with cols[idx]:
                z_name = html.escape(zone["zone_name"])
                z_state = html.escape(zone["state"])
                elev = zone["elevation_m"]
                dist = zone["distance_from_coast_km"]
                cap = zone["capacity"]
                facilities = zone["facilities"]

                fac_html = "".join([f"<li style='margin-bottom: 0.2rem;'>{html.escape(f)}</li>" for f in facilities])

                card_html = f"""
                <div class="cv-card" style="margin-bottom: 1rem;">
                    <div class="cv-card-header" style="margin-bottom: 0.35rem;">
                        <span style="font-weight: 600; color: #34D399; font-size: 1rem;">🛡️ {z_name}</span>
                        <span class="cv-badge cv-badge-verified">{z_state}</span>
                    </div>
                    <div class="cv-card-body">
                        <div style="display: flex; justify-content: space-between; font-size: 0.8125rem; background: #101820; padding: 0.5rem 0.75rem; border-radius: 4px; margin-bottom: 0.6rem;">
                            <span>Elevation: <strong style="color: #38BDF8;">{elev}m MSL</strong></span>
                            <span>Inland Buffer: <strong style="color: #F1F5F9;">{dist} km</strong></span>
                            <span>Muster Cap: <strong style="color: #34D399;">{cap:,}</strong></span>
                        </div>
                        <div style="font-size: 0.78rem; color: #94A3B8; margin-bottom: 0.25rem;">Key Infrastructure Facilities:</div>
                        <ul style="font-size: 0.78rem; color: #CBD5E1; margin: 0; padding-left: 1.25rem;">
                            {fac_html}
                        </ul>
                    </div>
                </div>
                """
                cv_markdown(card_html, unsafe_allow_html=True)
