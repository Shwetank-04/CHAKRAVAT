"""CHAKRAVAT Reusable UI Components.

Strictly typed, high-legibility components adhering to the Deep Navy (#101820)
design system and <=3 columns horizontal whitespace rule.
"""

from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Literal, Optional
import html
import textwrap
import streamlit as st

from src.ui.theme import COLOR_TOKENS, SEVERITY_COLORS, STATUS_COLORS

SeverityType = Literal["normal", "watch", "advisory", "moderate", "warning", "severe", "extreme", "danger", "verified", "experimental"]
StatusType = Literal["pending", "submitted", "under_review", "under review", "approved", "verified", "rejected", "changes_requested", "changes requested", "needs_more_info", "needs more info", "open", "in_progress", "in progress", "resolved"]
DeltaType = Literal["positive", "negative", "neutral"]


def normalize_html(body: str) -> str:
    """Make an HTML snippet safe for ``st.markdown(..., unsafe_allow_html=True)``.

    Markdown (CommonMark) ends an HTML block at the first blank line and treats any
    following line indented by 4+ spaces as a *code block*. Empty f-string fragments
    (e.g. ``{delta_html}`` -> "") leave blank lines inside cards, which made raw
    ``<div ...>`` text appear on screen. Flattening indentation and dropping blank
    lines removes that failure mode. Bodies that are not HTML are returned untouched.
    """
    text = textwrap.dedent(str(body)).strip()
    if not text.startswith("<"):
        return text
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def cv_markdown(body: str, **kwargs: Any) -> None:
    """Drop-in replacement for ``st.markdown`` that is robust for multi-line HTML."""
    if kwargs.get("unsafe_allow_html"):
        body = normalize_html(body)
    st.markdown(body, **kwargs)


def status_badge(status: str) -> str:
    """Return an HTML snippet for a styled workflow status badge."""
    clean_status = (status or "").strip().lower()
    style = STATUS_COLORS.get(clean_status, {
        "text": COLOR_TOKENS["text_muted"],
        "bg": "rgba(148, 163, 184, 0.15)",
        "border": "rgba(148, 163, 184, 0.35)",
    })
    safe_label = html.escape(status.upper())
    return (
        f'<span class="cv-badge" style="color: {style["text"]}; '
        f'background-color: {style["bg"]}; border: 1px solid {style["border"]};">'
        f'{safe_label}</span>'
    )


def severity_badge(severity: str, label: Optional[str] = None) -> str:
    """Return an HTML snippet for a meteorological or operational severity badge.

    ``severity`` picks the colour; ``label`` (optional) overrides the visible text so that a
    badge such as "ACTION REQUIRED" can be drawn in the "warning" colour.
    """
    clean_sev = (severity or "").strip().lower()
    style = SEVERITY_COLORS.get(clean_sev, {
        "text": COLOR_TOKENS["text_muted"],
        "bg": "rgba(148, 163, 184, 0.15)",
        "border": "rgba(148, 163, 184, 0.35)",
    })
    safe_label = html.escape((label or severity or "").upper())
    return (
        f'<span class="cv-badge" style="color: {style["text"]}; '
        f'background-color: {style["bg"]}; border: 1px solid {style["border"]};">'
        f'{safe_label}</span>'
    )


def metric_card(
    label: str,
    value: Any,
    unit: str = "",
    delta: Optional[str] = None,
    delta_type: DeltaType = "neutral",
    badge_text: Optional[str] = None,
    badge_severity: Optional[str] = None,
    help_text: Optional[str] = None,
) -> None:
    """Render a styled scientific KPI metric card.

    Note: Must be invoked within st.columns(N) where N <= 3 to honor
    the project-wide whitespace discipline.
    """
    safe_label = html.escape(label)
    safe_value = html.escape(str(value))
    # Pure-integer values get a count-up hook (the real value stays in the DOM as the fallback).
    if str(value).strip().isdigit():
        safe_value = f'<span class="cv-count" data-count="{int(str(value).strip())}">{safe_value}</span>'
    safe_unit = f' <span style="font-size: 0.875rem; color: #94A3B8; font-weight: 500;">{html.escape(unit)}</span>' if unit else ""
    
    badge_html = ""
    if badge_text:
        badge_html = severity_badge(badge_severity or "normal") if badge_severity else f'<span class="cv-badge cv-badge-normal">{html.escape(badge_text)}</span>'

    delta_html = ""
    if delta:
        delta_color = "#34D399" if delta_type == "positive" else ("#F87171" if delta_type == "negative" else "#94A3B8")
        safe_delta = html.escape(delta)
        delta_html = f'<div class="cv-metric-meta" style="color: {delta_color}; font-family: monospace;">{safe_delta}</div>'

    meta_html = ""
    if help_text:
        meta_html = f'<div class="cv-metric-meta">{html.escape(help_text)}</div>'

    html_card = f"""
    <div class="cv-metric-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div class="cv-metric-label">{safe_label}</div>
            {badge_html}
        </div>
        <div class="cv-metric-value">{safe_value}{safe_unit}</div>
        {delta_html}
        {meta_html}
    </div>
    """
    cv_markdown(html_card, unsafe_allow_html=True)


