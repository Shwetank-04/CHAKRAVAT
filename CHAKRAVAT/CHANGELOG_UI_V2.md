# UI v2: what changed

## Bugs fixed
1. **Tour / shortcut buttons crashed the app**: they wrote the nav widget's session key after it existed. Navigation now uses callbacks and re-syncs the widget before creation.
2. **Map timeline buttons crashed the app**: same bug class on the slider key. Now callback-driven; "Peak/Landfall" really jumps to peak / landfall (it used to jump to the last fix).
3. **Active storm not shared between views**: three id styles (IBTrACS, CSV, name) never matched. One canonical registry (`STORM_CATALOG`, `canonical_storm_id`); Map and Forecast Lab selectors follow the global choice.
4. **Overview showed FANI for Tauktae/Yaas** (only 3 of 5 storms had metadata) and listed only 3 storms. Metadata is now derived from the track data (all 8 storms), so Overview, Map and Forecast Lab agree.
5. **Badge bugs**: custom labels lost their colour; `card_container` printed the badge type instead of its label; every `section_header` showed a stray "NORMAL" badge.
6. **Fabricated "LIVE" HUD** (static "SYNCHRONIZED / UTC 06:45") replaced by a marquee of real dataset facts labelled "historical replay"; it was also clipped under Streamlit's header.
7. **Blank map offline**: Plotly pulled basemap geometry from cdn.plot.ly. Now bundled in `static/topojson` and served locally (`enableStaticServing = true`).
8. Legend HTML had a stray `f"` breaking its style attribute; hard-coded "8 Systems" / "2017-2023" are computed.
9. `use_container_width` (removed upstream) migrated to `width="stretch"`; `requirements.txt` now needs `streamlit>=1.52`.

## New UI (TreeHacks / HackMIT inspired)
- Animated particle-cyclone hero (cursor parallax, click = shockwave), typed taglines, live UTC clock, count-up stats
- Sticky pill navigation + keyboard shortcuts (1-9, ? for help), scroll-progress bar, cursor glow
- Hard-shadow "press" buttons, glass cards with cursor spotlight + 3D tilt, spinning gradient border on the active storm
- Marquee, "mission track" card grid, FAQ accordion, pill tabs
- Guided 60-second tour (Back / Next / Exit)
- **Storm replay**: Play / Pause / speed animates the track fix-by-fix
- Respects `prefers-reduced-motion`; works offline

## Known limitations (unchanged)
- Map / Forecast Lab use `data/nio_cyclones_sample.csv` (8 storms, daily fixes, Fani 140 kt) while the **Data Sources tab uses `data/bundled/historical_cyclones.csv`** (5 storms, 6-hourly, Fani 115 kt, matching IMD's ESCS rating). Unify before presenting numbers as factual.
- Basin-context text and SST figures on the Overview are illustrative.
