"""Animated landing hero: a particle cyclone that reacts to the cursor, typed taglines, live UTC clock."""

import json
from typing import Dict

import streamlit as st

_HERO_SCRIPT = """
<div id="cv-hero-js" hidden></div>
<script>
(function boot(tries){
  /* st.html may run this script a tick before it inserts the markup, so wait for the element. */
  var root=document.getElementById('cv-hero');
  if(!root){ if((tries||0)< 60) setTimeout(function(){boot((tries||0)+1);},50); return; }
  if(root.getAttribute('data-booted')) return; root.setAttribute('data-booted','1');
  var cv=document.getElementById('cv-hero-canvas'), ctx=cv.getContext('2d');
  var reduce=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var W=0,H=0,dpr=1;
  function size(){var r=cv.getBoundingClientRect();dpr=Math.min(2,window.devicePixelRatio||1);W=cv.width=Math.max(1,Math.round(r.width*dpr));H=cv.height=Math.max(1,Math.round(r.height*dpr));}
  size(); window.addEventListener('resize',size);
  var ARMS=5,N=2100,parts=[],i;
  for(i=0;i< N;i++){parts.push({arm:i%ARMS,r:Math.pow(Math.random(),0.6),j:(Math.random()-.5),s:Math.random()*1.7+.5});}
  var mx=0,my=0,tx=0,ty=0,t=0,pulses=[];
  root.addEventListener('mousemove',function(e){var b=root.getBoundingClientRect();tx=(e.clientX-b.left)/b.width-.5;ty=(e.clientY-b.top)/b.height-.5;});
  root.addEventListener('mouseleave',function(){tx=0;ty=0;});
  root.addEventListener('click',function(){pulses.push(0);});
  function draw(){
    ctx.clearRect(0,0,W,H);
    var cx=W/2+mx*W*.07, cy=H/2+my*H*.05, R=Math.min(W,H*.8)*.46, sq=0.86-my*.12, k, p, a, rr, x, y, h, al;
    ctx.lineWidth=dpr;
    for(k=1;k<=6;k++){ctx.strokeStyle='rgba(130,160,190,'+(0.05+0.03*(k%2))+')';ctx.beginPath();ctx.ellipse(cx,cy,R*k/6*1.04,R*k/6*sq,mx*.35,0,6.2832);ctx.stroke();}
    for(i=0;i< N;i++){
      p=parts[i];
      a=p.arm*(6.2832/ARMS)+p.r*5.4+p.j*(0.15+p.r*0.55)-t*(1.7-p.r*1.35);
      rr=p.r*R; x=cx+Math.cos(a)*rr; y=cy+Math.sin(a)*rr*sq;
      h=198+(1-p.r)*132; al=0.38+(1-p.r)*0.62;
      ctx.fillStyle='hsla('+h+',95%,'+(62+(1-p.r)*10)+'%,'+al+')';
      ctx.fillRect(x,y,p.s*dpr*1.25,p.s*dpr*1.25);
    }
    var g=ctx.createRadialGradient(cx,cy,0,cx,cy,R*.17);
    g.addColorStop(0,'rgba(11,17,23,1)');g.addColorStop(.6,'rgba(11,17,23,.88)');g.addColorStop(1,'rgba(244,114,182,0)');
    ctx.fillStyle=g;ctx.beginPath();ctx.arc(cx,cy,R*.17,0,6.2832);ctx.fill();
    for(k=pulses.length-1;k>=0;k--){
      pulses[k]+=0.018; if(pulses[k]>1){pulses.splice(k,1);continue;}
      ctx.strokeStyle='rgba(244,114,182,'+(1-pulses[k])*.8+')';ctx.lineWidth=2.2*dpr;
      ctx.beginPath();ctx.ellipse(cx,cy,R*pulses[k]*1.15,R*pulses[k]*1.15*sq,0,0,6.2832);ctx.stroke();ctx.lineWidth=dpr;
    }
  }
  function frame(){
    if(!document.body.contains(root)){window.removeEventListener('resize',size);return;}
    t+=0.011; mx+=(tx-mx)*.06; my+=(ty-my)*.06; draw(); window.requestAnimationFrame(frame);
  }
  if(reduce){t=2.4;draw();}else{frame();}
  var phrases=['Track the storm.','Forecast the intensity.','Dispatch the relief.','Protect the coast.'],pi=0,ci=0,del=false,el=document.getElementById('cv-typed');
  function type(){
    if(!document.body.contains(root)) return;
    var s=phrases[pi];
    if(reduce){el.textContent=s;return;}
    if(!del){ci++;el.textContent=s.slice(0,ci);if(ci===s.length){del=true;return void setTimeout(type,1500);}}
    else{ci--;el.textContent=s.slice(0,ci);if(ci===0){del=false;pi=(pi+1)%phrases.length;}}
    setTimeout(type,del?32:62);
  }
  type();
  var clk=document.getElementById('cv-clock');
  function tick(){if(!document.body.contains(root))return;var d=new Date();clk.textContent=d.toISOString().slice(11,19);setTimeout(tick,1000);}
  tick();
})(0);
</script>
"""