def experimental_disclaimer_banner(custom_text: Optional[str] = None) -> None:
    """Render the mandatory scientific decision-support disclaimer banner.

    Guarantees scientific credibility by prominently highlighting that CHAKRAVAT
    is an experimental research decision-support tool, not an official warning agency.
    """
    body = custom_text or (
        "<strong>⚠️ EXPERIMENTAL DECISION-SUPPORT PROTOTYPE — NOT FOR OPERATIONAL LIFE-SAFETY WARNINGS</strong><br>"
        "CHAKRAVAT is a research decision-support prototype evaluating North Indian Ocean cyclone prediction models. "
        "Forecasts and evaluations are decision-support estimates only and do NOT replace official bulletins issued by the "
        "India Meteorological Department (IMD) or national disaster management authorities."
    )
    cv_markdown(f'<div class="cv-disclaimer-banner">{body}</div>', unsafe_allow_html=True)


def unverified_report_banner(custom_text: Optional[str] = None) -> None:
    """Render the mandatory citizen observer warning banner for unverified reports."""
    body = custom_text or (
        "<strong>⚠️ CITIZEN OBSERVER NOTICE — UNVERIFIED FIELD SUBMISSIONS</strong><br>"
        "Community incident reports are crowdsourced from field observers and are unverified until confirmed by "
        "disaster response authorities. Treat unverified damage and flood reports as situational indicators only."
    )
    cv_markdown(f'<div class="cv-unverified-banner">{body}</div>', unsafe_allow_html=True)


