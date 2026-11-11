"""Audit: run every section headlessly and flag st.markdown(unsafe_allow_html) bodies
that CommonMark would render as code blocks (the 'raw <div> text' bug)."""
import sys, textwrap, collections
sys.path.insert(0, ".")
from markdown_it import MarkdownIt
import streamlit as st
from streamlit.testing.v1 import AppTest

md = MarkdownIt("commonmark", {"html": True})
bad = collections.defaultdict(list)

calls = collections.Counter()
def _spy(body, *a, **kw):
    if kw.get("unsafe_allow_html") or (len(a) > 0 and a[0]):
        cleaned = textwrap.dedent(str(body)).strip()   # what streamlit does
        toks = md.parse(cleaned)
        if any(t.type in ("code_block", "fence") for t in toks):
            bad[AUDIT_SECTION[0]].append(cleaned[:90].replace("\n", " | "))
    calls[AUDIT_SECTION[0]] += 1
    return _orig(body, *a, **kw)

_orig = st.markdown
st.markdown = _spy
AUDIT_SECTION = [""]

from src.ui.state import SECTIONS
for sec in SECTIONS:
    AUDIT_SECTION[0] = sec
    at = AppTest.from_file("/home/claude/CHAKRAVAT/app.py", default_timeout=120)
    at.run()
    at.sidebar.radio[0].set_value(sec).run()
    errs = [e.value for e in at.exception]
    print(f"{sec[:40]:42s} exceptions={len(errs)} code-block-bodies={len(bad[sec])} md-calls={calls[sec]}")
    for e in errs: print("   EXC:", str(e)[:200])
print()
for sec, items in bad.items():
    for i in items[:3]: print(f"[{sec[:20]}] {i}")
