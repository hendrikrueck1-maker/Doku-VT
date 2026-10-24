"""Doku VT – Stresstest (QA, misstrauisch). App-Code wird nicht verändert.
An 2.8.3 angepasst (Erwartungen, die sich mit den Korrekturen bewusst geändert haben, sind mit „2.8.3:“ markiert).
Aufruf:  python3 test_stress.py <ordner>            (alle Abschnitte)
         python3 test_stress.py <ordner> -k A1,B3   (nur passende Abschnitte, Präfix genügt: -k A)
Ergebnisse: OUT (Standard /tmp/doku-vt-stress): befunde.json, Protokoll, PDFs, screens/
Jedes Gerät ist ein eigener Browser-Kontext, Kamera über --use-fake-device-for-media-stream."""
import asyncio, sys, subprocess, http.server, threading, functools, os, json, time, re, traceback, base64, io, random
from playwright.async_api import async_playwright

ARGS = [a for a in sys.argv[1:] if not a.startswith('-')]
ROOT = os.path.abspath(ARGS[0] if ARGS else os.path.dirname(os.path.abspath(__file__)))
SEL = None
if '-k' in sys.argv:
    SEL = [s.strip() for s in sys.argv[sys.argv.index('-k') + 1].split(',') if s.strip()]
OUT = os.environ.get('OUT', '/tmp/doku-vt-stress')
os.makedirs(OUT, exist_ok=True); os.makedirs(f'{OUT}/screens', exist_ok=True); os.makedirs(f'{OUT}/pdf', exist_ok=True)

class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT))
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/index.html'
VER = json.load(open(os.path.join(ROOT, 'version.json')))['version']

CHECKS, BEFUNDE, ERRS = [], [], []
LOG = open(f'{OUT}/protokoll.txt', 'w')
def log(*a):
    s = ' '.join(str(x) for x in a); print(s); LOG.write(s + '\n'); LOG.flush()
CUR = ['']
def ok(c, m):
    CHECKS.append((CUR[0], bool(c), m)); log(('  OK    ' if c else '  FAIL  ') + m)
    return bool(c)
def bef(sev, titel, detail, art='reproduziert'):
    """Befund festhalten. sev: kritisch | hoch | mittel | niedrig | Hinweis. art: reproduziert | Verdacht – auf Gerät prüfen | dokumentiert"""
    BEFUNDE.append({'abschnitt': CUR[0], 'schwere': sev, 'titel': titel, 'detail': detail, 'art': art})
    log(f'  >>> BEFUND [{sev}] {titel}\n      {detail}')

INIT = r"""(()=>{
  const RD = Date; let off = +(sessionStorage.getItem('__off') || %OFF%);
  window.__setOff = v => { off = v; sessionStorage.setItem('__off', v); };
  class FD extends RD { constructor(...a) { if (a.length === 0) super(RD.now() + off); else super(...a); } static now() { return RD.now() + off; } }
  FD.UTC = RD.UTC; FD.parse = RD.parse; window.Date = FD;
  window.__xss = 0; window.alert = () => { window.__xss++; }; window.confirm = () => true;
})();"""

async def _accept(d):
    try: await d.accept()
    except Exception: pass          # schon von einer anderen Stelle behandelt (beforeunload)

async def newpage(b, w=1180, h=820, off=0, name='', demo=True, wait=True, tz='Europe/Berlin'):
    ctx = await b.new_context(viewport={'width': w, 'height': h}, service_workers='block', permissions=['camera'],
                              timezone_id=tz, locale='de-DE')
    await ctx.add_init_script(INIT.replace('%OFF%', str(int(off))))
    p = await ctx.new_page(); p._errs = []; p._name = name or f'{w}x{h}'
    def onerr(e):
        p._errs.append(str(e)); ERRS.append((CUR[0], p._name, str(e)[:300]))
    p.on('pageerror', onerr)
    p.on('console', lambda m: onerr('console.error: ' + m.text) if m.type == 'error' else None)
    p.on('dialog', lambda d: asyncio.ensure_future(_accept(d)))
    if wait:
        await p.goto(URL)
        await p.wait_for_function('window.Boot && Boot.started', timeout=30000)
        if not demo:   # frisches Gerät ohne Demo (Demo hat Zufalls-IDs je Gerät): Demo abschalten, Daten leeren, neu laden
            await p.evaluate("(async()=>{await Settings.set({demoOnFirstStart:false}); await Store.tx(['shows','entries','photos','fulls','thumbs'],'readwrite',s=>{['shows','entries','photos','fulls','thumbs'].forEach(n=>s[n].clear())}); await Store.metaSet('demoDone',true);})()")
            await p.reload(); await p.wait_for_function('window.Boot && Boot.started', timeout=30000)
    return ctx, p

async def ev(p, s, ms=1500):
    """Ausdruck auswerten, ohne auf Blätter/Dialoge zu warten, die erst beim Schließen auflösen"""
    return await p.evaluate("([s,ms]) => Promise.race([Promise.resolve((0,eval)(s)).then(()=>'ok',e=>'err '+e.message), new Promise(r=>setTimeout(()=>r('offen'),ms))])", [s, ms])

async def open_run(p):
    """Kasten „Vor der Vorstellung“ aufklappen (bei reinen Licht-Geräten absichtlich zu)"""
    await p.evaluate("SetupView.open.run=true; App.render()"); await p.wait_for_timeout(250)

async def reload(p):
    await p.reload(); await p.wait_for_function('window.Boot && Boot.started', timeout=30000); await p.wait_for_timeout(300)

async def pkg(p, since=0, typ='sync', depts='null', ids='null'):
    """Sync-Paket als Text bauen (wie FileAdapter, ohne Teilen-Dialog)"""
    return await p.evaluate(f"(async()=>{{const r=await Sync.buildPackage({{type:'{typ}',since:{since},depts:{depts},showIds:{ids}}}); return await r.blob.text()}})()")

async def imp(p, text):
    return await p.evaluate("async t=>{try{return await Sync.importPackage(new File([t],'x.json'))}catch(e){return {err:e.message}}}", text)

async def full_sync(a, b):
    """A → B komplett (Geräte-Abteilungen des Senders, wie FileAdapter)"""
    t = await a.evaluate("(async()=>{const r=await Sync.buildPackage({type:'sync',since:0,depts:Settings.v.depts.slice()}); return await r.blob.text()})()")
    return await imp(b, t)

JS_MKPHOTO = """async (n, px) => { const out = []; for (let i = 0; i < n; i++) { const c = document.createElement('canvas'); c.width = c.height = px || 200;
  const g = c.getContext('2d'); g.fillStyle = `hsl(${(i*47)%360},60%,40%)`; g.fillRect(0, 0, c.width, c.height); g.fillStyle = '#fff'; g.font = '40px sans-serif'; g.fillText(String(i), 20, 80);
  const r = await Photo.fromCanvas(c, 0.6); out.push(r); } return out; }"""

def pdftext(path, layout=True):
    return subprocess.run(['pdftotext'] + (['-layout'] if layout else []) + [path, '-'], capture_output=True, text=True).stdout
def qpdf_ok(path):
    return subprocess.run(['qpdf', '--check', path], capture_output=True).returncode == 0
async def save_pdf(p, js, name):
    data = await p.evaluate(f"(async()=>{{const b=await ({js}); return Array.from(new Uint8Array(await b.arrayBuffer()))}})()")
    path = f'{OUT}/pdf/{name}.pdf'; open(path, 'wb').write(bytes(data)); return path

SECTIONS = []
def section(code):
    def deco(fn):
        SECTIONS.append((code, fn)); return fn
    return deco

# =====================================================================================
# A. Datenintegrität und Speicher
# =====================================================================================
@section('A1')
async def a1_atomic(b):
    """Atomarität: Schreibvorgang scheitert mitten in Store.tx (synchron und asynchron)"""
    ctx, p = await newpage(b, name='A1')
    r = await p.evaluate("""(async()=>{
      const put = IDBObjectStore.prototype.put; let mode = 'sync';
      IDBObjectStore.prototype.put = function (v, ...a) {
        if (v && (v.id === 'boom' || (v.v && v.v.id === 'boom'))) { if (mode === 'sync') throw new DOMException('kaputt', 'DataError'); const r = put.call(this, v, ...a); this.transaction.abort(); return r; }
        return put.call(this, v, ...a); };
      const s = Rec.create({ id: 'atom-show' }, { titel: 'Atom', del: false });
      const e = Rec.create({ id: 'boom', showId: 'atom-show' }, { abt: 'L', kreis: '1', del: false });
      const res = [];
      for (mode of ['sync', 'async']) {
        let msg = '';
        try { await Repo._write({ shows: [s], entries: [e] }); msg = 'KEIN FEHLER'; } catch (err) { msg = err.message; }
        res.push([mode, msg, Repo.shows.has('atom-show'), Repo.entries.has('boom')]);
      }
      IDBObjectStore.prototype.put = put; return res; })()""")
    log('   ', r)
    for mode, msg, hs, he in r:
        ok(not hs and not he and msg != 'KEIN FEHLER', f'{mode}: Fehler gemeldet ({msg[:60]}), RAM zurückgerollt')
    await reload(p)
    ok(await p.evaluate("!Repo.shows.has('atom-show') && !Repo.entries.has('boom')"), 'Nach Neuladen: nichts gespeichert')
    if r[1][1].startswith('Speichern abgebrochen: unbekannter'):
        bef('niedrig', 'Abgebrochene Transaktion meldet nur „unbekannter Fehler“',
            'Wird eine IndexedDB-Transaktion ohne error-Objekt abgebrochen (z. B. Safari bei Speicherdruck), lautet die Meldung „Speichern abgebrochen: unbekannter Fehler“. '
            'Der Hinweis, dass NICHTS gespeichert wurde, fehlt – anders als bei Quota. Daten sind konsistent (Rückrollen funktioniert).')
    await ctx.close()

@section('A2')
async def a2_quota(b):
    """Speicher voll beim Speichern im Editor – Eingaben und Fotos bleiben, zweiter Versuch klappt"""
    ctx, p = await newpage(b, name='A2')
    hai = await p.evaluate("Repo.liveShows().find(s=>s.f.titel.startsWith('Demo: Der Haifisch')).id")
    await p.evaluate(f"App.state.edit=true; location.hash='#/show/{hai}'"); await p.wait_for_timeout(500)
    await p.evaluate(f"Editor.open({{showId:'{hai}', abt:'L'}})"); await p.wait_for_timeout(300)
    await p.fill('[data-editor] [name=kreis]', '4711'); await p.fill('[data-editor] [name=bemerkung]', 'Quota-Test Bemerkung')
    # Foto über die Mediathek der Kamera
    await p.click('[data-editor] .pk[data-k=A] [data-act=cam]'); await p.wait_for_timeout(700)
    jpg = await p.evaluate("new Promise(r=>{const c=document.createElement('canvas'); c.width=900; c.height=900; c.getContext('2d').fillRect(0,0,10,10); c.toBlob(async b=>r(Array.from(new Uint8Array(await b.arrayBuffer()))),'image/jpeg',0.9)})")
    await p.set_input_files('.cam input[type=file][multiple]', files=[{'name': 'a.jpg', 'mimeType': 'image/jpeg', 'buffer': bytes(jpg)}])
    await p.wait_for_timeout(1200)
    if await p.evaluate("!!document.querySelector('.cam')"): await p.click('.cam [data-a=done]')
    await p.wait_for_timeout(300)
    # synchroner Quota-Fehler (wie er in WebKit beim put geworfen werden kann)
    await p.evaluate("""window.__put = IDBObjectStore.prototype.put; IDBObjectStore.prototype.put = function(v,...a){ if (this.name==='fulls') throw new DOMException('Speicher voll','QuotaExceededError'); return __put.call(this,v,...a); }; 1""")
    await p.click('[data-editor] .sheet-h [data-act=save]'); await p.wait_for_timeout(600)
    d = await p.evaluate("[document.querySelector('.dialog h2')?.textContent||'', document.querySelector('.dialog p')?.textContent||'']")
    still = await p.evaluate("[!!document.querySelector('[data-editor]'), document.querySelector('[data-editor] [name=kreis]')?.value, document.querySelectorAll('[data-editor] .pgrid[data-k=A] .slot:not(.add)').length]")
    log('   Dialog:', d, 'Editor:', still)
    ok(d[0] == 'Speicher voll', 'Dialog „Speicher voll“')
    ok('NICHTS' in d[1], 'Meldung sagt „Es wurde NICHTS gespeichert“')
    if d[0] == 'Speicher voll' and 'NICHTS' not in d[1]:
        bef('niedrig', 'Speicher voll: Meldung ohne „Es wurde NICHTS gespeichert“ und ohne Hinweis auf Aufräumen',
            f'Wirft der Browser QuotaExceededError schon beim put() (synchron), endet Store.tx im catch-Zweig mit „{d[1][:90]}“. '
            'Der Dialog heißt zwar „Speicher voll“, sagt aber nicht, dass nichts gespeichert wurde und was zu tun ist. '
            'Nur beim asynchronen Abbruch (onabort) kommt die ausführliche Meldung. Ob ein Browser Quota synchron beim put() meldet, ist offen.', art='Verdacht – auf Gerät prüfen')
    ok(still[0] and still[1] == '4711' and still[2] == 1, 'Editor bleibt offen mit Kreis und Foto')
    ok(await p.evaluate("!Repo.entriesOf('%s').some(e=>e.f.kreis==='4711')" % hai), 'Nichts im RAM gespeichert')
    await p.evaluate("IDBObjectStore.prototype.put = __put; 1")
    await p.click('.dialog .btn.primary'); await p.wait_for_timeout(300)
    # realistischer Weg (Chromium/WebKit): Quota-Fehler kommt asynchron als Abbruch der Transaktion
    await p.evaluate("""IDBObjectStore.prototype.put = function(v,...a){ const r=__put.call(this,v,...a); if (this.name==='fulls') { const t=this.transaction; Object.defineProperty(t,'error',{get:()=>new DOMException('voll','QuotaExceededError')}); setTimeout(()=>{try{t.abort()}catch(e){}},0); } return r; }; 1""")
    await p.click('[data-editor] .sheet-h [data-act=save]'); await p.wait_for_timeout(700)
    d2 = await p.evaluate("[document.querySelector('.dialog h2')?.textContent||'', document.querySelector('.dialog p')?.textContent||'', !!document.querySelector('[data-editor]')]")
    log('   Asynchroner Quota-Abbruch:', d2)
    ok('NICHTS' in d2[1] and d2[2], 'Asynchroner Quota-Abbruch (Normalfall): „Es wurde NICHTS gespeichert“, Editor bleibt offen')
    await p.evaluate("IDBObjectStore.prototype.put = __put; 1")
    if await p.evaluate("!!document.querySelector('.dialog')"): await p.click('.dialog .btn.primary'); await p.wait_for_timeout(300)
    await p.click('[data-editor] .sheet-h [data-act=save]'); await p.wait_for_timeout(900)
    await reload(p)
    n = await p.evaluate("(()=>{const e=Repo.entriesOf('%s').filter(e=>e.f.kreis==='4711'); return [e.length, e[0]?Repo.photosOf(e[0].id).length:0, e[0]?e[0].f.bemerkung:'']})()" % hai)
    ok(n == [1, 1, 'Quota-Test Bemerkung'], f'Zweiter Versuch gespeichert, nach Neuladen genau 1 Eintrag mit Foto ({n})')
    await ctx.close()

@section('A3')
async def a3_rapid(b):
    """Schnelle Folgen: 30 Haken in < 1 s, Editor dreimal schnell speichern, 20 Cue-Fotos ohne Pause"""
    ctx, p = await newpage(b, name='A3')
    sid = await p.evaluate("""(async()=>{const f={}; for(let i=0;i<30;i++) f['ci:r'+i]={abt:'L',text:'Punkt '+i,ord:i,del:false};
      const s=await Repo.createShow('Schnell',['L']); await Repo.patchShow(s.id,f); return s.id})()""")
    await p.evaluate(f"location.hash='#/show/{sid}'"); await p.wait_for_timeout(500)
    await open_run(p)
    await p.click('[data-box=run] [data-run=start]'); await p.wait_for_timeout(500)
    t = await p.evaluate("""(async()=>{const t0=performance.now(); const keys=[...document.querySelectorAll('[data-box=run] .runchk')].map(b=>b.dataset.run);
      for (const k of keys) { const b=document.querySelector(`[data-box=run] .runchk[data-run="${k}"]`) || document.querySelector('[data-box=run] .runchk'); b.click(); await new Promise(r=>setTimeout(r,20)); }
      return [keys.length, Math.round(performance.now()-t0)]})()""")
    await p.wait_for_timeout(800)
    await reload(p)
    n = await p.evaluate(f"(()=>{{const r=RunList.runsOf('{sid}'); return [r.length, Object.keys(r[0].f).filter(k=>k.startsWith('h:')&&r[0].f[k].ok).length]}})()")
    ok(n == [1, t[0]], f'{t[0]} Haken (30 + Ablauf „vorher“) in {t[1]} ms, nach Neuladen alle 30 gespeichert, ein Durchgang ({n})')
    # Editor dreimal schnell speichern
    await p.evaluate(f"App.state.edit=true; location.hash='#/show/{sid}'"); await p.wait_for_timeout(300)
    await p.evaluate(f"Editor.open({{showId:'{sid}', abt:'L'}})"); await p.wait_for_timeout(300)
    await p.fill('[data-editor] [name=kreis]', '808')
    await p.evaluate("for(let i=0;i<3;i++) document.querySelector('[data-editor] .sheet-h [data-act=save]')?.click()")
    await p.wait_for_timeout(800); await reload(p)
    ok(await p.evaluate(f"Repo.entriesOf('{sid}').filter(e=>e.f.kreis==='808').length") == 1, 'Editor dreimal schnell gespeichert → genau ein Eintrag')
    # 20 Cue-Fotos ohne Pause
    lid = await p.evaluate("(async()=>{const l=await Cues.createList({titel:'Rapid'}); return l.id})()")
    await p.evaluate(f"App.state.edit=true; location.hash='#/cue/{lid}'"); await p.wait_for_timeout(400)
    await p.click('[data-cact=cam]')
    await p.wait_for_function("document.querySelector('.ccam video') && document.querySelector('.ccam video').videoWidth>0", timeout=15000)
    await p.evaluate("for(let i=0;i<20;i++) document.querySelector('.ccam [data-a=shot]').click()")
    await p.click('.ccam [data-a=close]')
    await p.wait_for_function('CueCam.pending()===0 && !CueCam.busy', timeout=30000)
    await reload(p)
    r = await p.evaluate(f"(()=>{{const c=Cues.cuesOf('{lid}'); return [c.length, c[0]?Cues.imgsOf(c[0].id).length:0, c[0]?Cues.imgsOf(c[0].id).map((x,i)=>Cues.letter(i)).join(''):'']}})()")
    ok(r[0] == 1 and r[1] == 20, f'20 Cue-Fotos schnell, Kamera sofort geschlossen → nach Neuladen alle da ({r})')
    await ctx.close()

@section('A4')
async def a4_maxfields(b):
    """Feldgrenze Rec.MAX_FIELDS: Tombstones wachsen, Paket an anderes Gerät"""
    ctx, p = await newpage(b, name='A4-A')
    # realistische Wachstumsrate: Raster anlegen und wieder löschen, Schritte anlegen/löschen
    r = await p.evaluate("""(async()=>{
      await Settings.set({depts:['L','T','B','R']}); await Req.ensureHouse(); const t=await Req.testShow(); const sid=t.id;
      const n0=Object.keys(Repo.show(sid).f).length;
      await Req.addOrts(sid, Array.from({length:24},(_,i)=>'R'+i), 'Raster');
      const n1=Object.keys(Repo.show(sid).f).length;
      const p={}; Req.showOrts(sid).filter(o=>o.gruppe==='Raster').forEach(o=>{p[o.key]=Object.assign({},Repo.show(sid).f[o.key],{del:true})}); await Repo.patchShow(sid,p);
      const n2=Object.keys(Repo.show(sid).f).length; return [sid,n0,n1,n2]})()""")
    sid, n0, n1, n2 = r
    log(f'   Testvorstellung: {n0} Felder, nach Raster 24: {n1}, nach Löschen: {n2} (Tombstones bleiben)')
    ok(n2 == n1, 'Gelöschte Orte bleiben als Feld stehen (Tombstone) – wie dokumentiert')
    # über die Grenze: Schritte anlegen und löschen bis > 2000 Felder
    await p.evaluate(f"""(async()=>{{const p={{}}; for(let i=0;i<2000;i++) p['rs:t'+i]={{abschnitt:'ra:test-t1',text:'alt '+i,ord:i,del:true}}; await Repo.patchShow('{sid}',p);}})()""")
    nf = await p.evaluate(f"Object.keys(Repo.show('{sid}').f).length")
    ok(nf > 2000, f'Veranstaltung hat jetzt {nf} Felder (lokal ohne Warnung gespeichert)')
    await p.evaluate(f"App.state.edit=true; location.hash='#/show/{sid}'"); await p.wait_for_timeout(500)
    await p.evaluate(f"Repo.patchShow('{sid}',{{dauer:'2:45 mit Pause'}})")
    text = await pkg(p)
    ctx2, p2 = await newpage(b, name='A4-B')
    await p2.evaluate("Settings.set({depts:['L','T','B','R']})")
    # Import über die Oberfläche (Dialog lesen)
    await p2.evaluate("async t=>{ window.__f=new File([t],'paket.ldsync.json'); }", text)
    await p2.evaluate("App.importFile(window.__f)"); await p2.wait_for_timeout(2500)
    dlg = await p2.evaluate("document.querySelector('.dialog')?.innerText||''")
    has = await p2.evaluate(f"[!!Repo.show('{sid}'), Repo.entriesOf('{sid}').length, Sync.status().label]")
    log('   Gerät B Dialog:', dlg.replace('\n', ' | ')[:300]); log('   Gerät B:', has)
    ok(has[0], 'Gerät B hat die Veranstaltung')
    if not has[0]:
        bef('hoch', 'Veranstaltung mit > 2000 Feldern wird beim Abgleich still verworfen',
            f'Lokal speichert die App beliebig viele Felder (Tombstones gelöschter Schritte/Orte/Punkte bleiben für immer). Rec.valid lehnt beim Empfänger '
            f'Datensätze mit > {2000} Feldern ab. Ergebnis auf Gerät B: Veranstaltung fehlt, aber {has[1]} Einträge sind da (unsichtbar, ohne Veranstaltung). '
            f'Der Import-Dialog meldet „{dlg.splitlines()[1] if len(dlg.splitlines())>1 else dlg[:80]}“, der Status zeigt „{has[2]}“ – die Ablehnung erfährt niemand. '
            'Die Diagnose warnt ab 1500 Feldern nur, wenn man sie öffnet; beim Speichern/Paket gibt es keine Warnung. '
            'Realistisch: Testvorstellung hat ~45 Felder; ein falsch angelegtes Raster 10×20 (200 Felder) dreimal anlegen und löschen reicht für 600 tote Felder. '
            'Über eine normale Spielzeit selten, aber dann ohne jede Rückmeldung.')
    # 2.8.3: Grenze beim Empfänger 20 000 Felder – nichts abgelehnt; Abgelehntes würde der Dialog mit „NICHT übernommen“ nennen (test_283.py)
    ok('NICHT übernommen' not in dlg, 'Import-Dialog: nichts abgelehnt (2.8.3: Grenze 20 000 Felder)')
    diag = await p.evaluate("(async()=>{await DiagView.open(); await new Promise(r=>setTimeout(r,500)); return document.querySelector('.sheet .sheet-b').innerText})()")
    ok('2.8.2 oder älter' in diag, 'Diagnose auf Gerät A zeigt die Feldwarnung (für Geräte mit 2.8.2 oder älter)')
    # Textgrenze MAX_STR
    # 2.8.3: Ein Text über MAX_STR wird gar nicht erst gespeichert (klare Meldung) – der Empfänger kann ihn nicht mehr still verwerfen
    big = await p.evaluate(f"""(async()=>{{const e=Repo.entriesOf('{sid}')[0]; try {{ await Repo.saveDraft({{id:e.id, showId:e.showId, abt:'R', f:{{bemerkung:'x'.repeat(100001)}}, photos:{{A:Repo.photosOf(e.id,'A').map(p=>({{photoId:p.id,b:p.b,w:p.w,h:p.h}})),E:[]}}, initialPhotos:new Set()}}); }} catch(err) {{ window.__refused=err.message; }} return e.id}})()""")
    refused = await p.evaluate("window.__refused||''")
    ok('zu lang' in refused and 'NICHTS gespeichert' in refused, '2.8.3: Bemerkung > 100 000 Zeichen wird lokal abgelehnt (klare Meldung)')
    text = await pkg(p, ids=f"['{sid}']", typ='backup')
    st = await imp(p2, text)
    got = await p2.evaluate(f"(Repo.entries.get('{big}')||{{f:{{}}}}).f.bemerkung?.length||0")
    log('   MAX_STR:', st.get('ungueltig'), got)
    if got < 100001 and not refused:
        bef('mittel', 'Eintrag mit sehr langer Bemerkung (> 100 000 Zeichen) wird beim Empfänger still verworfen',
            f'Lokal speicherbar (kein Limit im Editor), beim Abgleich lehnt Rec.valid den ganzen Eintrag ab (ungültig: {st.get("ungueltig")}). '
            'Der Empfänger behält den alten Stand des Eintrags; der Absender sieht „Synchron“. Kein Hinweis beim Speichern oder Import.')
    await ctx.close(); await ctx2.close()

@section('A5')
async def a5_trash(b):
    """Papierkorb über zwei Geräte, auch Löschungen aus 2.4.2 ohne delGrp"""
    ctxA, A = await newpage(b, name='A5-A'); ctxB, B = await newpage(b, name='A5-B')
    sid = await A.evaluate("""(async()=>{const s=await Repo.createShow('Papierkorb',['L']); const es=[]; for(let i=1;i<=5;i++) es.push(Rec.create({showId:s.id},{abt:'L',kreis:String(i),chkA:false,chkE:false,del:false}));
      await Repo._write({entries:es}); return s.id})()""")
    await imp(B, await pkg(A))
    e = await A.evaluate(f"Repo.entriesOf('{sid}').sort((a,b)=>a.f.kreis-b.f.kreis).map(e=>e.id)")
    # B löscht Kreis 2 VOR dem Löschen der Veranstaltung auf A (ohne Abgleich dazwischen)
    await B.evaluate(f"Repo.deleteEntry('{e[1]}')"); await A.wait_for_timeout(30)
    await A.evaluate(f"Repo.deleteShow('{sid}')"); await A.wait_for_timeout(30)
    # B löscht Kreis 3 NACH dem Löschen auf A (ohne Abgleich dazwischen)
    await B.evaluate(f"Repo.deleteEntry('{e[2]}')")
    await imp(B, await pkg(A)); await imp(A, await pkg(B))
    await A.evaluate(f"Repo.restoreShow('{sid}')")
    await imp(B, await pkg(A))
    for P, nm in ((A, 'A'), (B, 'B')):
        await reload(P)
        live = await P.evaluate(f"Repo.entriesOf('{sid}').map(e=>e.f.kreis).sort().join(',')")
        log(f'   {nm} nach Wiederherstellen: {live}')
        ok('3' not in live.split(','), f'{nm}: Kreis 3 (später einzeln gelöscht) bleibt gelöscht')
        if nm == 'A' and '2' in live.split(','):
            bef('niedrig', 'Wiederherstellen bringt einen Eintrag zurück, den ein anderes Gerät VOR dem Löschen der Veranstaltung einzeln gelöscht hatte',
                'Gerät B löscht Kreis 2, Gerät A (noch ohne Abgleich) löscht danach die ganze Veranstaltung. A markiert Kreis 2 mit seiner Lösch-Kennung und jüngerem Zeitstempel – '
                'nach dem Abgleich gilt Kreis 2 als „mit der Veranstaltung gelöscht“ und kommt beim Wiederherstellen zurück. Nur bei Löschen ohne vorherigen Abgleich.')
    # 2.4.2: Löschung ohne delGrp nachbauen
    sid2 = await A.evaluate("""(async()=>{const s=await Repo.createShow('Alt 2.4.2',['L']); const es=[1,2,3].map(i=>Rec.create({showId:s.id},{abt:'L',kreis:String(i),chkA:false,chkE:false,del:false}));
      await Repo._write({entries:es}); await new Promise(r=>setTimeout(r,20));
      const e1=Rec.patch(Repo.entries.get(es[0].id),{del:true}); await Repo._write({entries:[e1]}); await new Promise(r=>setTimeout(r,20));
      const sh=Rec.patch(Repo.shows.get(s.id),{del:true}); await Repo._write({shows:[sh]});
      const rest=es.slice(1).map(x=>Rec.patch(Repo.entries.get(x.id),{del:true})); await Repo._write({entries:rest});
      await Repo.restoreShow(s.id); return Repo.entriesOf(s.id).map(e=>e.f.kreis).sort().join(',')})()""")
    ok(sid2 == '2,3', f'Löschung ohne Kennung (2.4.2): wiederhergestellt nur, was mit der Veranstaltung ging ({sid2})')
    await ctxA.close(); await ctxB.close()

