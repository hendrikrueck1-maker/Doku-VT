#!/usr/bin/env python3
"""Automatischer Test für Doku VT (ab 2.5.0 mit Requisite).

Aufruf:
  python3 test/test_dokuvt.py                 prüft die App im Ordner über test/
  python3 test/test_dokuvt.py <ordner>        prüft eine andere Fassung
  python3 test/test_dokuvt.py -k requisite    nur Tests, deren Name den Teil enthält
  python3 test/test_dokuvt.py --alt <ordner>  Vergleichsfassung 2.4.4 (für den DOM-Vergleich und die
                                              Format-Tests; ohne Angabe: Ordner „v244“ neben test/, falls vorhanden)

Braucht Python 3.9+, Playwright mit Chromium (pip install playwright && playwright install chromium),
für die PDF-Prüfung zusätzlich qpdf. Jedes Gerät ist ein eigener Browser-Kontext (eigene IndexedDB).
Ohne pytest lauffähig.
"""
import asyncio, functools, http.server, json, os, re, shutil, subprocess, sys, tempfile, threading, time, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:]
ONLY = None
ALT = None
ROOT = os.path.dirname(HERE)
i = 0
while i < len(args):
    if args[i] == '-k': ONLY = args[i + 1].lower(); i += 2
    elif args[i] == '--alt': ALT = os.path.abspath(args[i + 1]); i += 2
    else: ROOT = os.path.abspath(args[i]); i += 1
if ALT is None and os.path.isfile(os.path.join(HERE, 'v244', 'index.html')): ALT = os.path.join(HERE, 'v244')

from playwright.async_api import async_playwright


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass


def serve(directory):
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=directory))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f'http://127.0.0.1:{srv.server_address[1]}/index.html'


BASE = serve(ROOT)
BASE_ALT = serve(ALT) if ALT else None
TMP = tempfile.mkdtemp(prefix='dokuvt-test-')
TESTS = []


def test(fn):
    TESTS.append(fn); return fn


class Dev:
    """Ein Gerät = ein Browser-Kontext mit eigener Datenbank."""
    def __init__(self, ctx, page, errors):
        self.ctx, self.p, self.errors = ctx, page, errors

    async def js(self, code, arg=None):
        return await self.p.evaluate(code, arg) if arg is not None else await self.p.evaluate(code)

    async def wait(self, ms=150): await self.p.wait_for_timeout(ms)

    async def confirm(self):
        """obersten eigenen Dialog bestätigen (primär bzw. Löschen)"""
        sel = '.scrim.dlg .btn.primary, .scrim.dlg .btn.danger.solid'
        await self.p.wait_for_selector(sel, timeout=5000)
        await self.p.locator(sel).last.click()
        await self.wait(250)

    async def reload(self):
        await self.p.reload(); await self.p.wait_for_function('window.Boot && Boot.started', timeout=20000); await self.wait(300)


async def device(browser, base=None, depts=None, width=1024, height=900):
    ctx = await browser.new_context(viewport={'width': width, 'height': height}, service_workers='block', accept_downloads=True)
    page = await ctx.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('console', lambda m: errors.append('console: ' + m.text) if m.type == 'error' else None)
    await page.goto(base or BASE)
    await page.wait_for_function('window.Boot && Boot.started', timeout=20000)
    await page.wait_for_timeout(300)
    d = Dev(ctx, page, errors)
    if depts:
        await d.js("""async (dp) => { await Settings.set({ depts: dp }); if (dp.includes('R')) { await Req.ensureHouse(); await Req.maybeDemo(); } App.render(); }""", depts)
        await d.wait(200)
    return d


async def package(dev, opts):
    """Paket als JSON-Text bauen (wie FileAdapter/Backup)"""
    return await dev.js("""async (o) => { const r = await Sync.buildPackage(o); return await r.blob.text(); }""", opts)


async def importText(dev, text, name='paket.json'):
    return await dev.js("""async ([t, n]) => { try { return await Sync.importPackage(new File([t], n, { type: 'application/json' })); } catch (e) { return { error: e.message }; } }""", [text, name])


def check(cond, msg):
    if not cond: raise AssertionError(msg)


def qpdf_ok(path):
    if not shutil.which('qpdf'): return True
    r = subprocess.run(['qpdf', '--check', path], capture_output=True, text=True)
    return r.returncode in (0, 3)


def pdf_text(path):
    """alle Textstücke der Seiten, mit Leerzeichen verbunden (Zeilenumbrüche im PDF werden so überbrückt)"""
    raw = pdf_bytes(path)
    parts = re.findall(rb'\((.*?)(?<!\\)\) Tj', raw)
    return b' '.join(x.replace(b'\\(', b'(').replace(b'\\)', b')') for x in parts)


def pdf_bytes(path):
    """dekomprimierter Inhalt (für Textsuche)"""
    if not shutil.which('qpdf'): return open(path, 'rb').read()
    out = path + '.qdf'
    subprocess.run(['qpdf', '--qdf', '--object-streams=disable', path, out], capture_output=True)
    return open(out, 'rb').read()


async def build_pdf(dev, show_id, opts):
    return await dev.js("""async ([id, o]) => { const b = await Pdf.build(id, Object.assign({ kat: 'all', cover: true, compact: true }, o)); const u = new Uint8Array(await b.arrayBuffer());
        let s = ''; for (let i = 0; i < u.length; i += 0x8000) s += String.fromCharCode.apply(null, u.subarray(i, i + 0x8000)); return { b64: btoa(s), pages: Pdf.lastPages }; }""", [show_id, opts])


def save_pdf(res, name):
    import base64
    p = os.path.join(TMP, name); open(p, 'wb').write(base64.b64decode(res['b64'])); return p


# ======================================================================
# Grundfunktionen (Licht, Ton, Bühne)
# ======================================================================
@test
async def t_start_demo(B):
    d = await device(B)
    n = await d.js("Repo.liveShows().map(s => s.f.titel)")
    check(any('Haifisch' in t for t in n), f'Demo fehlt: {n}')
    check(await d.js("APP_VERSION") == '2.5.0', 'Version')
    check(await d.js("Settings.v.depts.join()") == 'L', 'Standard nur Licht')
    check(await d.js("Repo.house.size") == 0, 'ohne Requisite kein Haus-Datensatz')
    return d


@test
async def t_save_reload_merge(B):
    d = await device(B)
    sid = await d.js("Repo.liveShows()[0].id")
    await d.js("""async (sid) => { await Repo.saveDraft({ id: null, showId: sid, abt: 'L', f: { kreis: '777 778', bemerkung: 'eins' }, photos: { A: [], E: [] } });
        await Repo.saveDraft({ id: null, showId: sid, abt: 'L', f: { kreis: '778+777', bemerkung: 'zwei' }, photos: { A: [], E: [] } }); }""", sid)
    await d.reload()
    es = await d.js("(sid) => Repo.entriesOf(sid).filter(e => Utils.kreisEq(e.f.kreis, '777+778')).map(e => e.f.bemerkung)", sid)
    check(len(es) == 1 and 'eins' in es[0] and 'zwei' in es[0], f'Zusammenführen: {es}')
    return d


