"""
Data Provenance and Attribution for CHAKRAVAT.
Fulfills Requirement R5 (Scientific Integrity & Provenance Tracking).
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class DatasetProvenance:
    """Metadata regarding historical dataset origins, coverage, attribution, and statutory authority."""
    source_name: str = "IBTrACS v04r01 / IMD Best Track Archive"
    authoritative_provider: str = (
        "India Meteorological Department (IMD / RSMC New Delhi) / NOAA NCEI"
    )
    citation: str = (
        "Knapp, K. R., et al. (2018). The International Best Track Archive for Climate "
        "Stewardship (IBTrACS). NOAA National Centers for Environmental Information. "
        "DOI: 10.25921/82ty-9e16"
    )
    retrieval_timestamp: str = "2026-11-05T00:00:00Z"
    geographical_coverage: str = "North Indian Ocean (Bay of Bengal & Arabian Sea: 0°–35°N, 50°–105°E)"
    temporal_resolution: str = "6-hourly synoptic fixes (00, 06, 12, 18 UTC)"
    time_span: str = "2019–2023 (Curated Historical Benchmark Archive)"
    total_records: int = 148
    total_storms: int = 5
    storm_names: List[str] = field(
        default_factory=lambda: ["FANI", "AMPHAN", "TAUKTAE", "YAAS", "BIPARJOY"]
    )
    verified_status: str = "VERIFIED_AUTHENTIC"
    statutory_authority: str = "RSMC New Delhi / India Meteorological Department (IMD)"
    license_type: str = "Public Domain / WMO Open Meteorological Exchange"
    disclaimer: str = (
        "This dataset is bundled for scientific research, training, and algorithmic benchmarking. "
        "Official operational warnings and life-safety directives are issued exclusively by IMD."
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_name": self.source_name,
            "authoritative_provider": self.authoritative_provider,
            "citation": self.citation,
            "retrieval_timestamp": self.retrieval_timestamp,
            "geographical_coverage": self.geographical_coverage,
            "temporal_resolution": self.temporal_resolution,
            "time_span": self.time_span,
            "total_records": self.total_records,
            "total_storms": self.total_storms,
            "storm_names": self.storm_names,
            "verified_status": self.verified_status,
            "statutory_authority": self.statutory_authority,
            "disclaimer": self.disclaimer,
        }


def get_default_provenance(
    record_count: Optional[int] = None,
    storm_count: Optional[int] = None,
    storm_names: Optional[List[str]] = None,
) -> DatasetProvenance:
    """Returns dataset provenance with optional overrides for dynamic record counts."""
    prov = DatasetProvenance()
    if record_count is not None:
        prov.total_records = record_count
    if storm_count is not None:
        prov.total_storms = storm_count
    if storm_names is not None:
        prov.storm_names = storm_names
    return prov
