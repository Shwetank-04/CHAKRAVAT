"""CHAKRAVAT UI Design System Theme & Custom CSS Definitions.

Strictly offline-resilient, native system font stack, deep navy/charcoal base palette (#101820).
"""

from typing import Final, Dict

# Core Color Tokens
COLOR_TOKENS: Final[Dict[str, str]] = {
    "bg_base": "#101820",
    "surface_card": "#17222D",
    "surface_elevated": "#1E2D3B",
    "surface_hover": "#253748",
    "border_subtle": "#1E2D3B",
    "border_default": "#2C4056",
    "border_focus": "#38BDF8",
    "text_primary": "#F1F5F9",
    "text_secondary": "#CBD5E1",
    "text_muted": "#94A3B8",
    "text_disabled": "#64748B",
    "accent_primary": "#38BDF8",
    "accent_amber": "#FBBF24",
    "accent_orange": "#FB923C",
    "accent_crimson": "#F87171",
    "accent_emerald": "#34D399",
    "accent_violet": "#A78BFA",
}

# Semantic Severity Palette
SEVERITY_COLORS: Final[Dict[str, Dict[str, str]]] = {
    "normal": {
        "text": "#38BDF8",
        "bg": "rgba(56, 189, 248, 0.12)",
        "border": "rgba(56, 189, 248, 0.35)",
    },
    "watch": {
        "text": "#38BDF8",
        "bg": "rgba(56, 189, 248, 0.12)",
        "border": "rgba(56, 189, 248, 0.35)",
    },
    "advisory": {
        "text": "#FBBF24",
        "bg": "rgba(251, 191, 36, 0.12)",
        "border": "rgba(251, 191, 36, 0.35)",
    },
    "moderate": {
        "text": "#FBBF24",
        "bg": "rgba(251, 191, 36, 0.12)",
        "border": "rgba(251, 191, 36, 0.35)",
    },
    "warning": {
        "text": "#FB923C",
        "bg": "rgba(251, 146, 60, 0.12)",
        "border": "rgba(251, 146, 60, 0.35)",
    },
    "severe": {
        "text": "#FB923C",
        "bg": "rgba(251, 146, 60, 0.12)",
        "border": "rgba(251, 146, 60, 0.35)",
    },
    "extreme": {
        "text": "#F87171",
        "bg": "rgba(248, 113, 113, 0.15)",
        "border": "rgba(248, 113, 113, 0.40)",
    },
    "danger": {
        "text": "#F87171",
        "bg": "rgba(248, 113, 113, 0.15)",
        "border": "rgba(248, 113, 113, 0.40)",
    },
    "verified": {
        "text": "#34D399",
        "bg": "rgba(52, 211, 153, 0.12)",
        "border": "rgba(52, 211, 153, 0.35)",
    },
    "experimental": {
        "text": "#A78BFA",
        "bg": "rgba(167, 139, 250, 0.12)",
        "border": "rgba(167, 139, 250, 0.35)",
    },
}

STATUS_COLORS: Final[Dict[str, Dict[str, str]]] = {
    "pending": {
        "text": "#FBBF24",
        "bg": "rgba(251, 191, 36, 0.12)",
        "border": "rgba(251, 191, 36, 0.35)",
    },
    "submitted": {
        "text": "#FBBF24",
        "bg": "rgba(251, 191, 36, 0.12)",
        "border": "rgba(251, 191, 36, 0.35)",
    },
    "under review": {
        "text": "#38BDF8",
        "bg": "rgba(56, 189, 248, 0.12)",
        "border": "rgba(56, 189, 248, 0.35)",
    },
    "under_review": {
        "text": "#38BDF8",
        "bg": "rgba(56, 189, 248, 0.12)",
        "border": "rgba(56, 189, 248, 0.35)",
    },
    "approved": {
        "text": "#34D399",
        "bg": "rgba(52, 211, 153, 0.12)",
        "border": "rgba(52, 211, 153, 0.35)",
    },
    "verified": {
        "text": "#34D399",
        "bg": "rgba(52, 211, 153, 0.12)",
        "border": "rgba(52, 211, 153, 0.35)",
    },
    "rejected": {
        "text": "#F87171",
        "bg": "rgba(248, 113, 113, 0.15)",
        "border": "rgba(248, 113, 113, 0.40)",
    },
    "changes requested": {
        "text": "#FB923C",
        "bg": "rgba(251, 146, 60, 0.12)",
        "border": "rgba(251, 146, 60, 0.35)",
    },
    "changes_requested": {
        "text": "#FB923C",
        "bg": "rgba(251, 146, 60, 0.12)",
        "border": "rgba(251, 146, 60, 0.35)",
    },
    "needs more info": {
        "text": "#A78BFA",
        "bg": "rgba(167, 139, 250, 0.12)",
        "border": "rgba(167, 139, 250, 0.35)",
    },
    "needs_more_info": {
        "text": "#A78BFA",
        "bg": "rgba(167, 139, 250, 0.12)",
        "border": "rgba(167, 139, 250, 0.35)",
    },
    "open": {
        "text": "#38BDF8",
        "bg": "rgba(56, 189, 248, 0.12)",
        "border": "rgba(56, 189, 248, 0.35)",
    },
    "in progress": {
        "text": "#FBBF24",
        "bg": "rgba(251, 191, 36, 0.12)",
        "border": "rgba(251, 191, 36, 0.35)",
    },
    "in_progress": {
        "text": "#FBBF24",
        "bg": "rgba(251, 191, 36, 0.12)",
        "border": "rgba(251, 191, 36, 0.35)",
    },
    "resolved": {
        "text": "#34D399",
        "bg": "rgba(52, 211, 153, 0.12)",
        "border": "rgba(52, 211, 153, 0.35)",
    },
}

