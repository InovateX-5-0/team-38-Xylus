const CACHE_NAME = "petcare-cache-v1";
const urlsToCache = [
  "/",
  "/offline",
  "/offline.html",
  "/static/css/style.css",
  "/static/js/app.js",
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => Promise.allSettled(urlsToCache.map(url => cache.add(url))))
  );
});

self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});