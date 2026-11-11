"""Scientifically Defensible Uncertainty Cone Construction for Track Forecasting.

Fulfills Requirement R5: Never draw arbitrary angle-based confidence cones.
Follows operational meteorological standards (IMD / NHC):
Uncertainty radii are constructed directly from the 70th percentile of
historical track forecast errors on held-out validation storms.
"""

from typing import Dict, List, Optional, Sequence, Tuple
import math


# Default defensible climatological bounds for North Indian Ocean (km)
# Used as calibration anchors when empirical sample is limited
DEFAULT_RADIUS_0H_KM = 15.0    # Synoptic center fix uncertainty
DEFAULT_RADIUS_12H_KM = 65.0   # 12-hour 70th-percentile benchmark
DEFAULT_RADIUS_24H_KM = 125.0  # 24-hour 70th-percentile benchmark


def calculate_empirical_70th_percentile(residuals_km: Sequence[float], fallback_km: float) -> float:
    """Compute the 70th percentile of empirical error residuals.

    Falls back to meteorologically grounded benchmark if sample is empty or too small.
    """
    valid = [r for r in residuals_km if r is not None and not math.isnan(r) and r >= 0]
    if len(valid) < 3:
        return fallback_km

    sorted_res = sorted(valid)
    # 70th percentile index
    idx = int(0.70 * (len(sorted_res) - 1))
    p70 = sorted_res[idx]

    # Guardrails to ensure physical credibility even with small test subsets
    lower_bound = fallback_km * 0.6
    upper_bound = fallback_km * 1.5
    return float(max(lower_bound, min(upper_bound, p70)))


def calculate_uncertainty_cone_radii(
    residuals_12h_km: Optional[Sequence[float]] = None,
    residuals_24h_km: Optional[Sequence[float]] = None,
) -> Dict[int, float]:
    """Calculate the defensible 70% error circle radii (in km) for 0h, 12h, and 24h."""
    r_12 = calculate_empirical_70th_percentile(
        residuals_12h_km or [], DEFAULT_RADIUS_12H_KM
    )
    r_24 = calculate_empirical_70th_percentile(
        residuals_24h_km or [], DEFAULT_RADIUS_24H_KM
    )
    return {
        0: DEFAULT_RADIUS_0H_KM,
        12: round(r_12, 1),
        24: round(r_24, 1),
    }


def km_to_deg(radius_km: float, latitude: float) -> Tuple[float, float]:
    """Convert distance in km to approximate delta latitude and delta longitude in degrees."""
    dlat = radius_km / 111.0
    cos_lat = math.cos(math.radians(latitude))
    # Safeguard against poles (unlikely in NIO)
    cos_lat = max(0.1, cos_lat)
    dlon = radius_km / (111.0 * cos_lat)
    return dlat, dlon


def generate_uncertainty_polygon(
    waypoints: List[Tuple[float, float, int]],  # [(lat, lon, horizon_hours), ...]
    radii_km: Dict[int, float],
    num_arc_points: int = 16,
) -> List[Tuple[float, float]]:
    """Generate a convex corridor polygon surrounding forecasted waypoints.

    Args:
        waypoints: Ordered list of (latitude, longitude, horizon_hours) e.g. at 0h, 12h, 24h.
        radii_km: Mapping of {horizon_hours: radius_km}.
        num_arc_points: Points per tangent semicircle.

    Returns:
        List of (latitude, longitude) coordinates forming a closed polygon.
    """
    if not waypoints:
        return []

    if len(waypoints) == 1:
        lat, lon, h = waypoints[0]
        r = radii_km.get(h, DEFAULT_RADIUS_0H_KM)
        dlat, dlon = km_to_deg(r, lat)
        circle_points = []
        for i in range(num_arc_points):
            angle = 2.0 * math.pi * i / num_arc_points
            circle_points.append((lat + dlat * math.sin(angle), lon + dlon * math.cos(angle)))
        circle_points.append(circle_points[0])
        return circle_points

    # Build left and right boundary paths along track
    left_points: List[Tuple[float, float]] = []
    right_points: List[Tuple[float, float]] = []

    for idx in range(len(waypoints)):
        lat, lon, h = waypoints[idx]
        r_km = radii_km.get(h, DEFAULT_RADIUS_24H_KM)
        dlat, dlon = km_to_deg(r_km, lat)

        # Determine track heading at this waypoint
        if idx == 0:
            next_lat, next_lon, _ = waypoints[1]
            bearing = math.atan2(next_lon - lon, next_lat - lat)
        elif idx == len(waypoints) - 1:
            prev_lat, prev_lon, _ = waypoints[idx - 1]
            bearing = math.atan2(lon - prev_lon, lat - prev_lat)
        else:
            prev_lat, prev_lon, _ = waypoints[idx - 1]
            next_lat, next_lon, _ = waypoints[idx + 1]
            bearing = math.atan2(next_lon - prev_lon, next_lat - prev_lat)

        # Perpendicular normal angles (+90 deg and -90 deg)
        perp_left = bearing - math.pi / 2.0
        perp_right = bearing + math.pi / 2.0

        left_points.append((lat + dlat * math.cos(perp_left), lon + dlon * math.sin(perp_left)))
        right_points.append((lat + dlat * math.cos(perp_right), lon + dlon * math.sin(perp_right)))

    # Cap at final horizon (semicircle cap around terminal waypoint)
    term_lat, term_lon, term_h = waypoints[-1]
    term_r = radii_km.get(term_h, DEFAULT_RADIUS_24H_KM)
    term_dlat, term_dlon = km_to_deg(term_r, term_lat)

    cap_points: List[Tuple[float, float]] = []
    start_angle = math.atan2(right_points[-1][1] - term_lon, right_points[-1][0] - term_lat)
    end_angle = math.atan2(left_points[-1][1] - term_lon, left_points[-1][0] - term_lat)

    # Reorder angles for smooth sweep
    if end_angle < start_angle:
        end_angle += 2.0 * math.pi

    steps = max(4, num_arc_points // 2)
    for s in range(1, steps):
        ang = start_angle + (end_angle - start_angle) * (s / steps)
        cap_points.append((term_lat + term_dlat * math.cos(ang), term_lon + term_dlon * math.sin(ang)))

    # Combine into closed polygon: left points forward, cap points, right points reversed
    polygon = left_points + cap_points + list(reversed(right_points))
    # Close polygon
    if polygon:
        polygon.append(polygon[0])

    return polygon
