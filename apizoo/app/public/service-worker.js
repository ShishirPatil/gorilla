const CACHE_NAME = 'apizoo-data-cache';
const urlsToCache = [
  'https://apizooindex.gorilla-llm.com/api/data',
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            return cache.addAll(urlsToCache);
        })
    );
});

self.addEventListener('activate', event => {
    event.waitUntil(clients.claim());
});

// Implement 'stale-while-revalidate' cache strategy: return the cached data immediately (if available) for a fast response, 
// while the fetchPromise runs in the background to update the cache.
self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request).then(cachedResponse => {
            const fetchPromise = fetch(event.request).then(networkResponse => {
                if (networkResponse.ok) {
                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(event.request, networkResponse.clone());
                    });
                }
                return networkResponse;
            }).catch(error => {
                console.error(`[Service Worker] Fetching resource: ${event.request.url}`, error);
                throw error;
            });
            return cachedResponse || fetchPromise;
        })
    );
});