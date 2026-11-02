"""Generate the stream deck (01-pizarra.html) and the run-of-show (guion.html).

Run with: python3 build.py (from this folder or any other).
Inputs: content.py (DECK, BLOCKS, SLIDES) and theme.py (brand). Both outputs are
self-contained: fonts, logo and texture are embedded, no network.
"""
from pathlib import Path
import base64
import html
import json
import re

import sys
sys.path.insert(0, str(Path(__file__).parent))
sys.dont_write_bytecode = True
import theme  # noqa: E402
from content import BLOCKS, DECK, SLIDES  # noqa: E402

ROOT = Path(__file__).parent
BRAILLE = theme.TEXTURE.read_text().rstrip('\n') if theme.TEXTURE else ''
C = theme.COLORS


def b64(path):
    return base64.b64encode(path.read_bytes()).decode()


FONTS = ''.join(
    f'@font-face {{ font-family: "{family}"; font-weight: {weight}; font-display: block; '
    f"src: url(data:font/woff2;base64,{b64(path)}) format('woff2'); }}\n"
    for family, weight, path in theme.FONTS)
LOGO = 'data:image/svg+xml;base64,' + b64(theme.LOGO)

TOKENS = f'''
:root {{ --background: {C['background']}; --background-2: {C['background_2']}; --background-3: {C['background_3']}; --text: {C['text']}; --text-2: {C['text_2']};
  --border: {C['border']}; --brand: {C['brand']}; --spark: {C['spark']}; --glow: {C['brand_glow']}; --paper: {C['paper']};
  --sans: "{theme.SANS}", system-ui, sans-serif; --mono: "{theme.MONO}", ui-monospace, Menlo, monospace;
  --ease: cubic-bezier(.16,1,.3,1); --glow-sm: 0 0 0 1px rgba(var(--glow),.4), 0 8px 24px -10px rgba(var(--glow),.6); }}
'''


def esc(text):
    """Escape text and turn *word* into the single violet heading accent."""
    return re.sub(r'\*(.+?)\*', r'<em>\1</em>', html.escape(text))


def card(title, body):
    return f'<div class="card"><h3>{esc(title)}</h3><p>{esc(body)}</p></div>'


def render(slide, index, total):
    kind = slide['type']
    kicker = slide.get('kicker', '')
    head = f'<p class="kicker">{esc(kicker)}</p>' if kicker else ''
    title = f'<h2 id="t{index}">{esc(slide["title"])}</h2>' if 'title' in slide else ''
    lead = f'<p class="lead">{esc(slide["lead"])}</p>' if 'lead' in slide else ''
    if kind == 'cover':
        rows = ''.join(f'<span style="animation-delay:{r * 55}ms">{html.escape(row)}</span>' for r, row in enumerate(BRAILLE.split('\n')))
        inner = f'<div class="cover-text">{head}<h1 id="t{index}">{esc(slide["title"])}</h1>{lead}<p class="meta">{esc(slide["meta"])}</p></div><pre class="braille" aria-hidden="true">{rows}</pre>'
    elif kind == 'section':
        inner = f'<p class="section-number" aria-hidden="true">{esc(slide["number"])}</p><div>{head}{title}{lead}<p class="meta">{esc(slide["meta"])}</p></div>'
    elif kind == 'statement':
        inner = f'{head}<p class="statement" id="t{index}">{esc(slide["title"])}</p>{lead}'
    elif kind == 'cards':
        inner = f'{head}{title}{lead}<div class="cards">{"".join(card(*c) for c in slide["cards"])}</div>'
    elif kind == 'flow':
        nodes = '<span class="arrow" aria-hidden="true">→</span>'.join(
            f'<div class="node{" node-accent" if n.get("accent") else ""}"><h3>{esc(n["name"])}</h3><p>{esc(n["role"])}</p></div>' for n in slide['nodes'])
        inner = f'{head}{title}{lead}<div class="flow">{nodes}</div><p class="caption">{esc(slide["caption"])}</p>'
    elif kind == 'compare':
        cols = ''.join(f'<div class="col"><h3>{esc(c["name"])}</h3><ul>{"".join(f"<li>{esc(i)}</li>" for i in c["items"])}</ul></div>' for c in slide['columns'])
        inner = f'{head}{title}<div class="compare">{cols}</div><p class="decide"><span>Decidí por</span> {esc(slide["decide"])}</p>'
    elif kind == 'table':
        thead = ''.join(f'<th scope="col">{esc(h)}</th>' for h in slide['columns'])
        rows = ''.join('<tr>' + ''.join((f'<th scope="row">{esc(c)}</th>' if j == 0 else f'<td>{esc(c)}</td>') for j, c in enumerate(r)) + '</tr>' for r in slide['rows'])
        inner = f'{head}{title}<table><thead><tr>{thead}</tr></thead><tbody>{rows}</tbody></table>'
    elif kind == 'demo':
        steps = ''.join(f'<li>{esc(s)}</li>' for s in slide['steps'])
        proof = ''.join(f'<li>{esc(s)}</li>' for s in slide['evidence'])
        inner = (f'<p class="kicker">Demo en vivo · {esc(slide["task"])}</p>{title}'
                 f'<div class="demo"><div><h3>Qué hacemos</h3><ol>{steps}</ol></div>'
                 f'<div><h3>Qué evidencia esperamos</h3><ul class="checks">{proof}</ul></div></div>'
                 f'<p class="status"><span class="dot" aria-hidden="true"></span>Estado: por demostrar en vivo</p>')
    else:
        raise ValueError(f'unknown slide type {kind}')
    hidden = '' if index == 0 else ' hidden'
    watermark = '' if kind in ('cover', 'section') or not BRAILLE else f'<pre class="braille watermark" aria-hidden="true">{html.escape(BRAILLE)}</pre>'
    return (f'<section class="slide slide--{kind}" aria-labelledby="t{index}" data-block="{html.escape(slide["block"])}"'
            f' data-notes="{html.escape(slide["notes"], quote=True)}"{hidden}>{watermark}{inner}'
            f'<p class="folio">{html.escape(slide["block"])} · {index + 1:02} / {total:02}</p></section>')


