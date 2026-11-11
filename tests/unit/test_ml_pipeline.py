"""Unit and Integration Tests for Scientific ML Pipeline and Evaluation.

Covers:
- Storm-level train/test split zero-leakage guarantee
- Linear Persistence, CLIPER, and Intensity baselines
- Haversine MTE, MAE, and Genesis classification metrics
- Empirical uncertainty cone construction
- End-to-end CycloneMLPipeline train, evaluate, and predict workflows
- Fallback states (MODEL_NOT_TRAINED, DATA_LIMITED)
"""

import math
import pytest
import pandas as pd
from pathlib import Path

from src.ml.split import (
    storm_level_split,
    get_default_train_test_storms,
    resolve_storm_identifier_col,
)
from src.ml.baselines import (
    LinearPersistenceBaseline,
    CLIPERBaseline,
    IntensityPersistenceBaseline,
)
from src.ml.evaluation import (
    haversine_distance_km,
    compute_track_mte_km,
    compute_intensity_mae,
    compute_bias,
    compute_genesis_metrics,
)
from src.ml.uncertainty import (
    calculate_uncertainty_cone_radii,
    calculate_empirical_70th_percentile,
    generate_uncertainty_polygon,
    km_to_deg,
)
from src.ml.models import (
    TrackDeltaRegressor,
    IntensityDeltaRegressor,
    GenesisClassifier,
)
from src.ml.pipeline import (
    CycloneMLPipeline,
    ModelState,
    get_ml_pipeline,
)
from src.ui.state import init_session_state, set_active_storm_id
from src.views.section_prediction import render as render_section_prediction


@pytest.fixture
def sample_csv_path() -> Path:
    p = Path("c:/Users/pc/OneDrive/Desktop/CHAKRAVAT/data/nio_cyclones_sample.csv")
    if not p.exists():
        p = Path("data/nio_cyclones_sample.csv")
    return p


@pytest.fixture
def sample_df(sample_csv_path: Path) -> pd.DataFrame:
    return pd.read_csv(sample_csv_path)


# =============================================================================
# 1. Storm-Level Split Tests
# =============================================================================

def test_storm_level_split_strict_disjointness(sample_df: pd.DataFrame):
    """Verify that all observations of any storm remain exclusively in train or test."""
    train_df, test_df = storm_level_split(sample_df)

    assert not train_df.empty
    assert not test_df.empty
    assert len(train_df) + len(test_df) == len(sample_df)

    storm_col = resolve_storm_identifier_col(sample_df)
    train_storms = set(train_df[storm_col].unique())
    test_storms = set(test_df[storm_col].unique())

    # Mathematical assertion: disjoint sets
    assert train_storms.isdisjoint(test_storms), (
        f"Data leakage detected! Overlap: {train_storms.intersection(test_storms)}"
    )


def test_storm_level_split_custom_test_storms(sample_df: pd.DataFrame):
    """Verify splitting with explicit test storm names."""
    custom_test = ["FANI"]
    train_df, test_df = storm_level_split(sample_df, test_storm_names=custom_test)

    storm_col = resolve_storm_identifier_col(sample_df)
    assert set(test_df[storm_col].unique()) == {"FANI"}
    assert "FANI" not in set(train_df[storm_col].unique())


# =============================================================================
# 2. Baselines Tests
# =============================================================================

def test_linear_persistence_baseline():
    """Verify linear velocity extrapolation."""
    # Moving north at 1 deg / 6 hours = 0.1667 deg/hr
    v_lat, v_lon = LinearPersistenceBaseline.compute_velocity(
        lat_t0=10.0, lon_t0=80.0, lat_t1=11.0, lon_t1=80.0, dt_hours=6.0
    )
    assert math.isclose(v_lat, 1.0 / 6.0, rel_tol=1e-3)
    assert math.isclose(v_lon, 0.0, abs_tol=1e-5)

    pred_lat, pred_lon = LinearPersistenceBaseline.predict_position(
        current_lat=11.0,
        current_lon=80.0,
        past_lat=10.0,
        past_lon=80.0,
        forecast_horizon_hours=24,
    )
    # 11.0 + (1.0/6.0) * 24 = 15.0
    assert math.isclose(pred_lat, 15.0, rel_tol=1e-3)
    assert math.isclose(pred_lon, 80.0, abs_tol=1e-5)


def test_cliper_baseline_blending():
    """Verify CLIPER blends linear persistence with climatological drift."""
    pred_lat, pred_lon = CLIPERBaseline.predict_position(
        current_lat=12.0,
        current_lon=85.0,
        past_lat=11.0,
        past_lon=85.0,
        basin="BOB",
        forecast_horizon_hours=24,
    )
    # CLIPER blends persistence with NIO climatology, should be in northern/NW sector
    assert pred_lat > 12.0
    assert 75.0 <= pred_lon <= 95.0


def test_intensity_persistence_baselines():
    """Verify pure and damped trend persistence."""
    # Pure persistence
    p_w, p_p = IntensityPersistenceBaseline.predict_pure_persistence(75.0, 970.0)
    assert p_w == 75.0
    assert p_p == 970.0

    # Trend persistence (intensifying by 10 kts over 6h)
    tr_w, tr_p = IntensityPersistenceBaseline.predict_trend_persistence(
        current_wind_kts=75.0,
        past_wind_kts=65.0,
        current_pressure_hpa=970.0,
        past_pressure_hpa=980.0,
        forecast_horizon_hours=12,
    )
    assert tr_w > 75.0
    assert tr_p < 970.0


