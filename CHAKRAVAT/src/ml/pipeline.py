"""End-to-End Scientific Machine Learning Pipeline Coordinator for CHAKRAVAT.

Coordinates:
1. Data loading and ingestion of North Indian Ocean cyclone records.
2. Zero-leakage storm-level train/test partitioning.
3. Training of track displacement, intensity delta, and genesis models.
4. Evaluation of ML models alongside Linear Persistence & CLIPER baselines on held-out test storms.
5. Real dynamic evaluation metrics (Haversine MTE in km, MAE in kts, Precision/Recall).
6. Empirical 70th-percentile uncertainty cone estimation.
7. Fallback state management (MODEL_NOT_TRAINED, DATA_LIMITED, READY).
"""

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import os
import pandas as pd

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
from src.ml.models import (
    TrackDeltaRegressor,
    IntensityDeltaRegressor,
    GenesisClassifier,
    _get_val,
)
from src.ml.evaluation import (
    haversine_distance_km,
    compute_track_mte_km,
    compute_intensity_mae,
    compute_bias,
    compute_genesis_metrics,
    TrackEvaluation,
    IntensityEvaluation,
    GenesisEvaluation,
)
from src.ml.uncertainty import (
    calculate_uncertainty_cone_radii,
    generate_uncertainty_polygon,
)


class ModelState(str, Enum):
    MODEL_NOT_TRAINED = "MODEL_NOT_TRAINED"
    DATA_LIMITED = "DATA_LIMITED"
    READY = "READY"


DEFAULT_DATA_PATH = Path("c:/Users/pc/OneDrive/Desktop/CHAKRAVAT/data/nio_cyclones_sample.csv")


