"""(A) Cyclone Intelligence Overview Section View.

Landing page: animated hero, operational readiness strip, replay spotlight for the active
benchmark storm, mission-track cards, the 5-storm benchmark library and an FAQ.

All numeric storm facts (peak wind, pressure, category, landfall) are derived from the bundled
best-track dataset so that this page can never disagree with the Map and Prediction views.
"""

from functools import lru_cache
from typing import Any, Dict, List

import streamlit as st

from src.geo.tracks import load_cyclone_tracks_from_csv
from src.ui.components import (
    cv_markdown,
    eyebrow,
    experimental_disclaimer_banner,
    faq,
    grid_row,
    metric_card,
    card_container,
    severity_badge,
    track_card_html,
)
from src.ui.hero import render_hero
from src.ui.state import (
    BENCHMARK_STORMS,
    STORM_CATALOG,
    canonical_storm_id,
    get_active_storm_id,
    get_alerts,
    get_community_reports,
    get_shelters,
    go_to_tour_step,
    set_active_storm_id,
    set_current_section,
)

# Editorial context that cannot be derived from numbers (kept short and factual).
_EDITORIAL: Dict[str, Dict[str, str]] = {
    "NIO_2017_01": {
        "landfall_target": "Kerala / Lakshadweep",
        "summary": "Struck southern Kerala, Tamil Nadu and Lakshadweep before curving north toward Gujarat. Many fishing boats were caught at sea, which reshaped how fishermen are warned.",
    },
    "NIO_2018_01": {
        "landfall_target": "Gopalpur, Odisha",
        "summary": "A Very Severe Cyclonic Storm that crossed the Odisha–Andhra coast near Gopalpur, flooding Srikakulam and Ganjam districts with heavy rain and surge.",
    },
    "NIO_2022_01": {
        "landfall_target": "Andhra Pradesh coast",
        "summary": "Weakened as it skirted the Andhra Pradesh coast, a useful benchmark for a storm whose intensity fell sharply close to land.",
    },
    "2019117N12089": {
        "landfall_target": "Puri, Odisha",
        "summary": "Made landfall near Puri with winds near 175 km/h, one of the most intense pre-monsoon storms to strike Odisha in two decades. Large-scale early evacuations kept the human toll far below what the intensity implied.",
    },
    "2020137N10086": {
        "landfall_target": "Sundarbans, West Bengal",
        "summary": "The first Super Cyclonic Storm in the Bay of Bengal since 1999. Its tidal surge inundated the Sundarbans and caused catastrophic damage across the Kolkata region.",
    },
    "2021134N11072": {
        "landfall_target": "Diu / Saurashtra, Gujarat",
        "summary": "A rapidly intensifying Arabian Sea storm that tracked up India's west coast before landfall in Gujarat, one of the strongest to strike the state in over two decades.",
    },
    "2021144N16090": {
        "landfall_target": "Dhamra, Odisha",
        "summary": "A Very Severe Cyclonic Storm that crossed the Odisha coast near Dhamra days after Tauktae, driving storm-surge flooding along Odisha and West Bengal.",
    },
    "2023157N13066": {
        "landfall_target": "Kutch, Gujarat",
        "summary": "Among the longest-lived cyclones recorded in the Arabian Sea. A complex recurving track delayed its Gujarat landfall by days and gave authorities long lead time to evacuate.",
    },
}

_CATEGORY_LABELS = {
    "D": "Depression (D)", "DD": "Deep Depression (DD)", "CS": "Cyclonic Storm (CS)",
    "SCS": "Severe Cyclonic Storm (SCS)", "VSCS": "Very Severe Cyclonic Storm (VSCS)",
    "ESCS": "Extremely Severe Cyclonic Storm (ESCS)", "SuCS": "Super Cyclonic Storm (SuCS)",
}
_CATEGORY_SEVERITY = {"SuCS": "extreme", "ESCS": "extreme", "VSCS": "severe", "SCS": "warning", "CS": "advisory", "DD": "watch", "D": "normal"}
_ACCENTS = ["cyan", "violet", "pink", "mint", "amber", "coral"]
_COMPASS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]


