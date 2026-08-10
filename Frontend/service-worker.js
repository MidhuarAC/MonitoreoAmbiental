const CACHE_NAME = "monitoreo-ambiental-v1";

const ARCHIVOS_APP = [
    "/",
    "/index.html",
    "/manifest.json"
];

self.addEventListener("install", (event) => {
    console.log("Service Worker: instalando...");

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                return cache.addAll(ARCHIVOS_APP);
            })
            .then(() => {
                return self.skipWaiting();
            })
    );
});


self.addEventListener("activate", (event) => {
    console.log("Service Worker: activado");

    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys
                    .filter((key) => key !== CACHE_NAME)
                    .map((key) => caches.delete(key))
            );
        }).then(() => {
            return self.clients.claim();
        })
    );
});


self.addEventListener("fetch", (event) => {

    const url = new URL(event.request.url);

    /*
     * MUY IMPORTANTE:
     * NO interceptar las llamadas a la API.
     *
     * La función consultarDatos() del index.html
     * será la encargada de:
     *
     * 1. Intentar consultar la API cuando hay Internet.
     * 2. Si falla, consultar IndexedDB.
     */

    if (url.pathname.startsWith("/api/")) {
        return;
    }


    /*
     * Para archivos de la aplicación:
     * primero intenta Internet y, si no hay,
     * utiliza la versión almacenada en caché.
     */

    event.respondWith(
        fetch(event.request)
            .then((response) => {

                if (
                    !response ||
                    response.status !== 200 ||
                    response.type !== "basic"
                ) {
                    return response;
                }

                const responseClone = response.clone();

                caches.open(CACHE_NAME)
                    .then((cache) => {
                        cache.put(event.request, responseClone);
                    });

                return response;
            })
            .catch(() => {
                return caches.match(event.request);
            })
    );
});