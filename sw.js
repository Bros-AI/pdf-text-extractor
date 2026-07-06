/* Service worker — makes the app work offline after the first visit.
   Strategy: network-first for page navigations (updates land immediately),
   cache-first for same-origin assets and immutable CDN files (pdf.js,
   Tesseract.js and its OCR language data). */

const VERSION = "v1";
const CACHE = `pdf-extractor-${VERSION}`;

const PRECACHE = [
  "./",
  "index.html",
  "pdf-to-text.html",
  "ocr-pdf.html",
  "how-to-extract-text-from-pdf.html",
  "privacy.html",
  "about.html",
  "404.html",
  "manifest.webmanifest",
  "icon-192.png",
  "icon-512.png",
  "apple-touch-icon.png",
];

// Hosts serving immutable, versioned assets (safe to cache forever)
const CDN_HOSTS = ["cdn.jsdelivr.net", "tessdata.projectnaptha.com"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE)
      .then((cache) => cache.addAll(PRECACHE))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

async function cacheFirst(request) {
  const cache = await caches.open(CACHE);
  const hit = await cache.match(request);
  if (hit) return hit;
  const response = await fetch(request);
  if (response.ok || response.type === "opaque") {
    cache.put(request, response.clone());
  }
  return response;
}

async function networkFirst(request) {
  const cache = await caches.open(CACHE);
  try {
    const response = await fetch(request);
    if (response.ok) cache.put(request, response.clone());
    return response;
  } catch {
    const hit = await cache.match(request);
    return hit || cache.match("index.html");
  }
}

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  const url = new URL(event.request.url);

  if (CDN_HOSTS.includes(url.hostname)) {
    event.respondWith(cacheFirst(event.request));
    return;
  }
  if (url.origin === location.origin) {
    event.respondWith(
      event.request.mode === "navigate"
        ? networkFirst(event.request)
        : cacheFirst(event.request)
    );
  }
});
