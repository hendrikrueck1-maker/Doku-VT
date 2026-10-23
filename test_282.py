"""Doku VT 2.8.2 – Test: Schnellauswahl der Cue-Nummern beim Anlegen, ±0,1 in der Cue-Kamera.
Aufruf: python3 test_282.py <ordner>"""
import asyncio, sys, http.server, threading, functools, os, json
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
        # ---- Rechenregeln ----
        r = await p.evaluate("""[Cues.stepNr('13',1), Cues.stepNr('13',-1), Cues.stepNr('13.9',1), Cues.stepNr('12.25',1), Cues.stepNr('0',-1), Cues.stepNr('Ende',1), Cues.stepNr('0.1',-1)]""")
        print('  ', r)
        ok(r == ['13.1', '12.9', '14', '12.35', None, None, '0'], '±0,1: 13→13.1/12.9, 13.9→14, 12.25→12.35, nicht unter 0, Text bleibt')
        lid = await p.evaluate("(async()=>{const l=await Cues.createList({titel:'Schnellauswahl'}); return l.id})()")
        q0 = await p.evaluate(f"Cues.quickNrs('{lid}')")
        ok(q0['next'] == ['1', '2', '3'] and q0['dots'] == [], 'Leere Liste: Vorschlag 1, 2, 3, keine Punktstimmungen')
        await p.evaluate(f"Cues.addRange('{lid}','1','13','1')")
        q = await p.evaluate(f"Cues.quickNrs('{lid}')")
        ok(q['next'] == ['14', '15', '16'] and q['dots'] == ['13.%d' % i for i in range(1, 10)], 'Letzte Cue 13: 14–16 und 13.1–13.9')
        await p.evaluate(f"(async()=>{{await new Promise(r=>setTimeout(r,5)); await Repo._write({{cues:[Cues.newCue('{lid}','15')]}})}})()")
        q = await p.evaluate(f"Cues.quickNrs('{lid}')")
        print('  ', q)
        ok(q['base'] == 15 and q['next'] == ['16', '17', '18'] and '15.1' in q['dots'], 'Zuletzt angelegt 15 → 16–18, 15.x')
        await p.evaluate(f"(async()=>{{await new Promise(r=>setTimeout(r,5)); await Repo._write({{cues:[Cues.newCue('{lid}','13.5'), Cues.newCue('{lid}','13.2')]}})}})()")
        q = await p.evaluate(f"Cues.quickNrs('{lid}')")
        ok(q['base'] == 13 and q['next'] == ['14', '16'] and '13.2' not in q['dots'] and '13.5' not in q['dots'] and len(q['dots']) == 7,
           f'Zuletzt 13.2: Basis 13, vorhandene Nummern fallen weg ({q["next"]}, {q["dots"]})')
        # ---- über die Oberfläche: + Cue ----
        await p.evaluate(f"App.state.edit=true; location.hash='#/cue/{lid}'"); await p.wait_for_timeout(500)
        await p.click('[data-cact=addcue]'); await p.wait_for_timeout(300)
        r = await p.evaluate("[document.querySelector('[data-editor] [name=nr]').value, [...document.querySelectorAll('.pickkeys')].map(g=>[...g.querySelectorAll('button')].map(b=>b.textContent)), [...document.querySelectorAll('.pickh')].map(x=>x.textContent)]")
        print('  ', r)
        ok(r[0] == '14' and r[1][0] == ['14', '16'] and r[1][1][0] == '13.1' and 'Punktstimmungen zu 13' in r[2], 'Blatt „Neue Cue“: Vorschlag 14, Schnellauswahl Nächste + Punktstimmungen')
        await p.screenshot(path=f'{OUT}/282_neue_cue.png')
        await p.click('.pickkeys button:text-is("13.4")'); await p.wait_for_timeout(100)
        r = await p.evaluate("[document.querySelector('[data-editor] [name=nr]').value, document.querySelector('.pickkeys button[aria-pressed=true]').textContent]")
        ok(r == ['13.4', '13.4'], 'Antippen setzt die Nummer und markiert sie')
        await p.click('[data-editor] [data-ok]'); await p.wait_for_timeout(600)
        ok(await p.evaluate(f"!!Cues.cueByNr('{lid}','13.4')"), 'Cue 13.4 angelegt')
        await p.click('[data-cact=addcue]'); await p.wait_for_timeout(300)
        ok(await p.evaluate("![...document.querySelectorAll('.pickkeys button')].some(b=>b.textContent==='13.4')"), 'Danach steht 13.4 nicht mehr in der Auswahl')
        await p.evaluate("history.back()"); await p.wait_for_timeout(300)
        # ---- Kamera ±0,1 ----
        c13 = await p.evaluate(f"Cues.cueByNr('{lid}','13').id")
        await p.evaluate(f"void CueCam.open({{listId:'{lid}', cueId:'{c13}'}})")
        await p.wait_for_function("document.querySelector('.ccam video') && document.querySelector('.ccam video').videoWidth>0", timeout=15000)
        nr = lambda: p.evaluate("document.querySelector('.ccam [data-nr]').textContent")
        ok(await nr() == '13', 'Kamera bei Cue 13')
        await p.click('.ccam [data-a="nr+"]'); ok(await nr() == '13.1', '+0.1 → 13.1')
        await p.click('.ccam [data-a="nr+"]'); await p.click('.ccam [data-a="nr+"]'); ok(await nr() == '13.3', '+0.1 zweimal → 13.3')
        await p.click('.ccam [data-a="nr-"]'); ok(await nr() == '13.2', '−0.1 → 13.2 (gibt es schon)')
        lbl = await p.evaluate("document.querySelector('.ccam [data-lbl]').textContent")
        await p.click('.ccam [data-a="nr+"]')        # 13.3, neu
        await p.click('.ccam [data-a=shot]'); await p.click('.ccam [data-a=shot]')
        await p.click('.ccam [data-a="nr+"]')        # 13.4 (vorhanden)
        await p.click('.ccam [data-a=shot]')
        await p.wait_for_function('CueCam.pending()===0 && !CueCam.busy', timeout=20000); await p.wait_for_timeout(200)
        r = await p.evaluate(f"['13.2','13.3','13.4'].map(n=>{{const c=Cues.cueByNr('{lid}',n); return n+':'+(c?Cues.imgsOf(c.id).length:'-')}}).join(' ')")
        ok(r == '13.2:0 13.3:2 13.4:1', 'Punktstimmung 13.3 mit dem ersten Foto angelegt, Fotos A/B; 13.4 bekommt Foto: ' + r)
        ok(await p.evaluate(f"Cues.cuesOf('{lid}').filter(c=>c.f.nr==='13.1').length") == 0, 'Durchgezählte Nummer ohne Foto legt keine Cue an')
        await p.keyboard.press('ArrowUp'); ok(await nr() == '13.5', 'Taste ↑ = +0.1')
        await p.screenshot(path=f'{OUT}/282_cam.png')
        # Text-Nummer: Hinweis statt Fehler
        await p.click('.ccam [data-a=nr]'); await p.wait_for_timeout(200)
        await p.fill('.dialog input.txt', 'Ende'); await p.click('.dialog .btn.primary'); await p.wait_for_timeout(200)
        await p.click('.ccam [data-a="nr+"]'); await p.wait_for_timeout(200)
        ok(await nr() == 'Ende' and 'Zahlen' in await p.evaluate("document.querySelector('#toasts').textContent"), 'Text-Nummer: ±0,1 mit Hinweis, Nummer bleibt')
        await p.click('.ccam [data-a=close]'); await p.wait_for_timeout(300)
        # ---- Smartphone: alles im Bild ----
        for (w, h) in [(390, 844), (375, 667)]:
            c2, p2, e2 = await newpage(b, w, h)
            l2 = await p2.evaluate("(async()=>{const l=await Cues.createList({titel:'Telefon'}); await Cues.addRange(l.id,'1','5','1'); return l.id})()")
            await p2.evaluate(f"App.state.edit=true; location.hash='#/cue/{l2}'"); await p2.wait_for_timeout(500)
            await p2.click('[data-cact=cam]')
            await p2.wait_for_function("document.querySelector('.ccam video') && document.querySelector('.ccam video').videoWidth>0", timeout=15000)
            r = await p2.evaluate("""(()=>{const vis=s=>{const r=document.querySelector(s).getBoundingClientRect(); return r.bottom<=innerHeight && r.right<=innerWidth && r.width>0};
              return [vis('.ccam .shutter'), vis('.ccam .cnext'), vis('.ccam [data-a="nr+"]'), vis('.ccam [data-a="nr-"]'), vis('.ccam .cnr'),
                Math.round(document.querySelector('.ccam [data-a="nr+"]').getBoundingClientRect().height), Math.round(document.querySelector('.ccam .vf').getBoundingClientRect().width),
                document.querySelector('.ccam [data-a="nr+"]').getBoundingClientRect().bottom <= document.querySelector('.ccam .cnext').getBoundingClientRect().top]})()""")
            print('  ', w, h, r)
            ok(all(r[:5]) and r[5] >= 44 and r[7], f'Smartphone {w}×{h}: ±0.1 über „Nächster Cue“, alles im Bild (Sucher {r[6]} px)')
            await p2.screenshot(path=f'{OUT}/282_phone_{w}x{h}.png')
            await p2.evaluate("Settings.set({theme:'red'})"); await p2.wait_for_timeout(200)
            await p2.screenshot(path=f'{OUT}/282_phone_{w}x{h}_rot.png')
            await p2.click('.ccam [data-a=close]')
            errs += e2; await c2.close()
        ok(not errs, 'Keine Seitenfehler ' + ('' if not errs else str(errs[:5])))
        await b.close()
    print('\n' + ('ALLES OK' if not fails else f'{len(fails)} FEHLER'))
asyncio.run(main())
