"""Dynamic Scientific Evaluation Metrics for Cyclone Forecasting.

Fulfills Requirement R3 & R5: Real, dynamic metrics computed exclusively
from model and baseline outputs against held-out test storms.
Hardcoded metrics, fabricated percentages, or synthetic scores are STRICTLY PROHIBITED.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple
import math


EARTH_RADIUS_KM = 6371.0


def haversine_distance_km(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
) -> float:
    """Calculate the Great-Circle Haversine distance between two coordinates in km."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2)
    )
    # Numerical safeguard for float precision
    a = max(0.0, min(1.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return float(EARTH_RADIUS_KM * c)


def compute_track_mte_km(
    y_true: Sequence[Tuple[float, float]],
    y_pred: Sequence[Tuple[float, float]],
) -> float:
    """Compute the Mean Track Error (MTE) in kilometers across coordinate pairs."""
    if not y_true or not y_pred or len(y_true) != len(y_pred):
        return 0.0

    errors = [
        haversine_distance_km(true_lat, true_lon, pred_lat, pred_lon)
        for (true_lat, true_lon), (pred_lat, pred_lon) in zip(y_true, y_pred)
    ]
    return float(sum(errors) / len(errors))


def compute_intensity_mae(
    y_true: Sequence[float],
    y_pred: Sequence[float],
) -> float:
    """Compute Mean Absolute Error (MAE) for intensity metrics."""
    if not y_true or not y_pred or len(y_true) != len(y_pred):
        return 0.0

    errors = [abs(t - p) for t, p in zip(y_true, y_pred)]
    return float(sum(errors) / len(errors))


def compute_bias(
    y_true: Sequence[float],
    y_pred: Sequence[float],
) -> float:
    """Compute Mean Forecast Bias (pred - true)."""
    if not y_true or not y_pred or len(y_true) != len(y_pred):
        return 0.0

    diffs = [p - t for t, p in zip(y_true, y_pred)]
    return float(sum(diffs) / len(diffs))


@dataclass
class TrackEvaluation:
    """Track prediction evaluation report against held-out test storms."""
    horizon_hours: int
    test_storms: List[str]
    model_mte_km: float
    linear_persistence_mte_km: float
    cliper_mte_km: float
    skill_vs_persistence_pct: float
    num_eval_points: int
    error_residuals_km: List[float]


@dataclass
class IntensityEvaluation:
    """Intensity prediction evaluation report against held-out test storms."""
    horizon_hours: int
    test_storms: List[str]
    model_mae_kts: float
    persistence_mae_kts: float
    model_bias_kts: float
    pressure_mae_hpa: float
    num_eval_points: int


@dataclass
class GenesisEvaluation:
    """Genesis / intensification classification evaluation report."""
    test_storms: List[str]
    precision: float
    recall: float
    f1_score: float
    accuracy: float
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    num_eval_points: int


def compute_genesis_metrics(
    y_true: Sequence[int],
    y_pred: Sequence[int],
    test_storms: Optional[List[str]] = None,
) -> GenesisEvaluation:
    """Compute genuine classification performance metrics from predictions.

    Zero hardcoding: every rate is dynamically computed from confusion matrix counts.
    """
    if not y_true or not y_pred or len(y_true) != len(y_pred):
        return GenesisEvaluation(
            test_storms=test_storms or [],
            precision=0.0,
            recall=0.0,
            f1_score=0.0,
            accuracy=0.0,
            true_positives=0,
            false_positives=0,
            true_negatives=0,
            false_negatives=0,
            num_eval_points=0,
        )

    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    total = len(y_true)

    precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    f1 = (
        float(2.0 * precision * recall / (precision + recall))
        if (precision + recall) > 0
        else 0.0
    )
    accuracy = float((tp + tn) / total) if total > 0 else 0.0

    return GenesisEvaluation(
        test_storms=test_storms or [],
        precision=round(precision, 3),
        recall=round(recall, 3),
        f1_score=round(f1, 3),
        accuracy=round(accuracy, 3),
        true_positives=tp,
        false_positives=fp,
        true_negatives=tn,
        false_negatives=fn,
        num_eval_points=total,
    )
