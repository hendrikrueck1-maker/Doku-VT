"""Doku VT 2.8.3 – Test der Korrekturen aus dem QA-Bericht zu 2.8.2 (Python + Playwright/Chromium mit simulierter Kamera).
Aufruf: python3 test_283.py <ordner> [<ordner mit 2.8.2>]   (mit zweitem Ordner zusätzlich der Abgleich mit einem Gerät auf 2.8.2)
Jeder Abschnitt nennt die Befund-Nummer aus dem QA-Bericht. Geräte = eigene Browser-Kontexte, Uhr je Gerät verstellbar."""
import asyncio, sys, subprocess, http.server, threading, functools, os, json, time, re, base64
from playwright.async_api import async_playwright
ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
ALT = sys.argv[2] if len(sys.argv) > 2 else None
OUT = os.environ.get('OUT', '/tmp/doku-vt-test')
os.makedirs(OUT, exist_ok=True)
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT))
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/index.html'
URL_ALT = None
if ALT:
    srv2 = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ALT))
    threading.Thread(target=srv2.serve_forever, daemon=True).start()
    URL_ALT = f'http://127.0.0.1:{srv2.server_address[1]}/index.html'
fails = []; ERRS = []
def ok(c, m):
    print(('OK   ' if c else 'FAIL ') + m)
    if not c: fails.append(m)
    return bool(c)

# Uhr je Gerät verschieben (Date + Date.now), wie im Stresstest
INIT = r"""(()=>{ const RD = Date; let off = +(sessionStorage.getItem('__off') || %OFF%);
  window.__setOff = v => { off = v; sessionStorage.setItem('__off', v); };
  class FD extends RD { constructor(...a) { if (a.length === 0) super(RD.now() + off); else super(...a); } static now() { return RD.now() + off; } }
  FD.UTC = RD.UTC; FD.parse = RD.parse; window.Date = FD; })();"""

async def newpage(b, w=1180, h=820, off=0, demo=True, name='', url=None):
    ctx = await b.new_context(viewport={'width': w, 'height': h}, service_workers='block', permissions=['camera'], timezone_id='Europe/Berlin', locale='de-DE')
    await ctx.add_init_script(INIT.replace('%OFF%', str(int(off))))
    p = await ctx.new_page(); p._name = name or f'{w}x{h}'
    p.on('pageerror', lambda e: ERRS.append((p._name, str(e)[:300])))
    p.on('console', lambda m: ERRS.append((p._name, 'console: ' + m.text[:300])) if m.type == 'error' and not getattr(p, '_quiet', False) else None)
    await p.goto(url or URL); await p.wait_for_function('window.Boot && Boot.started', timeout=30000)
    if not demo:
        await p.evaluate("(async()=>{await Settings.set({demoOnFirstStart:false}); await Store.tx(['shows','entries','photos','fulls','thumbs'],'readwrite',s=>{['shows','entries','photos','fulls','thumbs'].forEach(n=>s[n].clear())}); await Store.metaSet('demoDone',true);})()")
        await p.reload(); await p.wait_for_function('window.Boot && Boot.started', timeout=30000)
    return ctx, p

async def reload(p):
    await p.reload(); await p.wait_for_function('window.Boot && Boot.started', timeout=30000); await p.wait_for_timeout(300)

async def pkg(p, since=0, depts='null'):
    return await p.evaluate(f"(async()=>{{const r=await Sync.buildPackage({{type:'sync',since:{since},depts:{depts}}}); return await r.blob.text()}})()")

async def imp(p, text):
    return await p.evaluate("async t=>{try{return await Sync.importPackage(new File([t],'x.json'))}catch(e){return {err:e.message}}}", text)

HAI = "Repo.liveShows().find(s=>s.f.titel.startsWith('Demo: Der Haifisch')).id"

