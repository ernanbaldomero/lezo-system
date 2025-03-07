self.addEventListener('install', event => {
    event.waitUntil(
        caches.open('lezo-system-v1').then(cache => {
            return cache.addAll([
                '/citizens/',
                '/static/core/sw.js'
            ]);
        })
    );
});

self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request).then(response => {
            return response || fetch(event.request);
        })
    );
});