@test
async def t_editor_ui_licht_and_no_change(B):
    d = await device(B)
    sid = await d.js("Repo.liveShows()[0].id")
    await d.js("(sid) => { location.hash = '#/show/' + sid; }", sid); await d.wait(400)
    await d.p.click('[data-act=mode]'); await d.wait(200)
    await d.p.click('.fab:not(.qcam)'); await d.wait(300)
    await d.p.fill('#ed-kreis', '4711'); await d.p.fill('#ed-filter', 'L201')
    await d.p.click('.savebtn2'); await d.wait(400)
    e = await d.js("(sid) => Repo.entriesOf(sid).find(e => e.f.kreis === '4711')?.f.filter", sid)
    check(e == 'L201', 'Editor speichert nicht')
    # unverändert speichern → kein neuer Zeitstempel
    mod = await d.js("(sid) => Repo.entriesOf(sid).find(e => e.f.kreis === '4711').mod", sid)
    eid = await d.js("(sid) => Repo.entriesOf(sid).find(e => e.f.kreis === '4711').id", sid)
    await d.js("([sid, id]) => Editor.open({ showId: sid, entryId: id })", [sid, eid]); await d.wait(300)
    await d.p.click('.savebtn2'); await d.wait(300)
    check(await d.js("(id) => Repo.entries.get(id).mod", eid) == mod, 'Speichern ohne Änderung schreibt')
    return d


@test
async def t_views_no_errors(B):
    d = await device(B, depts=['L', 'T', 'B'])
    sid = await d.js("Repo.liveShows().find(s => s.f.titel.includes('Haifisch')).id")
    await d.js("(sid) => { location.hash = '#/show/' + sid; }", sid); await d.wait(400)
    for v in ['list', 'grid', 'big']:
        await d.p.click(f'[data-view="{v}"]'); await d.wait(200)
    for a in ['L', 'T', 'B', 'all']:
        await d.p.click(f'.deptbtn[data-dept="{a}"]'); await d.wait(150)
    await d.p.click('[data-view="list"]')
    return d


@test
async def t_pdf_licht(B):
    d = await device(B, depts=['L', 'T', 'B'])
    sid = await d.js("Repo.liveShows().find(s => s.f.titel.includes('Haifisch')).id")
    r = await build_pdf(d, sid, {'depts': ['L', 'T', 'B']})
    p = save_pdf(r, 'haifisch.pdf')
    check(qpdf_ok(p), 'qpdf --check')
    check(r['pages'] > 3, 'Seiten')
    return d


@test
async def t_backup_twice(B):
    a = await device(B); b = await device(B)
    t = await package(a, {'type': 'backup'})
    r1 = await importText(b, t); r2 = await importText(b, t)
    check(r1.get('neu', 0) > 0, f'erster Import {r1}')
    check(r2.get('neu') == 0 and r2.get('geaendert') == 0, f'zweiter Import {r2}')
    check(json.loads(t)['formatVersion'] == 2, 'Backup ohne Requisite bleibt Format 2')
    return a


@test
async def t_trash_restore(B):
    d = await device(B)
    sid = await d.js("Repo.liveShows()[0].id")
    await d.js("async (sid) => { await Repo.deleteShow(sid); await Repo.restoreShow(sid); }", sid)
    check(await d.js("(sid) => !!Repo.show(sid) && Repo.entriesOf(sid).length > 0", sid), 'Wiederherstellen')
    return d


async def live_pair(a, b, tries=3):
    """WebRTC-Live-Abgleich zwischen zwei Kontexten (Signalisierung direkt statt QR). Headless-Chromium
    findet die lokalen Kandidaten nicht immer beim ersten Mal – dann neuer Versuch mit frischen Sitzungen."""
    for _ in range(tries):
        off = await a.js("async () => { if (window.__ps) window.__ps.close(); window.__ps = new PeerSession(); return await window.__ps.createOffer(); }")
        ans = await b.js("async (o) => { if (window.__ps) window.__ps.close(); window.__ps = new PeerSession(); return await window.__ps.acceptOffer(await PeerAdapter.decodeSignal(o)); }", off)
        await a.js("async (x) => { await window.__ps.acceptAnswer(await PeerAdapter.decodeSignal(x)); }", ans)
        for _ in range(60):
            if await a.js("!!window.__ps.initialDone") and await b.js("!!window.__ps.initialDone"): return True
            await a.wait(200)
    return False


@test
async def t_live_licht(B):
    a = await device(B); b = await device(B)
    check(await live_pair(a, b), 'Live-Verbindung kam nicht zustande')
    sid = await a.js("Repo.liveShows()[0].id")
    await a.js("(sid) => Repo.patchShow(sid, { notiz: 'live!' })", sid)
    for _ in range(30):
        if await b.js("(sid) => Repo.shows.get(sid) && Repo.shows.get(sid).f.notiz", sid) == 'live!': break
        await b.wait(150)
    check(await b.js("(sid) => Repo.shows.get(sid).f.notiz", sid) == 'live!', 'Live-Änderung kam nicht an')
    return a


@test
async def t_mobile_width_three(B):
    d = await device(B, depts=['L', 'T', 'B'], width=375, height=780)
    sid = await d.js("Repo.liveShows()[0].id")
    await d.js("(sid) => { location.hash = '#/show/' + sid; }", sid); await d.wait(400)
    check(await d.js("document.documentElement.scrollWidth <= innerWidth + 1"), 'waagrechtes Scrollen')
    return d


# ======================================================================
# Requisite (ab 2.5.0)
# ======================================================================
def norm_html(h):
    h = re.sub(r'(?<![\d.])(2\.4\.4|2\.5\.0)(?![\d])', 'V', h)
    h = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', 'ID', h)
    h = re.sub(r'blob:[^"\')\s]+', 'BLOB', h)
    h = re.sub(r'(vor \d+ (Min|Std)\.|gerade eben)', 'T', h)
    h = re.sub(r'\d+ offen|Nie', 'N', h)
    return h