def _compass(deg: Any) -> str:
    try:
        return _COMPASS[int((float(deg) % 360) / 22.5 + 0.5) % 16]
    except (TypeError, ValueError):
        return "n/a"


@lru_cache(maxsize=1)
def _build_storm_metadata() -> Dict[str, Dict[str, Any]]:
    """Build the storm table from the bundled dataset (cached; the data is static)."""
    try:
        tracks = load_cyclone_tracks_from_csv()
    except Exception:
        tracks = {}
    meta: Dict[str, Dict[str, Any]] = {}
    for sid, cat in STORM_CATALOG.items():
        track = tracks.get(cat["name"])
        edit = _EDITORIAL.get(sid, {})
        entry: Dict[str, Any] = {
            "id": sid, "csv_id": cat["csv_id"], "name": cat["name"],
            "landfall_target": edit.get("landfall_target", "Coastal India"),
            "summary": edit.get("summary", ""),
            "has_data": track is not None,
        }
        if track is not None:
            code = track.max_category_code
            lf = track.landfall_waypoint
            entry.update(
                year=int(track.start_time[:4]),
                basin=track.basin_full_name,
                basin_code="BOB" if track.basin_full_name == "Bay of Bengal" else "AS",
                category_code=code,
                peak_category=_CATEGORY_LABELS.get(code, track.max_category_name),
                severity=_CATEGORY_SEVERITY.get(code, "warning"),
                peak_wind_kts=round(track.peak_wind_kts),
                peak_wind_kmh=round(track.peak_wind_kmh),
                min_pressure_hpa=round(track.min_pressure_mb),
                fixes=len(track.waypoints),
                start=track.start_time[:10],
                end=track.end_time[:10],
                days=max(1, round((len(track.waypoints) - 1) * 6 / 24)),
                landfall_date=lf.timestamp_utc[:10] if lf else "No coastal crossing",
                landfall_wind_kts=round(lf.wind_kts) if lf else None,
                movement=(f"{_compass(lf.movement_dir_deg)} at {lf.movement_speed_kph:.0f} km/h"
                          if lf and lf.movement_dir_deg is not None and lf.movement_speed_kph is not None else "n/a"),
            )
        else:  # dataset missing: degrade gracefully rather than crash the landing page
            entry.update(
                year=int(sid[:4]), basin="North Indian Ocean", basin_code="BOB", category_code="n/a",
                peak_category="Unavailable", severity="normal", peak_wind_kts=0, peak_wind_kmh=0,
                min_pressure_hpa=0, fixes=0, start="-", end="-", days=0, landfall_date="-",
                landfall_wind_kts=None, movement="n/a",
            )
        meta[sid] = entry
    return meta


# Public, import-compatible views of the table.
STORM_METADATA: Dict[str, Dict[str, Any]] = _build_storm_metadata()
ALIASES: Dict[str, str] = {}
for _sid, _c in STORM_CATALOG.items():
    ALIASES[_c["name"]] = _sid
    ALIASES[_c["csv_id"]] = _sid
    ALIASES[_c["csv_id"][:-1]] = _sid
    ALIASES[_sid] = _sid


def _resolve_storm_meta(storm_id: str) -> Dict[str, Any]:
    """Resolve storm metadata from any identifier style (never silently returns the wrong storm)."""
    return _build_storm_metadata()[canonical_storm_id(storm_id)]


# ---------------------------------------------------------------------------
# Callbacks (run before the script body, so navigation can never hit a live widget key)
# ---------------------------------------------------------------------------
def _goto(section_key: str) -> None:
    set_current_section(section_key)


def _select_storm(storm_id: str) -> None:
    set_active_storm_id(storm_id)
    st.toast(f"{STORM_CATALOG[storm_id]['name']} is now the active storm everywhere", icon="🌀")


def _replay_on_map(storm_id: str) -> None:
    set_active_storm_id(storm_id)
    st.session_state["map_autoplay"] = True
    set_current_section("b")


def _start_tour() -> None:
    go_to_tour_step(0)


