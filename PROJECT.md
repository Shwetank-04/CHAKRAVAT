# Project: CHAKRAVAT (North Indian Ocean Cyclone Intelligence Platform)

## Architecture Overview
CHAKRAVAT is an experimental decision-support prototype for cyclone-monitoring, prediction, and disaster-response focused on the North Indian Ocean (Bay of Bengal, Arabian Sea, Indian coastal regions). Built using **Python + Streamlit** with a modular, highly decoupled architecture:

```
c:\Users\pc\OneDrive\Desktop\CHAKRAVAT\
├── .streamlit/
│   └── config.toml                  # Dark theme base (#101820) & headless configuration
├── app.py                           # Main application entry point & routing shell
├── requirements.txt                 # Dependencies (streamlit, pandas, numpy, scikit-learn, plotly)
├── src/
│   ├── ui/                          # Reusable UI design system & components
│   │   ├── __init__.py
│   │   ├── theme.py                 # Custom CSS injection, typography, whitespace constraints
│   │   ├── components.py            # Cards, badges, metric displays, alert banners, disclaimers
│   │   └── state.py                 # Deterministic session state initialization & accessors
│   ├── data_pipeline/               # Historical IBTrACS data ingestion & validation
│   │   ├── __init__.py
│   │   ├── schema.py                # 18-column IBTrACS canonical schema & IMD scale constants
│   │   ├── loader.py                # Bundled CSV loading, type casting, filtering
│   │   ├── quality.py               # Missing values, completeness metrics, quality flags
│   │   └── provenance.py           # Source metadata, retrieval timestamps, coverage tracking
│   ├── ml/                          # Scientific ML models, storm-level splits, baselines
│   │   ├── __init__.py
│   │   ├── split.py                 # Strict storm-level group splitting (zero-leakage assertion)
│   │   ├── baselines.py             # Linear Persistence & NIO CLIPER (track), Trend Persistence (intensity)
│   │   ├── models.py                # Track delta regressor, intensity regressor, genesis classifier
│   │   ├── evaluation.py            # Haversine MTE (km), Wind MAE (kts), Precision/Recall (genuine metrics)
│   │   ├── uncertainty.py           # Empirical 70th-percentile validation error cones
│   │   └── pipeline.py              # End-to-end training, caching, inference orchestrator
│   ├── geo/                         # Offline geospatial mapping engine
│   │   ├── __init__.py
│   │   ├── map_engine.py            # Plotly go.Scattergeo offline North Indian Ocean basemap
│   │   ├── tracks.py                # Multi-storm track plotting, waypoint telemetry, hovercards
│   │   └── styling.py               # IMD 8-tier category color mappings & legends
│   ├── workflows/                   # State machines for alerts, reports, shelters, response
│   │   ├── __init__.py
│   │   ├── alerts.py                # Alert dataclass, state machine, audit history logging
│   │   ├── reports.py               # Community report submission, 5-state review workflow
│   │   ├── shelters.py              # 7 illustrative shelters, search/filter algorithms
│   │   └── disaster_response.py     # Regional risk summaries, safe zones, dispatch task manager
│   └── views/                       # 9 Integrated Section Views
│       ├── __init__.py
│       ├── section_overview.py      # (A) Cyclone Intelligence Overview
│       ├── section_map.py           # (B) Interactive Map & Track Intelligence
│       ├── section_prediction.py    # (C) Prediction & Model Evaluation
│       ├── section_data_sources.py  # (D) Data Sources & Data Quality
│       ├── section_alerts.py        # (E) Alerts & Human Review
│       ├── section_community.py     # (F) Community Reports
│       ├── section_shelters.py      # (G) Shelter Directory
│       ├── section_response.py      # (H) Disaster Response
│       └── section_about.py         # (I) About & Methodology
├── data/
│   └── bundled/
│       ├── historical_cyclones.csv  # Bundled 148 synoptic fixes across 5 benchmark storms
│       └── illustrative_shelters.csv# 7 pre-seeded coastal cyclone shelters
└── tests/                           # E2E & Unit Test Suites
    ├── e2e/                         # Requirement-driven opaque-box E2E tests (Tiers 1-4)
    └── unit/                        # Module unit tests
```

---

## Feature Inventory
Every requirement from R1 through R5 and all Acceptance Criteria are accounted for and assigned to a milestone:

| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Dark Design System (#101820) | Cohesive deep navy/charcoal styling, custom CSS, typography | M1 | R1, AC-Visual |
| 2 | Whitespace Discipline | Strict max 3 cards/columns per horizontal row across all pages | M1 | R1, AC-Visual |
| 3 | State Boxes & Loading/Empty UI | Styled UI for loading/empty/error states, no raw stack traces | M1 | R1, AC-Visual |
| 4 | Effortless Sidebar Navigation | Navigation menu routing across all 9 sections (A through I) | M1 | R1, R2, AC-Startup |
| 5 | Session State Store | Pure Python in-memory state store for alerts, reports, demo | M1 | R4, AC-Workflow |
| 6 | Bundled Historical Cyclone Dataset | 148 fixes across 5 storms (Fani, Amphan, Tauktae, Yaas, Biparjoy) | M2 | R3, R4, AC-Data |
| 7 | Data Validation & Schema Enforcement | 18-column canonical schema, type validation, data quality flags | M2 | R3, AC-Data |
| 8 | Data Quality & Provenance Centre | Section D: Source metadata, timestamps, missing values, coverage | M2 | R2(D), R5, AC-Integrity |
| 9 | Strict Storm-Level Splitter | Group-based splitting with zero within-storm observation leakage | M3 | R3, AC-Data |
| 10 | Persistence Baselines | Linear Persistence & CLIPER (track), Trend Persistence (intensity) | M3 | R3, AC-Data |
| 11 | Genuine ML Prediction Models | Track displacement regressor, Intensity regressor, Genesis class. | M3 | R3, AC-Data |
| 12 | Real Dynamic Evaluation Metrics | Haversine MTE (km), Wind MAE, Precision/Recall (NO hardcoding) | M3 | R3, AC-Data |
| 13 | Defensible Uncertainty Cones | Empirical 70th-percentile error radii validation cones | M3 | R5, AC-Integrity |
| 14 | Model State Management & Disclaimers | Fallback UI for "MODEL_NOT_TRAINED" and "DATA_LIMITED" | M3 | R3, R5, AC-Data |
| 15 | Prediction View (Section C) | Genesis, Track, Intensity views with metrics, baselines, warnings | M3 | R2(C), AC-Demo |
| 16 | North Indian Ocean Map Engine | Plotly go.Scattergeo basemap (52°-98°E, 2°-28.5°N) 100% offline | M4 | R2(B), R4, AC-Map |
| 17 | Multi-Storm Track Rendering | >=3 distinct tracks (Fani, Amphan, Tauktae, Biparjoy) with IMD colors | M4 | R2(B), AC-Map |
| 18 | Waypoint Telemetry & Hovercards | Timestamps, coordinates, wind speed, pressure, storm selector | M4 | R2(B), AC-Map |
| 19 | Map Legends & Controls | Visual legend of IMD intensity tiers, zoom/pan controls | M4 | R2(B), AC-Map |
| 20 | Alert Management System | Create alerts with severity, region, description, validity | M5 | R2(E), AC-Alert |
| 21 | Alert Review Workflow & Audit Trail | Pending->Approved/Rejected/Changes Requested + timestamped log | M5 | R2(E), AC-Alert |
| 22 | Community Report Submission | Description, coordinates/region, incident time, category, photo | M5 | R2(F), AC-Community |
| 23 | Community Verification Lifecycle | Submitted->Under Review->Verified/Rejected/Needs More Info | M5 | R2(F), AC-Community |
| 24 | Unverified Citizen Report Warning | Mandatory prominent warning banner on unverified submissions | M5 | R2(F), R5, AC-Community |
| 25 | Coastal Shelter Directory | >=5 illustrative shelters with name, location, contact, capacity | M5 | R2(G), AC-Shelter |
| 26 | Shelter Search & Filter | Multi-parameter filtering (district, accessibility, capacity) | M5 | R2(G), AC-Shelter |
| 27 | Shelter Simulation Disclaimers | Prominent label stating illustrative demo data | M5 | R2(G), R5, AC-Shelter |
| 28 | Regional Disaster Response Center | Section H: Risk summary cards (max 3/row), triage, response tasks | M5 | R2(H), AC-Workflow |
| 29 | Cyclone Intelligence Overview | Section A: Editorial hierarchy, active status, risk highlights | M6 | R2(A), AC-Startup |
| 30 | About & Scientific Methodology | Section I: Architecture, ML methodology, limitations, disclaimers | M6 | R2(I), R5, AC-Integrity |
| 31 | Complete Demo Journey | Seamless walkthrough across all sections without credentials | M6 | R4, AC-Demo |
| 32 | Experimental Disclaimers Display | Mandatory banner stating prototype status on overview/prediction | M6 | R1, R5, AC-Integrity |
| 33 | 100% E2E Test Suite Pass | Opaque-box automated test suite (Tiers 1-4) passing cleanly | M7 | AC 1-9 |
| 34 | Adversarial Hardening (Tier 5) | Stress testing, missing data resilience, edge-case coverage | M7 | Project Pattern |

---

## Milestones & Execution Plan

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Core Design System, App Shell & Navigation | Theme, custom CSS, layout helpers, sidebar, session state, app.py | None | DONE |
| M2 | Historical Cyclone Data Pipeline & Data Centre | Bundled 148-fix CSV, schema validation, quality checks, Section D | None | DONE |
| M3 | Scientific ML Pipeline & Model Evaluation | Storm split, persistence baselines, ML models, dynamic metrics, Section C | M2 | DONE |
| M4 | Interactive Map & Track Intelligence | Offline Plotly NIO map, tracks, waypoint telemetry, Section B | M2 | DONE |
| M5 | Operational Workflows (Alerts, Reports, Shelters, Response) | Alerts + audit, Reports + review, Shelters + search, Response, Sections E, F, G, H | M1 | DONE |
| M6 | Intelligence Overview, Methodology & Demo Polish | Section A, Section I, end-to-end demo journey integration, disclaimers | M1, M3, M4, M5 | DONE |
| M7 | E2E Verification & Adversarial Hardening | Pass 100% test suite + Forensic Integrity Audit + AppTest Walkthrough | M1-M6, TEST_READY | DONE |

Parallel Track:
- **E2E Testing Track**: Dispatched concurrently to design and implement the 4-tier opaque-box test suite and publish `TEST_READY.md`.

---

## Interface Contracts

### 1. Data Pipeline ↔ ML & UI
```python
@dataclass(frozen=True)
class CycloneFix:
    record_id: str
    storm_id: str
    storm_name: str
    iso_time: str
    basin: str               # 'Bay of Bengal' | 'Arabian Sea'
    latitude: float
    longitude: float
    wind_speed_kts: float
    wind_speed_kmh: float
    central_pressure_hpa: float
    pressure_drop_hpa: float
    nature_code: str
    imd_category: str        # 'D', 'DD', 'CS', 'SCS', 'VSCS', 'ESCS', 'SuCS'
    is_landfall: bool
    data_source: str
    quality_flag: str

class CycloneDataLoader:
    def load_dataset(self, csv_path: str = None) -> list[CycloneFix]: ...
    def get_storm_tracks(self) -> dict[str, list[CycloneFix]]: ...
    def get_data_quality_summary(self) -> dict: ...
```

### 2. ML Pipeline ↔ Section C
```python
@dataclass
class TrackEvaluation:
    horizon_hours: int
    test_storms: list[str]
    model_mte_km: float
    linear_persistence_mte_km: float
    cliper_mte_km: float
    skill_vs_persistence_pct: float
    num_eval_points: int

@dataclass
class IntensityEvaluation:
    horizon_hours: int
    test_storms: list[str]
    model_mae_kts: float
    persistence_mae_kts: float
    model_bias_kts: float
    num_eval_points: int

class CycloneMLPipeline:
    def train_and_evaluate(self) -> tuple[TrackEvaluation, IntensityEvaluation, dict]: ...
    def predict_track(self, storm_history: list[CycloneFix], horizon_hours: int) -> tuple[float, float, float]: ... # lat, lon, radius_km
```

### 3. Workflows & State Store ↔ Views
```python
@dataclass
class AlertRecord:
    id: str
    severity: str            # 'Watch', 'Warning', 'Severe', 'Extreme'
    region: str
    headline: str
    description: str
    evidence: str
    valid_until: str
    status: str              # 'Pending', 'Approved', 'Rejected', 'Changes Requested'
    reviewer_comments: str
    audit_history: list[dict] # [{'timestamp': str, 'action': str, 'actor': str, 'note': str}]

@dataclass
class CommunityReportRecord:
    id: str
    incident_time: str
    region: str
    category: str            # 'Flooding', 'Wind Damage', 'Storm Surge', 'Structural', 'Other'
    description: str
    status: str              # 'Submitted', 'Under Review', 'Verified', 'Rejected', 'Needs More Info'
    reviewer_notes: str
    has_photo: bool
    is_verified: bool
    timestamp: str

@dataclass
class ShelterRecord:
    id: str
    name: str
    district: str
    state: str
    latitude: float
    longitude: float
    capacity: int
    occupancy: int
    contact_phone: str
    is_accessible: bool
    source_label: str
```

---

## Code Layout & Conventions
- Base directory: `c:\Users\pc\OneDrive\Desktop\CHAKRAVAT`
- Primary stack: Python 3.14 + Streamlit, Plotly, Pandas, Scikit-learn
- Strict 100% offline air-gapped compatibility (no external font CDN, no external tile endpoints, no API keys)
- Dark palette base `#101820`, cards `#17222D`, border `#2D3F50`, accents Sky/Amber/Crimson
- Whitespace rule: max 3 cards/columns per row horizontally
- Dynamic metrics computation: NO hardcoding of evaluation metrics or probabilities
- Prominent experimental disclaimers on overview and prediction pages