@test
async def t_r01_ohne_requisite_identisch(B):
    if not BASE_ALT: return 'übersprungen (keine Vergleichsfassung 2.4.4, --alt <ordner>)'
    outs = []
    for base in (BASE_ALT, BASE):
        d = await device(B, base=base)
        res = {}
        res['home'] = norm_html(await d.js("document.getElementById('app').innerHTML"))
        for dp in (['L'], ['L', 'T', 'B']):
            await d.js("async (dp) => { await Settings.set({ depts: dp }); App.render(); }", dp)
            sid = await d.js("Repo.liveShows()[0].id")
            await d.js("(sid) => { location.hash = '#/show/' + sid; }", sid); await d.wait(500)
            res['show' + ''.join(dp)] = norm_html(await d.js("document.getElementById('app').innerHTML"))
            await d.p.click('[data-act=mode]'); await d.wait(200)
            res['edit' + ''.join(dp)] = norm_html(await d.js("document.getElementById('app').innerHTML"))
            await d.p.click('[data-act=mode]'); await d.wait(200)
            r = await build_pdf(d, sid, {'depts': dp})
            res['pdf' + ''.join(dp)] = r['pages']
            await d.js("location.hash = '#/'"); await d.wait(300)
        outs.append(res)
        await d.ctx.close()
    for k in outs[0]:
        if outs[0][k] != outs[1][k]:
            a, b = str(outs[0][k]), str(outs[1][k])
            i = next((j for j in range(min(len(a), len(b))) if a[j] != b[j]), min(len(a), len(b)))
            raise AssertionError(f'Unterschied in {k}: 2.4.4 …{a[max(0, i - 80):i + 80]}… / 2.5.0 …{b[max(0, i - 80):i + 80]}…')


@test
async def t_r02_einschalten_haus_demo_ohne_dubletten(B):
    a = await device(B, depts=['L', 'R']); b = await device(B, depts=['R'])
    for d in (a, b):
        check(await d.js("Req.houseOrts().length") >= 30, 'Haus-Orte fehlen')
        check(await d.js("Req.vorlagen().length") == 14, 'Vorlagen fehlen')
        check(await d.js("!!Repo.show('demo-r-show')"), 'Demo „Einfache Leute“ fehlt')
    t = await package(a, {'type': 'sync', 'depts': ['L', 'R']})
    await importText(b, t)
    check(await b.js("Repo.liveShows().filter(s => s.f.titel.includes('Einfache Leute')).length") == 1, 'Demo doppelt')
    check(await b.js("Req.houseOrts().length") == await a.js("Req.houseOrts().length"), 'Haus-Orte doppelt')
    check(await b.js("Req.entriesR('demo-r-show').length") == await a.js("Req.entriesR('demo-r-show').length"), 'Gegenstände doppelt')
    return a


@test
async def t_r03_abschnitte_pause_verschieben_loeschen(B):
    d = await device(B, depts=['R'])
    sid = await d.js("(async () => (await Repo.createShow('Testpaket', ['R'])).id)()")
    labels = lambda: d.js("(sid) => Req.abschnitte(sid).map(a => a.label)", sid)
    check(await labels() == ['Vor der Vorstellung', 'Vorstellung', 'Nach der Vorstellung'], f'Standard: {await labels()}')
    await d.js("(sid) => Req.addPause(sid)", sid); await d.wait(300)
    check(await labels() == ['Vor der Vorstellung', 'Teil 1', 'Pause', 'Teil 2', 'Nach der Vorstellung'], f'+Pause: {await labels()}')
    # Schritte: einer in Teil 2, einer in Teil 1, dann zwischen Abschnitten verschieben
    await d.js("""async (sid) => { const ab = Req.abschnitte(sid); await Repo.patchShow(sid, {
        'rs:a1': { abschnitt: ab[1].key, text: 'eins', ord: 10, del: false }, 'rs:a2': { abschnitt: ab[1].key, text: 'zwei', ord: 20, del: false },
        'rs:a3': { abschnitt: ab[3].key, text: 'drei', ord: 10, del: false } }); }""", sid)
    await d.js("(sid) => Req.moveStep(sid, 'rs:a2', -1)", sid)
    check(await d.js("(sid) => Req.steps(sid).map(s => s.text).join()", sid) == 'zwei,eins,drei', 'Schritt verschieben')
    await d.js("(sid) => Req.moveAbschnitt(sid, Req.abschnitte(sid)[4].key, -1)", sid)
    check((await labels())[3] == 'Nach der Vorstellung', 'Abschnitt verschieben')
    await d.js("(sid) => Req.moveAbschnitt(sid, Req.abschnitte(sid)[3].key, 1)", sid)
    # Pause entfernen → Rückfrage → wieder „Vorstellung“, Schritte aus Teil 2 kommen zu Teil 1
    pk = await d.js("(sid) => Req.abschnitte(sid).find(a => a.typ === 'pause').key", sid)
    await d.js("([sid, k]) => { window.__del = Req.deleteAbschnitt(sid, k); }", [sid, pk])
    await d.confirm(); await d.js("window.__del")
    check(await labels() == ['Vor der Vorstellung', 'Vorstellung', 'Nach der Vorstellung'], f'Pause entfernen: {await labels()}')
    check(await d.js("(sid) => Req.steps(sid).filter(s => s.abschnitt === Req.abschnitte(sid)[1].key).length", sid) == 3, 'Schritte zusammengeführt')
    # Abschnitt löschen mit Rückfrage, Abbrechen ändert nichts
    nk = await d.js("(sid) => Req.abschnitte(sid)[2].key", sid)
    await d.js("([sid, k]) => { window.__del = Req.deleteAbschnitt(sid, k); }", [sid, nk])
    await d.p.locator('.scrim.dlg .btn').first.click(); await d.wait(200); await d.js("window.__del")
    check(len(await labels()) == 3, 'Abbrechen hat gelöscht')
    await d.js("([sid, k]) => { window.__del = Req.deleteAbschnitt(sid, k); }", [sid, nk]); await d.confirm(); await d.js("window.__del")
    check(len(await labels()) == 2, 'Löschen')
    return d


async def open_r_show(d, sid, edit=False):
    await d.js("(sid) => { App.state.abt = 'all'; location.hash = '#/show/' + sid; }", sid); await d.wait(400)
    if edit and not await d.js("App.state.edit"):
        await d.p.click('[data-act=mode]'); await d.wait(250)