_FAQ = [
    {"q": "Is this a live forecast system?",
     "a": "No. CHAKRAVAT is a decision-support prototype that replays historical IBTrACS best-track data for five benchmark storms. Nothing here is a live feed, and it must never replace bulletins from IMD / RSMC New Delhi."},
    {"q": "How do you avoid inflated ML scores?",
     "a": "Storms are split at the storm level (never fix-by-fix), so no storm appears in both train and test. Every model is scored against persistence and CLIPER baselines using held-out great-circle error in km and wind MAE in knots."},
    {"q": "What does the human-in-the-loop alert workflow do?",
     "a": "Drafted alerts sit in a review queue. A reviewer must approve, reject or request changes, and every transition is written to an audit trail, so no model output becomes a public bulletin automatically."},
    {"q": "Does it need an internet connection?",
     "a": "No. The basemap, fonts, data and models are all bundled. The interface uses system fonts and zero CDN assets, so it keeps working in an air-gapped control room."},
    {"q": "Can I change the active storm?",
     "a": "Yes. Pick any storm in the library below, or use the ⚙️ menu in the top bar. The Map, Forecast Lab and this page all follow the same selection."},
]

_TRACKS = [
    ("map", "🗺️", "Storm Map", "Replay tracks fix-by-fix with a play button, scrubber and hover telemetry.", "Interactive", "cyan"),
    ("c", "🧠", "Forecast Lab", "Leak-free ML track and intensity forecasts vs. real baselines.", "ML", "violet"),
    ("d", "🧪", "Data Quality", "Provenance, completeness and a canonical 18-column schema.", "Audit", "mint"),
    ("e", "🚨", "Alert Workflow", "Draft, review and approve bulletins with a full audit trail.", "Human-in-loop", "coral"),
    ("f", "📣", "Community Reports", "Crowdsourced field reports with a five-state review flow.", "Crowd", "amber"),
    ("g", "🛟", "Shelter Directory", "Search and filter cyclone shelters by capacity and district.", "Relief", "pink"),
    ("h", "🚁", "Disaster Response", "Regional risk, safe zones and a dispatch task board.", "Ops", "cyan"),
    ("i", "📖", "Methodology", "Every assumption, metric and safeguard, written down.", "Docs", "violet"),
    ("tour", "🧭", "60-Second Tour", "A guided walk through the map, the ML engine and the alert workflow.", "Start here", "pink"),
]


