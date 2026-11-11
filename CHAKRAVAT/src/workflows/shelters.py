"""CHAKRAVAT Operational Workflow: Coastal Shelter Directory Engine.

Provides search, multi-parameter filtering, occupancy analysis, and CSV export
for illustrative emergency cyclone shelters across high-vulnerability coastal districts.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
import io
import os
from typing import Any, Dict, List, Optional

try:
    import streamlit as st
except ImportError:
    st = None  # type: ignore

from src.ui.state import INITIAL_SHELTERS, _get_store, init_session_state

DEFAULT_CSV_PATHS = [
    os.path.join("data", "illustrative_shelters.csv"),
    os.path.join("data", "bundled", "illustrative_shelters.csv"),
    os.path.join("c:", os.sep, "Users", "pc", "OneDrive", "Desktop", "CHAKRAVAT", "data", "illustrative_shelters.csv"),
]


@dataclass
class ShelterRecord:
    """Canonical data model for an illustrative coastal shelter record."""
    id: str
    name: str
    district: str
    state: str
    latitude: float
    longitude: float
    capacity: int
    current_occupancy: int
    contact_phone: str
    is_accessible: bool
    source_label: str = "ILLUSTRATIVE DEMO RECORD"

    @property
    def available_capacity(self) -> int:
        return max(0, self.capacity - self.current_occupancy)

    @property
    def occupancy_pct(self) -> float:
        if self.capacity <= 0:
            return 0.0
        return round((self.current_occupancy / self.capacity) * 100.0, 1)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["occupancy"] = self.current_occupancy  # alias for backwards compatibility
        d["available_capacity"] = self.available_capacity
        d["occupancy_pct"] = self.occupancy_pct
        return d


def load_shelters_from_csv(file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Load shelters from CSV file path, checking common locations."""
    candidate_paths = [file_path] if file_path else DEFAULT_CSV_PATHS
    
    target_path = None
    for p in candidate_paths:
        if p and os.path.exists(p):
            target_path = p
            break

    if not target_path:
        # Fallback to in-memory INITIAL_SHELTERS
        return [
            {
                "id": s.get("id", f"SHL-GEN-{i+1}"),
                "name": s.get("name", "Shelter"),
                "district": s.get("district", "Coastal"),
                "state": s.get("state", "Odisha"),
                "latitude": float(s.get("latitude", 20.0)),
                "longitude": float(s.get("longitude", 86.0)),
                "capacity": int(s.get("capacity", 1000)),
                "current_occupancy": int(s.get("occupancy", s.get("current_occupancy", 0))),
                "occupancy": int(s.get("occupancy", s.get("current_occupancy", 0))),
                "contact_phone": s.get("contact_phone", "+91-112"),
                "is_accessible": bool(s.get("is_accessible", True)),
                "source_label": s.get("source_label", "ILLUSTRATIVE DEMO RECORD"),
            }
            for i, s in enumerate(INITIAL_SHELTERS)
        ]

    shelters: List[Dict[str, Any]] = []
    with open(target_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cap = int(row.get("capacity", 1000))
            occ = int(row.get("current_occupancy", row.get("occupancy", 0)))
            accessible_val = str(row.get("is_accessible", "True")).strip().lower()
            is_acc = accessible_val in ("true", "1", "yes")

            shelters.append({
                "id": row.get("id", f"SHL-{len(shelters)+1:03d}"),
                "name": row.get("name", "Coastal Cyclone Shelter"),
                "district": row.get("district", "Coastal"),
                "state": row.get("state", "Odisha"),
                "latitude": float(row.get("latitude", 20.0)),
                "longitude": float(row.get("longitude", 86.0)),
                "capacity": cap,
                "current_occupancy": occ,
                "occupancy": occ,
                "available_capacity": max(0, cap - occ),
                "occupancy_pct": round((occ / cap) * 100.0, 1) if cap > 0 else 0.0,
                "contact_phone": row.get("contact_phone", "+91-112"),
                "is_accessible": is_acc,
                "source_label": row.get("source_label", "ILLUSTRATIVE DEMO RECORD"),
            })

    return shelters


def ensure_shelters_initialized() -> List[Dict[str, Any]]:
    """Ensure st.session_state has shelters initialized from CSV."""
    init_session_state()
    store = _get_store()
    if "shelters" not in store or not isinstance(store["shelters"], list) or len(store["shelters"]) == 0:
        store["shelters"] = load_shelters_from_csv()
    return store["shelters"]


def get_shelters(
    search_query: Optional[str] = None,
    state_filter: Optional[str] = None,
    min_capacity: int = 0,
    accessibility_only: bool = False,
) -> List[Dict[str, Any]]:
    """Retrieve shelters with full-text search and multi-facet filtering."""
    shelters = ensure_shelters_initialized()
    filtered: List[Dict[str, Any]] = []

    q = (search_query or "").strip().lower()

    for s in shelters:
        # Full-text name or district search
        if q:
            name_match = q in s.get("name", "").lower()
            dist_match = q in s.get("district", "").lower()
            state_match = q in s.get("state", "").lower()
            if not (name_match or dist_match or state_match):
                continue

        # State filter
        if state_filter and state_filter.lower() != "all":
            if s.get("state", "").lower() != state_filter.lower():
                continue

        # Minimum total capacity
        if s.get("capacity", 0) < min_capacity:
            continue

        # Accessibility filter
        if accessibility_only and not s.get("is_accessible", False):
            continue

        # Compute dynamic helpers
        cap = s.get("capacity", 0)
        occ = s.get("current_occupancy", s.get("occupancy", 0))
        s["current_occupancy"] = occ
        s["occupancy"] = occ
        s["available_capacity"] = max(0, cap - occ)
        s["occupancy_pct"] = round((occ / cap) * 100.0, 1) if cap > 0 else 0.0

        filtered.append(s)

    return filtered


def get_shelter_by_id(shelter_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single shelter by ID."""
    shelters = ensure_shelters_initialized()
    for s in shelters:
        if s.get("id") == shelter_id:
            return s
    return None


def get_shelters_kpis() -> Dict[str, Any]:
    """Compute aggregate shelter capacity and occupancy metrics."""
    shelters = ensure_shelters_initialized()
    total_shelters = len(shelters)
    total_capacity = sum(s.get("capacity", 0) for s in shelters)
    total_occupancy = sum(s.get("current_occupancy", s.get("occupancy", 0)) for s in shelters)
    accessible_count = sum(1 for s in shelters if s.get("is_accessible", False))
    overall_utilization = round((total_occupancy / total_capacity) * 100.0, 1) if total_capacity > 0 else 0.0

    return {
        "total_shelters": total_shelters,
        "total_capacity": total_capacity,
        "total_occupancy": total_occupancy,
        "available_capacity": max(0, total_capacity - total_occupancy),
        "overall_utilization_pct": overall_utilization,
        "accessible_count": accessible_count,
    }


def export_shelters_csv(shelters_subset: Optional[List[Dict[str, Any]]] = None) -> str:
    """Export shelter records into RFC 4180 CSV format."""
    dataset = shelters_subset if shelters_subset is not None else ensure_shelters_initialized()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "name", "district", "state", "latitude", "longitude",
        "capacity", "current_occupancy", "available_capacity",
        "occupancy_pct", "contact_phone", "is_accessible", "source_label"
    ])
    for s in dataset:
        cap = s.get("capacity", 0)
        occ = s.get("current_occupancy", s.get("occupancy", 0))
        writer.writerow([
            s.get("id", ""),
            s.get("name", ""),
            s.get("district", ""),
            s.get("state", ""),
            s.get("latitude", ""),
            s.get("longitude", ""),
            cap,
            occ,
            max(0, cap - occ),
            round((occ / cap) * 100.0, 1) if cap > 0 else 0.0,
            s.get("contact_phone", ""),
            s.get("is_accessible", True),
            s.get("source_label", "ILLUSTRATIVE DEMO RECORD"),
        ])
    return output.getvalue()
