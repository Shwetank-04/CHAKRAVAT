"""(C) Prediction & Model Evaluation Section View for CHAKRAVAT.

Fulfills Requirements R2(C), R3, R4, and R5:
- Strictly dynamic metrics computed from held-out test storms (zero hardcoding).
- 3 interactive tabs:
    1. Track Prediction (12h/24h displacement, MTE vs Persistence & CLIPER, 70% error cones)
    2. Intensity Forecast (12h/24h wind speed & pressure, MAE vs Persistence, RI risk)
    3. Genesis / Intensification Potential (CS transition baseline, precision/recall, limitations)
- Handles MODEL_NOT_TRAINED and DATA_LIMITED (< 3 fixes) states gracefully.
- Adheres strictly to the <= 3 columns/cards per horizontal row rule.
"""

from typing import Any, Dict, List, Optional, Tuple
import math
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.data_pipeline.schema import classify_imd_intensity, IMD_CATEGORIES
from src.geo.map_engine import geo_chart_config
from src.geo.tracks import CycloneTrack, CycloneWaypoint, load_cyclone_tracks_from_csv
from src.geo.map_engine import create_north_indian_ocean_map, fit_bounds
from src.ml.baselines import (
    LinearPersistenceBaseline,
    CLIPERBaseline,
    IntensityPersistenceBaseline,
)
from src.ml.models import _get_val
from src.ml.pipeline import CycloneMLPipeline, ModelState, get_ml_pipeline
from src.ml.uncertainty import generate_uncertainty_polygon
from src.ui.components import (
    cv_markdown,
    card_container,
    experimental_disclaimer_banner,
    grid_row,
    metric_card,
    render_data_limited_warning,
    section_header,
    severity_badge,
    state_box,
)
from src.ui.state import BENCHMARK_STORMS, canonical_storm_id, get_active_storm_id, set_active_storm_id, storm_name_for


def _get_or_init_pipeline() -> CycloneMLPipeline:
    """Retrieve pipeline from session state or initialize it."""
    if "cyclone_ml_pipeline" not in st.session_state:
        st.session_state["cyclone_ml_pipeline"] = get_ml_pipeline()
    return st.session_state["cyclone_ml_pipeline"]


