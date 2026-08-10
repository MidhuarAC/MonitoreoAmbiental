// ==========================================================
// SERVICE WORKER - MONITOREO AMBIENTAL
// ==========================================================

const CACHE_NAME = "monitoreo-ambiental-v2";


// ==========================================================
// ARCHIVOS ESTÁTICOS
// ==========================================================

const ARCHIVOS_CACHE = [
    "/",
    "/index.html",
    "/manifest.json"
];


// ==========================================================
// INSTALAR
// ==========================================================

self.addEventListener("install", event => {

    console.log("Service Worker instalando...");

    event.waitUntil(
        caches
            .open(CACHE_NAME)
            .then(cache => cache.addAll(ARCHIVOS_CACHE))
    );

    self.skipWaiting();

});


// ==========================================================
// ACTIVAR
// ==========================================================

self.addEventListener("activate", event => {

    console.log("Service Worker activado.");

    event.waitUntil(
        caches
            .keys()
            .then(nombres => {

                return Promise.all(
                    nombres
                        .filter(nombre => nombre !== CACHE_NAME)
                        .map(nombre => caches.delete(nombre))
                );

            })
    );

    self.clients.claim();

});


// ==========================================================
// FETCH
// ==========================================================

self.addEventListener("fetch", event => {

    const request = event.request;

    if (request.method !== "GET") {
        return;
    }

    const url = new URL(request.url);


    // ======================================================
    // MUY IMPORTANTE:
    // NO INTERCEPTAR NINGUNA PETICIÓN DE LA API
    // ======================================================

    if (url.pathname.startsWith("/api/")) {
        return;
    }


    // ======================================================
    // NO INTERCEPTAR OTROS DOMINIOS
    // ======================================================

    if (url.origin !== self.location.origin) {
        return;
    }


    // ======================================================
    // ARCHIVOS DEL FRONTEND
    // NETWORK FIRST → CACHE COMO RESPALDO
    // ======================================================

    event.respondWith(

        fetch(request)
            .then(response => {

                if (response && response.ok) {

                    const copia = response.clone();

                    caches
                        .open(CACHE_NAME)
                        .then(cache => {
                            cache.put(request, copia);
                        })
                        .catch(error => {
                            console.warn(
                                "No se pudo guardar en cache:",
                                error
                            );
                        });

                }

                return response;

            })
            .catch(() => {

                console.log(
                    "📴 Usando archivo desde cache:",
                    request.url
                );

                return caches.match(request);

            })

    );

});
