"""(I) About & Methodology Section View.

Comprehensive scientific documentation for the CHAKRAVAT platform:
- Platform mission and 4-tier decoupled system architecture.
- Data provenance and attribution (IMD RSMC New Delhi, NOAA IBTrACS v04, WMO GTS).
- Rigorous machine learning methodology:
  * Strict storm-level train/test splitting (zero autocorrelation leakage).
  * Linear Persistence and NIO CLIPER baselines.
  * Dynamic Haversine Great-Circle error calculation.
  * Empirical 70th-percentile error uncertainty cones vs arbitrary geometric cones.
- Scientific limitations, model failure modes, and data-limited boundaries.
- Responsible use and statutory ethics policy (IMD sole warning authority).
"""

from typing import Any, Dict, List
import streamlit as st

from src.ui.components import (
    cv_markdown,
    section_header,
    experimental_disclaimer_banner,
    card_container,
    metric_card,
    grid_row,
    severity_badge,
    status_badge,
)
from src.ui.state import set_current_section


def render() -> None:
    """Render Section I: About & Methodology."""
    # Standard Section Header Bar
    section_header(
        title="About & Scientific Methodology",
        subtitle="Platform architecture, meteorological data provenance, zero-leakage machine learning methodology, and responsible operational use charter.",
        badge_label="SCIENTIFIC METHODOLOGY",
        badge_type="experimental",
    )

    # Mandatory Prominent Statutory Experimental Disclaimer
    experimental_disclaimer_banner(
        "<strong>⚠️ RESEARCH PROTOTYPE — NOT AN OFFICIAL METEOROLOGICAL WARNING SERVICE</strong><br>"
        "CHAKRAVAT is an experimental research decision-support prototype. It does NOT issue official cyclone warnings, "
        "storm surge alerts, or evacuation orders. Under the Disaster Management Act (2005) and WMO conventions, the "
        "<strong>India Meteorological Department (IMD / RSMC New Delhi)</strong> is the sole statutory authority for "
        "tropical cyclone forecasting in the North Indian Ocean. For life-safety decisions, refer exclusively to "
        "<a href='https://rsmcnewdelhi.imd.gov.in' target='_blank' style='color: #38BDF8; text-decoration: underline; font-weight: 600;'>"
        "rsmcnewdelhi.imd.gov.in</a>."
    )

    # 5 Detailed Thematic Tabs
    tabs = st.tabs([
        "🏛️ Platform Mission & Architecture",
        "🛰️ Data Provenance & Attribution",
        "🧠 Machine Learning Methodology",
        "⚠️ Limitations & Failure Modes",
        "📜 Responsible Use & Statutory Mandate",
    ])

    # =========================================================================
    # TAB 1: Mission & Architecture
    # =========================================================================
    with tabs[0]:
        cv_markdown(
            """
            <div style="font-size: 1.125rem; font-weight: 700; color: #F1F5F9; margin-bottom: 0.5rem;">
                Platform Mission & Regional Context
            </div>
            <div style="font-size: 0.875rem; color: #CBD5E1; line-height: 1.65; margin-bottom: 1.25rem;">
                The <strong>North Indian Ocean (NIO)</strong> basin — encompassing the Bay of Bengal and the Arabian Sea — accounts 
                for approximately 7% of the world’s tropical cyclones, yet historically suffers over <strong>70% of global cyclone-induced fatalities</strong>. 
                This vulnerability stems from shallow bathymetry, astronomical tidal ranges, concave coastline geometry (such as the Odisha-Bengal arc), 
                and dense coastal populations.
                <br><br>
                <strong>CHAKRAVAT</strong> was engineered as an advanced decision-support prototype bridging modern data science with 
                strict operational meteorological practices. It provides researchers, emergency managers, and civil protection teams 
                with an auditable, transparent environment to evaluate cyclone tracking, ML prediction, and disaster coordination workflows.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 3 Architectural Pillar Cards (Max 3 columns)
        cv_markdown(
            "<span style='font-size: 0.75rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em;'>"
            "Modular 4-Tier Architecture Overview"
            "</span>",
            unsafe_allow_html=True,
        )
        arch_cols = grid_row(3)

        with arch_cols[0]:
            cv_markdown(
                """
                <div class="cv-card" style="height: 100%;">
                    <div style="font-size: 0.9375rem; font-weight: 700; color: #38BDF8; margin-bottom: 0.4rem;">
                        1. Ingestion & Provenance
                    </div>
                    <div style="font-size: 0.8125rem; color: #CBD5E1; line-height: 1.55;">
                        • IBTrACS v04r00 & IMD Best Track archives.<br>
                        • 18-column canonical schema validation.<br>
                        • Offline bundled historical synoptic fixes.<br>
                        • Physical sanity bounds checking (pressure, wind).
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with arch_cols[1]:
            cv_markdown(
                """
                <div class="cv-card" style="height: 100%;">
                    <div style="font-size: 0.9375rem; font-weight: 700; color: #A78BFA; margin-bottom: 0.4rem;">
                        2. ML & Baseline Engine
                    </div>
                    <div style="font-size: 0.8125rem; color: #CBD5E1; line-height: 1.55;">
                        • Strict storm-level group splitting.<br>
                        • Linear Persistence & NIO CLIPER baselines.<br>
                        • Dynamic Great-Circle Haversine error.<br>
                        • Empirical 70th-percentile uncertainty cones.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with arch_cols[2]:
            cv_markdown(
                """
                <div class="cv-card" style="height: 100%;">
                    <div style="font-size: 0.9375rem; font-weight: 700; color: #34D399; margin-bottom: 0.4rem;">
                        3. Response & Coordination
                    </div>
                    <div style="font-size: 0.8125rem; color: #CBD5E1; line-height: 1.55;">
                        • Human-in-the-loop alert verification.<br>
                        • Crowdsourced report triage desk.<br>
                        • Coastal shelter directory & capacity routing.<br>
                        • Air-gapped Plotly vector mapping basemap.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        cv_markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        with card_container(title="Engineering Specifications"):
            cv_markdown(
                """
                <table class="cv-timeline-table">
                    <thead>
                        <tr>
                            <th>Subsystem</th>
                            <th>Implementation Technology</th>
                            <th>Design Guarantee</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="color: #38BDF8; font-weight: 600;">Presentation Layer</td>
                            <td>Streamlit, Custom CSS (#101820 base)</td>
                            <td>Strict whitespace discipline (max 3 cards/row), responsive tabular monospace fonts.</td>
                        </tr>
                        <tr>
                            <td style="color: #38BDF8; font-weight: 600;">Geospatial Canvas</td>
                            <td>Plotly Graph Objects (Scattergeo)</td>
                            <td>100% offline air-gapped operation; no external map tile CDN or API token requirements.</td>
                        </tr>
                        <tr>
                            <td style="color: #38BDF8; font-weight: 600;">State Engine</td>
                            <td>In-Memory Session State Store</td>
                            <td>Deterministic demo lifecycle, timestamped audit history, multi-tab coordination.</td>
                        </tr>
                        <tr>
                            <td style="color: #38BDF8; font-weight: 600;">Data Contracts</td>
                            <td>Python dataclasses & strict schema typing</td>
                            <td>Zero raw stack traces; structured empty and data-limited fallback states.</td>
                        </tr>
                    </tbody>
                </table>
                """,
                unsafe_allow_html=True,
            )

    # =========================================================================
    # TAB 2: Data Provenance & Attribution
    # =========================================================================
    with tabs[1]:
        cv_markdown(
            """
            <div style="font-size: 1.125rem; font-weight: 700; color: #F1F5F9; margin-bottom: 0.5rem;">
                Meteorological Data Provenance & Institutional Attribution
            </div>
            <div style="font-size: 0.875rem; color: #CBD5E1; line-height: 1.65; margin-bottom: 1.25rem;">
                Scientific credibility mandates total transparency regarding the origins, observational cadence, 
                and limitations of meteorological data. CHAKRAVAT ingests and validates historical best-track datasets 
                conforming to World Meteorological Organization (WMO) standards.
            </div>
            """,
            unsafe_allow_html=True,
        )

        prov_cols = grid_row(3)

        with prov_cols[0]:
            cv_markdown(
                """
                <div class="cv-card" style="height: 100%;">
                    <div style="font-size: 0.75rem; font-weight: 700; color: #38BDF8; text-transform: uppercase;">Primary Authority</div>
                    <div style="font-size: 1rem; font-weight: 700; color: #F1F5F9; margin: 0.25rem 0;">IMD RSMC New Delhi</div>
                    <div style="font-size: 0.8125rem; color: #CBD5E1; line-height: 1.55;">
                        Official WMO Regional Specialized Meteorological Centre for Tropical Cyclones over the North Indian Ocean. 
                        Source of best-track reanalyses, radar telemetry, and 8-tier classification standards.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with prov_cols[1]:
            cv_markdown(
                """
                <div class="cv-card" style="height: 100%;">
                    <div style="font-size: 0.75rem; font-weight: 700; color: #A78BFA; text-transform: uppercase;">Global Archive</div>
                    <div style="font-size: 1rem; font-weight: 700; color: #F1F5F9; margin: 0.25rem 0;">NOAA IBTrACS v04</div>
                    <div style="font-size: 0.8125rem; color: #CBD5E1; line-height: 1.55;">
                        International Best Track Archive for Climate Stewardship (NOAA NCEI). Provides standardized 3-hourly 
                        and 6-hourly synoptic fixes, storm identifiers, central pressure, and maximum sustained winds.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with prov_cols[2]:
            cv_markdown(
                """
                <div class="cv-card" style="height: 100%;">
                    <div style="font-size: 0.75rem; font-weight: 700; color: #34D399; text-transform: uppercase;">Domain Coverage</div>
                    <div style="font-size: 1rem; font-weight: 700; color: #F1F5F9; margin: 0.25rem 0;">NIO Basin Bounds</div>
                    <div style="font-size: 0.8125rem; color: #CBD5E1; line-height: 1.55;">
                        Geographic envelope: 0.0°N to 35.0°N, 50.0°E to 105.0°E. 
                        Includes the Bay of Bengal, Andaman Sea, Arabian Sea, and coastal land sectors of the Indian subcontinent.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        cv_markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        with card_container(title="IMD 8-Tier Classification Scale Reference (RSMC New Delhi)"):
            cv_markdown(
                """
                <div style="font-size: 0.8125rem; color: #CBD5E1; margin-bottom: 0.75rem;">
                    The India Meteorological Department classifies tropical cyclonic disturbances based on 3-minute maximum sustained surface wind speed (MSW):
                </div>
                <table class="cv-timeline-table">
                    <thead>
                        <tr>
                            <th>Code</th>
                            <th>Classification Name</th>
                            <th>Wind Speed (Knots)</th>
                            <th>Wind Speed (km/h)</th>
                            <th>Central Pressure Drop</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><span class="cv-badge cv-badge-normal">LPA</span></td>
                            <td style="color: #F1F5F9;">Low Pressure Area</td>
                            <td class="cv-mono">&lt; 17 kts</td>
                            <td class="cv-mono">&lt; 31 km/h</td>
                            <td class="cv-mono">&lt; 1.0 hPa</td>
                        </tr>
                        <tr>
                            <td><span class="cv-badge cv-badge-normal">D</span></td>
                            <td style="color: #F1F5F9;">Depression</td>
                            <td class="cv-mono">17 – 27 kts</td>
                            <td class="cv-mono">31 – 49 km/h</td>
                            <td class="cv-mono">1.0 – 2.0 hPa</td>
                        </tr>
                        <tr>
                            <td><span class="cv-badge cv-badge-normal">DD</span></td>
                            <td style="color: #F1F5F9;">Deep Depression</td>
                            <td class="cv-mono">28 – 33 kts</td>
                            <td class="cv-mono">50 – 61 km/h</td>
                            <td class="cv-mono">2.1 – 4.4 hPa</td>
                        </tr>
                        <tr>
                            <td><span class="cv-badge cv-badge-advisory">CS</span></td>
                            <td style="color: #F1F5F9;">Cyclonic Storm</td>
                            <td class="cv-mono">34 – 47 kts</td>
                            <td class="cv-mono">62 – 88 km/h</td>
                            <td class="cv-mono">4.5 – 8.4 hPa</td>
                        </tr>
                        <tr>
                            <td><span class="cv-badge cv-badge-warning">SCS</span></td>
                            <td style="color: #F1F5F9;">Severe Cyclonic Storm</td>
                            <td class="cv-mono">48 – 63 kts</td>
                            <td class="cv-mono">89 – 117 km/h</td>
                            <td class="cv-mono">8.5 – 15.4 hPa</td>
                        </tr>
                        <tr>
                            <td><span class="cv-badge cv-badge-extreme">VSCS</span></td>
                            <td style="color: #F1F5F9;">Very Severe Cyclonic Storm</td>
                            <td class="cv-mono">64 – 89 kts</td>
                            <td class="cv-mono">118 – 166 km/h</td>
                            <td class="cv-mono">15.5 – 35.4 hPa</td>
                        </tr>
                        <tr>
                            <td><span class="cv-badge cv-badge-extreme">ESCS</span></td>
                            <td style="color: #F1F5F9;">Extremely Severe Cyclonic Storm</td>
                            <td class="cv-mono">90 – 119 kts</td>
                            <td class="cv-mono">167 – 221 km/h</td>
                            <td class="cv-mono">35.5 – 65.4 hPa</td>
                        </tr>
                        <tr>
                            <td><span class="cv-badge cv-badge-extreme" style="background-color: rgba(248, 113, 113, 0.35);">SuCS</span></td>
                            <td style="color: #F1F5F9; font-weight: 700;">Super Cyclonic Storm</td>
                            <td class="cv-mono">&ge; 120 kts</td>
                            <td class="cv-mono">&ge; 222 km/h</td>
                            <td class="cv-mono">&ge; 65.5 hPa</td>
                        </tr>
                    </tbody>
                </table>
                """,
                unsafe_allow_html=True,
            )

    # =========================================================================
    # TAB 3: Machine Learning Methodology
    # =========================================================================
    with tabs[2]:
        cv_markdown(
            """
            <div style="font-size: 1.125rem; font-weight: 700; color: #F1F5F9; margin-bottom: 0.5rem;">
                Scientific Machine Learning Methodology & Baselines
            </div>
            <div style="font-size: 0.875rem; color: #CBD5E1; line-height: 1.65; margin-bottom: 1.25rem;">
                A cornerstone of CHAKRAVAT is uncompromising adherence to scientific integrity. Many machine learning 
                demonstrators make critical statistical errors that produce artificially inflated performance metrics. 
                Below is an explanation of the core principles implemented in our modeling pipeline.
            </div>
            """,
            unsafe_allow_html=True,
        )

        with card_container(title="1. Storm-Level Train/Test Splitting (Zero Autocorrelation Leakage)"):
            cv_markdown(
                """
                <div style="font-size: 0.875rem; color: #CBD5E1; line-height: 1.65;">
                    <strong style="color: #F87171;">The Catastrophic Pitfall: Observation-Level Splitting</strong><br>
                    In tropical cyclone best-track records, observations are spaced at 3-hour or 6-hour synoptic intervals. 
                    Consecutive track fixes within a single storm (e.g. Cyclone Fani at 06:00 UTC and 12:00 UTC) possess an extreme 
                    degree of temporal and spatial autocorrelation (<span class="cv-mono">ρ > 0.98</span>).
                    <br><br>
                    If a model is trained using standard random K-fold cross-validation or uniform train/test splits, fixes from 
                    <em>the same storm</em> inevitably appear in both the training set and the test set. The model is not learning 
                    atmospheric steering dynamics or pressure gradient forces; it is simply interpolating between points of an already-seen track. 
                    In academic literature, this is known as <strong>autocorrelation leakage</strong>.
                    <br><br>
                    <strong style="color: #34D399;">The CHAKRAVAT Solution: Grouped Storm Partitioning</strong><br>
                    CHAKRAVAT strictly implements <strong>Storm-Level Group Splitting</strong>. All observations belonging to a given 
                    storm (from genesis to final dissipation) are allocated entirely to either the training set OR the held-out test set. 
                    The model is evaluated purely on unseen storms whose lifecycles occurred independently, mirroring real operational deployment.
                </div>
                """,
                unsafe_allow_html=True,
            )

        cv_markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        with card_container(title="2. Operational Baseline Benchmarks (Persistence & NIO CLIPER)"):
            cv_markdown(
                """
                <div style="font-size: 0.875rem; color: #CBD5E1; line-height: 1.65;">
                    In operational meteorology, a complex machine learning model has zero scientific value unless it demonstrates 
                    measurable skill over standard reference baselines:
                    <br><br>
                    <strong>A. Linear Persistence Baseline (PER)</strong><br>
                    Assumes the cyclone will continue moving along its recent velocity vector calculated from the preceding 12 hours:
                </div>
                <div style="background-color: #1E2D3B; padding: 0.75rem 1rem; border-radius: 6px; margin: 0.5rem 0; font-family: monospace; color: #38BDF8; font-size: 0.875rem;">
                    x̂(t + τ) = x(t) + [ (x(t) - x(t - 12h)) / 12h ] × τ
                </div>
                <div style="font-size: 0.875rem; color: #CBD5E1; line-height: 1.65;">
                    <strong>B. NIO CLIPER (Climatology and Persistence)</strong><br>
                    Combines the linear persistence vector with historical climatological mean displacement vectors for the North Indian Ocean basin, 
                    weighted by initial position, translation speed, direction, and calendar month.
                    <br><br>
                    <strong>C. Trend Intensity Persistence</strong><br>
                    Extrapolates central pressure and sustained wind deltas from the preceding synoptic fixes:
                </div>
                <div style="background-color: #1E2D3B; padding: 0.75rem 1rem; border-radius: 6px; margin: 0.5rem 0; font-family: monospace; color: #38BDF8; font-size: 0.875rem;">
                    V̂(t + τ) = V(t) + τ × [ (V(t) - V(t - 12h)) / 12 ]
                </div>
                """,
                unsafe_allow_html=True,
            )

        cv_markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        method_cols = grid_row(2)

        with method_cols[0]:
            with card_container(title="3. Dynamic Haversine Great-Circle Error"):
                cv_markdown(
                    """
                    <div style="font-size: 0.8125rem; color: #CBD5E1; line-height: 1.6;">
                        Planar Euclidean approximations (<span class="cv-mono">√(Δx² + Δy²)</span>) are invalid across spherical 
                        coordinates due to longitude convergence at higher latitudes. CHAKRAVAT computes genuine Great-Circle distances:
                    </div>
                    <div style="background-color: #1E2D3B; padding: 0.6rem 0.8rem; border-radius: 6px; margin: 0.5rem 0; font-family: monospace; color: #38BDF8; font-size: 0.8125rem;">
                        a = sin²(Δφ/2) + cos(φ₁)cos(φ₂)sin²(Δλ/2)<br>
                        d = 2 · R · arcsin(√a)<br>
                        where R = 6,371.0 km
                    </div>
                    <div style="font-size: 0.8125rem; color: #CBD5E1; line-height: 1.6;">
                        Mean Track Error (MTE) at forecast horizon τ is the mean Haversine separation between predicted and actual coordinates:
                    </div>
                    <div style="background-color: #1E2D3B; padding: 0.6rem 0.8rem; border-radius: 6px; margin: 0.5rem 0; font-family: monospace; color: #A78BFA; font-size: 0.8125rem;">
                        MTE(τ) = (1/N) ∑ d( x̂ᵢ(τ), xᵢ(τ) )
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with method_cols[1]:
            with card_container(title="4. Empirical 70% Uncertainty Cones"):
                cv_markdown(
                    """
                    <div style="font-size: 0.8125rem; color: #CBD5E1; line-height: 1.6;">
                        Commercial weather apps frequently draw arbitrary geometric cones (e.g. expanding circle ±50 km/day) without statistical backing.
                        <br><br>
                        CHAKRAVAT adheres to the <strong>WMO/IMD operational standard</strong>: the uncertainty cone radius <span class="cv-mono">R₇₀(τ)</span> 
                        at each lead time (12h, 24h, 36h, 48h) is calculated as the <strong>empirical 70th percentile</strong> of historical track errors on 
                        held-out validation storms:
                    </div>
                    <div style="background-color: #1E2D3B; padding: 0.6rem 0.8rem; border-radius: 6px; margin: 0.5rem 0; font-family: monospace; color: #34D399; font-size: 0.8125rem;">
                        P( d(x̂, x) ≤ R₇₀(τ) ) = 0.70
                    </div>
                    <div style="font-size: 0.8125rem; color: #CBD5E1; line-height: 1.6;">
                        This means the physical center of the cyclone is statistically expected to remain within the cone exactly 70% of the time, 
                        with 30% of actual centers expected outside the boundary.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # =========================================================================
    # TAB 4: Limitations & Failure Modes
    # =========================================================================
    with tabs[3]:
        cv_markdown(
            """
            <div style="font-size: 1.125rem; font-weight: 700; color: #F1F5F9; margin-bottom: 0.5rem;">
                Scientific Limitations & Model Failure Modes
            </div>
            <div style="font-size: 0.875rem; color: #CBD5E1; line-height: 1.65; margin-bottom: 1.25rem;">
                No meteorological predictive model is infallible. In high-consequence emergency environments, understanding when 
                and why an algorithmic model will fail is as critical as knowing its average accuracy.
            </div>
            """,
            unsafe_allow_html=True,
        )

        lim_cols = grid_row(3)

        with lim_cols[0]:
            cv_markdown(
                """
                <div class="cv-card" style="height: 100%;">
                    <div style="font-size: 0.75rem; font-weight: 700; color: #F87171; text-transform: uppercase;">Failure Mode 1</div>
                    <div style="font-size: 1rem; font-weight: 700; color: #F1F5F9; margin: 0.25rem 0;">Rapid Intensification (RI)</div>
                    <div style="font-size: 0.8125rem; color: #CBD5E1; line-height: 1.55;">
                        Defined as wind speed increase of &ge; 30 kts in 24 hours. Statistical models often fail to capture sudden convective 
                        bursts driven by ocean heat content spikes, under-predicting peak intensity prior to landfall.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with lim_cols[1]:
            cv_markdown(
                """
                <div class="cv-card" style="height: 100%;">
                    <div style="font-size: 0.75rem; font-weight: 700; color: #FB923C; text-transform: uppercase;">Failure Mode 2</div>
                    <div style="font-size: 1rem; font-weight: 700; color: #F1F5F9; margin: 0.25rem 0;">Landfall Topography Friction</div>
                    <div style="font-size: 0.8125rem; color: #CBD5E1; line-height: 1.55;">
                        Continental boundary layer interaction causes non-linear deceleration and asymmetric core collapse. 
                        Kinematic persistence models may over-estimate inland forward penetration after coastal boundary crossing.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with lim_cols[2]:
            cv_markdown(
                """
                <div class="cv-card" style="height: 100%;">
                    <div style="font-size: 0.75rem; font-weight: 700; color: #FBBF24; text-transform: uppercase;">Failure Mode 3</div>
                    <div style="font-size: 1rem; font-weight: 700; color: #F1F5F9; margin: 0.25rem 0;">Observational Sparsity</div>
                    <div style="font-size: 0.8125rem; color: #CBD5E1; line-height: 1.55;">
                        The NIO has no routine hurricane hunter aircraft reconnaissance. Satellite Dvorak estimates have inherent 
                        &plusmn;5–10 kt uncertainty. When fixes are missing, CHAKRAVAT invokes a structured data-limited state.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        cv_markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        with card_container(title="Data-Limited Boundary Handling"):
            cv_markdown(
                """
                <div style="font-size: 0.875rem; color: #CBD5E1; line-height: 1.65;">
                    When observational inputs have fewer than 3 chronological synoptic fixes, or when sensor latency exceeds 18 hours, 
                    CHAKRAVAT deliberately suspends automated ML inference and renders a styled <strong>DATA-LIMITED STATE</strong>. 
                    We reject the practice of synthesizing fake track fixes or hallucinating telemetry to fill interface blanks.
                </div>
                """,
                unsafe_allow_html=True,
            )

    # =========================================================================
    # TAB 5: Responsible Use & Statutory Mandate
    # =========================================================================
    with tabs[4]:
        cv_markdown(
            """
            <div style="font-size: 1.125rem; font-weight: 700; color: #F1F5F9; margin-bottom: 0.5rem;">
                Responsible Use Charter & Statutory Warnings Mandate
            </div>
            <div style="font-size: 0.875rem; color: #CBD5E1; line-height: 1.65; margin-bottom: 1.25rem;">
                Operational disaster management is a high-consequence domain where unvetted algorithmic output can result in loss 
                of life or misallocation of emergency relief resources. This charter sets forth the strict ethical and legal boundaries 
                under which CHAKRAVAT operates.
            </div>
            """,
            unsafe_allow_html=True,
        )

        with card_container(title="Statutory Role of the India Meteorological Department (IMD)"):
            cv_markdown(
                """
                <div style="font-size: 0.875rem; color: #CBD5E1; line-height: 1.65;">
                    Under the <strong>Disaster Management Act, 2005 (Government of India)</strong> and the international 
                    regulations of the <strong>World Meteorological Organization (WMO)</strong>, the <strong>India Meteorological Department 
                    (RSMC New Delhi)</strong> is the sole authorized agency responsible for:
                    <br><br>
                    1. Issuing official Cyclone Watches, Alerts, Warnings, and Post-Landfall Outlooks for the Indian coastline.<br>
                    2. Hoisting recognized port warning signals (Signals 1 through 11) for commercial and maritime vessels.<br>
                    3. Providing official track cones, landfall point estimates, and storm surge inundation heights to the National Disaster Management Authority (NDMA) and State Disaster Management Authorities (SDMAs).
                    <br><br>
                    <span style="color: #F87171; font-weight: 600;">
                        No private algorithm, academic prototype, or commercial platform has legal standing to issue public cyclone warnings or evacuation mandates in the Indian territorial domain.
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        cv_markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        ethics_cols = grid_row(2)

        with ethics_cols[0]:
            with card_container(title="Human-in-the-Loop Safeguards"):
                cv_markdown(
                    """
                    <div style="font-size: 0.8125rem; color: #CBD5E1; line-height: 1.6;">
                        • <strong>Quarantine Workflow:</strong> All automated triggers generate alerts in a quarantined <span class="cv-badge cv-badge-advisory">Pending</span> state. No advisory is published without human forecaster authorization.<br><br>
                        • <strong>Immutable Audit Trail:</strong> Every approval, modification, or rejection is logged with UTC timestamps, reviewer identity, and operational rationale.<br><br>
                        • <strong>Citizen Verification:</strong> Unverified field reports carry mandatory warning banners to prevent panic.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with ethics_cols[1]:
            with card_container(title="Official Emergency Directory"):
                cv_markdown(
                    """
                    <div style="font-size: 0.8125rem; color: #CBD5E1; line-height: 1.6;">
                        For genuine emergency warnings and evacuation instructions, consult:<br><br>
                        • <strong>IMD RSMC New Delhi:</strong> <a href="https://rsmcnewdelhi.imd.gov.in" target="_blank" style="color: #38BDF8;">rsmcnewdelhi.imd.gov.in</a><br>
                        • <strong>National Disaster Management Authority:</strong> <a href="https://ndma.gov.in" target="_blank" style="color: #38BDF8;">ndma.gov.in</a><br>
                        • <strong>INCOIS Ocean State Services:</strong> <a href="https://incois.gov.in" target="_blank" style="color: #38BDF8;">incois.gov.in</a><br>
                        • <strong>National Emergency Helpline:</strong> <span class="cv-mono" style="color: #34D399; font-weight: 700;">1070 / 112</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