@section('A6')
async def a6_cleanup(b):
    """„Speicher aufräumen“ darf keine noch gebrauchten Bilder löschen – Gegenprobe je Fall"""
    ctx, p = await newpage(b, name='A6')
    r = await p.evaluate(JS_MKPHOTO.replace('async (n, px) =>', 'window.__mk = async (n, px) =>') + "; 1")
    r = await p.evaluate("""(async()=>{
      await Settings.set({depts:['L','T','B','R']}); await Req.ensureHouse();
      const ph = await __mk(10, 200); const B = {}; const names = ['trashShow','ortFoto','uebersicht','hausOrt','vorlage','cueLive','cueTrash','cueOrig','cueMarked','dupDel'];
      names.forEach((n,i)=>B[n]=ph[i]); const fulls = ph.map(x=>({id:x.b,d:x.full})), thumbs = ph.map(x=>({id:x.b,d:x.thumb}));
      await Repo._write({fulls, thumbs});
      // 1 Veranstaltung im Papierkorb mit Foto
      const s1 = await Repo.createShow('Weg',['L']); const e1 = Rec.create({showId:s1.id},{abt:'L',kreis:'1',del:false});
      const p1 = Rec.create({showId:s1.id,b:B.trashShow.b,w:200,h:200},{entryId:e1.id,kat:'A',ord:0,label:'',del:false});
      await Repo._write({entries:[e1],photos:[p1]}); await Repo.deleteShow(s1.id);
      // 2 Requisite: Ortsfoto, Übersichtsfoto
      const s2 = await Repo.createShow('Req',['R']); await Repo.patchShow(s2.id,{fotoR:B.uebersicht.b,'ro:o1':{name:'Ort',foto:B.ortFoto.b,ord:1,del:false}});
      // 3 Haus-Ort-Foto und Vorlagenfoto
      const hf = Req.houseF(); const hk = Object.keys(hf).find(k=>k.startsWith('ho:')), vk = Object.keys(hf).find(k=>k.startsWith('hg:'));
      await Repo.patchHouse({[hk]:Object.assign({},hf[hk],{foto:B.hausOrt.b}), [vk]:Object.assign({},hf[vk],{foto:B.vorlage.b})});
      // 4 Cue-Fotos: lebend, Liste im Papierkorb, markiert mit Original
      const l1 = await Cues.createList({titel:'Lebend'}), l2 = await Cues.createList({titel:'Papierkorb'});
      const c1 = Cues.newCue(l1.id,'1'), c2 = Cues.newCue(l2.id,'1');
      const i1 = Rec.create({listId:l1.id},{cueId:c1.id,ord:0,b:B.cueLive.b,o:'',w:200,h:200,notiz:'',hinweis:'',del:false});
      const i2 = Rec.create({listId:l2.id},{cueId:c2.id,ord:0,b:B.cueTrash.b,o:'',w:200,h:200,notiz:'',hinweis:'',del:false});
      const i3 = Rec.create({listId:l1.id},{cueId:c1.id,ord:1,b:B.cueMarked.b,o:B.cueOrig.b,w:200,h:200,notiz:'',hinweis:'',del:false});
      await Repo._write({cues:[c1,c2],cueimgs:[i1,i2,i3]}); await Cues.deleteList(l2.id);
      // 5 duplizierte Veranstaltung löschen – Original behält Bilder
      const s3 = await Repo.createShow('Original',['L']); const e3 = Rec.create({showId:s3.id},{abt:'L',kreis:'9',del:false});
      const p3 = Rec.create({showId:s3.id,b:B.dupDel.b,w:200,h:200},{entryId:e3.id,kat:'A',ord:0,label:'',del:false});
      await Repo._write({entries:[e3],photos:[p3]}); const dup = await Repo.duplicateShow(s3.id); await Repo.deleteShow(dup.id);
      // Waise zur Gegenprobe
      const orphan = (await __mk(1, 100))[0]; await Repo._write({fulls:[{id:orphan.b,d:orphan.full}],thumbs:[{id:orphan.b,d:orphan.thumb}]});
      const n = await Repo.cleanup();
      const res = {}; for (const k of names) res[k] = !!(await Repo.full(B[k].b)); res.orphan = !!(await Repo.full(orphan.b)); res.removed = n;
      // endgültig löschen der Papierkorb-Veranstaltung? nicht vorgesehen. Wiederherstellen prüfen:
      await Repo.restoreShow(s1.id); res.restoredPhoto = !!(await Repo.full(Repo.photosOf(Repo.entriesOf(s1.id)[0].id)[0].b));
      return res; })()""")
    log('   ', r)
    for k, v in r.items():
        if k in ('removed', 'orphan'): continue
        ok(v, f'Aufräumen behält: {k}')
    ok(r['orphan'] is False and r['removed'] >= 1, f'Gegenprobe: echte Waise wird entfernt ({r["removed"]})')
    # Geteilte Bilddaten: Foto kopieren, dann Kopie markieren (= neues Foto) / löschen
    r = await p.evaluate("""(async()=>{
      const s = await Repo.createShow('Teilen',['L']); const ph = (await __mk(2, 300));
      const res = await Repo.saveDraft({id:null, showId:s.id, abt:'L', f:{kreis:'5'}, photos:{A:[{photoId:null,b:ph[0].b,w:300,h:300,full:ph[0].full,thumb:ph[0].thumb}],E:[]}});
      const pa = Repo.photosOf(res.entryId,'A')[0];
      // Kopie in Einleuchten (wie Editor „Zu Einleuchten kopieren“)
      await Repo.saveDraft({id:res.entryId, showId:s.id, abt:'L', f:{}, photos:{A:[{photoId:pa.id,b:pa.b,w:300,h:300}],E:[{photoId:null,b:pa.b,w:300,h:300}]}, initialPhotos:new Set([pa.id])});
      const pe = Repo.photosOf(res.entryId,'E')[0];
      // Kopie markieren → neues Bild ersetzt die Kopie
      await Repo.saveDraft({id:res.entryId, showId:s.id, abt:'L', f:{}, photos:{A:[{photoId:pa.id,b:pa.b,w:300,h:300}],E:[{photoId:null,b:ph[1].b,w:300,h:300,full:ph[1].full,thumb:ph[1].thumb}]}, initialPhotos:new Set([pa.id,pe.id])});
      await Repo.cleanup();
      const a = Repo.photosOf(res.entryId,'A')[0], e = Repo.photosOf(res.entryId,'E')[0];
      return [a.b===pa.b, !!(await Repo.full(a.b)), e.b===ph[1].b, !!(await Repo.full(e.b))]; })()""")
    ok(r == [True, True, True, True], f'Kopie markiert/ersetzt + Aufräumen: Original unverändert ({r})')
    await reload(p)
    ok(await p.evaluate("Repo.liveShows().some(s=>s.f.titel==='Weg')"), 'Nach Neuladen: wiederhergestellte Veranstaltung da')
    await ctx.close()

@section('A7')
async def a7_migration(b):
    """Datenbank aus 1.8.1 und 2.3.0/2.4.0 (mit Speicher „runs“) nachbauen, 2.8.x darauf starten"""
    for variant in ('1.8.1', '2.4.0'):
        ctx = await b.new_context(viewport={'width': 1180, 'height': 820}, service_workers='block', timezone_id='Europe/Berlin')
        await ctx.add_init_script(INIT.replace('%OFF%', '0'))
        p = await ctx.new_page(); p._errs = []
        p.on('pageerror', lambda e: ERRS.append((CUR[0], 'A7', str(e))))
        await ctx.route('**/index.html', lambda r: r.fulfill(body='<!doctype html><title>leer</title>', content_type='text/html'))
        await p.goto(URL)
        now = int(time.time() * 1000)
        made = await p.evaluate("""async ([variant, now]) => {
          const ver = variant === '1.8.1' ? 1 : 2;
          const db = await new Promise((res, rej) => { const r = indexedDB.open('lichtdoku', ver); r.onupgradeneeded = () => { const d = r.result;
            d.createObjectStore('shows',{keyPath:'id'}); d.createObjectStore('entries',{keyPath:'id'}).createIndex('showId','showId'); d.createObjectStore('photos',{keyPath:'id'}).createIndex('showId','showId');
            d.createObjectStore('fulls',{keyPath:'id'}); d.createObjectStore('thumbs',{keyPath:'id'}); d.createObjectStore('meta',{keyPath:'k'}); if (ver===2) d.createObjectStore('runs',{keyPath:'id'}); };
            r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error); });
          const t0 = now - 86400000; const rec = (id, base, f) => { const r = Object.assign({id, c:t0, mod:t0, f:{}, t:{}}, base); for (const k in f) { r.f[k]=f[k]; r.t[k]=t0; } return r; };
          const show = rec('old-show', {}, {titel:'Alte Produktion', spielstaette:'', notiz:'', einrichtung:'OLZ prüfen', del:false});
          const es = [rec('old-e1',{showId:'old-show'},{kreis:'101',gruppe:'',filter:'L201',adresse:'',bemerkung:'',geraet:'',dmx:'1/12',position:'',farbe:'',chkA:true,chkE:false,del:false}),
                      rec('old-e2',{showId:'old-show'},{kreis:'102+103',gruppe:'2',filter:'',adresse:'',bemerkung:'alt',geraet:'',dmx:'',position:'',farbe:'',chkA:false,chkE:false,del:false})];
          const run = ver===2 ? rec('old-run',{showId:'old-show'},{datum:'2026-09-01',titel:'Vorstellung 01.09.2026',del:false,'h:ci:x':{ok:true,at:t0,dev:'iPad'}}) : null;
          await new Promise((res, rej) => { const tx = db.transaction(db.objectStoreNames, 'readwrite'); tx.objectStore('shows').put(show); es.forEach(e=>tx.objectStore('entries').put(e));
            if (run) tx.objectStore('runs').put(run);
            tx.objectStore('meta').put({k:'syncState', v:{lastSyncAt: now - 3600000, lastPackageAt: now - 3600000, lastError:'', log:[]}});
            tx.objectStore('meta').put({k:'settings', v:{theme:'dark'}}); tx.objectStore('meta').put({k:'deviceId', v:'old-device'}); tx.objectStore('meta').put({k:'demoDone', v:true});
            tx.oncomplete = res; tx.onerror = () => rej(tx.error); });
          db.close(); return JSON.stringify([show, es]); }""", [variant, now])
        await ctx.unroute('**/index.html')
        await p.goto(URL); await p.wait_for_function('window.Boot && Boot.started', timeout=30000); await p.wait_for_timeout(500)
        r = await p.evaluate("""(async()=>{const s=Repo.show('old-show'); const recs=[await Store.get('shows','old-show'), await Store.get('entries','old-e1'), await Store.get('entries','old-e2')];
          return {pending: Sync.pending(), status: Sync.status().label, depts: Repo.showDepts('old-show'), n: Repo.entriesOf('old-show').length, runs: RunList.runsOf('old-show').length,
            mods: recs.map(r=>r.mod), fields: recs.map(r=>Object.keys(r.f).sort().join(',')), demo: Repo.liveShows().length, dev: Settings.v.depts}})()""")
        orig = json.loads(made)
        same = r['mods'] == [orig[0]['mod'], orig[1][0]['mod'], orig[1][1]['mod']]
        log(f'   {variant}:', {k: r[k] for k in ('pending', 'status', 'depts', 'n', 'runs', 'demo', 'dev')})
        ok(r['pending'] == 0 and r['status'] == 'Synchron', f'{variant}: nichts gilt als geändert, Status „Synchron“')
        ok(same, f'{variant}: Datensätze unverändert in der Datenbank (mod gleich)')
        ok(r['depts'] == ['L'] and r['n'] == 2 and r['dev'] == ['L'], f'{variant}: alles Licht, Gerät nur Licht')
        if variant == '2.4.0': ok(r['runs'] == 1, '2.4.0: Durchgang aus Speicher „runs“ gelesen')
        # Öffnen und einen Eintrag unverändert speichern → kein neuer Zeitstempel
        await p.evaluate("App.state.edit=true; location.hash='#/show/old-show'"); await p.wait_for_timeout(500)
        await p.evaluate("Editor.open({showId:'old-show', entryId:'old-e1'})"); await p.wait_for_timeout(300)
        await p.click('[data-editor] .sheet-h [data-act=save]'); await p.wait_for_timeout(500)
        ok(await p.evaluate("Sync.pending()") == 0, f'{variant}: Eintrag unverändert gespeichert → bleibt „Synchron“')
        await ctx.close()

# =====================================================================================
# B. Abgleich
# =====================================================================================
@section('B1')
async def b1_merge(b):
    """Merge: 500 zufällige Paare – kommutativ, idempotent, assoziativ; Reihenfolge der Pakete egal (alle Datensatzarten)"""
    ctx, p = await newpage(b, name='B1')
    r = await p.evaluate("""(()=>{
      let seed = 7; const rnd = () => (seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff;
      const keys = ['titel','notiz','del','z:a','rs:x','h:ci:1','nr','b','cueId'];
      const val = () => [null,'A','B',true,false,{a:1},{a:2},[1,2],'Ü'][Math.floor(rnd()*9)];
      const mk = () => { const r = {id:'x', c: Math.floor(rnd()*10), mod:0, f:{}, t:{}}; keys.forEach(k => { if (rnd()<0.6) { r.f[k]=val(); r.t[k]=1+Math.floor(rnd()*5); } }); return r; };
      const norm = r => JSON.stringify([Object.keys(r.f).sort().map(k=>[k,r.f[k],r.t[k]]), r.c]);
      let bad = {comm:0, idem:0, assoc:0};
      for (let i = 0; i < 500; i++) { const a = mk(), b = mk(), c = mk();
        const ab = Rec.merge(a,b).rec, ba = Rec.merge(b,a).rec;
        if (norm(ab) !== norm(ba)) bad.comm++;
        if (norm(Rec.merge(ab,b).rec) !== norm(ab) || Rec.merge(ab,b).changed) bad.idem++;
        if (norm(Rec.merge(Rec.merge(a,b).rec,c).rec) !== norm(Rec.merge(a,Rec.merge(b,c).rec).rec)) bad.assoc++; }
      return bad; })()""")
    log('   ', r)
    ok(r == {'comm': 0, 'idem': 0, 'assoc': 0}, 'Rec.merge kommutativ, idempotent, assoziativ (500 Paare, mit Gleichstand der Zeitstempel)')
    # Pakete in verschiedener Reihenfolge auf zwei Geräte → gleicher Endstand (inkl. Haus, Durchgänge, Cue-Daten)
    ctxA, A = await newpage(b, name='B1-A'); ctxB, B = await newpage(b, name='B1-B')
    for P in (A, B): await P.evaluate("Settings.set({depts:['L','T','B','R']}).then(()=>Req.ensureHouse())")
    base = await pkg(A)
    await imp(B, base)
    async def edits(P, tag):
        await P.evaluate("""async tag => { const s = Repo.liveShows().find(s=>s.f.titel.startsWith('Demo: Der Haifisch'));
          await Repo.patchShow(s.id, {notiz: 'notiz '+tag, ['ci:'+tag]: {abt:'L', text:tag, ord:5, del:false}});
          const hf = Req.houseF(), hk = Object.keys(hf).find(k=>k.startsWith('ho:')); await Repo.patchHouse({[hk]: Object.assign({}, hf[hk], {notiz: tag})});
          const run = RunList.runsOf(s.id)[0] || await RunList.create(s.id); await RunList.toggle(run.id, 'ci:d1');
          const l = Cues.lists()[0] || await Cues.createList({titel:'L'}); await Repo._write({cues:[Cues.newCue(l.id, tag==='A'?'1':'2')]}); await Cues.patchList(l.id, {notiz: tag}); }""", tag)
    await edits(A, 'A'); await edits(B, 'B')
    pa, pb = await pkg(A), await pkg(B)
    ctxC, C = await newpage(b, name='B1-C', demo=False); ctxD, D = await newpage(b, name='B1-D', demo=False)
    for P in (C, D): await P.evaluate("Settings.set({depts:['L','T','B','R'], demoOnFirstStart:false})")
    await imp(C, base); await imp(C, pa); await imp(C, pb); await imp(C, pa)
    await imp(D, pb); await imp(D, base); await imp(D, pa); await imp(D, pb)
    snap = "(()=>{const pick=m=>[...m.values()].map(r=>JSON.stringify([r.id,Object.keys(r.f).sort().map(k=>[k,r.f[k],r.t[k]])])).sort(); return JSON.stringify({s:pick(Repo.shows),e:pick(Repo.entries),p:pick(Repo.photos),r:pick(Repo.runs),h:pick(Repo.house),cl:pick(Repo.cuelists),cq:pick(Repo.cues)})})()"
    sc, sd = await C.evaluate(snap), await D.evaluate(snap)
    ok(sc == sd, 'Pakete in anderer Reihenfolge und doppelt eingespielt → identischer Endstand (Show, Einträge, Haus, Durchgänge, Cues)')
    if sc != sd:
        jc, jd = json.loads(sc), json.loads(sd)
        log('   Unterschiede in:', [k for k in jc if jc[k] != jd[k]])
    for x in (ctx, ctxA, ctxB, ctxC, ctxD): await x.close()

@section('B2')
async def b2_chain(b):
    """Drei Geräte in Kette: iPad (alles) → iPhone → Pixel, „Nur Änderungen“"""
    cA, iPad = await newpage(b, name='iPad'); cB, iPhone = await newpage(b, name='iPhone'); cC, Pixel = await newpage(b, name='Pixel')
    for P in (iPad, iPhone, Pixel): await P.evaluate("Settings.set({depts:['L','T','B','R'], demoOnFirstStart:false}).then(()=>Req.ensureHouse())")
    # Erstabgleich komplett überall
    await iPad.evaluate("(async()=>{await Req.maybeTest()})()")
    full = await pkg(iPad); await imp(iPhone, full); await imp(Pixel, full)
    async def mark(P, tag):
        return await P.evaluate("""async tag => { const s = Repo.liveShows().find(s=>s.id==='test-r-show'); const out = [];
          for (const abt of ['L','T','B','R']) { const f = abt==='L'?{kreis:'9'+tag}:abt==='T'?{kanal:'9'+tag}:abt==='B'?{zug:'Pos '+tag}:{was:'Ding '+tag};
            const r = await Repo.saveDraft({id:null, showId:s.id, abt, f, photos:{A:[],E:[]}}); out.push(r.entryId); }
          const l = Cues.lists()[0] || await Cues.createList({titel:'Kette'}); const c = Cues.newCue(l.id, tag); await Repo._write({cues:[c]}); out.push(c.id);
          return out; }""", tag)
    await iPad.wait_for_timeout(20)
    ids = await mark(iPad, 'X')
    # iPad → iPhone komplett, iPhone → Pixel nur Änderungen
    t = await iPad.evaluate("(async()=>{const t0=Date.now()-1; const r=await Sync.buildPackage({type:'sync',since:0,depts:Settings.v.depts}); Sync.state.lastPackageAt=t0; return await r.blob.text()})()")
    await imp(iPhone, t)
    t = await iPhone.evaluate("(async()=>{const r=await Sync.buildPackage({type:'sync',since:Sync.state.lastPackageAt||0,depts:Settings.v.depts}); return await r.blob.text()})()")
    await imp(Pixel, t)
    have = await Pixel.evaluate("ids => ids.map(i => !!(Repo.entries.get(i) || Repo.cues.get(i)))", ids)
    ok(all(have), f'Kette iPad → iPhone (Komplett) → Pixel (Nur Änderungen): alles da ({have})')
    # Gegenrichtung mit Abteilungsfilter: iPhone nur Ton
    await iPhone.evaluate("Settings.set({depts:['T']})")
    ids2 = await mark(iPad, 'Y')
    t = await iPad.evaluate("(async()=>{const r=await Sync.buildPackage({type:'sync',since:0,depts:Settings.v.depts}); return await r.blob.text()})()")
    await imp(iPhone, t)
    t = await iPhone.evaluate("(async()=>{const r=await Sync.buildPackage({type:'sync',since:0,depts:Settings.v.depts}); return await r.blob.text()})()")
    await imp(Pixel, t)
    have = await Pixel.evaluate("ids => ids.map(i => !!(Repo.entries.get(i) || Repo.cues.get(i)))", ids2)
    st = await iPhone.evaluate("Sync.status().label")
    log(f'   Pixel über Ton-iPhone: L,T,B,R,Cue = {have}; iPhone-Status „{st}“')
    ok(have[1] and have[4], 'Über ein Ton-Gerät: Ton und Cue-Fotos kommen an')
    if not have[0]:
        bef('Hinweis', 'Ein Gerät mit anderer Abteilung reicht fremde Einträge nicht weiter (dokumentiert) – Status zeigt trotzdem „Synchron“',
            f'iPad (alles) → iPhone (nur Ton) → Pixel: Licht-, Bühnen- und Requisite-Einträge kommen auf dem Pixel nicht an ({have}). '
            f'Das iPhone speichert sie, sendet sie aber nicht weiter, und zeigt „{st}“. Dokumentiert unter „Abgleich nach Abteilungen“, '
            'im Theater aber leicht falsch zu verstehen: Wer „Synchron“ sieht, glaubt, das nächste Gerät bekommt alles. '
            'Empfehlung für die Praxis: Pakete immer direkt vom Gerät der Abteilung oder von einem Alle-Gerät verteilen.', art='dokumentiert')
    for x in (cA, cB, cC): await x.close()

@section('B3')
async def b3_same_object(b):
    """Gleichzeitige Änderung desselben Zugs / Requisite-Schritts – betrifft nur dieses Objekt"""
    cA, A = await newpage(b, name='Licht'); cB, B = await newpage(b, name='Bühne')
    await imp(B, await pkg(A))
    hai = await A.evaluate("Repo.liveShows().find(s=>s.f.titel.startsWith('Demo: Der Haifisch')).id")
    await A.evaluate(f"Repo.patchShow('{hai}', {{'z:olz1': Repo.zugValue('{hai}','olz1',{{bestueckung:'8× PC'}}), 'z:bgz1': Repo.zugValue('{hai}','bgz1',{{hoehe:'7,00 m'}})}})")
    await B.wait_for_timeout(30)
    await B.evaluate(f"Repo.patchShow('{hai}', {{'z:olz1': Repo.zugValue('{hai}','olz1',{{last:'250 kg'}}), notiz:'Bühne war hier'}})")
    await imp(A, await pkg(B)); await imp(B, await pkg(A))
    r = await A.evaluate(f"(()=>{{const f=Repo.show('{hai}').f; return [f['z:olz1'].bestueckung, f['z:olz1'].last, f['z:bgz1'].hoehe, f.notiz]}})()")
    log('   ', r)
    ok(r[2] == '7,00 m' and r[3] == 'Bühne war hier', 'Andere Züge und Felder bleiben erhalten')
    # 2.8.3: Züge werden Angabe für Angabe zusammengeführt – Bestückung (Licht) und Last (Bühne) bleiben beide
    ok(r[0] == '8× PC' and r[1] == '250 kg', '2.8.3: Gleicher Zug: Bestückung (Licht) und Last (Bühne) bleiben beide')
    if r[0] != '8× PC':
        bef('mittel', 'Gemeinsamer Zug: Licht-Bestückung geht verloren, wenn Bühne denselben Zug ändert (dokumentierte Grenze, aber stiller Verlust)',
            'Licht trägt „8× PC“ bei OLZ 1 ein, Bühne kurz danach „250 kg“ Last am selben Zug, beide ohne Abgleich dazwischen. Nach dem Abgleich steht auf beiden Geräten nur die Last – '
            'die Bestückung ist weg, ohne Hinweis. In „Grenzen (ehrlich)“ beschrieben; genau dieser Fall (Licht und Bühne am selben Zug) ist im Haus aber der Normalfall bei getrennten Geräten.',
            art='dokumentiert')
    await cA.close(); await cB.close()

@section('B4')
async def b4_clock(b):
    """Falsche Geräteuhr: A +1 Tag (und +2 Tage), B −2 Stunden"""
    cA, A = await newpage(b, name='A+1d', off=86400000 + 60000); cB, B = await newpage(b, name='B-2h', off=-7200000)
    await imp(B, await pkg(A))
    hai = await A.evaluate("Repo.liveShows().find(s=>s.f.titel.startsWith('Demo: Der Haifisch')).id")
    await A.evaluate(f"Repo.patchShow('{hai}',{{titel:'Titel von A'}})")
    await imp(B, await pkg(A))
    await B.evaluate(f"Repo.patchShow('{hai}',{{titel:'Titel von B (später)'}})")
    await imp(A, await pkg(B))
    ok(await A.evaluate(f"Repo.show('{hai}').f.titel") == 'Titel von B (später)', 'Zuletzt getippter Titel (auf B, Uhr −2 h) gewinnt nach Abgleich')
    st = await B.evaluate("[Sync.status().label, Sync.pending()]")
    log('   B nach Import von A:', st)
    # Gleichzeitig (ohne Abgleich): A ändert Notiz, eine Minute später echt ändert B Notiz
    await A.evaluate(f"Repo.patchShow('{hai}',{{notiz:'A früher'}})"); await A.wait_for_timeout(50)
    await B.evaluate(f"Repo.patchShow('{hai}',{{notiz:'B später'}})")
    await imp(A, await pkg(B)); await imp(B, await pkg(A))
    nb = await B.evaluate(f"Repo.show('{hai}').f.notiz")
    ok(nb == 'A früher', f'Gleichzeitige Änderung ohne Abgleich: Gerät mit vorgehender Uhr gewinnt ({nb}) – dokumentierte Grenze')
    stB = await B.evaluate("[Sync.status().label, Sync.pending()]")
    log('   B-Status direkt nach dem Abgleich:', stB)
    if stB[1] > 0:
        bef('mittel', 'Nach Abgleich mit einem Gerät, dessen Uhr vorgeht, zeigt der Empfänger bis zu einen Tag lang „n offen“',
            f'Sync.pending() zählt Datensätze mit mod > lastSyncAt. mod stammt von der Uhr des Absenders (+1 Tag). Direkt nach dem Einspielen zeigt Gerät B „{stB[0]}“ ({stB[1]} offen) – '
            'obwohl gerade abgeglichen. Im Saal wirkt das wie ein fehlgeschlagener Abgleich; wer daraufhin erneut sendet, ändert nichts. Bleibt, bis die echte Zeit den Zeitstempel einholt.')
    # Clock.observe ignoriert > 24 h Zukunft
    cC, C = await newpage(b, name='C+2d', off=2 * 86400000)
    await C.evaluate(f"(async()=>{{}})()")
    await imp(C, await pkg(A))
    await C.evaluate(f"Repo.patchShow('{hai}',{{notiz:'C +2 Tage'}})")
    await imp(B, await pkg(C))
    r = await B.evaluate(f"[Clock.last > Date.now() + 864e5, Repo.show('{hai}').f.notiz]")
    log('   Clock.observe bei +2 Tagen:', r)
    await B.evaluate(f"Repo.patchShow('{hai}',{{notiz:'B danach'}})")
    ok(await B.evaluate(f"Repo.show('{hai}').f.notiz") == 'B danach', 'Eigene Änderung nach Empfang eines Zukunftsstempels gilt trotzdem (Rec.patch: t+1)')
    for x in (cA, cB, cC): await x.close()

@section('B5')
async def b5_formats(b):
    """Paketformate 2/3/4 je Kombination; Gerät ohne Requisite übernimmt keine Requisite, aber Cue-Fotos"""
    c, p = await newpage(b, name='B5')
    await p.evaluate("Settings.set({depts:['L','T','B','R']}).then(()=>Req.ensureHouse())")
    r = await p.evaluate("""(async()=>{
      const fv = async o => (await Sync.buildPackage(o)).formatVersion; const hai = Repo.liveShows().find(s=>s.f.titel.startsWith('Demo: Der Haifisch')).id;
      const res = {};
      res.nurLicht = await fv({type:'sync',since:0,depts:['L']});          // Haifisch + Haus? depts L → kein Haus
      res.mitHaus = await fv({type:'sync',since:0,depts:['L','R']});
      const l = await Cues.createList({titel:'F'}); await Repo._write({cues:[Cues.newCue(l.id,'1')]});
      res.licht_cue = await fv({type:'sync',since:0,depts:['L']});
      res.backupShow = await fv({type:'backup',showIds:[hai]});
      const t = await Req.testShow(); res.backupReq = await fv({type:'backup',showIds:[t.id]});
      res.alles = await fv({type:'sync',since:0,depts:null});
      await Cues.purgeList(l.id); res.req_ohne_cue = await fv({type:'sync',since:Date.now()+5,depts:['R']});
      return res; })()""")
    log('   ', r)
    ok(r['nurLicht'] == 2 and r['mitHaus'] == 3 and r['licht_cue'] == 4 and r['backupShow'] == 2 and r['backupReq'] == 3 and r['alles'] == 4,
       'Format 2 ohne Requisite/Cue, 3 mit Requisite, 4 mit Cue-Fotos; Backup einer Veranstaltung richtig')
    if r['req_ohne_cue'] == 4:
        bef('niedrig', 'Endgültig gelöschte Cue-Liste macht jedes Paket zu Format 4',
            'Der Tombstone einer gelöschten Cue-Liste bleibt für immer und geht in jedes Komplett-Paket – damit ist jedes Paket Format 4 und für 2.7.0 unlesbar, '
            'auch wenn gar keine Cue-Fotos mehr existieren.')
    text = await pkg(p, depts="['L','T','B','R']")
    c2, p2 = await newpage(b, name='B5-ohneR')
    await p2.evaluate("Settings.set({depts:['L'], demoOnFirstStart:false})")
    await imp(p2, text)
    r2 = await p2.evaluate("[[...Repo.entries.values()].filter(e=>abtOf(e)==='R').length, Repo.house.size, Repo.cuelists.size, Repo.shows.has('test-r-show')]")
    ok(r2[0] == 0 and r2[1] == 0 and r2[3], f'Gerät ohne Requisite: keine Gegenstände/Haus-Daten, Veranstaltung schon ({r2})')
    await c.close(); await c2.close()

