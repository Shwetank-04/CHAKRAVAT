"""(B) Interactive Map & Track Intelligence Section View.

Provides North Indian Ocean (Bay of Bengal & Arabian Sea) offline geospatial
mapping, multi-storm comparative trajectories, single-storm waypoint telemetry,
chronological timeline scrubbing, and IMD-scale intensity classification.
"""

from functools import lru_cache
from typing import Any, Dict, List, Optional
import pandas as pd
import streamlit as st

from src.geo.map_engine import build_multi_storm_figure, build_single_storm_figure, geo_chart_config
from src.geo.styling import (
    IMD_CATEGORIES,
    STORM_COLOR_PALETTE,
    get_category_style,
    get_imd_legend_items,
)
from src.geo.tracks import CycloneTrack, build_track_summary, load_cyclone_tracks_from_csv
from src.ui.components import (
    cv_markdown,
    card_container,
    experimental_disclaimer_banner,
    grid_row,
    metric_card,
    section_header,
    severity_badge,
    state_box,
)
from src.ui.state import canonical_storm_id, get_active_storm_id, set_active_storm_id, storm_name_for


_PLOT_CONFIG = geo_chart_config({"displayModeBar": True})


@lru_cache(maxsize=1)
def _cached_tracks() -> Dict[str, CycloneTrack]:
    return load_cyclone_tracks_from_csv()


def _scrub_key(name: str) -> str:
    return f"sec_b_scrub_{name}"


def _on_map_storm_change() -> None:
    """Selecting a storm on the map makes it the active storm app-wide."""
    choice = st.session_state.get("sec_b_storm_selector")
    st.session_state["map_playing"] = False
    if choice and choice != "ALL_STORMS":
        set_active_storm_id(choice)
        st.session_state["map_seen_active"] = canonical_storm_id(choice)


# Transport callbacks run before the script body, so writing the slider's key is legal here
# (doing it inline, after the slider existed, raised StreamlitAPIException and crashed the page).
def _cb_seek(name: str, idx: int) -> None:
    st.session_state[_scrub_key(name)] = idx
    st.session_state["map_playing"] = False


def _cb_step(name: str, delta: int, n: int) -> None:
    cur = int(st.session_state.get(_scrub_key(name), n - 1))
    st.session_state[_scrub_key(name)] = max(0, min(n - 1, cur + delta))
    st.session_state["map_playing"] = False


def _cb_toggle_play(name: str, n: int) -> None:
    if st.session_state.get("map_playing"):
        st.session_state["map_playing"] = False
        return
    if int(st.session_state.get(_scrub_key(name), n - 1)) >= n - 1:
        st.session_state[_scrub_key(name)] = 0  # replay from genesis
    st.session_state["map_playing"] = True


def _render_transport(track: CycloneTrack) -> None:
    """Play/pause + seek controls. Kept outside the fragment so toggling play re-arms its timer."""
    name, n = track.storm_name, len(track.waypoints)
    if n < 2:
        return
    peak_idx = max(range(n), key=lambda i: track.waypoints[i].wind_kts)
    lf_idx = next((i for i, w in enumerate(track.waypoints) if w.is_landfall), None)
    playing = bool(st.session_state.get("map_playing", False))
    cv_markdown(
        "<div class='cv-eyebrow' style='margin-top:.2rem'>Storm replay</div>",
        unsafe_allow_html=True,
    )
    cols = st.columns([1, 1, 1.7, 1, 1.3, 1.5, 1.5], vertical_alignment="bottom")
    with cols[0]:
        st.button("⏮", key=f"btn_gen_{name}", width="stretch", help="Genesis", on_click=_cb_seek, args=(name, 0))
    with cols[1]:
        st.button("◀", key=f"btn_prev_{name}", width="stretch", help="Previous fix", on_click=_cb_step, args=(name, -1, n))
    with cols[2]:
        st.button("⏸ Pause" if playing else "▶ Play", key=f"btn_play_{name}", type="primary", width="stretch",
                  on_click=_cb_toggle_play, args=(name, n))
    with cols[3]:
        st.button("▶|", key=f"btn_next_{name}", width="stretch", help="Next fix", on_click=_cb_step, args=(name, 1, n))
    with cols[4]:
        st.button("🌪️ Peak", key=f"btn_peak_{name}", width="stretch", help="Jump to peak intensity", on_click=_cb_seek, args=(name, peak_idx))
    with cols[5]:
        st.button("📍 Landfall", key=f"btn_land_{name}", width="stretch", disabled=lf_idx is None,
                  help="Jump to the landfall fix" if lf_idx is not None else "This storm has no landfall fix",
                  on_click=_cb_seek, args=(name, lf_idx if lf_idx is not None else 0))
    with cols[6]:
        st.select_slider("Speed", options=["0.5×", "1×", "2×"], value="1×", key="map_speed", label_visibility="collapsed")


