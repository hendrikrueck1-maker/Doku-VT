"""Doku VT 2.9.0 – Stückdaten, Besetzung, Zuständige, Archiv „Abgespielt“ und Gastspiel-Schalter (Python + Playwright/Chromium).
Aufruf: python3 test_290.py <ordner> [<ordner mit 2.8.3>]   (mit zweitem Ordner zusätzlich der Mischbetrieb mit einem Gerät auf 2.8.3)
Geräte = eigene Browser-Kontexte. Die Nummern in den Überschriften entsprechen Abschnitt 7 des Prompts zu 2.9.0."""
import asyncio, sys, subprocess, http.server, threading, functools, os, json, re
from playwright.async_api import async_playwright
ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
ALT = sys.argv[2] if len(sys.argv) > 2 else None
OUT = os.environ.get('OUT', '/tmp/doku-vt-test')
os.makedirs(OUT, exist_ok=True)
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
def serve(d):
    s = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=d))
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return f'http://127.0.0.1:{s.server_address[1]}/index.html'
URL = serve(ROOT)
URL_ALT = serve(ALT) if ALT else None
fails = []; ERRS = []; NOK = [0]
def ok(c, m):
    print(('OK   ' if c else 'FAIL ') + m, flush=True)
    NOK[0] += 1
    if not c: fails.append(m)
    return bool(c)

XSS = '<img src=x onerror="window.__xss=(window.__xss||0)+1">'
MKPHOTO = """window.__mk = async (px, hue) => { const c = document.createElement('canvas'); c.width = c.height = px || 240;
  const g = c.getContext('2d'); g.fillStyle = `hsl(${hue || 200},60%,40%)`; g.fillRect(0, 0, c.width, c.height); return await Photo.fromCanvas(c, 0.6); }; 1"""

async def newpage(b, w=1180, h=820, demo=False, name='', url=None, depts=None):
    ctx = await b.new_context(viewport={'width': w, 'height': h}, service_workers='block', timezone_id='Europe/Berlin', locale='de-DE')
    p = await ctx.new_page(); p._name = name or f'{w}x{h}'
    p.on('pageerror', lambda e: ERRS.append((p._name, str(e)[:300])))
    p.on('console', lambda m: ERRS.append((p._name, 'console: ' + m.text[:300])) if m.type == 'error' else None)
    await p.goto(url or URL); await p.wait_for_function('window.Boot && Boot.started', timeout=30000)
    if not demo:
        await p.evaluate("(async()=>{await Settings.set({demoOnFirstStart:false}); await Store.tx(['shows','entries','photos','fulls','thumbs'],'readwrite',s=>{['shows','entries','photos','fulls','thumbs'].forEach(n=>s[n].clear())}); await Store.metaSet('demoDone',true);})()")
        await p.reload(); await p.wait_for_function('window.Boot && Boot.started', timeout=30000)
    if depts:
        await p.evaluate(f"Settings.set({{depts:{json.dumps(depts)}}})")
    await p.evaluate(MKPHOTO)
    return ctx, p

async def pkg(p, since=0, depts='App.deviceDepts()', typ='sync'):
    return await p.evaluate(f"(async()=>{{const r=await Sync.buildPackage({{type:'{typ}',since:{since},depts:{depts}}}); return await r.blob.text()}})()")

async def imp(p, text):
    return await p.evaluate("async t=>{try{return await Sync.importPackage(new File([t],'x.json'))}catch(e){return {err:e.message}}}", text)

async def closeall(p):
    await p.evaluate("while(Ui.stack.length) Ui.stack[Ui.stack.length-1].el.remove(), Ui.stack.pop();")

async def live(A, B):
    """Live-Verbindung A ↔ B (WebRTC im selben Browser), wartet auf den Erstabgleich"""
    code = await A.evaluate("(async()=>{window._s&&window._s.close(); window._s=new PeerSession(); return await window._s.createOffer()})()")
    ans = await B.evaluate("async c=>{window._s&&window._s.close(); window._s=new PeerSession(); return await window._s.acceptOffer(await PeerAdapter.decodeSignal(c))}", code)
    await A.evaluate("async a=>{await window._s.acceptAnswer(await PeerAdapter.decodeSignal(a))}", ans)
    await A.wait_for_function("window._s && window._s.initialDone", timeout=30000)
    await B.wait_for_function("window._s && window._s.gotMeta", timeout=30000)

def pdftext(path, layout=True):
    return subprocess.run(['pdftotext'] + (['-layout'] if layout else []) + [path, '-'], capture_output=True, text=True).stdout
def pdfpage(path, n):
    return subprocess.run(['pdftotext', '-layout', '-f', str(n), '-l', str(n), path, '-'], capture_output=True, text=True).stdout
def qpdf_ok(path):
    r = subprocess.run(['qpdf', '--check', path], capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr)[-300:]
async def save_pdf(p, sid, opts, name):
    await p.evaluate(f"(async()=>{{const b=await Pdf.build('{sid}',{json.dumps(opts)}); window._pdf=Array.from(new Uint8Array(await b.arrayBuffer())); window._pages=Pdf.lastPages}})()")
    path = f'{OUT}/{name}.pdf'; open(path, 'wb').write(bytes(await p.evaluate('window._pdf')))
    return path, await p.evaluate('window._pages')

def nstand(t):
    return re.sub(r'Stand \d\d\.\d\d\.\d{4},? \d\d:\d\d', 'Stand X', t)