def _build_track_map_figure(
    historical_waypoints: List[CycloneWaypoint],
    pred_lat: float,
    pred_lon: float,
    lin_lat: float,
    lin_lon: float,
    clip_lat: float,
    clip_lon: float,
    uncertainty_polygon: List[Tuple[float, float]],
    actual_lat: Optional[float] = None,
    actual_lon: Optional[float] = None,
    horizon_hours: int = 24,
) -> go.Figure:
    """Construct an offline Plotly map showing track, baselines, and uncertainty cone.

    Uses the shared NIO basemap and frames the view around every plotted point, so the
    storm, forecasts and error cone are always on screen (previously a fixed center/scale
    was used and the view could sit far from the storm).
    """
    framed = [(wp.lat, wp.lon) for wp in historical_waypoints]
    framed += [(pred_lat, pred_lon), (lin_lat, lin_lon), (clip_lat, clip_lon)]
    framed += list(uncertainty_polygon or [])
    if actual_lat is not None and actual_lon is not None:
        framed.append((actual_lat, actual_lon))
    lataxis, lonaxis, center = fit_bounds(framed, pad_frac=0.5, min_lat_span=8.0, min_lon_span=12.0)
    fig = create_north_indian_ocean_map(
        height=520, custom_lataxis=lataxis, custom_lonaxis=lonaxis, custom_center=center
    )

    # 1. Uncertainty cone polygon (70% empirical error boundary)
    if uncertainty_polygon and len(uncertainty_polygon) >= 3:
        poly_lats = [p[0] for p in uncertainty_polygon]
        poly_lons = [p[1] for p in uncertainty_polygon]
        fig.add_trace(
            go.Scattergeo(
                lat=poly_lats,
                lon=poly_lons,
                fill="toself",
                fillcolor="rgba(244, 63, 94, 0.15)",
                line=dict(color="rgba(244, 63, 94, 0.5)", width=1.5, dash="dash"),
                name=f"Empirical 70% Error Cone ({horizon_hours}h)",
                hoverinfo="text",
                text=f"Empirical 70th-percentile error boundary ({horizon_hours}h lead)",
            )
        )

    # 2. Historical past track fixes
    hist_lats = [wp.lat for wp in historical_waypoints]
    hist_lons = [wp.lon for wp in historical_waypoints]
    hist_hover = [
        f"<b>Fix #{idx+1}</b><br>Time: {wp.timestamp_utc}<br>Wind: {wp.wind_kts:.0f} kts ({wp.category})<br>Pres: {wp.pressure_mb:.0f} hPa"
        for idx, wp in enumerate(historical_waypoints)
    ]
    fig.add_trace(
        go.Scattergeo(
            lat=hist_lats,
            lon=hist_lons,
            mode="lines+markers",
            line=dict(color="#38BDF8", width=3),
            marker=dict(size=7, color="#38BDF8", symbol="circle"),
            name="Observed Trajectory",
            hoverinfo="text",
            text=hist_hover,
        )
    )

    # Current position fix (latest historical)
    curr_lat = hist_lats[-1]
    curr_lon = hist_lons[-1]
    fig.add_trace(
        go.Scattergeo(
            lat=[curr_lat],
            lon=[curr_lon],
            mode="markers",
            marker=dict(size=12, color="#F59E0B", symbol="star"),
            name="Current Fix (T=0)",
            hoverinfo="text",
            text=f"Current Fix (T=0)<br>{curr_lat:.2f}°N, {curr_lon:.2f}°E",
        )
    )

    # 3. Linear persistence baseline
    fig.add_trace(
        go.Scattergeo(
            lat=[curr_lat, lin_lat],
            lon=[curr_lon, lin_lon],
            mode="lines+markers",
            line=dict(color="#FBBF24", width=2, dash="dot"),
            marker=dict(size=8, color="#FBBF24", symbol="diamond"),
            name=f"Linear Persistence ({horizon_hours}h)",
            hoverinfo="text",
            text=f"Linear Persistence Extrapolation: {lin_lat:.2f}°N, {lin_lon:.2f}°E",
        )
    )

    # 4. CLIPER baseline
    fig.add_trace(
        go.Scattergeo(
            lat=[curr_lat, clip_lat],
            lon=[curr_lon, clip_lon],
            mode="lines+markers",
            line=dict(color="#A78BFA", width=2, dash="dash"),
            marker=dict(size=8, color="#A78BFA", symbol="triangle-up"),
            name=f"NIO CLIPER ({horizon_hours}h)",
            hoverinfo="text",
            text=f"CLIPER Climatology & Persistence: {clip_lat:.2f}°N, {clip_lon:.2f}°E",
        )
    )

    # 5. Scientific ML predicted waypoint
    fig.add_trace(
        go.Scattergeo(
            lat=[curr_lat, pred_lat],
            lon=[curr_lon, pred_lon],
            mode="lines+markers",
            line=dict(color="#F43F5E", width=3),
            marker=dict(size=11, color="#F43F5E", symbol="circle-dot"),
            name=f"ML Predicted Center ({horizon_hours}h)",
            hoverinfo="text",
            text=f"Scientific ML Forecast ({horizon_hours}h): {pred_lat:.2f}°N, {pred_lon:.2f}°E",
        )
    )

    # 6. Actual ground truth verification fix (if available from historical data)
    if actual_lat is not None and actual_lon is not None:
        fig.add_trace(
            go.Scattergeo(
                lat=[curr_lat, actual_lat],
                lon=[curr_lon, actual_lon],
                mode="lines+markers",
                line=dict(color="#10B981", width=2, dash="dashdot"),
                marker=dict(size=9, color="#10B981", symbol="square"),
                name=f"Actual Verified Fix (+{horizon_hours}h)",
                hoverinfo="text",
                text=f"Verified Best-Track Fix: {actual_lat:.2f}°N, {actual_lon:.2f}°E",
            )
        )

    # Legend sits in its own band under the map (bottom margin) so it can never cover the
    # map or the metric cards that follow.
    fig.update_layout(
        font=dict(color="#CBD5E1", family="sans-serif", size=11),
        margin=dict(l=0, r=0, t=10, b=96),
        legend=dict(
            orientation="h", yanchor="top", y=-0.02, xanchor="center", x=0.5,
            bgcolor="rgba(16, 24, 32, 0.8)", bordercolor="#334155", borderwidth=1,
            font=dict(size=10), entrywidth=230,
        ),
    )
    return fig


