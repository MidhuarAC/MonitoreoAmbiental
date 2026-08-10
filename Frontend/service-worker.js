const CACHE_NAME = "monitoreo-ambiental-v2";

const ARCHIVOS = [
    "/",
    "/manifest.json",
    "/service-worker.js"
];

// INSTALACIÓN
self.addEventListener("install", event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(ARCHIVOS))
    );

    self.skipWaiting();
});

// ACTIVACIÓN
self.addEventListener("activate", event => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(
                keys
                    .filter(key => key !== CACHE_NAME)
                    .map(key => caches.delete(key))
            )
        )
    );

    self.clients.claim();
});

// PETICIONES
self.addEventListener("fetch", event => {

    // Solo nos interesan peticiones GET
    if (event.request.method !== "GET") {
        return;
    }

    const url = new URL(event.request.url);

    // API: primero intenta Internet.
    // Si no hay Internet, utiliza la copia guardada.
    if (url.pathname.startsWith("/api/")) {

        event.respondWith(
            fetch(event.request)
                .then(response => {

                    // Guardar una copia de la respuesta
                    const copia = response.clone();

                    caches.open(CACHE_NAME)
                        .then(cache => {
                            cache.put(event.request, copia);
                        });

                    return response;
                })
                .catch(() => {
                    return caches.match(event.request);
                })
        );

        return;
    }

    // Archivos de la aplicación:
    // primero busca una copia local.
    event.respondWith(
        caches.match(event.request)
            .then(cachedResponse => {

                if (cachedResponse) {
                    return cachedResponse;
                }

                return fetch(event.request)
                    .then(response => {

                        const copia = response.clone();

                        caches.open(CACHE_NAME)
                            .then(cache => {
                                cache.put(event.request, copia);
                            });

                        return response;
                    });
            })
    );
});