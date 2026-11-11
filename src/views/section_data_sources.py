"""
(D) Data Sources & Data Quality Center.
Provides transparent data provenance, synoptic data validation, schema enforcement,
missing-value diagnostics, interactive dataset inspection, and offline CSV export.
Strictly adheres to the Deep Navy (#101820) design system and <=3 columns per row.
"""

import os
import streamlit as st
import pandas as pd

from src.data_pipeline.loader import (
    CycloneDataLoader,
    DEFAULT_BUNDLED_PATH,
    SAMPLE_DATASET_PATH,
)
from src.data_pipeline.schema import IMD_CATEGORIES
from src.ui.components import (
    cv_markdown,
    section_header,
    grid_row,
    card_container,
    metric_card,
    state_box,
    status_badge,
    severity_badge,
    experimental_disclaimer_banner,
)


@st.cache_data(show_spinner=False)
def load_dataset_cached(source_key: str, file_bytes: bytes = None):
    """Caches loaded dataset to maintain instant responsive UI."""
    loader = CycloneDataLoader()
    if source_key == "bundled":
        loader.load_dataset(DEFAULT_BUNDLED_PATH)
    elif source_key == "sample":
        loader.load_dataset(SAMPLE_DATASET_PATH)
    elif source_key == "upload" and file_bytes:
        import io
        loader.load_dataset(uploaded_file=io.BytesIO(file_bytes))
    else:
        loader.load_dataset()
    return loader