DECK_CSS = '''
* { box-sizing: border-box; }
html, body { margin: 0; height: 100%; background: #000; overflow: hidden; }
body { font-family: var(--sans); color: var(--text); }
.viewport { position: fixed; inset: 0; }
.stage { width: 1600px; height: 900px; position: absolute; left: 50%; top: 50%; background: var(--background); overflow: hidden; transform-origin: center; transform: translate(-50%, -50%); }
header.bar { position: absolute; top: 0; left: 0; right: 0; height: 80px; display: flex; align-items: center; justify-content: space-between; padding: 0 64px; z-index: 2; }
.wordmark { display: flex; align-items: center; gap: 12px; font-weight: 500; font-size: 22px; letter-spacing: -.03em; }
.wordmark img { width: 36px; height: 36px; border-radius: 8px; }
.wordmark b { font-weight: 500; color: var(--brand); }
.bar .block-name { font-family: var(--mono); font-size: 15px; color: var(--text-2); }
.slide { position: absolute; inset: 80px 0 0; padding: 40px 112px 80px; display: flex; flex-direction: column; justify-content: center; }
.slide[hidden] { display: none; }
.kicker { font-family: var(--mono); font-size: 18px; color: var(--spark); margin: 0 0 20px; }
.kicker::after { content: "_"; animation: blink 1000ms steps(1) infinite; }
@keyframes blink { 50% { opacity: 0; } }
h1, h2, h3, .statement { font-weight: 500; letter-spacing: -.03em; text-wrap: balance; margin: 0; }
h1 { font-size: 88px; line-height: 1.02; }
h2 { font-size: 60px; line-height: 1.06; max-width: 1300px; }
h3 { font-size: 28px; line-height: 1.2; margin-bottom: 12px; }
em { font-style: normal; color: var(--brand); }
.lead { font-size: 30px; line-height: 1.4; color: var(--text-2); max-width: 1180px; margin: 24px 0 0; text-wrap: pretty; }
.meta { font-family: var(--mono); font-size: 18px; color: var(--text-2); margin: 32px 0 0; }
.cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 32px; margin-top: 48px; }
.card, .col, .node, .demo > div { background: var(--background-2); border: 1px solid var(--border); border-radius: 16px; padding: 28px; }
.card p, .node p { font-size: 22px; line-height: 1.5; color: var(--text-2); margin: 0; text-wrap: pretty; }
.slide--cover { flex-direction: row; align-items: center; gap: 64px; padding-top: 0; }
.cover-text { flex: 1.15; }
.slide--cover .lead { font-size: 32px; }
.braille { font-family: var(--mono); font-size: 13px; line-height: 1.12; letter-spacing: 0; white-space: pre; margin: 0; color: var(--text); text-shadow: 0 0 24px rgba(var(--glow),.35); }
.slide--cover .braille span { display: block; opacity: 0; animation: rise 480ms var(--ease) forwards; }
@keyframes rise { from { opacity: 0; transform: translateY(12px); filter: blur(8px); } to { opacity: 1; transform: none; filter: none; } }
.watermark { position: absolute; right: -40px; bottom: -60px; opacity: .05; pointer-events: none; }
.slide--section { flex-direction: row; align-items: center; gap: 72px; }
.section-number { font-family: var(--mono); font-size: 220px; line-height: 1; color: var(--brand); margin: 0; text-shadow: 0 0 48px rgba(var(--glow),.45); }
.statement { font-size: 76px; line-height: 1.08; max-width: 1350px; }
.flow { display: flex; align-items: stretch; gap: 16px; margin-top: 48px; }
.flow .node { flex: 1; }
.node-accent { border-color: var(--brand); box-shadow: var(--glow-sm); }
.arrow { align-self: center; font-family: var(--mono); font-size: 36px; color: var(--text-2); }
.caption { font-size: 22px; color: var(--text-2); margin: 32px 0 0; }
.compare { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; margin-top: 40px; }
ul, ol { margin: 0; padding-left: 28px; font-size: 23px; line-height: 1.5; color: var(--text-2); }
li + li { margin-top: 10px; }
.decide { font-size: 26px; margin: 32px 0 0; }
.decide span { font-family: var(--mono); font-size: 18px; color: var(--spark); margin-right: 12px; }
table { width: 100%; border-collapse: collapse; margin-top: 40px; font-size: 22px; line-height: 1.4; }
th, td { text-align: left; padding: 18px 20px; border-bottom: 1px solid var(--border); vertical-align: top; }
thead th { font-family: var(--mono); font-size: 16px; font-weight: 400; color: var(--text-2); }
tbody th { font-weight: 500; width: 18%; }
td { color: var(--text-2); }
tbody tr:nth-child(odd) { background: var(--background-2); }
.demo { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; margin-top: 40px; }
.checks { list-style: none; padding: 0; }
.checks li::before { content: "[ ] "; font-family: var(--mono); color: var(--text-2); }
.status { font-family: var(--mono); font-size: 18px; color: var(--text-2); margin: 28px 0 0; display: flex; align-items: center; gap: 12px; }
.dot { width: 10px; height: 10px; border-radius: 50%; background: var(--spark); }
.folio { position: absolute; left: 112px; bottom: 32px; margin: 0; font-family: var(--mono); font-size: 14px; color: var(--text-2); }
.progress { position: absolute; left: 0; bottom: 0; height: 4px; background: var(--brand); transition: width 480ms var(--ease); z-index: 2; }
.toolbar { position: fixed; right: 16px; bottom: 16px; display: flex; gap: 8px; opacity: 0; transition: opacity 240ms var(--ease); z-index: 10; }
body.pointer .toolbar, .toolbar:focus-within { opacity: 1; }
.toolbar button { font: 500 15px var(--sans); color: var(--text); background: var(--background-2); border: 1px solid var(--text-2); border-radius: 8px; padding: 10px 14px; cursor: pointer; transition: all 240ms var(--ease); }
@media (hover: hover) { .toolbar button:hover { background: var(--text); color: var(--background); transform: translateY(-2px); box-shadow: var(--glow-sm); } }
:focus-visible { outline: 2px solid var(--text); outline-offset: 3px; }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation: none !important; transition: none !important; } .slide--cover .braille span { opacity: 1; } }
@media print {
  html, body { height: auto; overflow: visible; background: var(--background); }
  .viewport { position: static; } .stage { position: static; transform: none !important; height: auto; overflow: visible; }
  .slide, .slide[hidden] { position: relative; inset: auto; display: flex; height: 900px; break-after: page; padding-top: 120px; }
  .toolbar, .progress, header.bar { display: none; }
  @page { size: 1600px 900px; margin: 0; }
}
'''

