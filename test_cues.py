"""Doku VT 2.8.x – automatischer Test der Cue-Fotos (Python + Playwright/Chromium mit simulierter Kamera).
Aufruf: python3 test_cues.py <ordner 2.8.x> [<ordner 2.7.0>]"""
import asyncio, sys, subprocess, http.server, threading, functools, os
from playwright.async_api import async_playwright
ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
ALT = sys.argv[2] if len(sys.argv) > 2 else None
OUT = os.environ.get('OUT', '/tmp/doku-vt-test')
os.makedirs(OUT, exist_ok=True)
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
def serve(d):
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=d))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f'http://127.0.0.1:{srv.server_address[1]}/index.html'
URL = serve(ROOT); URL_ALT = serve(ALT) if ALT else None
fails = []
def ok(c, m):
    print(('OK   ' if c else 'FAIL ') + m)
    if not c: fails.append(m)

async def newpage(b, w=1180, h=820, url=None):
    ctx = await b.new_context(viewport={'width': w, 'height': h}, service_workers='block', permissions=['camera'])
    p = await ctx.new_page(); errs = []
    p.on('pageerror', lambda e: errs.append(str(e)))
    p.on('console', lambda m: errs.append('console: ' + m.text) if m.type == 'error' else None)
    await p.goto(url or URL); await p.wait_for_function('document.querySelector(".showcard") || document.querySelector(".empty")', timeout=20000)
    return ctx, p, errs