NEWKEYS = ['dauer', 'zustL', 'zustT', 'zustB', 'zustR', 'abgespielt']

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])
        cA, A = await newpage(b, name='A', depts=['L', 'T', 'B', 'R'])
        VER = json.load(open(os.path.join(ROOT, 'version.json')))['version']
        sw = open(os.path.join(ROOT, 'sw.js')).read()
        ok(await A.evaluate('APP_VERSION') == VER == '2.9.0' and f"VERSION = '{VER}'" in sw, f'Version {VER} in index.html, sw.js und version.json')
        fmt = await A.evaluate("[FORMAT_BASE, FORMAT_VERSION, JSON.stringify(DB_STORES)]")
        ok(fmt == [2, 4, '["shows","entries","photos","fulls","thumbs","meta"]'], f'Paketformat und Datenbank unverändert wie 2.8.3 (FORMAT_BASE/FORMAT_VERSION/DB_STORES {fmt})')

        # ---------- 1. Anlegen nur mit Titel ----------
        await A.evaluate("location.hash='#/'"); await A.wait_for_timeout(300)
        await A.click('[data-act=newshow]'); await A.wait_for_timeout(250)
        r = await A.evaluate("[!!document.querySelector('.sheet [data-more]'), document.querySelector('.sheet [data-more]').open, document.querySelector('.sheet .sfm small').textContent, !!document.querySelector('.sheet [data-abgsw]'), !!document.querySelector('.sheet [data-allsw]'), document.querySelector('.sheet [data-ok]').textContent.trim()]")
        ok(r[0] and r[1] is False and r[2] == 'Dauer, Besetzung, Zuständig, Notiz – alles optional' and not r[3] and r[4] and r[5] == 'Anlegen',
           f'Formular „Neue Veranstaltung“: Mehr Angaben eingeklappt, kein Abgespielt-Schalter, Gastspiel-Kasten, Knopf Anlegen ({r})')
        await A.fill('#ns-t', 'Nur Titel'); await A.click('.sheet [data-ok]'); await A.wait_for_timeout(700)
        r = await A.evaluate("(()=>{const s=Repo.liveShows().find(x=>x.f.titel==='Nur Titel'); return [location.hash==='#/show/'+s.id, App.state.edit, Object.keys(s.f).filter(k=>!/^(ci|ra):/.test(k)).sort(), Object.keys(s.f).some(k=>k.startsWith('rp:'))]})()")
        ok(r[0] and r[1] and r[2] == ['abteilungen', 'del', 'notiz', 'spielstaette', 'titel'] and not r[3],
           f'1. Anlegen nur mit Titel: direkt in die Veranstaltung (Bearbeitungsmodus), Felder wie 2.8.3, keine leeren neuen Felder ({r[2]})')

        # ---------- 2. Anlegen mit allen Angaben (eine Transaktion) ----------
        await A.evaluate("Settings.set({reqQuick:[{id:'q1',name:'Anna'},{id:'q2',name:'Ben'},{id:'q3',name:'Carla'}]})")
        await A.evaluate("location.hash='#/'"); await A.wait_for_timeout(300)
        await A.click('[data-act=newshow]'); await A.wait_for_timeout(250)
        await A.fill('#ns-t', 'Dreigroschenoper')
        await A.click('.sheet [data-more] summary'); await A.wait_for_timeout(150)
        await A.fill('#sf-d', '2:40 mit Pause')
        keys0 = await A.evaluate("[...document.querySelectorAll('.sheet [data-qn]')].map(b=>b.dataset.qn)")
        await A.click('.sheet [data-qn="Anna"]'); await A.wait_for_timeout(100)
        foc = await A.evaluate("document.activeElement.matches('[data-pr]') && document.activeElement.closest('.sfprow').querySelector('[data-pd]').value")
        await A.keyboard.type('Polly')
        await A.click('.sheet [data-qn="Ben"]'); await A.wait_for_timeout(100); await A.keyboard.type('Peachum')
        await A.click('.sheet [data-addp]'); await A.wait_for_timeout(100)
        foc2 = await A.evaluate("document.activeElement.matches('[data-pd]')")
        await A.keyboard.type('Gastsänger'); await A.keyboard.press('Tab'); await A.keyboard.type('Bote')
        await A.click('.sheet [data-addp]'); await A.wait_for_timeout(100)        # leere Zeile → wird verworfen
        keys1 = await A.evaluate("[...document.querySelectorAll('.sheet [data-qn]')].map(b=>b.dataset.qn)")
        ok(keys0 == ['Anna', 'Ben', 'Carla'] and keys1 == ['Carla'] and foc == 'Anna' and foc2,
           f'2. Ensemble als Schnelltasten: Antippen → Zeile Person (vorausgefüllt) + Rolle (Fokus), Taste verschwindet ({keys0} → {keys1})')
        # Zuständige: Licht und Requisite
        await A.fill('#sf-zL', 'Hendrik'); await A.fill('#sf-zR', 'Maria'); await A.fill('#ns-n', 'Premiere im Großen Haus')
        await A.evaluate("(()=>{window.__w=0; window.__ow=Repo._write; Repo._write=function(...a){window.__w++; return window.__ow.apply(Repo,a)}; return 1})()")
        await A.click('.sheet [data-ok]'); await A.wait_for_timeout(800)
        r = await A.evaluate("""(()=>{const s=Repo.liveShows().find(x=>x.f.titel==='Dreigroschenoper'); const ps=Req.persons(s.id);
          return [window.__w, s.f.dauer, s.f.zustL, s.f.zustR, s.f.zustT===undefined, s.f.notiz, ps.map(p=>[p.darsteller,p.rolle,p.ord]), s.f.abgespielt===undefined, s.id]})()""")
        await A.evaluate("(()=>{Repo._write=window.__ow; return 1})()")
        DGO = r[8]
        ok(r[0] == 1 and r[1] == '2:40 mit Pause' and r[2] == 'Hendrik' and r[3] == 'Maria' and r[4] and r[5] == 'Premiere im Großen Haus' and r[7]
           and r[6] == [['Anna', 'Polly', 10], ['Ben', 'Peachum', 20], ['Gastsänger', 'Bote', 30]],
           f'2. Anlegen mit Dauer, drei Personen, Zuständigen und Notiz: eine Transaktion, Personen in Reihenfolge, leere Zeile verworfen ({r[:7]})')
        await A.reload(); await A.wait_for_function('window.Boot && Boot.started'); await A.evaluate(MKPHOTO)

        # ---------- 3. Abteilung abwählen ----------
        await A.evaluate(f"App.state.edit=true; location.hash='#/show/{DGO}'"); await A.wait_for_timeout(400)
        await A.click('.appbar .title-btn'); await A.wait_for_timeout(300)
        r0 = await A.evaluate("[document.querySelector('.sheet h2').textContent, document.querySelector('.sheet [data-more]').open, document.querySelector('[data-zr=R]').classList.contains('hidden'), document.querySelector('.sheet [data-ok]').textContent.trim(), !!document.querySelector('.sheet [data-abgsw]')]")
        await A.click('.sheet [data-tgl=R]'); await A.wait_for_timeout(100)
        r1 = await A.evaluate("[document.querySelector('[data-zr=R]').classList.contains('hidden'), document.querySelector('[data-zr=L]').classList.contains('hidden'), document.querySelector('#sf-zR').value]")
        await A.click('.sheet [data-tgl=T]'); await A.wait_for_timeout(100)
        rT0 = await A.evaluate("document.querySelector('[data-zr=T]').classList.contains('hidden')")
        await A.click('.sheet [data-tgl=T]'); await A.wait_for_timeout(100)
        rT = rT0 and await A.evaluate("!document.querySelector('[data-zr=T]').classList.contains('hidden')")
        await A.click('.sheet [data-ok]'); await A.wait_for_timeout(600)
        r2 = await A.evaluate(f"[Repo.show('{DGO}').f.abteilungen, Repo.show('{DGO}').f.zustR]")
        ok(r0 == ['Stückdaten', True, False, 'Speichern', True] and r1 == [True, False, 'Maria'] and rT and r2 == [['L', 'T', 'B'], 'Maria'],
           f'3. Bearbeiten: „Mehr Angaben“ offen; Requisite abwählen → Feld verschwindet sofort, gespeicherter Wert bleibt ({r0}, {r1}, {r2})')
        await A.evaluate(f"Repo.patchShow('{DGO}',{{abteilungen:['L','T','B','R']}})")

        # ---------- 4. Nur geänderte Felder; gleichzeitige Änderung eines anderen Geräts bleibt ----------
        cB, B = await newpage(b, name='B', depts=['L', 'T', 'B', 'R'])
        await imp(B, await pkg(A))
        t0 = await A.evaluate(f"Utils.clone(Repo.show('{DGO}').t)")
        await A.click('.appbar .title-btn'); await A.wait_for_timeout(300)        # Formular auf A offen (Stand beim Öffnen)
        await B.evaluate(f"Repo.patchShow('{DGO}',{{zustT:'Tonmeisterin Jo', notiz:'Notiz von B'}})")
        await imp(A, await pkg(B))                                                       # kommt an, während das Formular offen ist
        await A.fill('#sf-d', '2:45 mit Pause'); await A.click('.sheet [data-ok]'); await A.wait_for_timeout(600)
        r = await A.evaluate(f"""(()=>{{const s=Repo.show('{DGO}'), t0={json.dumps(t0)}; return [Object.keys(s.t).filter(k=>s.t[k]!==t0[k]).sort(), s.f.dauer, s.f.zustT, s.f.notiz]}})()""")
        await imp(B, await pkg(A))
        rb = await B.evaluate(f"[Repo.show('{DGO}').f.dauer, Repo.show('{DGO}').f.zustT, Repo.show('{DGO}').f.notiz]")
        ok(r[1] == '2:45 mit Pause' and r[2] == 'Tonmeisterin Jo' and r[3] == 'Notiz von B' and set(r[0]) == {'dauer', 'zustT', 'notiz'} and rb == ['2:45 mit Pause', 'Tonmeisterin Jo', 'Notiz von B'],
           f'4. Speichern schreibt nur die Dauer; Zuständig Ton und Notiz von Gerät B (während das Formular offen war) bleiben – auf beiden Geräten ({r}, {rb})')

        # ---------- 5. Ensemble bearbeiten aus dem Formular ----------
        await A.evaluate("location.hash='#/'"); await A.wait_for_timeout(300)
        await A.click('[data-act=newshow]'); await A.wait_for_timeout(250)
        await A.click('.sheet [data-more] summary'); await A.wait_for_timeout(100)
        await A.click('.sheet [data-qn="Anna"]'); await A.keyboard.type('Jenny')
        await A.click('.sheet [data-addp]'); await A.keyboard.type('Frei Eingetippt')
        await A.click('.sheet [data-ens]'); await A.wait_for_timeout(300)
        h = await A.evaluate("document.querySelectorAll('.sheet')[document.querySelectorAll('.sheet').length-1].querySelector('h2').textContent")
        await A.evaluate("Settings.set({reqQuick:Settings.v.reqQuick.concat([{id:'q4',name:'Dora'}])})")
        await A.evaluate("history.back()"); await A.wait_for_timeout(700)
        r = await A.evaluate("[[...document.querySelectorAll('.sheet [data-qn]')].map(b=>b.dataset.qn), [...document.querySelectorAll('.sheet .sfprow')].map(r=>[r.querySelector('[data-pd]').value, r.querySelector('[data-pr]').value])]")
        ok(h == 'Ensemble' and r[0] == ['Ben', 'Carla', 'Dora'] and r[1] == [['Anna', 'Jenny'], ['Frei Eingetippt', '']],
           f'5. „Ensemble bearbeiten“ aus dem Formular: Schnelltasten aktualisiert, eingegebene Zeilen bleiben ({r})')
        await A.click('.sheet .sfprow:nth-child(2) [data-rm]'); await A.wait_for_timeout(100)
        r = await A.evaluate("document.querySelectorAll('.sheet .sfprow').length")
        ok(r == 1 and not await A.evaluate("!!document.querySelector('.dialog')"), '5. Zeile entfernen ohne Rückfrage')
        await A.evaluate("Settings.set({reqQuick:[]})"); await A.wait_for_timeout(200)
        await closeall(A)
        await A.evaluate("location.hash='#/'"); await A.wait_for_timeout(300)
        await A.click('[data-act=newshow]'); await A.wait_for_timeout(250)
        r = await A.evaluate("document.querySelector('.sheet [data-ensempty]')?.textContent||''")
        ok(r == 'Ensemble leer – Personen hier eintippen oder unter Einstellungen pflegen.', '5. Leeres Ensemble: Hinweis im Formular')
        await A.evaluate("history.back()"); await A.wait_for_timeout(300)
        await A.evaluate("Settings.set({reqQuick:[{id:'q1',name:'Anna'},{id:'q2',name:'Ben'},{id:'q3',name:'Carla'}]})")

        # ---------- 6. Ansichtsmodus ----------
        await A.evaluate(f"App.state.edit=false; location.hash='#/show/{DGO}'"); await A.wait_for_timeout(400)
        await A.click('.appbar .title-btn'); await A.wait_for_timeout(300)
        h1 = await A.evaluate("document.querySelector('.dialog h2')?.textContent||''"); m1 = await A.evaluate("document.querySelector('.dialog p')?.textContent||''")
        await A.click('.dialog .btn:has-text("Abbrechen")'); await A.wait_for_timeout(300)
        f1 = await A.evaluate("!!document.querySelector('[data-sform]')")
        await A.click('.appbar [data-act=showmenu]'); await A.wait_for_timeout(300)
        lab = await A.evaluate("[...document.querySelectorAll('.dialog .btn')].map(b=>b.textContent.trim())")
        await A.click('.dialog .btn:has-text("Als abgespielt markieren")'); await A.wait_for_timeout(600)
        h2 = await A.evaluate("document.querySelector('.dialog h2')?.textContent||''")
        await A.click('.dialog .btn:has-text("Abbrechen")'); await A.wait_for_timeout(300)
        ok(h1 == 'Ansichtsmodus' and 'Stückdaten ändern' in m1 and not f1 and h2 == 'Ansichtsmodus' and not await A.evaluate(f"App.isAbg(Repo.show('{DGO}'))")
           and 'Stückdaten bearbeiten' in lab and 'Titel & Details bearbeiten' not in lab,
           f'6. Ansichtsmodus: Stückdaten und „Als abgespielt markieren“ fragen erst nach dem Bearbeitungsmodus; Menüpunkt heißt „Stückdaten bearbeiten“')

        # ---------- 7. Abgespielt und Archiv ----------
        await A.evaluate(f"Repo.patchShow('{DGO}',{{spielstaette:'Spiegelhalle'}})")
        await A.evaluate("(async()=>{const s=await Repo.createShow('Im Spielplan',['L'],'Großes Haus');})()")
        await A.evaluate(f"App.state.edit=true; location.hash='#/show/{DGO}'"); await A.wait_for_timeout(400)
        await A.click('.appbar [data-act=showmenu]'); await A.wait_for_timeout(300)
        await A.click('.dialog .btn:has-text("Als abgespielt markieren")'); await A.wait_for_timeout(600)
        h = await A.evaluate("document.querySelector('.dialog h2')?.textContent||''")
        await A.click('.dialog .btn:has-text("Abgespielt")'); await A.wait_for_timeout(600)
        ban = await A.evaluate("document.querySelector('.abgbanner')?.textContent.trim()||''")
        ok(h == 'Als abgespielt markieren?' and await A.evaluate(f"Repo.show('{DGO}').f.abgespielt===true") and 'Abgespielt – auf der Startseite ausgeblendet' in ban,
           f'7. Als abgespielt markieren (eigene Rückfrage), Hinweis oben in der Veranstaltung („{ban[:60]}“)')
        await A.evaluate("location.hash='#/'"); await A.wait_for_timeout(400)
        r = await A.evaluate("""[[...document.querySelectorAll('.showcard h3')].map(h=>h.textContent), document.querySelector('.home-head p').textContent,
          [...document.querySelectorAll('.spfilter button')].map(b=>b.textContent.trim()), document.querySelector('[data-act=archiv]')?.textContent.trim()||'']""")
        nlive = await A.evaluate("Repo.liveShows().filter(s=>!App.isAbg(s)).length")
        ok('Dreigroschenoper' not in r[0] and r[1].startswith(f'{nlive} ') and not any('Spiegelhalle' in x for x in r[2]) and r[3] == 'Abgespielt (1)',
           f'7. Startseite: abgespielt nicht in Liste, Zähler und Spielstätten-Filter; Knopf „{r[3]}“ ({r[1]}, {r[2]})')
        await A.click('[data-act=archiv]'); await A.wait_for_timeout(400)
        r = await A.evaluate("[location.hash, [...document.querySelectorAll('.showcard h3')].map(h=>h.textContent), document.querySelector('.appbar h1').textContent]")
        ok(r[0] == '#/archiv' and r[1] == ['Dreigroschenoper'] and 'Abgespielt' in r[2], f'7. Ansicht „Abgespielt“ (#/archiv) zeigt das Stück ({r})')
        await A.click('.showcard [data-act=open]'); await A.wait_for_timeout(400)
        r = await A.evaluate(f"[location.hash==='#/show/{DGO}', document.querySelector('.appbar [data-act=archiv]')!==null]")
        ok(r == [True, True], '7. Aus dem Archiv öffnen; Zurück führt zu „Abgespielt“')
        await A.evaluate("location.hash='#/archiv'"); await A.wait_for_timeout(400)
        await A.click('.showcard [data-act=showmenu]'); await A.wait_for_timeout(300)
        await A.click('.dialog .btn:has-text("Wieder in den Spielplan")'); await A.wait_for_timeout(600)
        r = await A.evaluate(f"[Repo.show('{DGO}').f.abgespielt, document.querySelectorAll('.showcard').length]")
        await A.evaluate("location.hash='#/'"); await A.wait_for_timeout(400)
        r2 = await A.evaluate("[[...document.querySelectorAll('.showcard h3')].map(h=>h.textContent).includes('Dreigroschenoper'), !!document.querySelector('[data-act=archiv]')]")
        ok(r == [False, 0] and r2 == [True, False], f'7. „Wieder in den Spielplan“ im Archiv holt es zurück ({r}, {r2})')
        # Banner-Knopf im Bearbeitungsmodus und Ansichtsmodus
        await A.evaluate(f"Repo.patchShow('{DGO}',{{abgespielt:true}})")
        await A.evaluate(f"App.state.edit=false; location.hash='#/show/{DGO}'"); await A.wait_for_timeout(400)
        await A.click('.abgbanner [data-act=unplay]'); await A.wait_for_timeout(300)
        h = await A.evaluate("document.querySelector('.dialog h2')?.textContent||''")
        await A.click('.dialog .btn:has-text("Bearbeiten einschalten")'); await A.wait_for_timeout(700)
        r = await A.evaluate(f"[Repo.show('{DGO}').f.abgespielt, App.state.edit, !!document.querySelector('.abgbanner')]")
        ok(h == 'Ansichtsmodus' and r == [False, True, False], f'7. Hinweis-Knopf „Wieder in den Spielplan“: im Ansichtsmodus erst Rückfrage, dann zurückgeholt ({h}, {r})')
        # Abgleich: auf zweitem 2.9.0-Gerät ebenfalls ausgeblendet
        await A.evaluate(f"Repo.patchShow('{DGO}',{{abgespielt:true}})")
        await imp(B, await pkg(A))
        await B.evaluate("location.hash='#/'; App.render(true)"); await B.wait_for_timeout(400)
        r = await B.evaluate(f"[[...document.querySelectorAll('.showcard h3')].map(h=>h.textContent).includes('Dreigroschenoper'), document.querySelector('[data-act=archiv]')?.textContent.trim(), !!Repo.show('{DGO}'), Repo.entriesOf('{DGO}').length>=0]")
        ok(r[0] is False and r[1] == 'Abgespielt (1)' and r[2], f'7. Nach dem Abgleich auf Gerät B ebenfalls ausgeblendet, Daten vollständig da ({r})')
        # Demo kann ebenfalls abgespielt werden
        cD, D = await newpage(b, name='Demo', demo=True)
        r = await D.evaluate("(async()=>{const d=Repo.liveShows().find(s=>App.isDemo(s)); if(!d) return 'keine Demo'; await App.setAbg(d.id,true); App.render(true); return [App.isAbg(Repo.show(d.id)), [...document.querySelectorAll('.showcard h3')].some(h=>h.textContent===d.f.titel)]})()")
        ok(r == [True, False], f'7. Demo-Veranstaltung lässt sich ebenfalls als abgespielt markieren ({r})')
        await cD.close()

        # ---------- 8. Zuständig-Zeile ----------
        await A.evaluate(f"Repo.patchShow('{DGO}',{{abgespielt:false, zustT:'Jo', zustB:''}})")
        await A.evaluate(f"App.state.edit=false; App.state.abt='all'; location.hash='#/show/{DGO}'; App.render(true)"); await A.wait_for_timeout(500)
        r = await A.evaluate("[...document.querySelectorAll('[data-setup] .zline')].map(z=>[z.dataset.abt, z.querySelector('.zt').textContent, z.tagName])")
        rbox = await A.evaluate("document.querySelector('[data-setup] .setup[data-abt=R]').textContent.includes('2:45 mit Pause')")
        ok(r == [['L', 'Zuständig: Hendrik · Dauer 2:45 mit Pause', 'DIV'], ['T', 'Zuständig: Jo · Dauer 2:45 mit Pause', 'DIV'], ['B', 'Dauer 2:45 mit Pause', 'DIV'], ['R', 'Zuständig: Maria', 'DIV']],
           f'8. Zuständig-Zeile je Abteilung, nur Vorhandenes (Bühne ohne Zuständige: nur Dauer; Requisite nur Zuständig) ({r})')
        ok(rbox, '8. Requisite: Dauer weiter in „Allgemeine Infos“ (keine doppelte Anzeige in der Zeile)')
        await A.evaluate(f"(async()=>{{const p=Repo.patchShow('{DGO}',{{dauer:''}}); await p; App.render(true)}})()"); await A.wait_for_timeout(400)
        r2 = await A.evaluate("[...document.querySelectorAll('[data-setup] .zline')].map(z=>z.dataset.abt)")
        ok(r2 == ['L', 'T', 'R'], f'8. Fehlt beides (Bühne ohne Zuständige und ohne Dauer): keine Zeile ({r2})')
        await A.evaluate(f"Repo.patchShow('{DGO}',{{dauer:'2:45 mit Pause'}})"); await A.wait_for_timeout(300)
        await A.evaluate("App.state.abt='T'; App.renderToolbar(); App.renderList()"); await A.wait_for_timeout(300)
        r = await A.evaluate("[...document.querySelectorAll('[data-setup] .zline')].map(z=>z.dataset.abt)")
        ok(r == ['T'], f'8. Gewählte Abteilung: nur ihre Zeile ({r})')
        await A.evaluate("App.state.edit=true; App.state.abt='all'; App.render()"); await A.wait_for_timeout(300)
        await A.click('[data-setup] .zline[data-abt=T]'); await A.wait_for_timeout(400)
        r = await A.evaluate("[!!document.querySelector('[data-sform]'), document.querySelector('.sheet [data-more]').open, document.activeElement && document.activeElement.id]")
        ok(r == [True, True, 'sf-zT'], f'8. Zeile antippen (Bearbeitungsmodus) öffnet die Stückdaten mit „Mehr Angaben“, Fokus im Zuständig-Feld ({r})')
        await A.evaluate("history.back()"); await A.wait_for_timeout(300)

        # ---------- 9. Duplizieren ----------
        await A.evaluate(f"(async()=>{{await Repo.patchShow('{DGO}',{{abgespielt:true}}); await App.setAllDept('{DGO}',true);}})()")
        r = await A.evaluate(f"""(async()=>{{const n=await Repo.duplicateShow('{DGO}'); return [n.f.dauer, n.f.zustL, n.f.zustT, n.f.zustR, n.f.abgespielt===undefined||n.f.abgespielt===false, Req.persons(n.id).map(p=>Req.personLabel(p)), Settings.v.allDeptShows.includes(n.id), n.id]}})()""")
        ok(r[:5] == ['2:45 mit Pause', 'Hendrik', 'Jo', 'Maria', True] and r[5] == ['Anna (Polly)', 'Ben (Peachum)', 'Gastsänger (Bote)'] and r[6],
           f'9. Duplizieren übernimmt Dauer, Zuständige, Besetzung und den Gastspiel-Schalter; Kopie nicht abgespielt ({r[:7]})')
        await A.evaluate(f"(async()=>{{await Repo.patchShow('{DGO}',{{abgespielt:false}}); await App.setAllDept('{DGO}',false);}})()")

        # ---------- 10. Gastspiel-Schalter ----------
        cL, L = await newpage(b, name='Licht', depts=['L'])
        cR, R = await newpage(b, name='Requisite', depts=['R'])
        GS = await R.evaluate("""(async()=>{ await Req.ensureHouse(); const s=await Repo.createShow('Gastspiel Ulm',['L','T','B','R'],'Sonstiges',{zustR:'Maria'});
          const ph=await __mk(300,30), ov=await __mk(300,90);
          await Repo.patchShowBlobs(s.id,{fotoR:ov.b},[ov]);
          await Repo.saveDraft({id:null,showId:s.id,abt:'R',f:{was:'Koffer'},photos:{A:[{photoId:null,b:ph.b,w:300,h:300,full:ph.full,thumb:ph.thumb}],E:[]}});
          await Repo.saveDraft({id:null,showId:s.id,abt:'R',f:{was:'Regenschirm'},photos:{A:[],E:[]}});
          window.__ph=ph.b; window.__ov=ov.b; return s.id})()""")
        pR = await pkg(R)
        await imp(L, pR)
        r0 = await L.evaluate(f"[App.visibleDepts('{GS}'), Repo.entriesOf('{GS}').length]")
        await L.evaluate(f"App.setAllDept('{GS}', true)")
        st = await imp(L, pR)
        r = await L.evaluate(f"""(async()=>[App.visibleDepts('{GS}'), App.deviceDepts(), Repo.entriesOf('{GS}').filter(e=>abtOf(e)==='R').length, (await Repo.missingBlobs()).length,
          !!(await Repo.full('{await R.evaluate('window.__ph')}')), !!(await Repo.full('{await R.evaluate('window.__ov')}')), Settings.v.depts])()""")
        ok(r0 == [['L'], 0] and r[0] == ['L', 'T', 'B', 'R'] and r[1] == ['L', 'T', 'B', 'R'] and r[2] == 2 and r[3] == 0 and r[4] and r[5] and r[6] == ['L'],
           f'10. Licht-Gerät mit Gastspiel-Schalter: alle vier Abteilungen sichtbar, Sync-Paket vom Requisite-Gerät behält Gegenstände und Fotos (kein dropReq) ({r0}, {r})')
        r = await L.evaluate("""(()=>{const s=new PeerSession(); const out=[]; s.send=async m=>out.push(m); const dc={}; s._bind(dc); dc.onopen(); const h=out.find(m=>m.t==='hello'); s.unsub&&s.unsub(); s.pc.close(); Sync.peer=null; return h.d})()""")
        ok(r == ['L', 'T', 'B', 'R'], f'10. Live-Abgleich: hello.d mit Requisite ({r})')
        # echte Live-Verbindung Requisite-Gerät → Licht-Gerät mit Gastspiel
        try:
            await live(L, R)
            await R.evaluate(f"""(async()=>{{const ph=await __mk(260,140); window.__ph2=ph.b; await Repo.saveDraft({{id:null,showId:'{GS}',abt:'R',f:{{was:'Live-Hut'}},photos:{{A:[{{photoId:null,b:ph.b,w:260,h:260,full:ph.full,thumb:ph.thumb}}],E:[]}}}});}})()""")
            b2 = await R.evaluate('window.__ph2')
            await L.wait_for_function(f"Repo.entriesOf('{GS}').some(e=>e.f.was==='Live-Hut')", timeout=15000)
            await L.wait_for_function(f"Repo.full('{b2}').then(d=>window.__h2=!!d) && window.__h2", timeout=15000, polling=300)
            r = await L.evaluate("window._s.depts")
            ok('R' in r, f'10. Live: neuer Gegenstand samt Foto kommt auf dem Licht-Gerät an (Schnittmenge {r})')
            await L.evaluate("window._s.close()"); await R.wait_for_timeout(300)
        except Exception as ex:
            ok(False, '10. Live-Abgleich Gastspiel: ' + str(ex)[:150])
        rdemo = await L.evaluate("(async()=>[Repo.liveShows().some(s=>/Einfache Leute|Testvorstellung/.test(s.f.titel)), await Store.metaGet('demoRDone', false), Repo.house.has('requisite')])()")
        ok(rdemo[0] is False and not rdemo[1] and rdemo[2], f'10. Keine Requisite-Demo/Testvorstellung auf dem Licht-Gerät; Haus-Orte für den Ort-Picker vorhanden ({rdemo})')
        await L.evaluate(f"App.state.edit=false; location.hash='#/'"); await L.wait_for_timeout(400)
        badge = await L.evaluate(f"[...document.querySelectorAll('.showcard')].filter(c=>c.querySelector('h3').textContent==='Gastspiel Ulm').map(c=>c.querySelector('.allbadge')?.textContent.trim())")
        ok(badge == ['alle Abteilungen'], f'10. Startseite: Plakette „alle Abteilungen“ ({badge})')
        diag = await L.evaluate("(async()=>{await DiagView.open(); await new Promise(r=>setTimeout(r,600)); const t=document.querySelector('.sheet .kv').textContent; history.back(); return t})()")
        await L.wait_for_timeout(300)
        await L.evaluate("SyncView.open()"); await L.wait_for_timeout(300)
        sv = await L.evaluate("document.querySelector('.sheet .gasthint')?.textContent.replace(/\\s+/g,' ')||''")
        await L.evaluate("history.back()"); await L.wait_for_timeout(300)
        ok('Dieses Gerät dokumentiert: Licht · zusätzlich für Gastspiele: Gastspiel Ulm' in diag and 'Requisite aller Stücke' in sv,
           f'10. Diagnose („…zusätzlich für Gastspiele: Gastspiel Ulm“) und Hinweis in „Abgleich & Sicherung“')
        # Form-Schalter aus
        await L.evaluate(f"App.state.edit=true; location.hash='#/show/{GS}'"); await L.wait_for_timeout(400)
        await L.click('.appbar .title-btn'); await L.wait_for_timeout(300)
        chk = await L.evaluate("document.querySelector('.sheet [data-allsw]').checked")
        await L.click('.sheet .sfdev .switch'); await L.click('.sheet [data-ok]'); await L.wait_for_timeout(700)
        r = await L.evaluate(f"[App.visibleDepts('{GS}'), App.deviceDepts(), Repo.entriesOf('{GS}').filter(e=>abtOf(e)==='R').length, Settings.v.allDeptShows.includes('{GS}')]")
        ok(chk and r == [['L'], ['L'], 3, False], f'10. Schalter im Formular aus → wieder nur Licht sichtbar, Requisite-Daten bleiben gespeichert ({r})')
        st = await imp(L, await pkg(R))
        r = await L.evaluate(f"Repo.entriesOf('{GS}').filter(e=>abtOf(e)==='R').length")
        ok(r == 3, f'10. Ohne Schalter: vorhandene Requisite-Gegenstände bleiben, nur neue Requisite wird beim Import wie bisher nicht übernommen ({r})')

        # ---------- 11. „Hier trotzdem anzeigen“ ----------
        TON = await L.evaluate("(async()=>{const s=await Repo.createShow('Nur Ton',['T']); return s.id})()")
        await L.evaluate(f"App.state.edit=false; location.hash='#/show/{TON}'"); await L.wait_for_timeout(400)
        r = await L.evaluate("[document.querySelector('.empty h3')?.textContent, [...document.querySelectorAll('.empty .btn')].map(b=>b.textContent.trim())]")
        await L.click('.empty [data-act=allhere]'); await L.wait_for_timeout(500)
        r2 = await L.evaluate(f"[App.allDept('{TON}'), App.visibleDepts('{TON}'), !!document.querySelector('.toolbar')]")
        ok(r[0] == 'Keine Abteilung dieses Geräts' and len(r[1]) == 3 and r[1][2] == 'Hier trotzdem anzeigen (nur dieses Stück)' and r2 == [True, ['T'], True],
           f'11. „Keine Abteilung dieses Geräts“ → „Hier trotzdem anzeigen“ setzt den Schalter ({r[1]}, {r2})')
        await cR.close()

        # ---------- 12. PDF ----------
        PS = await A.evaluate("""(async()=>{const s=await Repo.createShow('Zauberflöte',['L','T','B'],'Großes Haus',{dauer:'1:40, keine Pause',zustL:'Hendrik Rück',zustT:'Jörg Weiß'});
          for (const [abt,k] of [['L','101'],['T','M3'],['B','']]) { const ph=await __mk(300,k.length*40); const f=abt==='L'?{kreis:k}:abt==='T'?{kanal:k}:{was:'Podest'}; await Repo.saveDraft({id:null,showId:s.id,abt,f,photos:{A:[{photoId:null,b:ph.b,w:300,h:300,full:ph.full,thumb:ph.thumb}],E:[]}}); }
          return s.id})()""")
        path, n = await save_pdf(A, PS, {'kat': 'all', 'depts': ['L', 'T', 'B'], 'cover': True}, '290_stueck')
        txt = pdftext(path); q = qpdf_ok(path)
        flat = re.sub(r'\s+', ' ', txt)
        ok(q[0], '12. qpdf --check: PDF fehlerfrei ' + ('' if q[0] else q[1]))
        ok('Zuständig: Hendrik Rück · Dauer: 1:40, keine Pause' in flat and 'Zuständig: Jörg Weiß · Dauer: 1:40, keine Pause' in flat and 'Dauer: 1:40, keine Pause' in flat,
           '12. Kapitelseiten Licht und Ton: „Zuständig: … · Dauer: …“ (Bühne ohne Zuständige: nur Dauer), Umlaute korrekt')
        bpage = [pdfpage(path, i) for i in range(1, n + 1)]
        bz = [i + 1 for i, t in enumerate(bpage) if 'BÜHNENTECHNIK' in t.upper() and 'Dauer: 1:40' in t and 'Zuständig:' not in t]
        ok(len(bz) >= 1, f'12. Kapitelseite Bühne: nur Dauer (Seite {bz})')
        fz = [i + 1 for i, t in enumerate(bpage) if re.search(r'Zuständig Hendrik Rück', t)]
        ft = [i + 1 for i, t in enumerate(bpage) if re.search(r'Zuständig Jörg Weiß', t)]
        ok(len(fz) >= 2 and len(ft) >= 2 and not set(fz) & set(ft) and 1 not in fz + ft, f'12. Fußzeile der Abteilungsseiten mit „Zuständig <Name>“ (Licht S. {fz}, Ton S. {ft}), Deckblatt ohne')
        # einzelne Abteilung ohne Kapitelseite: keine Zusatzseite
        P1 = await A.evaluate("""(async()=>{const s=await Repo.createShow('Nur Licht',['L'],'',{dauer:'0:55',zustL:'Hendrik Rück'}); const pt={};
          Object.keys(s.f).filter(k=>k.startsWith('ci:')).forEach(k=>pt[k]=Object.assign({},s.f[k],{del:true})); await Repo.patchShow(s.id,pt);
          const ph=await __mk(300,10); await Repo.saveDraft({id:null,showId:s.id,abt:'L',f:{kreis:'7'},photos:{A:[{photoId:null,b:ph.b,w:300,h:300,full:ph.full,thumb:ph.thumb}],E:[]}}); return s.id})()""")
        _, n1 = await save_pdf(A, P1, {'kat': 'all', 'depts': ['L'], 'cover': False}, '290_licht')
        p1t = pdftext(f'{OUT}/290_licht.pdf')
        await A.evaluate(f"Repo.patchShow('{P1}',{{zustL:'',dauer:''}})")
        _, n0 = await save_pdf(A, P1, {'kat': 'all', 'depts': ['L'], 'cover': False}, '290_licht0')
        ok(n1 == n0 == 1 and 'Zuständig:' not in p1t and 'Dauer:' not in p1t and 'Zuständig Hendrik Rück' in p1t,
           f'12. Nur Licht ohne Kapitelseite: keine Seite nur für Zuständig/Dauer ({n1} = {n0}), Zuständig steht in der Fußzeile')
        # Requisite: Dauer-Zeile ergänzt
        rp, _ = await save_pdf(A, DGO, {'kat': 'all', 'depts': ['R'], 'cover': False, 'rsort': 'ort'}, '290_req')
        rt = re.sub(r'\s+', ' ', pdftext(rp))
        ok('Dauer: 2:45 mit Pause · Zuständig: Maria' in rt and rt.count('Dauer: 2:45') == 1, '12. Requisite: „Dauer: … · Zuständig: …“ in „Allgemeine Infos“, Dauer nicht doppelt')
        # Deckblatt unverändert
        cov = pdfpage(path, 1)
        await A.evaluate(f"Repo.patchShow('{PS}',{{zustL:'',zustT:''}})")
        p0, _ = await save_pdf(A, PS, {'kat': 'all', 'depts': ['L', 'T', 'B'], 'cover': True}, '290_ohne')
        ok(nstand(cov) == nstand(pdfpage(p0, 1)), '12. Deckblatt mit und ohne Zuständige identisch (keine neuen Angaben)')
        if URL_ALT:
            cO, O = await newpage(b, name='2.8.3-PDF', url=URL_ALT, depts=['L', 'T', 'B', 'R'])
            await A.evaluate(f"Repo.patchShow('{PS}',{{zustL:'Hendrik Rück',zustT:'Jörg Weiß'}})")
            await imp(O, await pkg(A, typ='backup'))
            path, _ = await save_pdf(A, PS, {'kat': 'all', 'depts': ['L', 'T', 'B'], 'cover': True}, '290_neu')
            await O.evaluate(f"(async()=>{{const b=await Pdf.build('{PS}',{{kat:'all',depts:['L','T','B'],cover:true}}); window._pdf=Array.from(new Uint8Array(await b.arrayBuffer()))}})()")
            open(f'{OUT}/290_alt.pdf', 'wb').write(bytes(await O.evaluate('window._pdf')))
            norm = lambda t: nstand(re.sub(r'Doku VT 2\.\d+\.\d+', 'Doku VT x', t))
            c_new, c_old = norm(pdfpage(path, 1)), norm(pdfpage(f'{OUT}/290_alt.pdf', 1))
            ok(c_new == c_old, '12. Deckblatt identisch mit 2.8.3 (gleiche Daten, nur die Versionsnummer verschieden)')
            if c_new != c_old:
                import difflib; print('\n'.join(list(difflib.unified_diff(c_old.splitlines(), c_new.splitlines(), lineterm=''))[:30]))
            await cO.close()

        # ---------- 13. Mischbetrieb mit 2.8.3 ----------
        if URL_ALT:
            cN, N = await newpage(b, name='2.9.0', depts=['L', 'T', 'B', 'R'])
            cO, O = await newpage(b, name='2.8.3', url=URL_ALT, depts=['L', 'T', 'B', 'R'])
            ok(await O.evaluate('APP_VERSION') == '2.8.3', 'Zweiter Ordner ist 2.8.3')
            MX = await N.evaluate("""(async()=>{const s=await Repo.createShow('Mischbetrieb',['L','T','R'],'',{dauer:'1:30',zustL:'Hendrik',zustT:'Jo',zustR:'Maria',notiz:'n',persons:[{darsteller:'Anna',rolle:'Polly'}]});
              await Repo.patchShow(s.id,{abgespielt:true}); return s.id})()""")
            st = await imp(O, await pkg(N))
            r = await O.evaluate(f"(()=>{{const s=Repo.show('{MX}'); return s && [s.f.zustL, s.f.zustT, s.f.zustR, s.f.abgespielt, s.f.dauer, Req.persons(s.id).length, Rec.valid(s,'show')]}})()")
            ok(not st.get('err') and st.get('ungueltig') == 0 and r == ['Hendrik', 'Jo', 'Maria', True, '1:30', 1, True],
               f'13. Paket 2.9.0 → 2.8.3 ohne Meldung gelesen, Rec.valid auf 2.8.3 akzeptiert die neuen Felder ({st.get("err") or st.get("ungueltig")}, {r})')
            await O.evaluate(f"Repo.patchShow('{MX}',{{titel:'Mischbetrieb (von 2.8.3)', dauer:'1:35'}})")
            OS = await O.evaluate("(async()=>{const s=await Repo.createShow('Von 2.8.3',['L']); return s.id})()")
            st = await imp(N, await pkg(O, depts='Settings.v.depts.slice()'))
            r = await N.evaluate(f"(()=>{{const s=Repo.show('{MX}'); return [s.f.titel, s.f.dauer, s.f.zustL, s.f.zustT, s.f.zustR, s.f.abgespielt, !!Repo.show('{OS}')]}})()")
            ok(not st.get('err') and st.get('ungueltig') == 0 and r == ['Mischbetrieb (von 2.8.3)', '1:35', 'Hendrik', 'Jo', 'Maria', True, True],
               f'13. 2.8.3 ändert Titel und Dauer → Zuständige und „abgespielt“ bleiben; Paket 2.8.3 → 2.9.0 ohne Meldung ({r})')
            ok(await O.evaluate(f"Repo.liveShows().some(s=>s.id==='{MX}')"), '13. 2.8.3 zeigt das abgespielte Stück weiter normal an (gewollt)')
            try:
                await live(N, O)
                await N.evaluate(f"Repo.patchShow('{MX}',{{zustB:'Bühnenmeister Kurt', abgespielt:false}})")
                await O.wait_for_function(f"Repo.show('{MX}').f.zustB==='Bühnenmeister Kurt' && Repo.show('{MX}').f.abgespielt===false", timeout=15000)
                await O.evaluate(f"Repo.patchShow('{MX}',{{notiz:'live von 2.8.3'}})")
                await N.wait_for_function(f"Repo.show('{MX}').f.notiz==='live von 2.8.3'", timeout=15000)
                r = await N.evaluate(f"[Repo.show('{MX}').f.zustB, Repo.show('{MX}').f.zustR]")
                ok(r == ['Bühnenmeister Kurt', 'Maria'], f'13. Live in beide Richtungen 2.9.0 ↔ 2.8.3: neue Felder kommen an und bleiben ({r})')
                await N.evaluate("window._s.close()")
            except Exception as ex:
                ok(False, '13. Live 2.9.0 ↔ 2.8.3: ' + str(ex)[:150])
            # Gastspiel-Gerät (Licht + Schalter) gegen 2.8.3-Requisite-Gerät: hello.d ist eine normale Abteilungsliste
            r = await O.evaluate(f"(async()=>{{const s=new PeerSession(); const out=[]; s.send=async m=>out.push(m); s.open=false; await s._handle({{t:'hello',n:'Gast',id:'g',v:'2.9.0',d:['L','T','B','R'],c:1}}); const m=out.find(x=>x.t==='meta'); s.unsub&&s.unsub(); s.pc.close(); return [s.depts, m.entries.some(e=>abtOf(e)==='R')]}})()")
            ok(r[0] == ['L', 'T', 'B', 'R'], f'13. 2.8.3 versteht hello.d des Gastspiel-Geräts ({r})')
            await cN.close(); await cO.close()
        else:
            print('   (13. Mischbetrieb übersprungen – kein Ordner mit 2.8.3 angegeben)')

        # ---------- 14. Merge-Eigenschaften und Backup-Reimport ----------
        r = await A.evaluate(f"""(()=>{{const base=Repo.show('{DGO}');
          const a=Rec.patch(base,{{zustL:'A-Licht', abgespielt:true, dauer:'1:00'}});
          Clock.observe(Date.now()+5); const b=Rec.patch(base,{{zustT:'B-Ton', abgespielt:true, dauer:'2:00', ['rp:mx']:{{rolle:'R',darsteller:'D',ord:99,del:false}}}});
          const ab=Rec.merge(a,b).rec, ba=Rec.merge(b,a).rec, aab=Rec.merge(ab,b).rec, aba=Rec.merge(ab,a).rec;
          const J=x=>JSON.stringify(Object.keys(x.f).sort().map(k=>[k,x.f[k],x.t[k]]));
          return [J(ab)===J(ba), J(ab)===J(aab), J(ab)===J(aba), ab.f.zustL, ab.f.zustT, ab.f.abgespielt, ab.f.dauer, !!ab.f['rp:mx'], Rec.merge(ab,ab).changed]}})()""")
        ok(r[:3] == [True, True, True] and r[3:8] == ['A-Licht', 'B-Ton', True, '2:00', True] and r[8] is False,
           f'14. Merge mit den neuen Feldern: kommutativ, idempotent, feldweise (Zuständige beider Geräte bleiben) ({r})')
        bk = await pkg(A, typ='backup', depts='null')
        cF, F = await newpage(b, name='Backup', depts=['L', 'T', 'B', 'R'])
        s1 = await imp(F, bk); s2 = await imp(F, bk)
        ok(s1.get('neu', 0) > 0 and s2.get('neu') == 0 and s2.get('geaendert') == 0, f'14. Zweiter Import desselben Backups: 0 neu, 0 geändert ({s1.get("neu")}/{s1.get("geaendert")} → {s2.get("neu")}/{s2.get("geaendert")})')
        await cF.close()

        # ---------- 15. XSS ----------
        await A.evaluate("window.__xss=0")
        XS = await A.evaluate(f"""(async()=>{{const X={json.dumps(XSS)}; await Settings.set({{reqQuick:[{{id:'qx',name:X}}]}});
          const s=await Repo.createShow(X,['L','T','R'],X,{{dauer:X,zustL:X,zustT:X,zustR:X,notiz:X,persons:[{{darsteller:X,rolle:X}}]}}); await Repo.patchShow(s.id,{{abgespielt:true}}); return s.id}})()""")
        await A.evaluate(f"App.state.edit=true; App.state.abt='all'; location.hash='#/show/{XS}'"); await A.wait_for_timeout(500)
        await A.click('.appbar .title-btn'); await A.wait_for_timeout(400)
        await A.click('.sheet [data-editp]'); await A.wait_for_timeout(400)
        await A.evaluate("history.back()"); await A.wait_for_timeout(300); await A.evaluate("history.back()"); await A.wait_for_timeout(300)
        await A.evaluate("location.hash='#/'"); await A.wait_for_timeout(300)
        await A.click('[data-act=newshow]'); await A.wait_for_timeout(300)
        await A.click('.sheet [data-more] summary'); await A.click('.sheet [data-qn]'); await A.wait_for_timeout(200)
        await A.evaluate("history.back()"); await A.wait_for_timeout(300)
        await A.evaluate("location.hash='#/archiv'"); await A.wait_for_timeout(400)
        xp, _ = await save_pdf(A, XS, {'kat': 'all', 'depts': ['L', 'T', 'R'], 'cover': True}, '290_xss')
        xt = pdftext(xp)
        await A.wait_for_timeout(300)
        x = await A.evaluate('window.__xss')
        zl = await A.evaluate(f"(()=>{{App.state.route='show'; App.state.showId='{XS}'; const d=document.createElement('div'); SetupView.render(d,'{XS}',false,['L','T','R']); return d.querySelectorAll('img').length}})()")
        ok(x == 0 and zl == 0 and '<img src=x' in xt, f'15. XSS: Zuständige, Dauer, Personen, Titel maskiert (Formular, Zuständig-Zeile, Archiv, Besetzung, PDF-Text) – Zähler {x}')
        await A.evaluate("Settings.set({reqQuick:[]})")

        # ---------- 16. Smartphone 320 px ----------
        cP, P = await newpage(b, w=320, h=568, name='320px', depts=['L', 'T', 'R'])
        await P.evaluate("Settings.set({reqQuick:[{id:'a',name:'Anna-Lena Musterfrau'},{id:'b',name:'Ben'}]})")
        await P.click('[data-act=newshow]'); await P.wait_for_timeout(300)
        await P.click('.sheet [data-more] summary'); await P.wait_for_timeout(150)
        await P.click('.sheet [data-qn="Ben"]'); await P.keyboard.type('Mackie Messer')
        await P.click('.sheet [data-addp]'); await P.click('.sheet [data-addp]'); await P.click('.sheet [data-addp]')
        await P.wait_for_timeout(200)
        r = await P.evaluate("""(()=>{const sb=document.querySelector('.sheet-b'); const rows=[...document.querySelectorAll('.sfprow')];
          const rr=rows.map(r=>{const d=r.querySelector('[data-pd]').getBoundingClientRect(), x=r.querySelector('[data-rm]').getBoundingClientRect(); return [Math.round(d.width), Math.round(x.width), Math.round(x.height), Math.round(d.right)]});
          const sw=[...document.querySelectorAll('.sheet [data-sform] *')].filter(e=>e.getBoundingClientRect().right>window.innerWidth+1).map(e=>e.className||e.tagName).slice(0,5);
          return [sb.scrollWidth<=sb.clientWidth, document.documentElement.scrollWidth<=320, rr, sw, [...document.querySelectorAll('.sfdev .switch, .sheet [data-tgl]')].every(e=>e.getBoundingClientRect().height>=32)]})()""")
        ok(r[0] and r[1] and not r[3] and all(w >= 150 and xw >= 44 and xh >= 44 and right <= 320 for w, xw, xh, right in r[2]) and r[4],
           f'16. 320 px: Formular ohne waagrechtes Scrollen, Besetzungszeilen bedienbar (Feldbreite/Knopf {r[2][:2]}, überstehend {r[3]})')
        # Tastatur (Android: Seite wird kleiner) – aktives Feld bleibt sichtbar
        await P.set_viewport_size({'width': 320, 'height': 300})
        await P.focus('.sfprow:last-child [data-pr]'); await P.wait_for_timeout(900)
        r = await P.evaluate("(()=>{const el=document.activeElement, b=el.getBoundingClientRect(); return [el.matches('[data-pr]'), Math.round(b.top), Math.round(b.bottom), window.innerHeight]})()")
        ok(r[0] and r[1] >= 0 and r[2] <= r[3], f'16. Bei offener Tastatur (Höhe 300 px) bleibt das aktive Feld sichtbar ({r})')
        await P.set_viewport_size({'width': 320, 'height': 568})
        await P.fill('#ns-t', 'Handy'); await P.click('.sheet [data-ok]'); await P.wait_for_timeout(700)
        r = await P.evaluate("(()=>{const s=Repo.liveShows().find(x=>x.f.titel==='Handy'); return Req.persons(s.id).map(p=>Req.personLabel(p))})()")
        ok(r == ['Ben (Mackie Messer)'], f'16. Leere Zeilen verworfen, Besetzung gespeichert ({r})')
        await P.evaluate("App.state.edit=true; App.render()"); await P.wait_for_timeout(300)
        await P.click('.appbar .title-btn'); await P.wait_for_timeout(300)
        r = await P.evaluate("(()=>{const sb=document.querySelector('.sheet-b'); return [sb.scrollWidth<=sb.clientWidth, document.querySelector('.sheet [data-more]').open]})()")
        ok(r == [True, True], f'16. 320 px: Stückdaten bearbeiten ohne waagrechtes Scrollen ({r})')
        await cP.close()

        for c in (cA, cB, cL):
            await c.close()
        await b.close()
    errs = [e for e in ERRS if 'favicon' not in e[1] and 'ERR_' not in e[1]]
    ok(not errs, f'Keine Seitenfehler {errs[:4]}')
    print(f'\n{NOK[0]} Prüfungen, ' + (f'{len(fails)} FEHLER' if fails else 'ALLES OK') + (' (mit Mischbetrieb 2.8.3)' if URL_ALT else ' (ohne 2.8.3-Ordner)'))
    sys.exit(1 if fails else 0)

asyncio.run(main())