@test
async def t_r04_gegenstand_anlegen(B):
    d = await device(B, depts=['R'])
    sid = await d.js("(async () => (await Repo.createShow('Anlegen', ['R'])).id)()")
    await open_r_show(d, sid, edit=True)
    # nur Name, Ort per Schnelltaste, „+ Nächster am selben Ort“
    await d.p.click('.fab:not(.qcam)'); await d.wait(300)
    await d.p.fill('#ed-was', 'Lesebrille')
    await d.p.locator('[data-rort]').first.click()
    ort = await d.js("document.querySelector('[data-rort][aria-pressed=true]').textContent")
    await d.p.click('[data-act=savenext]'); await d.wait(700)
    check(await d.js("!!document.querySelector('[data-editor] [data-rort][aria-pressed=true]')"), '„Nächster am selben Ort“ behält den Ort nicht')
    await d.p.fill('#ed-was', 'Lesebrille'); await d.p.click('.savebtn2'); await d.wait(500)
    es = await d.js("(sid) => Req.entriesR(sid).map(e => [e.f.was, e.f.ort])", sid)
    check(len(es) == 2 and all(e[0] == 'Lesebrille' and e[1] == ort for e in es), f'gleicher Name zweimal → zwei Einträge: {es}')
    # ohne Name und ohne Foto: kein Speichern, Hinweis
    await d.p.click('.fab:not(.qcam)'); await d.wait(300)
    await d.p.fill('#ed-stelle', 'irgendwo'); await d.p.click('.savebtn2'); await d.wait(300)
    check(await d.js("!!document.querySelector('[data-editor]')"), 'ohne Name/Foto gespeichert')
    await d.p.click('[data-editor] [data-act=cancel]'); await d.wait(200); await d.confirm()
    # nur Foto
    await d.js("""async (sid) => { const c = document.createElement('canvas'); c.width = c.height = 200; const g = c.getContext('2d'); g.fillStyle = '#4a8'; g.fillRect(0, 0, 200, 200);
        const p = await Photo.fromCanvas(c); await Repo.saveDraft({ id: null, showId: sid, abt: 'R', f: { was: '' }, photos: { A: [{ b: p.b, w: p.w, h: p.h, full: p.full, thumb: p.thumb, cap: 'von hinten' }], E: [] } }); }""", sid)
    check(await d.js("(sid) => Req.entriesR(sid).some(e => !e.f.was && Repo.photosOf(e.id).length === 1 && Repo.photosOf(e.id)[0].f.cap === 'von hinten')", sid), 'Foto-only mit Bildunterschrift')
    await d.wait(300)
    check(await d.js("[...document.querySelectorAll('.rcard .rwas')].some(x => x.textContent.includes('Ohne Namen'))"), 'Karte „Ohne Namen“')
    # Vorlage übernehmen = Kopie
    await d.p.click('.fab:not(.qcam)'); await d.wait(300)
    await d.p.fill('#ed-was', 'Gewe')
    await d.p.locator('[data-sugg-i]', has_text='Gewehr').first.click()
    check(await d.js("document.querySelector('[data-rchip=sicherheit][data-v=waffe]').getAttribute('aria-pressed')") == 'true', 'Vorlage setzt Sicherheit')
    await d.p.click('.savebtn2'); await d.wait(400)
    await d.p.locator('.scrim.dlg .btn').first.click(); await d.wait(300)          # Waffen-Schritte ablehnen
    await d.js("async () => { const k = 'hg:std-gewehr'; await Repo.patchHouse({ [k]: Object.assign({}, Req.houseF()[k], { was: 'Flinte' }) }); }")
    check(await d.js("(sid) => Req.entriesR(sid).some(e => e.f.was === 'Gewehr' && e.f.sicherheit === 'waffe')", sid), 'Vorlage ist keine Kopie')
    return d


@test
async def t_r05_behaelter(B):
    d = await device(B, depts=['R'])
    await open_r_show(d, 'demo-r-show')
    check(await d.js("document.querySelectorAll('.rcard.rin').length") >= 4, 'Inhalt eingerückt')
    bid = await d.js("Req.entriesR('demo-r-show').find(e => e.f.was === 'Bauchtasche').id")
    check(await d.js("(id) => Req.contentsOf(Repo.entry(id)).length", bid) == 3, 'Bauchtasche enthält 3')
    await d.p.click('[data-act=mode]'); await d.wait(200)
    await d.js("(id) => Editor.open({ showId: 'demo-r-show', entryId: id })", bid); await d.wait(300)
    check(await d.js("document.querySelector('[data-inid]').disabled"), 'Behälter darf nicht in etwas liegen')
    await d.p.click('[data-editor] [data-act=cancel]'); await d.wait(200)
    # ein Gegenstand, der in etwas liegt, steht nicht als Behälter zur Wahl
    tid = await d.js("Req.entriesR('demo-r-show').find(e => e.f.was === 'Tablet').id")
    await d.js("(id) => Editor.open({ showId: 'demo-r-show', entryId: id })", tid); await d.wait(300)
    opts = await d.js("[...document.querySelectorAll('[data-inid] option')].map(o => o.value)")
    inner = await d.js("Req.entriesR('demo-r-show').filter(e => e.f.inId).map(e => e.id)")
    check(not set(opts) & set(inner), 'innenliegende Gegenstände als Behälter angeboten')
    return d


@test
async def t_r06_personen(B):
    d = await device(B, depts=['R'])
    await d.js("async () => { const k = 'rp:demo-r-anna'; await Repo.patchShow('demo-r-show', { [k]: Object.assign({}, Req.sh('demo-r-show')[k], { darsteller: 'Anna K.' }) }); }")
    await open_r_show(d, 'demo-r-show')
    check(await d.js("[...document.querySelectorAll('.rcard .rmeta')].filter(x => x.textContent.includes('Anna (Anna K.)')).length") >= 8, 'Umbenennen wirkt nicht auf Karten')
    await d.p.click('[data-rview="personen"]'); await d.wait(300)
    check(await d.js("document.querySelectorAll('.rorthead').length") == 5, 'Ansicht Personen')
    # Mehrfachauswahl
    await d.js("async () => { const e = Req.entriesR('demo-r-show').find(x => x.f.was === 'Tablet'); await Repo.saveDraft({ id: e.id, showId: e.showId, f: { personIds: ['rp:demo-r-ruby', 'rp:demo-r-luise'] }, photos: { A: [], E: [] } }); }")
    check(await d.js("Req.val(Req.entriesR('demo-r-show').find(x => x.f.was === 'Tablet'), 'zuWem')") == 'Ruby, Luise', 'Mehrfachauswahl')
    await d.p.click('[data-rview="ort"]')
    return d