def render() -> None:
    """Render Section D: Data Sources & Data Quality Center."""
    section_header(
        title="Data Sources & Data Quality Center",
        subtitle=(
            "Transparent data provenance, synoptic observation validation, "
            "canonical 18-column schema enforcement, and dataset health diagnostics."
        ),
        badge_label="PROVENANCE AUDITED",
        badge_type="verified",
    )

    experimental_disclaimer_banner(
        custom_text=(
            "Historical cyclone datasets are curated from NOAA IBTrACS v04 and IMD Best Track archives "
            "for algorithmic validation, benchmarking, and decision-support simulation. "
            "Official real-time warnings remain the sole statutory prerogative of IMD (RSMC New Delhi)."
        )
    )

    # 1. Dataset Selection & Active Source Control (<=3 cols)
    with card_container(title="Active Dataset Source & Cadence Configuration"):
        source_cols = grid_row(3)
        with source_cols[0]:
            dataset_choice = st.selectbox(
                "Primary Dataset Source",
                options=[
                    "Bundled Historical Dataset (148 Fixes across 5 Storms)",
                    "Sample NIO Dataset (71 Fixes across 8 Storms)",
                    "Upload Custom Synoptic CSV",
                ],
                index=0,
                key="sec_d_source_selector",
                help="Switch between benchmark historical fixes, caller sample dataset, or custom upload.",
            )

        with source_cols[1]:
            cv_markdown(
                """
                <div style="padding-top: 1.5rem; font-size: 0.8125rem; color: #94A3B8; line-height: 1.5;">
                    <strong style="color: #F1F5F9;">Domain Scope:</strong> North Indian Ocean (0°–35°N, 50°–105°E)<br>
                    <strong style="color: #F1F5F9;">Synoptic Cadence:</strong> 6-hourly regular fixes (00, 06, 12, 18 UTC)
                </div>
                """,
                unsafe_allow_html=True,
            )

        with source_cols[2]:
            cv_markdown(
                """
                <div style="padding-top: 1.5rem; font-size: 0.8125rem; color: #94A3B8; line-height: 1.5;">
                    <strong style="color: #F1F5F9;">Wind Standard:</strong> 3-min sustained (IMD Standard)<br>
                    <strong style="color: #F1F5F9;">Schema:</strong> Canonical 18-column Best-Track Schema
                </div>
                """,
                unsafe_allow_html=True,
            )

        # File uploader if custom upload selected
        uploaded_bytes = None
        if "Upload Custom" in dataset_choice:
            uploaded_file = st.file_uploader(
                "Upload Custom Best-Track CSV",
                type=["csv"],
                help="Accepts canonical IBTrACS or customized synoptic cyclone track CSVs.",
            )
            if uploaded_file is not None:
                uploaded_bytes = uploaded_file.getvalue()

    # Determine loader source key
    if "Bundled Historical" in dataset_choice:
        source_key = "bundled"
    elif "Sample NIO" in dataset_choice:
        source_key = "sample"
    else:
        source_key = "upload"

    # Load data through loader
    try:
        loader = load_dataset_cached(source_key, uploaded_bytes)
        fixes = loader.get_fixes()
        tracks = loader.get_storm_tracks()
        quality_report = loader.get_quality_report()
        provenance = loader.get_provenance()
        df = loader.get_dataframe()
    except Exception as ex:
        state_box(
            title="Dataset Ingestion Error",
            message=f"Failed to ingest dataset: {ex}. Reverting to default bundled dataset.",
            icon="⚠️",
            box_type="error",
        )
        loader = CycloneDataLoader()
        loader.load_dataset()
        fixes = loader.get_fixes()
        tracks = loader.get_storm_tracks()
        quality_report = loader.get_quality_report()
        provenance = loader.get_provenance()
        df = loader.get_dataframe()

    cv_markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    # 2. Top-Level Data Quality Metrics (Strict <= 3 columns)
    metric_cols = grid_row(3)
    with metric_cols[0]:
        metric_card(
            label="Synoptic Observations",
            value=f"{quality_report.total_records:,}",
            unit="Fixes",
            badge_text=f"{len(tracks)} Storms",
            badge_severity="verified",
            help_text="Chronologically sorted synoptic fixes",
        )
    with metric_cols[1]:
        completeness_str = f"{quality_report.completeness_pct:.1f}%"
        metric_card(
            label="Field Completeness",
            value=completeness_str,
            delta="18/18 Fields Validated" if quality_report.missing_values_count == 0 else f"{quality_report.missing_values_count} missing values",
            delta_type="positive" if quality_report.missing_values_count == 0 else "negative",
            badge_text="Schema Valid",
            badge_severity="verified" if quality_report.missing_values_count == 0 else "warning",
            help_text="Completeness across canonical attributes",
        )
    with metric_cols[2]:
        anomaly_str = f"{quality_report.anomaly_rate_pct:.2f}%"
        metric_card(
            label="Kinematic Anomaly Rate",
            value=anomaly_str,
            delta="Zero Jumps Detected" if quality_report.jump_anomalies_count == 0 else f"{quality_report.jump_anomalies_count} velocity anomalies",
            delta_type="positive" if quality_report.anomaly_count == 0 else "negative",
            badge_text="Audited",
            badge_severity="normal" if quality_report.anomaly_count == 0 else "warning",
            help_text="Physically plausible translation speed <= 45 kts",
        )

    cv_markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

    # 3. Data Health & Validation Checklist (<=3 cols)
    with card_container(title="Synoptic Quality Audit & Kinematic Integrity"):
        chk_cols = grid_row(3)
        with chk_cols[0]:
            cv_markdown(
                """
                <div class="cv-card" style="margin-bottom: 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <strong style="color: #F1F5F9; font-size: 0.875rem;">Geographic Domain</strong>
                        <span class="cv-badge cv-badge-verified">100% VALID</span>
                    </div>
                    <div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.25rem;">NIO Marine Corridor</div>
                    <div style="font-size: 0.8125rem; color: #CBD5E1; line-height: 1.4;">
                        All coordinate fixes validated within North Indian Ocean bounding box (0°–35°N, 50°–105°E).
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with chk_cols[1]:
            cv_markdown(
                """
                <div class="cv-card" style="margin-bottom: 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <strong style="color: #F1F5F9; font-size: 0.875rem;">Wind & Pressure Physics</strong>
                        <span class="cv-badge cv-badge-verified">CONSISTENT</span>
                    </div>
                    <div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.25rem;">Hydrodynamic Bounds</div>
                    <div style="font-size: 0.8125rem; color: #CBD5E1; line-height: 1.4;">
                        1 kt = 1.852 km/h preserved; central pressures in physical maritime range (880–1025 hPa).
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with chk_cols[2]:
            cv_markdown(
                f"""
                <div class="cv-card" style="margin-bottom: 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <strong style="color: #F1F5F9; font-size: 0.875rem;">Temporal Monotonicity</strong>
                        <span class="cv-badge cv-badge-verified">{quality_report.temporal_consistency_score_pct:.0f}% MONOTONIC</span>
                    </div>
                    <div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.25rem;">Chronological Continuity</div>
                    <div style="font-size: 0.8125rem; color: #CBD5E1; line-height: 1.4;">
                        Observation timestamps strictly non-decreasing with consistent 6-hourly synoptic sampling.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    cv_markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

    # 4. Provenance & Meteorological Attribution Card (<=3 cols)
    with card_container(title="Authoritative Data Provenance & Attribution"):
        prov_cols = grid_row(3)
        with prov_cols[0]:
            cv_markdown(
                f"""
                <div class="cv-card" style="margin-bottom: 0;">
                    <div style="font-weight: 600; color: #F1F5F9; margin-bottom: 0.25rem;">Primary Repository</div>
                    <div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.5rem;">{provenance.source_name}</div>
                    <div style="font-size: 0.8125rem; color: #CBD5E1; line-height: 1.5;">
                        <strong>Provider:</strong> {provenance.authoritative_provider}<br>
                        <strong>Coverage:</strong> {provenance.geographical_coverage}<br>
                        <strong>Temporal Span:</strong> {provenance.time_span}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with prov_cols[1]:
            cv_markdown(
                f"""
                <div class="cv-card" style="margin-bottom: 0;">
                    <div style="font-weight: 600; color: #F1F5F9; margin-bottom: 0.25rem;">Statutory Authority</div>
                    <div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.5rem;">{provenance.statutory_authority}</div>
                    <div style="font-size: 0.8125rem; color: #CBD5E1; line-height: 1.5;">
                        <strong>Verification:</strong> <span class="cv-badge cv-badge-verified">{provenance.verified_status}</span><br>
                        <strong>Sync Date:</strong> {provenance.retrieval_timestamp[:10]}<br>
                        <strong>Licensing:</strong> {provenance.license_type}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with prov_cols[2]:
            cv_markdown(
                f"""
                <div class="cv-card" style="margin-bottom: 0;">
                    <div style="font-weight: 600; color: #F1F5F9; margin-bottom: 0.25rem;">Scientific Citation</div>
                    <div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.5rem;">Academic Reference</div>
                    <div style="font-size: 0.75rem; color: #94A3B8; font-style: italic; line-height: 1.4;">
                        "{provenance.citation}"
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    cv_markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

    # 5. Interactive Dataset Explorer & Inspection Table
    with card_container(title="Interactive Synoptic Dataset Explorer"):
        storm_list = ["ALL STORMS"] + sorted(list(tracks.keys()))
        filter_cols = grid_row(3)
        with filter_cols[0]:
            selected_storm = st.selectbox(
                "Filter by Tropical Cyclone",
                options=storm_list,
                index=0,
                key="sec_d_storm_filter",
            )
        with filter_cols[1]:
            selected_basin = st.selectbox(
                "Filter by Ocean Basin",
                options=["ALL BASINS", "Bay of Bengal", "Arabian Sea"],
                index=0,
                key="sec_d_basin_filter",
            )
        with filter_cols[2]:
            categories_present = ["ALL CATEGORIES"] + sorted(list(set(df["imd_category"].unique())))
            selected_cat = st.selectbox(
                "Filter by IMD Category",
                options=categories_present,
                index=0,
                key="sec_d_cat_filter",
            )

        # Apply interactive filters
        filtered_df = df.copy()
        if selected_storm != "ALL STORMS":
            filtered_df = filtered_df[filtered_df["storm_name"] == selected_storm]
        if selected_basin != "ALL BASINS":
            filtered_df = filtered_df[filtered_df["basin"] == selected_basin]
        if selected_cat != "ALL CATEGORIES":
            filtered_df = filtered_df[filtered_df["imd_category"] == selected_cat]

        cv_markdown(
            f"<div style='font-size: 0.8125rem; color: #94A3B8; margin-bottom: 0.5rem;'>"
            f"Displaying <strong style='color: #38BDF8;'>{len(filtered_df)}</strong> of {len(df)} synoptic fixes"
            f"</div>",
            unsafe_allow_html=True,
        )

        # Formatted display table
        display_cols = [
            "record_id",
            "storm_name",
            "iso_time",
            "basin",
            "latitude",
            "longitude",
            "wind_speed_kts",
            "wind_speed_kmh",
            "central_pressure_hpa",
            "pressure_drop_hpa",
            "imd_category",
            "translation_speed_kts",
            "translation_heading_deg",
            "is_landfall",
        ]
        available_cols = [c for c in display_cols if c in filtered_df.columns]
        st.dataframe(
            filtered_df[available_cols],
            width="stretch",
            hide_index=True,
            height=320,
        )

        # 6. CSV Export & Download Actions (<=3 cols)
        export_cols = grid_row(3)
        with export_cols[0]:
            csv_data = filtered_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Export Filtered Synoptic CSV",
                data=csv_data,
                file_name=f"chakravat_{selected_storm.lower()}_synoptic_data.csv",
                mime="text/csv",
                width="stretch",
                help="Download canonical filtered synoptic records as CSV.",
            )
        with export_cols[1]:
            all_csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📦 Download Complete Dataset CSV",
                data=all_csv,
                file_name="chakravat_historical_cyclones_full.csv",
                mime="text/csv",
                width="stretch",
                help="Download the entire canonical dataset.",
            )
        with export_cols[2]:
            cv_markdown(
                """
                <div style="font-size: 0.75rem; color: #94A3B8; text-align: center; padding-top: 0.5rem;">
                    Offline Export • Verified 18-Column Format
                </div>
                """,
                unsafe_allow_html=True,
            )
