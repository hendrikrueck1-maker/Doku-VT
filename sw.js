/* Doku VT – Service Worker
   Offline-Start: Die App-Dateien kommen aus dem Cache, im Hintergrund wird
   die neue Fassung geholt (stale-while-revalidate). Bei jeder neuen Version
   VERSION erhöhen – dann wird der alte Cache entfernt.                       */
const VERSION = '1.5.0';
const CACHE = 'dokuvt-' + VERSION;
const CORE = ['./', './index.html', './manifest.json'];                       // muss vorhanden sein
const EXTRA = ['./icon-192.png', './icon-512.png', './icon-maskable-512.png', './apple-touch-icon.png'];  // fehlertolerant

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(async c => {
    await c.addAll(CORE);
    await Promise.all(EXTRA.map(u => c.add(u).catch(() => null)));   // fehlendes Icon verhindert die Installation nicht
  }));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k.startsWith('dokuvt-') && k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('message', e => { if (e.data === 'SKIP_WAITING') self.skipWaiting(); });
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;
  if (url.pathname.endsWith('/version.json')) return;          // immer frisch vom Server
  const isPage = req.mode === 'navigate';
  e.respondWith(caches.open(CACHE).then(async cache => {
    const key = isPage ? './index.html' : req;
    const cached = await cache.match(key, { ignoreSearch: true });
    const net = fetch(req).then(res => { if (res && res.ok && res.type === 'basic') cache.put(key, res.clone()); return res; }).catch(() => null);
    if (cached) { e.waitUntil(net); return cached; }
    return (await net) || new Response('Offline – Seite nicht im Cache', { status: 503, headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
  }));
});
