"""
Unit tests for CHAKRAVAT Data Pipeline & Quality Control Engine.
Verifies Milestone M2 contracts, schema enforcement, dataset integrity, and quality auditing.
"""

import os
import pytest
import pandas as pd
from datetime import datetime

from src.data_pipeline.schema import (
    CycloneFix,
    IMD_CATEGORIES,
    classify_imd_intensity,
    MIN_LATITUDE,
    MAX_LATITUDE,
    MIN_LONGITUDE,
    MAX_LONGITUDE,
    MIN_CENTRAL_PRESSURE_HPA,
)
from src.data_pipeline.loader import (
    CycloneDataLoader,
    DEFAULT_BUNDLED_PATH,
    SAMPLE_DATASET_PATH,
)
from src.data_pipeline.quality import QualityAuditor, haversine_distance_km
from src.data_pipeline.provenance import DatasetProvenance, get_default_provenance


CANONICAL_18_COLUMNS = [
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


class TestHistoricalCyclonesDataset:
    """Verifies the bundled historical cyclone CSV meets all specifications."""

    def test_csv_file_exists(self):
        """Verifies that data/bundled/historical_cyclones.csv exists."""
        assert os.path.exists(DEFAULT_BUNDLED_PATH), f"Missing bundled dataset at {DEFAULT_BUNDLED_PATH}"

    def test_canonical_18_columns_present(self):
        """Verifies that all 18 canonical columns exist in the CSV."""
        df = pd.read_csv(DEFAULT_BUNDLED_PATH)
        for col in CANONICAL_18_COLUMNS:
            assert col in df.columns, f"Canonical column '{col}' missing from CSV"
        assert len(df.columns) == 18, f"Expected exactly 18 columns, found {len(df.columns)}"

    def test_total_records_count_is_148(self):
        """Verifies the CSV contains exactly 148 authentic synoptic fixes."""
        df = pd.read_csv(DEFAULT_BUNDLED_PATH)
        assert len(df) == 148, f"Expected 148 synoptic fixes, found {len(df)}"

    def test_five_benchmark_storms_present(self):
        """Verifies that all 5 benchmark storms are present."""
        df = pd.read_csv(DEFAULT_BUNDLED_PATH)
        storms = set(df["storm_name"].unique())
        expected_storms = {"FANI", "AMPHAN", "TAUKTAE", "YAAS", "BIPARJOY"}
        assert expected_storms.issubset(storms), f"Missing storms: {expected_storms - storms}"

    def test_each_storm_has_at_least_20_records(self):
        """Verifies each of the 5 storms has at least 20 synoptic records."""
        df = pd.read_csv(DEFAULT_BUNDLED_PATH)
        counts = df["storm_name"].value_counts()
        for storm, count in counts.items():
            assert count >= 20, f"Storm '{storm}' has {count} records, expected >= 20"

        # Verify exact benchmark distribution
        assert counts["FANI"] == 34
        assert counts["AMPHAN"] == 23
        assert counts["TAUKTAE"] == 23
        assert counts["YAAS"] == 21
        assert counts["BIPARJOY"] == 47

    def test_data_types_and_ranges(self):
        """Verifies physical ranges and types for all observations."""
        df = pd.read_csv(DEFAULT_BUNDLED_PATH)

        # Latitude in NIO marine basin
        assert (df["latitude"] >= MIN_LATITUDE).all()
        assert (df["latitude"] <= MAX_LATITUDE).all()

        # Longitude in NIO marine basin
        assert (df["longitude"] >= MIN_LONGITUDE).all()
        assert (df["longitude"] <= MAX_LONGITUDE).all()

        # Wind speed strictly positive
        assert (df["wind_speed_kts"] > 0).all()

        # Central pressure within physical maritime bounds
        assert (df["central_pressure_hpa"] >= MIN_CENTRAL_PRESSURE_HPA).all()
        assert (df["central_pressure_hpa"] <= 1025.0).all()

        # Wind speed km/h invariant: approx kts * 1.852
        expected_kmh = (df["wind_speed_kts"] * 1.852).round(1)
        diff = (df["wind_speed_kmh"] - expected_kmh).abs()
        assert (diff <= 0.2).all(), "Wind speed km/h must match kts * 1.852"


class TestCycloneFixSchema:
    """Verifies CycloneFix dataclass and validation rules."""

    def test_valid_fix(self):
        fix = CycloneFix(
            record_id="FANI_2019_001",
            storm_id="NIO_2019_01B",
            storm_name="FANI",
            iso_time="2019-04-26 00:00:00",
            basin="Bay of Bengal",
            latitude=12.5,
            longitude=86.4,
            wind_speed_kts=75.0,
            wind_speed_kmh=138.9,
            central_pressure_hpa=972.0,
            pressure_drop_hpa=38.0,
            nature_code="TS",
            imd_category="VSCS",
            translation_speed_kts=9.5,
            translation_heading_deg=10.0,
            is_landfall=False,
            data_source="IBTrACS v04r00 / IMD RSMC New Delhi",
            quality_flag="0",
        )
        assert fix.is_valid
        assert len(fix.validate()) == 0

    def test_invalid_latitude_out_of_bounds(self):
        fix = CycloneFix(
            record_id="BAD_001",
            storm_id="NIO_TEST",
            storm_name="TEST",
            iso_time="2020-01-01 00:00:00",
            basin="Bay of Bengal",
            latitude=42.0,  # Outside 0-35 N
            longitude=85.0,
            wind_speed_kts=50.0,
            wind_speed_kmh=92.6,
            central_pressure_hpa=990.0,
            pressure_drop_hpa=20.0,
            nature_code="TS",
            imd_category="SCS",
            translation_speed_kts=10.0,
            translation_heading_deg=0.0,
            is_landfall=False,
            data_source="TEST",
            quality_flag="0",
        )
        assert not fix.is_valid
        errors = fix.validate()
        assert any("Latitude" in e for e in errors)

    def test_invalid_wind_speed_non_positive(self):
        fix = CycloneFix(
            record_id="BAD_002",
            storm_id="NIO_TEST",
            storm_name="TEST",
            iso_time="2020-01-01 00:00:00",
            basin="Bay of Bengal",
            latitude=15.0,
            longitude=85.0,
            wind_speed_kts=0.0,  # Invalid <= 0
            wind_speed_kmh=0.0,
            central_pressure_hpa=990.0,
            pressure_drop_hpa=20.0,
            nature_code="TS",
            imd_category="D",
            translation_speed_kts=10.0,
            translation_heading_deg=0.0,
            is_landfall=False,
            data_source="TEST",
            quality_flag="0",
        )
        assert not fix.is_valid
        errors = fix.validate()
        assert any("Wind speed" in e for e in errors)


class TestIMDClassificationScale:
    """Verifies that wind speed mappings strictly adhere to official IMD 8-tier standards."""

    def test_imd_category_scale_thresholds(self):
        assert classify_imd_intensity(15.0) == "LPA"
        assert classify_imd_intensity(20.0) == "D"
        assert classify_imd_intensity(30.0) == "DD"
        assert classify_imd_intensity(40.0) == "CS"
        assert classify_imd_intensity(55.0) == "SCS"
        assert classify_imd_intensity(75.0) == "VSCS"
        assert classify_imd_intensity(105.0) == "ESCS"
        assert classify_imd_intensity(130.0) == "SuCS"


class TestCycloneDataLoader:
    """Verifies data loader ingestion, grouping, and dual dataset support."""

    def test_load_bundled_dataset(self):
        loader = CycloneDataLoader()
        fixes = loader.load_dataset(DEFAULT_BUNDLED_PATH)
        assert len(fixes) == 148

        tracks = loader.get_storm_tracks()
        assert len(tracks) == 5
        assert set(tracks.keys()) == {"FANI", "AMPHAN", "TAUKTAE", "YAAS", "BIPARJOY"}

        # Verify chronological order
        for storm_name, track in tracks.items():
            for i in range(1, len(track)):
                assert track[i].iso_time >= track[i - 1].iso_time

    def test_load_sample_dataset_from_caller(self):
        """Verifies support for caller's sample dataset at data/nio_cyclones_sample.csv."""
        if os.path.exists(SAMPLE_DATASET_PATH):
            loader = CycloneDataLoader()
            fixes = loader.load_dataset(SAMPLE_DATASET_PATH)
            assert len(fixes) >= 70
            tracks = loader.get_storm_tracks()
            assert len(tracks) >= 7

    def test_contract1_load_tuple(self):
        """Verifies survey_report Contract 1: load() returning (DataFrame, Metadata)."""
        loader = CycloneDataLoader()
        df, metadata = loader.load(DEFAULT_BUNDLED_PATH)
        assert isinstance(df, pd.DataFrame)
        assert metadata.total_records == 148
        assert metadata.storm_count == 5
        assert metadata.completeness_score == 100.0


class TestQualityAuditor:
    """Verifies data quality diagnostics, completeness calculation, and anomaly detection."""

    def test_bundled_dataset_quality_report(self):
        loader = CycloneDataLoader()
        loader.load_dataset(DEFAULT_BUNDLED_PATH)
        report = loader.get_quality_report()

        assert report.total_records == 148
        assert report.valid_records == 148
        assert report.invalid_records == 0
        assert report.completeness_pct == 100.0
        assert report.missing_values_count == 0
        assert report.anomaly_count == 0
        assert report.anomaly_rate_pct == 0.0
        assert report.temporal_consistency_score_pct == 100.0

    def test_auditor_detects_unphysical_coordinate_jump(self):
        """Tests that a translation speed exceeding 45 knots is flagged as an anomaly."""
        fix1 = CycloneFix(
            record_id="JUMP_001",
            storm_id="NIO_JUMP",
            storm_name="JUMP",
            iso_time="2022-05-01 00:00:00",
            basin="Bay of Bengal",
            latitude=10.0,
            longitude=85.0,
            wind_speed_kts=50.0,
            wind_speed_kmh=92.6,
            central_pressure_hpa=990.0,
            pressure_drop_hpa=20.0,
            nature_code="TS",
            imd_category="SCS",
            translation_speed_kts=10.0,
            translation_heading_deg=0.0,
            is_landfall=False,
            data_source="TEST",
            quality_flag="0",
        )
        # Fix 2 is 10 degrees north 6 hours later (~1110 km in 6h = ~185 km/h = 100 kts)
        fix2 = CycloneFix(
            record_id="JUMP_002",
            storm_id="NIO_JUMP",
            storm_name="JUMP",
            iso_time="2022-05-01 06:00:00",
            basin="Bay of Bengal",
            latitude=20.0,
            longitude=85.0,
            wind_speed_kts=50.0,
            wind_speed_kmh=92.6,
            central_pressure_hpa=990.0,
            pressure_drop_hpa=20.0,
            nature_code="TS",
            imd_category="SCS",
            translation_speed_kts=10.0,
            translation_heading_deg=0.0,
            is_landfall=False,
            data_source="TEST",
            quality_flag="0",
        )

        report = QualityAuditor.audit_fixes([fix1, fix2])
        assert report.jump_anomalies_count == 1
        assert any(a.anomaly_type == "UNPHYSICAL_COORDINATE_JUMP" for a in report.anomalies)

    def test_auditor_detects_temporal_inversion(self):
        """Tests that a timestamp moving backward is flagged as an anomaly."""
        fix1 = CycloneFix(
            record_id="TIME_001",
            storm_id="NIO_TIME",
            storm_name="TIME",
            iso_time="2022-05-01 12:00:00",
            basin="Bay of Bengal",
            latitude=10.0,
            longitude=85.0,
            wind_speed_kts=50.0,
            wind_speed_kmh=92.6,
            central_pressure_hpa=990.0,
            pressure_drop_hpa=20.0,
            nature_code="TS",
            imd_category="SCS",
            translation_speed_kts=10.0,
            translation_heading_deg=0.0,
            is_landfall=False,
            data_source="TEST",
            quality_flag="0",
        )
        fix2 = CycloneFix(
            record_id="TIME_002",
            storm_id="NIO_TIME",
            storm_name="TIME",
            iso_time="2022-05-01 06:00:00",  # Backward in time!
            basin="Bay of Bengal",
            latitude=10.5,
            longitude=85.0,
            wind_speed_kts=50.0,
            wind_speed_kmh=92.6,
            central_pressure_hpa=990.0,
            pressure_drop_hpa=20.0,
            nature_code="TS",
            imd_category="SCS",
            translation_speed_kts=10.0,
            translation_heading_deg=0.0,
            is_landfall=False,
            data_source="TEST",
            quality_flag="0",
        )

        report = QualityAuditor.audit_fixes([fix1, fix2])
        assert any(a.anomaly_type == "TEMPORAL_INVERSION" for a in report.anomalies)


class TestProvenance:
    """Verifies provenance tracking metadata."""

    def test_provenance_metadata_completeness(self):
        prov = get_default_provenance(record_count=148, storm_count=5)
        assert "IBTrACS" in prov.source_name
        assert "IMD" in prov.authoritative_provider
        assert prov.total_records == 148
        assert prov.total_storms == 5
        assert prov.verified_status == "VERIFIED_AUTHENTIC"


class TestMathematicalAndEdgeCases:
    """Verifies edge cases, boundary conditions, and mathematical routines."""

    def test_invalid_central_pressure(self):
        fix = CycloneFix(
            record_id="P_BAD",
            storm_id="NIO_P",
            storm_name="P",
            iso_time="2020-01-01 00:00:00",
            basin="Bay of Bengal",
            latitude=15.0,
            longitude=85.0,
            wind_speed_kts=50.0,
            wind_speed_kmh=92.6,
            central_pressure_hpa=800.0,  # Below 850 hPa physical limit
            pressure_drop_hpa=210.0,
            nature_code="TS",
            imd_category="SCS",
            translation_speed_kts=10.0,
            translation_heading_deg=0.0,
            is_landfall=False,
            data_source="TEST",
            quality_flag="0",
        )
        assert not fix.is_valid
        assert any("pressure" in e.lower() for e in fix.validate())

    def test_invalid_longitude_out_of_bounds(self):
        fix = CycloneFix(
            record_id="LON_BAD",
            storm_id="NIO_LON",
            storm_name="LON",
            iso_time="2020-01-01 00:00:00",
            basin="Bay of Bengal",
            latitude=15.0,
            longitude=115.0,  # Outside 50-105 E NIO bounds
            wind_speed_kts=50.0,
            wind_speed_kmh=92.6,
            central_pressure_hpa=990.0,
            pressure_drop_hpa=20.0,
            nature_code="TS",
            imd_category="SCS",
            translation_speed_kts=10.0,
            translation_heading_deg=0.0,
            is_landfall=False,
            data_source="TEST",
            quality_flag="0",
        )
        assert not fix.is_valid
        assert any("longitude" in e.lower() for e in fix.validate())

    def test_haversine_distance_accuracy(self):
        # 1 degree of latitude is approximately 111.19 km
        dist = haversine_distance_km(10.0, 80.0, 11.0, 80.0)
        assert 111.0 <= dist <= 111.5

    def test_auditor_handles_empty_dataset(self):
        report = QualityAuditor.audit_fixes([])
        assert report.total_records == 0
        assert report.completeness_pct == 0.0
        assert report.anomaly_count == 0

    def test_loader_from_string_buffer(self):
        csv_text = (
            "record_id,storm_id,storm_name,iso_time,basin,latitude,longitude,wind_speed_kts,"
            "wind_speed_kmh,central_pressure_hpa,pressure_drop_hpa,nature_code,imd_category,"
            "translation_speed_kts,translation_heading_deg,is_landfall,data_source,quality_flag\n"
            "BUF_001,NIO_01,BUF,2022-01-01 00:00:00,Arabian Sea,12.0,65.0,45.0,83.3,995.0,15.0,TS,CS,8.0,330.0,False,TEST,0\n"
        )
        import io
        loader = CycloneDataLoader()
        fixes = loader.load_dataset(uploaded_file=io.StringIO(csv_text))
        assert len(fixes) == 1
        assert fixes[0].storm_name == "BUF"
        assert fixes[0].wind_speed_kts == 45.0

    def test_section_d_view_imports_cleanly(self):
        from src.views import section_data_sources
        assert hasattr(section_data_sources, "render")

