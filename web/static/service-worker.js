const CACHE_NAME = "adamsy-free-tv-shell-v1";
const SHELL_ASSETS = [
  "/",
  "/static/styles.css",
  "/static/app.js",
  "/static/manifest.webmanifest",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

// App shell only: HTML/CSS/JS/manifest use network-first (falls back to the
// cached shell offline). Everything else - the channel API, streams, the
// hls.js CDN script - is left to the network untouched, since that data is
// live and must never be served stale.
self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") {
    return;
  }

  const url = new URL(request.url);
  const isShellAsset =
    url.origin === self.location.origin && SHELL_ASSETS.includes(url.pathname);

  if (!isShellAsset) {
    return;
  }

  event.respondWith(
    fetch(request)
      .then((response) => {
        const copy = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
        return response;
      })
      .catch(() => caches.match(request))
  );
});