THEME_CSS: Final[str] = """
<style>
/* ==========================================================================
   CHAKRAVAT DESIGN SYSTEM - DEEP NAVY / CHARCOAL CORE CSS
   Strict Offline System Font Stack, Zero External CDN Dependency
   ========================================================================== */

/* Main canvas background and typography */
.stApp {
    background-color: #101820 !important;
    color: #F1F5F9 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
}

/* Eliminate awkward top whitespace in block container */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2.5rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 1440px !important;
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background-color: #0B1117 !important;
    border-right: 1px solid #1E2D3B !important;
}

section[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem !important;
    padding-left: 1.25rem !important;
    padding-right: 1.25rem !important;
}

/* Sidebar header & titles */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #F1F5F9 !important;
    font-weight: 600 !important;
}

/* Metric card container override */
div[data-testid="stMetric"] {
    background-color: #17222D !important;
    border: 1px solid #2C4056 !important;
    border-radius: 8px !important;
    padding: 1rem 1.25rem !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.25) !important;
}

div[data-testid="stMetric"] label {
    color: #94A3B8 !important;
    font-size: 0.8125rem !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.03em !important;
}

div[data-testid="stMetricValue"] {
    color: #F1F5F9 !important;
    font-family: "JetBrains Mono", "SF Mono", Consolas, "Courier New", monospace !important;
    font-size: 1.625rem !important;
    font-weight: 700 !important;
    font-variant-numeric: tabular-nums !important;
}

div[data-testid="stMetricDelta"] {
    font-family: "JetBrains Mono", "SF Mono", Consolas, monospace !important;
    font-weight: 600 !important;
}

/* Tab container styling */
.stTabs [data-baseweb="tab-list"] {
    background-color: transparent !important;
    border-bottom: 1px solid #2C4056 !important;
    gap: 8px !important;
}

.stTabs [data-baseweb="tab"] {
    color: #94A3B8 !important;
    border-radius: 6px 6px 0 0 !important;
    padding: 8px 16px !important;
    font-weight: 500 !important;
    border: none !important;
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
    color: #38BDF8 !important;
    background-color: #17222D !important;
    border-bottom: 2px solid #38BDF8 !important;
}

/* Streamlit alerts overrides */
.stAlert {
    background-color: #17222D !important;
    border: 1px solid #2C4056 !important;
    border-radius: 8px !important;
    color: #F1F5F9 !important;
}

/* Inputs, Selectboxes, and Buttons */
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div {
    background-color: #17222D !important;
    border-color: #2C4056 !important;
    color: #F1F5F9 !important;
}

div[data-baseweb="select"] span {
    color: #F1F5F9 !important;
}

.stButton > button {
    background-color: #17222D !important;
    color: #F1F5F9 !important;
    border: 1px solid #2C4056 !important;
    border-radius: 6px !important;
    padding: 0.5rem 1rem !important;
    font-weight: 500 !important;
    transition: all 0.15s ease-in-out !important;
}

.stButton > button:hover {
    background-color: #253748 !important;
    border-color: #38BDF8 !important;
    color: #38BDF8 !important;
}

.stButton > button[kind="primary"] {
    background-color: #38BDF8 !important;
    color: #101820 !important;
    font-weight: 600 !important;
    border: 1px solid #38BDF8 !important;
}

.stButton > button[kind="primary"]:hover {
    background-color: #7DD3FC !important;
    border-color: #7DD3FC !important;
    color: #101820 !important;
}

/* Radio button in sidebar */
div[data-testid="stSidebarUserContent"] div[role="radiogroup"] label {
    padding: 6px 10px !important;
    border-radius: 6px !important;
    transition: background 0.15s ease !important;
}

div[data-testid="stSidebarUserContent"] div[role="radiogroup"] label:hover {
    background-color: #17222D !important;
}

/* Custom UI Component Classes with Dribbble Glassmorphism & Cyber Neon Accents */
@keyframes cvPulse {
    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.7); }
    70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(56, 189, 248, 0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(56, 189, 248, 0); }
}

@keyframes cvRadarSweep {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.cv-pulse-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    background-color: #38BDF8;
    border-radius: 50%;
    margin-right: 6px;
    animation: cvPulse 2s infinite;
}

.cv-pulse-dot-red {
    display: inline-block;
    width: 8px;
    height: 8px;
    background-color: #F87171;
    border-radius: 50%;
    margin-right: 6px;
    animation: cvPulse 1.5s infinite;
}

.cv-hud-ticker {
    background: linear-gradient(90deg, rgba(16, 24, 32, 0.95), rgba(23, 34, 45, 0.9), rgba(16, 24, 32, 0.95));
    border: 1px solid rgba(56, 189, 248, 0.25);
    border-radius: 10px;
    padding: 0.5rem 1rem;
    margin-bottom: 1.25rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.75rem;
    color: #94A3B8;
    font-family: "JetBrains Mono", "SF Mono", Consolas, monospace;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
}

.cv-tour-banner {
    background: linear-gradient(135deg, rgba(23, 34, 45, 0.9), rgba(30, 45, 59, 0.8));
    border: 1px solid rgba(56, 189, 248, 0.3);
    border-radius: 10px;
    padding: 0.75rem 1rem;
    margin-bottom: 1.25rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
}

.cv-card {
    background: rgba(23, 34, 45, 0.85);
    border: 1px solid rgba(44, 64, 86, 0.6);
    border-radius: 10px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
    backdrop-filter: blur(12px);
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.cv-card:hover {
    border-color: rgba(56, 189, 248, 0.4);
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.4), 0 0 15px rgba(56, 189, 248, 0.15);
    transform: translateY(-2px);
}

.cv-card-header {
    font-size: 1rem;
    font-weight: 600;
    color: #F1F5F9;
    margin-bottom: 0.75rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.cv-card-body {
    color: #CBD5E1;
    font-size: 0.875rem;
    line-height: 1.55;
}

.cv-metric-card {
    background: linear-gradient(180deg, rgba(23, 34, 45, 0.95), rgba(19, 28, 38, 0.95));
    border: 1px solid rgba(44, 64, 86, 0.7);
    border-radius: 10px;
    padding: 1.1rem 1.25rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    margin-bottom: 0.75rem;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    backdrop-filter: blur(8px);
}

.cv-metric-card:hover {
    border-color: rgba(56, 189, 248, 0.5);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35), 0 0 12px rgba(56, 189, 248, 0.2);
    transform: translateY(-2px);
}

.cv-metric-label {
    color: #94A3B8;
    font-size: 0.8125rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    margin-bottom: 0.25rem;
}

.cv-metric-value {
    color: #F1F5F9;
    font-family: "JetBrains Mono", "SF Mono", Consolas, monospace;
    font-size: 1.625rem;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    line-height: 1.2;
}

.cv-metric-meta {
    font-size: 0.75rem;
    color: #94A3B8;
    margin-top: 0.25rem;
}

/* Badges */
.cv-badge {
    display: inline-block;
    padding: 2px 8px;
    font-size: 0.6875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    border-radius: 4px;
    line-height: 1.4;
}

.cv-badge-normal {
    background: rgba(56, 189, 248, 0.15);
    color: #38BDF8;
    border: 1px solid rgba(56, 189, 248, 0.4);
}

.cv-badge-advisory {
    background: rgba(251, 191, 36, 0.15);
    color: #FBBF24;
    border: 1px solid rgba(251, 191, 36, 0.4);
}

.cv-badge-warning {
    background: rgba(251, 146, 60, 0.15);
    color: #FB923C;
    border: 1px solid rgba(251, 146, 60, 0.4);
}

.cv-badge-extreme {
    background: rgba(248, 113, 113, 0.20);
    color: #F87171;
    border: 1px solid rgba(248, 113, 113, 0.45);
}

.cv-badge-verified {
    background: rgba(52, 211, 153, 0.15);
    color: #34D399;
    border: 1px solid rgba(52, 211, 153, 0.4);
}

.cv-badge-experimental {
    background: rgba(167, 139, 250, 0.15);
    color: #A78BFA;
    border: 1px solid rgba(167, 139, 250, 0.4);
}

.cv-badge-muted {
    background: rgba(148, 163, 184, 0.15);
    color: #94A3B8;
    border: 1px solid rgba(148, 163, 184, 0.4);
}

/* Disclaimer Banners */
.cv-disclaimer-banner {
    background: linear-gradient(90deg, rgba(167, 139, 250, 0.12) 0%, rgba(56, 189, 248, 0.08) 100%);
    border: 1px solid rgba(167, 139, 250, 0.35);
    border-left: 4px solid #A78BFA;
    border-radius: 6px;
    padding: 0.75rem 1rem;
    margin-bottom: 1.25rem;
    color: #CBD5E1;
    font-size: 0.8125rem;
    line-height: 1.45;
}

.cv-disclaimer-banner strong {
    color: #F1F5F9;
}

.cv-unverified-banner {
    background: linear-gradient(90deg, rgba(251, 191, 36, 0.12) 0%, rgba(251, 146, 60, 0.08) 100%);
    border: 1px solid rgba(251, 191, 36, 0.35);
    border-left: 4px solid #FBBF24;
    border-radius: 6px;
    padding: 0.75rem 1rem;
    margin-bottom: 1.25rem;
    color: #CBD5E1;
    font-size: 0.8125rem;
    line-height: 1.45;
}

.cv-unverified-banner strong {
    color: #F1F5F9;
}

/* State Boxes (Empty, Loading, Error, Data Limited) */
.cv-state-box {
    background-color: #17222D;
    border: 1px dashed #2C4056;
    border-radius: 8px;
    padding: 2.5rem 1.5rem;
    text-align: center;
    color: #94A3B8;
    margin: 1rem 0;
}

.cv-state-box h4 {
    color: #F1F5F9;
    font-size: 1.125rem;
    margin-bottom: 0.5rem;
}

.cv-state-box p {
    font-size: 0.875rem;
    color: #94A3B8;
    margin: 0;
}

/* Section Header Bar */
.cv-section-header {
    border-bottom: 1px solid #1E2D3B;
    padding-bottom: 0.875rem;
    margin-bottom: 1.5rem;
}

.cv-section-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: #F1F5F9;
    letter-spacing: -0.01em;
    margin: 0 0 0.25rem 0;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.cv-section-subtitle {
    font-size: 0.875rem;
    color: #94A3B8;
    margin: 0;
}

/* Audit History Timeline Table */
.cv-timeline-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.8125rem;
}

.cv-timeline-table th {
    text-align: left;
    color: #94A3B8;
    font-weight: 600;
    padding: 8px 12px;
    border-bottom: 1px solid #2C4056;
    text-transform: uppercase;
    font-size: 0.6875rem;
}

.cv-timeline-table td {
    padding: 8px 12px;
    border-bottom: 1px solid #1E2D3B;
    color: #CBD5E1;
}

.cv-timeline-table tr:hover {
    background-color: #1E2D3B;
}

.cv-mono {
    font-family: "JetBrains Mono", "SF Mono", Consolas, monospace !important;
    font-variant-numeric: tabular-nums !important;
}
</style>
"""


def get_theme_css() -> str:
    """Return the raw CSS markup string for injection (base design system + v2 layer)."""
    from src.ui.theme_v2 import THEME_CSS_V2
    return THEME_CSS + THEME_CSS_V2


def inject_custom_theme() -> None:
    """Inject the CHAKRAVAT custom dark design system CSS into the Streamlit app."""
    try:
        import streamlit as st
        st.markdown(get_theme_css(), unsafe_allow_html=True)
    except Exception:
        # Fallback for environments where Streamlit runtime is not active (e.g. testing)
        pass