def berlin_ms(y, mo, d, h, mi):
    from zoneinfo import ZoneInfo
    import datetime
    return datetime.datetime(y, mo, d, h, mi, tzinfo=ZoneInfo('Europe/Berlin')).timestamp() * 1000

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])
        ctx, p = await newpage(b, name='Grund')
        VER = json.load(open(os.path.join(ROOT, 'version.json')))['version']
        ok(await p.evaluate('APP_VERSION') == VER, 'Version ' + VER)

        # ---------------- Befund 1: Spieltag bis 4 Uhr ----------------
        r = await p.evaluate("[RunList.today(new Date(2026,9,24,3,59)), RunList.today(new Date(2026,9,24,4,0)), RunList.today(new Date(2026,9,24,0,10)), RunList.today(new Date(2026,2,29,3,30)), RunList.today(new Date(2026,9,25,2,30)), RunList.today(new Date(2026,9,25,4,30))]")
        ok(r == ['2026-10-23', '2026-10-24', '2026-10-23', '2026-03-28', '2026-10-24', '2026-10-25'], f'Spieltag wechselt um 4 Uhr, auch in den Nächten der Zeitumstellung ({r})')
        off = int(berlin_ms(2026, 10, 23, 23, 40) - time.time() * 1000)
        c1, p1 = await newpage(b, off=off, name='Mitternacht')
        await p1.evaluate("Settings.set({depts:['L','T','B','R']}).then(()=>Req.ensureHouse()).then(()=>Req.testShow())")
        hai = await p1.evaluate(HAI)
        await p1.evaluate(f"location.hash='#/show/{hai}'"); await p1.wait_for_timeout(400)
        await p1.evaluate("SetupView.open.run=true; App.render()"); await p1.wait_for_timeout(200)
        await p1.click('[data-box=run] [data-run=start]'); await p1.wait_for_timeout(300)
        await p1.click('[data-box=run] .runchk >> nth=0'); await p1.wait_for_timeout(300)
        await p1.evaluate("location.hash='#/show/test-r-show'"); await p1.wait_for_timeout(400)
        await p1.evaluate("App.state.abt='R'; Settings.set({reqView:'einrichten'}).then(()=>App.render())"); await p1.wait_for_timeout(300)
        await p1.click('.gchk >> nth=0'); await p1.wait_for_timeout(300)
        await p1.evaluate(f"__setOff({off + 30 * 60000})"); await reload(p1)          # 00:10
        await p1.evaluate(f"location.hash='#/show/{hai}'"); await p1.wait_for_timeout(400)
        await p1.evaluate("SetupView.open['abl-L']=true; App.render()"); await p1.wait_for_timeout(200)
        await p1.click('[data-box=abl-L] .runchk >> nth=0'); await p1.wait_for_timeout(400)
        await p1.evaluate("location.hash='#/show/test-r-show'"); await p1.wait_for_timeout(400)
        rq = await p1.evaluate("document.querySelectorAll('.gchk[aria-checked=true]').length")
        await p1.click('.gchk >> nth=1'); await p1.wait_for_timeout(300)
        runs = await p1.evaluate(f"RunList.runsOf('{hai}').map(r=>[r.f.datum,Object.keys(r.f).filter(k=>k.startsWith('h:')).length])")
        rr = await p1.evaluate("RunList.runsOf('test-r-show').map(r=>[r.f.datum,Object.keys(r.f).filter(k=>k.startsWith('h:')).length])")
        ok(runs == [['2026-10-23', 2]] and rr == [['2026-10-23', 2]] and rq == 1, f'Nach Mitternacht (00:10) im selben Durchgang vom 23.10. – Licht {runs}, Requisite {rr} (vorher {rq} Haken sichtbar)')
        await p1.evaluate(f"__setOff({off + 270 * 60000})"); await reload(p1)          # 04:10
        await p1.evaluate(f"location.hash='#/show/{hai}'"); await p1.wait_for_timeout(400)
        await p1.evaluate("SetupView.open.run=true; App.render()"); await p1.wait_for_timeout(200)
        ok(await p1.evaluate("!!document.querySelector('[data-box=run] [data-run=start]')"), 'Um 04:10 beginnt der neue Spieltag („Vorstellung heute beginnen“)')
        await c1.close()

        # ---------------- Befund 2: ein Durchgang je Spieltag über mehrere Geräte ----------------
        cA, A = await newpage(b, name='Licht-iPad'); cB, B = await newpage(b, name='Ton-Pixel')
        await imp(B, await pkg(A))
        await A.evaluate("Settings.set({depts:['L']})"); await B.evaluate("Settings.set({depts:['T']})")
        hai = await A.evaluate(HAI)
        for P in (A, B):
            await P.evaluate(f"location.hash='#/show/{hai}'"); await P.wait_for_timeout(300)
            await P.evaluate("SetupView.open.run=true; App.render()"); await P.wait_for_timeout(200)
            await P.click('[data-box=run] [data-run=start]'); await P.wait_for_timeout(300)
            n = await P.evaluate("document.querySelectorAll('[data-box=run] .runchk').length")
            for i in range(n): await P.click(f'[data-box=run] .runchk >> nth={i}'); await P.wait_for_timeout(80)
        await imp(B, await pkg(A)); await imp(A, await pkg(B)); await A.wait_for_timeout(700)
        ra = await A.evaluate(f"(()=>{{const rs=RunList.runsOf('{hai}'); const it=RunList.items('{hai}',['L','T']).filter(i=>i.vor); return [rs.length, rs.map(r=>RunList.progress(r,it).done), rs.map(r=>r.id)]}})()")
        ok(ra[0] == 1 and ra[1][0] >= 2 and ra[2][0].startswith('run-'), f'Zwei Geräte beginnen unabhängig: ein Durchgang mit allen Haken ({ra[:2]})')
        # ältere Durchgänge (2.8.2, zufällige Kennung) werden zusammengeführt – auch Nachzügler
        r = await A.evaluate(f"""(async()=>{{const sid='{hai}', d=RunList.today();
          const mk=(h,c,t)=>{{const r=Rec.create({{showId:sid}},Object.assign({{datum:d,titel:t||'Vorstellung alt',del:false}},h)); r.c=c; return r;}};
          for (const r of RunList.runsOf(sid)) await RunList.remove(r.id);
          const r1=mk({{'h:ci:a':{{ok:true,at:1,dev:'A'}}}},100), r2=mk({{'h:ci:b':{{ok:true,at:2,dev:'B'}}}},50), r3=mk({{'h:ci:c':{{ok:true,at:3,dev:'C'}}}},10,'Vorstellung alt (2)');
          await Repo._write({{runs:[r1,r2,r3]}},false); await new Promise(x=>setTimeout(x,900));
          const live=RunList.runsOf(sid).map(r=>[r.id===r2.id?'r2':r.id===r3.id?'r3':'?', Object.keys(r.f).filter(k=>k.startsWith('h:')).sort().join(',')]);
          const late=Rec.patch(Repo.runs.get(r1.id),{{'h:ci:z':{{ok:true,at:9,dev:'alt'}}}}); await Repo._write({{runs:[late]}},false); await new Promise(x=>setTimeout(x,900));
          return [live, Repo.runs.get(r1.id).f.mergedInto===r2.id, Object.keys(Repo.runs.get(r2.id).f).filter(k=>k.startsWith('h:')).sort().join(','), RunList.todayRun(sid).id===r3.id]}})()""")
        ok(r[0] == [['r3', 'h:ci:c'], ['r2', 'h:ci:a,h:ci:b']] and r[1] and r[2] == 'h:ci:a,h:ci:b,h:ci:z' and r[3],
           f'Alte Doppel-Durchgänge zusammengeführt, „Neu beginnen“ (2) bleibt eigener Durchgang, späte Haken wandern nach ({r})')
        # Neu beginnen auf zwei Geräten → derselbe zweite Durchgang
        await imp(B, await pkg(A))
        await A.evaluate(f"RunList.create('{hai}')"); await B.evaluate(f"RunList.create('{hai}')")
        await imp(B, await pkg(A)); await imp(A, await pkg(B)); await A.wait_for_timeout(700)
        n1 = await A.evaluate(f"RunList.runsOf('{hai}').filter(r=>r.f.datum===RunList.today()).map(r=>RunList.slot(r))")
        n2 = await B.evaluate(f"RunList.runsOf('{hai}').filter(r=>r.f.datum===RunList.today()).map(r=>RunList.slot(r))")
        ok(n1 == n2 and len(n1) == len(set(n1)), f'„Neu beginnen“ auf zwei Geräten: gleiche Durchgänge, keine Dopplung ({n1} / {n2})')
        pdfb = await A.evaluate(f"(async()=>{{const r=RunList.todayRun('{hai}'); const bl=Pdf.buildRun('{hai}',r.id,['L','T']); window._pdf=Array.from(new Uint8Array(await bl.arrayBuffer())); return bl.size}})()")
        open(f'{OUT}/283_protokoll.pdf', 'wb').write(bytes(await A.evaluate('window._pdf')))
        ok(subprocess.run(['qpdf', '--check', f'{OUT}/283_protokoll.pdf'], capture_output=True).returncode == 0, 'PDF-Protokoll: qpdf --check')
        await cA.close(); await cB.close()

        # ---------------- Befund 3 + 4: Kameras quer und im Rotlicht ----------------
        for (w, h, nm) in [(844, 390, 'iPhone quer'), (667, 375, 'klein quer'), (915, 412, 'Pixel quer'), (390, 844, 'iPhone hoch'), (1180, 820, 'iPad quer')]:
            cc, pc = await newpage(b, w, h, name=nm)
            hai = await pc.evaluate(HAI)
            await pc.evaluate(f"location.hash='#/show/{hai}'"); await pc.wait_for_timeout(300)
            await pc.evaluate("void Camera.open({abt:'L',kat:'A',title:'Test',onShot:()=>{},allowKatSwitch:true,forceApp:true})")
            await pc.wait_for_function("document.querySelector('.cam video') && document.querySelector('.cam video').videoWidth>0", timeout=15000)
            vis = "(sel)=>{const v=s=>{const e=document.querySelector(s); if(!e) return false; const r=e.getBoundingClientRect(); return r.bottom<=innerHeight+1 && r.right<=innerWidth+1 && r.top>=0 && r.width>0}; return sel.map(v)}"
            d = await pc.evaluate("Math.round(document.querySelector('.cam .vf').getBoundingClientRect().width)")
            dv = await pc.evaluate(vis, ['.cam .shutter', '.cam [data-a=done]', '.cam .katsw'])
            await pc.evaluate("history.back()"); await pc.wait_for_timeout(300)
            lid = await pc.evaluate("(async()=>{const l=await Cues.createList({titel:'Quer'}); await Cues.addRange(l.id,'1','5','1'); return l.id})()")
            await pc.evaluate(f"App.state.edit=true; location.hash='#/cue/{lid}'"); await pc.wait_for_timeout(300)
            await pc.click('[data-cact=cam]')
            await pc.wait_for_function("document.querySelector('.ccam video') && document.querySelector('.ccam video').videoWidth>0", timeout=15000)
            cv = await pc.evaluate("Math.round(document.querySelector('.ccam .vf').getBoundingClientRect().width)")
            cvv = await pc.evaluate(vis, ['.ccam .shutter', '.ccam .cnext', '.ccam [data-a="nr+"]', '.ccam [data-a="nr-"]', '.ccam .cnr', '.ccam [data-a=close]'])
            need = 280 if h < 500 else 240
            ok(d >= need and cv >= need and all(dv) and all(cvv), f'{nm} {w}×{h}: Sucher Doku {d} px, Cue {cv} px, alle Knöpfe im Bild')
            await pc.screenshot(path=f'{OUT}/283_cam_{nm.replace(" ", "_")}.png')
            await pc.click('.ccam [data-a=close]'); await pc.wait_for_timeout(200)
            await cc.close()
        cc, pc = await newpage(b, 390, 844, name='Rotlicht-Kamera')
        await pc.evaluate("Settings.set({theme:'red'})")
        hai = await pc.evaluate(HAI)
        await pc.evaluate(f"location.hash='#/show/{hai}'"); await pc.wait_for_timeout(300)
        await pc.evaluate("void Camera.open({abt:'T',kat:'E',title:'Test',onShot:()=>{},allowKatSwitch:true,forceApp:true})")
        await pc.wait_for_function("document.querySelector('.cam video') && document.querySelector('.cam video').videoWidth>0", timeout=15000)
        await pc.click('.cam [data-a=shot]'); await pc.wait_for_timeout(60)
        st = await pc.evaluate("""(()=>{const g=(s,p)=>getComputedStyle(document.querySelector(s))[p]; const white=c=>/rgb\\(2[3-5]\\d, 2[3-5]\\d, 2[3-5]\\d/.test(c);
          return {shutter:g('.cam .shutter','backgroundColor'), done:g('.cam [data-a=done]','backgroundColor'), doneC:g('.cam [data-a=done]','color'), video:g('.cam video','filter'),
            flash:g('.cam .flash','display'), hint:g('.cam .hintlbl','backgroundColor'), border:g('.cam .vf','borderTopColor'), anim:g('.cam .vf','animationName'), white:[g('.cam .shutter','backgroundColor'),g('.cam [data-a=done]','backgroundColor'),g('.cam .top .ttl','color'),g('.cam .vf','borderTopColor'),g('.cam .hintlbl','color')].filter(white)}})()""")
        print('  ', st)
        ok(not st['white'] and 'grayscale' in st['video'] and st['flash'] == 'none' and 'cpulseR' in st['anim'], 'Doku-Kamera im Rotlicht: nichts Weißes, Sucherbild rot gefiltert, kein weißes Aufblitzen')
        await pc.screenshot(path=f'{OUT}/283_cam_rot.png')
        await pc.evaluate("history.back()"); await pc.wait_for_timeout(200)
        await pc.evaluate("Settings.set({theme:'dark'})")
        await pc.evaluate("void Camera.open({abt:'L',kat:'A',title:'Test',onShot:()=>{},forceApp:true})")
        await pc.wait_for_function("document.querySelector('.cam video') && document.querySelector('.cam video').videoWidth>0", timeout=15000)
        ok(await pc.evaluate("getComputedStyle(document.querySelector('.cam .flash')).display==='none'"), 'Dunkel: kein weißes Aufblitzen (wie Cue-Kamera)')
        await pc.evaluate("history.back()"); await cc.close()

        # ---------------- Befund 5 + 19 + 28 + 29: Grenzen beim Abgleich ----------------
        cA, A = await newpage(b, name='A-Felder'); cB, B = await newpage(b, name='B-Felder')
        for P in (A, B): await P.evaluate("Settings.set({depts:['L','T','B','R']})")
        sid = await A.evaluate("(async()=>{await Req.ensureHouse(); const t=await Req.testShow(); const p={}; for(let i=0;i<2100;i++) p['rs:t'+i]={abschnitt:'ra:test-t1',text:'alt '+i,ord:i,del:true}; await Repo.patchShow(t.id,p); return t.id})()")
        nf = await A.evaluate(f"Object.keys(Repo.show('{sid}').f).length")
        st = await imp(B, await pkg(A))
        ok(nf > 2000 and await B.evaluate(f"!!Repo.show('{sid}')") and st.get('ungueltig') == 0, f'Veranstaltung mit {nf} Feldern kommt an (ungültig {st.get("ungueltig")})')
        diag = await A.evaluate("(async()=>{DiagView.open(); await new Promise(r=>setTimeout(r,400)); const t=document.querySelector('.sheet .sheet-b').innerText; history.back(); return t})()")
        ok('2.8.2 oder älter' in diag, 'Diagnose: Hinweis für Geräte mit 2.8.2 oder älter')
        bad = json.dumps({'format': 'lichtdoku', 'type': 'sync', 'formatVersion': 2, 'deviceName': 'Fremd', 'shows': [
            {'id': 'riesig', 'c': 1, 'mod': 1, 'f': dict({'titel': 'Riesig', 'del': False}, **{f'x{i}': 1 for i in range(20001)}), 't': dict({'titel': 1, 'del': 1}, **{f'x{i}': 1 for i in range(20001)})},
            {'id': 'zukunft', 'c': 1, 'mod': 1, 'f': {'titel': 'Zukunft', 'del': False}, 't': {'titel': 1e16, 'del': 1}}],
            'entries': [{'id': 'e-zust', 'showId': sid, 'c': 1, 'mod': 1, 'f': {'abt': 'R', 'was': 'Kaputt', 'zustand': 5, 'del': False}, 't': {'abt': 1, 'was': 1, 'zustand': 1, 'del': 1}},
                        {'id': 'e-lang', 'showId': sid, 'c': 1, 'mod': 1, 'f': {'abt': 'L', 'kreis': '1', 'bemerkung': 'x' * 100001, 'del': False}, 't': {'abt': 1, 'kreis': 1, 'bemerkung': 1, 'del': 1}}], 'blobs': []})
        await B.evaluate("async t=>{window.__f=new File([t],'fremd.ldsync.json')}", bad)
        await B.evaluate("App.importFile(window.__f)"); await B.wait_for_timeout(1500)
        dlg = await B.evaluate("document.querySelector('.dialog')?.innerText||''")
        stt = await B.evaluate("Sync.status()")
        ok('NICHT übernommen' in dlg and '4 Datensätze' in dlg and stt['state'] == 'error', f'Abgelehntes wird gemeldet (Dialog, Status „{stt["label"]}“)')
        await B.evaluate("document.querySelector('.dialog .btn')?.click()"); await B.wait_for_timeout(200)
        await B.evaluate(f"location.hash='#/show/{sid}'; App.state.abt='R'; App.render()"); await B.wait_for_timeout(400)
        ok(await B.evaluate("!Repo.entries.has('e-zust') && !Repo.shows.has('zukunft')"), 'Falscher Feldtyp (zustand = 5) und Zeitstempel 1e16 abgelehnt, Ansicht ohne Absturz')
        # eigener Text über 100 000 Zeichen: nicht speichern, klare Meldung, Editor bleibt offen
        hai = await A.evaluate(HAI)
        await A.evaluate(f"location.hash='#/show/{hai}'; App.state.edit=true; App.render()"); await A.wait_for_timeout(300)
        await A.evaluate(f"Editor.open({{showId:'{hai}', abt:'L'}})"); await A.wait_for_timeout(300)
        await A.fill('[data-editor] [name=kreis]', '4711')
        await A.evaluate("(()=>{const t=document.querySelector('[data-editor] [name=bemerkung]'); t.value='y'.repeat(100001); t.dispatchEvent(new Event('input',{bubbles:true}))})()")
        A._quiet = True
        await A.click('[data-editor] .sheet-h [data-act=save]'); await A.wait_for_timeout(600)
        A._quiet = False
        msg = await A.evaluate("document.querySelector('.dialog')?.innerText||''")
        still = await A.evaluate(f"[!!document.querySelector('[data-editor]'), Repo.entriesOf('{hai}').some(e=>e.f.kreis==='4711')]")
        ok('zu lang' in msg and 'NICHTS gespeichert' in msg and still == [True, False], f'Bemerkung > 100 000 Zeichen: nicht gespeichert, Meldung, Editor bleibt offen ({still})')
        await A.evaluate("document.querySelector('.dialog .btn')?.click()"); await A.wait_for_timeout(200)
        await A.evaluate("(()=>{const t=document.querySelector('[data-editor] [name=bemerkung]'); t.value='kurz'; t.dispatchEvent(new Event('input',{bubbles:true}))})()")
        await A.click('[data-editor] .sheet-h [data-act=save]'); await A.wait_for_timeout(600)
        ok(await A.evaluate(f"Repo.entriesOf('{hai}').some(e=>e.f.kreis==='4711' && e.f.bemerkung==='kurz')"), 'Nach dem Kürzen gespeichert')
        await cA.close(); await cB.close()

        # ---------------- Befund 26 + 27: Speicherfehler-Meldungen ----------------
        p._quiet = True
        r = await p.evaluate("""(async()=>{const out=[];
          try { await Store.tx(['meta'],'readwrite',(s,t)=>{ s.meta.put({k:'x',v:1}); t.abort(); }); out.push('kein Fehler'); } catch(e) { out.push(e.message); }
          const put=IDBObjectStore.prototype.put; IDBObjectStore.prototype.put=function(){ throw new DOMException('voll','QuotaExceededError'); };
          try { await Repo.patchShow(Repo.liveShows()[0].id,{notiz:'q'}); out.push('kein Fehler'); } catch(e) { out.push(e.message, e.quota); } finally { IDBObjectStore.prototype.put=put; }
          return out})()""")
        p._quiet = False
        ok('NICHTS gespeichert' in r[0] and 'unbekannter Fehler' not in r[0] and 'NICHTS gespeichert' in r[1] and r[2] is True, f'Abbruch ohne Fehlerobjekt und „Speicher voll“ beim Schreiben: klare Meldung ({r[0][:60]}…)')

        # ---------------- Befund 6 + 7 + 18: Rotlicht-Meldungen, Bildansicht, Kontrast ----------------
        for theme in ('dark', 'light', 'red'):
            await p.evaluate(f"Settings.set({{theme:'{theme}'}})"); await p.wait_for_timeout(100)
            t = await p.evaluate("""(()=>{const mk=k=>{Ui.toast('Test '+k,k,{ms:4000}); const el=[...document.querySelectorAll('.toast')].pop(); const cs=getComputedStyle(el); return [cs.backgroundColor, cs.color, cs.borderTopStyle, !!el.querySelector('.ti svg')]};
              const r={ok:mk(''),err:mk('err'),warn:mk('warn')}; document.querySelectorAll('.toast').forEach(x=>x.remove()); return r})()""")
            ok(t['err'][:3] != t['ok'][:3] and t['warn'][:3] != t['ok'][:3] and t['err'][:3] != t['warn'][:3] and t['err'][3] and t['warn'][3] and not t['ok'][3],
               f'{theme}: Fehler-, Warn- und Erfolgsmeldung unterscheidbar, Fehler/Warnung mit Symbol')
        cr = await p.evaluate("""(()=>{const L=c=>{const m=c.match(/\\d+(\\.\\d+)?/g).map(Number).slice(0,3).map(v=>{v/=255; return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4)}); return 0.2126*m[0]+0.7152*m[1]+0.0722*m[2]};
          const cr=(a,b)=>{const x=L(a),y=L(b); return Math.round((Math.max(x,y)+0.05)/(Math.min(x,y)+0.05)*100)/100};
          const out={}; for (const th of ['dark','light','red']) { document.documentElement.dataset.theme=th;
            const b=document.createElement('button'); b.className='btn danger solid'; b.textContent='Löschen'; document.body.appendChild(b); const cs=getComputedStyle(b); out[th+' Löschen']=cr(cs.color,cs.backgroundColor); b.remove();
            Ui.toast('x','err'); const t=[...document.querySelectorAll('.toast')].pop(), ts=getComputedStyle(t); out[th+' Fehler']=cr(ts.color,ts.backgroundColor); t.remove();
            const s=document.createElement('span'); s.style.color='var(--muted)'; document.body.appendChild(s); out[th+' muted']=cr(getComputedStyle(s).color, getComputedStyle(document.body).backgroundColor); s.remove(); }
          document.documentElement.dataset.theme=Settings.v.theme; return out})()""")
        print('  ', cr)
        ok(all(v >= 4.5 for k, v in cr.items() if 'muted' not in k and not k.startswith('red')) and all(v >= 4 for k, v in cr.items()), f'Kontrast „Löschen“, Fehlermeldung, gedämpfte Schrift ≥ 4,5 : 1 (Rotlicht ≥ 4 : 1)')
        await p.evaluate("Settings.set({theme:'red'})")
        hai = await p.evaluate(HAI)
        await p.evaluate(f"location.hash='#/show/{hai}'; App.state.edit=false; App.render()"); await p.wait_for_timeout(400)
        e361 = await p.evaluate(f"Repo.entriesOf('{hai}').find(e=>e.f.kreis==='361').id")
        await p.evaluate(f"App.openLightbox('{e361}','A',0)")
        await p.wait_for_timeout(500)
        wh = await p.evaluate("""(()=>{const white=c=>/rgb\\(2[3-5]\\d, 2[3-5]\\d, 2[3-5]\\d/.test(c); const els=[...document.querySelectorAll('.lbx, .lbx *')].filter(e=>e.offsetParent!==null || e.classList.contains('lbx'));
          return els.filter(e=>white(getComputedStyle(e).color) && (e.textContent||'').trim()).map(e=>e.className||e.tagName).slice(0,5)})()""")
        ok(not wh, f'Bildansicht im Rotlicht ohne weiße Schrift ({wh})')
        await p.screenshot(path=f'{OUT}/283_lightbox_rot.png')
        await p.evaluate("history.back()"); await p.wait_for_timeout(300)
        await p.evaluate("Settings.set({theme:'dark'})")

        # ---------------- Befund 8: Großbild-Kopf bricht nur nach „+“ um ----------------
        for (w, h, nm) in [(390, 844, 'iPhone'), (375, 667, 'iPhone SE'), (320, 568, 'SE 1')]:
            cc, pc = await newpage(b, w, h, name=nm)
            hai = await pc.evaluate(HAI)
            await pc.evaluate(f"location.hash='#/show/{hai}'; App.state.abt='L'; Settings.set({{view:'big'}}).then(()=>App.render())"); await pc.wait_for_timeout(500)
            r = await pc.evaluate("""[...document.querySelectorAll('.card .bighead .bk')].map(bk=>{
                const v=bk.querySelector('.bv'), sm=bk.querySelector('small'); const chars=[];
                const tw=document.createTreeWalker(v, NodeFilter.SHOW_TEXT); let n; while((n=tw.nextNode())) for(let i=0;i<n.textContent.length;i++){ const rg=document.createRange(); rg.setStart(n,i); rg.setEnd(n,i+1); const q=rg.getBoundingClientRect(); chars.push([n.textContent[i], Math.round(q.top)]); }
                const bad=[]; for(let i=1;i<chars.length;i++) if (Math.abs(chars[i][1]-chars[i-1][1])>4 && chars[i-1][0]!=='+') bad.push(chars.slice(0,i).map(c=>c[0]).join(''));
                const rg=document.createRange(); rg.selectNodeContents(sm); const tops=new Set([...rg.getClientRects()].map(q=>Math.round(q.top)));
                return [v.textContent, bad, tops.size]})""")
            badv = [x for x in r if x[1] or x[2] > 1]
            ok(not badv, f'{nm}: Kreis im Großbild-Kopf bricht nur nach „+“, „KREIS“ einzeilig ({[x[0] for x in r][:4]})')
            if nm == 'iPhone': await pc.screenshot(path=f'{OUT}/283_grossbild_phone.png')
            await cc.close()

        # ---------------- Befund 9: Werkzeugleiste klappt im Querformat weg ----------------
        for (w, h, nm) in [(844, 390, 'iPhone quer'), (915, 412, 'Pixel quer')]:
            cc, pc = await newpage(b, w, h, name=nm)
            hai = await pc.evaluate(HAI)
            for view in ('list', 'big'):
                await pc.evaluate(f"location.hash='#/show/{hai}'; Settings.set({{view:'{view}'}}).then(()=>App.render())"); await pc.wait_for_timeout(400)
                await pc.evaluate("window.scrollTo(0,0)"); await pc.wait_for_timeout(150)
                for y in (300, 600, 900): await pc.evaluate(f"window.scrollTo(0,{y})"); await pc.wait_for_timeout(120)
                await pc.wait_for_timeout(300)
                r = await pc.evaluate("""(()=>{const ab=document.getElementById('appbar').getBoundingClientRect().bottom; const tb=document.querySelector('.toolbar').getBoundingClientRect();
                   const big=document.querySelector('.cards.big .card .bigsticky'); let top=Math.max(ab, tb.bottom>ab+2?tb.bottom:ab);
                   if (big) { const st=[...document.querySelectorAll('.cards.big .card .bigsticky')].map(x=>x.getBoundingClientRect()).filter(q=>q.top<=top+2 && q.bottom>top); if (st.length) top=Math.max(top, st[0].bottom); }
                   return [document.documentElement.classList.contains('tbhide'), Math.round((innerHeight-top)/innerHeight*100)]})()""")
                await pc.screenshot(path=f'{OUT}/283_quer_{view}_{nm.replace(" ", "_")}.png')
                await pc.evaluate("window.scrollTo(0,750)"); await pc.wait_for_timeout(350)
                back = await pc.evaluate("!document.documentElement.classList.contains('tbhide')")
                ok(r[0] and r[1] >= 35 and back, f'{nm} {view}: Leiste beim Runterscrollen weg ({r[1]} % frei), beim Hochscrollen wieder da')
            await cc.close()
        cc, pc = await newpage(b, 390, 844, name='hoch')
        hai = await pc.evaluate(HAI)
        await pc.evaluate(f"location.hash='#/show/{hai}'"); await pc.wait_for_timeout(300)
        for y in (300, 600, 900): await pc.evaluate(f"window.scrollTo(0,{y})"); await pc.wait_for_timeout(120)
        ok(await pc.evaluate("!document.documentElement.classList.contains('tbhide')"), 'Hochformat und iPad: Werkzeugleiste bleibt fixiert (unverändert)')
        # Befund 34: Titel auf dem Smartphone, PDF im Menü
        tw = await pc.evaluate("[Math.round(document.querySelector('.appbar h1').getBoundingClientRect().width), getComputedStyle(document.querySelector('.appbar [data-act=pdf]')).display]")
        ok(tw[0] >= 120 and tw[1] == 'none', f'Smartphone: Titel {tw[0]} px breit, PDF über ⋯')
        await cc.close()

        # ---------------- Befund 10 + 20 + 30: Cue-Nummern ----------------
        lid = await p.evaluate("(async()=>{const l=await Cues.createList({titel:'Text-Cue'}); await Cues.addRange(l.id,'1','5','1'); await Repo._write({cues:[Cues.newCue(l.id,'Ende')]}); return l.id})()")
        ende = await p.evaluate(f"Cues.cueByNr('{lid}','Ende').id")
        await p.evaluate(f"App.state.edit=true; location.hash='#/cue/{lid}'"); await p.wait_for_timeout(300)
        await p.evaluate(f"void CueCam.open({{listId:'{lid}', cueId:'{ende}'}})")
        await p.wait_for_function("document.querySelector('.ccam video') && document.querySelector('.ccam video').videoWidth>0", timeout=15000)
        await p.click('.ccam [data-a=shot]')
        nx = await p.evaluate("document.querySelector('.ccam [data-nx]').textContent")
        await p.click('.ccam [data-a=next]')
        await p.wait_for_function('CueCam.pending()===0 && !CueCam.busy', timeout=20000)
        await p.click('.ccam [data-a=close]'); await p.wait_for_timeout(200)
        r = await p.evaluate(f"Cues.cuesOf('{lid}').map(c=>c.f.nr+':'+Cues.imgsOf(c.id).length).join(' ')")
        ok(nx == '→ 6' and r == '1:0 2:0 3:0 4:0 5:0 6:1 Ende:1', f'„Nächster Cue“ nach „Ende“: → 6 statt 1 ({nx}; {r})')
        r = await p.evaluate("(async()=>{const l=await Cues.createList({titel:'Viele'}); const n=await Cues.addRange(l.id,'1','800','1'); return [n, Cues.rangeCount('1','3000','1'), Cues.rangeCount('1','2','0.25')]})()")
        ok(r == [800, 3000, 5], f'„Mehrere Cues“: 1–800 vollständig, Zählung für die Rückfrage ({r})')
        lid2 = await p.evaluate("(async()=>{const l=await Cues.createList({titel:'Grenze'}); return l.id})()")
        await p.evaluate(f"location.hash='#/cue/{lid2}'"); await p.wait_for_timeout(300)
        await p.click('[data-cact=addmany]'); await p.wait_for_timeout(300)
        await p.fill('[data-editor] [name=von]', '1'); await p.fill('[data-editor] [name=bis]', '3000'); await p.click('[data-editor] [data-ok]'); await p.wait_for_timeout(300)
        t = await p.evaluate("document.querySelector('#toasts').innerText")
        ok('höchstens 2000' in t and await p.evaluate(f"Cues.cuesOf('{lid2}').length") == 0, '1–3000: klare Rückfrage statt stillem Kappen')
        await p.evaluate("history.back()"); await p.wait_for_timeout(200)
        r = await p.evaluate(f"""(async()=>{{const l=await Cues.createList({{titel:'Uhr'}}); const f=Cues.newCue(l.id,'3.5'); f.c=Date.now()+25*36e5; await Repo._write({{cues:[f]}},false);
            await new Promise(r=>setTimeout(r,10)); await Repo._write({{cues:[Cues.newCue(l.id,'20')]}}); return Cues.quickNrs(l.id)}})()""")
        ok(r['last'] == '20' and r['next'][0] == '21', f'Schnellauswahl: Cue eines Geräts mit vorgehender Uhr hängt nicht fest (zuletzt {r["last"]})')

        # ---------------- Befund 12 + 21 + 23: PDF kürzt sichtbar ----------------
        hai = await p.evaluate(HAI)
        warn = ' '.join(['Achtung Leiter steht im Weg, Kabel gesichert, erst nach Freigabe Inspizienz.'] * 14)
        langk = '+'.join(str(i) for i in range(100, 160))
        await p.evaluate("([sid,w,k])=>Repo.saveDraft({id:null,showId:sid,abt:'L',f:{kreis:k,warnung:w},photos:{A:[],E:[]}})", [hai, warn, langk])
        await p.evaluate("([sid,w])=>Repo.saveDraft({id:null,showId:sid,abt:'L',f:{kreis:'999',warnung:'Kurz und vollständig'},photos:{A:[],E:[]}})", [hai, warn])
        e361 = await p.evaluate(f"Repo.entriesOf('{hai}').find(e=>e.f.kreis==='361').id")
        await p.evaluate("([id,k])=>{const e=Repo.entry(id); return Repo._write({entries:[Rec.patch(e,{kreis:k})]})}", [e361, langk + '+361'])
        await p.evaluate(f"(async()=>{{const b=await Pdf.build('{hai}',{{kat:'all',depts:['L'],cover:true,compact:true}}); window._pdf=Array.from(new Uint8Array(await b.arrayBuffer()))}})()")
        open(f'{OUT}/283_licht.pdf', 'wb').write(bytes(await p.evaluate('window._pdf')))
        ok(subprocess.run(['qpdf', '--check', f'{OUT}/283_licht.pdf'], capture_output=True).returncode == 0, 'PDF Licht: qpdf --check')
        txt = subprocess.run(['pdftotext', '-layout', f'{OUT}/283_licht.pdf', '-'], capture_output=True, text=True).stdout
        bbox = subprocess.run(['pdftotext', '-bbox', f'{OUT}/283_licht.pdf', '-'], capture_output=True, text=True).stdout
        xmax = max([float(m) for m in re.findall(r'xMax="([\d.]+)"', bbox)] or [0])
        ach = [ln for ln in txt.splitlines() if 'Freigabe' in ln or 'ACHTUNG' in ln]
        ok('ACHTUNG: Kurz und vollständig' in txt and any('…' in ln for ln in txt.splitlines() if 'Inspizienz' in ln or 'Achtung' in ln), 'PDF: langer Warnhinweis endet sichtbar mit „…“, kurzer vollständig')
        ok(xmax <= 596, f'PDF: kein Text rechts außerhalb der Seite (größtes xMax {xmax:.0f} von 595)')
        lid3 = await p.evaluate("(async()=>{const l=await Cues.createList({titel:'Lang'}); const c=Cues.newCue(l.id,'1',{notiz:'Cue-Notiz '.repeat(200)}); const cv=document.createElement('canvas'); cv.width=cv.height=300; const r=await Photo.fromCanvas(cv); const im=Rec.create({listId:l.id},{cueId:c.id,ord:0,b:r.b,o:'',w:300,h:300,notiz:'Bild-Notiz '.repeat(200),hinweis:'Hinweis '.repeat(150),del:false}); await Repo._write({cues:[c],cueimgs:[im],fulls:[{id:r.b,d:r.full}],thumbs:[{id:r.b,d:r.thumb}]}); return l.id})()")
        await p.evaluate(f"(async()=>{{const b=await Pdf.buildCues('{lid3}',{{cover:false,compact:true}}); window._pdf=Array.from(new Uint8Array(await b.arrayBuffer()))}})()")
        open(f'{OUT}/283_cues.pdf', 'wb').write(bytes(await p.evaluate('window._pdf')))
        ct = subprocess.run(['pdftotext', '-layout', f'{OUT}/283_cues.pdf', '-'], capture_output=True, text=True).stdout
        ok(sum(1 for ln in ct.splitlines() if ln.rstrip().endswith('…')) >= 3, 'Cue-PDF: gekürzte Notizen und Hinweise enden mit „…“')

        # ---------------- Befund 13 + 32: Ansichtsmodus ändert nichts ohne Rückfrage ----------------
        await p.evaluate(f"App.state.edit=false; location.hash='#/show/{hai}'"); await p.wait_for_timeout(400)
        await p.click('.appbar .title-btn'); await p.wait_for_timeout(300)
        h2 = await p.evaluate("document.querySelector('.dialog h2')?.textContent||''")
        await p.click('.dialog .btn:has-text("Abbrechen")'); await p.wait_for_timeout(300)
        r1 = await p.evaluate("[App.state.edit, !!document.querySelector('#sh-t')]")
        await p.click('.appbar [data-act=showmenu]'); await p.wait_for_timeout(300)
        await p.click('.dialog .btn:has-text("Veranstaltung löschen")'); await p.wait_for_timeout(400)
        h2b = await p.evaluate("document.querySelector('.dialog h2')?.textContent||''")
        await p.click('.dialog .btn:has-text("Abbrechen")'); await p.wait_for_timeout(300)
        alive = await p.evaluate(f"!!Repo.show('{hai}')")
        await p.click('.appbar .title-btn'); await p.wait_for_timeout(300)
        await p.click('.dialog .btn:has-text("Bearbeiten einschalten")'); await p.wait_for_timeout(500)
        r2 = await p.evaluate("[App.state.edit, !!document.querySelector('#sh-t')]")
        ok(h2 == 'Ansichtsmodus' and r1 == [False, False] and h2b == 'Ansichtsmodus' and alive and r2 == [True, True],
           f'Ansichtsmodus: Titel und ⋯-Menü fragen erst nach dem Bearbeitungsmodus ({r1}, {r2})')
        await p.evaluate("history.back()"); await p.wait_for_timeout(300)
        await p.evaluate("App.state.edit=false; App.state.checklist=true; App.render()"); await p.wait_for_timeout(300)
        if await p.evaluate("!!document.querySelector('[data-act=resetchk]')"):
            await p.click('[data-act=resetchk]'); await p.wait_for_timeout(300)
            ok(await p.evaluate("document.querySelector('.dialog h2')?.textContent") == 'Ansichtsmodus', '„Zurücksetzen“ im Ansichtsmodus: erst Rückfrage')
            await p.click('.dialog .btn:has-text("Abbrechen")'); await p.wait_for_timeout(200)
        await p.evaluate("App.state.checklist=false; App.render()")
        await p.evaluate(f"location.hash='#/cue/{lid}'"); await p.wait_for_timeout(300)
        await p.click('.appbar .title-btn'); await p.wait_for_timeout(300)
        ok(await p.evaluate("document.querySelector('.dialog h2')?.textContent") == 'Ansichtsmodus', 'Cue-Liste: Titel im Ansichtsmodus mit Rückfrage')
        await p.click('.dialog .btn:has-text("Abbrechen")'); await p.wait_for_timeout(200)
        await p.evaluate("location.hash='#/'"); await p.wait_for_timeout(300)

        # ---------------- Befund 31: Fokusrahmen am Titel ----------------
        await p.evaluate(f"location.hash='#/show/{hai}'"); await p.wait_for_timeout(300)
        await p.evaluate("document.activeElement && document.activeElement.blur(); window.scrollTo(0,0)")
        found = False
        for _ in range(6):
            await p.keyboard.press('Tab')
            if await p.evaluate("document.activeElement && document.activeElement.classList.contains('title-btn')"):
                found = True; break
        st = await p.evaluate("getComputedStyle(document.activeElement).outlineStyle + ' ' + getComputedStyle(document.activeElement).outlineWidth")
        ok(found and not st.startswith('none'), f'Titel-Knopf mit sichtbarem Fokusrahmen ({st})')

        # ---------------- Befund 17: Tippflächen ----------------
        r = await p.evaluate("[...document.querySelectorAll('.syncpill, .seg button, .qb')].filter(e=>e.offsetParent).map(e=>Math.round(Math.min(e.getBoundingClientRect().height, e.getBoundingClientRect().width)))")
        ok(r and min(r) >= 44, f'Sync-Pille, Ansichts-Umschalter, Schnellzugriff mindestens 44 px ({min(r) if r else "-"})')

        # ---------------- Befund 14 + 15 + 16: Abgleich ----------------
        cA, A = await newpage(b, off=36 * 3600 * 1000, name='Uhr+36h'); cB, B = await newpage(b, name='normal')
        await imp(B, await pkg(A)); await imp(A, await pkg(B))
        await A.evaluate("(async()=>{const s=Repo.liveShows()[0]; await Repo.patchShow(s.id,{notiz:'von A'})})()")
        await imp(B, await pkg(A))
        ok(await B.evaluate("Sync.pending()") == 0 and (await B.evaluate("Sync.status()"))['state'] == 'ok', 'Nach Abgleich mit einem Gerät, dessen Uhr vorgeht: „Synchron“ statt „… offen“')
        await cA.close(); await cB.close()
        # Zug: Licht und Bühne am selben Zug, unabhängig
        cA, A = await newpage(b, name='Licht'); cB, B = await newpage(b, name='Bühne')
        await imp(B, await pkg(A))
        hai = await A.evaluate(HAI)
        await A.evaluate(f"Repo.patchShow('{hai}',{{'z:olz1':Repo.zugValue('{hai}','olz1',{{name:'OLZ 1',bestueckung:'6× PC'}})}})")
        await B.evaluate(f"Repo.patchShow('{hai}',{{'z:olz1':Repo.zugValue('{hai}','olz1',{{name:'OLZ 1',last:'200 kg',hoehe:'5,20'}})}})")
        await A.wait_for_timeout(20)
        await A.evaluate(f"Repo.patchShow('{hai}',{{'z:olz1':Repo.zugValue('{hai}','olz1',{{bemerkung:'nur Licht'}})}})")
        await imp(B, await pkg(A)); await imp(A, await pkg(B))
        za = await A.evaluate(f"(()=>{{const z=Repo.zuegeOf('{hai}').find(z=>z.id==='olz1'); return [z.bestueckung,z.last,z.hoehe,z.bemerkung]}})()")
        zb = await B.evaluate(f"(()=>{{const z=Repo.zuegeOf('{hai}').find(z=>z.id==='olz1'); return [z.bestueckung,z.last,z.hoehe,z.bemerkung]}})()")
        ok(za == zb == ['6× PC', '200 kg', '5,20', 'nur Licht'], f'Gemeinsamer Zug: Bestückung (Licht) und Last/Höhe (Bühne) bleiben beide ({za})')
        await A.evaluate(f"SetupView.editL('{hai}')"); await A.wait_for_timeout(300)
        ok(await A.evaluate("document.querySelectorAll('.zed').length>=4"), 'Beleuchterzüge-Editor öffnet mit den zusammengeführten Zügen')
        await A.evaluate("history.back()"); await A.wait_for_timeout(200)
        r = await A.evaluate("""(()=>{ let seed=5; const rnd=()=>(seed=(seed*1103515245+12345)&0x7fffffff)/0x7fffffff;
          const props=['name','hoehe','bestueckung','last','del']; const pv=()=>[null,undefined,'','X','Y',true,false][Math.floor(rnd()*7)];
          const mkObj=t=>{const o={}; props.forEach(p=>{ if(rnd()<0.7) o[p]=pv(); }); if(rnd()<0.5){ o._t={}; Object.keys(o).forEach(p=>o._t[p]=1+Math.floor(rnd()*t)); o._ft=rnd()<0.8?t:t-1; } return o; };
          const mk=()=>{const t=1+Math.floor(rnd()*6); return JSON.parse(JSON.stringify({id:'s',c:1,mod:0,f:{'z:1':mkObj(t),titel:[null,'A','B',true][Math.floor(rnd()*4)]},t:{'z:1':t,titel:1+Math.floor(rnd()*5)}}))};   // wie gespeichert (JSON)
          const N=r=>JSON.stringify([r.f, r.t]); const bad={comm:0,idem:0,assoc:0};
          for(let i=0;i<3000;i++){ const a=mk(),b=mk(),c=mk(); const ab=Rec.merge(a,b).rec, ba=Rec.merge(b,a).rec; if(N(ab)!==N(ba)) bad.comm++;
            const ab2=Rec.merge(ab,b); if(N(ab2.rec)!==N(ab)||ab2.changed) bad.idem++; if(N(Rec.merge(Rec.merge(a,b).rec,c).rec)!==N(Rec.merge(a,Rec.merge(b,c).rec).rec)) bad.assoc++; }
          return bad })()""")
        ok(r == {'comm': 0, 'idem': 0, 'assoc': 0}, f'Zug-Zusammenführung kommutativ, idempotent, assoziativ (3000 Dreiergruppen) {r}')
        r = await A.evaluate("""(()=>{ let seed=9, T=1000; const now0=Date.now; const rnd=()=>(seed=(seed*1103515245+12345)&0x7fffffff)/0x7fffffff;
          const props=['hoehe','bestueckung','last','bemerkung'];
          const oldPatch=(r,k,v,ts)=>{const x=JSON.parse(JSON.stringify(r)); x.f[k]=v; x.t[k]=Math.max(ts,(x.t[k]||0)+1); return x;};
          const oldMerge=(l,r)=>{const x=JSON.parse(JSON.stringify(l)); for(const k of new Set([...Object.keys(l.t),...Object.keys(r.t)])){const tl=l.t[k]||0,tr=r.t[k]||0,vl=JSON.stringify(l.f[k]??null),vr=JSON.stringify(r.f[k]??null); if(tr>tl||(tr===tl&&tr>0&&vr>vl)){x.f[k]=r.f[k];x.t[k]=tr;}} return x;};
          let div=0, lost=0; const clk=Clock.last; Date.now=()=>T;
          try { for(let run=0;run<1500;run++){ T=1000; Clock.last=0; const N=5, old=[false,rnd()<0.5,rnd()<0.3,false,rnd()<0.4];
            let reps=[...Array(N)].map(()=>({id:'s',c:1,mod:0,f:{'z:1':{name:'OLZ 1',hoehe:'',bestueckung:'',last:''}},t:{'z:1':1}})); const last={};
            for(let s=0;s<30;s++){ const i=Math.floor(rnd()*N);
              if(rnd()<0.6){ const p=props[Math.floor(rnd()*4)], v='v'+s, nv=Object.assign({},reps[i].f['z:1'],{[p]:v}); const ts=++T;
                if(old[i]) reps[i]=oldPatch(reps[i],'z:1',nv,ts); else { const r=Rec.patch(reps[i],{'z:1':nv}); if(r) reps[i]=r; } last[p]=v; }
              else { const j=Math.floor(rnd()*N); if(i!==j) reps[i]=old[i]?oldMerge(reps[i],reps[j]):Rec.merge(reps[i],reps[j]).rec; } }
            for(let k=0;k<3;k++) for(let i=0;i<N;i++) for(let j=0;j<N;j++) if(i!==j) reps[i]=old[i]?oldMerge(reps[i],reps[j]):Rec.merge(reps[i],reps[j]).rec;
            const vals=reps.map(r=>props.map(p=>r.f['z:1'][p]).join('|')); if(new Set(vals).size!==1) div++;
            if(!old.some(x=>x)){ const z=reps[0].f['z:1']; if(Object.keys(last).some(p=>z[p]!==last[p])) lost++; } } }
          finally { Date.now=now0; Clock.last=clk; }
          return [div, lost] })()""")
        ok(r == [0, 0], f'Simulation 1500 × 5 Geräte (teils 2.8.2): alle Geräte gleich, mit nur 2.8.3 keine Angabe verloren {r}')
        await cA.close(); await cB.close()
        # Weitergeben: Kreis L → T → B → Alle (nur „Nur Änderungen“)
        devs = {}
        for d in ('L', 'T', 'B', 'A'):
            cx, px = await newpage(b, name='Gerät ' + d, demo=False); devs[d] = (cx, px)
            await px.evaluate(f"Settings.set({{depts:{json.dumps(['L', 'T', 'B', 'R'] if d == 'A' else [d])}}})")
        L, T, Bu, Al = (devs[d][1] for d in ('L', 'T', 'B', 'A'))
        sid = await L.evaluate("(async()=>{const s=await Repo.createShow('Kreisabgleich',['L','T','B']); return s.id})()")
        for P in (T, Bu, Al): await imp(P, await pkg(L))
        await L.evaluate(f"Repo.saveDraft({{id:null,showId:'{sid}',abt:'L',f:{{kreis:'101'}},photos:{{A:[],E:[]}}}})")
        await T.evaluate(f"Repo.saveDraft({{id:null,showId:'{sid}',abt:'T',f:{{kanal:'7'}},photos:{{A:[],E:[]}}}})")
        await Bu.evaluate(f"Repo.saveDraft({{id:null,showId:'{sid}',abt:'B',f:{{zug:'Podest'}},photos:{{A:[],E:[]}}}})")
        for _ in range(2):
            await imp(T, await pkg(L, depts="['L']")); await imp(Bu, await pkg(T, depts="['T']")); await imp(Al, await pkg(Bu, depts="['B']")); await imp(L, await pkg(Al, depts="['L','T','B','R']"))
        r = await Al.evaluate(f"Repo.entriesOf('{sid}').map(e=>abtOf(e)).sort().join('')")
        rl = await L.evaluate(f"Repo.entriesOf('{sid}').map(e=>abtOf(e)).sort().join('')")
        ok(r == 'BLT' and rl == 'BLT', f'Pakete im Kreis L → T → B → Alle: alle Geräte haben alles (Alle: {r}, L: {rl})')
        # Requisite bleibt bei Geräten mit Requisite
        await Al.evaluate(f"(async()=>{{await Req.ensureHouse(); await Repo.patchShow('{sid}',{{abteilungen:['L','T','B','R']}}); await Repo.saveDraft({{id:null,showId:'{sid}',abt:'R',f:{{was:'Degen'}},photos:{{A:[]}}}})}})()")
        await imp(T, await pkg(Al, depts="['L','T','B','R']"))
        pt = await T.evaluate("(async()=>{const r=await Sync.buildPackage({type:'sync',since:0,depts:['T']}); const d=JSON.parse(await r.blob.text()); return [r.formatVersion, d.entries.filter(e=>e.f.abt==='R').length, d.house.length]})()")
        ok(pt[1] == 0 and pt[2] == 0 and pt[0] in (2, 4), f'Requisite geht nicht über Geräte ohne Requisite (Format {pt[0]})')
        for d in devs.values(): await d[0].close()

        # ---------------- Befund 24 + 25 ----------------
        r = await p.evaluate("""(async()=>{const c=document.createElement('canvas'); c.width=c.height=200; const g=c.getContext('2d'); g.fillStyle='rgba(255,0,0,1)'; g.fillRect(0,0,100,200);
          const blob=await new Promise(r=>c.toBlob(r,'image/png')); const ph=await Photo.fromFile(new File([blob],'t.png',{type:'image/png'}));
          const img=new Image(); img.src=URL.createObjectURL(new Blob([ph.full],{type:'image/jpeg'})); await img.decode(); const k=document.createElement('canvas'); k.width=k.height=ph.w; const kg=k.getContext('2d'); kg.drawImage(img,0,0);
          return [...kg.getImageData(ph.w-20,ph.w/2,1,1).data].slice(0,3)})()""")
        ok(all(v > 235 for v in r), f'Transparente PNG: Hintergrund weiß statt schwarz ({r})')
        cA, A = await newpage(b, name='A5-A'); cB, B = await newpage(b, name='A5-B')
        sid = await A.evaluate("(async()=>{const s=await Repo.createShow('Papierkorb',['L']); const es=[]; for(let i=1;i<=5;i++) es.push(Rec.create({showId:s.id},{abt:'L',kreis:String(i),chkA:false,chkE:false,del:false})); await Repo._write({entries:es}); return s.id})()")
        await imp(B, await pkg(A))
        e = await A.evaluate(f"Repo.entriesOf('{sid}').sort((a,b)=>a.f.kreis-b.f.kreis).map(e=>e.id)")
        await B.evaluate(f"Repo.deleteEntry('{e[1]}')"); await A.wait_for_timeout(30)
        await A.evaluate(f"Repo.deleteShow('{sid}')"); await A.wait_for_timeout(30)
        await B.evaluate(f"Repo.deleteEntry('{e[2]}')")
        await imp(B, await pkg(A)); await imp(A, await pkg(B))
        await A.evaluate(f"Repo.restoreShow('{sid}')"); await imp(B, await pkg(A))
        la = await A.evaluate(f"Repo.entriesOf('{sid}').map(e=>e.f.kreis).sort().join(',')")
        lb = await B.evaluate(f"Repo.entriesOf('{sid}').map(e=>e.f.kreis).sort().join(',')")
        ok(la == lb == '1,4,5', f'Wiederherstellen bringt einzeln Gelöschtes (auch vor dem Löschen der Veranstaltung) nicht zurück ({la} / {lb})')
        await cA.close(); await cB.close()

        # ---------------- Gemischter Betrieb mit 2.8.2 (nur mit zweitem Ordner) ----------------
        if URL_ALT:
            cN, N = await newpage(b, name='2.8.3'); cO, O = await newpage(b, name='2.8.2', url=URL_ALT)
            ok(await O.evaluate('APP_VERSION') == '2.8.2', 'Altgerät läuft mit 2.8.2')
            for P in (N, O): await P.evaluate("Settings.set({depts:['L','T','B']})")
            await imp(O, await pkg(N)); await imp(N, await pkg(O))
            hai = await N.evaluate(HAI)
            await N.evaluate(f"Repo.patchShow('{hai}',{{'z:olz1':Repo.zugValue('{hai}','olz1',{{bestueckung:'neu von 2.8.3'}})}})")
            await N.evaluate(f"(async()=>{{const r=RunList.todayRun('{hai}')||await RunList.create('{hai}'); await RunList.toggle(r.id, RunList.items('{hai}',['L']).filter(i=>i.vor)[0].key)}})()")
            st = await imp(O, await pkg(N))
            await O.evaluate(f"location.hash='#/show/{hai}'"); await O.wait_for_timeout(500)
            await O.evaluate("SetupView.open.L=true; SetupView.open.run=true; App.render()"); await O.wait_for_timeout(300)
            r = await O.evaluate(f"""(async()=>{{const z=Repo.zuegeOf('{hai}').find(z=>z.id==='olz1'); SetupView.editL('{hai}'); await new Promise(r=>setTimeout(r,300)); const n=document.querySelectorAll('.zed').length; history.back(); await new Promise(r=>setTimeout(r,300));
                const b=await Pdf.build('{hai}',{{kat:'all',depts:['L','B'],cover:true,compact:true}}); const run=RunList.runsOf('{hai}').find(r=>r.f.datum===RunList.isoDate()); return [z.bestueckung, n, b.size>1000, !!run]}})()""")
            ok(st.get('ungueltig') == 0 and r[0] == 'neu von 2.8.3' and r[1] >= 4 and r[2] and r[3], f'2.8.2 liest Pakete von 2.8.3: Zug, Zug-Editor, PDF, Durchgang ({r})')
            await O.evaluate(f"Repo.patchShow('{hai}',{{'z:olz1':Repo.zugValue('{hai}','olz1',{{last:'300 kg'}})}})")
            await imp(N, await pkg(O)); await imp(O, await pkg(N))
            zn = await N.evaluate(f"(()=>{{const z=Repo.zuegeOf('{hai}').find(z=>z.id==='olz1'); return [z.bestueckung,z.last]}})()")
            zo = await O.evaluate(f"(()=>{{const z=Repo.zuegeOf('{hai}').find(z=>z.id==='olz1'); return [z.bestueckung,z.last]}})()")
            ok(zn == zo == ['neu von 2.8.3', '300 kg'], f'Zug von 2.8.2 geändert: beide Geräte gleich, nichts verloren ({zn} / {zo})')
            await cN.close(); await cO.close()

        # ---------------- Gesamt: Requisite-Ansicht und PDFs laufen, keine Seitenfehler ----------------
        await p.evaluate("Settings.set({depts:['L','T','B','R']}).then(()=>Req.ensureHouse()).then(()=>Req.testShow())")
        await p.evaluate("location.hash='#/show/test-r-show'; App.state.abt='R'; App.render()"); await p.wait_for_timeout(500)
        ok(await p.evaluate("document.querySelectorAll('.erow').length") > 20, 'Requisite „Einrichten“ unverändert')
        await p.evaluate("(async()=>{const b=await Pdf.build('test-r-show',{kat:'all',depts:['R'],cover:true,compact:true}); window._pdf=Array.from(new Uint8Array(await b.arrayBuffer()))})()")
        open(f'{OUT}/283_requisite.pdf', 'wb').write(bytes(await p.evaluate('window._pdf')))
        ok(subprocess.run(['qpdf', '--check', f'{OUT}/283_requisite.pdf'], capture_output=True).returncode == 0, 'PDF Requisite: qpdf --check')
        ok(not ERRS, 'Keine Seitenfehler ' + ('' if not ERRS else str(ERRS[:4])))
        await b.close()
    print('\n' + ('ALLES OK' if not fails else f'{len(fails)} FEHLER'))
asyncio.run(main())
