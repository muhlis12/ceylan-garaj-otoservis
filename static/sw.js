self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open('otoservis-pro-v1').then((cache) => {
      return cache.addAll([
        '/',
        '/static/manifest.webmanifest',
        '/static/icons/icon-192.png',
        '/static/icons/icon-512.png'
      ]);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  event.respondWith(
    caches.match(req).then((cached) => cached || fetch(req))
  );
});
