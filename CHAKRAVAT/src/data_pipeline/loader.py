"""
Historical Cyclone Data Ingestion & Normalizer for CHAKRAVAT.
Supports canonical bundled dataset, sample dataset, and arbitrary user CSV uploads.
"""

import os
import csv
import io
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Any, Union
import pandas as pd

from src.data_pipeline.schema import CycloneFix, classify_imd_intensity
from src.data_pipeline.quality import QualityAuditor, DataQualityReport
from src.data_pipeline.provenance import DatasetProvenance, get_default_provenance

DEFAULT_BUNDLED_PATH = os.path.join("data", "bundled", "historical_cyclones.csv")
SAMPLE_DATASET_PATH = os.path.join("data", "nio_cyclones_sample.csv")

# Standard IMD Category Text to Code normalization
CATEGORY_NAME_MAP = {
    "low pressure area": "LPA",
    "lpa": "LPA",
    "depression": "D",
    "d": "D",
    "deep depression": "DD",
    "dd": "DD",
    "cyclonic storm": "CS",
    "cs": "CS",
    "severe cyclonic storm": "SCS",
    "scs": "SCS",
    "very severe cyclonic storm": "VSCS",
    "vscs": "VSCS",
    "extremely severe cyclonic storm": "ESCS",
    "escs": "ESCS",
    "super cyclonic storm": "SuCS",
    "sucs": "SuCS",
    "super cyclone": "SuCS",
}

# Basin Code Normalization
BASIN_MAP = {
    "as": "Arabian Sea",
    "arabian sea": "Arabian Sea",
    "bob": "Bay of Bengal",
    "bay of bengal": "Bay of Bengal",
    "nio": "North Indian Ocean",
    "north indian ocean": "North Indian Ocean",
}


@dataclass
class DatasetMetadata:
    """Summary metadata of loaded dataset."""
    total_records: int
    storm_count: int
    storm_names: List[str]
    start_time: str
    end_time: str
    basins: List[str]
    completeness_score: float