_HERO_HTML = """
<style>
.cv-hero{position:relative;overflow:hidden;border-radius:28px;padding:clamp(1.4rem,3.2vw,2.6rem);min-height:430px;margin:0 0 1.2rem;
  border:1.5px solid rgba(130,160,190,.28);background:linear-gradient(135deg,rgba(20,31,42,.82),rgba(11,17,23,.55));
  box-shadow:0 24px 70px rgba(0,0,0,.45),inset 0 1px 0 rgba(255,255,255,.07);isolation:isolate;
  font-family:ui-rounded,"SF Pro Rounded","Segoe UI Variable Display","Segoe UI",system-ui,sans-serif}
.cv-hero canvas{position:absolute;right:-6%;top:50%;transform:translateY(-50%);width:62%;height:130%;z-index:-1;pointer-events:none}
.cv-hero-copy{max-width:640px;position:relative}
.cv-hero-chip{display:inline-flex;align-items:center;gap:.55rem;font:800 .68rem ui-monospace,"JetBrains Mono",Consolas,monospace;letter-spacing:.14em;text-transform:uppercase;
  color:#7dd3fc;border:1px solid rgba(56,189,248,.45);background:rgba(56,189,248,.09);padding:.38rem .85rem;border-radius:999px}
.cv-hero-chip .dot{width:8px;height:8px;border-radius:50%;background:#38BDF8;animation:cvHeroPulse 2s infinite}
@keyframes cvHeroPulse{0%{box-shadow:0 0 0 0 rgba(56,189,248,.7)}70%{box-shadow:0 0 0 9px rgba(56,189,248,0)}100%{box-shadow:0 0 0 0 rgba(56,189,248,0)}}
.cv-hero-title{margin:.9rem 0 .1rem;font-size:clamp(2.7rem,8.4vw,6.2rem);line-height:.95;font-weight:900;letter-spacing:-.055em;white-space:nowrap;
  background:linear-gradient(100deg,#38BDF8,#A78BFA 45%,#F472B6 75%,#38BDF8);background-size:220% 100%;-webkit-background-clip:text;background-clip:text;color:transparent;
  animation:cvShimmer 7s linear infinite}
.cv-hero-title span{display:inline-block;transition:transform .35s cubic-bezier(.16,1,.3,1);cursor:default}
.cv-hero-title span:hover{transform:translateY(-.14em) rotate(-5deg) scale(1.08)}
@keyframes cvShimmer{to{background-position:-220% 0}}
.cv-hero-type{min-height:2.2rem;font-size:clamp(1.15rem,2.4vw,1.65rem);font-weight:750;color:#f1f5f9;letter-spacing:-.02em}
.cv-caret{display:inline-block;width:3px;height:1.1em;margin-left:4px;vertical-align:-.15em;background:#F472B6;animation:cvCaret 1s steps(1) infinite}
@keyframes cvCaret{50%{opacity:0}}
.cv-hero-lede{margin:.7rem 0 1.15rem;color:#a9b9ca;font-size:.97rem;line-height:1.6;max-width:56ch}
.cv-hero-stats{display:flex;flex-wrap:wrap;gap:.65rem}
.cv-hero-stat{min-width:104px;padding:.65rem .95rem;border-radius:16px;border:1px solid rgba(130,160,190,.28);background:rgba(11,17,23,.55);backdrop-filter:blur(8px);
  transition:transform .3s cubic-bezier(.16,1,.3,1),border-color .2s,box-shadow .3s}
.cv-hero-stat:hover{transform:translateY(-4px) rotate(-1deg);border-color:#A78BFA;box-shadow:4px 4px 0 rgba(167,139,250,.5)}
.cv-hero-stat b{display:block;font-size:1.65rem;font-weight:900;letter-spacing:-.04em;color:#fff;line-height:1.1}
.cv-hero-stat small{font:700 .6rem ui-monospace,Consolas,monospace;letter-spacing:.13em;text-transform:uppercase;color:#8aa0b6}
.cv-hero-clock{position:absolute;right:1.4rem;bottom:1rem;font:700 .72rem ui-monospace,Consolas,monospace;letter-spacing:.12em;color:#7f93a8;text-align:right}
.cv-hero-clock b{color:#7dd3fc;font-size:1.05rem;letter-spacing:.06em}
.cv-hero-hint{position:absolute;right:1.4rem;top:1rem;font:700 .62rem ui-monospace,Consolas,monospace;letter-spacing:.14em;color:#6b7f94;text-transform:uppercase}
@media(max-width:820px){.cv-hero canvas{width:100%;right:-30%;opacity:.5}.cv-hero-clock,.cv-hero-hint{display:none}}
@media(prefers-reduced-motion:reduce){.cv-hero-title{animation:none}}
</style>
<section class="cv-hero" id="cv-hero">
  <canvas id="cv-hero-canvas"></canvas>
  <div class="cv-hero-hint">move cursor · click to pulse</div>
  <div class="cv-hero-copy">
    <div class="cv-hero-chip"><span class="dot"></span>Replay mode · IBTrACS best-track · offline-ready</div>
    <h1 class="cv-hero-title" aria-label="CHAKRAVAT">__LETTERS__</h1>
    <div class="cv-hero-type"><span id="cv-typed"></span><span class="cv-caret"></span></div>
    <p class="cv-hero-lede">North Indian Ocean cyclone intelligence: replay historical storms, benchmark honest ML forecasts, and rehearse the human-in-the-loop alert and relief workflow.</p>
    <div class="cv-hero-stats">
      <div class="cv-hero-stat"><b class="cv-count" data-count="__STORMS__">__STORMS__</b><small>Benchmark storms</small></div>
      <div class="cv-hero-stat"><b class="cv-count" data-count="__FIXES__">__FIXES__</b><small>Synoptic fixes</small></div>
      <div class="cv-hero-stat"><b class="cv-count" data-count="__PEAK__">__PEAK__</b><small>Peak wind (kt)</small></div>
      <div class="cv-hero-stat"><b class="cv-count" data-count="2">2</b><small>Ocean basins</small></div>
    </div>
  </div>
  <div class="cv-hero-clock">UTC<br><b id="cv-clock">--:--:--</b></div>
</section>
"""


def render_hero(stats: Dict[str, int]) -> None:
    """Render the animated hero. ``stats`` keys: storms, fixes, peak_kt (all real, dataset-derived)."""
    letters = "".join(f"<span>{c}</span>" for c in "CHAKRAVAT")
    body = (
        _HERO_HTML.replace("__LETTERS__", letters)
        .replace("__STORMS__", str(int(stats.get("storms", 0))))
        .replace("__FIXES__", str(int(stats.get("fixes", 0))))
        .replace("__PEAK__", str(int(stats.get("peak_kt", 0))))
    )
    st.html(body)  # markup + CSS only (no JavaScript needed to look right)
    try:
        st.html(_HERO_SCRIPT, unsafe_allow_javascript=True)  # animation layer, progressive enhancement
    except TypeError:  # Streamlit < 1.52: static hero, no canvas animation
        pass