class CycloneMLPipeline:
    """Coordinator for North Indian Ocean cyclone predictive modeling and evaluation."""

    def __init__(self, data_path: Optional[Union[str, Path]] = None):
        self.data_path = Path(data_path) if data_path else DEFAULT_DATA_PATH
        self.state: ModelState = ModelState.MODEL_NOT_TRAINED

        self.track_model = TrackDeltaRegressor(random_state=42)
        self.intensity_model = IntensityDeltaRegressor(random_state=42)
        self.genesis_model = GenesisClassifier(random_state=42)

        # Evaluation results cache
        self.track_eval_12h: Optional[TrackEvaluation] = None
        self.track_eval_24h: Optional[TrackEvaluation] = None
        self.intensity_eval_12h: Optional[IntensityEvaluation] = None
        self.intensity_eval_24h: Optional[IntensityEvaluation] = None
        self.genesis_eval: Optional[GenesisEvaluation] = None
        self.uncertainty_radii: Dict[int, float] = {0: 15.0, 12: 65.0, 24: 125.0}

        self.train_storms: List[str] = []
        self.test_storms: List[str] = []
        self._raw_df: Optional[pd.DataFrame] = None

    def load_data(self) -> pd.DataFrame:
        """Load and cache the cyclone dataset."""
        if self._raw_df is not None:
            return self._raw_df

        if not self.data_path.exists():
            # Try fallback relative path
            fallback = Path("data/nio_cyclones_sample.csv")
            if fallback.exists():
                self.data_path = fallback
            else:
                raise FileNotFoundError(f"Cyclone dataset not found at {self.data_path}")

        df = pd.read_csv(self.data_path)
        self._raw_df = df
        return df

    def train_and_evaluate(
        self,
        df: Optional[pd.DataFrame] = None,
        test_storm_names: Optional[List[str]] = None,
    ) -> Tuple[TrackEvaluation, IntensityEvaluation, Dict[str, Any]]:
        """Train models on train storms, evaluate on held-out test storms, and cache genuine metrics."""
        if df is None:
            df = self.load_data()

        storm_col = resolve_storm_identifier_col(df)
        train_df, test_df = storm_level_split(df, test_storm_names)

        self.train_storms = train_df[storm_col].astype(str).unique().tolist()
        self.test_storms = test_df[storm_col].astype(str).unique().tolist()

        # 1. Fit ML models on train partition
        self.track_model.fit(train_df, storm_col=storm_col)
        self.intensity_model.fit(train_df, storm_col=storm_col)
        self.genesis_model.fit(train_df, storm_col=storm_col)

        # 2. Evaluate dynamically on test partition
        (
            self.track_eval_12h,
            self.track_eval_24h,
            self.intensity_eval_12h,
            self.intensity_eval_24h,
            self.genesis_eval,
        ) = self._evaluate_on_test_storms(test_df, storm_col)

        # 3. Compute empirical 70% error radii from actual validation residuals
        res_12 = self.track_eval_12h.error_residuals_km if self.track_eval_12h else []
        res_24 = self.track_eval_24h.error_residuals_km if self.track_eval_24h else []
        self.uncertainty_radii = calculate_uncertainty_cone_radii(res_12, res_24)

        self.state = ModelState.READY

        extra_metrics = {
            "track_12h": self.track_eval_12h,
            "track_24h": self.track_eval_24h,
            "intensity_12h": self.intensity_eval_12h,
            "intensity_24h": self.intensity_eval_24h,
            "genesis": self.genesis_eval,
            "uncertainty_radii": self.uncertainty_radii,
            "train_storms": self.train_storms,
            "test_storms": self.test_storms,
        }

        return self.track_eval_24h, self.intensity_eval_24h, extra_metrics

    def _evaluate_on_test_storms(
        self,
        test_df: pd.DataFrame,
        storm_col: str,
    ) -> Tuple[
        TrackEvaluation,
        TrackEvaluation,
        IntensityEvaluation,
        IntensityEvaluation,
        GenesisEvaluation,
    ]:
        """Compute genuine dynamic evaluation metrics against unseen test storms."""
        # Track metric collectors
        actual_coords_12, ml_coords_12, lin_coords_12, cliper_coords_12 = [], [], [], []
        actual_coords_24, ml_coords_24, lin_coords_24, cliper_coords_24 = [], [], [], []

        # Intensity metric collectors
        actual_wind_12, ml_wind_12, pers_wind_12 = [], [], []
        actual_wind_24, ml_wind_24, pers_wind_24 = [], [], []
        actual_pres_12, ml_pres_12 = [], []
        actual_pres_24, ml_pres_24 = [], []

        # Genesis classification collectors
        genesis_y_true, genesis_y_pred = [], []

        for _, group in test_df.groupby(storm_col):
            records = group.to_dict("records")
            n = len(records)
            if n < 3:
                continue

            basin = str(_get_val(records[0], "basin", default="BOB"))

            # Genesis evaluation: did this test storm reach CS (>= 34 kts)?
            max_wind = max(float(_get_val(r, "wind_kts", "wind_speed_kts", default=0)) for r in records)
            actual_cs = 1 if max_wind >= 34.0 else 0
            pred_class, _ = self.genesis_model.predict_risk(records[0])
            genesis_y_true.append(actual_cs)
            genesis_y_pred.append(pred_class)

            for i in range(2, n):
                window = records[: i + 1]
                curr_lat = float(_get_val(records[i], "lat", "latitude"))
                curr_lon = float(_get_val(records[i], "lon", "longitude"))
                curr_wind = float(_get_val(records[i], "wind_kts", "wind_speed_kts"))
                curr_pres = float(_get_val(records[i], "pressure_mb", "central_pressure_hpa"))

                past_lat = float(_get_val(records[i - 1], "lat", "latitude"))
                past_lon = float(_get_val(records[i - 1], "lon", "longitude"))

                # 12-hour evaluation point (index i + 1)
                if i + 1 < n:
                    act_lat_12 = float(_get_val(records[i + 1], "lat", "latitude"))
                    act_lon_12 = float(_get_val(records[i + 1], "lon", "longitude"))
                    act_wind_12 = float(_get_val(records[i + 1], "wind_kts", "wind_speed_kts"))
                    act_pres_12 = float(_get_val(records[i + 1], "pressure_mb", "central_pressure_hpa"))

                    # ML predictions
                    dlat_12, dlon_12 = self.track_model.predict(window, horizon_hours=12)
                    dwind_12, dpres_12 = self.intensity_model.predict(window, horizon_hours=12)

                    # Baselines
                    lin_lat_12, lin_lon_12 = LinearPersistenceBaseline.predict_position(
                        curr_lat, curr_lon, past_lat, past_lon, forecast_horizon_hours=12
                    )
                    clip_lat_12, clip_lon_12 = CLIPERBaseline.predict_position(
                        curr_lat, curr_lon, past_lat, past_lon, basin=basin, forecast_horizon_hours=12
                    )
                    pers_w_12, _ = IntensityPersistenceBaseline.predict_pure_persistence(curr_wind, curr_pres)

                    actual_coords_12.append((act_lat_12, act_lon_12))
                    ml_coords_12.append((curr_lat + dlat_12, curr_lon + dlon_12))
                    lin_coords_12.append((lin_lat_12, lin_lon_12))
                    cliper_coords_12.append((clip_lat_12, clip_lon_12))

                    actual_wind_12.append(act_wind_12)
                    ml_wind_12.append(curr_wind + dwind_12)
                    pers_wind_12.append(pers_w_12)
                    actual_pres_12.append(act_pres_12)
                    ml_pres_12.append(curr_pres + dpres_12)

                # 24-hour evaluation point (index i + 2)
                if i + 2 < n:
                    act_lat_24 = float(_get_val(records[i + 2], "lat", "latitude"))
                    act_lon_24 = float(_get_val(records[i + 2], "lon", "longitude"))
                    act_wind_24 = float(_get_val(records[i + 2], "wind_kts", "wind_speed_kts"))
                    act_pres_24 = float(_get_val(records[i + 2], "pressure_mb", "central_pressure_hpa"))

                    # ML predictions
                    dlat_24, dlon_24 = self.track_model.predict(window, horizon_hours=24)
                    dwind_24, dpres_24 = self.intensity_model.predict(window, horizon_hours=24)

                    # Baselines
                    lin_lat_24, lin_lon_24 = LinearPersistenceBaseline.predict_position(
                        curr_lat, curr_lon, past_lat, past_lon, forecast_horizon_hours=24
                    )
                    clip_lat_24, clip_lon_24 = CLIPERBaseline.predict_position(
                        curr_lat, curr_lon, past_lat, past_lon, basin=basin, forecast_horizon_hours=24
                    )
                    pers_w_24, _ = IntensityPersistenceBaseline.predict_pure_persistence(curr_wind, curr_pres)

                    actual_coords_24.append((act_lat_24, act_lon_24))
                    ml_coords_24.append((curr_lat + dlat_24, curr_lon + dlon_24))
                    lin_coords_24.append((lin_lat_24, lin_lon_24))
                    cliper_coords_24.append((clip_lat_24, clip_lon_24))

                    actual_wind_24.append(act_wind_24)
                    ml_wind_24.append(curr_wind + dwind_24)
                    pers_wind_24.append(pers_w_24)
                    actual_pres_24.append(act_pres_24)
                    ml_pres_24.append(curr_pres + dpres_24)

        # Compute genuine track metrics
        def _build_track_eval(horizon, act, ml, lin, clip):
            n_pts = len(act)
            if n_pts == 0:
                return TrackEvaluation(
                    horizon_hours=horizon,
                    test_storms=self.test_storms,
                    model_mte_km=0.0,
                    linear_persistence_mte_km=0.0,
                    cliper_mte_km=0.0,
                    skill_vs_persistence_pct=0.0,
                    num_eval_points=0,
                    error_residuals_km=[],
                )
            mte_ml = compute_track_mte_km(act, ml)
            mte_lin = compute_track_mte_km(act, lin)
            mte_clip = compute_track_mte_km(act, clip)
            skill = round(100.0 * (mte_lin - mte_ml) / max(1e-3, mte_lin), 1)
            residuals = [haversine_distance_km(a[0], a[1], m[0], m[1]) for a, m in zip(act, ml)]
            return TrackEvaluation(
                horizon_hours=horizon,
                test_storms=self.test_storms,
                model_mte_km=round(mte_ml, 1),
                linear_persistence_mte_km=round(mte_lin, 1),
                cliper_mte_km=round(mte_clip, 1),
                skill_vs_persistence_pct=skill,
                num_eval_points=n_pts,
                error_residuals_km=residuals,
            )

        track_12 = _build_track_eval(12, actual_coords_12, ml_coords_12, lin_coords_12, cliper_coords_12)
        track_24 = _build_track_eval(24, actual_coords_24, ml_coords_24, lin_coords_24, cliper_coords_24)

        # Compute genuine intensity metrics
        def _build_intensity_eval(horizon, act_w, ml_w, pers_w, act_p, ml_p):
            n_pts = len(act_w)
            if n_pts == 0:
                return IntensityEvaluation(
                    horizon_hours=horizon,
                    test_storms=self.test_storms,
                    model_mae_kts=0.0,
                    persistence_mae_kts=0.0,
                    model_bias_kts=0.0,
                    pressure_mae_hpa=0.0,
                    num_eval_points=0,
                )
            mae_w = compute_intensity_mae(act_w, ml_w)
            mae_pers = compute_intensity_mae(act_w, pers_w)
            bias_w = compute_bias(act_w, ml_w)
            mae_p = compute_intensity_mae(act_p, ml_p)
            return IntensityEvaluation(
                horizon_hours=horizon,
                test_storms=self.test_storms,
                model_mae_kts=round(mae_w, 1),
                persistence_mae_kts=round(mae_pers, 1),
                model_bias_kts=round(bias_w, 1),
                pressure_mae_hpa=round(mae_p, 1),
                num_eval_points=n_pts,
            )

        intensity_12 = _build_intensity_eval(12, actual_wind_12, ml_wind_12, pers_wind_12, actual_pres_12, ml_pres_12)
        intensity_24 = _build_intensity_eval(24, actual_wind_24, ml_wind_24, pers_wind_24, actual_pres_24, ml_pres_24)

        genesis_eval = compute_genesis_metrics(genesis_y_true, genesis_y_pred, self.test_storms)

        return track_12, track_24, intensity_12, intensity_24, genesis_eval

    def predict_track(
        self,
        storm_history: List[Any],
        horizon_hours: int = 24,
    ) -> Tuple[float, float, float]:
        """Predict future (latitude, longitude, uncertainty_radius_km).

        Returns: (pred_lat, pred_lon, radius_km)
        """
        if self.state == ModelState.MODEL_NOT_TRAINED:
            raise RuntimeError("ModelNotTrained: Execute train_and_evaluate() first.")

        if len(storm_history) < 3:
            raise ValueError(f"DATA_LIMITED: Need >= 3 observations to compute velocity and predict. Got {len(storm_history)}.")

        curr = storm_history[-1]
        curr_lat = float(_get_val(curr, "lat", "latitude"))
        curr_lon = float(_get_val(curr, "lon", "longitude"))

        dlat, dlon = self.track_model.predict(storm_history, horizon_hours=horizon_hours)
        pred_lat = curr_lat + dlat
        pred_lon = curr_lon + dlon

        # Select corresponding defensible uncertainty radius
        radius_km = self.uncertainty_radii.get(horizon_hours, self.uncertainty_radii.get(24, 125.0))

        return float(round(pred_lat, 2)), float(round(pred_lon, 2)), float(radius_km)

    def predict_intensity(
        self,
        storm_history: List[Any],
        horizon_hours: int = 24,
    ) -> Tuple[float, float]:
        """Predict future (wind_speed_kts, central_pressure_hpa)."""
        if self.state == ModelState.MODEL_NOT_TRAINED:
            raise RuntimeError("ModelNotTrained: Execute train_and_evaluate() first.")

        if len(storm_history) < 3:
            raise ValueError(f"DATA_LIMITED: Need >= 3 observations. Got {len(storm_history)}.")

        curr = storm_history[-1]
        curr_wind = float(_get_val(curr, "wind_kts", "wind_speed_kts"))
        curr_pres = float(_get_val(curr, "pressure_mb", "central_pressure_hpa"))

        dwind, dpres = self.intensity_model.predict(storm_history, horizon_hours=horizon_hours)
        pred_wind = max(15.0, min(165.0, curr_wind + dwind))
        pred_pres = max(880.0, min(1020.0, curr_pres + dpres))

        return float(round(pred_wind, 1)), float(round(pred_pres, 1))

    def predict_genesis(self, early_fixes: List[Any]) -> Tuple[int, float]:
        """Predict intensification class (0 or 1) and probability [0.0, 1.0]."""
        if not early_fixes:
            return 0, 0.38
        latest = early_fixes[-1]
        prev = early_fixes[-2] if len(early_fixes) >= 2 else None
        return self.genesis_model.predict_risk(latest, prev)


# Global singleton instance for Streamlit session reuse
_PIPELINE_INSTANCE: Optional[CycloneMLPipeline] = None


def get_ml_pipeline(auto_train: bool = True) -> CycloneMLPipeline:
    """Retrieve or create the shared CycloneMLPipeline singleton.
    
    If auto_train is True, trains and evaluates the models on historical records
    immediately so prediction views are instantly active with real metrics.
    """
    global _PIPELINE_INSTANCE
    if _PIPELINE_INSTANCE is None:
        _PIPELINE_INSTANCE = CycloneMLPipeline()
        if auto_train:
            try:
                _PIPELINE_INSTANCE.train_and_evaluate()
            except Exception:
                pass
    return _PIPELINE_INSTANCE
