"""Build the replay page: one self-contained HTML file that steps through what was done on the canvas.

The canvas keeps, for every command, the state before it (``<name>.hist/``) and the command text
(``history``). The page shows each state as an SVG drawing (nodes, wires, groups), highlights the nodes
the command moved or added, lists the problems that appeared or disappeared, and can switch to the
original workflow for comparison. No network, no external scripts: everything is inline.

``build(steps, canvases, original)`` returns the HTML text. canvas.py collects the data (it owns the
state and the checks) and calls it.
"""

import html
import json

# The look follows the skill author's site (Comfy-with-ComfyUI): near-black panels, grey text, one purple
# accent; light colours when the viewer prefers a light theme.
STYLE = """
:root{--bg:#040404;--panel:#111;--panel2:#1d1d1d;--border:#292929;--text:#b0b0b0;--muted:#636363;--head:#dfdfdf;
--accent:#9458a3;--add:#d9a64e;--good:#6fbf8a;--bad:#ff7a7a;--node:#2b2b2b;--node-title:#353535;--canvas:#161616;
--tint:1;--font:"Plus Jakarta Sans","Zen Kaku Gothic New","Hiragino Sans",system-ui,sans-serif}
@media (prefers-color-scheme:light){:root{--bg:#f1f1f1;--panel:#fff;--panel2:#e8e8e8;--border:#d8d8e0;--text:#181818;
--muted:#51515a;--head:#222;--tint:.45;--accent:#7b3f8c;--add:#b3771b;--good:#1f7a3e;--bad:#b42318;--node:#fafafa;--node-title:#e4e4e4;--canvas:#eaeaea}}
*{box-sizing:border-box}html,body{height:100%;margin:0}
body{background:var(--bg);color:var(--text);font:14px/1.5 var(--font);display:grid;grid-template-rows:auto 1fr}
header{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center;padding:10px 16px;background:var(--panel);border-bottom:1px solid var(--border)}
h1{font-size:15px;margin:0;color:var(--head);font-weight:600}
select,button{font:inherit;color:var(--text);background:var(--panel2);border:1px solid var(--border);border-radius:4px;padding:3px 10px}
button:hover{border-color:var(--accent)}button[aria-pressed=true]{background:var(--accent);color:#fff;border-color:var(--accent)}
input[type=range]{flex:1;min-width:160px;accent-color:var(--accent)}
#pos{font-variant-numeric:tabular-nums;color:var(--muted);min-width:7em;text-align:right}
main{display:grid;grid-template-columns:1fr 320px;min-height:0}
@media (max-width:800px){main{grid-template-columns:1fr;grid-template-rows:1fr auto}}
#view{background:var(--canvas);min-height:300px;overflow:hidden;cursor:grab;touch-action:none}
#view:active{cursor:grabbing}svg{width:100%;height:100%;display:block}
aside{background:var(--panel);border-left:1px solid var(--border);padding:12px 16px;overflow:auto}
aside h2{font-size:12px;letter-spacing:.04em;text-transform:uppercase;color:var(--muted);margin:14px 0 4px}
#cmd{font-family:ui-monospace,Menlo,monospace;color:var(--head);white-space:pre-wrap;word-break:break-word}
ul{margin:0;padding-left:1.1em}li{margin:2px 0}.add{color:var(--bad)}.gone{color:var(--good)}
.counts{display:grid;grid-template-columns:1fr auto;gap:0 8px;font-variant-numeric:tabular-nums}
.hint{color:var(--muted);font-size:12px;margin-top:16px}
.tint{opacity:var(--tint)}
"""

