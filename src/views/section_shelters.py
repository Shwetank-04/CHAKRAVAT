"""CHAKRAVAT View: Section G - Shelter Directory.

Features:
- Mandatory prominent illustrative simulation disclaimer banner
- Instant search by shelter name or district
- Multi-parameter filtering by state, minimum capacity, and wheelchair accessibility
- Clean cards with occupancy progress bars and contact information (<=3 per row)
- CSV export capability
"""

from __future__ import annotations

import html
from typing import Any, Dict, List
import streamlit as st

from src.ui.components import (
    cv_markdown,
    experimental_disclaimer_banner,
    grid_row,
    metric_card,
    render_empty_state,
    section_header,
    severity_badge,
    status_badge,
)
from src.workflows.shelters import (
    export_shelters_csv,
    get_shelters,
    get_shelters_kpis,
)


def render() -> None:
    """Render Section G: Shelter Directory."""
    section_header(
        title="(G) Shelter Directory",
        subtitle="Designated coastal multipurpose cyclone shelters, capacity tracking & logistics directory",
        badge_label="Directory",
        badge_type="normal",
    )

    # 1. Mandatory Prominent Illustrative Simulation Disclaimer Banner
    experimental_disclaimer_banner(
        "<strong>ℹ️ ILLUSTRATIVE DEMO DIRECTORY — NOT REAL-TIME OPERATIONAL EMERGENCY DATA</strong><br>"
        "All shelter listings, contact numbers, and occupancy figures are synthetic demonstrative records created for "
        "disaster decision-support workflow simulation. In a real meteorological emergency, contact official State Disaster "
        "Management Authorities (OSDMA: 1070, GSDMA: 1077, WBDMD: 1070, APSDMA: 1070) or dial 112."
    )

    # 2. KPI Summary Metrics (Strict <= 3 columns)
    kpis = get_shelters_kpis()
    c1, c2, c3 = grid_row(3)
    with c1:
        metric_card(
            label="Total Safe Havens",
            value=kpis["total_shelters"],
            help_text="Mapped across 4 coastal states",
        )
    with c2:
        metric_card(
            label="Total Rated Capacity",
            value=f"{kpis['total_capacity']:,}",
            unit="Evacuees",
            help_text=f"{kpis['accessible_count']} wheelchair accessible",
        )
    with c3:
        util_sev = "extreme" if kpis["overall_utilization_pct"] > 85 else ("warning" if kpis["overall_utilization_pct"] > 60 else "verified")
        metric_card(
            label="Current Evacuees Sheltered",
            value=f"{kpis['total_occupancy']:,}",
            unit="People",
            delta=f"{kpis['overall_utilization_pct']}% Total Utilized",
            delta_type="neutral",
            badge_text=f"{kpis['overall_utilization_pct']}% Occupied",
            badge_severity=util_sev,
            help_text=f"{kpis['available_capacity']:,} spaces remaining",
        )

    cv_markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # 3. Search & Filter Bar (Strict <= 3 columns per row)
    f_c1, f_c2, f_c3 = grid_row(3)
    with f_c1:
        search_query = st.text_input(
            "🔍 Search Shelters (Name or District)",
            placeholder="e.g. Puri, Digha, Porbandar, Safe Haven...",
            key="shelter_search_input",
        )
    with f_c2:
        state_filter = st.selectbox(
            "Filter by Coastal State",
            ["All", "Odisha", "West Bengal", "Andhra Pradesh", "Gujarat"],
            index=0,
            key="shelter_state_filter_select",
        )
    with f_c3:
        accessible_only = st.checkbox(
            "♿ Wheelchair Accessible Only",
            value=False,
            key="shelter_accessible_checkbox",
            help="Filter for facilities equipped with ADA ramps and ground-floor access",
        )

    f2_c1, f2_c2, f2_c3 = grid_row(3)
    with f2_c1:
        min_cap = st.slider(
            "Minimum Rated Capacity",
            min_value=0,
            max_value=2000,
            value=0,
            step=250,
            key="shelter_min_cap_slider",
        )
    with f2_c2:
        cv_markdown("<div style='height: 1.7rem;'></div>", unsafe_allow_html=True)
        # Placeholder column to balance 3-column row
        cv_markdown(
            f"<div style='font-size: 0.8125rem; color: #94A3B8; padding-top: 0.5rem;'>"
            f"Source attribution: <strong>OSDMA, GSDMA, WBDMD, APSDMA (Simulated)</strong>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with f2_c3:
        cv_markdown("<div style='height: 1.7rem;'></div>", unsafe_allow_html=True)
        # Fetch preliminary results to export
        matching_shelters = get_shelters(
            search_query=search_query,
            state_filter=state_filter,
            min_capacity=min_cap,
            accessibility_only=accessible_only,
        )
        csv_data = export_shelters_csv(matching_shelters)
        st.download_button(
            label="📥 Export Shelters to CSV",
            data=csv_data,
            file_name="chakravat_shelters_directory.csv",
            mime="text/csv",
            width="stretch",
        )

    cv_markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # 4. Display Shelters in Clean Cards (Strict <= 3 per row)
    if not matching_shelters:
        render_empty_state(
            title="No Matching Shelters Found",
            message="No coastal shelters match the active search query and accessibility filters.",
            icon="🏠",
        )
        return

    cv_markdown(
        f"<div style='color: #94A3B8; font-size: 0.8125rem; margin-bottom: 0.75rem;'>"
        f"Displaying <strong>{len(matching_shelters)}</strong> shelter record(s) "
        f"(Max 3 cards per row)"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Chunk into rows of at most 3 cards
    chunk_size = 3
    chunks = [matching_shelters[i:i + chunk_size] for i in range(0, len(matching_shelters), chunk_size)]

    for row_idx, chunk in enumerate(chunks):
        cols = grid_row(3)
        for col_idx, s in enumerate(chunk):
            with cols[col_idx]:
                _render_shelter_card(s)


def _render_shelter_card(s: Dict[str, Any]) -> None:
    """Render an individual shelter facility card with occupancy bar and contact details."""
    shl_id = html.escape(s.get("id", "SHL-001"))
    name = html.escape(s.get("name", "Coastal Cyclone Shelter"))
    district = html.escape(s.get("district", "District"))
    state = html.escape(s.get("state", "State"))
    lat = float(s.get("latitude", 0.0))
    lon = float(s.get("longitude", 0.0))
    capacity = int(s.get("capacity", 1000))
    occupancy = int(s.get("current_occupancy", s.get("occupancy", 0)))
    available = max(0, capacity - occupancy)
    occ_pct = round((occupancy / capacity) * 100.0, 1) if capacity > 0 else 0.0
    phone = html.escape(s.get("contact_phone", "+91-112"))
    is_acc = bool(s.get("is_accessible", True))
    source_label = html.escape(s.get("source_label", "ILLUSTRATIVE DEMO RECORD"))

    # Color semantics for occupancy progress bar
    if occ_pct >= 85:
        progress_color = "#F87171"  # Crimson
        status_tag = '<span class="cv-badge cv-badge-extreme">Near Capacity</span>'
    elif occ_pct >= 60:
        progress_color = "#FB923C"  # Amber
        status_tag = '<span class="cv-badge cv-badge-warning">Filling</span>'
    else:
        progress_color = "#38BDF8"  # Sky
        status_tag = '<span class="cv-badge cv-badge-verified">Available</span>'

    acc_badge = '<span class="cv-badge cv-badge-verified">♿ Wheelchair Accessible</span>' if is_acc else '<span class="cv-badge cv-badge-muted">Standard Access</span>'

    card_html = f"""
    <div class="cv-card" style="margin-bottom: 1rem;">
        <div class="cv-card-header" style="margin-bottom: 0.35rem;">
            <div>
                <span class="cv-mono" style="font-weight: 700; color: #F1F5F9; font-size: 0.875rem;">{shl_id}</span>
            </div>
            <div>{status_tag}</div>
        </div>
        <div class="cv-card-body">
            <div style="font-size: 1.05rem; font-weight: 600; color: #F1F5F9; margin-bottom: 0.25rem;">{name}</div>
            <div style="color: #38BDF8; font-size: 0.8125rem; font-weight: 500; margin-bottom: 0.6rem;">
                📍 {district}, {state} <span style="color: #94A3B8; font-size: 0.75rem;">({lat:.3f}°N, {lon:.3f}°E)</span>
            </div>

            <!-- Capacity & Occupancy Metrics -->
            <div style="background: #101820; border-radius: 6px; padding: 0.6rem 0.75rem; margin-bottom: 0.75rem; border: 1px solid #1E2D3B;">
                <div style="display: flex; justify-content: space-between; font-size: 0.8125rem; margin-bottom: 0.35rem;">
                    <span style="color: #94A3B8;">Occupancy: <strong style="color: #F1F5F9;">{occupancy:,}</strong> / {capacity:,}</span>
                    <span class="cv-mono" style="font-weight: 700; color: {progress_color};">{occ_pct}%</span>
                </div>
                <!-- Custom Pure CSS Progress Bar -->
                <div style="width: 100%; height: 8px; background-color: #17222D; border-radius: 4px; overflow: hidden;">
                    <div style="width: {min(100.0, occ_pct)}%; height: 100%; background-color: {progress_color}; border-radius: 4px;"></div>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #94A3B8; margin-top: 0.35rem;">
                    <span>Available Spaces: <strong style="color: #34D399;">{available:,}</strong></span>
                    <span>Rated: {capacity:,} max</span>
                </div>
            </div>

            <!-- Accessibility & Contact -->
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;">
                {acc_badge}
                <span style="font-size: 0.8125rem; color: #CBD5E1; font-family: monospace;">📞 {phone}</span>
            </div>

            <div style="border-top: 1px solid #1E2D3B; padding-top: 0.4rem; font-size: 0.6875rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.04em;">
                🛡️ {source_label}
            </div>
        </div>
    </div>
    """
    cv_markdown(card_html, unsafe_allow_html=True)