# =============================================================================
# 3. Dynamic Evaluation Metrics Tests
# =============================================================================

def test_haversine_distance():
    """Verify great-circle distance calculation."""
    # Same point -> 0 km
    assert haversine_distance_km(15.0, 80.0, 15.0, 80.0) == 0.0

    # 1 degree of latitude on Earth is approx 111 km
    d = haversine_distance_km(0.0, 80.0, 1.0, 80.0)
    assert math.isclose(d, 111.19, rel_tol=1e-2)

    # Compute MTE across pairs
    y_true = [(10.0, 80.0), (12.0, 82.0)]
    y_pred = [(10.0, 80.0), (12.0, 82.0)]
    assert compute_track_mte_km(y_true, y_pred) == 0.0


def test_intensity_metrics():
    """Verify MAE and Bias calculations."""
    true_w = [50.0, 60.0, 70.0]
    pred_w = [55.0, 58.0, 68.0]
    mae = compute_intensity_mae(true_w, pred_w)
    # (|5| + | -2| + | -2|) / 3 = 9 / 3 = 3.0
    assert math.isclose(mae, 3.0, rel_tol=1e-3)

    bias = compute_bias(true_w, pred_w)
    # (5 - 2 - 2) / 3 = 1 / 3 = 0.333
    assert math.isclose(bias, 1.0 / 3.0, rel_tol=1e-2)


def test_genesis_classification_metrics():
    """Verify Precision, Recall, F1 from dynamic confusion matrix."""
    y_true = [1, 1, 0, 0]
    y_pred = [1, 0, 0, 1]
    # TP=1, FN=1, TN=1, FP=1
    g = compute_genesis_metrics(y_true, y_pred, test_storms=["YAAS"])
    assert g.true_positives == 1
    assert g.false_negatives == 1
    assert g.false_positives == 1
    assert g.true_negatives == 1
    assert math.isclose(g.precision, 0.5, rel_tol=1e-2)
    assert math.isclose(g.recall, 0.5, rel_tol=1e-2)
    assert math.isclose(g.f1_score, 0.5, rel_tol=1e-2)


# =============================================================================
# 4. Uncertainty Cone Tests
# =============================================================================

def test_uncertainty_cone_radii():
    """Verify defensible 70th-percentile error calculation."""
    residuals_12 = [30.0, 40.0, 50.0, 60.0, 70.0, 80.0]
    residuals_24 = [70.0, 90.0, 110.0, 130.0, 150.0, 170.0]

    radii = calculate_uncertainty_cone_radii(residuals_12, residuals_24)
    assert radii[0] == 15.0
    assert 40.0 <= radii[12] <= 90.0
    assert 90.0 <= radii[24] <= 180.0


def test_uncertainty_polygon_generation():
    """Verify closed polygon geometry around waypoints."""
    waypoints = [(15.0, 85.0, 0), (17.0, 86.0, 12), (19.0, 87.0, 24)]
    radii = {0: 15.0, 12: 65.0, 24: 125.0}

    poly = generate_uncertainty_polygon(waypoints, radii)
    assert len(poly) >= 6
    # Polygon must be closed (first == last)
    assert poly[0] == poly[-1]


# =============================================================================
# 5. ML Pipeline End-to-End Tests
# =============================================================================

def test_ml_pipeline_train_and_evaluate(sample_csv_path: Path):
    """Test full pipeline execution, state transitions, and inference."""
    pipeline = CycloneMLPipeline(data_path=sample_csv_path)
    assert pipeline.state == ModelState.MODEL_NOT_TRAINED

    # Must raise error if predict called before training
    dummy_history = [{"lat": 10.0, "lon": 80.0, "wind_kts": 35.0, "pressure_mb": 1000.0}] * 3
    with pytest.raises(RuntimeError):
        pipeline.predict_track(dummy_history)

    # Train and evaluate
    t24, i24, extra = pipeline.train_and_evaluate()

    assert pipeline.state == ModelState.READY
    assert t24 is not None
    assert i24 is not None
    assert t24.num_eval_points > 0
    assert t24.model_mte_km > 0.0
    assert i24.num_eval_points > 0
    assert i24.model_mae_kts > 0.0

    # Ensure train and test storms are disjoint
    train_storms = set(extra["train_storms"])
    test_storms = set(extra["test_storms"])
    assert train_storms.isdisjoint(test_storms)

    # Test predict_track
    pred_lat, pred_lon, unc_r = pipeline.predict_track(dummy_history, horizon_hours=24)
    assert isinstance(pred_lat, float)
    assert isinstance(pred_lon, float)
    assert unc_r > 0.0

    # Test DATA_LIMITED state check (< 3 fixes)
    short_history = dummy_history[:2]
    with pytest.raises(ValueError, match="DATA_LIMITED"):
        pipeline.predict_track(short_history)


# =============================================================================
# 6. Section C UI View Smoke Test
# =============================================================================

def test_section_prediction_render_smoke():
    """Verify Section C view renders cleanly without runtime exceptions."""
    init_session_state(force_reset=True)
    # Pipeline will auto-train or render clean state box
    render_section_prediction()
