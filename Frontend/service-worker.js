const CACHE_NAME = "monitoreo-ambiental-v2";

const ARCHIVOS = [
    "/",
    "/manifest.json",
    "/service-worker.js"
];

self.addEventListener("install", event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(ARCHIVOS))
            .then(() => self.skipWaiting())
    );
});

self.addEventListener("activate", event => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(
                keys
                    .filter(key => key !== CACHE_NAME)
                    .map(key => caches.delete(key))
            )
        ).then(() => self.clients.claim())
    );
});

self.addEventListener("fetch", event => {

    const request = event.request;

    // Ignorar cosas que no sean HTTP/HTTPS
    if (!request.url.startsWith("http://") &&
        !request.url.startsWith("https://")) {
        return;
    }

    // Solo nos interesa GET
    if (request.method !== "GET") {
        return;
    }

    const url = new URL(request.url);

    // ==========================================
    // API: INTERNET -> guardar / OFFLINE -> usar
    // ==========================================

    if (url.pathname.startsWith("/api/")) {

        event.respondWith(
            fetch(request)
                .then(response => {

                    if (response.ok) {
                        const copia = response.clone();

                        caches.open(CACHE_NAME)
                            .then(cache => {
                                cache.put(request, copia);
                            });
                    }

                    return response;
                })
                .catch(() => {
                    return caches.match(request);
                })
        );

        return;
    }

    // ==========================================
    // PÁGINA Y ARCHIVOS
    // ==========================================

    event.respondWith(
        caches.match(request)
            .then(response => {
                return response || fetch(request);
            })
    );
});