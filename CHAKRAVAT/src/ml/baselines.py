"""Meteorological Baselines for Cyclone Track & Intensity Forecasting.

North Indian Ocean (NIO) operational baselines:
1. Linear Persistence: Assumes current translation velocity continues unchanged.
2. NIO CLIPER (Climatology and Persistence): Blends linear persistence with
   historical seasonal climatological drift vectors.
3. Intensity Persistence:
   - Pure persistence (future intensity = current intensity)
   - Damped trend persistence (extrapolates recent intensity trend with damping).
"""

from typing import Dict, List, Optional, Tuple
import math


# Climatological drift velocity vectors (deg/hour) for North Indian Ocean basins
# BOB: Bay of Bengal tends NW-NNW drift; AS: Arabian Sea tends NW drift
NIO_CLIMATOLOGY_DRIFT: Dict[str, Tuple[float, float]] = {
    # basin: (lat_velocity_deg_per_hr, lon_velocity_deg_per_hr)
    "BOB": (0.13, -0.06),
    "AS": (0.11, -0.07),
    "BAY OF BENGAL": (0.13, -0.06),
    "ARABIAN SEA": (0.11, -0.07),
    "DEFAULT": (0.12, -0.06),
}


class LinearPersistenceBaseline:
    """Operational track baseline extrapolating recent velocity vector."""

    @staticmethod
    def compute_velocity(
        lat_t0: float, lon_t0: float,
        lat_t1: float, lon_t1: float,
        dt_hours: float = 6.0,
    ) -> Tuple[float, float]:
        """Compute lat/lon translation velocity in degrees per hour.

        (lat_t0, lon_t0) is past position; (lat_t1, lon_t1) is current position.
        """
        if dt_hours <= 0:
            dt_hours = 6.0
        v_lat = (lat_t1 - lat_t0) / dt_hours
        v_lon = (lon_t1 - lon_t0) / dt_hours
        return v_lat, v_lon

    @classmethod
    def predict_position(
        cls,
        current_lat: float,
        current_lon: float,
        past_lat: float,
        past_lon: float,
        dt_past_hours: float = 6.0,
        forecast_horizon_hours: int = 24,
    ) -> Tuple[float, float]:
        """Extrapolate position at forecast_horizon_hours using constant velocity.

        Returns: (pred_lat, pred_lon)
        """
        v_lat, v_lon = cls.compute_velocity(
            lat_t0=past_lat,
            lon_t0=past_lon,
            lat_t1=current_lat,
            lon_t1=current_lon,
            dt_hours=dt_past_hours,
        )
        pred_lat = current_lat + v_lat * forecast_horizon_hours
        pred_lon = current_lon + v_lon * forecast_horizon_hours
        return pred_lat, pred_lon


class CLIPERBaseline:
    """Climatology and Persistence (CLIPER) track baseline for NIO.

    Blends persistence translation vector with historical basin-specific
    climatological drift vectors using lead-time decay weights.
    """

    WEIGHT_12H = 0.80
    WEIGHT_24H = 0.55

    @classmethod
    def predict_position(
        cls,
        current_lat: float,
        current_lon: float,
        past_lat: float,
        past_lon: float,
        basin: str = "BOB",
        dt_past_hours: float = 6.0,
        forecast_horizon_hours: int = 24,
    ) -> Tuple[float, float]:
        """Predict future position by blending persistence and climatology."""
        v_pers_lat, v_pers_lon = LinearPersistenceBaseline.compute_velocity(
            lat_t0=past_lat,
            lon_t0=past_lon,
            lat_t1=current_lat,
            lon_t1=current_lon,
            dt_hours=dt_past_hours,
        )

        clean_basin = (basin or "BOB").strip().upper()
        v_clim_lat, v_clim_lon = NIO_CLIMATOLOGY_DRIFT.get(
            clean_basin, NIO_CLIMATOLOGY_DRIFT["DEFAULT"]
        )

        # Lead-time dependent weighting
        if forecast_horizon_hours <= 12:
            w = cls.WEIGHT_12H
        elif forecast_horizon_hours <= 24:
            # Linear interpolation between 12h (0.80) and 24h (0.55)
            frac = (forecast_horizon_hours - 12) / 12.0
            w = cls.WEIGHT_12H - frac * (cls.WEIGHT_12H - cls.WEIGHT_24H)
        else:
            w = cls.WEIGHT_24H

        v_blend_lat = w * v_pers_lat + (1.0 - w) * v_clim_lat
        v_blend_lon = w * v_pers_lon + (1.0 - w) * v_clim_lon

        pred_lat = current_lat + v_blend_lat * forecast_horizon_hours
        pred_lon = current_lon + v_blend_lon * forecast_horizon_hours
        return pred_lat, pred_lon


class IntensityPersistenceBaseline:
    """Intensity persistence baselines for wind speed and central pressure."""

    @staticmethod
    def predict_pure_persistence(
        current_wind_kts: float,
        current_pressure_hpa: float,
    ) -> Tuple[float, float]:
        """Pure persistence assumes zero intensity change over the forecast window."""
        return float(current_wind_kts), float(current_pressure_hpa)

    @staticmethod
    def predict_trend_persistence(
        current_wind_kts: float,
        past_wind_kts: float,
        current_pressure_hpa: float,
        past_pressure_hpa: float,
        dt_past_hours: float = 6.0,
        forecast_horizon_hours: int = 24,
    ) -> Tuple[float, float]:
        """Damped trend persistence extrapolating recent rate of intensity change.

        Applies damping gamma to prevent runaway explosive intensification/weakening.
        Clamps outputs to physical meteorological bounds.
        """
        if dt_past_hours <= 0:
            dt_past_hours = 6.0

        # Damping factors to prevent overshooting
        gamma = 0.70 if forecast_horizon_hours <= 12 else 0.50

        # Wind speed extrapolation
        d_wind_per_hr = (current_wind_kts - past_wind_kts) / dt_past_hours
        pred_wind = current_wind_kts + d_wind_per_hr * forecast_horizon_hours * gamma
        pred_wind = max(15.0, min(165.0, pred_wind))

        # Central pressure extrapolation
        d_pres_per_hr = (current_pressure_hpa - past_pressure_hpa) / dt_past_hours
        pred_pres = current_pressure_hpa + d_pres_per_hr * forecast_horizon_hours * gamma
        pred_pres = max(880.0, min(1020.0, pred_pres))

        return float(pred_wind), float(pred_pres)