SCRIPT = r"""
const D = JSON.parse(document.getElementById('data').textContent);
const $ = id => document.getElementById(id);
const NS = 'http://www.w3.org/2000/svg';
const TYPE_COLOR = {MODEL:'#b39ddb',CLIP:'#ffd500',VAE:'#ff6e6e',CONDITIONING:'#ffa931',LATENT:'#ff9cf9',IMAGE:'#64b5f6',
  MASK:'#81c784',AUDIO:'#ea9999',INT:'#8fc3c3',FLOAT:'#aaee88',STRING:'#99bb88'};
let canvas = D.canvases[0], idx = 0, showOriginal = false, timer = null;
let vb = null;

function stepsOf(c){ return D.steps.filter(s => s.canvas === c); }
function el(tag, attrs, parent){ const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; }

function draw(state, changed){
  const svg = $('svg'); svg.innerHTML = '';
  const g = el('g', {}, svg);
  for (const gr of state.groups || []){
    const [x,y,w,h] = gr.box;
    el('rect', {x, y, width:w, height:h, rx:6, fill:gr.color, 'fill-opacity':.18, stroke:gr.color, 'stroke-opacity':.6}, g);
    const t = el('text', {x:x+10, y:y+24, fill:'currentColor', 'font-size':18}, g); t.textContent = gr.title;
  }
  for (const w of state.wires || []){
    const [x0,y0,x1,y1] = w.p, dx = Math.max(40, Math.abs(x1-x0)/2);
    el('path', {d:`M${x0},${y0} C${x0+dx},${y0} ${x1-dx},${y1} ${x1},${y1}`, fill:'none',
      stroke: TYPE_COLOR[w.t] || '#999', 'stroke-width':2, 'stroke-opacity':.85}, g);
  }
  for (const n of state.nodes){
    const hot = changed && changed.has(n.id);
    if (n.reroute){ el('rect', {x:n.x, y:n.y, width:n.w, height:n.h, rx:8, fill:'var(--node)', stroke: hot ? 'var(--add)' : 'var(--border)', 'stroke-width': hot ? 3 : 1}, g); continue; }
    el('rect', {x:n.x, y:n.y-30, width:n.w, height:n.h+30, rx:6, fill:'var(--node)'}, g);
    if (n.bg) el('rect', {x:n.x, y:n.y-30, width:n.w, height:n.h+30, rx:6, fill:n.bg, class:'tint'}, g);
    el('rect', {x:n.x, y:n.y-30, width:n.w, height:30, rx:6, fill: n.fg || 'var(--node-title)', class: n.fg ? 'tint' : ''}, g);
    el('rect', {x:n.x, y:n.y-30, width:n.w, height:n.h+30, rx:6, fill:'none',
      stroke: hot ? 'var(--add)' : 'var(--border)', 'stroke-width': hot ? 4 : 1}, g);
    const t = el('text', {x:n.x+8, y:n.y-10, fill:'currentColor', 'font-size':14}, g);
    t.textContent = n.label;
  }
  if (!vb) fit(showOriginal ? [D.original] : stepsOf(canvas).map(x => x.state));
  svg.setAttribute('viewBox', vb.join(' '));
}

function fit(states){
  // one frame for every step of the canvas, so the drawing does not jump while stepping
  const xs = [], ys = [];
  for (const st of states) for (const n of st.nodes){ xs.push(n.x, n.x+n.w); ys.push(n.y-30, n.y+n.h); }
  if (!xs.length){ vb = [0,0,1000,600]; return; }
  const x0 = Math.min(...xs)-40, y0 = Math.min(...ys)-40;
  vb = [x0, y0, Math.max(...xs)+40-x0, Math.max(...ys)+40-y0];
}

function list(id, items, cls){
  const ul = $(id); ul.innerHTML = '';
  if (!items.length){ const li = document.createElement('li'); li.textContent = '—'; ul.appendChild(li); return; }
  for (const s of items){ const li = document.createElement('li'); li.className = cls; li.textContent = s; ul.appendChild(li); }
}

function show(i){
  const S = stepsOf(canvas);
  idx = Math.max(0, Math.min(S.length-1, i));
  const s = S[idx];
  $('range').max = S.length-1; $('range').value = idx;
  $('pos').textContent = (idx+1) + ' / ' + S.length;
  if (showOriginal){
    draw(D.original, null);
    $('cmd').textContent = '(original workflow)';
    list('moved', [], ''); list('added', [], 'add'); list('removed', [], 'gone'); $('counts').innerHTML = '';
    return;
  }
  draw(s.state, new Set(s.changed));
  $('cmd').textContent = s.k + ': ' + s.cmd;
  list('moved', s.changed.concat(s.gone.map(x => x + ' (removed)')), '');
  list('added', s.problems_added, 'add');
  list('removed', s.problems_removed, 'gone');
  $('counts').innerHTML = Object.entries(s.counts).map(([k,v]) => `<span>${k}</span><span>${v}</span>`).join('');
}

function stop(){ if (timer){ clearInterval(timer); timer = null; $('play').setAttribute('aria-pressed','false'); } }
$('range').oninput = e => { stop(); show(+e.target.value); };
$('prev').onclick = () => { stop(); show(idx-1); };
$('next').onclick = () => { stop(); show(idx+1); };
$('play').onclick = () => {
  if (timer) return stop();
  $('play').setAttribute('aria-pressed','true');
  timer = setInterval(() => { if (idx >= stepsOf(canvas).length-1) return stop(); show(idx+1); }, 700);
};
$('orig').onclick = () => { showOriginal = !showOriginal; $('orig').setAttribute('aria-pressed', String(showOriginal)); vb = null; show(idx); };
$('fit').onclick = () => { vb = null; show(idx); };
const sel = $('canvas');
for (const c of D.canvases){ const o = document.createElement('option'); o.value = o.textContent = c; sel.appendChild(o); }
sel.onchange = () => { stop(); canvas = sel.value; vb = null; show(0); };
if (D.canvases.length < 2) sel.hidden = true;
document.addEventListener('keydown', e => {
  if (e.key === 'ArrowLeft') $('prev').click();
  if (e.key === 'ArrowRight') $('next').click();
  if (e.key === ' '){ e.preventDefault(); $('play').click(); }
});
// pan and zoom
const view = $('view'); let drag = null;
view.addEventListener('wheel', e => {
  e.preventDefault();
  const r = view.getBoundingClientRect(), f = e.deltaY > 0 ? 1.15 : 1/1.15;
  const mx = vb[0] + (e.clientX - r.left) / r.width * vb[2], my = vb[1] + (e.clientY - r.top) / r.height * vb[3];
  vb = [mx - (mx - vb[0]) * f, my - (my - vb[1]) * f, vb[2] * f, vb[3] * f];
  $('svg').setAttribute('viewBox', vb.join(' '));
}, {passive:false});
view.addEventListener('pointerdown', e => { drag = [e.clientX, e.clientY, vb.slice()]; view.setPointerCapture(e.pointerId); });
view.addEventListener('pointermove', e => {
  if (!drag) return;
  const r = view.getBoundingClientRect();
  vb = [drag[2][0] - (e.clientX - drag[0]) / r.width * drag[2][2], drag[2][1] - (e.clientY - drag[1]) / r.height * drag[2][3], drag[2][2], drag[2][3]];
  $('svg').setAttribute('viewBox', vb.join(' '));
});
view.addEventListener('pointerup', () => { drag = null; });
show(0);
"""