class CycloneDataLoader:
    """
    Ingests and normalizes historical cyclone datasets from CSV or file-like objects.
    Enforces the 18 canonical IBTrACS/IMD schema attributes, sorts chronologically,
    and partitions into storm trajectories.
    """

    def __init__(self, default_path: Optional[str] = None):
        self.default_path = default_path or DEFAULT_BUNDLED_PATH
        self._cached_fixes: List[CycloneFix] = []
        self._storm_tracks: Dict[str, List[CycloneFix]] = {}
        self._provenance: Optional[DatasetProvenance] = None
        self._quality_report: Optional[DataQualityReport] = None

    @classmethod
    def normalize_header(cls, header: str) -> str:
        """Cleans and standardizes header string."""
        return header.strip().lower().replace(" ", "_").replace("-", "_")

    @classmethod
    def map_row_to_fix(cls, row: Dict[str, Any], index: int) -> CycloneFix:
        """Maps an arbitrary dict row to a canonical CycloneFix dataclass."""
        norm_row = {cls.normalize_header(k): v for k, v in row.items()}

        # 1. Storm identification
        storm_name = str(
            norm_row.get("storm_name")
            or norm_row.get("name")
            or norm_row.get("cyclone_name")
            or "UNNAMED"
        ).strip().upper()

        storm_id = str(
            norm_row.get("storm_id")
            or norm_row.get("id")
            or norm_row.get("sid")
            or f"NIO_{storm_name}"
        ).strip()

        # 2. Timestamp
        iso_time = str(
            norm_row.get("iso_time")
            or norm_row.get("timestamp_utc")
            or norm_row.get("time")
            or norm_row.get("timestamp")
            or ""
        ).strip()

        # 3. Basin
        raw_basin = str(norm_row.get("basin") or norm_row.get("sub_basin") or "Bay of Bengal").strip().lower()
        basin = BASIN_MAP.get(raw_basin, "Bay of Bengal")

        # 4. Latitude and Longitude
        lat_val = norm_row.get("latitude") or norm_row.get("lat") or 0.0
        lon_val = norm_row.get("longitude") or norm_row.get("lon") or norm_row.get("long") or 0.0
        latitude = float(lat_val)
        longitude = float(lon_val)

        # 5. Wind Speed
        wind_val = norm_row.get("wind_speed_kts") or norm_row.get("wind_kts") or norm_row.get("wind") or 25.0
        wind_speed_kts = float(wind_val)

        wind_kmh_val = norm_row.get("wind_speed_kmh") or norm_row.get("wind_kph") or norm_row.get("wind_kmh")
        if wind_kmh_val is not None and str(wind_kmh_val).strip() != "":
            wind_speed_kmh = float(wind_kmh_val)
        else:
            wind_speed_kmh = round(wind_speed_kts * 1.852, 1)

        # 6. Pressure
        pres_val = (
            norm_row.get("central_pressure_hpa")
            or norm_row.get("pressure_mb")
            or norm_row.get("pressure_hpa")
            or norm_row.get("pres")
            or 1000.0
        )
        central_pressure_hpa = float(pres_val)

        drop_val = norm_row.get("pressure_drop_hpa") or norm_row.get("p_drop") or norm_row.get("delta_p")
        if drop_val is not None and str(drop_val).strip() != "":
            pressure_drop_hpa = float(drop_val)
        else:
            pressure_drop_hpa = round(1010.0 - central_pressure_hpa, 1)

        # 7. Nature & Category
        nature_code = str(norm_row.get("nature_code") or norm_row.get("type") or "TS").strip().upper()

        raw_cat = str(norm_row.get("imd_category") or norm_row.get("category") or norm_row.get("cat") or "").strip()
        if raw_cat.lower() in CATEGORY_NAME_MAP:
            imd_category = CATEGORY_NAME_MAP[raw_cat.lower()]
        else:
            imd_category = classify_imd_intensity(wind_speed_kts)

        # 8. Kinematics
        raw_speed = norm_row.get("translation_speed_kts") or norm_row.get("speed_kts")
        if raw_speed is not None and str(raw_speed).strip() != "":
            translation_speed_kts = float(raw_speed)
        elif norm_row.get("movement_speed_kph") is not None and str(norm_row.get("movement_speed_kph")).strip() != "":
            translation_speed_kts = round(float(norm_row.get("movement_speed_kph")) / 1.852, 1)
        else:
            translation_speed_kts = 0.0

        raw_heading = (
            norm_row.get("translation_heading_deg")
            or norm_row.get("movement_dir_deg")
            or norm_row.get("heading")
            or norm_row.get("dir_deg")
        )
        translation_heading_deg = float(raw_heading) if raw_heading is not None and str(raw_heading).strip() != "" else 0.0

        # 9. Landfall, source, quality
        raw_landfall = norm_row.get("is_landfall") or norm_row.get("landfall") or False
        if isinstance(raw_landfall, str):
            is_landfall = raw_landfall.strip().lower() in ("true", "1", "yes", "t")
        else:
            is_landfall = bool(raw_landfall)

        data_source = str(
            norm_row.get("data_source") or norm_row.get("source") or "IBTrACS v04r00 / IMD RSMC New Delhi"
        ).strip()
        quality_flag = str(norm_row.get("quality_flag") or norm_row.get("flag") or "0").strip()

        # 10. Record ID
        raw_rec_id = norm_row.get("record_id")
        if raw_rec_id and str(raw_rec_id).strip():
            record_id = str(raw_rec_id).strip()
        else:
            year_str = iso_time[:4] if len(iso_time) >= 4 else "YYYY"
            record_id = f"{storm_name}_{year_str}_{index:03d}"

        return CycloneFix(
            record_id=record_id,
            storm_id=storm_id,
            storm_name=storm_name,
            iso_time=iso_time,
            basin=basin,
            latitude=latitude,
            longitude=longitude,
            wind_speed_kts=wind_speed_kts,
            wind_speed_kmh=wind_speed_kmh,
            central_pressure_hpa=central_pressure_hpa,
            pressure_drop_hpa=pressure_drop_hpa,
            nature_code=nature_code,
            imd_category=imd_category,
            translation_speed_kts=translation_speed_kts,
            translation_heading_deg=translation_heading_deg,
            is_landfall=is_landfall,
            data_source=data_source,
            quality_flag=quality_flag,
        )

    def load_dataset(
        self,
        csv_path: Optional[str] = None,
        uploaded_file: Optional[Any] = None,
    ) -> List[CycloneFix]:
        """
        Loads dataset from file path or uploaded file buffer.
        Defaults to bundled historical dataset, with fallback to sample dataset.
        """
        fixes: List[CycloneFix] = []

        if uploaded_file is not None:
            # Handle UploadedFile or BytesIO / StringIO
            if hasattr(uploaded_file, "getvalue"):
                content = uploaded_file.getvalue()
                if isinstance(content, bytes):
                    content = content.decode("utf-8", errors="replace")
                reader = csv.DictReader(io.StringIO(content))
            elif hasattr(uploaded_file, "read"):
                content = uploaded_file.read()
                if isinstance(content, bytes):
                    content = content.decode("utf-8", errors="replace")
                reader = csv.DictReader(io.StringIO(content))
            else:
                reader = csv.DictReader(uploaded_file)
            
            for idx, row in enumerate(reader, start=1):
                fixes.append(self.map_row_to_fix(row, idx))

        else:
            target_path = csv_path or self.default_path
            # Check existence, fallback to sample dataset if target_path does not exist
            if not os.path.exists(target_path):
                if os.path.exists(SAMPLE_DATASET_PATH):
                    target_path = SAMPLE_DATASET_PATH
                elif os.path.exists(DEFAULT_BUNDLED_PATH):
                    target_path = DEFAULT_BUNDLED_PATH
                else:
                    raise FileNotFoundError(f"Neither {target_path} nor default paths exist.")

            with open(target_path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                for idx, row in enumerate(reader, start=1):
                    fixes.append(self.map_row_to_fix(row, idx))

        # Sort chronologically by iso_time
        fixes.sort(key=lambda f: f.iso_time)

        self._cached_fixes = fixes

        # Partition into storm tracks
        tracks: Dict[str, List[CycloneFix]] = {}
        for f in fixes:
            tracks.setdefault(f.storm_name, []).append(f)
        for sname in tracks:
            tracks[sname].sort(key=lambda x: x.iso_time)
        self._storm_tracks = tracks

        # Update quality report and provenance
        self._quality_report = QualityAuditor.audit_fixes(fixes)
        self._provenance = get_default_provenance(
            record_count=len(fixes),
            storm_count=len(tracks),
            storm_names=list(tracks.keys()),
        )

        return fixes

    def get_storm_tracks(self) -> Dict[str, List[CycloneFix]]:
        """Returns dictionary mapping storm_name -> chronologically sorted list of CycloneFix."""
        if not self._storm_tracks:
            self.load_dataset()
        return self._storm_tracks

    def get_fixes(self) -> List[CycloneFix]:
        """Returns cached flat list of all CycloneFix records."""
        if not self._cached_fixes:
            self.load_dataset()
        return self._cached_fixes

    def get_dataframe(self) -> pd.DataFrame:
        """Returns dataset as a clean pandas DataFrame with canonical columns."""
        fixes = self.get_fixes()
        return pd.DataFrame([f.to_dict() for f in fixes])

    def get_data_quality_summary(self) -> Dict[str, Any]:
        """Returns summary dictionary of dataset health and quality metrics."""
        if self._quality_report is None:
            self.load_dataset()
        return self._quality_report.to_dict()

    def get_quality_report(self) -> DataQualityReport:
        """Returns detailed DataQualityReport object."""
        if self._quality_report is None:
            self.load_dataset()
        return self._quality_report

    def get_provenance(self) -> DatasetProvenance:
        """Returns dataset provenance and attribution metadata."""
        if self._provenance is None:
            self.load_dataset()
        return self._provenance

    def load(self, filepath: Optional[str] = None) -> Tuple[pd.DataFrame, DatasetMetadata]:
        """
        Complies with survey_report Contract 1.
        Returns (DataFrame, DatasetMetadata).
        """
        fixes = self.load_dataset(csv_path=filepath)
        df = pd.DataFrame([f.to_dict() for f in fixes])
        storm_names = list(self._storm_tracks.keys())
        start_time = fixes[0].iso_time if fixes else ""
        end_time = fixes[-1].iso_time if fixes else ""
        basins = sorted(list({f.basin for f in fixes}))
        completeness = self._quality_report.completeness_pct if self._quality_report else 100.0

        metadata = DatasetMetadata(
            total_records=len(fixes),
            storm_count=len(storm_names),
            storm_names=storm_names,
            start_time=start_time,
            end_time=end_time,
            basins=basins,
            completeness_score=completeness,
        )
        return df, metadata