def render() -> None:
    """Render Section A: Cyclone Intelligence Overview."""
    all_meta = _build_storm_metadata()
    active_meta = _resolve_storm_meta(get_active_storm_id())
    active_id = active_meta["id"]

    # ---- Hero ---------------------------------------------------------------------------
    with_data = [m for m in all_meta.values() if m["has_data"]]
    render_hero({
        "storms": len(with_data),
        "fixes": sum(m["fixes"] for m in with_data),
        "peak_kt": max((m["peak_wind_kts"] for m in with_data), default=0),
    })
    with st.container(key="hero_cta"):
        c1, c2, c3 = grid_row(3)
        with c1:
            st.button("▶ Start the 60-second tour", type="primary", width="stretch", key="hero_tour", on_click=_start_tour)
        with c2:
            st.button(f"🌀 Replay {active_meta['name']} on the map", width="stretch", key="hero_replay", on_click=_replay_on_map, args=(active_id,))
        with c3:
            st.button("🧠 Open the Forecast Lab", width="stretch", key="hero_lab", on_click=_goto, args=("c",))

    experimental_disclaimer_banner(
        "<strong>⚠️ EXPERIMENTAL DECISION-SUPPORT PROTOTYPE — NOT AN OFFICIAL METEOROLOGICAL SERVICE.</strong><br>"
        "All telemetry, forecasts and impact assessments are research estimates built on <em>historical</em> best-track data. "
        "They are not warnings. For official cyclone bulletins and evacuation directives consult the India Meteorological Department "
        "(IMD / RSMC New Delhi) at <a href='https://rsmcnewdelhi.imd.gov.in' target='_blank' rel='noopener' "
        "style='color:#38BDF8;text-decoration:underline;font-weight:600;'>rsmcnewdelhi.imd.gov.in</a> and state disaster management authorities."
    )

    # ---- Readiness strip ----------------------------------------------------------------
    alerts = get_alerts()
    pending = len([a for a in alerts if a.get("status") == "Pending"])
    active_alerts = len([a for a in alerts if a.get("status") in ("Approved", "Pending")])
    reports = get_community_reports()
    verified = len([r for r in reports if r.get("is_verified") or r.get("status") == "Verified"])
    shelters = get_shelters()
    open_shelters = len([s for s in shelters if s.get("capacity", 0) > s.get("occupancy", 0)])

    eyebrow("Operational readiness")
    cols = grid_row(3)
    with cols[0]:
        metric_card("Active Coastal Alerts", active_alerts, unit="bulletins", delta=f"{pending} pending review",
                    delta_type="negative" if active_alerts else "neutral", badge_text="Operational",
                    badge_severity="warning" if active_alerts else "normal", help_text="Watch & warning advisories in the queue")
    with cols[1]:
        metric_card("Verified Field Reports", verified, unit=f"/ {len(reports)} total", delta="Ground-confirmed incident reports",
                    delta_type="positive" if verified else "neutral", badge_text="Ground truth",
                    badge_severity="verified" if verified else "advisory", help_text="Verified by local response teams")
    with cols[2]:
        metric_card("Available Relief Shelters", open_shelters, unit=f"/ {len(shelters)} shelters", delta="Open capacity along coastlines",
                    delta_type="positive", badge_text="Safe zones", badge_severity="verified", help_text="Multipurpose cyclone shelters")

    # ---- Replay spotlight ---------------------------------------------------------------
    eyebrow(f"Replay spotlight · {active_meta['name']} {active_meta['year']}")
    s1, s2, s3 = grid_row(3)
    with s1:
        metric_card("Peak Intensity Class", active_meta["category_code"], unit=f"({active_meta['basin']})",
                    delta=active_meta["peak_category"], delta_type="negative", badge_text="IMD tier",
                    badge_severity=active_meta["severity"], help_text="Derived from peak sustained wind")
    with s2:
        metric_card("Peak Wind & Core Pressure", active_meta["peak_wind_kmh"], unit="km/h",
                    delta=f"{active_meta['peak_wind_kts']} kts · {active_meta['min_pressure_hpa']} hPa", delta_type="negative",
                    badge_text="Dataset peak", badge_severity="danger", help_text="Maximum sustained wind across all fixes")
    with s3:
        metric_card("Storm Lifetime", active_meta["days"], unit="days",
                    delta=f"{active_meta['fixes']} fixes · {active_meta['start']} → {active_meta['end']}", delta_type="neutral",
                    badge_text=f"Landfall: {active_meta['landfall_target'].split(',')[0]}", badge_severity="warning",
                    help_text=f"Landfall fix {active_meta['landfall_date']} · heading {active_meta['movement']}")

    cv_markdown("<div style='height:.9rem'></div>", unsafe_allow_html=True)
    col_story, col_replay = st.columns([2, 1])
    with col_story:
        with card_container(title=f"Case file · Cyclone {active_meta['name']}", badge_label="Historical", badge_type="experimental"):
            cv_markdown(
                f"""
                <div style="font-size:.92rem;color:#cbd5e1;line-height:1.7;margin-bottom:.8rem;">{active_meta['summary']}</div>
                <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:.6rem;">
                    <div style="padding:.7rem .85rem;border-radius:14px;border:1px solid rgba(130,160,190,.22);background:rgba(11,17,23,.5)">
                        <div style="font:700 .6rem ui-monospace,Consolas,monospace;letter-spacing:.13em;color:#8aa0b6">LANDFALL SECTOR</div>
                        <div style="font-weight:800;color:#fff;margin-top:.2rem">{active_meta['landfall_target']}</div></div>
                    <div style="padding:.7rem .85rem;border-radius:14px;border:1px solid rgba(130,160,190,.22);background:rgba(11,17,23,.5)">
                        <div style="font:700 .6rem ui-monospace,Consolas,monospace;letter-spacing:.13em;color:#8aa0b6">LANDFALL FIX</div>
                        <div class="cv-mono" style="font-weight:800;color:#7dd3fc;margin-top:.2rem">{active_meta['landfall_date']}</div></div>
                    <div style="padding:.7rem .85rem;border-radius:14px;border:1px solid rgba(130,160,190,.22);background:rgba(11,17,23,.5)">
                        <div style="font:700 .6rem ui-monospace,Consolas,monospace;letter-spacing:.13em;color:#8aa0b6">MOTION AT LANDFALL</div>
                        <div style="font-weight:800;color:#fff;margin-top:.2rem">{active_meta['movement']}</div></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    with col_replay:
        with card_container(title="Watch it unfold"):
            cv_markdown("<p style='color:#a9b9ca;font-size:.86rem;line-height:1.55;margin:0 0 .6rem'>"
                        "Replay every synoptic fix of this storm on the basemap, with live telemetry.</p>", unsafe_allow_html=True)
            st.button("▶ Replay on the map", type="primary", width="stretch", key="spot_replay", on_click=_replay_on_map, args=(active_id,))
            st.button("🎯 Forecast this storm", width="stretch", key="spot_forecast", on_click=_goto, args=("c",))

    # ---- Mission tracks (TreeHacks-style "tracks" grid) -----------------------------------
    eyebrow("Mission tracks")
    for row_start in range(0, len(_TRACKS), 3):
        row = grid_row(len(_TRACKS[row_start:row_start + 3]))
        for col, (key, icon, title, blurb, tag, accent) in zip(row, _TRACKS[row_start:row_start + 3]):
            with col:
                with st.container(key=f"trk_{key}"):
                    cv_markdown(track_card_html(icon, title, blurb, tag, accent), unsafe_allow_html=True)
                    if key == "tour":
                        st.button("Start the tour →", key="trkbtn_tour", width="stretch", on_click=_start_tour)
                    else:
                        st.button(f"Open {title} →", key=f"trkbtn_{key}", width="stretch", on_click=_goto, args=(key,))

    # ---- Storm library --------------------------------------------------------------------
    eyebrow("Benchmark storm library")
    cv_markdown("<p style='color:#a9b9ca;font-size:.9rem;margin:-.2rem 0 .9rem'>Pick a storm. The map, forecast lab and spotlight all follow your choice.</p>", unsafe_allow_html=True)
    sids = list(STORM_CATALOG.keys())
    for row_start in range(0, len(sids), 3):
        row_ids = sids[row_start:row_start + 3]
        row = grid_row(len(row_ids))
        for col, sid in zip(row, row_ids):
            m = all_meta[sid]
            selected = sid == active_id
            with col:
                with st.container(key="storm_active" if selected else f"storm_{m['name'].lower()}"):
                    cv_markdown(
                        f"""
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.35rem;">
                            <span style="font-weight:850;font-size:1.12rem;letter-spacing:-.02em;color:#fff;">{m['name']}</span>
                            {severity_badge(m['severity'], label=m['category_code'])}
                        </div>
                        <div style="font:700 .66rem ui-monospace,Consolas,monospace;letter-spacing:.12em;color:#38BDF8;margin-bottom:.55rem;">{m['basin'].upper()} · {m['year']}</div>
                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:.3rem .8rem;font-size:.8rem;color:#cbd5e1;margin-bottom:.5rem;">
                            <div><span style="color:#8aa0b6">Peak wind</span><br><b class="cv-mono">{m['peak_wind_kts']} kt</b></div>
                            <div><span style="color:#8aa0b6">Core pressure</span><br><b class="cv-mono">{m['min_pressure_hpa']} hPa</b></div>
                        </div>
                        <div style="font-size:.76rem;color:#8aa0b6;margin-bottom:.65rem;">📍 {m['landfall_target']}</div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.button(
                        "✓ Active storm" if selected else f"Select {m['name']} →",
                        key=f"btn_select_storm_{m['name']}",
                        width="stretch",
                        type="primary" if selected else "secondary",
                        on_click=_select_storm,
                        args=(sid,),
                    )

    # ---- FAQ -------------------------------------------------------------------------------
    eyebrow("Mission briefing FAQ")
    faq(_FAQ)
