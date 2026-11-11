"""CHAKRAVAT design system v2: hackathon-site energy (TreeHacks / HackMIT inspired).

Layered on top of ``theme.THEME_CSS`` (loaded after it, so these rules win). 100% offline:
system font stacks only, no CDN. All motion respects ``prefers-reduced-motion``.
"""

from typing import Final

THEME_CSS_V2: Final[str] = """
<style>
/* ===== Tokens ============================================================ */
:root {
  --cv-bg: #0B1117;
  --cv-line: rgba(130, 160, 190, 0.20);
  --cv-cyan: #38BDF8; --cv-violet: #A78BFA; --cv-pink: #F472B6;
  --cv-mint: #34D399; --cv-amber: #FBBF24; --cv-coral: #FB7185;
  --cv-grad: linear-gradient(100deg, #38BDF8 0%, #A78BFA 52%, #F472B6 100%);
  --cv-display: ui-rounded, "SF Pro Rounded", "Segoe UI Variable Display", "Segoe UI", system-ui, -apple-system, Roboto, sans-serif;
  --cv-mono: ui-monospace, "JetBrains Mono", "SF Mono", Consolas, "Courier New", monospace;
  --cv-ease: cubic-bezier(0.16, 1, 0.3, 1);
}

/* ===== Canvas: animated mesh gradient + grain ============================ */
.stApp { background: var(--cv-bg) !important; }
.stApp::before {
  content: ""; position: fixed; inset: -25%; z-index: 0; pointer-events: none;
  background:
    radial-gradient(38% 34% at 14% 12%, rgba(56,189,248,.17), transparent 70%),
    radial-gradient(34% 30% at 86% 16%, rgba(167,139,250,.15), transparent 70%),
    radial-gradient(40% 34% at 72% 92%, rgba(244,114,182,.11), transparent 70%),
    radial-gradient(30% 30% at 8% 88%, rgba(52,211,153,.07), transparent 70%);
  animation: cvDrift 32s ease-in-out infinite alternate;
}
.stApp::after {
  content: ""; position: fixed; inset: 0; z-index: 0; pointer-events: none; opacity: .5; mix-blend-mode: overlay;
  background-image: url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0naHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmcnIHdpZHRoPScxNjAnIGhlaWdodD0nMTYwJz48ZmlsdGVyIGlkPSduJz48ZmVUdXJidWxlbmNlIHR5cGU9J2ZyYWN0YWxOb2lzZScgYmFzZUZyZXF1ZW5jeT0nLjknIG51bU9jdGF2ZXM9JzInIHN0aXRjaFRpbGVzPSdzdGl0Y2gnLz48ZmVDb2xvck1hdHJpeCB2YWx1ZXM9JzAgMCAwIDAgMSAgMCAwIDAgMCAxICAwIDAgMCAwIDEgIDAgMCAwIC4wNTUgMCcvPjwvZmlsdGVyPjxyZWN0IHdpZHRoPScxMDAlJyBoZWlnaHQ9JzEwMCUnIGZpbHRlcj0ndXJsKCNuKScvPjwvc3ZnPg==");
}
@keyframes cvDrift { from { transform: translate3d(-2%, -1%, 0) scale(1); } to { transform: translate3d(2%, 2%, 0) scale(1.08); } }
[data-testid="stAppViewContainer"], [data-testid="stMain"] { position: relative; z-index: 1; }

/* Chrome: no sidebar (controls live in the top bar), transparent header */
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"] { display: none !important; }
[data-testid="stHeader"] { background: transparent !important; pointer-events: none; }
[data-testid="stHeader"] * { pointer-events: auto; }
[data-testid="stAppDeployButton"] { display: none !important; }
.block-container { padding-top: 0.9rem !important; max-width: 1360px !important; }
::selection { background: rgba(167,139,250,.45); color: #fff; }
html { scroll-behavior: smooth; }
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-thumb { background: rgba(130,160,190,.28); border-radius: 10px; border: 2px solid transparent; background-clip: padding-box; }
::-webkit-scrollbar-thumb:hover { background: rgba(56,189,248,.5); background-clip: padding-box; border: 2px solid transparent; }

/* ===== Page-enter animation (re-plays when a section mounts) ============== */
@keyframes cvRise { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: none; } }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"],
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"],
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > .stVerticalBlock {
  animation: cvRise .55s var(--cv-ease) both;
}
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > *:nth-child(2) { animation-delay: .04s; }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > *:nth-child(3) { animation-delay: .08s; }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > *:nth-child(4) { animation-delay: .12s; }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > *:nth-child(5) { animation-delay: .16s; }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > *:nth-child(6) { animation-delay: .20s; }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > *:nth-child(n+7) { animation-delay: .24s; }
.st-key-topnav { animation: none !important; }

/* ===== Typography ========================================================= */
h1, h2, h3, .cv-section-title { font-family: var(--cv-display) !important; letter-spacing: -0.035em !important; }
.cv-section-title {
  font-size: clamp(1.7rem, 3.2vw, 2.5rem) !important; font-weight: 800 !important; line-height: 1.05;
  background: linear-gradient(180deg, #fff 30%, #b6c7da 100%); -webkit-background-clip: text; background-clip: text; color: transparent !important;
}
.cv-section-subtitle { font-size: .95rem !important; max-width: 62ch; }
.cv-section-header { border-bottom: 0 !important; padding-bottom: .4rem !important; margin-bottom: 1.1rem !important; }
.cv-eyebrow {
  font-family: var(--cv-mono); font-size: .72rem; font-weight: 700; letter-spacing: .16em; text-transform: uppercase;
  color: var(--cv-cyan); margin: 1.6rem 0 .6rem; display: flex; align-items: center; gap: .6rem;
}
.cv-eyebrow::before { content: ""; width: 28px; height: 2px; background: var(--cv-grad); border-radius: 2px; }
.cv-card-title { display: flex; justify-content: space-between; align-items: center; gap: .75rem; margin-bottom: .55rem; padding-bottom: .5rem; border-bottom: 1px dashed var(--cv-line); }
.cv-card-title-text { font-family: var(--cv-display); font-size: 1.02rem; font-weight: 750; color: #F1F5F9; letter-spacing: -0.01em; }

/* ===== Top navigation bar ================================================= */
.st-key-topnav { position: relative; }
/* Streamlit wraps keyed containers, so the *wrapper* must be the sticky element. */
[data-testid="stLayoutWrapper"]:has(> .st-key-topnav), [data-testid="stElementContainer"]:has(> .st-key-topnav), div:has(> .st-key-topnav) { position: sticky; top: 0; z-index: 990; }
.st-key-topnav {
  position: sticky; top: 0; z-index: 990; margin: 0 -0.5rem 1rem; padding: .55rem .5rem .6rem; padding-right: 3.4rem;
  background: linear-gradient(180deg, rgba(11,17,23,.92) 60%, rgba(11,17,23,0));
  backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
}
.cv-brand { display: flex; align-items: center; gap: .6rem; min-height: 2.6rem; }
.cv-brand-mark { font-size: 1.7rem; display: inline-block; animation: cvSpin 14s linear infinite; filter: drop-shadow(0 0 10px rgba(56,189,248,.55)); }
.cv-brand-name { font-family: var(--cv-display); font-weight: 850; font-size: 1.22rem; letter-spacing: -0.03em; color: #fff; line-height: 1; }
.cv-brand-sub { white-space: nowrap; font-family: var(--cv-mono); font-size: .56rem; letter-spacing: .14em; color: #7f93a8; text-transform: uppercase; margin-top: 3px; }
@keyframes cvSpin { to { transform: rotate(360deg); } }

.st-key-topnav [data-testid="stRadioGroup"] {
  display: flex !important; flex-direction: row !important; flex-wrap: wrap; gap: .2rem !important;
  background: rgba(23,34,45,.72); border: 1px solid var(--cv-line); border-radius: 999px; padding: .28rem;
  backdrop-filter: blur(14px); box-shadow: 0 10px 30px rgba(0,0,0,.35);
}
.st-key-topnav [data-testid="stRadioGroup"] > div { margin: 0 !important; }
.st-key-topnav label[data-testid="stRadioOption"] {
  margin: 0 !important; padding: .38rem .8rem !important; border-radius: 999px; cursor: pointer;
  transition: background .18s ease, transform .18s var(--cv-ease), box-shadow .18s ease;
}
.st-key-topnav label[data-testid="stRadioOption"] > div > div:first-child { display: none !important; }
.st-key-topnav label[data-testid="stRadioOption"] p { font-size: .84rem !important; font-weight: 650 !important; color: #a9b9ca !important; white-space: nowrap; margin: 0; }
.st-key-topnav label[data-testid="stRadioOption"]:hover { background: rgba(56,189,248,.14) !important; transform: translateY(-1px); }
.st-key-topnav label[data-testid="stRadioOption"]:hover p { color: #fff !important; }
.st-key-topnav label[data-testid="stRadioOption"][data-selected="true"] {
  background: var(--cv-grad) !important; box-shadow: 0 6px 22px rgba(167,139,250,.38), inset 0 0 0 1px rgba(255,255,255,.22);
}
.st-key-topnav label[data-testid="stRadioOption"][data-selected="true"] p { color: #0B1117 !important; font-weight: 850 !important; }
.st-key-topnav [data-testid="stPopover"] button, .st-key-topnav [data-testid="stPopoverButton"] { border-radius: 999px !important; }

/* ===== Tour bar =========================================================== */
.cv-tour-card {
  border: 1.5px solid rgba(167,139,250,.5); border-radius: 18px; padding: .85rem 1.1rem; margin: 0 0 1rem;
  background: linear-gradient(120deg, rgba(167,139,250,.16), rgba(56,189,248,.10) 60%, rgba(244,114,182,.10));
  box-shadow: 5px 5px 0 rgba(167,139,250,.35);
}
.cv-tour-head { display: flex; align-items: center; gap: .75rem; font-family: var(--cv-mono); font-size: .7rem; letter-spacing: .14em; text-transform: uppercase; color: var(--cv-violet); font-weight: 800; }
.cv-tour-dots { display: flex; gap: 6px; }
.cv-tour-dot { width: 26px; height: 6px; border-radius: 6px; background: rgba(148,163,184,.3); transition: all .3s; }
.cv-tour-dot.on { background: var(--cv-grad); box-shadow: 0 0 12px rgba(167,139,250,.7); }
.cv-tour-dot.done { background: rgba(167,139,250,.65); }
.cv-tour-tip { margin-top: .5rem; color: #dbe6f2; font-size: .93rem; line-height: 1.5; }
.cv-tour-tip b { color: #fff; font-family: var(--cv-display); font-size: 1.05rem; }

/* ===== Marquee ============================================================ */
.cv-marquee {
  overflow: hidden; white-space: nowrap; margin: .2rem -0.5rem 1.2rem; padding: .62rem 0; position: relative;
  border-top: 1.5px solid rgba(56,189,248,.35); border-bottom: 1.5px solid rgba(244,114,182,.35);
  background: linear-gradient(90deg, rgba(56,189,248,.07), rgba(167,139,250,.08), rgba(244,114,182,.07));
  -webkit-mask-image: linear-gradient(90deg, transparent, #000 6%, #000 94%, transparent); mask-image: linear-gradient(90deg, transparent, #000 6%, #000 94%, transparent);
}
.cv-marquee-track { display: inline-flex; animation: cvMarquee var(--cv-marquee-speed, 48s) linear infinite; will-change: transform; }
.cv-marquee:hover .cv-marquee-track { animation-play-state: paused; }
.cv-marquee-item { font-family: var(--cv-mono); font-size: .8rem; font-weight: 700; letter-spacing: .1em; color: #cfe0f1; text-transform: uppercase; padding: 0 1.1rem; }
.cv-marquee-sep { color: var(--cv-pink); font-size: .9rem; }
@keyframes cvMarquee { from { transform: translateX(0); } to { transform: translateX(-50%); } }

/* ===== Buttons (HackMIT-style hard shadow, press-down) ==================== */
.stButton > button, .stFormSubmitButton > button, [data-testid="stPopover"] > button {
  border: 1.5px solid rgba(148,163,184,.38) !important; background: rgba(23,34,45,.88) !important; color: #e8f0f8 !important;
  border-radius: 12px !important; font-weight: 700 !important; letter-spacing: .005em;
  box-shadow: 3px 3px 0 rgba(56,189,248,.30) !important;
  transition: transform .14s var(--cv-ease), box-shadow .14s var(--cv-ease), border-color .14s, background .14s !important;
}
.stButton > button:hover, .stFormSubmitButton > button:hover, [data-testid="stPopover"] > button:hover {
  transform: translate(-2px, -2px); box-shadow: 5px 5px 0 var(--cv-cyan) !important; border-color: var(--cv-cyan) !important; color: #fff !important; background: rgba(30,45,59,.95) !important;
}
.stButton > button:active, .stFormSubmitButton > button:active { transform: translate(2px, 2px); box-shadow: 0 0 0 var(--cv-cyan) !important; }
.stButton > button:focus-visible { outline: 2px solid var(--cv-pink) !important; outline-offset: 3px; }
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"] {
  background: var(--cv-grad) !important; color: #0B1117 !important; border: 1.5px solid rgba(255,255,255,.4) !important; box-shadow: 4px 4px 0 rgba(244,114,182,.6) !important;
}
.stButton > button[kind="primary"]:hover, .stButton > button[data-testid="stBaseButton-primary"]:hover { box-shadow: 6px 6px 0 var(--cv-pink) !important; color: #0B1117 !important; background: var(--cv-grad) !important; filter: brightness(1.08); }
.stButton > button[kind="primary"] p, .stButton > button[data-testid="stBaseButton-primary"] p { color: #0B1117 !important; font-weight: 850 !important; }
.stButton > button:disabled { opacity: .45; box-shadow: none !important; transform: none !important; }

/* ===== Glass cards with cursor spotlight ================================== */
.cv-card, .cv-metric-card, .cv-track, [class*="st-key-cvcard_"], [class*="st-key-trk_"], [class*="st-key-storm_"] {
  --mx: 50%; --my: 0%; position: relative; isolation: isolate;
  background: radial-gradient(420px circle at var(--mx) var(--my), rgba(56,189,248,.13), transparent 55%), rgba(20,31,42,.74) !important;
  border: 1px solid var(--cv-line) !important; border-radius: 18px !important;
  backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
  box-shadow: 0 10px 34px rgba(0,0,0,.30), inset 0 1px 0 rgba(255,255,255,.05) !important;
  transition: transform .35s var(--cv-ease), border-color .25s, box-shadow .35s var(--cv-ease);
}
[class*="st-key-cvcard_"], [class*="st-key-trk_"], [class*="st-key-storm_"] { padding: 1.05rem 1.15rem !important; }
.cv-card:hover, .cv-metric-card:hover, [class*="st-key-cvcard_"]:hover, [class*="st-key-trk_"]:hover, [class*="st-key-storm_"]:hover {
  border-color: rgba(56,189,248,.55) !important; transform: translateY(-3px);
  box-shadow: 0 18px 46px rgba(0,0,0,.42), 0 0 0 1px rgba(56,189,248,.12), 0 0 34px rgba(56,189,248,.14) !important;
}
.cv-metric-card .cv-metric-value { font-family: var(--cv-display); font-weight: 850; font-size: 2rem; letter-spacing: -0.04em; }
.cv-metric-card::after { content: ""; position: absolute; left: 14px; right: 14px; bottom: 0; height: 2px; background: var(--cv-grad); opacity: 0; transform: scaleX(.2); transition: all .4s var(--cv-ease); border-radius: 2px; }
.cv-metric-card:hover::after { opacity: 1; transform: scaleX(1); }

/* Mission-track / storm cards */
.cv-track { background: none !important; border: 0 !important; box-shadow: none !important; padding: 0 !important; backdrop-filter: none; transform: none !important; }
.cv-track-top { display: flex; justify-content: space-between; align-items: center; }
.cv-track-icon { font-size: 1.7rem; width: 3rem; height: 3rem; display: grid; place-items: center; border-radius: 14px; background: rgba(56,189,248,.12); border: 1px solid rgba(56,189,248,.35); transition: transform .4s var(--cv-ease); }
[class*="st-key-trk_"]:hover .cv-track-icon { transform: rotate(-8deg) scale(1.12); }
.cv-track-tag { font-family: var(--cv-mono); font-size: .62rem; letter-spacing: .14em; text-transform: uppercase; color: #8aa0b6; border: 1px solid var(--cv-line); padding: 2px 8px; border-radius: 999px; }
.cv-track-title { font-family: var(--cv-display); font-weight: 800; font-size: 1.18rem; letter-spacing: -0.02em; color: #fff; margin: .85rem 0 .25rem; }
.cv-track-blurb { color: #a9b9ca; font-size: .84rem; line-height: 1.5; min-height: 2.6rem; margin-bottom: .6rem; }
.cv-accent-violet .cv-track-icon { background: rgba(167,139,250,.13); border-color: rgba(167,139,250,.4); }
.cv-accent-pink .cv-track-icon { background: rgba(244,114,182,.13); border-color: rgba(244,114,182,.4); }
.cv-accent-mint .cv-track-icon { background: rgba(52,211,153,.13); border-color: rgba(52,211,153,.4); }
.cv-accent-amber .cv-track-icon { background: rgba(251,191,36,.13); border-color: rgba(251,191,36,.4); }
.cv-accent-coral .cv-track-icon { background: rgba(251,113,133,.13); border-color: rgba(251,113,133,.4); }

/* Selected storm: animated conic border */
@property --cv-angle { syntax: "<angle>"; initial-value: 0deg; inherits: false; }
@keyframes cvBorderSpin { to { --cv-angle: 360deg; } }
.st-key-storm_active { border-color: transparent !important;
  background: linear-gradient(rgba(20,31,42,.96), rgba(20,31,42,.96)) padding-box, conic-gradient(from var(--cv-angle), #38BDF8, #A78BFA, #F472B6, #38BDF8) border-box !important;
  border: 2px solid transparent !important; animation: cvBorderSpin 5s linear infinite; }

/* ===== FAQ accordion ====================================================== */
.cv-faq { display: grid; gap: .6rem; }
.cv-faq-item { border: 1px solid var(--cv-line); border-radius: 16px; background: rgba(20,31,42,.7); overflow: hidden; transition: border-color .2s, box-shadow .25s var(--cv-ease); }
.cv-faq-item:hover { border-color: rgba(167,139,250,.55); }
.cv-faq-item[open] { border-color: rgba(56,189,248,.6); box-shadow: 4px 4px 0 rgba(56,189,248,.28); }
.cv-faq-item summary { list-style: none; cursor: pointer; display: flex; justify-content: space-between; align-items: center; gap: 1rem; padding: .95rem 1.15rem; font-family: var(--cv-display); font-weight: 750; font-size: 1rem; color: #f1f5f9; }
.cv-faq-item summary::-webkit-details-marker { display: none; }
.cv-faq-chevron { font-family: var(--cv-mono); font-size: 1.3rem; color: var(--cv-cyan); transition: transform .3s var(--cv-ease); line-height: 1; }
.cv-faq-item[open] .cv-faq-chevron { transform: rotate(45deg); color: var(--cv-pink); }
.cv-faq-body { padding: 0 1.15rem 1.1rem; color: #b5c4d4; font-size: .92rem; line-height: 1.65; animation: cvRise .35s var(--cv-ease) both; }

/* ===== Inputs, tabs, expanders, charts ==================================== */
div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, .stTextArea textarea { border-radius: 12px !important; transition: border-color .15s, box-shadow .15s; }
div[data-baseweb="select"] > div:hover, div[data-baseweb="input"] > div:hover { border-color: rgba(56,189,248,.6) !important; }
div[data-baseweb="select"] > div:focus-within, div[data-baseweb="input"] > div:focus-within { border-color: var(--cv-cyan) !important; box-shadow: 0 0 0 3px rgba(56,189,248,.18) !important; }
[data-testid="stSlider"] [role="slider"] { box-shadow: 0 0 0 4px rgba(56,189,248,.25), 0 0 16px rgba(56,189,248,.6) !important; }
[data-testid="stTabs"] [role="tablist"] { gap: .35rem !important; background: rgba(23,34,45,.6) !important; border: 1px solid var(--cv-line) !important; border-radius: 999px !important; padding: .28rem !important; width: fit-content; max-width: 100%; overflow-x: auto; box-shadow: none !important; }
[data-testid="stTab"] { border-radius: 999px !important; padding: .4rem 1rem !important; transition: background .18s, transform .18s var(--cv-ease); border-bottom: 0 !important; }
[data-testid="stTab"]:hover { background: rgba(56,189,248,.14) !important; transform: translateY(-1px); }
[data-testid="stTab"][data-selected="true"], [data-testid="stTab"][aria-selected="true"] { background: var(--cv-grad) !important; box-shadow: 0 6px 20px rgba(167,139,250,.32); }
[data-testid="stTab"][aria-selected="true"] p { color: #0B1117 !important; font-weight: 800 !important; }
[data-testid="stTab"] > div:last-child:empty, [data-testid="stTab"] [data-rac]:empty { display: none !important; }
[data-testid="stTabs"] [role="tablist"]::after, [data-testid="stTabs"] [role="tablist"] + div:empty { display: none !important; }
[data-testid="stExpander"] { border: 1px solid var(--cv-line) !important; border-radius: 16px !important; background: rgba(20,31,42,.6) !important; transition: border-color .2s; }
[data-testid="stExpander"]:hover { border-color: rgba(167,139,250,.5) !important; }
[data-testid="stPlotlyChart"], [data-testid="stDataFrame"] { border-radius: 16px; overflow: hidden; }
iframe.stIFrame { border-radius: 24px; }
[data-testid="stToast"] { border: 1.5px solid rgba(56,189,248,.5) !important; border-radius: 14px !important; box-shadow: 4px 4px 0 rgba(56,189,248,.35) !important; }
.cv-badge { font-family: var(--cv-mono); letter-spacing: .1em !important; border-radius: 999px !important; padding: 2px 10px !important; }

/* The effects <script> host should not take up layout space */
[data-testid="stElementContainer"]:has(#cv-fx-host), [data-testid="stElementContainer"]:has(#cv-hero-js) { display: none !important; }

/* No grey-out flicker on charts / live readouts while the replay timer re-renders them */
[data-testid="stElementContainer"][data-stale="true"]:has([data-testid="stPlotlyChart"], [data-testid="stMarkdown"], [data-testid="stSlider"], [data-testid="stDataFrame"]) { opacity: 1 !important; transition: none !important; }

/* Hero CTA row */
.st-key-hero_cta { margin-top: -.2rem; }

/* ===== Small screens ====================================================== */
@media (max-width: 900px) {
  .st-key-topnav { padding-right: .5rem; position: static; }
  .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
  .cv-track-blurb { min-height: 0; }
}
/* ===== Accessibility: honour reduced motion ============================== */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: .001ms !important; animation-iteration-count: 1 !important; transition-duration: .001ms !important; scroll-behavior: auto !important; }
}
</style>
"""
