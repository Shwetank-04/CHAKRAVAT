"""Client-side interaction layer (cursor glow, card spotlight/tilt, count-up, shortcuts).

Injected once per session through ``st.html(..., unsafe_allow_javascript=True)`` (Streamlit >= 1.52).
Everything is progressive enhancement: if JavaScript is blocked the app is fully usable, and all
motion is skipped for users with ``prefers-reduced-motion``.
"""

import streamlit as st

EFFECTS_JS = """
<div id="cv-fx-host" hidden></div>
<script>
(function () {
  try {
    var W = window, D = document;
    if (W.__cvFx && W.__cvFx.dispose) { try { W.__cvFx.dispose(); } catch (e) {} }
    var reduce = W.matchMedia && W.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var cleanups = [];
    function on(t, ev, fn, o) { t.addEventListener(ev, fn, o); cleanups.push(function () { t.removeEventListener(ev, fn, o); }); }

    /* ---- 1. Soft cursor glow + scroll progress ---------------------------------------- */
    var glow = D.getElementById('cv-cursor');
    if (!glow) {
      glow = D.createElement('div'); glow.id = 'cv-cursor';
      glow.style.cssText = 'position:fixed;left:0;top:0;width:560px;height:560px;margin:-280px 0 0 -280px;border-radius:50%;pointer-events:none;z-index:0;opacity:0;transition:opacity .4s;will-change:transform;background:radial-gradient(circle,rgba(56,189,248,.10),rgba(167,139,250,.06) 42%,transparent 70%)';
      D.body.appendChild(glow);
    }
    var bar = D.getElementById('cv-progress');
    if (!bar) {
      bar = D.createElement('div'); bar.id = 'cv-progress';
      bar.style.cssText = 'position:fixed;left:0;top:0;height:3px;width:0;z-index:999999;pointer-events:none;background:linear-gradient(100deg,#38BDF8,#A78BFA,#F472B6);box-shadow:0 0 12px rgba(167,139,250,.8);transition:width .08s linear';
      D.body.appendChild(bar);
    }
    var tx = 0, ty = 0, cx = 0, cy = 0, raf = 0;
    function loop() { cx += (tx - cx) * 0.12; cy += (ty - cy) * 0.12; glow.style.transform = 'translate3d(' + cx + 'px,' + cy + 'px,0)'; raf = W.requestAnimationFrame(loop); }
    if (!reduce) {
      on(W, 'mousemove', function (e) { tx = e.clientX; ty = e.clientY; glow.style.opacity = 1; }, { passive: true });
      on(D.documentElement, 'mouseleave', function () { glow.style.opacity = 0; });
      loop(); cleanups.push(function () { W.cancelAnimationFrame(raf); });
    }
    on(D, 'scroll', function (e) {
      var s = e.target && e.target.scrollHeight ? e.target : D.documentElement;
      var max = s.scrollHeight - s.clientHeight;
      if (max > 40 && s.matches && s.matches('[data-testid="stMain"], html, body')) { bar.style.width = Math.min(100, (s.scrollTop / max) * 100) + '%'; }
    }, { capture: true, passive: true });

    /* ---- 2. Card spotlight (+ gentle 3-D tilt on track / storm cards) ------------------- */
    var CARD = '.cv-card,.cv-metric-card,[class*="st-key-cvcard_"],[class*="st-key-trk_"],[class*="st-key-storm_"]';
    var TILT = '[class*="st-key-trk_"],[class*="st-key-storm_"]';
    on(D, 'mousemove', function (e) {
      var c = e.target && e.target.closest ? e.target.closest(CARD) : null;
      if (!c) return;
      var r = c.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
      c.style.setProperty('--mx', x + 'px'); c.style.setProperty('--my', y + 'px');
      if (!reduce && c.matches(TILT)) {
        c.style.transform = 'perspective(900px) rotateX(' + (-(y / r.height - 0.5) * 5).toFixed(2) + 'deg) rotateY(' + ((x / r.width - 0.5) * 7).toFixed(2) + 'deg) translateY(-4px)';
      }
    }, { passive: true });
    on(D, 'mouseout', function (e) {
      var c = e.target && e.target.closest ? e.target.closest(TILT) : null;
      if (c && (!e.relatedTarget || !c.contains(e.relatedTarget))) { c.style.transform = ''; }
    }, { passive: true });

    /* ---- 3. Count-up numbers (values stay in the DOM, so no-JS users see the real number) */
    function countUp(el) {
      var to = parseFloat(el.getAttribute('data-count'));
      if (reduce || !isFinite(to)) return;
      var t0 = W.performance.now(), dur = 950;
      (function step(t) {
        var k = Math.min(1, (t - t0) / dur), v = Math.round(to * (1 - Math.pow(1 - k, 3)));
        el.textContent = v.toLocaleString();
        if (k < 1) W.requestAnimationFrame(step); else el.textContent = to.toLocaleString();
      })(t0);
    }
    var io = new W.IntersectionObserver(function (es) {
      es.forEach(function (en) { if (en.isIntersecting) { countUp(en.target); io.unobserve(en.target); } });
    }, { threshold: 0.35 });
    function scan() { D.querySelectorAll('.cv-count[data-count]:not([data-cv-seen])').forEach(function (el) { el.setAttribute('data-cv-seen', '1'); io.observe(el); }); }
    var mo = new W.MutationObserver(function () { scan(); });
    mo.observe(D.body, { childList: true, subtree: true }); scan();
    cleanups.push(function () { mo.disconnect(); io.disconnect(); });

    /* ---- 4. Keyboard shortcuts: 1-9 jump between sections, ? shows help -------------- */
    var toast = null, toastT = 0;
    function say(msg) {
      if (!toast) {
        toast = D.createElement('div');
        toast.style.cssText = 'position:fixed;left:50%;bottom:28px;transform:translateX(-50%) translateY(20px);z-index:999998;padding:.65rem 1.1rem;border-radius:14px;border:1.5px solid rgba(56,189,248,.6);background:rgba(11,17,23,.94);color:#e8f0f8;font:700 .82rem ui-monospace,Consolas,monospace;letter-spacing:.04em;box-shadow:4px 4px 0 rgba(56,189,248,.4);opacity:0;transition:all .3s cubic-bezier(.16,1,.3,1);pointer-events:none;white-space:pre';
        D.body.appendChild(toast);
      }
      toast.textContent = msg; toast.style.opacity = 1; toast.style.transform = 'translateX(-50%) translateY(0)';
      W.clearTimeout(toastT); toastT = W.setTimeout(function () { toast.style.opacity = 0; toast.style.transform = 'translateX(-50%) translateY(20px)'; }, 2200);
    }
    on(D, 'keydown', function (e) {
      var t = e.target || {};
      if (/INPUT|TEXTAREA|SELECT/.test(t.tagName || '') || t.isContentEditable || e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.key >= '1' && e.key <= '9') {
        var labels = D.querySelectorAll('.st-key-topnav label[data-testid="stRadioOption"]');
        var l = labels[parseInt(e.key, 10) - 1];
        if (l) { l.click(); say('\\u2192 ' + l.textContent.trim()); }
      } else if (e.key === '?') {
        say('Shortcuts\\n1-9  jump to a section\\n?    this help');
      }
    });

    W.__cvFx = { dispose: function () { cleanups.forEach(function (f) { try { f(); } catch (e) {} }); cleanups = []; } };
  } catch (err) { if (window.console) console.warn('CHAKRAVAT effects disabled:', err); }
})();
</script>
"""


def inject_effects() -> None:
    """Mount the interaction layer once. Safe to call on every rerun (the script is idempotent)."""
    try:
        st.html(EFFECTS_JS, unsafe_allow_javascript=True)
    except TypeError:  # Streamlit < 1.52 has no unsafe_allow_javascript: degrade gracefully
        pass
    except Exception:  # non-runtime contexts (unit tests)
        pass
