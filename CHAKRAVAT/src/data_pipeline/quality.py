"""
Data Quality and Health Auditing Engine for CHAKRAVAT.
Fulfills Requirements R2(D), R3, and R5 with pure dynamic verification.
"""

import math
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from src.data_pipeline.schema import (
    CycloneFix,
    MIN_LATITUDE,
    MAX_LATITUDE,
    MIN_LONGITUDE,
    MAX_LONGITUDE,
    MIN_CENTRAL_PRESSURE_HPA,
    MAX_CENTRAL_PRESSURE_HPA,
)


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle distance between two coordinates in kilometers."""
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


@dataclass
class AnomalyRecord:
    """Identified data anomaly or quality violation."""
    record_id: str
    storm_id: str
    storm_name: str
    field_name: str
    anomaly_type: str
    description: str
    severity: str  # 'WARNING' | 'ERROR'

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "storm_id": self.storm_id,
            "storm_name": self.storm_name,
            "field_name": self.field_name,
            "anomaly_type": self.anomaly_type,
            "description": self.description,
            "severity": self.severity,
        }


@dataclass
class DataQualityReport:
    """Aggregated audit metrics for a cyclone dataset."""
    total_records: int
    valid_records: int
    invalid_records: int
    completeness_pct: float
    field_completeness: Dict[str, float]
    missing_values_count: int
    anomaly_count: int
    anomaly_rate_pct: float
    temporal_consistency_score_pct: float
    jump_anomalies_count: int
    anomalies: List[AnomalyRecord] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_records": self.total_records,
            "valid_records": self.valid_records,
            "invalid_records": self.invalid_records,
            "completeness_pct": round(self.completeness_pct, 2),
            "field_completeness": {k: round(v, 2) for k, v in self.field_completeness.items()},
            "missing_values_count": self.missing_values_count,
            "anomaly_count": self.anomaly_count,
            "anomaly_rate_pct": round(self.anomaly_rate_pct, 2),
            "temporal_consistency_score_pct": round(self.temporal_consistency_score_pct, 2),
            "jump_anomalies_count": self.jump_anomalies_count,
            "anomalies": [a.to_dict() for a in self.anomalies],
        }


class QualityAuditor:
    """
    Performs comprehensive data quality audit, missing-value analysis,
    kinematic coordinate jump detection, and temporal sequence consistency checks.
    """

    CANONICAL_FIELDS = [
        "record_id",
        "storm_id",
        "storm_name",
        "iso_time",
        "basin",
        "latitude",
        "longitude",
        "wind_speed_kts",
        "wind_speed_kmh",
        "central_pressure_hpa",
        "pressure_drop_hpa",
        "nature_code",
        "imd_category",
        "translation_speed_kts",
        "translation_heading_deg",
        "is_landfall",
        "data_source",
        "quality_flag",
    ]

    MAX_PLAUSIBLE_SPEED_KTS = 45.0  # ~83 km/h maximum physical translation speed

    @classmethod
    def audit_fixes(cls, fixes: List[CycloneFix]) -> DataQualityReport:
        """Audits a list of CycloneFix objects."""
        if not fixes:
            return DataQualityReport(
                total_records=0,
                valid_records=0,
                invalid_records=0,
                completeness_pct=0.0,
                field_completeness={f: 0.0 for f in cls.CANONICAL_FIELDS},
                missing_values_count=0,
                anomaly_count=0,
                anomaly_rate_pct=0.0,
                temporal_consistency_score_pct=0.0,
                jump_anomalies_count=0,
                anomalies=[],
            )

        total_records = len(fixes)
        field_present_counts = {f: 0 for f in cls.CANONICAL_FIELDS}
        missing_values_count = 0
        anomalies: List[AnomalyRecord] = []
        valid_records = 0

        # Group fixes by storm for trajectory & temporal audit
        storm_groups: Dict[str, List[CycloneFix]] = {}

        for fix in fixes:
            fix_dict = fix.to_dict()
            is_record_valid = True

            # 1. Field completeness check
            for field_name in cls.CANONICAL_FIELDS:
                val = fix_dict.get(field_name)
                if val is not None and str(val).strip() != "":
                    field_present_counts[field_name] += 1
                else:
                    missing_values_count += 1
                    is_record_valid = False
                    anomalies.append(
                        AnomalyRecord(
                            record_id=fix.record_id,
                            storm_id=fix.storm_id,
                            storm_name=fix.storm_name,
                            field_name=field_name,
                            anomaly_type="MISSING_FIELD",
                            description=f"Field '{field_name}' is null or empty",
                            severity="ERROR",
                        )
                    )

            # 2. Meteorological bounds checks
            validation_errors = fix.validate()
            if validation_errors:
                is_record_valid = False
                for err in validation_errors:
                    anomalies.append(
                        AnomalyRecord(
                            record_id=fix.record_id,
                            storm_id=fix.storm_id,
                            storm_name=fix.storm_name,
                            field_name="bounds",
                            anomaly_type="METEOROLOGICAL_BOUND_VIOLATION",
                            description=err,
                            severity="ERROR",
                        )
                    )

            if is_record_valid:
                valid_records += 1

            storm_groups.setdefault(fix.storm_id, []).append(fix)

        # 3. Trajectory & Temporal Consistency Checks
        jump_anomalies_count = 0
        total_transitions = 0
        monotonic_transitions = 0

        for storm_id, track in storm_groups.items():
            for i in range(1, len(track)):
                total_transitions += 1
                prev_fix = track[i - 1]
                curr_fix = track[i]

                # Temporal monotonicity
                try:
                    t_prev = datetime.fromisoformat(prev_fix.iso_time.replace("Z", "+00:00"))
                    t_curr = datetime.fromisoformat(curr_fix.iso_time.replace("Z", "+00:00"))
                    delta_hours = (t_curr - t_prev).total_seconds() / 3600.0

                    if delta_hours > 0:
                        monotonic_transitions += 1
                    else:
                        anomalies.append(
                            AnomalyRecord(
                                record_id=curr_fix.record_id,
                                storm_id=storm_id,
                                storm_name=curr_fix.storm_name,
                                field_name="iso_time",
                                anomaly_type="TEMPORAL_INVERSION",
                                description=(
                                    f"Fix timestamp {curr_fix.iso_time} does not advance from {prev_fix.iso_time}"
                                ),
                                severity="ERROR",
                            )
                        )

                    # Coordinate jump check
                    if delta_hours > 0:
                        dist_km = haversine_distance_km(
                            prev_fix.latitude,
                            prev_fix.longitude,
                            curr_fix.latitude,
                            curr_fix.longitude,
                        )
                        calculated_speed_kts = (dist_km / delta_hours) / 1.852
                        if calculated_speed_kts > cls.MAX_PLAUSIBLE_SPEED_KTS:
                            jump_anomalies_count += 1
                            anomalies.append(
                                AnomalyRecord(
                                    record_id=curr_fix.record_id,
                                    storm_id=storm_id,
                                    storm_name=curr_fix.storm_name,
                                    field_name="coordinates",
                                    anomaly_type="UNPHYSICAL_COORDINATE_JUMP",
                                    description=(
                                        f"Implied translation speed of {calculated_speed_kts:.1f} kts "
                                        f"exceeds physical limit ({cls.MAX_PLAUSIBLE_SPEED_KTS} kts)"
                                    ),
                                    severity="WARNING",
                                )
                            )
                except Exception as ex:
                    anomalies.append(
                        AnomalyRecord(
                            record_id=curr_fix.record_id,
                            storm_id=storm_id,
                            storm_name=curr_fix.storm_name,
                            field_name="iso_time",
                            anomaly_type="TIMESTAMP_PARSE_ERROR",
                            description=f"Failed to parse timestamp '{curr_fix.iso_time}': {ex}",
                            severity="ERROR",
                        )
                    )

        # Calculate percentages
        field_completeness = {
            f: (field_present_counts[f] / total_records) * 100.0 for f in cls.CANONICAL_FIELDS
        }
        overall_completeness = sum(field_completeness.values()) / len(cls.CANONICAL_FIELDS)
        temporal_score = (
            (monotonic_transitions / total_transitions * 100.0) if total_transitions > 0 else 100.0
        )
        anomaly_count = len(anomalies)
        anomaly_rate = (anomaly_count / total_records * 100.0) if total_records > 0 else 0.0

        return DataQualityReport(
            total_records=total_records,
            valid_records=valid_records,
            invalid_records=total_records - valid_records,
            completeness_pct=overall_completeness,
            field_completeness=field_completeness,
            missing_values_count=missing_values_count,
            anomaly_count=anomaly_count,
            anomaly_rate_pct=anomaly_rate,
            temporal_consistency_score_pct=temporal_score,
            jump_anomalies_count=jump_anomalies_count,
            anomalies=anomalies,
        )