def _telemetry_html(wp: Any) -> str:
    cell = "<span style=\"font-size:0.6875rem;color:#94A3B8;text-transform:uppercase;letter-spacing:.08em\">{}</span><br>"
    return f"""
    <div style="border:1px solid rgba(56,189,248,.35);border-radius:16px;padding:12px 18px;margin:.6rem 0 .8rem;
                background:linear-gradient(90deg,rgba(20,31,42,.9),rgba(30,45,59,.8));box-shadow:4px 4px 0 rgba(56,189,248,.22);">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.9rem;">
        <div>{cell.format("Observation (UTC)")}<span class="cv-mono" style="color:#38BDF8;font-weight:700">{wp.timestamp_utc}</span></div>
        <div>{cell.format("Class")}<span style="color:{wp.category_color};font-weight:800;text-shadow:0 0 10px {wp.category_color}55">● {wp.category}</span></div>
        <div>{cell.format("Wind")}<b style="color:#F1F5F9">{wp.wind_kts:.0f} kt</b> <span style="color:#94A3B8;font-size:.78rem">({wp.wind_kmh:.0f} km/h)</span></div>
        <div>{cell.format("Pressure")}<b style="color:#F1F5F9">{wp.pressure_mb:.0f}</b> <span style="color:#94A3B8;font-size:.78rem">hPa</span></div>
        <div>{cell.format("Position")}<span class="cv-mono" style="color:#CBD5E1">{wp.lat:.2f}°N, {wp.lon:.2f}°E</span></div>
      </div>
    </div>"""


def _replay_panel(name: str, show_lines: bool, show_markers: bool, show_landfall: bool) -> None:
    """Scrubber, telemetry, map and fix table for one storm. Runs on a timer while playing."""
    track = _cached_tracks().get(name)
    if track is None or not track.waypoints:
        return
    n = len(track.waypoints)
    key = _scrub_key(name)
    playing = bool(st.session_state.get("map_playing", False))
    finished = False

    if key not in st.session_state:
        st.session_state[key] = n - 1
    if playing:  # advance *before* the slider is created, which is the only legal moment
        if int(st.session_state[key]) >= n - 1:
            finished = True
        else:
            st.session_state[key] = int(st.session_state[key]) + 1
            finished = st.session_state[key] >= n - 1

    step = n - 1
    if n > 1:
        step = st.slider("Track progression step", min_value=0, max_value=n - 1, format="Fix %d",
                         label_visibility="collapsed", key=key)
    wp = track.waypoints[step]
    cv_markdown(_telemetry_html(wp), unsafe_allow_html=True)

    with card_container():
        fig = build_single_storm_figure(track=track, up_to_step=step, show_lines=show_lines,
                                        show_markers=show_markers, show_landfall=show_landfall,
                                        auto_center=True, height=650)
        st.plotly_chart(fig, width="stretch", config=_PLOT_CONFIG)

    with card_container(title=f"Detailed Synoptic Fixes — Cyclone {track.storm_name} ({step + 1} of {n} fixes)"):
        rows = []
        for w in track.waypoints[: step + 1]:
            rows.append({
                "Timestamp (UTC)": w.timestamp_utc, "Latitude": f"{w.lat:.2f}°N", "Longitude": f"{w.lon:.2f}°E",
                "IMD Category": w.category_code, "Classification": w.category,
                "Wind (kt)": f"{w.wind_kts:.0f}", "Wind (km/h)": f"{w.wind_kmh:.0f}", "Pressure (hPa)": f"{w.pressure_mb:.0f}",
                "Coast Dist": f"{w.dist_coast_km:.0f} km" if w.dist_coast_km is not None else "-",
                "Forward Motion": (f"{w.movement_speed_kph:.0f} km/h @ {w.movement_dir_deg:.0f}°"
                                   if w.movement_speed_kph is not None and w.movement_dir_deg is not None else "-"),
                "Landfall Fix": "★ YES" if w.is_landfall else "No",
            })
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    if finished and playing:  # drop the timer: a full rerun re-decorates the fragment without run_every
        st.session_state["map_playing"] = False
        st.rerun(scope="app")