DECK_JS = '''
const stage = document.querySelector('.stage');
const DECK_TITLE = document.body.dataset.title;
const slides = [...document.querySelectorAll('.slide')];
const blockName = document.querySelector('.block-name');
const progress = document.querySelector('.progress');
let current = 0;
let presenter = null;

function fit() {
  const scale = Math.min(innerWidth / 1600, innerHeight / 900);
  stage.style.transform = `translate(-50%, -50%) scale(${scale})`;
}
function state() {
  const slide = slides[current];
  const next = slides[current + 1];
  return { type: 'state', index: current, total: slides.length, block: slide.dataset.block,
    title: slide.querySelector('[id^="t"]').textContent, notes: slide.dataset.notes,
    next: next ? next.querySelector('[id^="t"]').textContent : 'Fin de la presentación' };
}
function show(index, fromHash) {
  current = Math.max(0, Math.min(slides.length - 1, index));
  slides.forEach((slide, i) => { slide.hidden = i !== current; });
  blockName.textContent = slides[current].dataset.block;
  progress.style.width = `${((current + 1) / slides.length) * 100}%`;
  document.title = `${current + 1}/${slides.length} · ${DECK_TITLE}`;
  if (!fromHash) history.replaceState(null, '', `#${current + 1}`);
  if (presenter && !presenter.closed) presenter.postMessage(state(), '*');
}
function openPresenter() {
  presenter = window.open('', 'deck-presenter', 'width=980,height=640');
  if (!presenter) { alert('El navegador bloqueó la ventana del presentador. Permití ventanas emergentes para este archivo.'); return; }
  presenter.document.open();
  presenter.document.write(document.querySelector('#presenter-template').textContent);
  presenter.document.close();
  setTimeout(() => presenter.postMessage(state(), '*'), 150);
}
addEventListener('message', event => {
  if (!presenter || event.source !== presenter) return;
  if (event.data === 'next') show(current + 1);
  if (event.data === 'previous') show(current - 1);
  if (event.data === 'ready') presenter.postMessage(state(), '*');
});
document.querySelector('#previous').onclick = () => show(current - 1);
document.querySelector('#next').onclick = () => show(current + 1);
document.querySelector('#open-presenter').onclick = openPresenter;
document.querySelector('#fullscreen').onclick = async () => {
  try { if (document.fullscreenElement) await document.exitFullscreen(); else await document.documentElement.requestFullscreen(); }
  catch { /* Fullscreen denied: the browser's own fullscreen still works. */ }
};
document.addEventListener('keydown', event => {
  if (event.target instanceof Element && event.target.closest('button') && [' ', 'Enter'].includes(event.key)) return;
  if (event.altKey || event.ctrlKey || event.metaKey) return;
  const key = event.key;
  if (['ArrowRight', 'PageDown', ' ', 'ArrowLeft', 'PageUp', 'Home', 'End'].includes(key)) event.preventDefault();
  if (['ArrowRight', 'PageDown', ' '].includes(key)) show(current + 1);
  if (['ArrowLeft', 'PageUp'].includes(key)) show(current - 1);
  if (key === 'Home') show(0);
  if (key === 'End') show(slides.length - 1);
  if (key === 'p' || key === 'P') openPresenter();
  if (key === 'f' || key === 'F') document.querySelector('#fullscreen').click();
});
let idle;
addEventListener('pointermove', () => {
  document.body.classList.add('pointer');
  clearTimeout(idle);
  idle = setTimeout(() => document.body.classList.remove('pointer'), 2000);
});
addEventListener('resize', fit);
addEventListener('hashchange', () => show(parseInt(location.hash.slice(1), 10) - 1 || 0, true));
fit();
show(parseInt(location.hash.slice(1), 10) - 1 || 0, true);
'''

