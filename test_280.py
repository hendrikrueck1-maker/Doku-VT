import asyncio, sys, subprocess, http.server, threading, functools, os, json
from playwright.async_api import async_playwright
ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get('OUT', '/tmp/doku-vt-test')
os.makedirs(OUT, exist_ok=True)
H = http.server.SimpleHTTPRequestHandler
class Q(H):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{port}/index.html'
fails = []
def ok(c, m):
    print(('OK   ' if c else 'FAIL ') + m)
    if not c: fails.append(m)

async def newpage(b, w=1180, h=820):
    ctx = await b.new_context(viewport={'width': w, 'height': h}, service_workers='block')
    p = await ctx.new_page(); errs = []
    p.on('pageerror', lambda e: errs.append(str(e)))
    p.on('console', lambda m: errs.append('console: ' + m.text) if m.type == 'error' else None)
    await p.goto(URL); await p.wait_for_function('document.querySelector(".showcard")', timeout=20000)
    return ctx, p, errs

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        ctx, p, errs = await newpage(b)
        ok(await p.evaluate('APP_VERSION') == '2.8.0', 'Version 2.8.0')
        await p.evaluate("Settings.set({depts:['L','T','B','R']})")
        await p.evaluate("(async()=>{await Req.ensureHouse(); await Req.maybeDemo(); await Req.maybeTest(); App.render(true);})()")
        await p.wait_for_timeout(600)
        titles = await p.evaluate("[...document.querySelectorAll('.showcard h3')].map(x=>x.textContent)")
        print('  Startseite:', titles)
        sid = await p.evaluate("(async()=>{const s=await Repo.createShow('Zauberflöte',['L','T','B']); App.render(true); return s.id})()")
        await p.wait_for_timeout(300)
        titles = await p.evaluate("[...document.querySelectorAll('.showcard h3')].map(x=>x.textContent)")
        ok(titles[0] == 'Zauberflöte' and all(App for App in titles) and all(t.startswith(('Demo', 'Testvorstellung')) for t in titles[1:]), 'Demo/Test am Ende: ' + ' | '.join(titles))
        hai = await p.evaluate("Repo.liveShows().find(s=>s.f.titel.startsWith('Demo: Der Haifisch')).id")
        await p.evaluate(f"location.hash='#/show/{hai}'"); await p.wait_for_timeout(700)
        ok(await p.evaluate("document.querySelectorAll('.hintbox').length") >= 2, 'Hinweis-Kästen immer offen (Licht, Ton)')
        ok('Hinweis Einrichten / Ablauf' in await p.evaluate("document.querySelector('.hintbox h3').textContent"), 'Schriftzug „Hinweis Einrichten / Ablauf“')
        q = await p.evaluate("[...document.querySelectorAll('[data-qrow] .qb')].map(b=>b.textContent.trim())")
        ok(any('Beleuchterzüge' in x for x in q) and any('Vor der Vorstellung' in x for x in q), 'Schnellzugriff: ' + ' | '.join(q))
        ok('Beleuchterzüge' in await p.evaluate("document.querySelector('details.setup[data-abt=L] h3').textContent"), 'Kasten Licht heißt „Beleuchterzüge“')
        ok(await p.evaluate("document.querySelectorAll('.card .wbadge').length") >= 1, 'Warnhinweis auf der Karte')
        ok(await p.evaluate("[...document.querySelectorAll('.card .estp')].some(x=>x.textContent.includes('Pausenumbau'))"), 'Ablauf-Hinweis auf der Karte')
        ok(await p.evaluate("[...document.querySelectorAll('.card .chip b')].some(x=>x.textContent==='Position')"), 'Weitere Angaben (Position) auf der Karte')
        # Checkliste enthält Ablauf Licht
        it = await p.evaluate(f"RunList.items('{hai}',['L','T','B']).map(i=>i.key)")
        ok(any(k.startswith('bl:') for k in it) and any(k.startswith('bt:') for k in it), 'Checkliste enthält Ablauf Licht + Ton')
        # Sprung
        await p.evaluate("window.scrollTo(0,3000)"); await p.click('[data-qrow] [data-box=L]'); await p.wait_for_timeout(700)
        ok(await p.evaluate("document.querySelector('details.setup[data-abt=L]').open"), 'Schnellzugriff klappt Beleuchterzüge auf')
        # Großbild
        await p.evaluate("Settings.set({view:'big'}).then(()=>{App.renderToolbar();App.renderList()})"); await p.wait_for_timeout(500)
        ok(await p.evaluate("document.querySelectorAll('.bigsticky .bigfields').length") >= 3, 'Großbild: fixierte Leiste mit Feldern')
        labels = await p.evaluate("[...document.querySelector('.card[data-abt=L] .bigfields').querySelectorAll('small')].map(x=>x.textContent)")
        ok(labels == ['Gruppe', 'Filter', 'Adresse', 'Position', 'Zug'], 'Felder in der Leiste: ' + ','.join(labels))
        await p.evaluate("window.scrollTo(0, 900)"); await p.wait_for_timeout(300)
        await p.screenshot(path=f'{OUT}/big.png')
        pos = await p.evaluate("getComputedStyle(document.querySelector('.bigsticky')).position")
        ok(pos == 'sticky', 'Leiste ist fixiert (sticky)')
        await p.evaluate("Settings.set({view:'list'}).then(()=>{App.renderToolbar();App.renderList()})"); await p.wait_for_timeout(300)
        await p.evaluate("window.scrollTo(0,0)"); await p.screenshot(path=f'{OUT}/list.png')
        # Editor Licht
        await p.evaluate("App.state.edit=true; App.render()")
        eid = await p.evaluate(f"Repo.entriesOf('{hai}').find(e=>abtOf(e)==='L' && e.f.kreis==='361').id")
        await p.evaluate(f"Editor.open({{showId:'{hai}', entryId:'{eid}'}})"); await p.wait_for_timeout(400)
        names = await p.evaluate("[...document.querySelectorAll('[data-editor] form [name]')].map(x=>x.name)")
        ok('lzug' in names and 'warnung' in names and 'dmx' not in names and 'position' in names, 'Editor: Position + Zug getrennt, Warnhinweis, ohne DMX')
        ok(await p.evaluate("document.querySelectorAll('[data-qkeys=lzug] button').length") >= 4, 'Zug-Schnelltasten aus Beleuchterzügen')
        await p.fill('[data-editor] [name=warnung]', 'Heiß – nicht anfassen')
        await p.click('[data-qkeys=lzug] button >> nth=1')
        await p.click('[data-editor] [data-act=abladd]')
        await p.fill('[data-editor] .ablrow textarea', 'In der Pause abstecken')
        await p.click('[data-editor] .ablrow [data-ablk=im]')
        await p.click('[data-editor] .sheet-h [data-act=save]'); await p.wait_for_timeout(600)
        r = await p.evaluate(f"(()=>{{const e=Repo.entry('{eid}'); const st=Views.entrySteps(e); return [e.f.warnung,e.f.lzug,st.map(x=>x.abschnitt+':'+x.text)]}})()")
        print('  ', r)
        ok(r[0] == 'Heiß – nicht anfassen' and r[1] == 'OLZ 2' and r[2] == ['im:In der Pause abstecken'], 'Editor speichert Warnhinweis, Zug, Ablauf-Hinweis')
        # Hinweis entfernen
        await p.evaluate(f"Editor.open({{showId:'{hai}', entryId:'{eid}'}})"); await p.wait_for_timeout(300)
        await p.click('[data-editor] .ablrow [data-ablrm]'); await p.click('[data-editor] .sheet-h [data-act=save]'); await p.wait_for_timeout(500)
        ok(await p.evaluate(f"Views.entrySteps(Repo.entry('{eid}')).length") == 0, 'Ablauf-Hinweis wieder entfernt')
        # Neuer Eintrag Ton mit Hinweis
        await p.evaluate(f"Editor.open({{showId:'{hai}', abt:'T'}})"); await p.wait_for_timeout(300)
        await p.fill('[data-editor] [name=kanal]', '33'); await p.click('[data-editor] [data-act=abladd]'); await p.fill('[data-editor] .ablrow textarea', 'Mikro in Gasse 2 legen')
        await p.click('[data-editor] .sheet-h [data-act=save]'); await p.wait_for_timeout(500)
        ok(await p.evaluate(f"Repo.ablaufOf('{hai}','T').some(s=>s.text==='Mikro in Gasse 2 legen' && Repo.entry(s.entryId) && Repo.entry(s.entryId).f.kanal==='33')"), 'Neuer Ton-Kanal mit Ablauf-Hinweis verknüpft')
        # Ablauf-Editor Licht
        await p.evaluate(f"SetupView.editAblauf('{hai}','L')"); await p.wait_for_timeout(300)
        await p.click('[data-editor] [data-x=add][data-ab=im]'); await p.keyboard.type('Szene 4 Verfolger')
        await p.fill('#se-allg', 'Neuer Hinweis Licht'); await p.click('[data-editor] .sheet-h [data-x=save]'); await p.wait_for_timeout(500)
        ok(await p.evaluate(f"Repo.show('{hai}').f.einrichtung==='Neuer Hinweis Licht' && Repo.ablaufOf('{hai}','L').some(s=>s.abschnitt==='im')"), 'Ablauf-Editor Licht speichert Hinweis und Schritt')
        # Beleuchterzüge-Editor
        await p.evaluate(f"SetupView.editL('{hai}')"); await p.wait_for_timeout(300)
        ok(await p.evaluate("!document.querySelector('#se-allg') && document.querySelectorAll('.zed').length>=4"), 'Beleuchterzüge-Editor ohne Hinweisfeld')
        await p.evaluate("history.back()"); await p.wait_for_timeout(300)
        # PDF
        n = await p.evaluate(f"(async()=>{{const b=await Pdf.build('{hai}',{{kat:'all',depts:['L','T','B'],cover:true,compact:true}}); const a=new Uint8Array(await b.arrayBuffer()); window._pdf=Array.from(a); return [b.size, Pdf.lastPages]}})()")
        pdf = bytes(await p.evaluate("window._pdf"))
        open(f'{OUT}/haifisch.pdf', 'wb').write(pdf)
        ok(n[0] > 10000, f'PDF erzeugt ({n[1]} Seiten)')
        try:
            q = subprocess.run(['qpdf', '--check', f'{OUT}/haifisch.pdf'], capture_output=True, text=True); ok(q.returncode == 0, 'qpdf --check')
        except FileNotFoundError: print('  (qpdf fehlt)')
        txt = subprocess.run(['pdftotext', f'{OUT}/haifisch.pdf', '-'], capture_output=True, text=True).stdout if subprocess.run(['which', 'pdftotext'], capture_output=True).returncode == 0 else ''
        if txt: print('   PDF:', [k for k in ['HINWEIS EINRICHTEN','ACHTUNG: Heiß','WÄHREND DER VORSTELLUNG'] if k not in txt]); ok('HINWEIS EINRICHTEN' in txt and 'ACHTUNG: Heiß' in txt and 'WÄHREND DER VORSTELLUNG' in txt, 'PDF enthält Hinweis, Warnhinweis, Ablauf')
        # Thumbs: Bild kommt nach dem Eintrag
        await p.evaluate("App.state.edit=false; App.render()")
        r = await p.evaluate("""(async()=>{
          const ph=[...Repo.photos.values()].find(x=>!x.f.del && Repo.entry(x.f.entryId) && abtOf(Repo.entry(x.f.entryId))==='L' && Repo.entry(x.f.entryId).showId===App.state.showId);
          const full=await Repo.full(ph.b), thumb=await Repo.thumb(ph.b);
          await Store.tx(['fulls','thumbs'],'readwrite',s=>{s.fulls.delete(ph.b);s.thumbs.delete(ph.b)});
          Thumbs.map.delete(ph.b); App.renderList(); document.querySelector(`img[data-b="${ph.b}"]`).scrollIntoView(); await new Promise(r=>setTimeout(r,600));
          const img1=document.querySelector(`img[data-b="${ph.b}"]`); const miss=img1 && img1.parentElement.classList.contains('nob');
          await Repo.applyRemote({}, [{id:ph.b, full, thumb}]); await new Promise(r=>setTimeout(r,400)); document.querySelector(`img[data-b="${ph.b}"]`).scrollIntoView(); await new Promise(r=>setTimeout(r,700));
          const img=document.querySelector(`img[data-b="${ph.b}"]`); return [miss, !!(img && img.src && img.classList.contains('ok'))];})()""")
        ok(r[0], 'Fehlendes Bild zeigt „Bild fehlt“')
        ok(r[1], 'Nachgereichtes Bild erscheint ohne Neustart (Fehler Android → iPad)')
        # Sync-Paket A → B (Licht-Gerät), portionsweise
        pk = await p.evaluate("""(async()=>{const r=await Sync.buildPackage({type:'sync',since:0,depts:['L']}); return [await r.blob.text(), r.counts.blobs];})()""")
        ctx2, p2, errs2 = await newpage(b, 820, 1180)
        await p2.evaluate("Settings.set({depts:['L'], demoOnFirstStart:false})")
        st = await p2.evaluate("async t=>{const r=await Sync.importPackage(new File([t],'x.json')); return [r.bilder, r.missing, r.ungueltig]}", pk[0])
        ok(st[0] >= pk[1] - 1 and st[2] == 0, f'Sync-Paket: {st[0]} Bilder übernommen (Paket {pk[1]}), ungültig {st[2]}')
        await p2.evaluate(f"location.hash='#/show/{hai}'"); await p2.wait_for_timeout(1200)
        nimg = await p2.evaluate("[...document.querySelectorAll('.card .th img')].filter(i=>i.classList.contains('ok')).length")
        ok(nimg >= 4, f'Gerät B zeigt Bilder ({nimg})')
        ok(await p2.evaluate(f"Repo.ablaufOf('{hai}','L').length>0 && !!Repo.entries.size"), 'Ablauf Licht kommt per Paket an')
        await p2.screenshot(path=f'{OUT}/ipad_b.png')
        # Telefonbreite
        ctx3, p3, errs3 = await newpage(b, 390, 844)
        await p3.evaluate("Settings.set({depts:['L','T','B']})");
        await p3.evaluate("async t=>{await Sync.importPackage(new File([t],'x.json'))}", pk[0])
        await p3.evaluate(f"location.hash='#/show/{hai}'"); await p3.wait_for_timeout(800)
        ow = await p3.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
        ok(ow, 'Smartphone: kein waagrechtes Scrollen')
        await p3.screenshot(path=f'{OUT}/phone.png')
        # Requisite-Ansicht weiter ok
        tid = await p.evaluate("Repo.liveShows().find(s=>s.id==='test-r-show').id")
        await p.evaluate(f"location.hash='#/show/{tid}'"); await p.wait_for_timeout(700)
        ok(await p.evaluate("document.querySelectorAll('.erow').length") > 20, 'Requisite Einrichten weiter in Ordnung')
        ok(await p.evaluate("!!document.querySelector('.hintbox[data-abt=R]')"), 'Requisite: Wichtig als Hinweis-Kasten')
        await p.evaluate("(async()=>{const b=await Pdf.build('test-r-show',{kat:'all',depts:['R'],cover:true,compact:true}); window._n=Pdf.lastPages})()"); await p.wait_for_timeout(2500)
        ok(await p.evaluate("window._n>2"), 'PDF Requisite')
        # Spielstättenfarben
        ok(await p.evaluate("spColor('Großes Haus')!=='#d9534f' && spColor('Werkstattbühne')!=='#3b8fd9'"), 'Spielstätten-Farben geändert')
        allerr = errs + errs2 + errs3
        ok(not allerr, 'Keine Seitenfehler ' + ('' if not allerr else str(allerr[:5])))
        await b.close()
    print('\n' + ('ALLES OK' if not fails else f'{len(fails)} FEHLER'))
asyncio.run(main())