@test
async def t_r07_ort_picker_raster(B):
    d = await device(B, depts=['R'])
    sid = await d.js("(async () => (await Repo.createShow('Tauben', ['R'])).id)()")
    await open_r_show(d, sid, edit=True)
    await d.js("(sid) => { window.__r = Req.rasterDialog(sid); }", sid); await d.wait(300)
    await d.p.click('[data-ok]'); await d.js("window.__r"); await d.wait(200)
    names = await d.js("(sid) => Req.showOrts(sid).map(o => o.name)", sid)
    check(len(names) == 24 and names[0] == 'A1' and names[-1] == 'F4', f'Raster: {names[:3]}…{len(names)}')
    await d.js("(sid) => { window.__r = Req.numberedDialog(sid); }", sid); await d.wait(300)
    await d.p.click('[data-ok]'); await d.js("window.__r")
    check(await d.js("(sid) => Req.showOrts(sid).filter(o => /^Stuhl [1-6]$/.test(o.name)).length", sid) == 6, 'Stuhl n')
    # Ort-Picker: Suche + Auswahl eines Haus-Orts
    await d.js("(sid) => { window.__p = Req.pickOrt(sid); }", sid); await d.wait(300)
    await d.p.fill('#rp-q', 'nullgasse r'); await d.wait(100)
    vis = await d.js("[...document.querySelectorAll('.rpo:not(.hidden)')].map(b => b.textContent.trim())")
    check(vis == ['Nullgasse rechts'], f'Suche: {vis}')
    await d.p.locator('.rpo:not(.hidden)').first.click()
    r = await d.js("window.__p")
    check(r['name'] == 'Nullgasse rechts' and r['key'].startswith('ho:'), f'Auswahl {r}')
    # Haus-Ort ändern wirkt in allen Stücken; Ort löschen → „Ort entfernt“
    await d.js("""async ([sid, k]) => { await Repo.saveDraft({ id: null, showId: sid, abt: 'R', f: { was: 'Hut', ortId: k, ort: 'Nullgasse rechts' }, photos: { A: [], E: [] } });
        await Repo.saveDraft({ id: null, showId: 'demo-r-show', abt: 'R', f: { was: 'Schal', ortId: k, ort: 'Nullgasse rechts' }, photos: { A: [], E: [] } });
        await Repo.patchHouse({ [k]: Object.assign({}, Req.houseF()[k], { name: 'Nullgasse R' }) }); }""", [sid, r['key']])
    vals = await d.js("([sid]) => [Req.val(Req.entriesR(sid).find(e => e.f.was === 'Hut'), 'ort'), Req.val(Req.entriesR('demo-r-show').find(e => e.f.was === 'Schal'), 'ort')]", [sid])
    check(vals == ['Nullgasse R', 'Nullgasse R'], f'Haus-Ort wirkt nicht überall: {vals}')
    a1 = await d.js("(sid) => Req.showOrts(sid)[0].key", sid)
    await d.js("async ([sid, k]) => { await Repo.saveDraft({ id: null, showId: sid, abt: 'R', f: { was: 'Taube', ortId: k, ort: 'A1' }, photos: { A: [], E: [] } }); window.__d = Req.ortAct('del', k, { showId: sid }); }", [sid, a1])
    await d.wait(300)
    check('1 Gegenstand liegt hier' in await d.js("document.querySelector('.scrim.dlg p').textContent"), 'Rückfrage mit Anzahl')
    await d.confirm(); await d.js("window.__d")
    check(await d.js("(sid) => Req.val(Req.entriesR(sid).find(e => e.f.was === 'Taube'), 'ort')", sid) == 'A1 · Ort entfernt', 'Ort entfernt')
    return d


@test
async def t_r08_zeit_ausloeser(B):
    d = await device(B, depts=['R'])
    r = await d.js("""() => [Req.whenShort({ zeit: { art: 'vor', min: 60, frist: true } }), Req.whenLong({ zeit: { art: 'vor', min: 60, frist: true } }),
        Req.whenShort({ zeit: { art: 'im', min: 35 } }), Req.whenLong({ zeit: { art: 'im', min: 35 } }),
        Req.whenLong({ zeit: { art: 'ende', wann: 'nach' } }), Req.whenShort({ zeit: { art: 'ende', wann: 'im' } }),
        Req.whenShort({ zeit: { art: 'im', min: 10 }, ausloeser: [{ typ: 'einruf', anzahl: 1 }, { typ: 'licht', anzahl: 2 }] }),
        Req.whenLong({ ausloeser: [{ typ: 'einruf', anzahl: 2 }, { typ: 'licht', anzahl: 1 }] })]""")
    check(r == ['spät. −60', 'spätestens 60 min vor Beginn', 'ca. 35′', 'ca. 35 min', 'nach dem Applaus', 'im Applaus', 'ca. 10′ · Einruf → 2× Lichtzeichen', '2x Einruf -> Lichtzeichen'], f'Texte: {r}')
    # Schritt-Editor über die Oberfläche: Zeit „im Stück“ 35 + zwei Auslöser
    await open_r_show(d, 'demo-r-show', edit=True)
    await d.p.click('[data-rview="ablauf"]'); await d.wait(300)
    await d.p.locator('[data-ract="s-add"]').nth(1).click(); await d.wait(300)
    await d.p.fill('#rs-text', 'Schüsse')
    await d.p.click('[data-sc=zart][data-v=im]'); await d.p.click('[data-sc=imin][data-v="35"]')
    await d.p.click('[data-sx=add][data-v=einruf]'); await d.p.click('[data-sx=add][data-v=licht]'); await d.p.click('[data-sx=plus][data-i="1"]')
    await d.p.click('[data-editor] [data-x=save]'); await d.wait(400)
    s = await d.js("Req.steps('demo-r-show').find(s => s.text === 'Schüsse')")
    check(s and s['zeit']['min'] == 35 and s['ausloeser'] == [{'typ': 'einruf', 'anzahl': 1}, {'typ': 'licht', 'anzahl': 2}], f'Schritt: {s}')
    check('ca. 35′ · Einruf → 2× Lichtzeichen' in await d.js("document.querySelector('.rsteps').closest('[data-list]').textContent"), 'Anzeige im Ablauf')
    p = save_pdf(await build_pdf(d, 'demo-r-show', {'depts': ['R']}), 'zeit.pdf')
    raw = pdf_text(p)
    check(b'sp\xe4testens 30 min vor Beginn' in raw and b'ca. 35 min, Einruf -> 2x Lichtzeichen' in raw, 'Anzeige im PDF')
    return d


@test
async def t_r09_sicherheit_waffe(B):
    d = await device(B, depts=['R'])
    await open_r_show(d, 'demo-r-show')
    badge = await d.js("[...document.querySelectorAll('.rcard .rsafe')].map(b => [b.querySelector('svg') ? 1 : 0, b.textContent.trim()])")
    check(badge and all(x[0] == 1 and x[1] for x in badge), f'Symbol + Text: {badge}')
    await d.p.click('[data-act=rsafe]'); await d.wait(300)
    check(await d.js("[...document.querySelectorAll('.rsafeh')].map(h => h.textContent.trim().split(' ')[0])") == ['Glas'], 'Sicherheit gruppiert')
    await d.p.click('[data-act=rsafe]'); await d.p.click('[data-act=mode]'); await d.wait(200)
    await d.p.click('.fab:not(.qcam)'); await d.wait(300)
    await d.p.fill('#ed-was', 'Pistole'); await d.p.click('[data-rchip=sicherheit][data-v=waffe]')
    await d.p.click('.savebtn2'); await d.wait(500)
    await d.confirm(); await d.wait(300)
    st = await d.js("(() => { const e = Req.entriesR('demo-r-show').find(x => x.f.was === 'Pistole'); return Req.steps('demo-r-show').filter(s => s.gegenstand === e.id).map(s => [s.text, (Req.abschnitte('demo-r-show').find(a => a.key === s.abschnitt) || {}).typ, Req.stepSafety(s)]); })()")
    check(st == [['Pistole aus dem Waffenschrank holen', 'vor', 'waffe'], ['Pistole im Waffenschrank einschließen', 'nach', 'waffe']], f'Waffen-Schritte: {st}')
    return d