PRESENTER = '''<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Presentador</title><style>
:root { color-scheme: dark; }
body { margin: 0; padding: 32px; background: %BG%; color: #fff; font: 400 20px/1.5 system-ui, sans-serif; display: grid; gap: 20px; grid-template-rows: auto auto 1fr auto; height: 100vh; box-sizing: border-box; }
.top { display: flex; justify-content: space-between; font-family: ui-monospace, Menlo, monospace; color: rgba(255,255,255,.6); font-size: 16px; }
#clock { color: %SPARK%; }
h1 { font-weight: 500; font-size: 34px; letter-spacing: -.03em; margin: 0; }
#notes { background: %BG2%; border: 1px solid rgba(255,255,255,.2); border-radius: 16px; padding: 24px; font-size: 24px; overflow: auto; }
.bottom { display: flex; justify-content: space-between; align-items: center; gap: 16px; color: rgba(255,255,255,.6); }
button { font: 500 16px system-ui, sans-serif; color: #fff; background: %BG2%; border: 1px solid rgba(255,255,255,.6); border-radius: 8px; padding: 10px 16px; cursor: pointer; }
button:focus-visible { outline: 2px solid #fff; outline-offset: 3px; }
</style></head><body>
<div class="top"><span id="where"></span><span>Transcurrido <span id="clock">00:00:00</span> · <button id="reset" type="button">Reiniciar reloj</button></span></div>
<h1 id="title"></h1>
<div id="notes" aria-live="polite"></div>
<div class="bottom"><span>Siguiente: <strong id="next"></strong></span><span><button id="prev" type="button">← Anterior</button> <button id="fwd" type="button">Siguiente →</button></span></div>
<script>
let start = Date.now();
const pad = n => String(n).padStart(2, '0');
setInterval(() => { const s = Math.floor((Date.now() - start) / 1000); document.getElementById('clock').textContent = `${pad(Math.floor(s / 3600))}:${pad(Math.floor(s / 60) % 60)}:${pad(s % 60)}`; }, 500);
document.getElementById('reset').onclick = () => { start = Date.now(); };
const send = m => window.opener && window.opener.postMessage(m, '*');
document.getElementById('prev').onclick = () => send('previous');
document.getElementById('fwd').onclick = () => send('next');
addEventListener('keydown', e => { if (e.target instanceof Element && e.target.closest('button')) return; if (['ArrowRight', 'PageDown', ' '].includes(e.key)) { e.preventDefault(); send('next'); } if (['ArrowLeft', 'PageUp'].includes(e.key)) { e.preventDefault(); send('previous'); } });
addEventListener('message', e => { const d = e.data; if (!d || d.type !== 'state') return;
  document.getElementById('where').textContent = `${d.block} · ${d.index + 1} / ${d.total}`;
  document.getElementById('title').textContent = d.title;
  document.getElementById('notes').textContent = d.notes;
  document.getElementById('next').textContent = d.next; });
send('ready');
</script></body></html>'''


