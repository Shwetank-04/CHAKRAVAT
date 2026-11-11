"""CHAKRAVAT: North Indian Ocean Cyclone Intelligence & Disaster Response Platform.

Main Streamlit application shell: sticky pill navigation, guided tour and view router.
"""

import streamlit as st
from src.ui.components import cv_markdown, marquee

# 1. Page configuration (must be the first Streamlit command)
st.set_page_config(
    page_title="CHAKRAVAT | Cyclone Intelligence",
    page_icon="🌀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. Design system + interaction layer
from src.ui.theme import inject_custom_theme
from src.ui.effects import inject_effects

inject_custom_theme()

# 3. Persistent demo session state
from src.ui.state import (
    SECTIONS,
    BENCHMARK_STORMS,
    TOUR_STEPS,
    init_session_state,
    reset_session_state,
    get_current_section,
    set_current_section,
    get_active_storm_id,
    set_active_storm_id,
    get_tour_step,
    go_to_tour_step,
    end_tour,
)

init_session_state()

# 4. Section views
from src.views import (
    render_overview,
    render_map,
    render_prediction,
    render_data_sources,
    render_alerts,
    render_community,
    render_shelters,
    render_response,
    render_about,
)

VIEW_ROUTER = {
    SECTIONS[0]: render_overview,
    SECTIONS[1]: render_map,
    SECTIONS[2]: render_prediction,
    SECTIONS[3]: render_data_sources,
    SECTIONS[4]: render_alerts,
    SECTIONS[5]: render_community,
    SECTIONS[6]: render_shelters,
    SECTIONS[7]: render_response,
    SECTIONS[8]: render_about,
}

# Short pill labels (the long names stay in SECTIONS for routing/tests). Order == keyboard 1-9.
NAV_LABELS = {
    SECTIONS[0]: "🏠 Overview",
    SECTIONS[1]: "🗺️ Storm Map",
    SECTIONS[2]: "🧠 Forecast Lab",
    SECTIONS[3]: "🧪 Data",
    SECTIONS[4]: "🚨 Alerts",
    SECTIONS[5]: "📣 Community",
    SECTIONS[6]: "🛟 Shelters",
    SECTIONS[7]: "🚁 Response",
    SECTIONS[8]: "📖 About",
}


# ---------------------------------------------------------------------------
# Callbacks. They run *before* the script body, so they may safely touch widget-owned state.
# ---------------------------------------------------------------------------
def _on_nav_change() -> None:
    set_current_section(st.session_state.get("nav_radio_selection", SECTIONS[0]))


def _on_storm_change() -> None:
    set_active_storm_id(st.session_state.get("ctl_storm_selector", ""))


def _on_reset() -> None:
    reset_session_state()
    for key in ("tour_step", "nav_radio_selection", "ctl_storm_selector", "map_playing", "map_seen_active"):
        st.session_state.pop(key, None)
    st.toast("Demo state reset to defaults", icon="🔄")


def _tour_back() -> None:
    go_to_tour_step((get_tour_step() or 0) - 1)


def _tour_next() -> None:
    step = get_tour_step() or 0
    if step >= len(TOUR_STEPS) - 1:
        end_tour()
        st.toast("Tour complete. Explore freely!", icon="🎉")
    else:
        go_to_tour_step(step + 1)


def render_topnav() -> str:
    """Brand + sticky pill navigation + controls popover."""
    with st.container(key="topnav"):
        c_brand, c_nav, c_ctl = st.columns([1.45, 7.4, 0.9], vertical_alignment="center")

        with c_brand:
            cv_markdown(
                """
                <div class="cv-brand">
                    <span class="cv-brand-mark">🌀</span>
                    <div><div class="cv-brand-name">CHAKRAVAT</div>
                    <div class="cv-brand-sub">NIO intelligence</div></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c_nav:
            # Re-sync the widget from the source of truth *before* it is instantiated.
            current = get_current_section()
            if st.session_state.get("nav_radio_selection") != current:
                st.session_state["nav_radio_selection"] = current
            st.radio(
                "Section",
                options=SECTIONS,
                format_func=lambda s: NAV_LABELS.get(s, s),
                horizontal=True,
                label_visibility="collapsed",
                key="nav_radio_selection",
                on_change=_on_nav_change,
            )

        with c_ctl:
            with st.popover("⚙️", help="Demo controls", width="stretch"):
                active = get_active_storm_id()
                if st.session_state.get("ctl_storm_selector") != active:
                    st.session_state["ctl_storm_selector"] = active
                st.selectbox(
                    "Active storm focus",
                    options=list(BENCHMARK_STORMS.keys()),
                    format_func=lambda k: BENCHMARK_STORMS.get(k, k).split("—")[0].strip(),
                    key="ctl_storm_selector",
                    on_change=_on_storm_change,
                )
                if st.button("▶ Start 60-second tour", width="stretch", key="ctl_tour"):
                    go_to_tour_step(0)
                    st.rerun()
                st.button("🔄 Reset demo state", width="stretch", key="ctl_reset", on_click=_on_reset)
                cv_markdown(
                    "<div style='font-size:.7rem;color:#7f93a8;line-height:1.5;margin-top:.6rem'>"
                    "<b>Decision-support prototype.</b> Not for life-safety use. Official warnings: "
                    "<em>IMD New Delhi</em>.<br>Shortcuts: press <b>1–9</b> to jump, <b>?</b> for help.</div>",
                    unsafe_allow_html=True,
                )
    return current


def _marquee_items() -> list:
    """Real facts from the bundled best-track data (replaces the old fabricated 'live' HUD)."""
    try:
        from src.geo.tracks import load_cyclone_tracks_from_csv

        items = []
        for name, t in load_cyclone_tracks_from_csv().items():
            items.append(f"{name} {t.start_time[:4]} · {t.max_category_code} · {t.peak_wind_kts:.0f} kt · {t.min_pressure_mb:.0f} hPa")
        return ["Historical replay · not a live feed"] + items + ["IMD RSMC New Delhi is the official authority"]
    except Exception:
        return ["Historical replay · not a live feed", "North Indian Ocean", "Bay of Bengal · Arabian Sea"]


def render_tour() -> None:
    """Guided tour card with progress dots and Back / Next / Exit (all callback driven)."""
    step = get_tour_step()
    if step is None:
        return
    info = TOUR_STEPS[step]
    dots = "".join(
        f'<span class="cv-tour-dot {"on" if i == step else ("done" if i < step else "")}"></span>'
        for i in range(len(TOUR_STEPS))
    )
    cv_markdown(
        f"""
        <div class="cv-tour-card">
            <div class="cv-tour-head"><span>Guided tour {step + 1}/{len(TOUR_STEPS)}</span><span class="cv-tour-dots">{dots}</span></div>
            <div class="cv-tour-tip"><b>{info['title']}</b> — {info['tip']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    b1, b2, b3 = st.columns(3)
    with b1:
        st.button("← Back", key="tour_back", on_click=_tour_back, disabled=(step == 0), width="stretch")
    with b2:
        last = step >= len(TOUR_STEPS) - 1
        st.button("Finish 🎉" if last else "Next →", key="tour_next", on_click=_tour_next, type="primary", width="stretch")
    with b3:
        st.button("Exit tour", key="tour_exit", on_click=end_tour, width="stretch")


def main() -> None:
    """Main routing entrypoint."""
    st.session_state["_cv_card_n"] = 0  # card CSS-hook counter restarts every full run
    inject_effects()  # first element => stable position => script mounts exactly once
    selected_section = render_topnav()
    marquee(_marquee_items())
    render_tour()
    VIEW_ROUTER.get(selected_section, render_overview)()


if __name__ == "__main__":
    main()