@test
async def t_r10_ansichtsmodus(B):
    d = await device(B, depts=['R'])
    await open_r_show(d, 'demo-r-show')
    check(await d.js("!document.querySelector('.fab') && !document.querySelector('[data-setup-edit]')"), 'Anlegen im Ansichtsmodus sichtbar')
    await d.p.locator('.rcard .hit').first.click(); await d.wait(300)
    check(await d.js("!document.querySelector('[data-editor]')"), 'Ansichtsmodus öffnet den Editor')
    await d.p.keyboard.press('Escape'); await d.wait(200)
    await d.p.click('[data-rview="ablauf"]'); await d.wait(200)
    check(await d.js("!document.querySelector('.rsed') && !document.querySelector('[data-ract=s-add]')"), 'Verschieben/Anlegen im Ansichtsmodus')
    await d.p.click('[data-ract=run-start]'); await d.wait(400)
    await d.p.locator('[data-ract=s-chk]').first.click(); await d.wait(300)
    check(await d.js("document.querySelectorAll('.rstep.done').length") == 1, 'Abhaken im Ansichtsmodus')
    return d


@test
async def t_r11_durchgang_schnell(B):
    d = await device(B, depts=['R'])
    rid = await d.js("(async () => (await RunList.create('demo-r-show')).id)()")
    keys = await d.js("RunList.items('demo-r-show', ['R']).map(i => i.key)")
    check(len(keys) >= 7 and any(k.startswith('rs:') for k in keys), f'Punkte {keys}')
    await d.js("([rid, ks]) => Promise.all(ks.map(k => RunList.toggle(rid, k)))", [rid, keys])
    await d.reload()
    h = await d.js("(rid) => Object.keys(Repo.runs.get(rid).f).filter(k => k.startsWith('h:') && Repo.runs.get(rid).f[k].ok && Repo.runs.get(rid).f[k].dev && Repo.runs.get(rid).f[k].at).length", rid)
    check(h == len(keys), f'nach Neuladen {h}/{len(keys)} Haken')
    check(await d.js("RunList.abtOfItem('demo-r-show', 'rs:x')") == 'R', 'abtOfItem')
    return d


@test
async def t_r12_requisite_an_licht_geraet(B):
    a = await device(B, depts=['L', 'R']); b = await device(B, depts=['L'])
    await a.js("""async () => { const c = document.createElement('canvas'); c.width = c.height = 120; c.getContext('2d').fillRect(0, 0, 60, 60); const p = await Photo.fromCanvas(c);
        await Repo.saveDraft({ id: null, showId: 'demo-r-show', abt: 'R', f: { was: 'mit Foto' }, photos: { A: [{ b: p.b, w: p.w, h: p.h, full: p.full, thumb: p.thumb }], E: [] } }); window.__rb = p.b; }""")
    t = await package(a, {'type': 'sync', 'depts': ['L', 'R']})
    j = json.loads(t)
    check(j['formatVersion'] == 3, 'Paket mit Requisite muss Format 3 haben')
    r = await importText(b, t)
    check('error' not in r, r.get('error'))
    check(await b.js("!!Repo.show('demo-r-show')"), 'Veranstaltung kommt nicht an')
    check(await b.js("[...Repo.entries.values()].filter(e => e.f.abt === 'R').length") == 0, 'Requisite-Gegenstände übernommen')
    check(await b.js("Repo.house.size") == 0, 'Haus-Datensatz übernommen')
    rb = await a.js("window.__rb")
    check(not await b.js("(b) => Repo.blobIds().then(s => s.has(b))", rb), 'Requisite-Foto übernommen')
    # nur Licht aus einem Requisite-Gerät → Format 2
    t2 = await package(a, {'type': 'sync', 'depts': ['L']})
    check(json.loads(t2)['formatVersion'] == 2, 'ohne Requisite-Inhalt muss Format 2 bleiben')
    check(not json.loads(t2).get('house'), 'Haus-Datensatz an Licht-Paket')
    return a


@test
async def t_r13_format3_von_244_abgelehnt(B):
    a = await device(B, depts=['R'])
    t = await package(a, {'type': 'sync', 'depts': ['R']})
    check(json.loads(t)['formatVersion'] == 3, 'Format 3')
    if BASE_ALT:
        old = await device(B, base=BASE_ALT)
        r = await importText(old, t)
        check('error' in r and 'neueren' in r['error'], f'2.4.4 lehnt nicht ab: {r}')
    else:
        r = await a.js("(t) => { const d = JSON.parse(t); return (d.formatVersion || 1) > 2; }", t)
        check(r, 'Simulation 2.4.4')
    return a


@test
async def t_r14_244_dateien_lesen(B):
    if not BASE_ALT: return 'übersprungen (keine Vergleichsfassung 2.4.4)'
    old = await device(B, base=BASE_ALT, depts=['L', 'T', 'B'])
    bk = await package(old, {'type': 'backup'}); sy = await package(old, {'type': 'sync', 'depts': ['L', 'T', 'B']})
    n = await device(B)
    for t in (bk, sy):
        r1 = await importText(n, t); r2 = await importText(n, t)
        check('error' not in r1, r1.get('error'))
        check(r2.get('neu') == 0 and r2.get('geaendert') == 0, f'zweimal: {r2}')
    return n


@test
async def t_r15_live_requisite(B):
    a = await device(B, depts=['R']); b = await device(B, depts=['R'])
    check(await live_pair(a, b), 'Live-Verbindung')
    eid = await a.js("Req.entriesR('demo-r-show').find(e => e.f.was === 'Tablet').id")
    await a.js("(id) => Repo.saveDraft({ id, showId: 'demo-r-show', f: { stelle: 'links' }, photos: { A: [], E: [] } })", eid)
    await b.js("(id) => Repo.saveDraft({ id, showId: 'demo-r-show', f: { markierung: '(T)' }, photos: { A: [], E: [] } })", eid)
    await a.js("async () => { const k = 'ho:std-unterbuehne'; await Repo.patchHouse({ [k]: Object.assign({}, Req.houseF()[k], { notiz: 'Licht an!' }) }); }")
    for _ in range(40):
        if await b.js("Req.houseF()['ho:std-unterbuehne'].notiz") == 'Licht an!' and await a.js("(id) => Repo.entries.get(id).f.markierung", eid) == '(T)' and await b.js("(id) => Repo.entries.get(id).f.stelle", eid) == 'links': break
        await a.wait(150)
    for d in (a, b):
        f = await d.js("(id) => Repo.entries.get(id).f", eid)
        check(f.get('stelle') == 'links' and f.get('markierung') == '(T)', f'gleichzeitige Änderung verloren: {f}')
    check(await b.js("Req.houseF()['ho:std-unterbuehne'].notiz") == 'Licht an!', 'Haus-Ort-Änderung kam nicht an')
    # Gegenstelle ohne Requisite bekommt keine Requisite-Daten
    c = await device(B, depts=['R']); e = await device(B, depts=['L'])
    check(await live_pair(c, e), 'Live-Verbindung 2')
    await c.js("() => Repo.saveDraft({ id: null, showId: 'demo-r-show', abt: 'R', f: { was: 'neu live' }, photos: { A: [], E: [] } })"); await c.wait(1200)
    check(await e.js("[...Repo.entries.values()].filter(x => x.f.abt === 'R').length") == 0 and await e.js("Repo.house.size") == 0, 'Requisite-Daten an Gerät ohne Requisite gesendet')
    check(await e.js("!!Repo.show('demo-r-show')"), 'Veranstaltung fehlt auf Gerät ohne Requisite')
    return a