def presenter_html():
    page = PRESENTER.replace('%BG%', C['background']).replace('%BG2%', C['background_2']).replace('%SPARK%', C['spark'])
    return page.replace('</script>', '<\\/script>')


def build_deck():
    total = len(SLIDES)
    sections = ''.join(render(s, i, total) for i, s in enumerate(SLIDES))
    page = f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(DECK['title'])} | {theme.BRAND}</title><link rel="icon" href="{LOGO}">
<style>{FONTS}{TOKENS}{DECK_CSS}</style></head>
<body data-title="{html.escape(DECK['title'], quote=True)} | {theme.BRAND}"><div class="viewport"><div class="stage">
<header class="bar"><span class="wordmark"><img src="{LOGO}" alt=""><span>{theme.WORDMARK}</span></span><span class="block-name"></span></header>
<main>{sections}</main><div class="progress"></div></div></div>
<nav class="toolbar" aria-label="Controles de la presentación"><button id="previous" type="button" aria-label="Diapositiva anterior">←</button><button id="next" type="button" aria-label="Diapositiva siguiente">→</button><button id="open-presenter" type="button">Presentador (P)</button><button id="fullscreen" type="button">Pantalla completa (F)</button></nav>
<script type="text/plain" id="presenter-template">{presenter_html()}</script>
<script>{DECK_JS}</script></body></html>'''
    (ROOT / '01-pizarra.html').write_text(page)


GUION_CSS = '''
* { box-sizing: border-box; }
body { margin: 0; background: var(--background); color: var(--text); font: 400 18px/1.6 var(--sans); }
main { max-width: 1100px; margin: 0 auto; padding: 64px 32px 96px; }
.kicker { font-family: var(--mono); color: var(--spark); margin: 0 0 12px; }
h1, h2, h3 { font-weight: 500; letter-spacing: -.03em; text-wrap: balance; }
h1 { font-size: 56px; line-height: 1.05; margin: 0 0 16px; }
h2 { font-size: 34px; margin: 64px 0 8px; }
h3 { font-size: 22px; margin: 28px 0 6px; }
em { font-style: normal; color: var(--brand); }
p, li { color: var(--text-2); text-wrap: pretty; }
table { width: 100%; border-collapse: collapse; margin-top: 24px; }
th, td { text-align: left; padding: 12px 14px; border-bottom: 1px solid var(--border); vertical-align: top; }
thead th { font-family: var(--mono); font-weight: 400; font-size: 14px; color: var(--text-2); }
tbody tr:nth-child(odd) { background: var(--background-2); }
.time { font-family: var(--mono); white-space: nowrap; }
.block { background: var(--background-2); border: 1px solid var(--border); border-radius: 16px; padding: 8px 28px 24px; margin-top: 24px; }
.slide-note { border-top: 1px solid var(--border); padding-top: 4px; }
.slide-note strong { color: var(--text); font-weight: 500; }
:focus-visible { outline: 2px solid var(--text); outline-offset: 3px; }
@media print { body { background: #fff; color: var(--background); } p, li, td { color: #333; } .block, tbody tr:nth-child(odd) { background: var(--paper); } }
'''


def build_guion():
    rows = ''.join(f'<tr><td class="time">{esc(b["start"])}</td><td class="time">{b["minutes"]} min</td><th scope="row">{esc(b["name"])}</th><td>{esc(b["goal"])}</td></tr>' for b in BLOCKS)
    details = []
    for b in BLOCKS:
        notes = ''.join(
            f'<div class="slide-note"><h3>{i + 1:02}. {esc(s.get("title", ""))}</h3><p>{esc(s["notes"])}</p></div>'
            for i, s in enumerate(SLIDES) if s['block'] == b['name'])
        details.append(f'<section class="block" aria-labelledby="b-{b["id"]}"><h2 id="b-{b["id"]}">{esc(b["name"])}</h2><p class="time">{esc(b["start"])} · {b["minutes"]} min</p><p>{esc(b["goal"])}</p>{notes or "<p>Sin diapositivas: pausa o transición.</p>"}</section>')
    page = f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Guion · {html.escape(DECK['title'])} | {theme.BRAND}</title><link rel="icon" href="{LOGO}">
<style>{FONTS}{TOKENS}{GUION_CSS}</style></head>
<body><main>
<p class="kicker">Guion de conducción · solo para vos, no se transmite</p>
<h1>{esc(DECK['guion_title'])}</h1>
{''.join(f'<p>{esc(p)}</p>' for p in DECK['intro'])}
<h2>Cronograma</h2>
<table><thead><tr><th scope="col">Inicio</th><th scope="col">Duración</th><th scope="col">Bloque</th><th scope="col">Objetivo</th></tr></thead><tbody>{rows}</tbody></table>
<h2>Antes de salir al aire</h2>
<ul>{''.join(f'<li>{esc(item)}</li>' for item in DECK['checklist'])}</ul>
<h2>Notas por bloque</h2>
{"".join(details)}
</main></body></html>'''
    (ROOT / 'guion.html').write_text(page)


def build_manifest():
    manifest_path = ROOT / 'design.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else dict(title=DECK['title'], artboards=[])
    manifest['brief'] = DECK['brief']
    entries = {a['file']: a for a in manifest['artboards']}
    entries['01-pizarra.html'] = dict(file='01-pizarra.html', title='Pizarra', tradeoff=f'Lo que se transmite: {len(SLIDES)} diapositivas, escenario 16:9 fijo, vista de presentador privada.', width=1600, height=900)
    entries['guion.html'] = dict(file='guion.html', title='Guion de conducción', tradeoff='Documento privado: cronograma y notas por diapositiva. No se transmite.', width=1440, height=900)
    manifest['artboards'] = list(entries.values())
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    build_deck()
    build_guion()
    build_manifest()
    print(f'Built 01-pizarra.html ({len(SLIDES)} slides) and guion.html ({len(BLOCKS)} blocks).')