def build(steps, canvases, original, title="Canvas replay"):
    """steps: [{canvas, k, cmd, changed, gone, counts, problems_added, problems_removed, state}];
    state / original: {nodes: [{id, label, x, y, w, h, fg, bg, reroute}], wires: [{p: [x0, y0, x1, y1], t}],
    groups: [{title, box: [x, y, w, h], color}]}."""
    data = json.dumps({"steps": steps, "canvases": canvases, "original": original}, ensure_ascii=False,
                      separators=(",", ":")).replace("</", "<\\/")
    t = html.escape(title)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{t}</title><style>{STYLE}</style></head>
<body>
<header><h1>{t}</h1><select id="canvas" aria-label="canvas"></select>
<button id="prev" aria-label="previous step">&larr;</button><button id="play" aria-pressed="false">Play</button>
<button id="next" aria-label="next step">&rarr;</button><input type="range" id="range" min="0" value="0" aria-label="step">
<span id="pos"></span><button id="orig" aria-pressed="false">Original</button><button id="fit">Fit</button></header>
<main><div id="view"><svg id="svg" xmlns="http://www.w3.org/2000/svg"></svg></div>
<aside><h2>Command</h2><div id="cmd"></div>
<h2>Moved or added</h2><ul id="moved"></ul>
<h2>New problems</h2><ul id="added"></ul>
<h2>Resolved problems</h2><ul id="removed"></ul>
<h2>Counts</h2><div class="counts" id="counts"></div>
<p class="hint">Arrow keys step, Space plays. Drag to pan, wheel to zoom. "Original" shows the workflow before it was rebuilt.</p></aside></main>
<script type="application/json" id="data">{data}</script>
<script>{SCRIPT}</script>
</body></html>
"""