@test
async def t_r16_aufraeumen_behaelt_fotos(B):
    d = await device(B, depts=['R'])
    ids = await d.js("""async () => {
        const mk = async col => { const c = document.createElement('canvas'); c.width = c.height = 100; const g = c.getContext('2d'); g.fillStyle = col; g.fillRect(0, 0, 100, 100); return Photo.fromCanvas(c); };
        const a = await mk('#f00'), b = await mk('#0f0'), c = await mk('#00f'), e = await mk('#ff0'), x = await mk('#0ff');
        await Repo.patchShowBlobs('demo-r-show', { fotoR: a.b, 'ro:t1': { name: 'Wand', foto: b.b, ord: 10, del: false } }, [a, b]);
        await Repo.patchHouse({ 'ho:std-unterbuehne': Object.assign({}, Req.houseF()['ho:std-unterbuehne'], { foto: c.b }), 'hg:std-puffreis': Object.assign({}, Req.houseF()['hg:std-puffreis'], { foto: e.b }) }, [c, e]);
        await Store.tx(['fulls', 'thumbs'], 'readwrite', s => { s.fulls.put({ id: x.b, d: x.full }); s.thumbs.put({ id: x.b, d: x.thumb }); });
        return [a.b, b.b, c.b, e.b, x.b]; }""")
    n = await d.js("Repo.cleanup()")
    have = await d.js("async () => [...await Repo.blobIds()]")
    check(all(i in have for i in ids[:4]), 'Requisite-Fotos gelöscht')
    check(ids[4] not in have and n == 1, f'verwaistes Foto nicht entfernt ({n})')
    # auch im Paket enthalten
    t = json.loads(await package(d, {'type': 'backup'}))
    check(set(ids[:4]) <= set(b['id'] for b in t['blobs']), 'Requisite-Fotos fehlen im Backup')
    return d


@test
async def t_r17_merge_eigenschaften(B):
    d = await device(B)
    ok = await d.js("""() => {
        const keys = ['rs:a', 'rs:b', 'ro:x', 'rp:p', 'ho:h', 'hg:v', 'dauer'];
        const rnd = n => Math.floor(Math.random() * n), val = () => ({ text: 'v' + rnd(5), ord: rnd(3), del: rnd(4) === 0 });
        const mk = () => { const r = { id: 'requisite', c: 1, mod: 0, f: {}, t: {} }; keys.forEach(k => { if (rnd(2)) { r.f[k] = val(); r.t[k] = 1 + rnd(6); } }); return r; };
        const eq = (a, b) => JSON.stringify([a.f, a.t]) === JSON.stringify([b.f, b.t]);
        const sortR = r => ({ f: Object.fromEntries(Object.entries(r.f).sort()), t: Object.fromEntries(Object.entries(r.t).sort()) });
        for (let i = 0; i < 400; i++) {
            const a = mk(), b = mk(), c = mk();
            const ab = Rec.merge(a, b).rec, ba = Rec.merge(b, a).rec;
            if (!eq(sortR(ab), sortR(ba))) return 'kommutativ ' + i;
            if (Rec.merge(ab, b).changed) return 'idempotent ' + i;
            const l = Rec.merge(Rec.merge(a, b).rec, c).rec, r = Rec.merge(a, Rec.merge(b, c).rec).rec;
            if (!eq(sortR(l), sortR(r))) return 'assoziativ ' + i;
            if (!Rec.valid(ab, 'house')) return 'valid';
        }
        return 'ok'; }""")
    check(ok == 'ok', ok)
    return d


@test
async def t_r18_pdf_requisite(B):
    d = await device(B, depts=['R'])
    await d.js("async () => { await Repo.patchShow('demo-r-show', { einrichtungR: 'ACHTUNG: Garderoben sind getauscht', 'rp:demo-r-ruby': Object.assign({}, Req.sh('demo-r-show')['rp:demo-r-ruby'], { darsteller: 'Rübezahl' }) }); }")
    await d.js("async () => { const c = document.createElement('canvas'); c.width = c.height = 300; c.getContext('2d').fillRect(0, 0, 150, 150); const p = await Photo.fromCanvas(c); await Repo.patchShowBlobs('demo-r-show', { fotoR: p.b }, [p]); }")
    for rsort in ('ort', 'person'):
        r = await build_pdf(d, 'demo-r-show', {'depts': ['R'], 'rsort': rsort})
        p = save_pdf(r, f'requisite_{rsort}.pdf')
        check(qpdf_ok(p), 'qpdf --check')
        raw = pdf_bytes(p) + pdf_text(p)
        for s in [b'ABLAUF', b'SICHERHEIT', b'[!] GLAS', b'PERSONEN', b'R\xfcbezahl', b'VERBRAUCH', b'GEGENST\xc4NDE NACH ' + (b'ORT' if rsort == 'ort' else b'PERSON'),
                  b'ALLGEMEIN \xb7 WICHTIG', b'NACH DER VORSTELLUNG', b'S. ', b'/DCTDecode']:
            check(s in raw, f'PDF ({rsort}) enthält nicht {s!r}')
    # Dateiname über den Dialog
    await open_r_show(d, 'demo-r-show')
    await d.js("window.__names = []; Utils.offerFile = (blob, name) => { window.__names.push(name); return Promise.resolve('abort'); }; 0")
    await d.p.click('[data-act=pdf]'); await d.wait(300)
    await d.p.click('[data-go=build]'); await d.wait(2500)
    names = await d.js("window.__names.map(String)")
    check(names and re.match(r'^Demo_Einfache_Leute_Requisite_\d{4}-\d\d-\d\d\.pdf$', names[0]), f'Dateiname {names}')
    return d


