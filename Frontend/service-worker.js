const CACHE_NAME = "monitoreo-ambiental-v2";

const ARCHIVOS_APP = [
    "/",
    "/index.html",
    "/manifest.json"
];

self.addEventListener("install", (event) => {
    console.log("Service Worker: instalando v2...");

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => cache.addAll(ARCHIVOS_APP))
            .then(() => self.skipWaiting())
    );
});

self.addEventListener("activate", (event) => {
    console.log("Service Worker: activado v2");

    event.waitUntil(
        caches.keys()
            .then((keys) => Promise.all(
                keys
                    .filter((key) => key !== CACHE_NAME)
                    .map((key) => caches.delete(key))
            ))
            .then(() => self.clients.claim())
    );
});

self.addEventListener("fetch", (event) => {

    const url = new URL(event.request.url);

    // No interceptar la API.
    // El index.html se encarga de usar PostgreSQL
    // o IndexedDB según corresponda.
    if (url.pathname.startsWith("/api/")) {
        return;
    }

    // Para la aplicación y recursos externos:
    // primero intenta Internet y, si falla,
    // utiliza la versión guardada en caché.
    event.respondWith(
        fetch(event.request)
            .then((response) => {

                if (
                    !response ||
                    response.status !== 200
                ) {
                    return response;
                }

                const responseClone = response.clone();

                caches.open(CACHE_NAME)
                    .then((cache) => {
                        cache.put(event.request, responseClone);
                    })
                    .catch(() => {});

                return response;
            })
            .catch(() => {

                return caches.match(event.request)
                    .then((cached) => {

                        if (cached) {
                            return cached;
                        }

                        if (event.request.mode === "navigate") {
                            return caches.match("/index.html");
                        }

                        return new Response(
                            "Recurso no disponible sin conexión.",
                            {
                                status: 503,
                                headers: {
                                    "Content-Type":
                                        "text/plain; charset=utf-8"
                                }
                            }
                        );
                    });
            })
    );
});