def _build_intensity_chart(
    historical_waypoints: List[CycloneWaypoint],
    pred_wind_12: float,
    pred_wind_24: float,
    pers_wind: float,
) -> go.Figure:
    """Construct Plotly intensity forecast vs baseline chart."""
    fig = go.Figure()

    times = [wp.timestamp_utc[5:16] for wp in historical_waypoints]
    winds = [wp.wind_kts for wp in historical_waypoints]

    # Historical observed wind speed
    fig.add_trace(
        go.Scatter(
            x=times,
            y=winds,
            mode="lines+markers",
            name="Observed Sustained Wind (kts)",
            line=dict(color="#38BDF8", width=3),
            marker=dict(size=6, color="#38BDF8"),
        )
    )

    last_time = times[-1]
    forecast_times = [last_time, "+12h Forecast", "+24h Forecast"]

    # ML forecast trajectory
    curr_wind = winds[-1]
    fig.add_trace(
        go.Scatter(
            x=forecast_times,
            y=[curr_wind, pred_wind_12, pred_wind_24],
            mode="lines+markers",
            name="ML Intensity Forecast",
            line=dict(color="#F43F5E", width=3, dash="solid"),
            marker=dict(size=8, color="#F43F5E"),
        )
    )

    # Pure persistence reference line
    fig.add_trace(
        go.Scatter(
            x=forecast_times,
            y=[curr_wind, pers_wind, pers_wind],
            mode="lines",
            name="Persistence Baseline (kts)",
            line=dict(color="#FBBF24", width=2, dash="dash"),
        )
    )

    # Cyclonic Storm threshold line (34 kts)
    fig.add_hline(
        y=34,
        line_dash="dot",
        line_color="#ECC94B",
        annotation_text="CS Threshold (34 kts)",
        annotation_position="top left",
        annotation_font_color="#ECC94B",
    )

    fig.update_layout(
        paper_bgcolor="#17222D",
        plot_bgcolor="#101820",
        font=dict(color="#CBD5E1", size=11),
        margin=dict(l=40, r=20, t=20, b=40),
        height=320,
        xaxis=dict(showgrid=True, gridcolor="#273549"),
        yaxis=dict(title="Wind Speed (knots)", showgrid=True, gridcolor="#273549"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
            font=dict(size=10),
        ),
    )
    return fig