@test
async def t_r19_smartphone(B):
    d = await device(B, depts=['L', 'T', 'B', 'R'], width=375, height=780)
    sid = await d.js("Repo.liveShows().find(s => s.f.titel.includes('Haifisch')).id")
    await d.js("(sid) => Repo.patchShow(sid, { abteilungen: ['L', 'T', 'B', 'R'] })", sid)
    await open_r_show(d, sid)
    check(await d.js("document.querySelectorAll('.deptbtn').length") == 5, 'Abteilungsleiste')
    check(await d.js("document.documentElement.scrollWidth <= innerWidth + 1"), 'waagrechtes Scrollen (Alle)')
    check(await d.js("[...document.querySelectorAll('.deptbtn')].every(b => b.scrollWidth <= b.clientWidth + 1)"), 'Abteilungsknopf abgeschnitten')
    await d.p.click('.deptbtn[data-dept="R"]'); await d.wait(300)
    check(await d.js("document.documentElement.scrollWidth <= innerWidth + 1"), 'waagrechtes Scrollen (Requisite)')
    await open_r_show(d, 'demo-r-show', edit=True)
    await d.p.click('.fab:not(.qcam)'); await d.wait(300)
    await d.p.click('[data-rort="__pick"]'); await d.wait(300)
    box = await d.js("(() => { const b = document.querySelector('.rpo'); const r = b.getBoundingClientRect(); return [r.left, r.right, r.height, innerWidth]; })()")
    check(box[0] >= 0 and box[1] <= box[3] and box[2] >= 48, f'Ort-Picker: {box}')
    await d.p.locator('.rpo').nth(2).click(); await d.wait(300)
    check(await d.js("!!document.querySelector('[data-rort][aria-pressed=true]')"), 'Ort aus Picker nicht gewählt')
    return d


@test
async def t_r20_kontrast(B):
    d = await device(B)
    r = await d.js("""() => {
        const lum = h => { let x = h.replace('#', ''); if (x.length === 3) x = x.split('').map(y => y + y).join(''); const c = x.match(/../g).map(x => parseInt(x, 16) / 255).map(v => v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4)); return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]; };
        const cr = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
        const out = {};
        for (const th of ['dark', 'light', 'red']) {
            document.documentElement.dataset.theme = th; const cs = getComputedStyle(document.documentElement), v = n => cs.getPropertyValue(n).trim();
            out[th] = { ae: cr(v('--R-a'), v('--R-e')), text: cr(v('--text'), v('--bg')), muted: cr(v('--muted'), v('--bg')), aeL: cr(v('--L-a'), v('--L-e')) };
        }
        document.documentElement.dataset.theme = Settings.v.theme; return out; }""")
    check(r['dark']['ae'] >= 3.5 and r['light']['ae'] >= 3.5, f'Requisite A ↔ E: {r}')
    check(r['red']['text'] >= 4 and r['red']['muted'] >= 4, f'Rotlicht-Text: {r}')
    return d


@test
async def t_r21_xss(B):
    d = await device(B, depts=['R'])
    x = '<img src=x onerror="window.__xss=1">'
    await d.js("""async (x) => { await Repo.patchShow('demo-r-show', { 'ro:x1': { name: x, notiz: x, gruppe: x, foto: '', cap: x, ord: 1, del: false }, 'rp:x1': { rolle: x, darsteller: x, ord: 1, del: false },
        'rs:x1': { abschnitt: 'ra:demo-r-vor', text: x, ausloeser: [{ typ: 'stichwort', wert: x, anzahl: 2 }], ord: 1, del: false }, einrichtungR: x, dauer: x });
        const c = document.createElement('canvas'); c.width = c.height = 60; const p = await Photo.fromCanvas(c);
        await Repo.saveDraft({ id: null, showId: 'demo-r-show', abt: 'R', f: { was: x, ortId: 'ro:x1', ort: x, personIds: ['rp:x1'], markierung: x, zustand: [x] }, photos: { A: [{ b: p.b, w: p.w, h: p.h, full: p.full, thumb: p.thumb, cap: x }], E: [] } }); }""", x)
    await open_r_show(d, 'demo-r-show', edit=True)
    for m in ('ort', 'ablauf', 'personen'):
        await d.p.click(f'[data-rview="{m}"]'); await d.wait(250)
    await d.p.click('[data-rview="ort"]'); await d.wait(250)
    await d.js("App.openLightbox(Req.entriesR('demo-r-show').find(e => e.f.was.includes('onerror')).id, 'A', 0)"); await d.wait(400)
    await d.p.keyboard.press('Escape'); await d.wait(200)
    await d.js("(() => { window.__p = Req.pickOrt('demo-r-show'); })()"); await d.wait(300); await d.p.keyboard.press('Escape'); await d.wait(200)
    await d.js("Req.editPersons('demo-r-show')"); await d.wait(300); await d.p.keyboard.press('Escape'); await d.wait(200)
    check(not await d.js("window.__xss"), 'Skript ausgeführt')
    check(await d.js("document.querySelectorAll('img[onerror]').length") == 0, 'img mit onerror im DOM')
    return d


@test
async def t_r22_duplizieren(B):
    d = await device(B, depts=['R'])
    r = await d.js("""async () => { const n = await Repo.duplicateShow('demo-r-show'), sid = n.id;
        const es = Req.entriesR(sid), st = Req.steps(sid), ab = Req.abschnitte(sid), ps = Req.persons(sid);
        const ids = new Set(es.map(e => e.id)), pk = new Set(ps.map(p => p.key)), ak = new Set(ab.map(a => a.key));
        return { n: es.length, steps: st.length, abs: ab.map(a => a.label).join(), persons: ps.length,
          inOk: es.filter(e => e.f.inId).every(e => ids.has(e.f.inId)), persOk: es.every(e => (e.f.personIds || []).every(k => pk.has(k))),
          stepOk: st.every(s => ak.has(s.abschnitt) && (!s.gegenstand || ids.has(s.gegenstand))), dauer: Req.sh(sid).dauer }; }""")
    check(r['n'] == await d.js("Req.entriesR('demo-r-show').length") and r['steps'] == await d.js("Req.steps('demo-r-show').length"), f'Kopie unvollständig {r}')
    check(r['inOk'] and r['persOk'] and r['stepOk'] and r['persons'] == 5 and r['dauer'], f'Verweise zeigen nicht auf die Kopien {r}')
    return d


# ======================================================================
async def main():
    sel = [t for t in TESTS if not ONLY or ONLY in t.__name__.lower()]
    ok = fail = skip = 0
    t0 = time.time()
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])
        for t in sel:
            name = t.__name__[2:]
            try:
                res = await t(browser)
                if isinstance(res, str):
                    skip += 1; print(f'  –  {name}: {res}'); continue
                if isinstance(res, Dev) and res.errors:
                    raise AssertionError('Seitenfehler: ' + ' | '.join(res.errors[:3]))
                ok += 1; print(f'  ✓  {name}')
            except Exception as e:
                fail += 1; print(f'  ✗  {name}: {e}')
                if os.environ.get('TRACE'): traceback.print_exc()
            finally:
                for c in list(browser.contexts): await c.close()
        await browser.close()
    print(f'\n{ok} bestanden, {fail} fehlgeschlagen, {skip} übersprungen · {len(sel)} Prüfungen · {time.time() - t0:.0f} s')
    print(f'App: {ROOT}' + (f' · Vergleich: {ALT}' if ALT else ''))
    sys.exit(1 if fail else 0)


asyncio.run(main())