async def idle(p):
    await p.wait_for_function('CueCam.pending()===0 && !CueCam.busy', timeout=20000); await p.wait_for_timeout(200)

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])
        ctx, p, errs = await newpage(b)
        ok(await p.evaluate('APP_VERSION') == open(os.path.join(ROOT, 'version.json')).read().split('"')[3], 'Version aus version.json')
        # ---- Nummern ----
        r = await p.evaluate("""[Cues.norm('12,50'), Cues.norm(' Q 007 '), Cues.norm('.5'), Cues.nextNr('12.5'), Cues.nextNr('12'), Cues.letter(0)+Cues.letter(2)+Cues.letter(26),
          ['13','12.5','2','12','Ende','0.5'].sort((a,b)=>Cues.cmpNr(a,b)).join(' ')]""")
        print('  ', r)
        ok(r[:6] == ['12.5', '7', '0.5', '13', '13', 'ACAA'] and r[6] == '0.5 2 12 12.5 13 Ende', 'Cue-Nummern: Komma, Hochzählen 12.5→13, Sortierung, Buchstaben')
        # ---- Startseite: Umschalter ----
        ok(await p.evaluate("!!document.querySelector('.hometabs [data-act=gocues]')"), 'Startseite: Umschalter Dokumentation | Cue-Fotos')
        await p.click('.hometabs [data-act=gocues]'); await p.wait_for_timeout(400)
        ok(await p.evaluate("location.hash==='#/cues' && !!document.querySelector('[data-cact=newlist]')"), 'Cue-Fotos-Übersicht geöffnet')
        # ---- Liste anlegen über die Oberfläche ----
        await p.click('[data-cact=newlist]'); await p.wait_for_timeout(300)
        await p.fill('#cl-t', 'Zauberflöte HP')
        await p.click('[data-spc] [data-spv="Großes Haus"]')
        await p.fill('#cl-n', 'Hauptprobe 2')
        await p.click('[data-ok]'); await p.wait_for_timeout(600)
        lid = await p.evaluate("App.state.cueListId")
        ok(await p.evaluate("App.state.route==='cue' && App.state.edit && Cues.list(App.state.cueListId).f.spielstaette==='Großes Haus'"), 'Liste angelegt (Titel, Spielstätte), Bearbeitungsmodus an')
        # ---- Vorbereiten: 1–5 ----
        n = await p.evaluate(f"Cues.addRange('{lid}','1','5','1')")
        n2 = await p.evaluate(f"Cues.addRange('{lid}','1','2','0.5')")
        ok(n == 5 and n2 == 1, f'Mehrere anlegen: 1–5 ({n}), 1–2 Schritt 0,5 ergänzt nur 1.5 ({n2})')
        await p.evaluate(f"(async()=>{{const c=Cues.cueByNr('{lid}','1.5'); await Cues.deleteCue(c.id); const d=Cues.cueByNr('{lid}','2'); }})()")
        # ---- Kamera ----
        await p.wait_for_timeout(300)
        await p.click('[data-cact=cam]')
        await p.wait_for_function("document.querySelector('.ccam video') && document.querySelector('.ccam video').videoWidth>0", timeout=15000)
        lbl = await p.evaluate("document.querySelector('.ccam [data-lbl]').textContent")
        ok(lbl == 'Cue 1 · A', 'Kamera startet bei der ersten vorbereiteten Cue ohne Foto: ' + lbl)
        ok(await p.evaluate("!document.querySelector('.ccam .flash') && document.querySelector('.ccam [data-a=torch]').getAttribute('aria-pressed')==='false'"), 'Kein weißer Blitz, Taschenlampe aus')
        t0 = await p.evaluate('performance.now()')
        for _ in range(3): await p.click('.ccam [data-a=shot]')
        t1 = await p.evaluate('performance.now()')
        lbl = await p.evaluate("document.querySelector('.ccam [data-lbl]').textContent")
        ok(lbl == 'Cue 1 · D', f'Auslöser zählt weiter A → B → C, als nächstes D ({lbl}); 3 Fotos in {int(t1 - t0)} ms')
        await p.click('.ccam [data-a=next]')
        await p.click('.ccam [data-a=nr]'); await p.wait_for_timeout(200)
        await p.fill('.dialog input.txt', '12,5'); await p.click('.dialog .btn.primary'); await p.wait_for_timeout(200)
        await p.click('.ccam [data-a=shot]')
        nx = await p.evaluate("document.querySelector('.ccam [data-nx]').textContent")
        await p.click('.ccam [data-a=next]')
        await p.click('.ccam [data-a=shot]')
        await idle(p)
        stat = await p.evaluate("document.querySelector('.ccam .cstat').textContent")
        await p.screenshot(path=f'{OUT}/cue_cam.png')
        r = await p.evaluate(f"Cues.cuesOf('{lid}').map(c=>c.f.nr+':'+Cues.imgsOf(c.id).length).join(' ')")
        print('  ', r, '|', nx, '|', stat)
        ok(r == '1:3 2:1 3:0 4:0 5:0 12.5:1 13:2', 'Nächster Cue nimmt vorbereitete Cue (2), nach 12.5 → 13 (neu angelegt): ' + r)
        ok(nx == '→ 13' and '7 gespeichert' in stat, 'Anzeige „→ 13“, Zähler „7 gespeichert“')
        sz = await p.evaluate(f"(async()=>{{const im=Cues.imgsOf(Cues.cueByNr('{lid}','1').id)[0]; const d=await Repo.full(im.f.b); return [im.f.w, d.byteLength]}})()")
        ok(sz[0] == 1080 or sz[0] <= 1200, f'Foto 1:1, höchstens 1200 px ({sz[0]} px, {sz[1] // 1024} KB)')
        # Telefonbreite: Kamera-Knöpfe sichtbar
        await p.click('.ccam [data-a=close]'); await p.wait_for_timeout(400)
        ok(await p.evaluate("!document.querySelector('.ccam')"), 'Kamera geschlossen')
        # ---- Liste ----
        tiles = await p.evaluate(f"[...document.querySelectorAll('[data-cue=\"'+Cues.cueByNr('{lid}','1').id+'\"] .lt')].map(x=>x.textContent).join('')")
        ok(tiles == 'ABC', 'Liste zeigt Cue 1 mit Bild A, B, C')
        await p.screenshot(path=f'{OUT}/cue_list_edit.png', full_page=True)
        # ---- Cue bearbeiten über die Oberfläche: Notiz/Hinweis je Bild ----
        c1 = await p.evaluate(f"Cues.cueByNr('{lid}','1').id")
        await p.click(f'[data-cue="{c1}"] .cqh'); await p.wait_for_timeout(300)
        await p.fill('#cq-name', 'Sonnenaufgang')
        await p.fill('[data-editor] [data-img] >> nth=1 >> [data-f=notiz]', 'Verfolger auf Papageno')
        await p.fill('[data-editor] [data-img] >> nth=1 >> [data-f=hinweis]', 'Nebel muss laufen')
        await p.click('[data-editor] .sheet-h [data-x=save]'); await p.wait_for_timeout(400)
        r = await p.evaluate(f"(()=>{{const ims=Cues.imgsOf('{c1}'); return [Repo.cues.get('{c1}').f.name, ims[0].f.notiz||'', ims[1].f.notiz, ims[1].f.hinweis]}})()")
        ok(r == ['Sonnenaufgang', '', 'Verfolger auf Papageno', 'Nebel muss laufen'], 'Notiz und Hinweis je Bild getrennt, Name der Cue gemeinsam')
        # ---- Markieren: Original bleibt ----
        r = await p.evaluate(f"""(async()=>{{const im=Cues.imgsOf('{c1}')[0], orig=im.f.b;
          const c=document.createElement('canvas'); c.width=c.height=400; const g=c.getContext('2d'); g.fillStyle='#f00'; g.fillRect(0,0,400,400);
          const r=await Photo.fromCanvas(c); await Cues.patchImg(im.id,{{b:r.b,o:im.f.o||im.f.b,w:r.w,h:r.h}},[r]);
          const a=Repo.cueimgs.get(im.id); const marked=a.f.b!==orig && a.f.o===orig && !!(await Repo.full(orig));
          await Cues.patchImg(im.id,{{b:a.f.o,o:''}}); return [marked, Repo.cueimgs.get(im.id).f.b===orig];}})()""")
        ok(r == [True, True], 'Markieren legt neues Bild an, Original bleibt und lässt sich wiederherstellen')
        # ---- Foto zu anderer Cue, Zusammenführen ----
        r = await p.evaluate(f"""(async()=>{{const im=Cues.imgsOf(Cues.cueByNr('{lid}','13').id)[1]; const t=await Cues.moveImg(im.id,'20');
          return [t.f.nr, Cues.imgsOf(t.id).length, Cues.imgsOf(Cues.cueByNr('{lid}','13').id).length]}})()""")
        ok(r == ['20', 1, 1], 'Foto zu neuer Cue 20 verschoben')
        c2 = await p.evaluate(f"Cues.cueByNr('{lid}','2').id")
        await p.click(f'[data-cue="{c2}"] .cqh'); await p.wait_for_timeout(300)
        await p.fill('#cq-nr', '1'); await p.click('[data-editor] .sheet-h [data-x=save]'); await p.wait_for_timeout(300)
        ok(await p.evaluate("!!document.querySelector('.dialog') && document.querySelector('.dialog h2').textContent.includes('gibt es schon')"), 'Doppelte Nummer: Rückfrage')
        await p.click('.dialog .btn.primary'); await p.wait_for_timeout(600)
        r = await p.evaluate(f"[Cues.imgsOf('{c1}').length, Repo.cues.get('{c2}').f.del, Cues.cuesOf('{lid}').map(c=>c.f.nr).join(' ')]")
        ok(r[0] == 4 and r[1] is True, f'Zusammengeführt: Cue 1 hat jetzt 4 Fotos (A–D) · {r[2]}')
        # ---- Bildansicht (Ansichtsmodus) ----
        await p.evaluate("App.state.edit=false; App.render()"); await p.wait_for_timeout(300)
        await p.click(f'[data-cue="{c1}"] .cqi .th >> nth=1'); await p.wait_for_timeout(500)
        r = await p.evaluate("[document.querySelector('.lbx .infos').textContent, document.querySelector('.lbx .nextk').textContent]")
        ok('12' not in r[0][:3] and 'Bild B' in r[0] and 'Nebel muss laufen' in r[0] and 'Nächster Cue' in r[1], 'Bildansicht: Cue, Bild B, Hinweis, „Nächster Cue“')
        await p.click('.lbx [data-a=nextk]'); await p.wait_for_timeout(500)
        ok('12.5' in await p.evaluate("document.querySelector('.lbx .infos .kreis').textContent"), '„Nächster Cue“ springt zu Cue 12.5')
        await p.keyboard.press('Escape'); await p.wait_for_timeout(300)
        await p.screenshot(path=f'{OUT}/cue_list_view.png', full_page=True)
        # ---- PDF ----
        r = await p.evaluate(f"(async()=>{{const bl=await Pdf.buildCues('{lid}',{{cover:true,compact:false}}); window._pdf=Array.from(new Uint8Array(await bl.arrayBuffer())); return [Pdf.lastPages, Cues.stats('{lid}').imgs]}})()")
        open(f'{OUT}/cues.pdf', 'wb').write(bytes(await p.evaluate('window._pdf')))
        ok(r[0] == r[1] + 1, f'PDF: Deckblatt + ein Foto je Seite ({r[0]} Seiten, {r[1]} Fotos)')
        q = subprocess.run(['qpdf', '--check', f'{OUT}/cues.pdf'], capture_output=True, text=True); ok(q.returncode == 0, 'qpdf --check')
        txt = subprocess.run(['pdftotext', '-layout', f'{OUT}/cues.pdf', '-'], capture_output=True, text=True).stdout
        pages = txt.split('\f')
        ok('CUE-FOTOS' in pages[0] and 'kein Foto' in pages[0] and 'Zauberflöte HP · Großes Haus' in pages[1], 'Deckblatt mit Übersicht (auch ohne Foto), Kopfzeile Stück · Spielstätte · Datum')
        seq = [ln.split('CUE ')[1].split()[0] for pg in pages[1:] for ln in pg.splitlines() if ln.strip().startswith('CUE ') and 'Bild' in ln]
        print('   Reihenfolge im PDF:', seq)
        ok(seq == ['1', '1', '1', '1', '12.5', '13', '20'], 'PDF sortiert nach Cue-Nummer')
        ok('HINWEIS: Nebel muss laufen' in txt and 'Verfolger auf Papageno' in txt and 'Bild B von 4' in txt, 'PDF: Hinweis und Notiz je Bild, „Bild B von 4“')
        sz = os.path.getsize(f'{OUT}/cues.pdf')
        r = await p.evaluate(f"(async()=>{{const bl=await Pdf.buildCues('{lid}',{{cover:false,compact:true}}); return [Pdf.lastPages, bl.size]}})()")
        ok(r[0] == 7 and r[1] < sz, f'PDF ohne Deckblatt, kompakt ({r[0]} Seiten, {r[1] // 1024} KB statt {sz // 1024} KB)')
        # ---- Abgleich ----
        pk = await p.evaluate("(async()=>{const r=await Sync.buildPackage({type:'sync',since:0,depts:['L']}); return [await r.blob.text(), r.formatVersion, r.counts.blobs]})()")
        ok(pk[1] == 4, 'Sync-Paket mit Cue-Fotos hat Format 4')
        hai = await p.evaluate("Repo.liveShows().find(s=>s.f.titel.startsWith('Demo: Der Haifisch')).id")
        r = await p.evaluate(f"(async()=>{{const r=await Sync.buildPackage({{type:'backup',showIds:['{hai}']}}); const d=JSON.parse(await r.blob.text()); return [r.formatVersion, d.cueimgs.length, d.cuelists.length]}})()")
        ok(r == [2, 0, 0], 'Backup einer Veranstaltung ohne Cue-Fotos, bleibt Format 2')
        ctx2, p2, errs2 = await newpage(b, 820, 1180)
        await p2.evaluate("Settings.set({depts:['T'], demoOnFirstStart:false})")
        st = await p2.evaluate("async t=>{const r=await Sync.importPackage(new File([t],'x.json')); return [r.bilder, r.missing, r.ungueltig]}", pk[0])
        r = await p2.evaluate(f"[Cues.lists().length, Cues.cuesOf('{lid}').length, Cues.stats('{lid}').imgs]")
        ok(st[1] == 0 and st[2] == 0 and r[0] == 1 and r[2] == 7, f'Gerät B (nur Ton) bekommt Liste, Cues und alle Bilder ({st[0]} Bilder, fehlend {st[1]})')
        await p2.evaluate(f"location.hash='#/cue/{lid}'"); await p2.wait_for_timeout(1000)
        nimg = await p2.evaluate("[...document.querySelectorAll('.cqi .th img')].filter(i=>i.classList.contains('ok')).length")
        ok(nimg >= 4, f'Gerät B zeigt die Cue-Fotos ({nimg})')
        # Notiz auf B, Foto auf A, dann gegenseitig → beides bleibt
        await p2.evaluate(f"Cues.patchImg(Cues.imgsOf('{c1}')[0].id,{{notiz:'von B'}})")
        await p.evaluate(f"(async()=>{{const c=document.createElement('canvas'); c.width=c.height=300; const r=await Photo.fromCanvas(c); const im=Rec.create({{listId:'{lid}'}},{{cueId:'{c1}',ord:9,b:r.b,o:'',w:300,h:300,notiz:'',hinweis:'',del:false}}); await Repo._write({{cueimgs:[im],fulls:[{{id:r.b,d:r.full}}],thumbs:[{{id:r.b,d:r.thumb}}]}});}})()")
        pa = await p.evaluate("(async()=>{const r=await Sync.buildPackage({type:'sync',since:0}); return await r.blob.text()})()")
        pb = await p2.evaluate("(async()=>{const r=await Sync.buildPackage({type:'sync',since:0}); return await r.blob.text()})()")
        await p2.evaluate("async t=>{await Sync.importPackage(new File([t],'x.json'))}", pa)
        await p.evaluate("async t=>{await Sync.importPackage(new File([t],'x.json'))}", pb)
        ra = await p.evaluate(f"[Cues.imgsOf('{c1}').length, Cues.imgsOf('{c1}')[0].f.notiz]")
        rb = await p2.evaluate(f"[Cues.imgsOf('{c1}').length, Cues.imgsOf('{c1}')[0].f.notiz]")
        ok(ra == rb == [5, 'von B'], f'Gleichzeitig: Notiz von B und neues Foto von A gehen auf beiden Geräten durch ({ra}, {rb})')
        # alte Version lehnt Format 4 ab
        if URL_ALT:
            ctx3, p3, errs3 = await newpage(b, url=URL_ALT)
            msg = await p3.evaluate("async t=>{try{await Sync.importPackage(new File([t],'x.json')); return 'angenommen'}catch(e){return e.message}}", pk[0])
            ok('neueren Doku VT-Version' in msg, '2.7.0 lehnt Paket mit Cue-Fotos ab: ' + msg[:60])
            pk_old = await p.evaluate("(async()=>{const a=[...Repo.cuelists.values()]; const r=await Sync.buildPackage({type:'backup',showIds:[Repo.liveShows().find(s=>s.f.titel.startsWith('Demo: Der Haifisch')).id]}); return await r.blob.text()})()")
            msg = await p3.evaluate("async t=>{try{const r=await Sync.importPackage(new File([t],'x.json')); return 'ok '+r.ungueltig}catch(e){return e.message}}", pk_old)
            ok(msg == 'ok 0', '2.7.0 liest Pakete ohne Cue-Fotos weiter: ' + msg)
            await ctx3.close()
        # ---- Live-Abgleich: Cue-Fotos laufen sofort durch ----
        try:
            code = await p.evaluate("(async()=>{window._s=new PeerSession(); return await window._s.createOffer()})()")
            ans = await p2.evaluate("async c=>{window._s=new PeerSession(); return await window._s.acceptOffer(await PeerAdapter.decodeSignal(c))}", code)
            await p.evaluate("async a=>{await window._s.acceptAnswer(await PeerAdapter.decodeSignal(a))}", ans)
            await p.wait_for_function("window._s.initialDone", timeout=20000)
            await p.evaluate(f"(async()=>{{const c=document.createElement('canvas'); c.width=c.height=320; c.getContext('2d').fillRect(0,0,50,50); const r=await Photo.fromCanvas(c); const im=Rec.create({{listId:'{lid}'}},{{cueId:'{c1}',ord:10,b:r.b,o:'',w:320,h:320,notiz:'live',hinweis:'',del:false}}); window._lb=r.b; await Repo._write({{cueimgs:[im],fulls:[{{id:r.b,d:r.full}}],thumbs:[{{id:r.b,d:r.thumb}}]}});}})()")
            lb = await p.evaluate('window._lb')
            await p2.wait_for_function(f"Cues.imgsOf('{c1}').some(i=>i.f.notiz==='live')", timeout=10000)
            await p2.wait_for_function(f"Repo.full('{lb}').then(d=>window._has=!!d) && window._has", timeout=10000, polling=300)
            ok(True, 'Live-Abgleich: neues Cue-Foto samt Bild sofort auf Gerät B')
        except Exception as e:
            ok(False, 'Live-Abgleich: ' + str(e)[:120])
        # ---- Aufräumen und Papierkorb ----
        r = await p.evaluate(f"(async()=>{{const o=await Repo.orphanBlobs(); const mine=Cues.blobRefs(false); return [mine.length, o.filter(b=>mine.includes(b)).length]}})()")
        ok(r[0] >= 8 and r[1] == 0, f'„Speicher aufräumen“ fasst Cue-Fotos nicht an ({r[0]} Bilder geschützt)')
        r = await p.evaluate(f"""(async()=>{{const mine=Cues.blobRefs(false); await Cues.deleteList('{lid}');
          const kept=(await Repo.orphanBlobs()).filter(b=>mine.includes(b)).length; const inTrash=Cues.deletedLists().length;
          await Cues.restoreList('{lid}'); const back=Cues.stats('{lid}').imgs;
          const n=await Cues.purgeList('{lid}'); const left=(await Promise.all(mine.map(b=>Repo.full(b)))).filter(Boolean).length;
          return [kept, inTrash, back, n, left, Cues.lists().length, Cues.deletedLists().length]}})()""")
        print('  ', r)
        ok(r[0] == 0 and r[1] == 1 and r[2] >= 8, 'Papierkorb behält die Bilder, Wiederherstellen bringt alle Fotos zurück')
        ok(r[3] >= 8 and r[4] == 0 and r[5] == 0 and r[6] == 0, f'Endgültig löschen gibt den Speicher frei ({r[3]} Bilder entfernt)')
        # Löschen kommt per Abgleich auf Gerät B an, dort werden die Bilder beim Aufräumen frei
        pa = await p.evaluate("(async()=>{const r=await Sync.buildPackage({type:'sync',since:0}); return await r.blob.text()})()")
        await p2.evaluate("async t=>{await Sync.importPackage(new File([t],'x.json'))}", pa)
        r = await p2.evaluate("(async()=>{const n=(await Repo.orphanBlobs()).length; const d=await Repo.cleanup(); return [Cues.lists().length, n, d]})()")
        ok(r[0] == 0 and r[2] >= 8, f'Gerät B: Liste weg, „Speicher aufräumen“ gibt {r[2]} Bilder frei')
        # ---- Telefonbreite ----
        ctx4, p4, errs4 = await newpage(b, 390, 844)
        l2 = await p4.evaluate("(async()=>{const l=await Cues.createList({titel:'Telefon-Test',spielstaette:'Spiegelhalle'}); await Cues.addRange(l.id,'1','12','1'); return l.id})()")
        await p4.evaluate(f"App.state.edit=true; location.hash='#/cue/{l2}'"); await p4.wait_for_timeout(600)
        ok(await p4.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"), 'Smartphone: Cue-Liste ohne waagrechtes Scrollen')
        await p4.screenshot(path=f'{OUT}/cue_phone_list.png')
        await p4.click('[data-cact=cam]')
        await p4.wait_for_function("document.querySelector('.ccam video') && document.querySelector('.ccam video').videoWidth>0", timeout=15000)
        r = await p4.evaluate("""(()=>{const vis=s=>{const r=document.querySelector(s).getBoundingClientRect(); return r.bottom<=innerHeight && r.right<=innerWidth && r.width>0};
          return [vis('.ccam .shutter'), vis('.ccam .cnext'), vis('.ccam .cnr'), Math.round(document.querySelector('.ccam .shutter').getBoundingClientRect().width)]})()""")
        await p4.screenshot(path=f'{OUT}/cue_phone_cam.png')
        ok(r[:3] == [True, True, True] and r[3] >= 84, f'Smartphone-Kamera: Auslöser ({r[3]} px), „Nächster Cue“ und Nummer im Bild')
        await p4.click('.ccam [data-a=close]')
        # Rotlicht
        await p4.evaluate("Settings.set({theme:'red'})"); await p4.wait_for_timeout(200)
        await p4.screenshot(path=f'{OUT}/cue_phone_red.png')
        # ---- Startseite Dokumentation unverändert erreichbar ----
        await p.evaluate("location.hash='#/'"); await p.wait_for_timeout(400)
        ok(await p.evaluate("document.querySelectorAll('.showcard').length>=1 && document.querySelector('.hometabs [data-act=godocs]').getAttribute('aria-pressed')==='true'"), 'Dokumentation weiterhin Startseite')
        allerr = errs + errs2 + errs4
        ok(not allerr, 'Keine Seitenfehler ' + ('' if not allerr else str(allerr[:5])))
        await b.close()
    print('\n' + ('ALLES OK' if not fails else f'{len(fails)} FEHLER'))
asyncio.run(main())
