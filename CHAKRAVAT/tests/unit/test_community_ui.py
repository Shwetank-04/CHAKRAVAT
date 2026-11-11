"""UI regression tests for the Community Reports section (Section F)."""
import textwrap

import pytest
from markdown_it import MarkdownIt
from streamlit.testing.v1 import AppTest

from src.ui.components import normalize_html

APP = "app.py"
SECTION = "(F) Community Reports"


def _open_section():
    import pathlib
    app = str(pathlib.Path(__file__).resolve().parents[2] / APP)
    at = AppTest.from_file(app, default_timeout=120)
    at.run()
    at.radio(key="nav_radio_selection").set_value(SECTION).run()
    assert not at.exception
    return at


def _btn(at, label):
    return next(b for b in at.button if label in b.label)


def _n_reports(at):
    return len([m for m in at.markdown if "cv-card" in m.value and "REP-2026" in m.value])


def test_normalize_html_never_produces_code_blocks():
    # Empty interpolations (the old metric_card bug) leave blank lines inside the div.
    body = f"""
    <div class="cv-metric-card">
        <div>label</div>
        {""}
        <div class="meta">help</div>
    </div>
    """
    md = MarkdownIt("commonmark", {"html": True})
    assert any(t.type == "code_block" for t in md.parse(textwrap.dedent(body).strip()))  # the bug
    fixed = md.parse(normalize_html(body))
    assert not any(t.type in ("code_block", "fence") for t in fixed)


def test_plain_markdown_is_left_alone():
    assert normalize_html("**bold**\n\n- a\n- b") == "**bold**\n\n- a\n- b"


def test_cards_render_and_seed_reports_have_audit_trail():
    at = _open_section()
    assert _n_reports(at) == 4
    timeline = [m.value for m in at.markdown if "cv-timeline-table" in m.value]
    assert timeline, "seed reports should expose a verification history"
    assert "System Intake" in " ".join(timeline)


def test_invalid_submit_keeps_input_then_valid_submit_clears_and_flashes():
    at = _open_section()
    before = _n_reports(at)

    at.text_area[0].set_value("Water at knee height on the main road")
    _btn(at, "Submit Citizen").click().run()
    assert _n_reports(at) == before                       # rejected: location missing
    assert at.error and "Landmark" in at.error[0].value
    assert at.text_area[0].value.startswith("Water at knee")   # input NOT wiped

    at.text_input[[t.label for t in at.text_input].index("Specific Landmark / Ward / Village *")].set_value("Ward 4 sea dyke")
    _btn(at, "Submit Citizen").click().run()
    assert _n_reports(at) == before + 1
    assert any("submitted" in s.value for s in at.success)     # flash survives st.rerun()
    assert at.text_area[0].value == ""                          # form reset after success


def test_verify_transition_records_actor_and_action():
    at = _open_section()
    verify_buttons = [b for b in at.button if "Verify Incident" in b.label]
    verify_buttons[1].click().run()            # 2nd card: REP-2026-102 (Under Review)
    assert not at.exception
    rep = next(r for r in at.session_state["community_reports"] if r["id"] == "REP-2026-102")
    assert rep["status"] == "Verified" and rep["is_verified"] is True
    last = rep["audit_log"][-1]
    assert last["action"] == "Verified" and last["actor"]            # keys audit_timeline renders
    rows = " ".join(m.value for m in at.markdown if "cv-timeline-table" in m.value)
    assert "<td>-</td>" not in rows                                   # Actor/Action not blank
    assert rep["reviewer_notes"]                                       # earlier note not wiped by blank input