@section('B6')
async def b6_crafted(b):
    """Präparierte und kaputte Pakete"""
    c, p = await newpage(b, name='B6')
    await p.evaluate("Settings.set({depts:['L','T','B','R']})")
    X = '<img src=x onerror="window.__xss++">'
    pkgs = {
      'kaputt': '{"format":"lichtdoku", "shows": [',
      'leer': '',
      'abgeschnitten': None,
      'praepariert': json.dumps({'format': 'lichtdoku', 'type': 'sync', 'formatVersion': 4, 'shows': [
          {'id': 'ok-show', 'c': 1, 'mod': 1, 'f': {'titel': X, 'spielstaette': X, 'notiz': X, 'einrichtung': X, 'abteilungen': ['L', 'T', 'B', 'R'], 'del': False,
                                               'ci:' + '"><svg onload=window.__xss++>': {'abt': 'L', 'text': X, 'ord': 1}, 'z:a"b': {'name': X, 'typ': 'buehne'},
                                               'bl:x': {'abschnitt': 'pause', 'text': X}, 'rp:p1': {'rolle': X, 'darsteller': X}, 'ro:o1': {'name': X, 'notiz': X},
                                               'ra:a1': {'typ': 'teil', 'name': X, 'notiz': X}, 'rs:s1': {'abschnitt': 'ra:a1', 'text': X},
                                               'rv:ra:a1': ['rs:s1', 'g:"><b>', 5], 'z:str': 'kein Objekt', 'ci:null': None, 'abteilungen_kaputt': 'L'},
           't': {'titel': 1, 'spielstaette': 1, 'notiz': 1, 'einrichtung': 1, 'abteilungen': 1, 'del': 1}},
          {'id': 'bad id"<>', 'c': 1, 'mod': 1, 'f': {'titel': 'x'}, 't': {'titel': 1}},
          {'id': 'proto', 'c': 1, 'mod': 1, 'f': {'titel': 'p', 'x': {'__proto__': {'polluted': 1}}}, 't': {'titel': 1, 'x': 1}},
          {'id': 'nan', 'c': 1, 'mod': 1, 'f': {'titel': 'n'}, 't': {'titel': 'NaN'}},
          {'id': 'neg', 'c': 1, 'mod': 1, 'f': {'titel': 'n'}, 't': {'titel': -5}},
          {'id': 'huge', 'c': 1, 'mod': 1, 'f': {'titel': 'h'}, 't': {'titel': 1e308}},
      ], 'entries': [
          {'id': 'e-x', 'showId': 'ok-show', 'c': 1, 'mod': 1, 'f': {'abt': 'L', 'kreis': X, 'bemerkung': X, 'filter': X, 'warnung': X, 'sub': X, 'del': False}, 't': {'abt': 1, 'kreis': 1, 'bemerkung': 1, 'filter': 1, 'warnung': 1, 'sub': 1, 'del': 1}},
          {'id': 'e-r', 'showId': 'ok-show', 'c': 1, 'mod': 1, 'f': {'abt': 'R', 'was': X, 'zustand': 5, 'art': 'defekt', 'personIds': 'rp:p1', 'abschnitte': 'ra:a1', 'del': False}, 't': {'abt': 1, 'was': 1, 'zustand': 1, 'art': 1, 'personIds': 1, 'abschnitte': 1, 'del': 1}},
          {'id': 'e-t', 'showId': 'ok-show', 'c': 1, 'mod': 1, 'f': {'abt': 'T', 'kanal': {'a': 1}, 'phantom': 'ja', 'del': False}, 't': {'abt': 1, 'kanal': 1, 'phantom': 1, 'del': 1}},
      ], 'photos': [{'id': 'ph1', 'showId': 'ok-show', 'b': 'blob1', 'w': 1, 'h': 1, 'c': 1, 'mod': 1, 'f': {'entryId': 'e-x', 'kat': 'A', 'ord': 0, 'del': False}, 't': {'entryId': 1, 'kat': 1, 'ord': 1, 'del': 1}}],
      'cuelists': [{'id': 'cl1', 'c': 1, 'mod': 1, 'f': {'titel': X, 'del': False}, 't': {'titel': 1, 'del': 1}}],
      'cues': [{'id': 'cq1', 'listId': 'cl1', 'c': 1, 'mod': 1, 'f': {'nr': X, 'name': X, 'notiz': X, 'del': False}, 't': {'nr': 1, 'name': 1, 'notiz': 1, 'del': 1}}],
      'cueimgs': [{'id': 'cb1', 'listId': 'cl1', 'c': 1, 'mod': 1, 'f': {'cueId': 'cq1', 'b': 'blob1', 'ord': 0, 'hinweis': X, 'notiz': X, 'del': False}, 't': {'cueId': 1, 'b': 1, 'ord': 1, 'hinweis': 1, 'notiz': 1, 'del': 1}}],
      'house': [{'id': 'requisite', 'c': 1, 'mod': 1, 'f': {'ho:h1': {'name': X}, 'hg:g1': {'was': X}}, 't': {'ho:h1': 1, 'hg:g1': 1}}],
      'blobs': [{'id': 'blob1', 'full': base64.b64encode(b'GIF89a not a jpeg').decode()}, {'id': 'bad"id', 'full': 'AAAA'}, {'id': 'blob2', 'full': '###kein base64###'}]})
    }
    pkgs['abgeschnitten'] = pkgs['praepariert'][:len(pkgs['praepariert']) // 2]
    res = {}
    for k, t in pkgs.items():
        res[k] = await imp(p, t)
        res[k] = res[k].get('err') or {x: res[k].get(x) for x in ('neu', 'geaendert', 'ungueltig', 'bilder')}
    log('   ', json.dumps(res, ensure_ascii=False)[:600])
    ok(all(isinstance(res[k], str) for k in ('kaputt', 'leer', 'abgeschnitten')), 'Kaputtes/leeres/abgeschnittenes Paket: klare Meldung statt Absturz')
    ok(isinstance(res['praepariert'], dict) and res['praepariert']['ungueltig'] >= 5, f'Präpariert: ungültige Datensätze übersprungen – ID mit Sonderzeichen, Zeitstempel NaN/negativ ({res["praepariert"]}; 1e308 wird angenommen, siehe B10)')
    ok(await p.evaluate("({}).polluted === undefined && Object.prototype.polluted === undefined"), 'Keine Prototype-Pollution')
    # alle Ansichten öffnen
    views = ["location.hash='#/'", "location.hash='#/show/ok-show'", "App.state.abt='L';App.render()", "App.state.abt='T';App.render()",
             "App.state.abt='R';App.render()", "Settings.set({reqView:'ablauf'}).then(()=>App.render())", "App.state.reqSafe=true;App.render()",
             "App.state.reqSafe=false;App.state.abt='all';App.state.edit=true;App.render()", "Settings.set({view:'big'}).then(()=>App.render())",
             "Settings.set({view:'grid'}).then(()=>App.render())", "App.openDetailSheet('e-x')", "history.back()", "Editor.open({showId:'ok-show',entryId:'e-x'})", "history.back()",
             "Editor.open({showId:'ok-show',entryId:'e-r'})", "history.back()", "RunList.open('ok-show')", "history.back()", "SetupView.editP('ok-show')", "history.back()",
             "Req.editPersons('ok-show')", "history.back()", "Req.editOrts('ok-show')", "history.back()", "Req.editHouse('ok-show')", "history.back()",
             "location.hash='#/cues'", "location.hash='#/cue/cl1'", "CueView.editCue('cq1')", "history.back()", "CueView.openLb('cl1','cb1')", "history.back()", "location.hash='#/show/ok-show'"]
    errs0 = len([e for e in ERRS if e[0] == CUR[0]]); vfail = []
    for v in views:
        try:
            await ev(p, v); await p.wait_for_timeout(250)
        except Exception as ex:
            log('    Ansicht-Fehler:', v, str(ex)[:120]); vfail.append((v, str(ex).split('\n')[0][:120]))
    for d in (['L'], ['R'], None):
        try:
            await p.evaluate(f"Pdf.build('ok-show',{{kat:'all',depts:{json.dumps(d) if d else 'App.visibleDepts(\"ok-show\")'},cover:true,compact:false}})")
        except Exception as ex:
            log('    PDF-Fehler:', d, str(ex)[:160])
            bef('niedrig', f'PDF bricht bei präpariertem Paket ab ({d})', str(ex)[:200])
    x = await p.evaluate('window.__xss')
    ok(x == 0, f'Kein Skript ausgeführt (XSS-Zähler {x})')
    ok(not vfail, f'Alle Ansichten mit präpariertem Paket ohne Absturz ({vfail[:2]})')
    if vfail:
        bef('niedrig', 'Präpariertes Paket mit falschem Feldtyp bringt die Requisite-Ansicht zum Absturz',
            f'Ein Gegenstand mit zustand = 5 (Zahl statt Liste) wird angenommen (Rec.valid prüft keine Feldtypen); beim Anzeigen wirft App.render: {vfail[0][1]} – „Einrichten“ bleibt leer/kaputt. '
            'Nur über manipulierte oder sehr fremde Pakete erreichbar.')
    errs = [e for e in ERRS if e[0] == CUR[0]][errs0:]
    if errs:
        bef('niedrig', 'Präpariertes Paket mit falschen Feldtypen bringt Ansichten zum Absturz',
            f'Rec.valid prüft keine Feldtypen. Ein Requisite-Gegenstand mit zustand = 5 (Zahl statt Liste) o. ä. führt zu Seitenfehlern: {errs[0][2][:160]} '
            f'({len(errs)} Fehler). Betroffen ist v. a. die Requisite-Ansicht „Einrichten“ (eRow: [...(f.zustand||[])]); die Liste bleibt leer. '
            'Nur über manipulierte oder sehr fremde Pakete erreichbar – Abstürze statt Überspringen.')
    await c.close()

@section('B7')
async def b7_bigpkg(b):
    """Großes Paket: 300 Fotos à ~300 KB"""
    c, p = await newpage(b, name='B7', demo=False)
    r = await p.evaluate("""(async()=>{
      const cv = document.createElement('canvas'); cv.width = cv.height = 1000; const g = cv.getContext('2d'); const im = g.createImageData(1000,1000);
      for (let i=0;i<im.data.length;i++) im.data[i] = (i*2654435761>>>24)&255; g.putImageData(im,0,0);
      const full = await new Promise(r=>cv.toBlob(async b=>r(new Uint8Array(await b.arrayBuffer())),'image/jpeg',0.55));
      const b64 = Utils.bufToB64(full.buffer); const sh = Rec.create({id:'big-show'},{titel:'Groß',abteilungen:['L'],del:false});
      const es=[], ps=[], parts=[]; for (let i=0;i<300;i++){ const e=Rec.create({showId:'big-show'},{abt:'L',kreis:String(i+1),del:false}); es.push(e);
        ps.push(Rec.create({showId:'big-show',b:'bb'+i,w:1000,h:1000},{entryId:e.id,kat:'A',ord:0,label:'',del:false})); parts.push(JSON.stringify({id:'bb'+i,full:b64,thumb:null})); }
      const head = JSON.stringify({format:'lichtdoku',type:'sync',formatVersion:2,shows:[sh],entries:es,photos:ps,blobs:[]});
      window.__big = new File([head.slice(0,-2), parts.join(','), ']}'], 'gross.json'); return [full.length, window.__big.size]; })()""")
    log(f'   Foto {r[0]//1024} KB, Paket {r[1]//1048576} MB')
    t0 = time.time()
    st = await p.evaluate("(async()=>{const prog=[]; const r=await Sync.importPackage(window.__big,(i,n)=>prog.push(i)); return [r.bilder,r.missing,r.ungueltig,prog.length,performance.memory?Math.round(performance.memory.usedJSHeapSize/1048576):-1]})()")
    dt = time.time() - t0
    log(f'   Import: {st}, {dt:.1f} s')
    ok(st[0] == 300 and st[1] == 0 and st[3] >= 20, f'300 Fotos eingespielt, Fortschritt in {st[3]} Schritten, {dt:.0f} s')
    await reload(p)
    ok(await p.evaluate("Repo.entriesOf('big-show').length===300"), 'Nach Neuladen alle 300 Einträge')
    bef('Hinweis', 'Großes Sync-Paket wird vollständig als ein JSON-Text in den Speicher gelesen',
        f'Sync.importPackage liest die Datei mit file.text() und JSON.parse() auf einmal (Paket {r[1]//1048576} MB, JS-Heap danach ~{st[4]} MB). '
        'Bilder werden danach portionsweise geschrieben – der Spitzenbedarf entsteht aber schon beim Einlesen (Text + Objektbaum ≈ 3× Dateigröße). '
        'Im Chromium-Test unauffällig; auf iPad/iPhone mit Safari bei Paketen > 300 MB Abbruch möglich.', art='Verdacht – auf Gerät prüfen')
    await c.close()

@section('B8')
async def b8_live(b):
    """Live-Abgleich: Änderungen während des Erstabgleichs, Abbruch mitten im Bildtransfer, ältere Gegenstelle"""
    cA, A = await newpage(b, name='Live-A'); cB, B = await newpage(b, name='Live-B', demo=False)
    await B.evaluate("Settings.set({demoOnFirstStart:false})")
    await A.evaluate(JS_MKPHOTO.replace('async (n, px) =>', 'window.__mk = async (n, px) =>') + "; 1")
    await A.evaluate("""(async()=>{const s=await Repo.createShow('Live viel',['L']); for(let i=0;i<40;i++){ const ph=(await __mk(1,600))[0];
       await Repo.saveDraft({id:null,showId:s.id,abt:'L',f:{kreis:String(500+i)},photos:{A:[{photoId:null,b:ph.b,w:600,h:600,full:ph.full,thumb:ph.thumb}],E:[]}}); } })()""")
    async def connect():
        code = await A.evaluate("(async()=>{window._s&&window._s.close(); window._s=new PeerSession(); return await window._s.createOffer()})()")
        ans = await B.evaluate("async c=>{window._s&&window._s.close(); window._s=new PeerSession(); return await window._s.acceptOffer(await PeerAdapter.decodeSignal(c))}", code)
        await A.evaluate("async a=>{await window._s.acceptAnswer(await PeerAdapter.decodeSignal(a))}", ans)
    await connect()
    t_c = time.time()
    try:
        await B.wait_for_function("window._s && window._s.gotMeta", timeout=45000)
    except Exception:
        ev_a = await A.evaluate("window._s ? window._s.events.join(' | ') : '-'"); ev_b = await B.evaluate("window._s ? window._s.events.join(' | ') : '-'")
        log('   Verbindungsaufbau hängt. A:', ev_a[:600]); log('   B:', ev_b[:600])
        bef('mittel', 'Live-Abgleich: Erstverbindung kommt gelegentlich nicht zustande (Test-Umgebung)',
            f'In einem von mehreren Läufen kam nach 45 s keine Metadaten-Nachricht an. Ablauf A: {ev_a[:300]} · B: {ev_b[:300]}', art='Verdacht – auf Gerät prüfen')
        raise
    log(f'   Erstabgleich: Metadaten nach {time.time() - t_c:.1f} s')
    # während des Bildtransfers auf beiden Seiten speichern, dann hart trennen
    await A.evaluate("Repo.saveDraft({id:null,showId:Repo.liveShows().find(s=>s.f.titel==='Live viel').id,abt:'L',f:{kreis:'A-waehrend'},photos:{A:[],E:[]}})")
    await B.evaluate("Repo.saveDraft({id:null,showId:Repo.liveShows().find(s=>s.f.titel==='Live viel').id,abt:'L',f:{kreis:'B-waehrend'},photos:{A:[],E:[]}})")
    await B.wait_for_timeout(150)
    miss1 = await B.evaluate("(async()=>(await Repo.missingBlobs()).length)()")
    await A.evaluate("window._s.close()"); await B.wait_for_timeout(500)
    log(f'   Nach Abbruch fehlen auf B {miss1} Bilder')
    await reload(B)
    miss2 = await B.evaluate("(async()=>(await Repo.missingBlobs()).length)()")
    await connect()
    try:
        await B.wait_for_function("window._s && window._s.initialDone", timeout=30000)
    except Exception: pass
    await A.wait_for_timeout(1000)
    r = await B.evaluate("(async()=>[(await Repo.missingBlobs()).length, Repo.entriesOf(Repo.liveShows().find(s=>s.f.titel==='Live viel').id).length, Repo.entriesOf(Repo.liveShows().find(s=>s.f.titel==='Live viel').id).some(e=>e.f.kreis==='A-waehrend')])()")
    ra = await A.evaluate("Repo.entriesOf(Repo.liveShows().find(s=>s.f.titel==='Live viel').id).some(e=>e.f.kreis==='B-waehrend')")
    log(f'   Vor Neuverbindung fehlten {miss2}; danach {r}, A hat B-Eintrag: {ra}')
    ok(r[0] == 0 and r[1] == 42 and r[2] and ra, 'Neu verbinden: alle Bilder nachgeliefert, Änderungen beider Seiten da')
    # Gegenstelle älterer Version: hello ohne d und ohne c
    sent = await A.evaluate("""(async()=>{ const s = new PeerSession(); const out=[]; s.send = async m => out.push(m); s.open=false;
       const l = await Cues.createList({titel:'nicht für Alte'}); await Repo._write({cues:[Cues.newCue(l.id,'1')]});
       await s._handle({t:'hello', n:'Altgerät', id:'old', v:'2.6.5'}); const m = out.find(x=>x.t==='meta'); s.unsub&&s.unsub(); s.pc.close();
       return [s.depts, m.cuelists.length, m.cues.length, m.entries.every(e=>abtOf(e)==='L')]; })()""")
    ok(sent[0] == ['L'] and sent[1] == 0 and sent[2] == 0 and sent[3], f'Ältere Gegenstelle (ohne d, ohne c): nur Licht, keine Cue-Daten ({sent})')
    await cA.close(); await cB.close()

@section('B9')
async def b9_qr(b):
    """QR: Versionen 1–40 × L/M, gedreht, verrauscht, teilverdeckt; sehr lange Signal-Codes"""
    c, p = await newpage(b, name='B9', demo=False)
    r = await p.evaluate("""(async()=>{
      const cap = {L:[0,17,32,53,78,106,134,154,192,230,271,321,367,425,458,520,586,644,718,792,858,929,1003,1091,1171,1273,1367,1465,1528,1628,1732,1840,1952,2068,2188,2303,2431,2563,2699,2809,2953],
                   M:[0,14,26,42,62,84,106,122,152,180,213,251,287,331,362,412,450,504,560,624,666,711,779,857,911,997,1059,1125,1190,1264,1370,1452,1538,1628,1722,1809,1911,1989,2099,2213,2331]};
      const res = {wrongVer:[], fail:[]};
      const render = (q, scale, ang, noise, occl) => { const quiet=4, n=q.size+2*quiet, S=n*scale; const big=Math.ceil(S*1.5);
        const cv=document.createElement('canvas'); cv.width=cv.height=big; const g=cv.getContext('2d'); g.fillStyle='#fff'; g.fillRect(0,0,big,big);
        g.translate(big/2,big/2); g.rotate(ang*Math.PI/180); g.translate(-S/2,-S/2); g.fillStyle='#000';
        for(let y=0;y<q.size;y++)for(let x=0;x<q.size;x++) if(q.m[y*q.size+x]) g.fillRect((x+quiet)*scale,(y+quiet)*scale,scale,scale);
        g.setTransform(1,0,0,1,0,0);
        if (occl) { g.fillStyle='#777'; g.fillRect(big/2+S*0.05, big/2+S*0.05, S*0.08, S*0.08); }
        const im=g.getImageData(0,0,big,big); if (noise) for(let i=0;i<im.data.length;i+=4){ const v=(Math.random()-0.5)*noise; im.data[i]+=v; im.data[i+1]+=v; im.data[i+2]+=v; }
        return im; };
      for (const ecl of ['L','M']) for (let v=1; v<=40; v++) {
        const len = cap[ecl][v] - 3; const text = 'LD1z:' + 'x'.repeat(Math.max(0,len-5));
        let q; try { q = QR.encode(text, ecl); } catch(e) { res.fail.push(ecl+v+':enc'); continue; }
        if (q.ver !== v) res.wrongVer.push(ecl+v+'→'+q.ver);
        const scale = v > 25 ? 3 : 4;
        const t = QR.decodeImage(render(q, scale, 0, 0, false)); if (t !== text) res.fail.push(ecl+v+':gerade');
      }
      // gedreht / verrauscht / teilverdeckt für eine Auswahl
      res.rot = {};
      for (const v of [2,5,10,15,20]) for (const ang of [0,10,20,30,40]) { const text='LD1z:'+'a'.repeat(cap.M[v]-8); const q=QR.encode(text,'M');
        const t=QR.decodeImage(render(q, 6, ang, 60, ang===20)); res.rot['v'+v+'@'+ang] = t===text; }
      return res; })()""")
    log('   falsche Version:', r['wrongVer'][:10], 'Fehler:', r['fail'][:20])
    ok(not r['wrongVer'] and not r['fail'], f'Generator→Decoder alle 80 Kombinationen (gerade) ok ({len(r["fail"])} Fehler)')
    bad = [k for k, v in r['rot'].items() if not v]
    log('   gedreht/verrauscht nicht gelesen:', bad)
    ok(len(bad) <= 3, f'Gedreht 0–40°, verrauscht, teilverdeckt: {25 - len(bad)}/25 gelesen')
    if bad:
        bef('niedrig' if len(bad) <= 5 else 'mittel', f'Eigener QR-Decoder liest {len(bad)} von 25 gedrehten/verrauschten Codes nicht',
            'Nicht gelesen: ' + ', '.join(bad) + '. Betrifft nur iPad/iPhone (kein BarcodeDetector). Im echten Kamerabild mit Unschärfe vermutlich schlechter – '
            'Ausweg „Code als Text teilen“ ist vorhanden.', art='reproduziert')
    # lange Signal-Codes: SDP mit vielen Kandidaten
    r = await p.evaluate("""(async()=>{ const cands=[]; for(let i=0;i<60;i++) cands.push(`a=candidate:${1000+i} 1 udp ${2122260223-i} 192.168.${i%4}.${10+i} ${50000+i} typ host generation 0 network-id ${i}`);
       const sdp = 'v=0\\r\\no=- 4611731400430051336 2 IN IP4 127.0.0.1\\r\\ns=-\\r\\nt=0 0\\r\\na=group:BUNDLE 0\\r\\nm=application 9 UDP/DTLS/SCTP webrtc-datachannel\\r\\nc=IN IP4 0.0.0.0\\r\\n' + cands.join('\\r\\n') +
         '\\r\\na=ice-ufrag:abcd\\r\\na=ice-pwd:abcdefghijklmnopqrstuvwx\\r\\na=fingerprint:sha-256 ' + Array.from({length:32},(_,i)=>(i*7%256).toString(16).padStart(2,'0').toUpperCase()).join(':') + '\\r\\n';
       const code = await PeerAdapter.encodeSignal({r:'o',id:Utils.uuid(),n:'Gerät',sdp}); let v=null; try { v = QR.toCanvas(code,760,'M').dataset.version; } catch(e) { v = 'zu groß: '+e.message; }
       return [code.length, v]; })()""")
    log('   Signal mit 60 Kandidaten:', r)
    ok(True, f'Signal-Code mit 60 ICE-Kandidaten: {r[0]} Zeichen → QR {r[1]}')
    await c.close()

# =====================================================================================
# C. Vorstellungs-Checkliste und Ablauf
# =====================================================================================
@section('C1')
async def c1_midnight(b):
    """Durchgang um 23:40 beginnen, nach Mitternacht weiter abhaken (Abendvorstellung)"""
    import datetime
    from zoneinfo import ZoneInfo
    target = datetime.datetime(2026, 10, 23, 23, 40, tzinfo=ZoneInfo('Europe/Berlin')).timestamp() * 1000
    off = int(target - time.time() * 1000)
    c, p = await newpage(b, name='C1', off=off)
    await p.evaluate("Settings.set({depts:['L','T','B','R']}).then(()=>Req.ensureHouse())")
    hai = await p.evaluate("Repo.liveShows().find(s=>s.f.titel.startsWith('Demo: Der Haifisch')).id")
    await p.evaluate("Req.testShow()")
    await p.evaluate(f"location.hash='#/show/{hai}'"); await p.wait_for_timeout(500)
    log('   Uhr:', await p.evaluate("new Date().toLocaleString('de-DE')"))
    await p.click('[data-box=run] [data-run=start]'); await p.wait_for_timeout(400)
    await p.click('[data-box=run] .runchk >> nth=0'); await p.wait_for_timeout(300)
    # Requisite: Einrichten 2 Haken
    await p.evaluate("location.hash='#/show/test-r-show'"); await p.wait_for_timeout(500)
    await p.evaluate("App.state.abt='R'; Settings.set({reqView:'einrichten'}).then(()=>App.render())"); await p.wait_for_timeout(300)
    await p.click('.gchk >> nth=0'); await p.wait_for_timeout(300); await p.click('.gchk >> nth=1'); await p.wait_for_timeout(300)
    # 30 Minuten weiter: 00:10
    await p.evaluate(f"__setOff({off + 30 * 60000})"); await reload(p)
    log('   Uhr:', await p.evaluate("new Date().toLocaleString('de-DE')"))
    await p.evaluate(f"location.hash='#/show/{hai}'"); await p.wait_for_timeout(500)
    box = await p.evaluate("document.querySelector('[data-box=run]').innerText")
    vorher = await p.evaluate(f"RunList.runsOf('{hai}').length")
    # im Ablauf Pausen-Schritt abhaken
    await p.evaluate("SetupView.open['abl-L']=true; App.render()"); await p.wait_for_timeout(200)
    await p.click('[data-box=abl-L] .runchk >> nth=0'); await p.wait_for_timeout(500)
    runs = await p.evaluate(f"RunList.runsOf('{hai}').map(r=>[r.f.datum,r.f.titel,Object.keys(r.f).filter(k=>k.startsWith('h:')).length])")
    log('   nach 00:00 Kasten:', box.replace('\n', ' | ')[:160]); log('   Durchgänge:', runs)
    await p.evaluate("location.hash='#/show/test-r-show'"); await p.wait_for_timeout(500)
    rq = await p.evaluate("[document.querySelector('.rvorh p')?.innerText, document.querySelectorAll('.gchk[aria-checked=true]').length]")
    await p.click('.gchk >> nth=2'); await p.wait_for_timeout(400)
    rruns = await p.evaluate("RunList.runsOf('test-r-show').map(r=>[r.f.datum,Object.keys(r.f).filter(k=>k.startsWith('h:')).length])")
    log('   Requisite nach 00:00:', rq, rruns)
    split = len(runs) > 1 or len(rruns) > 1
    ok(not split, 'Nach Mitternacht weiter im selben Durchgang')
    if split:
        bef('hoch', 'Nach Mitternacht beginnt die Checkliste neu – Haken der laufenden Vorstellung landen in einem zweiten Durchgang',
            f'Durchgang um 23:40 begonnen, um 00:10 weiter: „Vor der Vorstellung“ zeigt wieder „Vorstellung heute beginnen“ ({box.splitlines()[0][:60]}…), '
            f'Requisite „Einrichten“ zeigt {rq[1]} statt 2 Haken. Der nächste Haken im Ablauf legt still einen neuen Durchgang mit dem neuen Datum an: {runs}; Requisite: {rruns}. '
            'Ursache: „heute“ = RunList.isoDate() (Ortsdatum) – SetupView.htmlRun, ReqView.todayRun und das Abhaken im Ablauf suchen den Durchgang mit datum === heute. '
            'Bei Abendvorstellungen (Ende nach 24 Uhr, Abbau, „Nach der Vorstellung“) ist das Protokoll damit zerrissen; der Pausen-/Nachher-Teil steht im Durchgang des Folgetags.')
    # PDF-Protokoll des ersten Durchgangs zeigt die Nachher-Haken nicht
    if split:
        rid = await p.evaluate(f"RunList.runsOf('{hai}').slice(-1)[0].id")
        path = await save_pdf(p, f"Promise.resolve(Pdf.buildRun('{hai}','{rid}',['L','T','B']))", 'C1_protokoll_vorabend')
        t = pdftext(path)
        ok('Spiegelkugel' in t and re.search(r'offen', t), 'Protokoll des Vorabends führt den nach Mitternacht abgehakten Schritt als offen')
    await c.close()

@section('C2')
async def c2_two_runs(b):
    """Zwei Geräte beginnen „heute“ unabhängig voneinander (Licht-iPad, Ton-Pixel)"""
    cA, A = await newpage(b, name='iPad Licht'); cB, B = await newpage(b, name='Pixel Ton')
    await imp(B, await pkg(A))
    await A.evaluate("Settings.set({depts:['L']})"); await B.evaluate("Settings.set({depts:['T']})")
    hai = await A.evaluate("Repo.liveShows().find(s=>s.f.titel.startsWith('Demo: Der Haifisch')).id")
    for P in (A, B):
        await P.evaluate(f"location.hash='#/show/{hai}'"); await P.wait_for_timeout(400)
        await open_run(P)
        await P.click('[data-box=run] [data-run=start]'); await P.wait_for_timeout(300)
        n = await P.evaluate("document.querySelectorAll('[data-box=run] .runchk').length")
        for i in range(n): await P.click(f'[data-box=run] .runchk >> nth={i}'); await P.wait_for_timeout(120)
    await imp(B, await pkg(A, depts="['L']")); await imp(A, await pkg(B, depts="['T']"))
    cC, C = await newpage(b, name='Alle'); await C.evaluate("Settings.set({depts:['L','T','B']})")
    await imp(C, await pkg(A, depts="['L']")); await imp(C, await pkg(B, depts="['T']"))
    await C.evaluate(f"location.hash='#/show/{hai}'"); await C.wait_for_timeout(500)
    r = await C.evaluate(f"""(()=>{{const runs=RunList.runsOf('{hai}'); const items=RunList.items('{hai}',['L','T','B']).filter(i=>i.vor);
       return [runs.length, runs.map(r=>RunList.progress(r,items).done), document.querySelector('[data-box=run] .sum')?.textContent]}})()""")
    log('   Alle-Gerät:', r)
    ok(r[0] == 1, 'Ein Durchgang für heute')
    if r[0] > 1:
        bef('hoch', 'Zwei Geräte, die „Vorstellung heute beginnen“ unabhängig tippen, erzeugen zwei Durchgänge – die Anzeige zeigt nur einen',
            f'Licht-iPad und Ton-Pixel beginnen beide vor dem Abgleich (auch: Abhaken im Ablauf/Einrichten legt den Durchgang still an). Nach dem Abgleich gibt es {r[0]} Durchgänge für dasselbe Datum, '
            f'erledigt {r[1]}. „Vor der Vorstellung“ zeigt „{r[2]}“ – nur den neueren Durchgang; die Haken des anderen Geräts wirken offen. '
            'Die Testcheckliste (2.3.0) beschreibt genau diesen Ablauf („Licht-Punkte auf dem iPad, Ton-Punkte auf dem Pixel abhaken“) – er funktioniert nur, wenn ein Gerät zuerst beginnt und vor dem zweiten abgleicht. '
            'Gleiches im PDF-Protokoll: jeder Durchgang einzeln, keiner vollständig.')
    for x in (cA, cB, cC): await x.close()

@section('C3')
async def c3_requisite(b):
    """Requisite: Abschnitt mit Reihenfolge löschen, Verschieben bei paralleler Bearbeitung, Behälter-Zyklus, „Neu beginnen“"""
    cA, A = await newpage(b, name='Req-A'); cB, B = await newpage(b, name='Req-B')
    for P in (A, B): await P.evaluate("Settings.set({depts:['R']}).then(()=>Req.ensureHouse())")
    await A.evaluate("Req.testShow()"); await imp(B, await pkg(A))
    sid = 'test-r-show'
    r = await A.evaluate(f"""(async()=>{{const a=Req.abschnitte('{sid}').find(x=>x.typ==='teil'); const its=Req.sectionItems('{sid}',a).map(x=>x.tok);
      await Repo.patchShow('{sid}',{{['rv:'+a.key]: its.slice().reverse()}});
      const g=Req.entriesR('{sid}').filter(e=>Req.whenKeys(e).includes(a.key)).length;
      const f=Req.sh('{sid}'); const p={{[a.key]:Object.assign({{}},f[a.key],{{del:true}})}}; Req.steps('{sid}').filter(s=>s.abschnitt===a.key).forEach(s=>p[s.key]=Object.assign({{}},f[s.key],{{del:true}}));
      await Repo.patchShow('{sid}',p); const after=Req.entriesR('{sid}').length; let pdf='ok'; try{{await Pdf.build('{sid}',{{kat:'all',depts:['R'],cover:true}})}}catch(e){{pdf=e.message}}
      return [g, after, pdf, RunList.items('{sid}',['R']).length]}})()""")
    ok(r[1] == 51 - 0 or r[1] >= 50, f'Abschnitt mit eigener Reihenfolge gelöscht: Gegenstände bleiben ({r})')
    ok(r[2] == 'ok', 'PDF nach Löschen des Abschnitts')
    await A.evaluate(f"location.hash='#/show/{sid}'"); await A.evaluate("Settings.set({reqView:'ablauf'}).then(()=>App.render())"); await A.wait_for_timeout(400)
    # Verschieben auf A, gleichzeitig Bemerkung auf B
    e = await A.evaluate(f"Req.entriesR('{sid}').find(e=>e.f.was==='Degen').id")
    await A.evaluate(f"Req.moveItemTo('{sid}','g:{e}','ra:test-t1','ra:test-t2')")
    await B.evaluate(f"(async()=>{{const x=Repo.entry('{e}'); await Repo._write({{entries:[Rec.patch(x,{{bemerkung:'Klinge stumpf'}})]}})}})()")
    await imp(A, await pkg(B)); await imp(B, await pkg(A))
    r = await B.evaluate(f"[Repo.entry('{e}').f.bemerkung, Repo.entry('{e}').f.abschnitte]")
    ok(r[0] == 'Klinge stumpf' and 'ra:test-t2' in r[1], f'Verschieben + parallele Bemerkung: beides bleibt ({r})')
    # Behälter-Zyklus
    r = await A.evaluate(f"""(async()=>{{const es=Req.entriesR('{sid}'); const a=es.find(e=>e.f.was==='Schmuckkästchen'), b2=es.find(e=>e.f.was==='Hutschachtel');
       await Repo._write({{entries:[Rec.patch(a,{{inId:b2.id}}), Rec.patch(b2,{{inId:a.id}})]}}); Settings.v.reqView='einrichten'; App.render(); await new Promise(r=>setTimeout(r,300));
       const shown=[...document.querySelectorAll('.erow .rwas')].map(x=>x.textContent); let pdf='ok'; try{{await Pdf.build('{sid}',{{kat:'all',depts:['R'],cover:true}})}}catch(e){{pdf=e.message}}
       return [shown.filter(x=>x.includes('Schmuckkästchen')).length, shown.filter(x=>x.includes('Hutschachtel')).length, pdf, RunList.items('{sid}',['R']).filter(i=>i.entryId===a.id||i.entryId===b2.id).length]}})()""")
    ok(r[0] == 1 and r[1] == 1 and r[2] == 'ok' and r[3] >= 2, f'Behälter-Zyklus A in B, B in A: beide einmal sichtbar, PDF ok ({r})')
    # Neu beginnen mehrfach
    r = await A.evaluate(f"""(async()=>{{for(let i=0;i<3;i++){{const rr=await RunList.create('{sid}'); await RunList.toggle(rr.id, RunList.items('{sid}',['R'])[i].key);}}
       const runs=RunList.runsOf('{sid}'); const ps=[]; for(const r of runs){{ const b=Pdf.buildRun('{sid}',r.id,['R']); ps.push(b.size>1000); }} return [runs.map(r=>r.f.titel), ps]}})()""")
    log('   ', r)
    ok(len(r[0]) == 3 and all(r[1]), 'Neu beginnen dreimal: drei Durchgänge, jedes Protokoll erzeugt')
    await cA.close(); await cB.close()

# =====================================================================================
# D. Cue-Fotos
# =====================================================================================
@section('D1')
async def d1_cuenr(b):
    """Cue-Nummern, „Nächster Cue“ nach Text-Cue, addRange-Grenzen"""
    c, p = await newpage(b, name='D1')
    r = await p.evaluate("""[['1.10','1.1','007','12,50','Q7','-1','1e3',' 5 ','Ende'].map(x=>Cues.norm(x)), Cues.nextNr('Ende'), Cues.nextNr('-1'), Cues.nextNr('1e3')]""")
    log('   norm:', r)
    ok(r[0][:5] == ['1.1', '1.1', '7', '12.5', '7'], 'Normalisierung 1.10=1.1, 007=7, 12,50=12.5, Q7=7')
    lid = await p.evaluate("(async()=>{const l=await Cues.createList({titel:'Text-Cue'}); await Cues.addRange(l.id,'1','5','1'); await Repo._write({cues:[Cues.newCue(l.id,'Ende')]}); return l.id})()")
    await p.evaluate(f"App.state.edit=true; location.hash='#/cue/{lid}'"); await p.wait_for_timeout(400)
    ende = await p.evaluate(f"Cues.cueByNr('{lid}','Ende').id")
    await p.evaluate(f"void CueCam.open({{listId:'{lid}', cueId:'{ende}'}})")
    await p.wait_for_function("document.querySelector('.ccam video') && document.querySelector('.ccam video').videoWidth>0", timeout=15000)
    await p.click('.ccam [data-a=shot]')
    nx = await p.evaluate("document.querySelector('.ccam [data-nx]').textContent")
    await p.click('.ccam [data-a=next]')
    await p.wait_for_function('CueCam.pending()===0 && !CueCam.busy', timeout=20000)
    lbl = await p.evaluate("document.querySelector('.ccam [data-lbl]').textContent")
    await p.click('.ccam [data-a=close]')
    r = await p.evaluate(f"Cues.cuesOf('{lid}').map(c=>c.f.nr+':'+Cues.imgsOf(c.id).length).join(' ')")
    log(f'   nach Text-Cue „Ende“: Knopf „{nx}“, danach „{lbl}“, Fotos: {r}')
    if '1:1' in r:
        bef('mittel', '„Nächster Cue“ nach einer Text-Cue (z. B. „Ende“) springt auf Cue 1 und hängt das Foto dort an',
            f'Cue-Liste 1–5 plus „Ende“. Kamera bei „Ende“, Auslöser, dann „Nächster Cue“ (löst sofort aus): Das Foto landet als zweites Bild bei Cue 1 ({r}). '
            f'Der Knopf zeigt zwar „{nx}“, im dunklen Saal unter Zeitdruck fällt das nicht auf. Ursache: Cues.nextNr(Text) liefert „1“. '
            'Besser: nach Text-Cue auf die nächste Cue der Liste bzw. höchste Nummer + 1, oder „Nächster Cue“ ohne Auslösen.')
    # addRange
    r = await p.evaluate("""(async()=>{const l=await Cues.createList({titel:'Range'}); const a=await Cues.addRange(l.id,'40','1','1'); const b2=await Cues.addRange(l.id,'1','2','0,25');
       const c2=await Cues.addRange(l.id,'100','2000','1'); return [a,b2,c2,Cues.cuesOf(l.id).length]})()""")
    log('   addRange:', r)
    ok(r[0] == 40 and r[1] == 3, 'Rückwärts 40→1 und 0,25-Schritte (nur fehlende Nummern)')
    if r[2] == 500:
        # über die Oberfläche: was sagt die Meldung?
        lid2 = await p.evaluate("(async()=>{const l=await Cues.createList({titel:'UI-Range'}); return l.id})()")
        await p.evaluate(f"location.hash='#/cue/{lid2}'"); await p.wait_for_timeout(400)
        await p.click('[data-cact=addmany]'); await p.wait_for_timeout(300)
        await p.fill('[data-editor] [name=von]', '1'); await p.fill('[data-editor] [name=bis]', '800'); await p.click('[data-editor] [data-ok]'); await p.wait_for_timeout(1200)
        t = await p.evaluate("document.querySelector('#toasts').innerText")
        bef('niedrig', '„Mehrere Cues anlegen“ kappt still bei 500',
            f'1–800 angelegt → es entstehen nur 500 Cues, die Meldung lautet „{t.strip()[:60]}“ ohne Hinweis, dass 300 fehlen. Große Opern/Musicals haben über 500 Cues.')
    await c.close()

@section('D2')
async def d2_queue(b):
    """Warteschlange: Kamera zu mit 15 Fotos, Hintergrund, Neuladen während der Warteschlange"""
    c, p = await newpage(b, name='D2')
    lid = await p.evaluate("(async()=>{const l=await Cues.createList({titel:'Queue'}); await Cues.addRange(l.id,'1','3','1'); return l.id})()")
    await p.evaluate(f"App.state.edit=true; location.hash='#/cue/{lid}'"); await p.wait_for_timeout(400)
    await p.click('[data-cact=cam]')
    await p.wait_for_function("document.querySelector('.ccam video') && document.querySelector('.ccam video').videoWidth>0", timeout=15000)
    # Speichern künstlich verlangsamen, damit die Warteschlange voll ist
    await p.evaluate("window.__fc = Photo.fromCanvas.bind(Photo); Photo.fromCanvas = async (...a) => { await new Promise(r=>setTimeout(r,400)); return __fc(...a); }; 1")
    await p.evaluate("for(let i=0;i<15;i++) document.querySelector('.ccam [data-a=shot]').click()")
    q1 = await p.evaluate("CueCam.pending()")
    await p.evaluate("Object.defineProperty(document,'hidden',{configurable:true,get:()=>true}); document.dispatchEvent(new Event('visibilitychange'))")
    await p.wait_for_timeout(500)
    await p.evaluate("delete document.hidden; document.dispatchEvent(new Event('visibilitychange'))")
    await p.click('.ccam [data-a=close]')
    q2 = await p.evaluate("CueCam.pending()")
    saved_before = await p.evaluate(f"Cues.allImgsOf('{lid}').length")
    dialogs = []
    p.remove_listener('dialog', p.listeners('dialog')[0]) if hasattr(p, 'listeners') else None
    log(f'   Warteschlange: {q1} nach dem Auslösen, {q2} nach Hintergrund+Schließen, gespeichert {saved_before}')
    # Neuladen während der Warteschlange
    got = {'bu': False}
    def ondlg(d):
        if d.type == 'beforeunload': got['bu'] = True
        asyncio.ensure_future(d.accept())
    p.on('dialog', ondlg)
    try:
        await p.reload(timeout=8000)
    except Exception: pass
    await p.wait_for_function('window.Boot && Boot.started', timeout=30000)
    after = await p.evaluate(f"Cues.allImgsOf('{lid}').length")
    log(f'   beforeunload-Warnung: {got["bu"]}; nach Neuladen gespeichert: {after} von 15')
    ok(got['bu'], 'Neuladen während der Warteschlange: Browser fragt nach (beforeunload)')
    if after < 15:
        bef('mittel', 'Cue-Fotos in der Warteschlange gehen beim Neuladen/Beenden verloren',
            f'15 Fotos ausgelöst, Kamera geschlossen, Speichern läuft noch. Neuladen (nach Bestätigung der Rückfrage): {after} von 15 gespeichert. '
            'Die Warteschlange liegt nur im Arbeitsspeicher (Canvas). iOS beendet Apps im Hintergrund ohne beforeunload – dort gehen sie ohne Rückfrage verloren. '
            'Die App zeigt nach dem Neustart nicht an, dass Fotos fehlen.', art='reproduziert (iOS-Hintergrund: Verdacht – auf Gerät prüfen)')
    await c.close()

@section('D3')
async def d3_cue_misc(b):
    """Foto für live gelöschte Cue, PDF 0/1/200 Fotos und lange Texte, endgültig löschen auf A bei offenem B"""
    cA, A = await newpage(b, name='Cue-A'); cB, B = await newpage(b, name='Cue-B')
    await A.evaluate(JS_MKPHOTO.replace('async (n, px) =>', 'window.__mk = async (n, px) =>') + "; 1")
    lid = await A.evaluate("(async()=>{const l=await Cues.createList({titel:'PDF-Test'}); await Cues.addRange(l.id,'1','3','1'); return l.id})()")
    await imp(B, await pkg(A))
    c2 = await A.evaluate(f"Cues.cueByNr('{lid}','2').id")
    await B.evaluate(f"Cues.deleteCue('{c2}')")
    await A.evaluate(f"(async()=>{{const ph=(await __mk(1,300))[0]; await Repo._write({{cueimgs:[Rec.create({{listId:'{lid}'}},{{cueId:'{c2}',ord:0,b:ph.b,o:'',w:300,h:300,notiz:'',hinweis:'',del:false}})],fulls:[{{id:ph.b,d:ph.full}}],thumbs:[{{id:ph.b,d:ph.thumb}}]}})}})()")
    await imp(A, await pkg(B)); await imp(B, await pkg(A))
    o = await B.evaluate(f"[Cues.orphansOf('{lid}').length, (location.hash='#/cue/{lid}', 1)]")
    await B.wait_for_timeout(500)
    ok(o[0] == 1 and await B.evaluate("document.body.innerText.includes('Fotos ohne Cue')"), 'Foto für live gelöschte Cue erscheint unter „Fotos ohne Cue“')
    # PDF-Varianten
    long = 'Sehr lange Notiz. ' * 120
    sizes = await A.evaluate(f"""(async()=>{{const res={{}};
      const l0=await Cues.createList({{titel:'Null'}}); await Cues.addRange(l0.id,'1','3','1'); res.null=(await Pdf.buildCues(l0.id,{{cover:true}})).size>0 && Pdf.lastPages;
      const l1=await Cues.createList({{titel:'Lang'}}); const c=Cues.newCue(l1.id,'1',{{name:'Name '.repeat(40), notiz:{json.dumps(long)}}}); const ph=(await __mk(1,300))[0];
      await Repo._write({{cues:[c], cueimgs:[Rec.create({{listId:l1.id}},{{cueId:c.id,ord:0,b:ph.b,o:'',w:300,h:300,notiz:{json.dumps(long)},hinweis:{json.dumps(long[:900])},del:false}})], fulls:[{{id:ph.b,d:ph.full}}], thumbs:[{{id:ph.b,d:ph.thumb}}]}});
      window.__l1=l1.id; return res}})()""")
    path = await save_pdf(A, "Pdf.buildCues(window.__l1,{cover:true})", 'D3_cue_lang')
    t = pdftext(path, layout=False)
    ok(qpdf_ok(path), 'Cue-PDF mit langen Texten: qpdf ok')
    n_in = t.count('Sehr lange Notiz')
    log(f'   Cue-PDF: „Sehr lange Notiz“ {n_in}× im PDF (eingegeben 2 × 120 + Hinweis)')
    if n_in < 200 and '…' not in t:   # 2.8.3: Gekürztes endet sichtbar mit „…“
        bef('niedrig', 'Cue-PDF kürzt lange Notizen und Hinweise ohne Kennzeichnung',
            f'Notiz zum Bild (2160 Zeichen) und Notiz zur Cue werden nach 8 bzw. 5 Zeilen abgeschnitten, der Hinweis nach 5 Zeilen – ohne „…“ oder „(gekürzt)“. '
            f'Im PDF stehen {n_in} von ~250 Wiederholungen. Wer das PDF als Ablage nutzt, merkt nicht, dass Text fehlt (Doku-PDF markiert „… (gekürzt)“).')
    # 200 Fotos
    r = await A.evaluate("""(async()=>{const l=await Cues.createList({titel:'Zweihundert'}); const ph=await __mk(20,300); const cues=[], ims=[], fulls=[], thumbs=[];
      ph.forEach(x=>{fulls.push({id:x.b,d:x.full}); thumbs.push({id:x.b,d:x.thumb});});
      for(let i=0;i<100;i++){const c=Cues.newCue(l.id,String(i+1)); cues.push(c); for(let k=0;k<2;k++){const x=ph[(i*2+k)%20]; ims.push(Rec.create({listId:l.id},{cueId:c.id,ord:k,b:x.b,o:'',w:300,h:300,notiz:'',hinweis:'',del:false}));}}
      const miss=Rec.create({listId:l.id},{cueId:cues[5].id,ord:5,b:'fehlt-ganz',o:'',w:300,h:300,notiz:'Bild fehlt',hinweis:'',del:false}); ims.push(miss);
      await Repo._write({cues,cueimgs:ims,fulls,thumbs}); const t0=performance.now(); const b=await Pdf.buildCues(l.id,{cover:true}); window.__l2=l.id; return [Pdf.lastPages, Math.round(performance.now()-t0), b.size]})()""")
    log('   200 Fotos + 1 fehlendes:', r)
    path = await save_pdf(A, "Pdf.buildCues(window.__l2,{cover:true})", 'D3_cue_200')
    ok(r[0] >= 202 and qpdf_ok(path), f'Cue-PDF mit 201 Fotos (eins ohne Bilddaten): {r[0]} Seiten, {r[1]} ms')
    # endgültig löschen auf A, B ist im Bearbeitungsmodus in der Liste
    await B.evaluate(f"App.state.edit=true; location.hash='#/cue/{lid}'"); await B.wait_for_timeout(300)
    c1 = await B.evaluate(f"Cues.cueByNr('{lid}','1').id")
    await B.evaluate(f"CueView.editCue('{c1}')"); await B.wait_for_timeout(300)
    st0 = await B.evaluate("!!document.querySelector('#cq-name')")
    await A.evaluate(f"Cues.purgeList('{lid}')")
    await imp(B, await pkg(A)); await B.wait_for_timeout(600)
    st = await B.evaluate("[location.hash, !!document.querySelector('[data-editor]')]")
    log('   B: Blatt vor dem Import offen:', st0, '· nach dem Import:', st)
    if st[1]:
        await B.fill('#cq-name', 'nach dem Löschen'); await B.click('[data-editor] .sheet-h [data-x=save]'); await B.wait_for_timeout(500)
    else:
        ok(st0, 'Blatt „Cue bearbeiten“ war offen und schließt sich nach dem Abgleich von selbst')
    r2 = await B.evaluate(f"[Cues.list('{lid}'), Cues.lists().length, Repo.cues.get('{c1}').f.del]")
    log('   B nach endgültigem Löschen auf A:', st, r2)
    ok(r2[0] is None and r2[2] is True, 'B: Liste weg; Speichern im noch offenen Blatt holt nichts zurück')
    await cA.close(); await cB.close()

# =====================================================================================
# E. Fotos und Kamera
# =====================================================================================
@section('E1')
async def e1_gallery(b):
    """Galerie-Import: sehr große Fotos, kaputt, HEIF, PNG transparent, EXIF-Drehung, 1×1, 20000×100"""
    c, p = await newpage(b, name='E1')
    from PIL import Image
    files = []
    def jpg(w, h, q=85, exif_orient=None, color=(40, 120, 90)):
        im = Image.new('RGB', (w, h), color)
        for y in range(0, h, max(1, h // 8)):
            for x in range(0, min(w, 400)): im.putpixel((x, y), (255, 255, 255))
        buf = io.BytesIO()
        if exif_orient:
            ex = Image.Exif(); ex[0x0112] = exif_orient; im.save(buf, 'JPEG', quality=q, exif=ex)
        else: im.save(buf, 'JPEG', quality=q)
        return buf.getvalue()
    t0 = time.time()
    big = [jpg(8660, 5773, 70) for _ in range(3)] + [jpg(12250, 8166, 60)]   # 3× 50 MP, 1× 100 MP
    log(f'   Testbilder erzeugt ({time.time() - t0:.0f} s): ' + ', '.join(f'{len(x)//1048576} MB' for x in big))
    png = io.BytesIO(); Image.new('RGBA', (400, 400), (255, 0, 0, 0)).save(png, 'PNG')
    rot = jpg(600, 300, exif_orient=6, color=(200, 30, 30))
    files = [('g50a.jpg', 'image/jpeg', big[0]), ('g50b.jpg', 'image/jpeg', big[1]), ('g50c.jpg', 'image/jpeg', big[2]), ('g100.jpg', 'image/jpeg', big[3]),
             ('kaputt.jpg', 'image/jpeg', b'\xff\xd8\xff\xe0' + os.urandom(2000)), ('IMG_1.heic', 'image/heic', bytes([0,0,0,24]) + b'ftypheic' + bytes(8)),
             ('ohne_endung', '', bytes([0,0,0,24]) + b'ftypmif1' + bytes(8)), ('frei.png', 'image/png', png.getvalue()), ('gedreht.jpg', 'image/jpeg', rot),
             ('eins.jpg', 'image/jpeg', jpg(1, 1)), ('lang.jpg', 'image/jpeg', jpg(20000, 100))]
    hai = await p.evaluate("Repo.liveShows().find(s=>s.f.titel.startsWith('Demo: Der Haifisch')).id")
    await p.evaluate(f"App.state.edit=true; location.hash='#/show/{hai}'"); await p.wait_for_timeout(400)
    await p.evaluate(f"Editor.open({{showId:'{hai}', abt:'L'}})"); await p.wait_for_timeout(300)
    await p.fill('[data-editor] [name=kreis]', '999')
    await p.click('[data-editor] .pk[data-k=A] [data-act=cam]'); await p.wait_for_timeout(700)
    t0 = time.time()
    await p.set_input_files('.cam input[type=file][multiple]', files=[{'name': n, 'mimeType': m, 'buffer': d} for n, m, d in files])
    dialogs = 0
    for i in range(240):
        await p.wait_for_timeout(500)
        if await p.evaluate("!!document.querySelector('.dialog')"):
            dialogs += 1; await p.click('.dialog .btn'); await p.wait_for_timeout(200)
        if await p.evaluate("!!document.querySelector('.cam')"):
            await p.click('.cam [data-a=done]'); await p.wait_for_timeout(200)
        busy = await p.evaluate("document.querySelectorAll('[data-editor] .slot .busy').length")
        if busy == 0 and i > 2: break
    dt = time.time() - t0
    r = await p.evaluate("[document.querySelectorAll('[data-editor] .pgrid[data-k=A] .slot:not(.add)').length, document.querySelectorAll('[data-editor] .slot .busy').length, document.querySelector('[data-editor] .savebtn').disabled, Sync.state.log.filter(l=>l.msg.startsWith('Foto nicht übernommen')).map(l=>l.msg.split(':')[1].split('(')[0].trim())]")
    log(f'   {dt:.0f} s: {r[0]} Fotos übernommen, in Arbeit {r[1]}, Speichern gesperrt {r[2]}, HEIF-Dialoge {dialogs}, Protokoll: {r[3]}')
    ok(r[1] == 0 and not r[2], 'Kein Hängen: alle verarbeitet, Speichern wieder frei')
    ok(r[0] == 8, f'8 lesbare Bilder übernommen (4 große, PNG, gedreht, 1×1, 20000×100) – {r[0]}')
    ok(dialogs == 1, f'HEIF-Hinweis genau einmal als Dialog ({dialogs})')
    ok(len(r[3]) == 3, f'Protokoll je Fehlschlag (kaputt, HEIF, ohne Endung): {r[3]}')
    # Was ist aus PNG mit Transparenz und dem gedrehten Foto geworden?
    px = await p.evaluate("""(async()=>{const sl=[...document.querySelectorAll('[data-editor] .pgrid[data-k=A] .slot:not(.add) img')]; const out=[];
      for (const im of sl) { await im.decode().catch(()=>{}); const c=document.createElement('canvas'); c.width=c.height=8; const g=c.getContext('2d'); g.drawImage(im,0,0,8,8); out.push(Array.from(g.getImageData(4,4,1,1).data.slice(0,3))); } return out})()""")
    log('   Mittelpixel je Vorschau:', px)
    if len(px) >= 5 and px[4][0] < 30 and px[4][1] < 30:
        bef('niedrig', 'Transparente PNG-Fotos werden mit schwarzem Hintergrund übernommen',
            'Ein PNG mit transparentem Hintergrund (z. B. freigestelltes Requisitfoto) wird als JPEG schwarz hinterlegt. Im Rotlicht/Dunkel kaum noch zu erkennen.')
    await p.click('[data-editor] .sheet-h [data-act=save]'); await p.wait_for_timeout(1000)
    ok(await p.evaluate(f"(()=>{{const e=Repo.entriesOf('{hai}').find(x=>x.f.kreis==='999'); return e && Repo.photosOf(e.id).length}})()") == r[0], 'Alle übernommenen Fotos gespeichert')
    # Editor schließen, während Fotos verarbeitet werden
    await p.evaluate(f"Editor.open({{showId:'{hai}', abt:'L'}})"); await p.wait_for_timeout(300)
    await p.click('[data-editor] .pk[data-k=A] [data-act=cam]'); await p.wait_for_timeout(600)
    await p.evaluate("window.__dec = Photo.decode.bind(Photo); Photo.decode = async (...a) => { await new Promise(r=>setTimeout(r,2500)); return __dec(...a); }; 1")
    await p.set_input_files('.cam input[type=file][multiple]', files=[{'name': 'x.jpg', 'mimeType': 'image/jpeg', 'buffer': big[3]}])
    await p.wait_for_timeout(300)
    if await p.evaluate("!!document.querySelector('.cam')"): await p.click('.cam [data-a=done]')
    st = await p.evaluate("[document.querySelectorAll('[data-editor] .slot .busy').length, document.querySelector('[data-editor] .savebtn').disabled]")
    await p.click('[data-editor] [data-act=cancel]'); await p.wait_for_timeout(300)
    d = await p.evaluate("document.querySelector('.dialog h2')?.textContent||''")
    log('   Während Verarbeitung:', st, 'Abbrechen →', d)
    ok(st == [1, True] and 'verwerfen' in d.lower(), 'Speichern gesperrt während Verarbeitung; Abbrechen fragt nach')
    await p.click('.dialog .btn >> nth=0'); await p.wait_for_timeout(5000)
    await c.close()

@section('E2')
async def e2_lightbox(b):
    """Lightbox über Abteilungs- und Phasengrenzen, „Nächster Eintrag“ am Ende"""
    c, p = await newpage(b, name='E2')
    await p.evaluate("Settings.set({depts:['L','T','B']})")
    hai = await p.evaluate("Repo.liveShows().find(s=>s.f.titel.startsWith('Demo: Der Haifisch')).id")
    await p.evaluate(f"location.hash='#/show/{hai}'"); await p.wait_for_timeout(600)
    await p.click('.card .th[data-act=lb] >> nth=0'); await p.wait_for_timeout(500)
    seen = []
    for i in range(30):
        info = await p.evaluate("[document.querySelector('.lbx .pos').textContent, document.querySelector('.lbx').dataset.abt, document.querySelector('.lbx .nextk').classList.contains('hidden'), document.querySelector('.lbx .nav.next').disabled]")
        seen.append(info)
        if info[3]: break
        await p.click('.lbx .nav.next'); await p.wait_for_timeout(260)
    abts = [x[1] for x in seen]
    log('   Lightbox-Reihe:', ' '.join(f'{x[0]}{x[1]}' for x in seen))
    ok(set(abts) >= {'L', 'T', 'B'}, 'Blättern über Licht, Ton, Bühne')
    ok(seen[-1][2], 'Am Ende: „Nächster Eintrag“ ausgeblendet')
    await c.close()

# =====================================================================================
# F. PDF
# =====================================================================================
@section('F1')
async def f1_pdf(b):
    """PDF-Varianten, Sonderzeichen, überlange Werte, Seitenzahlen im Inhaltsverzeichnis"""
    c, p = await newpage(b, name='F1')
    await p.evaluate("Settings.set({depts:['L','T','B','R']}).then(()=>Req.ensureHouse()).then(()=>Req.testShow())")
    hai = await p.evaluate("Repo.liveShows().find(s=>s.f.titel.startsWith('Demo: Der Haifisch')).id")
    bad = []
    for d in (['L'], ['T'], ['B'], ['R'], ['L', 'T', 'B']):
        for cover in (True, False):
            for compact in (True, False):
                sid = 'test-r-show' if d == ['R'] else hai
                nm = f"F1_{''.join(d)}_{'deck' if cover else 'ohne'}_{'kompakt' if compact else 'voll'}"
                path = await save_pdf(p, f"Pdf.build('{sid}',{{kat:'all',depts:{json.dumps(d)},cover:{str(cover).lower()},compact:{str(compact).lower()}}})", nm)
                if not qpdf_ok(path): bad.append(nm)
    empty = await p.evaluate("(async()=>{const s=await Repo.createShow('Leer',['L','T']); window.__leer=s.id; return s.id})()")
    path = await save_pdf(p, f"Pdf.build('{empty}',{{kat:'all',depts:['L','T'],cover:true}})", 'F1_leer')
    if not qpdf_ok(path): bad.append('leer')
    ok(not bad, f'qpdf --check für 20 Varianten + leere Veranstaltung ({bad})')
    # Sonderzeichen
    SZ = 'Ünïcødé ß € „Zitat“ – → ½ 😀 Привет 中文 Œ ™'
    sid = await p.evaluate(f"""(async()=>{{const s=await Repo.createShow({json.dumps(SZ)},['L']); await Repo.patchShow(s.id,{{spielstaette:{json.dumps(SZ)}}});
      await Repo.saveDraft({{id:null,showId:s.id,abt:'L',f:{{kreis:'1',bemerkung:{json.dumps(SZ)},filter:'→ L201'}},photos:{{A:[],E:[]}}}}); return s.id}})()""")
    path = await save_pdf(p, f"Pdf.build('{sid}',{{kat:'all',depts:['L'],cover:true}})", 'F1_sonderzeichen')
    t = pdftext(path, layout=False)
    first = [ln for ln in t.splitlines() if 'Ünïc' in ln or 'nïc' in ln][:2]
    log('   Sonderzeichen im PDF:', first)
    ok(qpdf_ok(path) and 'ß €' in t and '„Zitat“' in t and '->' in t, 'Umlaute, ß, €, „“, → als „->“ lesbar')
    if '???' in t:
        bef('niedrig', 'PDF: Kyrillisch, Chinesisch und Emojis werden zu „???“',
            'Helvetica/WinAnsi kennt keine Zeichen außerhalb Westeuropas. „Привет 中文 😀“ erscheint als „?????? ?? ?“. '
            'Betrifft Gastspiel-Titel, Namen internationaler Ensemble-Mitglieder (Requisite „Personen“). Kein Abbruch, aber nicht lesbar.')
    # Überlange Werte
    sid = await p.evaluate("""(async()=>{const s=await Repo.createShow('Überlang',['L']); const k=Array.from({length:60},(_,i)=>100+i).join('+');
      await Repo.saveDraft({id:null,showId:s.id,abt:'L',f:{kreis:k,bemerkung:'W'.repeat(300)+' '+('Satz mit Inhalt. '.repeat(300))+' ENDE-DER-BEMERKUNG',gruppe:'G'.repeat(80),warnung:'Achtung '.repeat(80)+'WARN-ENDE'},photos:{A:[],E:[]}});
      return s.id})()""")
    path = await save_pdf(p, f"Pdf.build('{sid}',{{kat:'all',depts:['L'],cover:true}})", 'F1_ueberlang')
    t = pdftext(path, layout=False)
    subprocess.run(['pdftoppm', '-r', '50', '-png', path, f'{OUT}/pdf/F1_ueberlang'])
    log('   Überlang: ENDE-DER-BEMERKUNG im PDF:', 'ENDE-DER-BEMERKUNG' in t, '| gekürzt markiert:', '(gekürzt)' in t, '| WARN-ENDE:', 'WARN-ENDE' in t)
    ok('(gekürzt)' in t, 'Gekürzte Bemerkung ist markiert')
    if 'WARN-ENDE' not in t and '…' not in t.split('ACHTUNG')[-1][:900]:
        bef('mittel', 'PDF schneidet lange Warnhinweise nach 6 Zeilen ab – ohne Kennzeichnung',
            'measure() nimmt vom Warnhinweis nur die ersten 6 Zeilen (slice(0,6)), ohne „…“. Gerade der Warnhinweis ist sicherheitsrelevant; das Ende (hier „WARN-ENDE“) fehlt im PDF. '
            'Ebenso ohne Kennzeichnung gekürzt: Requisite „Allgemeine Infos/Wichtig“ nach 30 Zeilen, Ablauf-Einträge nach 6/8 Zeilen, Tabellenzellen nach 8 Zeilen, Checklistenpunkte nach 20 Zeilen.')
    # Kreis 200 Zeichen in der Kopfzeile der Fotoseite
    sid2 = await p.evaluate("""(async()=>{const s=await Repo.createShow('Kreis lang',['L']); const k=Array.from({length:50},(_,i)=>100+i).join('+'); const ph=(await (async()=>{const c=document.createElement('canvas'); c.width=c.height=300; return [await Photo.fromCanvas(c)]})())[0];
      await Repo.saveDraft({id:null,showId:s.id,abt:'L',f:{kreis:k},photos:{A:[{photoId:null,b:ph.b,w:300,h:300,full:ph.full,thumb:ph.thumb}],E:[]}}); return s.id})()""")
    path = await save_pdf(p, f"Pdf.build('{sid2}',{{kat:'all',depts:['L'],cover:false}})", 'F1_kreislang')
    subprocess.run(['pdftoppm', '-r', '50', '-png', '-f', '1', '-l', '2', path, f'{OUT}/pdf/F1_kreislang'])
    bb = subprocess.run(['pdftotext', '-bbox', path, '-'], capture_output=True, text=True).stdout
    xmax = max([float(x) for x in re.findall(r'xMax="([\d.]+)"', bb)] + [0])
    log(f'   Kreis 200 Zeichen: rechtester Text bei x={xmax:.0f} pt (Seite 595 pt)')
    if xmax > 595:
        bef('niedrig', 'PDF-Fotoseite: sehr langer Kreis läuft rechts aus der Seite',
            f'Kreis mit 50 Nummern (≈ 200 Zeichen): Die Kopfzeile wird auf 14 pt verkleinert, aber nicht umgebrochen – Text endet bei x≈{xmax:.0f} pt, die Seite ist 595 pt breit. '
            'Der Infoblock unten bricht korrekt um.')
    # Inhaltsverzeichnis: Seitenzahlen gegen tatsächliche Seiten (> 100 Einträge, mehrseitig)
    sid3 = await p.evaluate("""(async()=>{const s=await Repo.createShow('Viele',['L','T']); const c=document.createElement('canvas'); c.width=c.height=120; const ph=await Photo.fromCanvas(c,0.5);
      await Repo._write({fulls:[{id:ph.b,d:ph.full}],thumbs:[{id:ph.b,d:ph.thumb}]}); const es=[], ps=[];
      for(let i=0;i<140;i++){ const abt=i%7===0?'T':'L'; const e=Rec.create({showId:s.id},Object.assign({abt,del:false,chkA:false,chkE:false}, abt==='L'?{kreis:String(1000+i)}:{kanal:String(i)})); es.push(e);
        if (i%3) ps.push(Rec.create({showId:s.id,b:ph.b,w:120,h:120},{entryId:e.id,kat:i%2?'A':'E',ord:0,label:'',del:false})); }
      await Repo._write({entries:es,photos:ps}); return s.id})()""")
    path = await save_pdf(p, f"Pdf.build('{sid3}',{{kat:'all',depts:['L','T'],cover:true,compact:true}})", 'F1_toc')
    pages = pdftext(path).split('\f')
    toc = {}
    for pg in pages[:4]:
        for m in re.finditer(r'^\s*(10\d\d)\s.*?(\d+)\s*$', pg, re.M): toc.setdefault(m.group(1), int(m.group(2)))
    wrong = []
    for k, n in toc.items():
        if n - 1 >= len(pages) or k not in pages[n - 1]: wrong.append((k, n))
    log(f'   Inhaltsverzeichnis: {len(toc)} Kreise geprüft, {len(pages)-1} Seiten, falsch: {wrong[:5]}')
    ok(len(toc) > 80 and not wrong, f'Seitenzahlen im Inhaltsverzeichnis stimmen ({len(toc)} geprüft)')
    # Requisite: „Foto S. x“
    path = await save_pdf(p, "Pdf.build('test-r-show',{kat:'all',depts:['R'],cover:true,compact:true,rsort:'ort'})", 'F1_requisite')
    pages = pdftext(path).split('\f')
    refs = []
    for i, pg in enumerate(pages):
        for m in re.finditer(r'Foto S\. (\d+)', pg): refs.append((i + 1, int(m.group(1))))
    log(f'   Requisite: {len(refs)} Verweise „Foto S. x“, {len(pages)-1} Seiten')
    ok(all(n <= len(pages) - 1 for _, n in refs), 'Requisite: alle „Foto S. x“ zeigen auf vorhandene Seiten')
    subprocess.run(['pdftoppm', '-r', '40', '-png', '-f', '1', '-l', '6', path, f'{OUT}/pdf/F1_requisite'])
    await c.close()

# =====================================================================================
# G. Oberfläche, Sicherheit, Bedienung
# =====================================================================================
XSS = '<img src=x onerror="window.__xss++">'
XSS2 = '"><svg onload="window.__xss++">'

@section('G1')
async def g1_xss(b):
    """XSS über jedes freie Textfeld – über die Oberfläche und als Daten"""
    c, p = await newpage(b, name='G1')
    await p.evaluate(f"""(async()=>{{const X={json.dumps(XSS)}, Y={json.dumps(XSS2)};
      await Settings.set({{depts:['L','T','B','R'], deviceName:X+Y, filterKeys:[X,Y], mikroKeys:[X], zustandKeys:[X,Y], reqQuick:[{{id:'q1',name:X+Y}}]}}); await Req.ensureHouse(); await Req.testShow();
      const sid='test-r-show'; const s=await Repo.createShow(X+Y,['L','T','B','R'],X+Y); window.__sid=s.id;
      await Repo.patchShow(s.id,{{notiz:X,einrichtung:X,einrichtungT:Y,einrichtungB:X,einrichtungR:Y,dauer:X,'z:x1':{{name:X+Y,typ:'buehne',ebene:'oben',bereich:'haupt',hoehe:X,last:Y,bemerkung:X,ord:200,del:false}},
        'ci:x1':{{abt:'L',text:X+Y,ord:1,del:false}},'bl:x1':{{abschnitt:'pause',text:X+Y,entryId:'',ord:1,del:false}},'b:x1':{{abschnitt:'grund',text:Y,entryId:'',ord:1,del:false}},
        'rp:x1':{{rolle:X,darsteller:Y,ord:1,del:false}},'ro:x1':{{name:X+Y,notiz:X,gruppe:Y,ord:1,del:false}},'ra:x1':{{typ:'teil',name:X,notiz:Y,ord:20,del:false}},'ra:x2':{{typ:'vor',name:'',notiz:'',ord:10,del:false}},
        'rs:x1':{{abschnitt:'ra:x1',text:X+Y,zeit:{{art:'im',min:5}},ausloeser:[{{typ:'stichwort',anzahl:1,wert:X}}],gegenstand:'',ortId:'ro:x1',sicherheit:'waffe',ord:1,del:false}}}});
      for (const [abt,f] of [['L',{{kreis:X+'1',filter:X,gruppe:Y,adresse:X,position:Y,lzug:X,warnung:X+Y,bemerkung:X,sub:Y,geraet:X}}],['T',{{kanal:Y,quelle:X,mikro:X,stagebox:Y,warnung:X,bemerkung:Y}}],
                             ['B',{{zug:X,element:Y,hoehe:X,warnung:Y,bemerkung:X}}],['R',{{was:X+Y,stelle:X,wofuer:Y,uebergabe:X,zuAndere:Y,zustand:[X],markierung:Y,bemerkung:X,ortId:'ro:x1',personIds:['rp:x1'],abschnitte:['ra:x1','ra:x2'],sicherheit:'waffe'}}]])
        await Repo.saveDraft({{id:null,showId:s.id,abt,f,photos:{{A:[],E:[]}}}});
      const hf=Req.houseF(); const hk=Object.keys(hf).find(k=>k.startsWith('ho:')); await Repo.patchHouse({{[hk]:Object.assign({{}},hf[hk],{{name:X+Y,notiz:Y}}),'hg:x1':{{was:X+Y,ortName:X,zustand:[Y],sicherheit:'',bemerkung:X,foto:'',ord:1,del:false}}}});
      const l=await Cues.createList({{titel:X+Y,spielstaette:X,notiz:Y}}); window.__lid=l.id; const cq=Cues.newCue(l.id,'1',{{name:X+Y,notiz:X}}); const cv=document.createElement('canvas'); cv.width=cv.height=100; const ph=await Photo.fromCanvas(cv);
      await Repo._write({{cues:[cq],cueimgs:[Rec.create({{listId:l.id}},{{cueId:cq.id,ord:0,b:ph.b,o:'',w:100,h:100,notiz:X,hinweis:Y,del:false}})],fulls:[{{id:ph.b,d:ph.full}}],thumbs:[{{id:ph.b,d:ph.thumb}}]}});
      window.__cq=cq.id; Sync.log(X); }})()""")
    sid = await p.evaluate('window.__sid'); lid = await p.evaluate('window.__lid')
    steps = ["location.hash='#/'", "App.state.homeSp=App.spOf(Repo.show(__sid)); App.render()", "App.openTrash()", "history.back()",
             f"location.hash='#/show/{sid}'", "App.state.edit=true; App.render()", "Settings.set({view:'big'}).then(()=>App.render())", "Settings.set({view:'grid'}).then(()=>App.render())",
             "Settings.set({view:'list'}).then(()=>App.render())", "App.state.checklist=true; App.render()"]
    for abt in 'LTBR': steps += [f"App.state.abt='{abt}'; App.render()"]
    steps += ["Settings.set({reqView:'ablauf'}).then(()=>App.render())", "App.state.reqSafe=true; App.render()", "App.state.reqSafe=false; App.state.abt='all'; App.render()"]
    steps += ["(()=>{const e=Repo.entriesOf(__sid)[0]; App.openDetailSheet(e.id)})()", "history.back()"]
    steps += [f"Editor.open({{showId:__sid, entryId:Repo.entriesOf(__sid).find(e=>abtOf(e)==='{a}').id}})" for a in 'LTBR']
    steps = [s for x in steps for s in ([x, "history.back()"] if x.startswith('Editor') else [x])]
    steps += ["App.openLightbox && 1", "RunList.open(__sid)", "history.back()", "RunList.editItems(__sid)", "history.back()", "SetupView.editL(__sid)", "history.back()",
              "SetupView.editP(__sid)", "history.back()", "SetupView.editAblauf(__sid,'L')", "history.back()", "SetupView.editHint(__sid,'T')", "history.back()",
              "Req.editGeneral(__sid)", "history.back()", "Req.editPersons(__sid)", "history.back()", "Req.editOrts(__sid)", "history.back()", "Req.editHouse(__sid)", "history.back()",
              "Req.editQuick()", "history.back()", "Req.editStep(__sid,'rs:x1')", "history.back()", "Req.pickOrt(__sid)", "history.back()", "Req.assignSheet(__sid,'ra:x1')", "history.back()",
              "App.showMenu(__sid)", "history.back()", "App.pdf(__sid)", "history.back()", "SettingsView.open()", "history.back()", "DiagView.open()", "history.back()",
              "SyncView.open()", "history.back()", "location.hash='#/cues'", f"location.hash='#/cue/{lid}'", "CueView.editCue(__cq)", "history.back()",
              f"CueView.openLb('{lid}', Cues.imgsOf(__cq)[0].id)", "history.back()", f"CueView.listMenu('{lid}')", "history.back()", "CueView.trash()", "history.back()"]
    fails = []
    for s in steps:
        try:
            await ev(p, s); await p.wait_for_timeout(180)
        except Exception as ex: fails.append((s, str(ex)[:80]))
    # Lightbox einer Doku-Karte
    await p.evaluate(f"location.hash='#/show/{sid}'"); await p.wait_for_timeout(300)
    await p.evaluate("Lightbox.open([{b:'x',entryId:Repo.entriesOf(__sid)[0].id,kat:'A',idx:0,n:1,cap:"+json.dumps(XSS)+"}],0)"); await p.wait_for_timeout(300)
    await p.evaluate("history.back()")
    for d in (['L', 'T', 'B', 'R'], ['R']):
        await p.evaluate(f"Pdf.build(__sid,{{kat:'all',depts:{json.dumps(d)},cover:true}})")
    await p.evaluate("Pdf.buildCues(__lid,{cover:true})")
    # XSS über die Oberfläche: Gerätename-Dialog, Titel im Anlegen-Dialog
    await p.evaluate("location.hash='#/'"); await p.wait_for_timeout(300)
    await p.click('[data-act=newshow]'); await p.wait_for_timeout(200); await p.fill('#ns-t', XSS2); await p.click('[data-ok]'); await p.wait_for_timeout(700)
    x = await p.evaluate('window.__xss')
    log(f'   {len(steps)} Ansichten/Blätter geöffnet, Fehler beim Öffnen: {fails[:3]}')
    ok(x == 0, f'Kein eingeschleustes Skript ausgeführt (Zähler {x})')
    await c.close()

@section('G2')
async def g2_viewmode(b):
    """Ansichtsmodus: Welche Klickwege schreiben trotzdem?"""
    c, p = await newpage(b, 390, 844, name='G2')
    await p.evaluate("Settings.set({depts:['L','T','B','R']}).then(()=>Req.ensureHouse()).then(()=>Req.testShow())")
    hai = await p.evaluate("Repo.liveShows().find(s=>s.f.titel.startsWith('Demo: Der Haifisch')).id")
    await p.evaluate(f"App.state.edit=false; location.hash='#/show/{hai}'"); await p.wait_for_timeout(500)
    snap = "(()=>{let n=0; for(const m of [Repo.shows,Repo.entries,Repo.photos,Repo.cuelists,Repo.cues,Repo.cueimgs,Repo.house]) for(const r of m.values()) n+=r.mod; return n})()"
    found = []
    async def tryit(name, fn):
        before = await p.evaluate(snap)
        try: await fn()
        except Exception as ex: log('    ', name, 'nicht ausführbar:', str(ex)[:80])
        await p.wait_for_timeout(400)
        after = await p.evaluate(snap)
        if after != before: found.append(name)
        log(f'    {name}: {"SCHREIBT" if after != before else "schreibt nicht"}')
        await p.evaluate("while(Ui.stack.length) Ui.stack[Ui.stack.length-1].el.remove(), Ui.stack.pop(); App.state.edit=false; App.render()")
    async def rename():
        await p.click('.appbar [data-act=rename]'); await p.wait_for_timeout(300)
        await p.fill('#sh-t', 'Im Ansichtsmodus umbenannt'); await p.click('.sheet [data-ok]')
    await tryit('Titel antippen → umbenennen (Veranstaltung)', rename)
    async def keyN():
        await p.keyboard.press('n'); await p.wait_for_timeout(200)
    await tryit('Taste N (neuer Eintrag)', keyN)
    async def reset():
        await p.click('[data-act=checklist]'); await p.wait_for_timeout(200); await p.click('[data-act=resetchk]'); await p.wait_for_timeout(200)
        await p.click('.dialog .btn >> nth=0')
    await p.evaluate(f"(async()=>{{const e=Repo.entriesOf('{hai}')[0]; await Repo.toggleCheck(e.id,'A');}})()")
    await tryit('„Abhaken“ → „Zurücksetzen“ (Massen-Änderung)', reset)
    async def dup():
        await p.click('.appbar [data-act=showmenu]'); await p.wait_for_timeout(200); await p.click('.dialog .btn:has-text("Duplizieren")')
    await tryit('⋯ → Duplizieren', dup)
    async def delshow():
        await p.click('.appbar [data-act=showmenu]'); await p.wait_for_timeout(200); await p.click('.dialog .btn:has-text("löschen")'); await p.wait_for_timeout(200)
        await p.click('.dialog .btn.danger')
    await tryit('⋯ → Veranstaltung löschen', delshow)
    await p.evaluate(f"(async()=>{{await Repo.restoreShow('{hai}'); location.hash='#/show/{hai}'}})()"); await p.wait_for_timeout(400)
    async def ddel():
        await p.click('.card [data-act=open] >> nth=0'); await p.wait_for_timeout(300)
        await p.click('.sheet [data-act=dedit]'); await p.wait_for_timeout(500)
    before_edit = await p.evaluate("App.state.edit")
    await tryit('Detail → „Bearbeiten“ (schaltet Bearbeitungsmodus ein)', ddel)
    lid = await p.evaluate("(async()=>{const l=await Cues.createList({titel:'Ansicht'}); await Cues.addRange(l.id,'1','3','1'); return l.id})()")
    await p.evaluate(f"App.state.edit=false; location.hash='#/cue/{lid}'"); await p.wait_for_timeout(400)
    async def cuetitle():
        await p.click('.appbar [data-cact=editlist]'); await p.wait_for_timeout(300); await p.fill('#cl-t', 'geändert'); await p.click('.sheet [data-ok]')
    await tryit('Cue-Liste: Titel antippen → ändern', cuetitle)
    async def cuedel():
        await p.click('.appbar [data-cact=listmenu]'); await p.wait_for_timeout(200); await p.click('.dialog .btn:has-text("löschen")'); await p.wait_for_timeout(300)
        await p.click('.dialog .btn:has-text("Papierkorb")')
    await tryit('Cue-Liste: ⋯ → löschen', cuedel)
    await p.evaluate("location.hash='#/show/test-r-show'"); await p.wait_for_timeout(400)
    await p.evaluate("App.state.abt='R'; Settings.set({reqView:'ablauf'}).then(()=>App.render())"); await p.wait_for_timeout(300)
    async def reqbtns():
        for sel in ['[data-ract=a-del]', '[data-ract=s-add]', '[data-ract=add-ab]', '[data-ract=i-up]']:
            n = await p.evaluate(f"document.querySelectorAll('{sel}').length")
            if n: await p.click(f'{sel} >> nth=0'); await p.wait_for_timeout(200)
    await tryit('Requisite Ablauf: Bearbeiten-Knöpfe im Ansichtsmodus', reqbtns)
    log('   Schreibende Wege im Ansichtsmodus:', found)
    real = [f for f in found if 'Bearbeiten“' not in f and 'Zurücksetzen' not in f]
    if real:
        bef('mittel', 'Ansichtsmodus schützt nicht vor Änderungen über Titel und ⋯-Menü',
            'Im Ansichtsmodus (Schutz vor versehentlichem Ändern, Designentscheidung 5) schreiben trotzdem: ' + '; '.join(real) + '. '
            'Ein Tipp auf den Titel in der Kopfzeile öffnet sofort „Veranstaltung bearbeiten“ (Titel, Spielstätte, Abteilungen abwählen!), das ⋯-Menü bietet Löschen und Duplizieren – '
            'genau die Stellen, die man im Halbdunkel versehentlich trifft. Löschen hat eine Rückfrage, Umbenennen/Abteilungen nicht.')
    if 'Zurücksetzen' in ' '.join(found):
        bef('niedrig', '„Abhaken → Zurücksetzen“ im Ansichtsmodus setzt alle Haken der Abteilung zurück',
            'Abhaken ist im Ansichtsmodus gewollt, das Zurücksetzen aller Haken ist aber eine Massen-Änderung (mit Auswahlmenü, ohne Rückfrage zum Inhalt).')
    await c.close()

@section('G3')
async def g3_history(b):
    """Zurück-Geste / History: Ebenen, Startseite"""
    c, p = await newpage(b, 390, 844, name='G3')
    hai = await p.evaluate("Repo.liveShows().find(s=>s.f.titel.startsWith('Demo: Der Haifisch')).id")
    await p.evaluate(f"location.hash='#/show/{hai}'"); await p.wait_for_timeout(500)
    # Detail-Blatt → Bearbeiten → Speichern → Zurück
    await p.click('.card [data-act=open] >> nth=0'); await p.wait_for_timeout(300)
    await p.click('.sheet [data-act=dedit]'); await p.wait_for_timeout(600)
    await p.click('[data-editor] .sheet-h [data-act=save]'); await p.wait_for_timeout(600)
    h1 = await p.evaluate("[location.hash, Ui.stack.length, history.length]")
    await p.evaluate("history.back()"); await p.wait_for_timeout(500)
    h2 = await p.evaluate("[location.hash, Ui.stack.length]")
    log('   nach Bearbeiten+Speichern:', h1, '→ Zurück:', h2)
    ok(h1[0].startswith('#/show/') and h1[1] == 0, 'Nach Speichern: in der Veranstaltung, keine Ebene offen')
    # Schnelle Folge Blatt → Dialog → Blatt
    await p.evaluate(f"location.hash='#/show/{hai}'"); await p.wait_for_timeout(300)
    await p.evaluate("SettingsView.open(); Ui.dialog({title:'x'}); SyncView.open()"); await p.wait_for_timeout(200)
    await p.evaluate("history.back(); history.back(); history.back()"); await p.wait_for_timeout(800)
    h3 = await p.evaluate("[location.hash, Ui.stack.length, document.querySelectorAll('.scrim').length]")
    log('   Blatt→Dialog→Blatt, dreimal zurück:', h3)
    ok(h3[1] == 0 and h3[2] == 0 and h3[0].startswith('#/show/'), 'Alle Ebenen zu, Veranstaltung bleibt')
    # Editor mit ungespeicherten Änderungen per Zurück
    await p.evaluate("App.state.edit=true; App.render()")
    await p.evaluate(f"Editor.open({{showId:'{hai}', abt:'L'}})"); await p.wait_for_timeout(300)
    await p.fill('[data-editor] [name=kreis]', '123')
    await p.evaluate("history.back()"); await p.wait_for_timeout(400)
    d = await p.evaluate("document.querySelector('.dialog h2')?.textContent||''")
    await p.click('.dialog .btn >> nth=0'); await p.wait_for_timeout(400)
    still = await p.evaluate("[!!document.querySelector('[data-editor]'), document.querySelector('[data-editor] [name=kreis]')?.value, location.hash]")
    log('   Zurück im Editor:', d, still)
    ok('verwerfen' in d and still[0] and still[1] == '123', 'Zurück mit ungespeicherten Änderungen: Rückfrage, „Abbrechen“ behält den Editor')
    await p.evaluate("history.back()"); await p.wait_for_timeout(400); await p.click('.dialog .btn.danger'); await p.wait_for_timeout(500)
    h4 = await p.evaluate("[location.hash, Ui.stack.length]")
    ok(h4[0].startswith('#/show/') and h4[1] == 0, 'Verwerfen: zurück in der Veranstaltung')
    await c.close()

def LAYOUT_JS():
    return r"""(() => {
  const vis = el => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el); return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && r.bottom > 0 && r.top < innerHeight && r.right > 0 && r.left < innerWidth; };
  const res = { hscroll: document.documentElement.scrollWidth - innerWidth, out: [], small: [], cut: [], tiny: [], overlap: [] };
  const taps = [...document.querySelectorAll('button, a, input:not([type=hidden]), select, textarea, [role=button], [role=checkbox], summary')].filter(vis)
     .filter(el => !el.closest('.hidden') && !(el.tagName==='INPUT' && ['checkbox','file'].includes(el.type) && el.closest('.switch')));
  const name = el => (el.getAttribute('aria-label') || el.textContent || el.name || el.tagName).trim().replace(/\s+/g,' ').slice(0, 40) + ' <' + el.tagName.toLowerCase() + (el.className && typeof el.className==='string' ? '.' + el.className.split(' ')[0] : '') + '>';
  taps.forEach(el => { const r = el.getBoundingClientRect();
    if (r.right > innerWidth + 1 || r.left < -1) res.out.push(name(el));
    const minS = el.matches('.switch input') ? 30 : 44;
    if ((r.width < minS - 0.5 || r.height < minS - 0.5) && !el.matches('input[type=range]')) res.small.push(name(el) + ` ${Math.round(r.width)}×${Math.round(r.height)}`); });
  for (let i = 0; i < taps.length; i++) for (let j = i + 1; j < taps.length; j++) { const a = taps[i], b2 = taps[j]; if (a.contains(b2) || b2.contains(a)) continue;
    const r1 = a.getBoundingClientRect(), r2 = b2.getBoundingClientRect(); const ox = Math.min(r1.right, r2.right) - Math.max(r1.left, r2.left), oy = Math.min(r1.bottom, r2.bottom) - Math.max(r1.top, r2.top);
    if (ox > 2 && oy > 2) { const ta = document.elementFromPoint((Math.max(r1.left,r2.left)+Math.min(r1.right,r2.right))/2, (Math.max(r1.top,r2.top)+Math.min(r1.bottom,r2.bottom))/2);
      res.overlap.push(name(a) + ' ⟷ ' + name(b2)); } }
  document.querySelectorAll('.kreis, .rwas, .cqnr, h1, h2, h3, .tag, .chip, .btn, .deptbtn, .katbtn, .qb, .bk, .zn, .rst').forEach(el => { if (!vis(el) || el.closest('.hidden')) return;
    const cs = getComputedStyle(el); if (cs.textOverflow === 'ellipsis' || cs.overflow === 'visible' && cs.overflowX === 'visible') return;
    if (el.scrollWidth > el.clientWidth + 2) res.cut.push(name(el) + ` ${el.scrollWidth}>${el.clientWidth}`); });
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); let n;
  while ((n = walker.nextNode())) { if (!n.textContent.trim()) continue; const el = n.parentElement; if (!el || !vis(el) || el.closest('.hidden,svg,.lbx .stage')) continue;
    const fs = parseFloat(getComputedStyle(el).fontSize); if (fs < 11) res.tiny.push(n.textContent.trim().slice(0, 30) + ` ${fs}px <${el.tagName.toLowerCase()}.${(el.className||'').toString().split(' ')[0]}>`); }
  for (const k of ['out','small','cut','tiny','overlap']) res[k] = [...new Set(res[k])];
  return res; })()"""

def CONTRAST_JS():
    return r"""(() => {
  const parse = s => { if (!s) return null; let m = s.match(/rgba?\(([^)]+)\)/); if (m) { const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number); return [p[0], p[1], p[2], p[3] == null ? 1 : p[3]]; }
    m = s.match(/color\(srgb ([^)]+)\)/); if (m) { const p = m[1].split(/[ \/]+/).filter(Boolean).map(Number); return [p[0]*255, p[1]*255, p[2]*255, p[3] == null ? 1 : p[3]]; } return null; };
  const blend = (top, bot) => { const a = top[3]; return [top[0]*a + bot[0]*(1-a), top[1]*a + bot[1]*(1-a), top[2]*a + bot[2]*(1-a), 1]; };
  const lum = c => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126*f(c[0]) + 0.7152*f(c[1]) + 0.0722*f(c[2]); };
  const bgOf = el => { const stack = []; let e = el; while (e) { const cs = getComputedStyle(e); const c = parse(cs.backgroundColor); if (cs.backgroundImage && cs.backgroundImage !== 'none' && !cs.backgroundImage.includes('gradient')) return null;
      if (c && c[3] > 0) { stack.push(c); if (c[3] >= 0.999) break; } e = e.parentElement; }
    let bg = parse(getComputedStyle(document.body).backgroundColor) || [0,0,0,1]; for (let i = stack.length - 1; i >= 0; i--) bg = blend(stack[i], bg); return bg; };
  const out = []; const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); let n; const seen = new Set();
  while ((n = walker.nextNode())) { const t = n.textContent.trim(); if (!t) continue; const el = n.parentElement; if (!el || seen.has(el)) continue; seen.add(el);
    const r = el.getBoundingClientRect(); if (!(r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < innerHeight)) continue; const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || el.closest('.hidden, svg, .lbx .stage, .qrbox')) continue;
    let op = 1; let e = el; while (e) { op *= +getComputedStyle(e).opacity; e = e.parentElement; } if (op < 0.4) continue;
    const fg0 = parse(cs.color); const bg = bgOf(el); if (!fg0 || !bg) continue; const fg = blend([fg0[0],fg0[1],fg0[2],fg0[3]*op], bg);
    const L1 = lum(fg), L2 = lum(bg); const cr = (Math.max(L1,L2) + 0.05) / (Math.min(L1,L2) + 0.05);
    const fs = parseFloat(cs.fontSize), bold = +cs.fontWeight >= 700; const large = fs >= 24 || (bold && fs >= 18.66);
    out.push({ t: t.slice(0, 28), cls: (el.className || '').toString().split(' ').slice(0,2).join('.'), tag: el.tagName.toLowerCase(), cr: Math.round(cr * 100) / 100, large, fs }); }
  return out; })()"""

@section('G4')
async def g4_layout(b):
    """Mobil/Tablet: waagrechtes Scrollen, Tippflächen, abgeschnittener Text, kleine Schrift, Überlappung – je Ansicht"""
    results = {}
    for (w, h, zoom, nm) in [(390, 844, 1, 'Smartphone'), (844, 390, 1, 'Smartphone quer'), (768, 1024, 1, 'Tablet'), (390, 844, 1.3, 'Smartphone 130 %'), (390, 844, 2, 'Smartphone 200 %')]:
        c, p = await newpage(b, w, h, name=nm)
        await p.evaluate("Settings.set({depts:['L','T','B','R']}).then(()=>Req.ensureHouse()).then(()=>Req.testShow())")
        await p.evaluate("(async()=>{const s=Repo.liveShows().find(s=>s.f.titel.startsWith('Demo: Der Haifisch')); await Repo.patchShow(s.id,{titel:'Die Dreigroschenoper – Wiederaufnahme mit langem Titel', abteilungen:['L','T','B','R']});})()")
        if zoom != 1:
            await p.add_style_tag(content=f'html{{zoom:{zoom}}}')
            await p.evaluate("dispatchEvent(new Event('resize'))")
        hai = await p.evaluate("Repo.liveShows().find(s=>s.f.titel.startsWith('Die Dreigroschenoper')).id")
        views = [('Startseite', "location.hash='#/'"), ('Veranstaltung Alle', f"location.hash='#/show/{hai}'; App.state.abt='all'; App.state.edit=true; App.render()"),
                 ('Kacheln', "Settings.set({view:'grid'}).then(()=>App.render())"), ('Großbild', "Settings.set({view:'big'}).then(()=>App.render())"),
                 ('Liste Licht', "Settings.set({view:'list'}).then(()=>{App.state.abt='L'; App.render()})"),
                 ('Requisite Einrichten', "location.hash='#/show/test-r-show'; App.state.abt='R'; Settings.set({reqView:'einrichten'}).then(()=>App.render())"),
                 ('Requisite Ablauf', "Settings.set({reqView:'ablauf'}).then(()=>App.render())"),
                 ('Editor Licht', f"Editor.open({{showId:'{hai}', abt:'L'}}); document.querySelector('[data-editor] details.more') && (document.querySelector('[data-editor] details.more').open=true)"),
                 ('Editor Requisite', "history.back(); setTimeout(()=>Editor.open({showId:'test-r-show', abt:'R'}),100)"),
                 ('Checkliste', "history.back(); setTimeout(()=>RunList.open('test-r-show'),100)"),
                 ('Einstellungen', "history.back(); setTimeout(()=>SettingsView.open(),100)"),
                 ('Abgleich', "history.back(); setTimeout(()=>SyncView.open(),100)"),
                 ('Cue-Liste', "history.back(); setTimeout(async()=>{const l=await Cues.createList({titel:'Lange Cue-Liste mit Titel'}); await Cues.addRange(l.id,'1','8','1'); App.state.edit=true; location.hash='#/cue/'+l.id},100)")]
        res = {}
        for vn, js in views:
            try:
                await p.evaluate(js); await p.wait_for_timeout(500)
                res[vn] = await p.evaluate(LAYOUT_JS())
            except Exception as ex:
                res[vn] = {'err': str(ex)[:100]}
        results[nm] = res
        await p.screenshot(path=f'{OUT}/screens/layout_{nm.replace(" ", "_").replace("%","pz")}.png')
        await c.close()
    json.dump(results, open(f'{OUT}/layout.json', 'w'), ensure_ascii=False, indent=1)
    for nm, res in results.items():
        hs = [v for v, r in res.items() if r.get('hscroll', 0) > 1]
        log(f'   {nm}: waagrecht scrollend: {hs or "–"}')
        ok(not hs, f'{nm}: kein waagrechtes Scrollen')
        for v, r in res.items():
            if r.get('small'): log(f'      {v}: zu kleine Tippflächen ({len(r["small"])}): {r["small"][:6]}')
            if r.get('overlap'): log(f'      {v}: Überlappung: {r["overlap"][:4]}')
            if r.get('cut'): log(f'      {v}: abgeschnitten: {r["cut"][:4]}')
            if r.get('tiny'): log(f'      {v}: Schrift < 11 px: {r["tiny"][:4]}')
    sm = results['Smartphone']
    small_all = sorted({x for r in sm.values() for x in r.get('small', [])})
    if small_all:
        bef('mittel', f'Tippflächen unter 44 px auf dem Smartphone ({len(small_all)} Stellen)',
            'Beispiele: ' + '; '.join(small_all[:10]) + '. Mit Handschuhen im Halbdunkel schwer zu treffen. Vollständige Liste: layout.json.')
    hsl = [(nm, v) for nm, res in results.items() for v, r in res.items() if r.get('hscroll', 0) > 1]
    if hsl:
        bef('mittel' if any(n in ('Smartphone', 'Tablet', 'Smartphone quer') for n, _ in hsl) else 'niedrig', 'Waagrechtes Scrollen in einzelnen Ansichten',
            'Betroffen: ' + ', '.join(f'{n}/{v}' for n, v in hsl[:12]) + '. (130 %/200 % per CSS-zoom nachgebildet – Annäherung an große Systemschrift.)')

@section('G5')
async def g5_contrast(b):
    """Kontrast nach WCAG je Farbschema (Dunkel, Hell, Rotlicht) über die wichtigsten Ansichten"""
    worst = {}
    for theme in ('dark', 'light', 'red'):
        c, p = await newpage(b, 820, 1180, name=f'Kontrast {theme}')
        await p.evaluate(f"Settings.set({{theme:'{theme}', depts:['L','T','B','R']}}).then(()=>Req.ensureHouse()).then(()=>Req.testShow())")
        hai = await p.evaluate("Repo.liveShows().find(s=>s.f.titel.startsWith('Demo: Der Haifisch')).id")
        await p.evaluate(f"Repo.patchShow('{hai}',{{abteilungen:['L','T','B','R']}})")
        views = [('Startseite', "location.hash='#/'"), ('Liste', f"location.hash='#/show/{hai}'; App.state.abt='all'; App.state.edit=false; App.state.checklist=true; App.render()"),
                 ('Großbild', "Settings.set({view:'big'}).then(()=>App.render())"), ('Requisite', "location.hash='#/show/test-r-show'; App.state.abt='R'; Settings.set({view:'list',reqView:'einrichten'}).then(()=>App.render())"),
                 ('Requisite Ablauf', "Settings.set({reqView:'ablauf'}).then(()=>App.render())"), ('Checkliste', f"RunList.open('{hai}')"), ('Einstellungen', "history.back(); setTimeout(()=>SettingsView.open(),100)"),
                 ('Löschen-Dialog', "history.back(); setTimeout(()=>Ui.confirm('Löschen?','Wirklich?','Löschen',true),100)"),
                 ('Fehler-Toast', "history.back(); setTimeout(()=>Ui.toast('Speichern fehlgeschlagen','err',{ms:9000}),100)"),
                 ('Editor', f"Editor.open({{showId:'{hai}', abt:'L'}})")]
        for vn, js in views:
            await p.evaluate(js); await p.wait_for_timeout(500)
            items = await p.evaluate(CONTRAST_JS())
            lim = 4 if theme == 'red' else 4.5
            for it in items:
                need = 3 if it['large'] else lim
                if it['cr'] < need:
                    key = (theme, it['cls'] or it['tag'], it['t'][:16])
                    if key not in worst or worst[key][0] > it['cr']: worst[key] = (it['cr'], vn, need)
            if vn in ('Liste', 'Requisite', 'Löschen-Dialog', 'Fehler-Toast'):
                await p.screenshot(path=f'{OUT}/screens/kontrast_{vn.replace(" ","_")}_{theme}.png')
        await c.close()
    rows = sorted(worst.items(), key=lambda kv: kv[1][0])
    json.dump([[k[0], k[1], k[2], v[0], v[1], v[2]] for k, v in rows], open(f'{OUT}/kontrast.json', 'w'), ensure_ascii=False, indent=0)
    for theme in ('dark', 'light', 'red'):
        tr = [(k, v) for k, v in rows if k[0] == theme]
        log(f'   {theme}: {len(tr)} Texte unter Grenzwert. Schlechteste: ' + '; '.join(f'„{k[2]}“ .{k[1]} {v[0]}:1 ({v[1]})' for k, v in tr[:8]))
        ok(not tr, f'{theme}: alle Texte ≥ Grenzwert')
    return rows

@section('G6')
async def g6_perf(b):
    """Leistung: 400 Einträge, 1500 Fotos, 200 Züge; dazu Requisite mit 400 Gegenständen"""
    c, p = await newpage(b, 1180, 820, name='G6')
    t0 = time.time()
    sid = await p.evaluate("""(async()=>{ const s = await Repo.createShow('Leistung',['L','T','B']); const zf = {}; for (let i=0;i<200;i++) zf['z:p'+i] = {name:'Zug '+i, typ:'buehne', ebene:['unter','boden','oben'][i%3], bereich:['vor','haupt','hinter'][i%3], ord:100+i, del:false};
      await Repo.patchShow(s.id, zf); const cv=document.createElement('canvas'); cv.width=cv.height=360; const g=cv.getContext('2d');
      const full = await Photo._jpeg((()=>{const x=document.createElement('canvas'); x.width=x.height=400; x.getContext('2d').fillRect(0,0,50,50); return x})(), 0.5);
      const es=[], ps=[], fulls=[], thumbs=[];
      for (let i=0;i<400;i++){ const abt=['L','L','T','B'][i%4]; const f = abt==='L'?{kreis:String(i)}:abt==='T'?{kanal:String(i)}:{zug:'Zug '+(i%200), zugId:'p'+(i%200), element:'E'+i};
        const e=Rec.create({showId:s.id},Object.assign({abt,del:false,chkA:false,chkE:false,bemerkung:'Bemerkung '+i},f)); es.push(e); }
      for (let k=0;k<1500;k++){ g.fillStyle=`hsl(${k%360},50%,40%)`; g.fillRect(0,0,360,360); const th = await Photo._jpeg(cv, 0.5); const id='pb'+k; fulls.push({id,d:full}); thumbs.push({id,d:th});
        const e = es[k%400]; ps.push(Rec.create({showId:s.id,b:id,w:400,h:400},{entryId:e.id,kat:(abtOf(e)==='B'||k%2)?'A':'E',ord:k,label:'',del:false})); }
      await Repo._write({entries:es,photos:ps,fulls,thumbs}); return s.id; })()""")
    log(f'   Daten angelegt in {time.time()-t0:.0f} s')
    await reload(p)
    m = {}
    t = time.time(); await p.evaluate(f"location.hash='#/show/{sid}'"); await p.wait_for_function("document.querySelectorAll('.card').length>0"); m['Liste öffnen'] = time.time() - t
    t = time.time(); await p.evaluate("Settings.set({view:'grid'}).then(()=>App.render())"); m['Kacheln'] = time.time() - t
    t = time.time(); await p.evaluate("Settings.set({view:'big'}).then(()=>App.render())"); m['Großbild'] = time.time() - t
    await p.evaluate("Settings.set({view:'list'}).then(()=>App.render())")
    t = time.time()
    for _ in range(40): await p.mouse.wheel(0, 3000); await p.wait_for_timeout(50)
    m['bis ans Ende scrollen'] = time.time() - t
    cards = await p.evaluate("document.querySelectorAll('.card').length")
    urls = await p.evaluate("Thumbs.map.size")
    t = time.time(); await p.evaluate(f"App.state.abt='B'; App.render()"); m['Bühne filtern (200 Züge)'] = time.time() - t
    t = time.time(); await p.evaluate(f"(async()=>{{const e=Repo.entriesOf('{sid}')[5]; await Repo.saveDraft({{id:e.id,showId:e.showId,abt:abtOf(e),f:{{bemerkung:'neu'}},photos:{{A:Repo.photosOf(e.id,'A').map(p=>({{photoId:p.id,b:p.b,w:p.w,h:p.h}})),E:Repo.photosOf(e.id,'E').map(p=>({{photoId:p.id,b:p.b,w:p.w,h:p.h}}))}}}})}})()"); m['Speichern'] = time.time() - t
    t = time.time(); n = await p.evaluate(f"(async()=>{{const b=await Pdf.build('{sid}',{{kat:'all',depts:['L','T','B'],cover:true,compact:false}}); return [Pdf.lastPages, b.size]}})()"); m['PDF'] = time.time() - t
    t = time.time(); sz = await p.evaluate("(async()=>{const r=await Sync.buildPackage({type:'sync',since:0}); return r.blob.size})()"); m['Sync-Paket'] = time.time() - t
    mem = await p.evaluate("performance.memory?Math.round(performance.memory.usedJSHeapSize/1048576):-1")
    log('   Zeiten (s): ' + ', '.join(f'{k} {v:.1f}' for k, v in m.items()))
    log(f'   Karten im DOM {cards}, Object-URLs {urls}, PDF {n[0]} Seiten/{n[1]//1048576} MB, Paket {sz//1048576} MB, Heap {mem} MB')
    ok(m['Liste öffnen'] < 3 and m['Speichern'] < 2, 'Liste und Speichern unter 3 s')
    ok(urls <= 500, f'Object-URL-Cache begrenzt ({urls} ≤ 500)')
    # Requisite groß
    t = time.time()
    await p.evaluate("""(async()=>{await Settings.set({depts:['L','T','B','R']}); await Req.ensureHouse(); const s=await Repo.createShow('Req groß',['R']); window.__rq=s.id;
      const f={}; for(let i=0;i<40;i++) f['ro:o'+i]={name:'Ort '+i,ord:i,del:false}; for(let i=0;i<30;i++) f['rp:p'+i]={rolle:'Rolle '+i,darsteller:'Person '+i,ord:i,del:false};
      ['vor','teil','pause','teil','nach'].forEach((t,i)=>f['ra:a'+i]={typ:t,name:'',ord:i*10,del:false}); for(let i=0;i<60;i++) f['rs:s'+i]={abschnitt:'ra:a'+(i%5),text:'Schritt '+i,ord:i,del:false};
      await Repo.patchShow(s.id,f); const es=[]; for(let i=0;i<400;i++) es.push(Rec.create({showId:s.id},{abt:'R',was:'Ding '+i,ortId:'ro:o'+(i%40),ort:'Ort '+(i%40),personIds:['rp:p'+(i%30)],abschnitte:['ra:a0','ra:a'+(1+i%4)],del:false,chkA:false,chkE:false}));
      await Repo._write({entries:es}); })()""")
    t = time.time(); await p.evaluate("location.hash='#/show/'+__rq; App.state.abt='R'; Settings.set({reqView:'einrichten'}).then(()=>App.render())"); await p.wait_for_function("document.querySelectorAll('.erow').length>100"); m['Requisite Einrichten (400)'] = time.time() - t
    t = time.time(); await p.click('.gchk >> nth=3'); await p.wait_for_timeout(50); await p.wait_for_function("document.querySelectorAll('.gchk[aria-checked=true]').length>=1"); m['Requisite 1 Haken bis Anzeige'] = time.time() - t
    t = time.time(); await p.evaluate("Settings.set({reqView:'ablauf'}).then(()=>App.render())"); m['Requisite Ablauf (400)'] = time.time() - t
    t = time.time(); await p.evaluate("Pdf.build(__rq,{kat:'all',depts:['R'],cover:true})"); m['Requisite PDF'] = time.time() - t
    log('   Requisite: ' + ', '.join(f'{k} {v:.1f} s' for k, v in m.items() if 'Requisite' in k))
    slow = {k: v for k, v in m.items() if v > 1.5 and k not in ('PDF', 'Sync-Paket', 'Requisite PDF', 'bis ans Ende scrollen')}
    if slow:
        bef('mittel', 'Träge Bedienung bei großen Veranstaltungen',
            'Über 1,5 s (Desktop-Chromium, Telefon deutlich langsamer): ' + ', '.join(f'{k} {v:.1f} s' for k, v in slow.items()) +
            '. Jeder Haken in der Requisite zeichnet die ganze Ansicht neu (ReqView.render nach jedem Repo-Ereignis).', art='reproduziert (Gerätezeiten: auf Gerät prüfen)')
    await c.close()

# =====================================================================================
# I. Abteilungen einzeln und kombiniert
# =====================================================================================
MATRIX = []
@section('I1')
async def i1_matrix(b):
    """Gerät × Veranstaltung: Leiste, Zähler, Phasen, Kästen, Schnellzugriff, Hinzufügen"""
    combos = [('L', 'L'), ('T', 'T'), ('B', 'B'), ('R', 'R'), ('LT', 'LT'), ('LB', 'LB'), ('TB', 'TB'), ('LR', 'LR'), ('BR', 'BR'), ('LTB', 'LTB'), ('LTR', 'LTR'), ('LTBR', 'LTBR'),
              ('B', 'L'), ('LT', 'TB')]
    c, p = await newpage(b, 390, 844, name='Matrix')
    await p.evaluate("Settings.set({depts:['L','T','B','R']}).then(()=>Req.ensureHouse()).then(()=>Req.testShow())")
    # Veranstaltung mit allen vier Abteilungen (Haifisch + Requisite-Gegenstände dazu)
    sid = await p.evaluate("""(async()=>{const h=Repo.liveShows().find(s=>s.f.titel.startsWith('Demo: Der Haifisch'));
      const src=Repo.entriesOf('test-r-show').slice(0,6); const es=src.map(e=>Rec.create({showId:h.id},Object.assign({},e.f,{ortId:'',abschnitte:undefined})));
      await Repo._write({entries:es}); await Repo.patchShow(h.id, Object.assign({abteilungen:['L','T','B','R'], einrichtungR:'Wichtig: Degen'}, Req.defaultAbschnitte())); return h.id})()""")
    for dev, show in combos:
        CUR[0] = f'I1 {dev}/{show}'
        row = {'Gerät': dev, 'Veranstaltung': show}
        await p.evaluate(f"Settings.set({{depts:{json.dumps(list(dev))}}})")
        await p.evaluate(f"Repo.patchShow('{sid}',{{abteilungen:{json.dumps(list(show))}}})")
        await p.evaluate(f"App.state.abt='all'; App.state.kat='all'; App.state.edit=true; location.hash='#/'; setTimeout(()=>location.hash='#/show/{sid}',50)"); await p.wait_for_timeout(500)
        vis = [d for d in 'LTBR' if d in dev and d in show]
        if not vis:
            t = await p.evaluate("document.querySelector('.empty h3')?.textContent||''")
            row['Hinweisseite'] = '✓' if 'Keine Abteilung' in t else '✗'
            MATRIX.append(row); log(f'   {dev}/{show}:', row); continue
        r = await p.evaluate("""(()=>{const dr=document.querySelector('[data-deptrow]'); const bar=!dr.classList.contains('hidden');
          const cnt=Object.fromEntries([...document.querySelectorAll('[data-dcnt]')].map(x=>[x.dataset.dcnt,+x.textContent]));
          const boxes=[...document.querySelectorAll('[data-setup] > [data-box], [data-setup] > .hintadd')].map(x=>x.dataset.box||'add');
          const fab=[...document.querySelectorAll('[data-fab] .fab')].map(x=>x.dataset.abt||x.textContent.trim());
          const q=[...document.querySelectorAll('[data-qrow] .qb')].map(x=>x.dataset.box);
          const kat=[...document.querySelectorAll('.katbar .kl')].map(x=>x.textContent); const katHidden=document.querySelector('.katbar').classList.contains('hidden');
          return {bar, cnt, boxes, fab, q, kat, katHidden, hs: document.documentElement.scrollWidth>innerWidth+1, short:[...document.querySelectorAll('.deptbtn .ds')].filter(x=>getComputedStyle(x).display!=='none').length}})()""")
        # Zähler gegen Karten je Abteilung
        cntok = True
        for d in vis if len(vis) > 1 else []:
            await p.evaluate(f"App.state.abt='{d}'; App.render()"); await p.wait_for_timeout(250)
            n = await p.evaluate("document.querySelectorAll('[data-list] .card').length")
            if n != r['cnt'].get(d): cntok = False; log(f'      Zähler {d}: {r["cnt"].get(d)} vs Karten {n}')
            if d == 'R':
                rb = await p.evaluate("[!!document.querySelector('[data-reqbar]'), document.querySelector('.toolbar .seg[aria-label=Darstellung]').classList.contains('hidden')]")
                await p.evaluate("App.state.abt='L' in {} ? 'L' : App.state.abt; App.state.abt=" + json.dumps([x for x in vis if x != 'R'][0] if [x for x in vis if x != 'R'] else 'R') + "; App.render()"); await p.wait_for_timeout(200)
                back = await p.evaluate("!document.querySelector('.toolbar .seg[aria-label=Darstellung]').classList.contains('hidden')")
                row['R-Leiste'] = '✓' if rb == [True, True] and (back or vis == ['R']) else '✗'
        row['Leiste'] = '✓' if r['bar'] == (len(vis) > 1) else '✗'
        row['Zähler'] = '✓' if cntok else '✗'
        exp_fab = len(vis) + 1 if len(vis) > 1 else 2
        row['Hinzufügen'] = '✓' if len(r['fab']) == exp_fab else f'✗ {r["fab"]}'
        if 'B' in vis and len(vis) == 1: row['Phasen'] = '✓' if r['katHidden'] else '✗'
        elif 'R' in vis and len(vis) == 1: row['Phasen'] = '✓' if r['katHidden'] else '✗'
        elif len(vis) > 1: row['Phasen'] = '✓' if r['kat'] == ['Alle', 'Aufbau', 'Einrichtung'] else f'✗ {r["kat"]}'
        else: row['Phasen'] = '✓' if r['kat'][2] in ('Einleuchten', 'Soundcheck') else f'✗ {r["kat"]}'
        # Kästen: nur passende Abteilungen
        wrong = [x for x in r['boxes'] if (x[-1] in 'LTBR' and x[-2:-1] == '-' and x[-1] not in vis) or (x in 'LB' and len(x) == 1 and x not in vis)]
        if vis == ['R']: wrong += [x for x in r['boxes'] if x == 'run']
        row['Kästen'] = '✓' if not wrong else f'✗ {wrong}'
        row['Schnellzugriff'] = '✓' if all((x in ('run',) or x[-1] in vis) for x in r['q'] if x) else f'✗ {r["q"]}'
        row['Smartphone'] = '✓' if not r['hs'] and (len(vis) < 4 or r['short'] == 4) else '✗'
        # Kamera-Knopf bei „Alle“ fragt nach der Abteilung
        if len(vis) > 1:
            await p.evaluate("App.state.abt='all'; App.render()"); await p.wait_for_timeout(200)
            await p.click('[data-act=quick]'); await p.wait_for_timeout(300)
            dl = await p.evaluate("[...document.querySelectorAll('.dialog .btn')].map(b=>b.textContent.trim())")
            await p.evaluate("history.back()"); await p.wait_for_timeout(300)
            row['Kamera fragt'] = '✓' if len(dl) == len(vis) + 1 else f'✗ {dl}'
        # Checkliste nur sichtbare Abteilungen
        its = await p.evaluate(f"[...new Set(RunList.items('{sid}', App.visibleDepts('{sid}')).map(i=>i.abt))]")
        row['Checkliste'] = '✓' if set(its) <= set(vis) else f'✗ {its}'
        # PDF-Dateiname / Kapitel
        pages = await p.evaluate(f"(async()=>{{await Pdf.build('{sid}',{{kat:'all',depts:App.visibleDepts('{sid}'),cover:true,compact:true}}); return Pdf.lastPages}})()")
        row['PDF'] = '✓' if pages > 1 else '✗'
        MATRIX.append(row); log(f'   {dev}/{show}:', row)
        for k, v in row.items():
            if isinstance(v, str) and v.startswith('✗'):
                bef('mittel', f'Abteilungsmatrix {dev}/{show}: {k}', v)
    CUR[0] = 'I1'
    # Abteilung abwählen und wieder wählen
    await p.evaluate("Settings.set({depts:['L','T','B','R']})")
    n0 = await p.evaluate(f"Repo.entriesOf('{sid}').length")
    await p.evaluate(f"Repo.patchShow('{sid}',{{abteilungen:['L']}})"); await p.evaluate(f"Repo.patchShow('{sid}',{{abteilungen:['L','T','B','R']}})")
    ok(await p.evaluate(f"Repo.entriesOf('{sid}').length") == n0, 'Abteilung ab- und wieder anwählen: nichts verloren')
    # Doppelte zusammenführen: Licht 17+18 und Ton 17+18 getrennt
    r = await p.evaluate(f"""(async()=>{{await Repo.saveDraft({{id:null,showId:'{sid}',abt:'L',f:{{kreis:'17+18'}},photos:{{A:[],E:[]}}}}); await Repo.saveDraft({{id:null,showId:'{sid}',abt:'T',f:{{kanal:'18 17'}},photos:{{A:[],E:[]}}}});
       return [Repo.entriesOf('{sid}').filter(e=>e.f.kreis==='17+18').length, Repo.entriesOf('{sid}').filter(e=>e.f.kanal==='18+17').length]}})()""")
    ok(r == [1, 1], 'Licht-Kreis 17+18 und Ton-Kanal 18+17 bleiben getrennt')
    # Duplizieren mit allen vier Abteilungen: Verweise zeigen auf die Kopien
    r = await p.evaluate("""(async()=>{const d=await Repo.duplicateShow('test-r-show'); const f=Repo.show(d.id).f; const es=Repo.entriesOf(d.id);
      const ab=Object.keys(f).filter(k=>k.startsWith('ra:')); const ors=Object.keys(f).filter(k=>k.startsWith('ro:')); const ps=Object.keys(f).filter(k=>k.startsWith('rp:'));
      const bad=es.filter(e=>(e.f.abschnitte||[]).some(k=>!ab.includes(k)) || (e.f.ortId && e.f.ortId.startsWith('ro:') && !ors.includes(e.f.ortId)) || (e.f.personIds||[]).some(k=>!ps.includes(k)) || (e.f.inId && !es.some(x=>x.id===e.f.inId)));
      const steps=Object.keys(f).filter(k=>k.startsWith('rs:')).map(k=>f[k]).filter(s=>s.gegenstand && !es.some(x=>x.id===s.gegenstand));
      return [es.length, Repo.entriesOf('test-r-show').length, bad.length, steps.length]})()""")
    ok(r[0] == r[1] and r[2] == 0 and r[3] == 0, f'Duplizieren: alle Verweise zeigen auf die Kopien ({r})')
    await c.close()

@section('I2')
async def i2_five(b):
    """Fünf Geräte (nur L, nur T, nur B, nur R, alle) in derselben Veranstaltung – Pakete im Kreis"""
    devs = {}
    for d in ['L', 'T', 'B', 'R', 'LTBR']:
        cx, px = await newpage(b, name='Gerät ' + d)
        await px.evaluate(f"Settings.set({{depts:{json.dumps(list(d))}, demoOnFirstStart:false}}).then(()=>Req.ensureHouse())")
        devs[d] = (cx, px)
    ALL = devs['LTBR'][1]
    await ALL.evaluate("(async()=>{await Req.testShow(); await Repo.patchShow('test-r-show',{abteilungen:['L','T','B','R'], 'z:olz1':{name:'OLZ 1',typ:'licht',ord:1,del:false}}); const l=await Cues.createList({titel:'Haus'}); await Cues.addRange(l.id,'1','3','1');})()")
    base = await pkg(ALL)
    for d in 'LTBR': await imp(devs[d][1], base)
    sid = 'test-r-show'
    marks = {}
    for d in 'LTBR':
        P = devs[d][1]
        marks[d] = await P.evaluate(f"""(async()=>{{const abt='{d}'; const f=abt==='L'?{{kreis:'7{d}'}}:abt==='T'?{{kanal:'7'}}:abt==='B'?{{zug:'Pos {d}'}}:{{was:'Ding {d}'}};
          const r=await Repo.saveDraft({{id:null,showId:'{sid}',abt,f,photos:{{A:[],E:[]}}}});
          const zp={{['ci:{d}']:{{abt,text:'Punkt {d}',ord:1,del:false}}}}; if(abt==='L'||abt==='B') zp['z:olz1']=Repo.zugValue('{sid}','olz1',abt==='L'?{{bestueckung:'6× PC'}}:{{last:'200 kg'}});
          await Repo.patchShow('{sid}',zp);
          const run=RunList.runsOf('{sid}').find(r=>r.f.datum===RunList.isoDate()) || await RunList.create('{sid}'); await RunList.toggle(run.id,'ci:{d}');
          const l=Cues.lists()[0]; const c=Cues.newCue(l.id,'1{d}'); await Repo._write({{cues:[c]}}); return [r.entryId, c.id, run.id]}})()""")
        await P.wait_for_timeout(20)
    ents = [m[0] for m in marks.values()]; cues = [m[1] for m in marks.values()]
    # 1) im Kreis: L → T → B → R → ALL → L … (je komplett mit eigenen Abteilungen, wie das Teilen-Menü)
    order = ['L', 'T', 'B', 'R', 'LTBR', 'L', 'T', 'B', 'R', 'LTBR']
    for a, bb in zip(order, order[1:]): await full_sync(devs[a][1], devs[bb][1])
    ring = await ALL.evaluate("ents => ents.map(i=>!!Repo.entries.get(i))", ents)
    log(f'   Nach dem Kreis hat das Alle-Gerät die Einträge L,T,B,R: {ring}')
    if not all(ring):
        bef('mittel', 'Pakete im Kreis: Das Alle-Gerät bekommt die Einträge der Abteilungsgeräte nicht (Weitergabe nur der eigenen Abteilung)',
            f'L → T → B → R → Alle → L … (zweimal herum, jeweils „Komplett“): Danach hat das Alle-Gerät nur die Einträge von R ({ring}). Jedes Einzelgerät gibt nur seine Abteilung weiter (dokumentiert), '
            'also kommt Licht nie über Ton hinaus. Verloren ist nichts – die Daten liegen noch auf dem Ursprungsgerät –, aber alle Geräte zeigen „Synchron“. '
            'Funktioniert nur sternförmig über das Alle-Gerät (siehe nächste Prüfung). Im Haus muss das als feste Regel dastehen.', art='dokumentiert')
    # 2) sternförmig: jedes Einzelgerät → Alle, danach Alle → jedes Einzelgerät
    for d in 'LTBR': await full_sync(devs[d][1], ALL)
    for d in 'LTBR': await full_sync(ALL, devs[d][1])
    res = {}
    for d, (cx, P) in devs.items():
        res[d] = await P.evaluate(f"""(([ents,cues])=>({{e: ents.map(i=>!!Repo.entries.get(i)), c: cues.map(i=>!!Repo.cues.get(i)), runs: RunList.runsOf('{sid}').length,
          haken: RunList.runsOf('{sid}').map(r=>Object.keys(r.f).filter(k=>k.startsWith('h:')).length), zug: Repo.show('{sid}').f['z:olz1']}}))""", [ents, cues])
        log(f'   {d}:', res[d])
    a = res['LTBR']
    ok(all(a['e']) and all(a['c']), 'Sternförmig: Alle-Gerät hat alle Einträge und Cues aller Geräte')
    ok(all(all(r['c']) for r in res.values()), 'Cue-Fotos überall vollständig')
    own = all(r['e'][i] for i, d in enumerate('LTBR') for k, r in res.items() if d in k)
    ok(own, 'Sternförmig: jedes Gerät hat seine Abteilung vollständig')
    log(f'   Fremde Einträge auf Einzelgeräten (nur gespeichert, nicht angezeigt): ' + str({k: r['e'] for k, r in res.items()}))
    ok(a['runs'] == 1, f'Ein Durchgang für heute auf dem Alle-Gerät ({a["runs"]}, Haken {a["haken"]})')
    if a['runs'] > 1:
        bef('hoch', 'Fünf-Geräte-Betrieb: jedes Abteilungsgerät erzeugt beim ersten Haken einen eigenen Durchgang',
            f'Licht, Ton, Bühne und Requisite haken unabhängig ab (je erster Haken legt still einen Durchgang an). Auf dem Alle-Gerät gibt es danach {a["runs"]} Durchgänge für heute mit je {a["haken"]} Haken; '
            'angezeigt wird nur einer. Ein vollständiges Protokoll der Vorstellung gibt es nicht. (Siehe C2.)')
    ok(a['zug'].get('bestueckung') == '6× PC' and a['zug'].get('last') == '200 kg', f'Gemeinsamer Zug: Licht-Bestückung und Bühnen-Last beide da ({a["zug"]})')
    for d, (cx, P) in devs.items(): await cx.close()

# =====================================================================================
# H. Bildschirmfotos (Matrix) und Galerie
# =====================================================================================
SHOTS = []
async def shot(p, name, group, cap, full=False):
    path = f'{OUT}/screens/{name}.png'
    try:
        await p.screenshot(path=path, full_page=full); SHOTS.append((group, name, cap))
    except Exception as ex: log('    Screenshot fehlgeschlagen', name, str(ex)[:80])

@section('H1')
async def h1_screens(b):
    """Bildschirmfoto-Matrix: Themes × Geräte für die wichtigsten Ansichten"""
    devices = [('phone', 390, 844), ('phonequer', 844, 390), ('ipadhoch', 820, 1180), ('ipadquer', 1180, 820), ('desktop', 1440, 900)]
    themes = [('dunkel', {'theme': 'dark'}), ('hell', {'theme': 'light'}), ('rot', {'theme': 'red', 'redPhotos': True}), ('rotOhneFoto', {'theme': 'red', 'redPhotos': False}), ('dimmer40', {'theme': 'dark', 'dim': 40})]
    for tn, tset in themes:
        for dn, w, h in devices:
            if tn not in ('dunkel', 'rot') and dn not in ('phone', 'ipadquer'): continue
            c, p = await newpage(b, w, h, name=f'{tn}-{dn}')
            await p.evaluate(f"Settings.set(Object.assign({json.dumps(tset)},{{depts:['L','T','B','R']}})).then(()=>Req.ensureHouse()).then(()=>Req.testShow())")
            hai = await p.evaluate("Repo.liveShows().find(s=>s.f.titel.startsWith('Demo: Der Haifisch')).id")
            await p.evaluate(f"Repo.patchShow('{hai}',{{abteilungen:['L','T','B','R'], spielstaette:'Großes Haus'}})")
            suf = f'{tn}_{dn}'
            await p.evaluate("location.hash='#/'; App.render()"); await p.wait_for_timeout(400); await shot(p, f'startseite_alle_{suf}', 'Startseite', f'Startseite · {tn} · {dn}')
            await p.evaluate(f"location.hash='#/show/{hai}'; App.state.abt='all'; App.state.edit=false; App.render()"); await p.wait_for_timeout(500)
            await shot(p, f'liste_LTBR_{suf}', 'Veranstaltung Liste', f'Liste alle Abteilungen · {tn} · {dn}')
            await p.evaluate("App.state.abt='L'; App.render(); window.scrollTo(0, 900)"); await p.wait_for_timeout(300); await shot(p, f'liste_L_gescrollt_{suf}', 'Veranstaltung Liste', f'Licht gescrollt (fixierte Leisten) · {tn} · {dn}')
            await p.evaluate("window.scrollTo(0,0); Settings.set({view:'big'}).then(()=>App.render())"); await p.wait_for_timeout(500)
            await p.evaluate("window.scrollTo(0, 1300)"); await p.wait_for_timeout(400); await shot(p, f'grossbild_L_gescrollt_{suf}', 'Großbild', f'Großbild Licht gescrollt · {tn} · {dn}')
            await p.evaluate("window.scrollTo(0,0); Settings.set({view:'grid'}).then(()=>App.render())"); await p.wait_for_timeout(400); await shot(p, f'kacheln_L_{suf}', 'Kacheln', f'Kacheln Licht · {tn} · {dn}')
            await p.evaluate("Settings.set({view:'list'}).then(()=>{App.state.edit=true; App.state.abt='all'; App.render()})"); await p.wait_for_timeout(400); await shot(p, f'bearbeiten_LTBR_{suf}', 'Bearbeitungsmodus', f'Bearbeitungsmodus alle · {tn} · {dn}')
            await p.evaluate("location.hash='#/show/test-r-show'; App.state.abt='R'; App.state.edit=false; Settings.set({reqView:'einrichten'}).then(()=>App.render())"); await p.wait_for_timeout(500)
            await shot(p, f'requisite_einrichten_{suf}', 'Requisite', f'Requisite Einrichten · {tn} · {dn}')
            await p.evaluate("Settings.set({reqView:'ablauf'}).then(()=>App.render())"); await p.wait_for_timeout(400); await shot(p, f'requisite_ablauf_{suf}', 'Requisite', f'Requisite Ablauf · {tn} · {dn}')
            await p.evaluate(f"Editor.open({{showId:'{hai}', entryId:Repo.entriesOf('{hai}').find(e=>e.f.kreis==='45').id}})"); await p.wait_for_timeout(400)
            await shot(p, f'editor_L_{suf}', 'Editor', f'Editor Licht · {tn} · {dn}')
            await p.evaluate("history.back()"); await p.wait_for_timeout(300)
            if tn in ('dunkel', 'rot') and dn in ('phone', 'ipadquer'):
                # Kamera (Doku) und Cue-Kamera, Lightbox
                await p.evaluate(f"location.hash='#/show/{hai}'; App.state.abt='L'; App.state.edit=true; App.render()"); await p.wait_for_timeout(300)
                await p.evaluate(f"Editor.open({{showId:'{hai}', abt:'L'}})"); await p.wait_for_timeout(300)
                await p.click('[data-editor] .pk[data-k=A] [data-act=cam]')
                try: await p.wait_for_function("document.querySelector('.cam video') && document.querySelector('.cam video').videoWidth>0", timeout=10000)
                except Exception: pass
                await p.evaluate("document.querySelector('.cam .flash').classList.add('go')"); await p.wait_for_timeout(80)
                await shot(p, f'kamera_doku_{suf}', 'Kamera', f'Doku-Kamera (Auslöse-Blitz sichtbar) · {tn} · {dn}')
                await p.click('.cam [data-a=close]'); await p.wait_for_timeout(200); await p.evaluate("history.back()"); await p.wait_for_timeout(300)
                lid = await p.evaluate("(async()=>{const l=await Cues.createList({titel:'Screens',spielstaette:'Großes Haus'}); await Cues.addRange(l.id,'1','6','1'); return l.id})()")
                await p.evaluate(f"App.state.edit=true; location.hash='#/cue/{lid}'"); await p.wait_for_timeout(400); await shot(p, f'cueliste_{suf}', 'Cue-Fotos', f'Cue-Liste · {tn} · {dn}')
                await p.click('[data-cact=cam]')
                try: await p.wait_for_function("document.querySelector('.ccam video') && document.querySelector('.ccam video').videoWidth>0", timeout=10000)
                except Exception: pass
                await p.click('.ccam [data-a=shot]'); await p.wait_for_timeout(600); await shot(p, f'kamera_cue_{suf}', 'Kamera', f'Cue-Kamera · {tn} · {dn}')
                await p.click('.ccam [data-a=close]'); await p.wait_for_timeout(500)
                await p.evaluate(f"location.hash='#/show/{hai}'; App.state.edit=false; App.state.abt='L'; App.render()"); await p.wait_for_timeout(400)
                await p.evaluate(f"(async()=>{{const e=Repo.entriesOf('{hai}').find(e=>e.f.kreis==='10127'); await Repo._write({{entries:[Rec.patch(e,{{bemerkung:'Sehr lange Bemerkung. '.repeat(40)}})]}}); App.openLightbox(e.id,'A',0)}})()"); await p.wait_for_timeout(700)
                await shot(p, f'lightbox_lang_{suf}', 'Lightbox', f'Lightbox lange Bemerkung · {tn} · {dn}')
                await p.evaluate("history.back()"); await p.wait_for_timeout(300)
                await p.evaluate(f"RunList.open('{hai}')"); await p.wait_for_timeout(400); await shot(p, f'checkliste_{suf}', 'Checkliste', f'Vorstellungs-Checkliste · {tn} · {dn}')
                await p.evaluate("history.back(); setTimeout(()=>Ui.confirm('Veranstaltung löschen?','„Der Haifisch“ mit 9 Einträgen wird gelöscht.','Löschen',true),100)"); await p.wait_for_timeout(500)
                await shot(p, f'dialog_loeschen_{suf}', 'Dialoge', f'Lösch-Dialog · {tn} · {dn}')
                await p.evaluate("history.back(); setTimeout(()=>{Ui.toast('Gespeichert'); Ui.toast('Speichern fehlgeschlagen','err',{ms:9000})},100)"); await p.wait_for_timeout(500)
                await shot(p, f'toasts_{suf}', 'Dialoge', f'Toasts · {tn} · {dn}')
                await p.evaluate("SettingsView.open()"); await p.wait_for_timeout(400); await shot(p, f'einstellungen_{suf}', 'Blätter', f'Einstellungen · {tn} · {dn}')
                await p.evaluate("history.back(); setTimeout(()=>DiagView.open(),100)"); await p.wait_for_timeout(700); await shot(p, f'diagnose_{suf}', 'Blätter', f'Diagnose · {tn} · {dn}')
                await p.evaluate("history.back(); setTimeout(()=>SyncView.open(),100)"); await p.wait_for_timeout(500); await shot(p, f'abgleich_{suf}', 'Blätter', f'Abgleich · {tn} · {dn}')
                await p.evaluate("history.back(); setTimeout(()=>PeerView.open(),100)"); await p.wait_for_timeout(500); await shot(p, f'live_wahl_{suf}', 'Blätter', f'Live verbinden · {tn} · {dn}')
                await p.evaluate("history.back()"); await p.wait_for_timeout(300)
                await p.evaluate(f"App.pdf('{hai}')"); await p.wait_for_timeout(400); await shot(p, f'pdfdialog_{suf}', 'Blätter', f'PDF-Dialog · {tn} · {dn}')
                await p.evaluate("history.back()"); await p.wait_for_timeout(300)
                await p.evaluate(f"App.state.edit=true; App.render(); SetupView.editP('{hai}')"); await p.wait_for_timeout(400); await shot(p, f'positionen_edit_{suf}', 'Blätter', f'Züge & Positionen bearbeiten · {tn} · {dn}')
                await p.evaluate("history.back(); setTimeout(()=>Req.editStep('test-r-show','rs:test-s04'),100)"); await p.wait_for_timeout(500); await shot(p, f'requisite_schritt_{suf}', 'Blätter', f'Requisite Schritt bearbeiten · {tn} · {dn}')
                await p.evaluate("history.back()"); await p.wait_for_timeout(300)
                await p.evaluate("Ui.busy('PDF wird erstellt … Seite 3 / 40')"); await p.wait_for_timeout(200); await shot(p, f'busy_{suf}', 'Dialoge', f'Busy-Anzeige · {tn} · {dn}')
                await p.evaluate("document.querySelector('.busyov').remove()")
            await c.close()
    # Boot-Seiten
    c, p = await newpage(b, 390, 844, name='boot')
    await p.evaluate("Boot.started=false; Boot.fail('TypeError: x is undefined\\nindex.html:1234')"); await shot(p, 'boot_fail_phone', 'Start', 'Startfehler (Boot.fail)')
    await p.evaluate("Boot.wait()"); await shot(p, 'boot_wait_phone', 'Start', 'Datenspeicher antwortet nicht (Boot.wait)')
    await c.close()

@section('H2')
async def h2_css(b):
    """Feste Farbwerte, Rotlicht in Kamera/Lightbox, Farbenblind-Simulation"""
    c, p = await newpage(b, 390, 844, name='H2')
    await p.evaluate("Settings.set({theme:'red'})")
    hai = await p.evaluate("Repo.liveShows().find(s=>s.f.titel.startsWith('Demo: Der Haifisch')).id")
    await p.evaluate(f"App.state.edit=true; location.hash='#/show/{hai}'"); await p.wait_for_timeout(400)
    await p.evaluate(f"Editor.open({{showId:'{hai}', abt:'L'}})"); await p.wait_for_timeout(300)
    await p.click('[data-editor] .pk[data-k=A] [data-act=cam]'); await p.wait_for_timeout(1200)
    r = await p.evaluate("""(()=>{const cs=s=>{const e=document.querySelector(s); return e?getComputedStyle(e):null};
      return {shutter: cs('.cam .shutter')?.backgroundColor, fertig: cs('.cam .tbtn.done')?.backgroundColor, text: cs('.cam .ttl')?.color, flash: cs('.cam .vf .flash')?.display === 'none' ? 'ausgeblendet' : cs('.cam .vf .flash')?.backgroundColor, hint: cs('.cam .hintlbl')?.color}})()""")
    log('   Doku-Kamera im Rotlicht:', r)
    white = [k for k, v in r.items() if v and re.search(r'rgb\(2[2-5]\d, 2[2-5]\d, 2[2-5]\d', v)]
    if white:
        bef('hoch', 'Doku-Kamera ignoriert den Rotlicht-Modus: weißer Auslöser, weiße Schrift und weißes Aufblitzen',
            f'Im Rotlicht sind in der Doku-Kamera weiß: {", ".join(white)} ({r}). Der 84-px-Auslöser ist eine weiße Scheibe, „Fertig“ ein weißer Knopf, '
            'und jede Aufnahme blitzt den Sucher weiß auf (.flash, 60 % Deckkraft). Die Cue-Kamera wurde dafür eigens dunkel gebaut, die Doku-Kamera nicht – '
            'gerade beim Einleuchten im dunklen Saal wird sie benutzt. Siehe Bild kamera_doku_rot_phone.png.')
    await p.click('.cam [data-a=close]'); await p.evaluate("history.back()"); await p.wait_for_timeout(300)
    await p.evaluate(f"(()=>{{const e=Repo.entriesOf('{hai}').find(e=>e.f.kreis==='361'); App.openLightbox(e.id,'A',0)}})()"); await p.wait_for_timeout(500)
    r = await p.evaluate("(()=>{const cs=s=>{const e=document.querySelector(s); return e?getComputedStyle(e).color:null}; return {kreis:cs('.lbx .infos .kreis'), note:cs('.lbx .infos .note'), pos:cs('.lbx .pos'), nextk:cs('.lbx .nextk')}})()")
    log('   Lightbox im Rotlicht:', r)
    if any(v and v.startswith('rgb(255, 255, 255') for v in r.values()):
        bef('mittel', 'Bildansicht (Lightbox) zeigt im Rotlicht weiße Schrift und Knöpfe',
            f'Das Foto wird rot eingefärbt, die Einblendung bleibt weiß ({r}). Kreis 44 px weiß auf Schwarz – im dunklen Saal blendend. Ebenso Markieren (Annotator: weißer „Übernehmen“-Knopf).')
    await p.evaluate("history.back()"); await p.wait_for_timeout(200)
    # Farbenblind-Simulation (Deuteranopie) auf Liste und Großbild
    await p.evaluate("Settings.set({theme:'dark', depts:['L','T','B']}).then(()=>{App.state.edit=false; App.state.abt='all'; App.render()})"); await p.wait_for_timeout(300)
    await p.add_style_tag(content="""svg#cb{position:absolute;width:0;height:0} html.deut body{filter:url(#deut)} html.prot body{filter:url(#prot)}""")
    await p.evaluate("""document.body.insertAdjacentHTML('beforeend','<svg id=cb><filter id=deut><feColorMatrix type=matrix values=\"0.625 0.375 0 0 0 0.7 0.3 0 0 0 0 0.3 0.7 0 0 0 0 0 1 0\"/></filter><filter id=prot><feColorMatrix type=matrix values=\"0.567 0.433 0 0 0 0.558 0.442 0 0 0 0 0.242 0.758 0 0 0 0 0 1 0\"/></filter></svg>')""")
    for f in ('deut', 'prot'):
        await p.evaluate(f"document.documentElement.classList.add('{f}')"); await p.wait_for_timeout(200)
        await shot(p, f'farbenblind_{f}_liste_LTB_dunkel_phone', 'Farbenblind', f'{"Deuteranopie" if f=="deut" else "Protanopie"} · Liste')
        await p.evaluate("Settings.set({view:'big'}).then(()=>App.render())"); await p.wait_for_timeout(300); await p.evaluate("scrollTo(0,700)"); await p.wait_for_timeout(200)
        await shot(p, f'farbenblind_{f}_grossbild_LTB_dunkel_phone', 'Farbenblind', f'{"Deuteranopie" if f=="deut" else "Protanopie"} · Großbild')
        await p.evaluate(f"scrollTo(0,0); document.documentElement.classList.remove('{f}'); Settings.set({{view:'list'}}).then(()=>App.render())")
    await c.close()

# =====================================================================================
# Ergänzungen für 2.8.2 und bisher nicht abgedeckte Fälle
# =====================================================================================
@section('D4')
async def d4_282(b):
    """2.8.2: Schnellauswahl beim Anlegen und ±0,1 in der Cue-Kamera – Rechenregeln, Randfälle, Warteschlange, Bildschirmgrößen"""
    c, p = await newpage(b, name='D4')
    r = await p.evaluate("""(()=>{const bad=[]; for(let i=0;i<=3000;i++){ const s=(i/100).toFixed(2); for(const d of [1,-1]){ const n=Cues.stepNr(s,d); if(n===null) continue;
        if(!/^\\d+(\\.\\d{1,2})?$/.test(n)) bad.push(s+'→'+n); const exp=Math.round((parseFloat(s)+d*0.1)*100)/100; if(Math.abs(parseFloat(n)-exp)>1e-9) bad.push(s+(d>0?'+':'-')+'→'+n); } }
      return [bad.length, bad.slice(0,6), Cues.stepNr('007',1), Cues.stepNr('13.10',1), Cues.stepNr('Q13',1), Cues.stepNr('12,5',-1), Cues.stepNr('999.9',1), Cues.stepNr('0.05',-1), Cues.stepNr('',1)]})()""")
    log('   ±0,1 über 0,00 … 30,00 in beiden Richtungen:', r)
    ok(r[0] == 0 and r[2:] == ['7.1', '13.2', '13.1', '12.4', '1000', None, None], 'stepNr: 6002 Werte ohne Rundungsfehler, 007/13.10/Q13/12,5 normalisiert, nicht unter 0')
    r = await p.evaluate("""(async()=>{const res={};
      const a=await Cues.createList({titel:'Rückwärts'}); await Cues.addRange(a.id,'40','1','1'); res.rueck=Cues.quickNrs(a.id);
      const t=await Cues.createList({titel:'Nur Text'}); await Repo._write({cues:[Cues.newCue(t.id,'Ende'),Cues.newCue(t.id,'Pause')]}); res.text=Cues.quickNrs(t.id);
      const m=await Cues.createList({titel:'Text zuletzt'}); await Cues.addRange(m.id,'1','20','1'); await new Promise(r=>setTimeout(r,5)); await Repo._write({cues:[Cues.newCue(m.id,'Ende')]}); res.textzuletzt=Cues.quickNrs(m.id);
      const g=await Cues.createList({titel:'Groß'}); await Repo._write({cues:[Cues.newCue(g.id,'998.5')]}); res.gross=Cues.quickNrs(g.id);
      return res})()""")
    log('   Schnellauswahl:', json.dumps(r, ensure_ascii=False))
    ok(r['rueck']['next'] == ['41', '42', '43'] and r['text']['next'] == ['1', '2', '3'] and r['textzuletzt']['base'] == 20 and r['gross']['next'] == ['999', '1000', '1001'],
       'Schnellauswahl: Rückwärts angelegt → 41–43; nur Text-Cues → 1–3; Text-Cue zuletzt → Basis bleibt 20; 998.5 → 999–1001')
    # Zeitstempel eines anderen Geräts mit vorgehender Uhr: „zuletzt angelegt“ hängt fest
    cA, A = await newpage(b, name='D4-Uhr+1d', off=86400000); cB, B = await newpage(b, name='D4-B')
    lid = await A.evaluate("(async()=>{const l=await Cues.createList({titel:'Uhr'}); await Cues.addRange(l.id,'1','5','1'); await Repo._write({cues:[Cues.newCue(l.id,'3.5')]}); return l.id})()")
    await imp(B, await pkg(A))
    await B.evaluate(f"(async()=>{{await Cues.addRange('{lid}','6','20','1')}})()")
    await B.evaluate(f"App.state.edit=true; location.hash='#/cue/{lid}'"); await B.wait_for_timeout(400)
    await B.click('[data-cact=addcue]'); await B.wait_for_timeout(300)
    r = await B.evaluate("[document.querySelector('[data-editor] [name=nr]').value, [...document.querySelectorAll('.pickkeys button')].map(b=>b.textContent).join(' '), document.querySelector('[data-editor]').innerText.match(/Zuletzt angelegt: Cue [^\\n]+/)?.[0]]")
    log('   Gerät B nach Abgleich mit Uhr +1 Tag, dann 6–20 selbst angelegt:', r)
    await shot(B, 'cue_neu_uhrversatz_dunkel_ipadquer', 'Cue-Fotos', 'Neue Cue nach Abgleich mit Gerät, dessen Uhr 1 Tag vorgeht')
    ok(r[2] and r[2].endswith('Cue 20'), f'Schnellauswahl geht von der zuletzt auf diesem Gerät angelegten Cue aus ({r[2]})')
    if not (r[2] and r[2].endswith('Cue 20')):
        bef('niedrig', 'Schnellauswahl „+ Cue“ hängt an einer Cue fest, die ein Gerät mit (mehr als 24 h) vorgehender Uhr angelegt hat',
            f'Gerät A (Uhr gut 1 Tag vor) legt Cue 3.5 an, Gerät B gleicht ab und legt danach selbst 6–20 an. „+ Cue“ auf B schlägt zwar „{r[0]}“ vor, zeigt aber „{r[2]}“ und bietet nur {r[1]} an – statt 21–23 und 20.1–20.9. '
            'Ursache: Cues.quickNrs nimmt die Cue mit dem größten Anlege-Zeitstempel (c), und der stammt von der Uhr des anderen Geräts. Bleibt so, bis die echte Zeit ihn einholt. '
            'Bei weniger als 24 h Versatz passt Clock.observe die eigene Uhr an – dann tritt es nicht auf.')
    await B.evaluate("history.back()"); await cA.close(); await cB.close()
    # Kamera: ±0,1 zwischen Aufnahmen bei langsamer Warteschlange → jedes Foto bei der richtigen Cue
    lid = await p.evaluate("(async()=>{const l=await Cues.createList({titel:'Race'}); await Cues.addRange(l.id,'12','14','1'); const d=Cues.newCue(l.id,'13.5'); await Repo._write({cues:[d]}); await Cues.deleteCue(d.id); return l.id})()")
    await p.evaluate(f"App.state.edit=true; location.hash='#/cue/{lid}'"); await p.wait_for_timeout(400)
    c13 = await p.evaluate(f"Cues.cueByNr('{lid}','13').id")
    await p.evaluate(f"void CueCam.open({{listId:'{lid}', cueId:'{c13}'}})")
    await p.wait_for_function("document.querySelector('.ccam video') && document.querySelector('.ccam video').videoWidth>0", timeout=15000)
    await p.evaluate("window.__fc = Photo.fromCanvas.bind(Photo); Photo.fromCanvas = async (...a) => { await new Promise(r=>setTimeout(r,300)); return __fc(...a); }; 1")
    for a in ['shot', 'nr+', 'shot', 'shot', 'nr+', 'shot', 'nr-', 'nr-', 'shot', 'next', 'nr-', 'shot', 'nr-', 'shot']:
        await p.click(f'.ccam [data-a="{a}"]')
    for _ in range(5): await p.click('.ccam [data-a="nr+"]')     # 12.9 → 13.4
    await p.click('.ccam [data-a="nr+"]')                           # 13.5 (gelöscht)
    await p.click('.ccam [data-a=shot]')
    await p.wait_for_function('CueCam.pending()===0 && !CueCam.busy', timeout=30000)
    await p.click('.ccam [data-a=close]'); await reload(p)
    r = await p.evaluate(f"Cues.cuesOf('{lid}').map(c=>c.f.nr+':'+Cues.imgsOf(c.id).length).join(' ')")
    log('   Nach ±0,1-Folge mit langsamer Warteschlange und Neuladen:', r)
    ok(r == '12:0 12.9:1 13:3 13.1:3 13.2:1 13.5:1 14:0', f'Jedes Foto bei der angezeigten Cue; gelöschte 13.5 wird neu angelegt, nicht wiederbelebt ({r})')
    # Bildschirmgrößen: Schnellauswahl und Kamera
    VIS = """(()=>{const g=s=>{const e=document.querySelector(s); const r=e.getBoundingClientRect(); return [Math.round(r.width),Math.round(r.height), r.bottom<=innerHeight+0.5&&r.right<=innerWidth+0.5&&r.top>=-0.5&&r.left>=-0.5]};
       return {vf:g('.ccam .vf'), shutter:g('.ccam .shutter'), next:g('.ccam .cnext'), plus:g('.ccam [data-a="nr+"]'), minus:g('.ccam [data-a="nr-"]'), nr:g('.ccam .cnr')}})()"""
    tiny = []
    for (w, h, nm) in [(390, 844, 'phone'), (844, 390, 'phonequer'), (915, 412, 'pixel8quer'), (667, 375, 'kleinquer'), (320, 568, 'se1'), (1180, 820, 'ipadquer'), (1280, 800, 'samsungquer')]:
        c2, p2 = await newpage(b, w, h, name=f'D4-{nm}')
        l2 = await p2.evaluate("(async()=>{const l=await Cues.createList({titel:'Größe'}); await Cues.addRange(l.id,'1','13','1'); return l.id})()")
        await p2.evaluate(f"App.state.edit=true; location.hash='#/cue/{l2}'"); await p2.wait_for_timeout(400)
        await p2.click('[data-cact=addcue]'); await p2.wait_for_timeout(300)
        pk = await p2.evaluate("(()=>{const rs=[...document.querySelectorAll('.pickkeys button')].map(b=>b.getBoundingClientRect()); return [rs.length, Math.round(Math.min(...rs.map(r=>r.height))), Math.round(Math.min(...rs.map(r=>r.width))), document.documentElement.scrollWidth<=innerWidth+1]})()")
        await shot(p2, f'cue_neu_schnellauswahl_dunkel_{nm}', 'Cue-Fotos', f'„+ Cue“ mit Schnellauswahl · {nm} {w}×{h}')
        await p2.evaluate("history.back()"); await p2.wait_for_timeout(300)
        await p2.click('[data-cact=cam]')
        await p2.wait_for_function("document.querySelector('.ccam video') && document.querySelector('.ccam video').videoWidth>0", timeout=15000); await p2.wait_for_timeout(300)
        v = await p2.evaluate(VIS)
        await shot(p2, f'kamera_cue_pm01_dunkel_{nm}', 'Kamera', f'Cue-Kamera mit ±0.1 · {nm} {w}×{h}')
        log(f'   {nm} {w}×{h}: Schnellauswahl {pk} · Kamera {v}')
        ok(pk[0] == 12 and pk[1] >= 44 and pk[3], f'{nm}: Schnellauswahl 12 Knöpfe ≥ 44 px, kein waagrechtes Scrollen')
        ok(all(x[2] for x in v.values()) and v['plus'][1] >= 44, f'{nm}: Auslöser, ±0.1, Nächster Cue, Nummer im Bild')
        if v['vf'][0] < 150: tiny.append(f'{nm} {w}×{h}: Sucher {v["vf"][0]}×{v["vf"][1]} px')
        await c2.close()
    ok(not tiny, 'Sucher der Cue-Kamera überall mindestens 150 px')
    if tiny:
        bef('hoch', 'Cue-Kamera im Querformat auf dem Smartphone: Sucher schrumpft auf einen Punkt',
            'Gemessen: ' + '; '.join(tiny) + '. CSS .ccam .vf { width: min(100vw, calc(100dvh − 420px)) } – bei 390–412 px Bildschirmhöhe wird das negativ, übrig bleibt der 12-px-Rahmen. '
            'Man fotografiert blind; die Bilder entstehen zwar, aber ob die Bühne drauf ist, sieht man erst in der Liste. Vom Stellwerk/FOH halten viele das Telefon quer. '
            'Die Doku-Kamera hat das Problem nicht. Bilder: kamera_cue_pm01_dunkel_phonequer.png, …_pixel8quer.png.')
    await c.close()

@section('B10')
async def b10_hugets(b):
    """Zeitstempel jenseits 2^53 (z. B. 1e308) aus einem Paket: friert das Feld ein?"""
    cA, A = await newpage(b, name='B10-A'); cB, B = await newpage(b, name='B10-B')
    await imp(B, await pkg(A))
    hai = await A.evaluate("Repo.liveShows().find(s=>s.f.titel.startsWith('Demo: Der Haifisch')).id")
    rec = await A.evaluate(f"JSON.parse(JSON.stringify(Repo.shows.get('{hai}')))")
    rec['f']['titel'] = 'Von außen'; rec['t']['titel'] = 1e308; rec['mod'] = 1e308
    st = await imp(A, json.dumps({'format': 'lichtdoku', 'type': 'sync', 'formatVersion': 2, 'shows': [rec], 'entries': [], 'photos': [], 'blobs': []}))
    log('   Import:', {k: st.get(k) for k in ('neu', 'geaendert', 'ungueltig')} if isinstance(st, dict) else st)
    await A.evaluate(f"Repo.patchShow('{hai}',{{titel:'Zauberflöte'}})")
    a1 = await A.evaluate(f"[Repo.show('{hai}').f.titel, Repo.show('{hai}').t.titel, Sync.pending(), Sync.status().label]")
    await B.evaluate(f"Repo.patchShow('{hai}',{{titel:'Zauberflöte (B)'}})")
    await imp(B, await pkg(A)); await imp(A, await pkg(B))
    a2 = await A.evaluate(f"Repo.show('{hai}').f.titel"); b2 = await B.evaluate(f"Repo.show('{hai}').f.titel")
    await B.evaluate(f"Repo.patchShow('{hai}',{{titel:'Später auf B'}})"); await imp(A, await pkg(B))
    a3 = await A.evaluate(f"[Repo.show('{hai}').f.titel, Sync.pending(), Sync.status().label]")
    await imp(B, await pkg(A)); await A.evaluate("Sync.state.lastSyncAt=Date.now()")
    log(f'   A nach Umbenennen: {a1}; nach Abgleich A „{a2}“ / B „{b2}“; B ändert später → A {a3}')
    ok(a3[0] == 'Später auf B', 'Jüngste Änderung (später auf B) gewinnt trotz Zeitstempel 1e308')
    if a3[0] != 'Später auf B' or a3[1] > 0:
        bef('niedrig', 'Zeitstempel ≥ 2^53 aus einem Paket werden angenommen und frieren das Feld ein',
            f'Rec.valid prüft nur „endlich und ≥ 0“. Ein Paket mit t = 1e308 für den Titel wird übernommen. Danach: eigene Änderung auf A bekommt t = 1e308 + 1 = 1e308 (Gleitkomma), '
            f'beim Abgleich entscheidet nur noch der Textvergleich; eine spätere Änderung auf B kommt auf A nicht an (A zeigt „{a3[0]}“), und A zeigt dauerhaft „{a3[2]}“ ({a3[1]} offen). '
            'Nur über präparierte/kaputte Pakete erreichbar – aber dann für immer. Grenze z. B. „t ≤ jetzt + 1 Jahr“ beim Import.')
    await cA.close(); await cB.close()

@section('C4')
async def c4_dst(b):
    """Zeitumstellung 25.10.2026 (Ende der Sommerzeit): Durchgang über 02:00–03:00 hinweg"""
    import datetime
    from zoneinfo import ZoneInfo
    utc = datetime.timezone.utc
    t1 = datetime.datetime(2026, 10, 24, 23, 50, tzinfo=utc).timestamp() * 1000      # 01:50 MESZ
    c, p = await newpage(b, name='C4', off=int(t1 - time.time() * 1000))
    hai = await p.evaluate("Repo.liveShows().find(s=>s.f.titel.startsWith('Demo: Der Haifisch')).id")
    await p.evaluate("Settings.set({depts:['L','T','B']})")
    await p.evaluate(f"location.hash='#/show/{hai}'"); await p.wait_for_timeout(400); await open_run(p)
    await p.click('[data-box=run] [data-run=start]'); await p.wait_for_timeout(300)
    keys = await p.evaluate("[...document.querySelectorAll('[data-box=run] .runchk')].map(b=>b.dataset.run)")
    times = [datetime.datetime(2026, 10, 24, 23, 55, tzinfo=utc), datetime.datetime(2026, 10, 25, 0, 30, tzinfo=utc), datetime.datetime(2026, 10, 25, 1, 10, tzinfo=utc), datetime.datetime(2026, 10, 25, 2, 5, tzinfo=utc)]
    shown = []
    for i, tt in enumerate(times[:min(4, len(keys))]):
        await p.evaluate(f"__setOff({int(tt.timestamp()*1000 - time.time()*1000)})")
        await p.click(f'[data-box=run] .runchk[data-run="{keys[i]}"]'); await p.wait_for_timeout(250)
        shown.append(await p.evaluate("new Date().toLocaleTimeString('de-DE',{hour:'2-digit',minute:'2-digit'})"))
    runs = await p.evaluate(f"RunList.runsOf('{hai}').map(r=>[r.f.datum, Object.keys(r.f).filter(k=>k.startsWith('h:')).length])")
    log('   Uhrzeiten beim Abhaken (Ortszeit):', shown, 'Durchgänge:', runs)
    ok(len(runs) == 1 and runs[0][1] == len(shown), 'Über die Zeitumstellung hinweg ein Durchgang mit allen Haken')
    await p.evaluate(f"RunList.open('{hai}')"); await p.wait_for_timeout(400)
    txt = await p.evaluate("document.querySelector('.sheet').innerText")
    await shot(p, 'checkliste_zeitumstellung_dunkel_ipadquer', 'Checkliste', 'Protokoll über die Zeitumstellung (02:30 MESZ, dann 02:10 MEZ)')
    rid = await p.evaluate(f"RunList.runsOf('{hai}')[0].id")
    path = await save_pdf(p, f"Promise.resolve(Pdf.buildRun('{hai}','{rid}',['L','T','B']))", 'C4_zeitumstellung')
    t = pdftext(path)
    hhmm = re.findall(r'\b0[0-3]:\d\d\b', t)
    log('   Uhrzeiten im PDF-Protokoll:', hhmm[:12])
    ok(qpdf_ok(path), 'PDF-Protokoll über die Zeitumstellung: qpdf ok')
    if '02:30' in t and '02:10' in t and 'MEZ' not in t:   # 2.8.3: Uhrzeiten mit Zone (MESZ/MEZ) in der Nacht der Umstellung
        bef('Hinweis', 'Protokoll in der Nacht der Zeitumstellung: Uhrzeiten springen zurück (02:30 → 02:10) ohne Zonenangabe',
            'Haken um 02:30 Sommerzeit und 02:10 Winterzeit stehen nacheinander als „02:30“, „02:10“ im Protokoll – richtig sortiert, aber ohne MESZ/MEZ. Nur in einer Nacht im Jahr; '
            'für ein Prüfprotokoll trotzdem missverständlich.', art='reproduziert')
    await c.close()

@section('G7')
async def g7_focus(b):
    """Tastatur: sichtbarer Fokus je Farbschema, Escape schließt Dialog und Blatt, reduced-motion/print vorhanden"""
    FJS = """(()=>{const e=document.activeElement; if(!e||e===document.body) return null; const cs=getComputedStyle(e);
      return {txt:(e.getAttribute('aria-label')||e.textContent||e.tagName).trim().replace(/\\s+/g,' ').slice(0,40), cls:(e.className||'').toString().split(' ')[0], none:(cs.outlineStyle==='none'||cs.outlineWidth==='0px') && cs.boxShadow==='none'}})()"""
    worst = {}
    for theme in ('dark', 'red', 'light'):
        c, p = await newpage(b, 820, 1180, name=f'Fokus {theme}')
        await p.evaluate(f"Settings.set({{theme:'{theme}'}})")
        hai = await p.evaluate("Repo.liveShows().find(s=>s.f.titel.startsWith('Demo: Der Haifisch')).id")
        await p.evaluate(f"location.hash='#/show/{hai}'"); await p.wait_for_timeout(500)
        no = []
        for i in range(40):
            await p.keyboard.press('Tab'); f = await p.evaluate(FJS)
            if f and f['none']: no.append(f"{f['txt']} <.{f['cls']}>")
        worst[theme] = sorted(set(no))
        await p.evaluate("void Ui.confirm('Test?','x','OK')"); await p.wait_for_timeout(200); await p.keyboard.press('Escape'); await p.wait_for_timeout(300)
        d = await p.evaluate("!!document.querySelector('.dialog')")
        await p.evaluate("void SettingsView.open()"); await p.wait_for_timeout(300); await p.keyboard.press('Escape'); await p.wait_for_timeout(300)
        s2 = await p.evaluate("!!document.querySelector('.sheet')")
        ok(not d and not s2, f'{theme}: Escape schließt Dialog und Blatt')
        await c.close()
    log('   Tab-Stopps ohne sichtbaren Fokusrahmen:', worst)
    ok(all(not v for v in worst.values()), 'Jeder Tab-Stopp hat einen sichtbaren Fokusrahmen')
    if any(worst.values()):
        bef('niedrig', 'Titel-Knopf in der Kopfzeile ohne sichtbaren Fokusrahmen',
            'Mit Tab (Tastatur am iPad) erreicht man den Veranstaltungstitel in der Kopfzeile, er zeigt aber keinen Fokusrahmen: ' + '; '.join(sorted({x for v in worst.values() for x in v})) +
            '. Alle anderen 37 Tab-Stopps zeigen ihn, in allen drei Farbschemata.')
    c, p = await newpage(b, name='Medien')
    r = await p.evaluate("[...document.styleSheets].flatMap(s=>{try{return [...s.cssRules]}catch(e){return []}}).filter(r=>r.media&&/reduced-motion|print/.test(r.media.mediaText)).map(r=>r.media.mediaText)")
    ok('print' in r and any('reduced-motion' in x for x in r), f'CSS hat print und prefers-reduced-motion ({r})')
    await c.close()

@section('G8')
async def g8_sticky(b):
    """Querformat Smartphone: wie viel Platz lassen App-Leiste, Werkzeugleiste und Großbild-Kopf für den Inhalt?"""
    JS = """(()=>{let bottom=0; for (const s of ['.appbar','.toolbar','.bigsticky']) for (const e of document.querySelectorAll(s)) { const r=e.getBoundingClientRect(); const cs=getComputedStyle(e);
        if ((cs.position==='sticky'||cs.position==='fixed') && r.height>0 && r.top<=innerHeight/2 && r.bottom>0) bottom=Math.max(bottom,r.bottom); }
      const fab=[...document.querySelectorAll('.fab')].map(e=>e.getBoundingClientRect()).filter(r=>r.height>0); const ftop=fab.length?Math.min(...fab.map(r=>r.top)):innerHeight;
      return [innerHeight, Math.round(bottom), Math.round(Math.max(0, ftop-bottom))]})()"""
    rows = []
    for (w, h, nm) in [(844, 390, 'iPhone quer'), (915, 412, 'Pixel 8 quer'), (390, 844, 'iPhone hoch'), (1180, 820, 'iPad quer')]:
        c, p = await newpage(b, w, h, name=nm)
        hai = await p.evaluate("Repo.liveShows().find(s=>s.f.titel.startsWith('Demo: Der Haifisch')).id")
        await p.evaluate(f"location.hash='#/show/{hai}'; App.state.abt='L'; App.state.edit=true; App.render()"); await p.wait_for_timeout(400)
        for v in ('list', 'big'):
            await p.evaluate(f"Settings.set({{view:'{v}'}}).then(()=>App.render())"); await p.wait_for_timeout(300)
            await p.evaluate("scrollTo(0,1400)"); await p.wait_for_timeout(300)
            r = await p.evaluate(JS); rows.append((nm, v, r))
            if v == 'big' and h < 500: await shot(p, f'grossbild_L_bearbeiten_dunkel_{nm.replace(" ","_")}', 'Großbild', f'Großbild + Bearbeiten, gescrollt · {nm} {w}×{h}')
        await c.close()
    for nm, v, r in rows: log(f'   {nm} {v}: Höhe {r[0]}, fixiert bis {r[1]}, frei bis zu den Knöpfen {r[2]} px ({round(r[2]/r[0]*100)} %)')
    bad = [(nm, v, r) for nm, v, r in rows if r[2] < 0.35 * r[0]]
    ok(not bad, 'Überall mindestens 35 % der Höhe für den Inhalt')
    if bad:
        bef('mittel', 'Smartphone quer: fixierte Leisten lassen kaum Platz für den Inhalt',
            'Frei bleibende Höhe zwischen fixierten Leisten und den schwebenden Knöpfen: ' + '; '.join(f'{nm} {"Großbild" if v=="big" else "Liste"} {r[2]} von {r[0]} px' for nm, v, r in bad) +
            '. App-Leiste (61 px) und Werkzeugleiste (184 px) bleiben beim Scrollen stehen, im Großbild kommt der Kartenkopf dazu, unten rechts schweben „Kamera“ und „+ Eintrag“. '
            'Von einem Foto sieht man nichts, nur eine Textzeile. Werkzeugleiste beim Scrollen einklappen oder im Querformat nicht fixieren.')

@section('G9')
async def g9_bigwrap(b):
    """Großbild-Kopf: bricht das Hauptfeld (Kreis/Kanal) mitten in der Nummer um?"""
    res = []
    for (w, h, nm) in [(390, 844, 'iPhone'), (375, 667, 'iPhone SE'), (820, 1180, 'iPad hoch')]:
        c, p = await newpage(b, w, h, name=nm)
        hai = await p.evaluate("Repo.liveShows().find(s=>s.f.titel.startsWith('Demo: Der Haifisch')).id")
        await p.evaluate(f"location.hash='#/show/{hai}'; App.state.abt='L'; Settings.set({{view:'big'}}).then(()=>App.render())"); await p.wait_for_timeout(500)
        r = await p.evaluate("""[...document.querySelectorAll('.card .bighead .bk')].map(bk=>{ const lines=n=>{ const rg=document.createRange(); rg.selectNodeContents(n); const tops=[];
              for (const q of rg.getClientRects()) if (q.width>0 && !tops.some(t=>Math.abs(t-q.top)<6)) tops.push(q.top); return tops.length; };
            const tn=[...bk.childNodes].find(n=>n.nodeType===3 && n.textContent.trim()); const sm=bk.querySelector('small');
            return [bk.textContent.replace(/\\s+/g,' ').trim(), Math.max(tn?lines(tn):1, sm?lines(sm):1)]})""")
        wrapped = [x for x in r if x[1] > 1]
        res.append((nm, wrapped))
        if wrapped: await p.evaluate("document.querySelector('.card .bighead .bk').scrollIntoView({block:'center'})"); await p.wait_for_timeout(200); await shot(p, f'grossbild_umbruch_kreis_dunkel_{nm.replace(" ","_")}', 'Großbild', f'Großbild-Kopf: Kreis bricht um · {nm}')
        await c.close()
    log('   Umgebrochene Hauptfelder im Großbild-Kopf:', res)
    bad = [(nm, wr) for nm, wr in res if wr]
    ok(not bad, 'Hauptfeld im Großbild-Kopf einzeilig')
    if bad:
        bef('mittel', 'Großbild auf dem Smartphone: Kreis-Nummer bricht mitten in der Zahl um',
            'Im Kopf der Großbild-Karte wird „123+124“ als „123+1“ / „24“ auf zwei Zeilen gesetzt, das Wort „KREIS“ daneben als „KREI“ / „S“. Gemessen: ' +
            '; '.join(f'{nm}: {[x[0] for x in wr][:3]}' for nm, wr in bad) + '. Im Halbdunkel liest man „123+1“ und „24“ – zwei falsche Kreise. Umbruch nur an „+“ zulassen oder Schrift verkleinern.')

@section('G10')
async def g10_toast(b):
    """Meldungen: Fehler-, Warn- und Erfolgs-Toast je Farbschema unterscheidbar?"""
    res = {}
    for theme in ('dark', 'light', 'red'):
        c, p = await newpage(b, 390, 844, name=f'Toast {theme}')
        await p.evaluate(f"Settings.set({{theme:'{theme}'}})"); await p.wait_for_timeout(200)
        await p.evaluate("Ui.toast('Gespeichert','',{ms:20000}); Ui.toast('Speichern fehlgeschlagen','err',{ms:20000}); Ui.toast('Taschenlampe nicht verfügbar','warn',{ms:20000}); 1"); await p.wait_for_timeout(400)
        res[theme] = await p.evaluate("[...document.querySelectorAll('.toast')].map(t=>{const cs=getComputedStyle(t); return [t.textContent.trim().slice(0,24), cs.backgroundColor, cs.color]})")
        await shot(p, f'toasts_drei_arten_{theme}_phone', 'Dialoge', f'Erfolg / Fehler / Warnung · {theme}')
        await c.close()
    for t, r in res.items(): log(f'   {t}:', r)
    same = [t for t, r in res.items() if len(r) == 3 and len({x[1] for x in r}) == 1]
    ok(not same, 'Fehler- und Warnmeldungen sehen anders aus als Erfolgsmeldungen')
    if same:
        bef('mittel', 'Rotlicht: Fehlermeldung sieht genauso aus wie „Gespeichert“',
            f'Im Farbschema {", ".join(same)} haben Erfolgs-, Fehler- und Warn-Toast dieselbe Farbe ({res[same[0]][0][1]}, Schrift {res[same[0]][0][2]}). '
            'Ursache: html[data-theme="red"] .toast ist spezifischer als .toast.err / .toast.warn und überschreibt beide. '
            '„Speichern fehlgeschlagen“ oder „Cue-Foto(s) konnten nicht gespeichert werden“ fällt im Saal nicht auf – genau im Modus, der während der Vorstellung läuft. Symbol oder Rahmen für Fehler ergänzen.')

def write_gallery():
    groups = {}
    for g, n, cap in SHOTS: groups.setdefault(g, []).append((n, cap))
    html = ['<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Doku VT – Bildschirmfotos</title>',
            '<style>body{margin:0;font:15px system-ui,sans-serif;background:#111;color:#eee}header{position:sticky;top:0;background:#111e;padding:10px 16px;border-bottom:1px solid #333}nav a{color:#9cf;margin-right:12px}'
            'h2{margin:28px 16px 10px}.g{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px;padding:0 16px}figure{margin:0;background:#1b1b1b;border-radius:10px;overflow:hidden}'
            'img{width:100%;display:block;background:#000}figcaption{padding:8px 10px;font-size:13px;color:#bbb}</style>',
            f'<header><b>Doku VT {VER} – Bildschirmfotos</b> · {len(SHOTS)} Bilder<br><nav>' + ''.join(f'<a href="#{g}">{g}</a>' for g in groups) + '</nav></header>']
    for g, items in groups.items():
        html.append(f'<h2 id="{g}">{g}</h2><div class="g">' + ''.join(f'<figure><a href="{n}.png"><img loading="lazy" src="{n}.png" alt=""></a><figcaption>{cap}</figcaption></figure>' for n, cap in items) + '</div>')
    open(f'{OUT}/screens/galerie.html', 'w').write(''.join(html))
    log(f'   {len(SHOTS)} Bildschirmfotos, Galerie: {OUT}/screens/galerie.html')


# =====================================================================================
async def main():
    t0 = time.time()
    async with async_playwright() as pw:
        b = await pw.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream', '--enable-precise-memory-info'])
        log(f'Doku VT {VER} – Stresstest, Ordner {ROOT}')
        for code, fn in SECTIONS:
            if SEL and not any(code.startswith(s) for s in SEL): continue
            CUR[0] = code; log(f'\n== {code}: {fn.__doc__.strip()}')
            t = time.time()
            try:
                await asyncio.wait_for(fn(b), timeout=1500)
            except Exception as ex:
                ok(False, f'Abschnitt {code} abgebrochen: {type(ex).__name__}: {str(ex)[:300]}')
                log(traceback.format_exc()[-1500:])
            log(f'   ({time.time() - t:.0f} s)')
        await b.close()
    if SHOTS: write_gallery()
    errs = [e for e in ERRS]
    log(f'\nSeitenfehler/console.error: {len(errs)}')
    for e in errs[:40]: log('   ', e)
    fails = [c for c in CHECKS if not c[1]]
    log(f'\n{len(CHECKS)} Prüfungen, {len(fails)} nicht bestanden, {len(BEFUNDE)} Befunde, {time.time() - t0:.0f} s')
    json.dump({'version': VER, 'checks': CHECKS, 'befunde': BEFUNDE, 'seitenfehler': errs, 'matrix': MATRIX}, open(f'{OUT}/befunde.json', 'w'), ensure_ascii=False, indent=1)

asyncio.run(main())
