"""Scientific Machine Learning & Evaluation Package for CHAKRAVAT.

Focus: North Indian Ocean (NIO) cyclone track & intensity prediction,
strict storm-level validation, verified baselines, and defensible uncertainty.
"""

from src.ml.split import storm_level_split, get_default_train_test_storms
from src.ml.baselines import (
    LinearPersistenceBaseline,
    CLIPERBaseline,
    IntensityPersistenceBaseline,
)
from src.ml.evaluation import (
    haversine_distance_km,
    compute_track_mte_km,
    compute_intensity_mae,
    compute_genesis_metrics,
    TrackEvaluation,
    IntensityEvaluation,
    GenesisEvaluation,
)
from src.ml.uncertainty import calculate_uncertainty_cone_radii, generate_uncertainty_polygon
from src.ml.models import (
    TrackDeltaRegressor,
    IntensityDeltaRegressor,
    GenesisClassifier,
)
from src.ml.pipeline import CycloneMLPipeline, ModelState

__all__ = [
    "storm_level_split",
    "get_default_train_test_storms",
    "LinearPersistenceBaseline",
    "CLIPERBaseline",
    "IntensityPersistenceBaseline",
    "haversine_distance_km",
    "compute_track_mte_km",
    "compute_intensity_mae",
    "compute_genesis_metrics",
    "TrackEvaluation",
    "IntensityEvaluation",
    "GenesisEvaluation",
    "calculate_uncertainty_cone_radii",
    "generate_uncertainty_polygon",
    "TrackDeltaRegressor",
    "IntensityDeltaRegressor",
    "GenesisClassifier",
    "CycloneMLPipeline",
    "ModelState",
]