def state_box(
    title: str,
    message: str,
    icon: str = "ℹ️",
    box_type: Literal["empty", "loading", "error", "data_limited"] = "empty",
) -> None:
    """Render a styled placeholder box for empty, loading, data-limited, or error states."""
    safe_title = html.escape(title)
    safe_msg = html.escape(message)
    border_color = "#2C4056"
    if box_type == "error":
        border_color = "rgba(248, 113, 113, 0.5)"
    elif box_type == "data_limited":
        border_color = "rgba(167, 139, 250, 0.5)"

    cv_markdown(
        f"""
        <div class="cv-state-box" style="border-color: {border_color};">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
            <h4>{safe_title}</h4>
            <p>{safe_msg}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state(
    title: str,
    message: str,
    icon: str = "ℹ️",
) -> None:
    """Convenience alias for state_box(box_type='empty')."""
    state_box(title=title, message=message, icon=icon, box_type="empty")


def render_data_limited_warning(reason: str) -> None:
    """Render a styled callout when observations are insufficient for genuine model inference."""
    state_box(
        title="Data Limited State — Genuine Evaluation Active",
        message=reason,
        icon="📊",
        box_type="data_limited",
    )


def section_header(
    title: str,
    subtitle: str,
    badge_label: Optional[str] = None,
    badge_type: str = "normal",
) -> None:
    """Render a standardized section header with title, operational tag, and subtitle."""
    safe_title = html.escape(title)
    safe_sub = html.escape(subtitle)
    badge_html = f"<div>{severity_badge(badge_type, label=badge_label)}</div>" if badge_label else ""

    cv_markdown(
        f"""
        <div class="cv-section-header">
            <div class="cv-section-title">
                <span>{safe_title}</span>
                {badge_html}
            </div>
            <p class="cv-section-subtitle">{safe_sub}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _next_card_key() -> Optional[str]:
    """Unique per-run key so each bordered card gets a ``st-key-cvcard_N`` CSS hook."""
    try:
        n = int(st.session_state.get("_cv_card_n", 0)) + 1
        st.session_state["_cv_card_n"] = n
        return f"cvcard_{n}"
    except Exception:
        return None


@contextmanager
def card_container(
    title: Optional[str] = None,
    badge_label: Optional[str] = None,
    badge_type: str = "normal",
) -> Generator[None, None, None]:
    """Context manager rendering a bordered, hover-reactive card adhering to the design system."""
    with st.container(border=True, key=_next_card_key()):
        if title:
            badge_html = f" {severity_badge(badge_type, label=badge_label)}" if badge_label else ""
            cv_markdown(
                f"""
                <div class="cv-card-title">
                    <div class="cv-card-title-text">{html.escape(title)}</div>
                    {badge_html}
                </div>
                """,
                unsafe_allow_html=True,
            )
        yield


def grid_row(cols: int = 3) -> List[Any]:
    """Layout helper enforcing strict layout discipline: no row may contain >3 columns."""
    if cols < 1 or cols > 3:
        raise ValueError(
            f"Strict Whitespace Discipline Violation: Requested {cols} columns in a row. "
            "Maximum allowed side-by-side columns is 3."
        )
    return list(st.columns(cols))


def audit_timeline(audit_records: List[Dict[str, Any]]) -> None:
    """Render a chronological audit timeline table with monospace timestamps and badges."""
    if not audit_records:
        cv_markdown('<p style="color: #94A3B8; font-size: 0.8125rem;">No audit records available.</p>', unsafe_allow_html=True)
        return

    rows_html = []
    for entry in audit_records:
        ts = html.escape(str(entry.get("timestamp", "-")))
        actor = html.escape(str(entry.get("actor", "-")))
        action = html.escape(str(entry.get("action", "-")))
        note = html.escape(str(entry.get("note", entry.get("notes", "-"))))
        
        # Colorize action
        action_lower = action.lower()
        if "approved" in action_lower or "verified" in action_lower:
            action_badge = status_badge("approved")
        elif "rejected" in action_lower:
            action_badge = status_badge("rejected")
        elif "change" in action_lower:
            action_badge = status_badge("changes requested")
        else:
            action_badge = f'<span class="cv-badge cv-badge-normal">{action}</span>'

        rows_html.append(
            f"""
            <tr>
                <td class="cv-mono" style="color: #94A3B8; white-space: nowrap;">{ts}</td>
                <td style="color: #38BDF8; font-weight: 500;">{actor}</td>
                <td>{action_badge}</td>
                <td style="color: #CBD5E1;">{note}</td>
            </tr>
            """
        )

    table_html = f"""
    <table class="cv-timeline-table">
        <thead>
            <tr>
                <th>Timestamp (UTC)</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Notes / Rationale</th>
            </tr>
        </thead>
        <tbody>
            {"".join(rows_html)}
        </tbody>
    </table>
    """
    cv_markdown(table_html, unsafe_allow_html=True)


def marquee(items: List[str], speed_s: int = 48, key_class: str = "") -> None:
    """Render an endlessly scrolling ticker strip (pure CSS, pauses on hover)."""
    if not items:
        return
    cells = "".join(f'<span class="cv-marquee-item">{html.escape(i)}</span><span class="cv-marquee-sep">✺</span>' for i in items)
    cv_markdown(
        f'<div class="cv-marquee {key_class}" style="--cv-marquee-speed: {int(speed_s)}s;">'
        f'<div class="cv-marquee-track">{cells}{cells}</div></div>',
        unsafe_allow_html=True,
    )


def faq(items: List[Dict[str, str]]) -> None:
    """Render a styled accordion (native <details>, no JavaScript required)."""
    rows = "".join(
        f'<details class="cv-faq-item"><summary><span>{html.escape(i["q"])}</span>'
        f'<span class="cv-faq-chevron">+</span></summary>'
        f'<div class="cv-faq-body">{html.escape(i["a"])}</div></details>'
        for i in items
    )
    cv_markdown(f'<div class="cv-faq">{rows}</div>', unsafe_allow_html=True)


def eyebrow(text: str) -> None:
    """Small mono uppercase label placed above a block (HackMIT-style section tag)."""
    cv_markdown(f'<div class="cv-eyebrow">{html.escape(text)}</div>', unsafe_allow_html=True)


def track_card_html(icon: str, title: str, blurb: str, tag: str, accent: str = "cyan") -> str:
    """Markup for a 'mission track' card body (the Streamlit button sits directly beneath it)."""
    return (
        f'<div class="cv-track cv-accent-{html.escape(accent)}">'
        f'<div class="cv-track-top"><span class="cv-track-icon">{icon}</span>'
        f'<span class="cv-track-tag">{html.escape(tag)}</span></div>'
        f'<div class="cv-track-title">{html.escape(title)}</div>'
        f'<div class="cv-track-blurb">{html.escape(blurb)}</div></div>'
    )