def render() -> None:
    """Render Section B: Interactive Map & Track Intelligence."""
    section_header(
        title="Interactive Map & Track Intelligence",
        subtitle="North Indian Ocean cyclonic track trajectories, IMD-grade synoptic telemetry, and historical waypoint inspection.",
        badge_label="BASIN INTELLIGENCE",
        badge_type="normal",
    )

    # Mandatory Scientific Decision-Support Disclaimer
    experimental_disclaimer_banner(
        "<strong>⚠️ RESEARCH & DECISION-SUPPORT CARTOGRAPHY — HISTORICAL BEST-TRACK DATA</strong><br>"
        "Tracks and telemetry represent verified historical observations (IBTrACS v04 / IMD RSMC New Delhi). "
        "Intended for meteorological decision-support, climatological comparison, and evacuation planning simulations."
    )

    # Load cyclone tracks from dataset
    try:
        tracks = load_cyclone_tracks_from_csv()
    except Exception as e:
        state_box(
            title="Dataset Loading Error",
            message=f"Unable to parse cyclone dataset: {str(e)}",
            icon="⚠️",
            box_type="error",
        )
        return

    if not tracks:
        state_box(
            title="No Cyclone Tracks Available",
            message="No valid cyclone observation records found in the configured data source.",
            icon="ℹ️",
            box_type="empty",
        )
        return

    # -----------------------------------------------------------------------
    # 1. Storm Selection & Basin Controls
    # -----------------------------------------------------------------------
    storm_names = list(tracks.keys())
    
    # Map storm options with informative labels
    overview_key = "ALL_STORMS"
    selector_options = [overview_key] + storm_names

    def format_storm_label(opt: str) -> str:
        if opt == overview_key:
            return f"🌐 All Storms (Comparative Basin Overview • {len(tracks)} Systems)"
        t = tracks.get(opt)
        if t:
            year = t.start_time[:4] if t.start_time and len(t.start_time) >= 4 else ""
            basin = "Bay of Bengal" if "Bay" in t.basin_full_name else "Arabian Sea"
            return f"Cyclone {t.storm_name} ({year}) — {basin} • {t.max_category_code}"
        return f"Cyclone {opt}"

    # Keep this widget in step with the global active storm (sidebar / overview / forecast lab).
    # Writing the widget key *before* it is created is allowed; ``index=`` would be ignored once
    # the key exists, which is why the old selector never followed the rest of the app.
    active_id = get_active_storm_id()
    active_name = storm_name_for(active_id)
    if st.session_state.get("map_seen_active") != active_id:
        st.session_state["map_seen_active"] = active_id
        if active_name in tracks:
            st.session_state["sec_b_storm_selector"] = active_name
    if st.session_state.get("sec_b_storm_selector") not in selector_options:
        st.session_state["sec_b_storm_selector"] = active_name if active_name in tracks else overview_key

    # Autoplay requested from the Overview ("Replay on the map")
    if st.session_state.pop("map_autoplay", False) and active_name in tracks:
        st.session_state[f"sec_b_scrub_{active_name}"] = 0
        st.session_state["map_playing"] = True

    ctrl_col1, ctrl_col2 = st.columns([3, 2])
    with ctrl_col1:
        selected_option = st.selectbox(
            "Select Cyclonic System / Overview:",
            options=selector_options,
            format_func=format_storm_label,
            key="sec_b_storm_selector",
            on_change=_on_map_storm_change,
        )
    with ctrl_col2:
        cv_markdown(
            "<div style='font-size: 0.8125rem; color: #94A3B8; margin-bottom: 0.25rem; font-weight: 500;'>DISPLAY LAYERS:</div>",
            unsafe_allow_html=True,
        )
        toggle_cols = st.columns(3)
        with toggle_cols[0]:
            show_lines = st.checkbox("Trajectory Lines", value=True, key="sec_b_lines")
        with toggle_cols[1]:
            show_markers = st.checkbox("Intensity Fixes", value=True, key="sec_b_markers")
        with toggle_cols[2]:
            show_landfall = st.checkbox("Landfall Points", value=True, key="sec_b_landfall")

    is_overview = (selected_option == overview_key)

    # -----------------------------------------------------------------------
    # 2. Telemetry KPI Metric Strip (Strictly <= 3 cards per row)
    # -----------------------------------------------------------------------
    if is_overview:
        # Comparative overview KPI strip
        total_storms = len(tracks)
        bob_count = sum(1 for t in tracks.values() if "Bay" in t.basin_full_name)
        as_count = total_storms - bob_count
        peak_storm = max(tracks.values(), key=lambda t: t.peak_wind_kts)

        kpi_row = grid_row(3)
        with kpi_row[0]:
            metric_card(
                label="Historical Cyclone Trajectories",
                value=f"{total_storms} Storms",
                badge_text=f"{min(t.start_time[:4] for t in tracks.values())}-{max(t.start_time[:4] for t in tracks.values())}",
                badge_severity="normal",
                help_text="Bay of Bengal & Arabian Sea basins",
            )
        with kpi_row[1]:
            metric_card(
                label="Maximum Historical Intensity",
                value=f"{peak_storm.peak_wind_kmh:.0f}",
                unit="km/h",
                delta=f"{peak_storm.peak_wind_kts:.0f} kt ({peak_storm.storm_name})",
                delta_type="negative",
                badge_text=peak_storm.max_category_code,
                badge_severity="extreme",
                help_text=f"Minimum pressure: {peak_storm.min_pressure_mb:.0f} hPa",
            )
        with kpi_row[2]:
            metric_card(
                label="Basin Distribution",
                value=f"{bob_count} BoB / {as_count} AS",
                badge_text="Dual Basin",
                badge_severity="watch",
                help_text="North Indian Ocean domain",
            )
    else:
        # Single storm telemetry KPI strip
        selected_track = tracks[selected_option]
        summary = build_track_summary(selected_track)

        kpi_row = grid_row(3)
        with kpi_row[0]:
            metric_card(
                label="Peak Sustained Wind",
                value=f"{summary['peak_wind_kmh']:.0f}",
                unit="km/h",
                delta=f"{summary['peak_wind_kts']:.0f} knots",
                delta_type="negative",
                badge_text=summary["max_category_code"],
                badge_severity="danger" if summary["peak_wind_kts"] >= 90 else "warning",
                help_text=f"IMD: {summary['max_category']}",
            )
        with kpi_row[1]:
            metric_card(
                label="Minimum Central Pressure",
                value=f"{summary['min_pressure_mb']:.0f}",
                unit="hPa",
                delta="Intense Core",
                delta_type="negative",
                badge_text="Deepest Fix",
                badge_severity="extreme" if summary["min_pressure_mb"] < 940 else "warning",
                help_text="Barometric central pressure",
            )
        with kpi_row[2]:
            lf_wp = selected_track.landfall_waypoint
            lf_value = f"{lf_wp.lat:.1f}°N, {lf_wp.lon:.1f}°E" if lf_wp else "Maritime"
            lf_time = lf_wp.timestamp_utc[:10] if lf_wp else "No coastal crossing"
            metric_card(
                label="Landfall / Coastal Target",
                value=lf_value,
                badge_text="Impact Zone",
                badge_severity="danger" if lf_wp else "normal",
                help_text=f"Landfall fix date: {lf_time}",
            )

    cv_markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # 3. Storm replay (transport bar + timed fragment) / multi-storm overview chart
    # -----------------------------------------------------------------------
    step_scrub: Optional[int] = None
    if is_overview:
        with card_container():
            fig = build_multi_storm_figure(
                tracks=tracks, show_lines=show_lines, show_markers=show_markers,
                show_landfalls=show_landfall, height=650,
            )
            st.plotly_chart(fig, width="stretch", config=_PLOT_CONFIG)
    else:
        _render_transport(tracks[selected_option])
        playing = bool(st.session_state.get("map_playing", False))
        speed = {"0.5×": 0.5, "1×": 1.0, "2×": 2.0}.get(st.session_state.get("map_speed", "1×"), 1.0)
        # The timer only exists while playing, so an idle page costs nothing.
        panel = st.fragment(run_every=(0.7 / speed) if playing else None)(_replay_panel)
        panel(selected_option, show_lines, show_markers, show_landfall)

    # -----------------------------------------------------------------------
    # 5. IMD 8-Tier Category Legend & Educational Reference
    # -----------------------------------------------------------------------
    with st.expander("📖 IMD Cyclone Intensity Scale Reference & Legend", expanded=False):
        cv_markdown(
            "<p style='color: #94A3B8; font-size: 0.8125rem; margin-bottom: 0.75rem;'>"
            "The India Meteorological Department (IMD) classifies cyclonic disturbances in the North Indian Ocean "
            "based on maximum sustained 3-minute surface wind speeds:"
            "</p>",
            unsafe_allow_html=True,
        )

        legend_items = get_imd_legend_items()
        cols = st.columns(len(legend_items))
        for idx, item in enumerate(legend_items):
            with cols[idx]:
                cv_markdown(
                    f"""
                    <div style="background-color: #17222D; border: 1px solid #2C4056; border-top: 3px solid {item['color']}; "
                         border-radius: 6px; padding: 8px 6px; text-align: center;">
                        <div style="font-weight: 700; font-size: 0.8125rem; color: {item['color']};">{item['code']}</div>
                        <div style="font-size: 0.6875rem; color: #F1F5F9; font-weight: 500; margin: 2px 0;">{item['name']}</div>
                        <div style="font-size: 0.6875rem; color: #94A3B8; font-family: monospace;">{item['min_kts']}-{item['max_kts']} kt</div>
                        <div style="font-size: 0.625rem; color: #64748B;">{item['min_kmh']:.0f}-{item['max_kmh']:.0f} km/h</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    cv_markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # 6. Waypoint Telemetry Data Table
    # -----------------------------------------------------------------------
    if is_overview:
        with card_container(title="North Indian Ocean Benchmark Storms Catalogue"):
            table_data = []
            for s_name, t in tracks.items():
                s = build_track_summary(t)
                table_data.append({
                    "Storm Name": s["storm_name"],
                    "Basin": s["basin"],
                    "Max Category": f"{s['max_category_code']} ({s['max_category']})",
                    "Peak Wind": f"{s['peak_wind_kts']:.0f} kt ({s['peak_wind_kmh']:.0f} km/h)",
                    "Min Pressure": f"{s['min_pressure_mb']:.0f} hPa",
                    "Fixes": s["total_fixes"],
                    "Track Distance": f"{s['total_distance_km']:.0f} km",
                    "Start Date": s["start_time"][:10],
                    "End Date": s["end_time"][:10],
                    "Landfall Location": s["landfall_summary"],
                })
            df_overview = pd.DataFrame(table_data)
            st.dataframe(
                df_overview,
                width="stretch",
                hide_index=True,
            )

    # -----------------------------------------------------------------------
    # 7. Data Provenance & Methodological Attribution
    # -----------------------------------------------------------------------
    cv_markdown(
        "<div style='border-top: 1px solid #1E2D3B; padding-top: 0.75rem; margin-top: 1.5rem; "
        "font-size: 0.75rem; color: #64748B; display: flex; justify-content: space-between;'>"
        "<span><strong>Data Provenance:</strong> International Best Track Archive for Climate Stewardship (IBTrACS v04) & IMD RSMC New Delhi</span>"
        "<span><strong>Cartography Engine:</strong> Plotly go.Scattergeo (100% Offline Air-Gapped)</span>"
        "<span><strong>Basin:</strong> North Indian Ocean (WMO Area of Responsibility)</span>"
        "</div>",
        unsafe_allow_html=True,
    )
