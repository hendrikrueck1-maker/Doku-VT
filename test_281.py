"""Doku VT 2.8.1 – Test der Änderungen aus 2.8.1 (Python + Playwright/Chromium mit simulierter Kamera).
Aufruf: python3 test_281.py <ordner>"""
import asyncio, sys, subprocess, http.server, threading, functools, os, json, io, struct, zlib
from playwright.async_api import async_playwright
ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get('OUT', '/tmp/doku-vt-test')
os.makedirs(OUT, exist_ok=True)
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT))
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/index.html'
fails = []
def ok(c, m):
    print(('OK   ' if c else 'FAIL ') + m)
    if not c: fails.append(m)

async def newpage(b, w=1180, h=820):
    ctx = await b.new_context(viewport={'width': w, 'height': h}, service_workers='block', permissions=['camera'])
    p = await ctx.new_page(); errs = []
    p.on('pageerror', lambda e: errs.append(str(e)))
    p.on('console', lambda m: errs.append('console: ' + m.text) if m.type == 'error' else None)
    await p.goto(URL); await p.wait_for_function('document.querySelector(".showcard")', timeout=20000)
    return ctx, p, errs

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])
        ctx, p, errs = await newpage(b)
        VER = json.load(open(os.path.join(ROOT, 'version.json')))['version']
        ok(await p.evaluate('APP_VERSION') == VER, 'Version ' + VER)
        await p.evaluate("Settings.set({depts:['L','T','B','R']})")
        await p.evaluate("(async()=>{await Req.ensureHouse(); await Req.maybeDemo(); await Req.maybeTest(); App.render(true);})()")
        hai = await p.evaluate("Repo.liveShows().find(s=>s.f.titel.startsWith('Demo: Der Haifisch')).id")
        await p.evaluate(f"location.hash='#/show/{hai}'"); await p.wait_for_timeout(700)

        # ---- 1–3: Kästen getrennt, Reihenfolge, Vor der Vorstellung nur vorher ----
        boxes = await p.evaluate("[...document.querySelectorAll('[data-setup] > [data-box]')].map(x=>x.dataset.box)")
        print('   Kästen:', boxes)
        ok(boxes[:3] == ['hint-L', 'hint-T', 'run'] and boxes.index('abl-L') < boxes.index('L') and boxes.index('abl-B') < boxes.index('B'),
           'Reihenfolge: Hinweise → Vor der Vorstellung → Ablauf → Beleuchterzüge / Positionen')
        ok(await p.evaluate("!document.querySelector('[data-box=L] .ablsec') && !!document.querySelector('[data-box=abl-L] .ablsec')"), 'Licht: Beleuchterzüge und Ablauf getrennt')
        ok(await p.evaluate("!document.querySelector('[data-box=B] .ablsec') && !!document.querySelector('[data-box=B] .ztab')"), 'Bühne: Positionen eigener Kasten')
        vor = await p.evaluate(f"RunList.items('{hai}',['L','T','B']).filter(i=>i.vor).map(i=>i.key)")
        ok('bl:d2' in vor and 'bl:d1' not in vor and 'bt:d1' not in vor and 'b:d1' in vor and 'b:d4' not in vor and 'ci:d1' in vor,
           'Vor der Vorstellung: nur feste Punkte und Ablauf „vorher“ (Pausenumbau nicht)')
        # Durchgang beginnen und Vor der Vorstellung zeigt Grund-Schritt, nicht Pause
        await p.click('[data-box=run] [data-run=start]'); await p.wait_for_timeout(500)
        runkeys = await p.evaluate("[...document.querySelectorAll('[data-box=run] .runchk')].map(b=>b.dataset.run)")
        ok('bl:d2' in runkeys and 'bl:d1' not in runkeys, 'Kasten „Vor der Vorstellung“ ohne Pausen-Schritt')
        # Ablauf abhakbar
        await p.wait_for_timeout(400); await p.click('[data-box=abl-L] > summary h3'); await p.wait_for_timeout(200)
        await p.click('[data-box=abl-L] .runchk[data-run="bl:d1"]'); await p.wait_for_timeout(500)
        r = await p.evaluate(f"(()=>{{const r=RunList.runsOf('{hai}')[0]; return [!!(r.f['h:bl:d1']&&r.f['h:bl:d1'].ok), document.querySelector('[data-box=abl-L] .runrow').classList.contains('ok'), document.querySelector('[data-setup] [data-box=abl-L]').open]}})()")
        print('  ', r)
        ok(r == [True, True, True], 'Ablauf Licht abhakbar (gleicher Durchgang), Kasten bleibt offen')
        q = await p.evaluate("[...document.querySelectorAll('[data-qrow] .qb')].map(b=>b.textContent.trim())")
        print('   Schnellzugriff:', q)
        ok(any(x.startswith('Licht · Ablauf') and '1/1' in x for x in q), 'Schnellzugriff zeigt Ablauf-Fortschritt')
        # Ablauf abhaken ohne Durchgang legt ihn an (zweite Veranstaltung)
        sid = await p.evaluate("(async()=>{const s=await Repo.createShow('Ohne Durchgang',['L']); await Repo.patchShow(s.id,{'bl:x1':{abschnitt:'pause',text:'Kugel einhängen',entryId:'',ord:10,del:false}}); return s.id})()")
        await p.evaluate(f"location.hash='#/show/{sid}'"); await p.wait_for_timeout(500)
        await p.evaluate("SetupView.open['abl-L']=true; App.render()"); await p.wait_for_timeout(200)
        await p.click('[data-box=abl-L] .runchk'); await p.wait_for_timeout(600)
        ok(await p.evaluate(f"RunList.runsOf('{sid}').length===1 && RunList.runsOf('{sid}')[0].f['h:bl:x1'].ok"), 'Abhaken im Ablauf ohne begonnenen Durchgang legt ihn an')
        # Hinweis: eigener Knopf im Bearbeitungsmodus
        await p.evaluate(f"location.hash='#/show/{hai}'"); await p.wait_for_timeout(400)
        await p.evaluate("App.state.edit=true; App.render()"); await p.wait_for_timeout(300)
        ok(await p.evaluate("!!document.querySelector('.hintadd[data-abt=B]')"), 'Ohne Hinweis: Knopf „Hinweis Einrichten · Bühne“')
        await p.click('.hintadd[data-abt=B]'); await p.wait_for_timeout(300)
        await p.fill('[data-editor] textarea[name=t]', 'Podest nur zu zweit'); await p.click('[data-editor] [data-ok]'); await p.wait_for_timeout(600)
        ok(await p.evaluate("[...document.querySelectorAll('.hintbox h3')].length===3 && document.querySelector('.hintbox[data-abt=B] .hbt').textContent==='Podest nur zu zweit'"), 'Hinweis Bühne gespeichert, Kasten oben')
        await p.screenshot(path=f'{OUT}/281_kaesten.png', full_page=False)

        # ---- 4: Sub ----
        eid = await p.evaluate(f"Repo.entriesOf('{hai}').find(e=>abtOf(e)==='L' && e.f.kreis==='45').id")
        await p.evaluate(f"Editor.open({{showId:'{hai}', entryId:'{eid}'}})"); await p.wait_for_timeout(400)
        ok(await p.evaluate("!!document.querySelector('[data-editor] details.more [name=sub]')"), 'Feld „Sub“ unter Weitere Angaben')
        await p.evaluate("document.querySelector('[data-editor] details.more').open=true")
        await p.fill('[data-editor] [name=sub]', '3 7')
        await p.click('[data-editor] .sheet-h [data-act=save]'); await p.wait_for_timeout(600)
        ok(await p.evaluate(f"Repo.entry('{eid}').f.sub") == '3+7', 'Sub gespeichert und normalisiert (3+7)')
        card = await p.evaluate(f"(()=>{{const c=document.querySelector('.card[data-key^=\"{eid}\"]'); return [c.querySelector('.kcol .krow .ksub')?.textContent, [...c.querySelectorAll('.chip b')].map(x=>x.textContent)]}})()")
        ok(card[0] == 'SUB3+7' and 'Sub' not in card[1], f'Karte: Sub neben dem Kreis, nicht als Chip ({card[0]})')
        ok(await p.evaluate("document.querySelectorAll('.card .ksub').length") == 1, 'Sub erscheint nur, wenn eingetragen')
        await p.evaluate("App.state.edit=false; App.render()")
        await p.evaluate(f"App.openDetailSheet('{eid}')"); await p.wait_for_timeout(300)
        ok(await p.evaluate("!!document.querySelector('.sheet .detail .dh .kreis .ksub')"), 'Detail: Sub neben dem Kreis')
        await p.evaluate("history.back()"); await p.wait_for_timeout(300)
        await p.evaluate("Settings.set({view:'big'}).then(()=>{App.renderToolbar();App.renderList()})"); await p.wait_for_timeout(400)
        ok(await p.evaluate(f"!!document.querySelector('.card[data-key^=\"{eid}\"] .bighead .bk .ksub')"), 'Großbild: Sub im Kopf neben dem Kreis')
        await p.evaluate("Settings.set({view:'list'}).then(()=>{App.renderToolbar();App.renderList()})"); await p.wait_for_timeout(300)
        await p.screenshot(path=f'{OUT}/281_sub.png')
        n = await p.evaluate(f"(async()=>{{const b=await Pdf.build('{hai}',{{kat:'all',depts:['L'],cover:true,compact:true}}); window._pdf=Array.from(new Uint8Array(await b.arrayBuffer())); return Pdf.lastPages}})()")
        open(f'{OUT}/281_licht.pdf', 'wb').write(bytes(await p.evaluate('window._pdf')))
        txt = subprocess.run(['pdftotext', '-layout', f'{OUT}/281_licht.pdf', '-'], capture_output=True, text=True).stdout
        ok(subprocess.run(['qpdf', '--check', f'{OUT}/281_licht.pdf'], capture_output=True).returncode == 0, 'PDF Licht: qpdf --check')
        ok(txt.count('45 · Sub 3+7') >= 2, 'PDF: Sub neben dem Kreis (Inhaltsverzeichnis und Infoblock)')
        pg = txt.split('\f')
        chap = next(x for x in pg if 'VOR DER VORSTELLUNG' in x)
        ok('HINWEIS EINRICHTEN' in chap and 'HINWEIS EINRICHTEN / ABLAUF' not in chap and chap.index('VOR DER VORSTELLUNG') < chap.index('ABLAUF')
           and 'OHP am Gerät' in chap[chap.index('VOR DER VORSTELLUNG'):chap.index('\nABLAUF')], 'PDF: Hinweis, Vor der Vorstellung (mit Ablauf vorher), dann Ablauf')

        # ---- 5: Foto in andere Phase kopieren ----
        e361 = await p.evaluate(f"Repo.entriesOf('{hai}').find(e=>e.f.kreis==='361').id")
        before = await p.evaluate(f"[Repo.photosOf('{e361}','A').length, Repo.photosOf('{e361}','E').length]")
        await p.evaluate("App.state.edit=true; App.render()")
        await p.evaluate(f"Editor.open({{showId:'{hai}', entryId:'{e361}'}})"); await p.wait_for_timeout(400)
        await p.click('[data-editor] .pgrid[data-k=A] .slot:not(.add) >> nth=0'); await p.wait_for_timeout(200)
        labels = await p.evaluate("[...document.querySelectorAll('.dialog .btn')].map(b=>b.textContent.trim())")
        ok(any('kopieren' in x for x in labels), 'Foto-Menü: „Zu „Einleuchten“ kopieren“')
        await p.click('.dialog .btn:has-text("kopieren")'); await p.wait_for_timeout(300)
        ok(await p.evaluate("document.querySelectorAll('[data-editor] .pgrid[data-k=E] .slot:not(.add)').length") == before[1] + 1, 'Kopie steht unter Einleuchten')
        await p.click('[data-editor] .sheet-h [data-act=save]'); await p.wait_for_timeout(600)
        r = await p.evaluate(f"(()=>{{const a=Repo.photosOf('{e361}','A'), e=Repo.photosOf('{e361}','E'); return [a.length, e.length, e.some(x=>x.b===a[0].b)]}})()")
        ok(r == [before[0], before[1] + 1, True], f'Gespeichert: Aufbau {r[0]}, Einleuchten {r[1]}, Bilddaten geteilt')

        # ---- 6: Requisite „Vor der Vorstellung“ sichtbar und vorgewählt ----
        tid = 'test-r-show'
        await p.evaluate(f"location.hash='#/show/{tid}'"); await p.wait_for_timeout(500)
        await p.evaluate(f"Editor.open({{showId:'{tid}', abt:'R'}})"); await p.wait_for_timeout(400)
        chips = await p.evaluate("[...document.querySelectorAll('[data-rwann] button')].map(b=>[b.textContent.trim(), b.getAttribute('aria-pressed')])")
        print('   Wann gebraucht:', chips)
        ok(chips and chips[0][0] == 'Vor der Vorstellung' and chips[0][1] == 'true', 'Neuer Gegenstand: „Vor der Vorstellung“ sichtbar und vorgewählt')
        await p.fill('[data-editor] [name=was]', 'Testfeder')
        await p.click('[data-rwann] button >> nth=0')     # abwählen – ohne Wirkung auf Einrichten
        await p.click('[data-editor] .sheet-h [data-act=save]'); await p.wait_for_timeout(700)
        fe = await p.evaluate(f"Req.entriesR('{tid}').find(e=>e.f.was==='Testfeder').id")
        ok(await p.evaluate(f"RunList.items('{tid}',['R']).some(i=>i.key===Req.setupKey(Repo.entry('{fe}')))"), 'Auch ohne „Vor der Vorstellung“ in der Einrichten-Checkliste')
        ex = await p.evaluate(f"Req.entriesR('{tid}').find(e=>e.f.was==='Lesebrille').id")
        await p.evaluate(f"Editor.open({{showId:'{tid}', entryId:'{ex}'}})"); await p.wait_for_timeout(400)
        ok(await p.evaluate("document.querySelector('[data-rwann] button').getAttribute('aria-pressed')") == 'true', 'Bestehender Gegenstand ohne Angabe: „Vor der Vorstellung“ angezeigt')
        await p.evaluate("history.back()"); await p.wait_for_timeout(300)

        # ---- 7: Ensemble sofort sichtbar ----
        await p.evaluate(f"Req.editPersons('{tid}')"); await p.wait_for_timeout(300)
        await p.click('[data-la=ens]'); await p.wait_for_timeout(300)
        await p.locator('[data-la=add]').last.click(); await p.wait_for_timeout(300)
        await p.fill('[data-editor] [name=name]', 'Neue Kollegin'); await p.click('[data-editor] [data-ok]'); await p.wait_for_timeout(500)
        ok(await p.evaluate("[...document.querySelectorAll('.rrow b')].some(x=>x.textContent==='Neue Kollegin')"), 'Ensemble-Liste zeigt die neue Person')
        await p.evaluate("history.back()"); await p.wait_for_timeout(500)
        ok(await p.evaluate("[...document.querySelectorAll('[data-la=take]')].some(x=>x.textContent.includes('Neue Kollegin'))"), 'Personen des Stücks: neue Person sofort unter „Aus dem Ensemble“')
        await p.evaluate("history.back()"); await p.wait_for_timeout(300)

        # ---- 8: Hinterbühne ----
        r = await p.evaluate("""(async()=>{const k=Req.houseKey('Hinterbühne'); const n1=Req.houseF()[k].name;
          await Repo.patchHouse({[k]:Object.assign({},Req.houseF()[k],{name:'Bühne hinten'})}); await Req.migrateHouse();
          return [k, n1, Req.houseF()[k].name, Req.houseOrts().filter(o=>/Bühne hinten|Hinterbühne/.test(o.name)).length]})()""")
        ok(r == ['ho:std-buehne-hinten', 'Hinterbühne', 'Hinterbühne', 1], f'Haus-Ort heißt „Hinterbühne“, Kennung bleibt, alter Name wird angepasst ({r})')
        ok(await p.evaluate(f"Req.val(Req.entriesR('{tid}').find(e=>e.f.was==='Stuhl (Spielstuhl)'),'ort')") == 'Hinterbühne', 'Gegenstand zeigt „Hinterbühne“')

        # ---- 9: Foto aus der Galerie ----
        await p.evaluate(f"location.hash='#/show/{hai}'"); await p.wait_for_timeout(400)
        r = await p.evaluate("""(async()=>{
          const mk=(w,h)=>new Promise(r=>{const c=document.createElement('canvas'); c.width=w; c.height=h; const g=c.getContext('2d'); g.fillStyle='#3a7'; g.fillRect(0,0,w,h); c.toBlob(b=>r(new File([b],'IMG_1.jpg',{type:'image/jpeg'})),'image/jpeg',0.9)});
          const big=await mk(4000,3000);
          const t0=performance.now(); const a=await Promise.all([Photo.fromFile(big), Photo.fromFile(await mk(1200,1600)), Photo.fromFile(await mk(800,800))]);
          const bad=new File([new Uint8Array([1,2,3,4,5,6,7,8,9])],'kaputt.jpg',{type:'image/jpeg'});
          const heic=new File([new Uint8Array([0,0,0,24,102,116,121,112,104,101,105,99,0,0,0,0,1,2,3,4])],'IMG_2.heic',{type:''});
          const e1=await Photo.fromFile(bad).then(()=>'ok',e=>e.message); const e2=await Photo.fromFile(heic).then(()=>'ok',e=>e.heic?'heic':e.message);
          return [a.map(x=>x.w).join(','), Math.round(performance.now()-t0)<20000, e1, e2, Sync.state.log.filter(l=>l.msg.startsWith('Foto nicht übernommen')).length]})()""")
        print('  ', r)
        ok(r[0] == '1600,1200,800' and r[1], 'Mehrere Galerie-Fotos nacheinander übernommen (1:1, höchstens 1600 px)')
        ok(r[2].startswith('Bild konnte nicht gelesen werden') and r[3] == 'heic' and r[4] == 2, 'Kaputtes Bild / HEIF: klare Meldung statt Hängen, im Protokoll')
        # über die Oberfläche: Editor → Kamera → Mediathek
        await p.evaluate("App.state.edit=true; App.render()")
        await p.evaluate(f"Editor.open({{showId:'{hai}', abt:'L'}})"); await p.wait_for_timeout(300)
        await p.fill('[data-editor] [name=kreis]', '777')
        await p.click('[data-editor] .pk[data-k=A] [data-act=cam]'); await p.wait_for_timeout(800)
        jpg = await p.evaluate("new Promise(r=>{const c=document.createElement('canvas'); c.width=3000; c.height=2000; c.getContext('2d').fillRect(0,0,10,10); c.toBlob(async b=>r(Array.from(new Uint8Array(await b.arrayBuffer()))),'image/jpeg',0.9)})")
        await p.set_input_files('.cam input[type=file][multiple]', files=[{'name': 'a.jpg', 'mimeType': 'image/jpeg', 'buffer': bytes(jpg)}, {'name': 'b.jpg', 'mimeType': 'image/jpeg', 'buffer': bytes(jpg)},
                                {'name': 'c.heic', 'mimeType': 'image/heic', 'buffer': bytes([0,0,0,24,102,116,121,112,104,101,105,99,0,0,0,0])}])
        await p.wait_for_timeout(2500)
        dlg = await p.evaluate("document.querySelector('.dialog h2')?.textContent || ''")
        if dlg: await p.click('.dialog .btn'); await p.wait_for_timeout(300)
        if await p.evaluate("!!document.querySelector('.cam')"): await p.click('.cam [data-a=done]')
        await p.wait_for_timeout(400)
        n = await p.evaluate("[document.querySelectorAll('[data-editor] .pgrid[data-k=A] .slot:not(.add)').length, document.querySelectorAll('[data-editor] .slot .busy').length, document.querySelector('[data-editor] .savebtn').disabled]")
        ok(n == [2, 0, False] and 'nicht gelesen' in dlg, f'Mediathek im Editor: 2 Fotos übernommen, HEIF-Hinweis, Speichern frei ({n}, „{dlg}“)')
        await p.click('[data-editor] .sheet-h [data-act=save]'); await p.wait_for_timeout(600)
        ok(await p.evaluate(f"(()=>{{const e=Repo.entriesOf('{hai}').find(x=>x.f.kreis==='777'); return e && Repo.photosOf(e.id,'A').length===2}})()"), 'Eintrag mit 2 Galerie-Fotos gespeichert')

        # ---- Smartphone ----
        ctx2, p2, errs2 = await newpage(b, 390, 844)
        await p2.evaluate("Settings.set({depts:['L','T','B']})")
        await p2.evaluate(f"(async()=>{{const e=Repo.entriesOf(Repo.liveShows().find(s=>s.f.titel.startsWith('Demo: Der Haifisch')).id).find(e=>e.f.kreis==='12+17+103+113+620'); await Repo.saveDraft({{id:e.id, showId:e.showId, abt:'L', f:{{sub:'12'}}, photos:{{A:[],E:Repo.photosOf(e.id,'E').map(p=>({{photoId:p.id,b:p.b,w:p.w,h:p.h}}))}}, initialPhotos:new Set()}})}})()")
        h2 = await p2.evaluate("Repo.liveShows().find(s=>s.f.titel.startsWith('Demo: Der Haifisch')).id")
        await p2.evaluate(f"location.hash='#/show/{h2}'"); await p2.wait_for_timeout(700)
        await p2.evaluate("App.state.edit=true; App.render()"); await p2.wait_for_timeout(300)
        ok(await p2.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"), 'Smartphone: kein waagrechtes Scrollen')
        await p2.screenshot(path=f'{OUT}/281_phone_top.png')
        await p2.evaluate("document.querySelector('.card .ksub').scrollIntoView({block:'center'})"); await p2.wait_for_timeout(300)
        await p2.screenshot(path=f'{OUT}/281_phone_sub.png')
        allerr = errs + errs2
        ok(not allerr, 'Keine Seitenfehler ' + ('' if not allerr else str(allerr[:5])))
        await b.close()
    print('\n' + ('ALLES OK' if not fails else f'{len(fails)} FEHLER'))
asyncio.run(main())