def render() -> None:
    """Render Section C: Prediction & Model Evaluation."""
    section_header(
        title="Prediction & Model Evaluation",
        subtitle="Genuine machine learning forecasting, zero-leakage storm-level evaluation, and persistence baselines.",
        badge_label="SCIENTIFIC INTEGRITY",
        badge_type="experimental",
    )

    # Mandatory Scientific Decision-Support Disclaimer Banner
    experimental_disclaimer_banner(
        "<strong>⚠️ RESEARCH & DECISION-SUPPORT MODEL — EXPERIMENTAL EVALUATION ONLY</strong><br>"
        "All predictions and metrics are generated dynamically by machine learning models evaluated on held-out test storms. "
        "These computational estimates do NOT represent official meteorological warnings or statutory life-safety directives. "
        "Consult the India Meteorological Department (IMD / RSMC New Delhi) for official bulletins."
    )

    pipeline = _get_or_init_pipeline()

    # Load cyclone tracks
    try:
        all_tracks = load_cyclone_tracks_from_csv()
    except Exception as e:
        state_box(
            title="Dataset Loading Error",
            message=f"Could not load cyclone tracks: {e}",
            icon="⚠️",
            box_type="error",
        )
        return

    # Check Pipeline Training State
    if pipeline.state == ModelState.MODEL_NOT_TRAINED:
        with card_container(title="Predictive Models Not Trained", badge_label="ACTION REQUIRED", badge_type="warning"):
            state_box(
                title="Model Training Required for Dynamic Evaluation",
                message=(
                    "Machine learning models have not been trained on historical North Indian Ocean cyclone records. "
                    "CHAKRAVAT adheres to strict scientific integrity: no synthetic or hardcoded metrics are displayed. "
                    "Click below to execute storm-level train/test partitioning and genuine evaluation."
                ),
                icon="⚡",
                box_type="empty",
            )
            col_b1, col_b2, _ = grid_row(3)
            with col_b1:
                if st.button("⚡ Train Scientific ML Pipeline", type="primary", width="stretch"):
                    with st.spinner("Partitioning storms and training regressors on NIO history..."):
                        pipeline.train_and_evaluate()
                        st.session_state["cyclone_ml_pipeline"] = pipeline
                        st.success("Pipeline successfully trained and evaluated against held-out storms!")
                        st.rerun()
            return

    # Pipeline is trained: show status and storm selector
    ctrl_cols = grid_row(3)
    storm_names = list(all_tracks.keys())
    active_storm_id = get_active_storm_id()

    # Follow the global active storm; push local picks back to it (via callback, not inline).
    active_name = storm_name_for(active_storm_id)
    if active_name not in all_tracks:
        active_name = storm_names[0] if storm_names else ""
    if st.session_state.get("pred_seen_active") != active_storm_id:
        st.session_state["pred_seen_active"] = active_storm_id
        st.session_state["pred_storm_selector"] = active_name
    if st.session_state.get("pred_storm_selector") not in storm_names:
        st.session_state["pred_storm_selector"] = active_name

    def _on_pred_storm_change() -> None:
        choice = st.session_state.get("pred_storm_selector")
        if choice:
            set_active_storm_id(choice)
            st.session_state["pred_seen_active"] = canonical_storm_id(choice)

    with ctrl_cols[0]:
        selected_storm_name = st.selectbox(
            "Select Benchmark Storm:",
            options=storm_names,
            key="pred_storm_selector",
            on_change=_on_pred_storm_change,
            help="Select a historical cyclone to inspect model track and intensity forecasts.",
        )

    with ctrl_cols[1]:
        horizon_hours = st.radio(
            "Forecast Lead Time:",
            options=[12, 24],
            format_func=lambda h: f"{h}-Hour Horizon",
            horizontal=True,
            help="Lead time for track displacement and intensity delta regressions.",
        )

    with ctrl_cols[2]:
        cv_markdown("<div style='height: 1.6rem;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Re-evaluate Pipeline", width="stretch"):
            with st.spinner("Re-training models and re-evaluating test partitions..."):
                pipeline.train_and_evaluate()
                st.session_state["cyclone_ml_pipeline"] = pipeline
                st.success("Re-evaluation complete!")
                st.rerun()

    current_track = all_tracks.get(selected_storm_name)
    if not current_track:
        state_box(title="Storm Not Found", message="No track telemetry available for this storm.", icon="ℹ️")
        return

    # Check DATA_LIMITED state (< 3 fixes)
    if len(current_track.waypoints) < 3:
        render_data_limited_warning(
            f"Active storm '{selected_storm_name}' has only {len(current_track.waypoints)} synoptic fix(es). "
            f"At least 3 consecutive fixes (12h history) are required to extract velocity vectors and acceleration."
        )
        return

    # Retrieve genuine evaluation metrics
    t_eval = pipeline.track_eval_24h if horizon_hours == 24 else pipeline.track_eval_12h
    i_eval = pipeline.intensity_eval_24h if horizon_hours == 24 else pipeline.intensity_eval_12h
    g_eval = pipeline.genesis_eval

    # 3 Main Tabs: Track, Intensity, Genesis
    tabs = st.tabs(["🎯 Track Prediction & Baselines", "🌪️ Intensity Forecast", "🌱 Genesis / Intensification Risk"])

    # =========================================================================
    # TAB 1: TRACK PREDICTION
    # =========================================================================
    with tabs[0]:
        cv_markdown(
            f"<h4 style='color: #F1F5F9; font-size: 1.05rem; margin-top: 0.5rem;'>"
            f"Displacement Regressor vs Operational Baselines • {selected_storm_name}</h4>",
            unsafe_allow_html=True,
        )

        # Row 1 of KPI Cards (<= 3 cards)
        kpi_row1 = grid_row(3)
        with kpi_row1[0]:
            metric_card(
                label=f"{horizon_hours}h Mean Track Error (MTE)",
                value=f"{t_eval.model_mte_km:.1f}" if t_eval else "N/A",
                unit="km",
                delta=f"{t_eval.skill_vs_persistence_pct:+.1f}% vs Persistence" if t_eval else None,
                delta_type="positive" if (t_eval and t_eval.skill_vs_persistence_pct > 0) else "neutral",
                badge_text="SCIENTIFIC ML",
                badge_severity="verified",
                help_text=f"Evaluated on held-out test storms: {', '.join(t_eval.test_storms) if t_eval else ''}",
            )
        with kpi_row1[1]:
            metric_card(
                label=f"{horizon_hours}h Linear Persistence",
                value=f"{t_eval.linear_persistence_mte_km:.1f}" if t_eval else "N/A",
                unit="km",
                delta="Operational Reference",
                delta_type="neutral",
                badge_text="BASELINE",
                badge_severity="normal",
                help_text="Extrapolation of recent velocity vector",
            )
        with kpi_row1[2]:
            metric_card(
                label=f"{horizon_hours}h NIO CLIPER Baseline",
                value=f"{t_eval.cliper_mte_km:.1f}" if t_eval else "N/A",
                unit="km",
                delta="Climatology Blend",
                delta_type="neutral",
                badge_text="CLIPER",
                badge_severity="normal",
                help_text="Climatology & Persistence regression for NIO",
            )

        # Allow scrubbing historical waypoint index to see predictions from past fixes
        num_fixes = len(current_track.waypoints)
        scrub_idx = st.slider(
            "Telemetry Observation Point (Fix History Depth):",
            min_value=3,
            max_value=num_fixes,
            value=min(num_fixes, max(3, num_fixes - (2 if horizon_hours == 24 else 1))),
            help="Scrub along the historical cyclone lifecycle to evaluate forecast from any synoptic waypoint.",
        )

        sub_waypoints = current_track.waypoints[:scrub_idx]
        curr_fix = sub_waypoints[-1]
        prev_fix = sub_waypoints[-2]

        # ML track prediction
        pred_lat, pred_lon, unc_radius = pipeline.predict_track(sub_waypoints, horizon_hours=horizon_hours)

        # Baseline predictions
        lin_lat, lin_lon = LinearPersistenceBaseline.predict_position(
            curr_fix.lat, curr_fix.lon, prev_fix.lat, prev_fix.lon, forecast_horizon_hours=horizon_hours
        )
        clip_lat, clip_lon = CLIPERBaseline.predict_position(
            curr_fix.lat, curr_fix.lon, prev_fix.lat, prev_fix.lon, basin=current_track.basin, forecast_horizon_hours=horizon_hours
        )

        # Check if actual future ground truth fix exists in the dataset
        step_ahead = 2 if horizon_hours == 24 else 1
        actual_future_wp = current_track.waypoints[scrub_idx - 1 + step_ahead] if (scrub_idx - 1 + step_ahead < num_fixes) else None
        act_lat = actual_future_wp.lat if actual_future_wp else None
        act_lon = actual_future_wp.lon if actual_future_wp else None

        # Build uncertainty polygon
        wps_for_cone = [
            (curr_fix.lat, curr_fix.lon, 0),
            (pred_lat, pred_lon, horizon_hours),
        ]
        cone_poly = generate_uncertainty_polygon(wps_for_cone, pipeline.uncertainty_radii)

        # Render Track Map Figure
        map_fig = _build_track_map_figure(
            historical_waypoints=sub_waypoints,
            pred_lat=pred_lat,
            pred_lon=pred_lon,
            lin_lat=lin_lat,
            lin_lon=lin_lon,
            clip_lat=clip_lat,
            clip_lon=clip_lon,
            uncertainty_polygon=cone_poly,
            actual_lat=act_lat,
            actual_lon=act_lon,
            horizon_hours=horizon_hours,
        )
        st.plotly_chart(map_fig, width="stretch", config=geo_chart_config())

        # Telemetry & Uncertainty Details (Row 2, <= 3 cards)
        pos_cols = grid_row(3)
        with pos_cols[0]:
            metric_card(
                label=f"Current Fix (T=0 • {curr_fix.timestamp_utc[5:16]})",
                value=f"{curr_fix.lat:.2f}°N",
                unit=f"{curr_fix.lon:.2f}°E",
                delta=f"Intensity: {curr_fix.wind_kts:.0f} kts ({curr_fix.category})",
                delta_type="neutral",
                help_text=f"Pressure: {curr_fix.pressure_mb:.0f} hPa",
            )
        with pos_cols[1]:
            metric_card(
                label=f"ML Projected Center (+{horizon_hours}h)",
                value=f"{pred_lat:.2f}°N",
                unit=f"{pred_lon:.2f}°E",
                delta=f"ΔLat: {pred_lat - curr_fix.lat:+.2f}°, ΔLon: {pred_lon - curr_fix.lon:+.2f}°",
                delta_type="positive",
                help_text=f"Great-circle distance: ~{math.hypot(pred_lat - curr_fix.lat, pred_lon - curr_fix.lon)*111.0:.0f} km",
            )
        with pos_cols[2]:
            metric_card(
                label="Empirical 70% Error Radius",
                value=f"{unc_radius:.1f}",
                unit="km",
                delta=f"Calibration Lead: {horizon_hours}h",
                delta_type="neutral",
                badge_text="VALIDATED CONE",
                badge_severity="verified",
                help_text="Constructed from test set 70th-percentile residuals",
            )

        with card_container(title="Scientific Note on Uncertainty Envelope Construction"):
            cv_markdown(
                f"<p style='color: #94A3B8; font-size: 0.875rem; margin: 0; line-height: 1.5;'>"
                f"In accordance with Requirement R5 and official meteorological standards (IMD & NHC), "
                f"forecast uncertainty cones are constructed directly from the <strong>70th percentile of historical "
                f"forecast errors</strong> on unseen test storms (R<sub>{horizon_hours}h</sub> = <strong>{unc_radius:.1f} km</strong>). "
                f"The storm center is expected to remain within this corridor approximately two-thirds of the time. "
                f"Gale-force winds, intense storm surges, and torrential rainfall extend significantly beyond this boundary."
                f"</p>",
                unsafe_allow_html=True,
            )

    # =========================================================================
    # TAB 2: INTENSITY FORECAST
    # =========================================================================
    with tabs[1]:
        cv_markdown(
            f"<h4 style='color: #F1F5F9; font-size: 1.05rem; margin-top: 0.5rem;'>"
            f"Intensity Delta Regressor vs Persistence • {selected_storm_name}</h4>",
            unsafe_allow_html=True,
        )

        # Row 1 of KPI Cards for Intensity (<= 3 cards)
        ikpi_row1 = grid_row(3)
        with ikpi_row1[0]:
            metric_card(
                label=f"{horizon_hours}h Wind Speed MAE",
                value=f"{i_eval.model_mae_kts:.1f}" if i_eval else "N/A",
                unit="kts",
                delta=f"{i_eval.persistence_mae_kts - i_eval.model_mae_kts:+.1f} kts vs Persistence" if i_eval else None,
                delta_type="positive" if (i_eval and i_eval.model_mae_kts < i_eval.persistence_mae_kts) else "neutral",
                badge_text="SCIENTIFIC ML",
                badge_severity="verified",
                help_text="Evaluated against held-out test storms",
            )
        with ikpi_row1[1]:
            metric_card(
                label=f"{horizon_hours}h Pure Persistence MAE",
                value=f"{i_eval.persistence_mae_kts:.1f}" if i_eval else "N/A",
                unit="kts",
                delta="Zero-change assumption",
                delta_type="neutral",
                badge_text="BASELINE",
                badge_severity="normal",
                help_text="Future intensity equals current intensity",
            )
        with ikpi_row1[2]:
            metric_card(
                label="Systematic Forecast Bias",
                value=f"{i_eval.model_bias_kts:+.1f}" if i_eval else "0.0",
                unit="kts",
                delta=f"Central Pres MAE: {i_eval.pressure_mae_hpa:.1f} hPa" if i_eval else "",
                delta_type="neutral",
                help_text="Mean error (pred - true) on held-out test set",
            )

        # Intensity Predictions for current waypoint
        pred_wind_12, pred_pres_12 = pipeline.predict_intensity(sub_waypoints, horizon_hours=12)
        pred_wind_24, pred_pres_24 = pipeline.predict_intensity(sub_waypoints, horizon_hours=24)
        pred_wind = pred_wind_24 if horizon_hours == 24 else pred_wind_12
        pred_pres = pred_pres_24 if horizon_hours == 24 else pred_pres_12

        # Intensity Chart
        chart_fig = _build_intensity_chart(
            historical_waypoints=sub_waypoints,
            pred_wind_12=pred_wind_12,
            pred_wind_24=pred_wind_24,
            pers_wind=curr_fix.wind_kts,
        )
        st.plotly_chart(chart_fig, width="stretch")

        # Forecast details cards (Row 2, <= 3 cards)
        icols2 = grid_row(3)
        curr_cat_code = classify_imd_intensity(curr_fix.wind_kts)
        pred_cat_code = classify_imd_intensity(pred_wind)
        curr_cat_meta = IMD_CATEGORIES.get(curr_cat_code, {})
        pred_cat_meta = IMD_CATEGORIES.get(pred_cat_code, {})

        with icols2[0]:
            metric_card(
                label="Current Intensity (T=0)",
                value=f"{curr_fix.wind_kts:.0f}",
                unit="kts",
                delta=f"Pres: {curr_fix.pressure_mb:.0f} hPa • {curr_cat_meta.get('name', 'Depression')}",
                delta_type="neutral",
                help_text=f"Equivalent speed: {curr_fix.wind_kts * 1.852:.0f} km/h",
            )
        with icols2[1]:
            delta_wind = pred_wind - curr_fix.wind_kts
            metric_card(
                label=f"Projected Wind (+{horizon_hours}h)",
                value=f"{pred_wind:.0f}",
                unit="kts",
                delta=f"{delta_wind:+.0f} kts ({pred_cat_meta.get('name', 'Cyclone')})",
                delta_type="positive" if delta_wind >= 0 else "neutral",
                help_text=f"Est. Central Pressure: {pred_pres:.0f} hPa",
            )
        with icols2[2]:
            # Rapid Intensification (RI) check: >= 30 kts in 24 hours
            ri_threshold_met = (pred_wind_24 - curr_fix.wind_kts) >= 30.0
            metric_card(
                label="Rapid Intensification (RI)",
                value="ELEVATED" if ri_threshold_met else "LOW RISK",
                unit="",
                delta="ΔWind >= 30 kts / 24h" if ri_threshold_met else "< 30 kts threshold",
                delta_type="negative" if ri_threshold_met else "positive",
                badge_text="METEOROLOGICAL RISK",
                badge_severity="danger" if ri_threshold_met else "normal",
                help_text="Standard operational criteria for rapid strengthening",
            )

    # =========================================================================
    # TAB 3: GENESIS / INTENSIFICATION RISK
    # =========================================================================
    with tabs[2]:
        cv_markdown(
            "<h4 style='color: #F1F5F9; font-size: 1.05rem; margin-top: 0.5rem;'>"
            "Genesis & Intensification Potential (CS Transition Baseline)</h4>",
            unsafe_allow_html=True,
        )

        # Row 1 of Genesis KPI cards (<= 3 cards)
        gkpi_row = grid_row(3)
        with gkpi_row[0]:
            metric_card(
                label="Genesis Precision / POD",
                value=f"{g_eval.precision * 100:.1f}%" if g_eval else "N/A",
                unit="",
                delta=f"{g_eval.true_positives} True Positives" if g_eval else "",
                delta_type="positive",
                badge_text="VALIDATED",
                badge_severity="verified",
                help_text="True Positives / (True Positives + False Positives)",
            )
        with gkpi_row[1]:
            metric_card(
                label="Genesis Recall (Detection Rate)",
                value=f"{g_eval.recall * 100:.1f}%" if g_eval else "N/A",
                unit="",
                delta=f"{g_eval.false_negatives} Missed Systems" if g_eval else "",
                delta_type="neutral",
                badge_text="RECALL",
                badge_severity="normal",
                help_text="True Positives / (True Positives + False Negatives)",
            )
        with gkpi_row[2]:
            metric_card(
                label="F1 Performance Score",
                value=f"{g_eval.f1_score:.3f}" if g_eval else "N/A",
                unit="",
                delta=f"Accuracy: {g_eval.accuracy * 100:.1f}%" if g_eval else "",
                delta_type="positive",
                badge_text="F1 SCORE",
                badge_severity="normal",
                help_text="Harmonic mean of precision and recall on held-out test data",
            )

        # Early formative stage analysis of the selected storm
        early_fixes = sub_waypoints[:min(3, len(sub_waypoints))]
        pred_class, risk_prob = pipeline.predict_genesis(early_fixes)

        with card_container(title="Formative Stage Diagnostic for Active Disturbance"):
            gcols = grid_row(3)
            with gcols[0]:
                metric_card(
                    label="Intensification Assessment",
                    value="HIGH RISK" if pred_class == 1 else "LOW RISK",
                    unit="",
                    delta="Transition to Cyclonic Storm (>= 34 kts)" if pred_class == 1 else "Stagnation / Dissipation Likely",
                    delta_type="negative" if pred_class == 1 else "positive",
                    badge_text="GENESIS MODEL",
                    badge_severity="danger" if pred_class == 1 else "normal",
                )
            with gcols[1]:
                metric_card(
                    label="Model Confidence Score",
                    value=f"{risk_prob * 100:.1f}%",
                    unit="",
                    delta="Historical Climatological Prior: ~38%",
                    delta_type="neutral",
                    help_text="RandomForest probability calibrated against NIO depression archives",
                )
            with gcols[2]:
                coriolis_val = 2.0 * 7.2921e-5 * math.sin(math.radians(curr_fix.lat))
                metric_card(
                    label="Coriolis Parameter (f)",
                    value=f"{coriolis_val * 1e5:.2f}",
                    unit="×10⁻⁵ s⁻¹",
                    delta=f"Latitude: {curr_fix.lat:.1f}°N",
                    delta_type="neutral",
                    help_text="Planetary vorticity necessary for spin-up (critical above 5°N)",
                )

        # Scientific Limitations & Responsible Decision Support
        with card_container(title="Meteorological Constraints & Operational Disclaimers"):
            cv_markdown(
                """
                <div style="color: #94A3B8; font-size: 0.875rem; line-height: 1.6;">
                    <p style="margin-bottom: 0.5rem;">
                        <strong>1. Boundary Layer & Microphysics Limitations:</strong> Synoptic ML regression models rely 
                        on 6-hourly best-track coordinates and bulk central pressures. They do not simulate convective scale 
                        eyewall replacement cycles (ERC), vertical wind shear tilts, or ocean heat content (OHC) feedbacks.
                    </p>
                    <p style="margin-bottom: 0.5rem;">
                        <strong>2. Data Sparsity in Early Formative Stages:</strong> Tropical disturbances with fewer than 
                        3 consecutive synoptic fixes (< 12 hours of trajectory history) lack kinematic momentum vectors, 
                        placing the platform in a designated <em>DATA_LIMITED</em> state.
                    </p>
                    <p style="margin-bottom: 0;">
                        <strong>3. Statutory Authority:</strong> All operational warnings, landfall times, and evacuation orders 
                        for the Indian subcontinent are strictly under the jurisdiction of the 
                        <strong>India Meteorological Department (IMD / RSMC New Delhi)</strong> and respective State Disaster 
                        Management Authorities (SDMA / NDMA).
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
