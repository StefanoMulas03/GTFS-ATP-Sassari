
const tripId = document.body.dataset.tripId; // prende il valore da data-route-id
console.log("Trip ID:", tripId);

function mostraToast(testo, tipo = "danger") {
    const toastContainer = document.getElementById("toastContainer");

    const toastEl = document.createElement("div");
    toastEl.className = `toast align-items-center text-white bg-${tipo} border-0`;
    toastEl.setAttribute("role", "alert");
    toastEl.setAttribute("aria-live", "assertive");
    toastEl.setAttribute("aria-atomic", "true");

    toastEl.innerHTML = `
        <div class="d-flex">
        <div class="toast-body">${testo}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    toastContainer.appendChild(toastEl);

    const bsToast = new bootstrap.Toast(toastEl, { delay: 3000 });
    bsToast.show();

    toastEl.addEventListener("hidden.bs.toast", () => {
        toastEl.remove();
    });
    }



async function caricaStopTimes() {
    try {
    const btnmedia = document.querySelector("button[onclick='caricamediaStopTimes()']");
    const btnMappa = document.querySelector("button[onclick='loadMap(tripId)']");

    const res = await fetch(`/api/stop_times?trip_id=${tripId}`);
    if (!res.ok) throw new Error("Errore nel caricamento");
    const stopTimes = await res.json();

    const tbody = document.getElementById("stop-times-body");
    tbody.innerHTML = "";


    if (stopTimes.length === 0) {
        // Nascondi i pulsanti
        btnmedia.style.display = "none";
        btnMappa.style.display = "none";

        const tr = document.createElement("tr");
        tr.innerHTML = `<td colspan="4" class="text-center fst-italic">Nessuna fermata disponibile per questa corsa</td>`;
        tbody.appendChild(tr);
        return;
    }


    // Se ci sono stop times, mostra i pulsanti
    btnmedia.style.display = "inline-block";
    btnMappa.style.display = "inline-block";
    

    for (const st of stopTimes) {
        const tr = document.createElement("tr");
        tr.innerHTML = `
        <td>${st.stop_sequence}</td>
        <td>${st.stop_name}</td>
        <td>${st.arrival_time || ""}</td>
        <td>${st.departure_time || ""}</td>
        `;
        tbody.appendChild(tr);
    }
    } catch (err) {
    mostraToast("Errore: " + err.message, "danger");
    }
}

caricaStopTimes();





let mediacaricata = false;
let mappaCaricata = false;




async function caricamediaStopTimes() {
    const cont = document.getElementById("media-stop-times");
    if (mediacaricata) { cont.innerHTML = ""; mediacaricata = false; return; }
    cont.innerHTML = "<p>Caricamento media...</p>";

    try {
        const res = await fetch(`/api/stop_times/${tripId}/num_stops`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        cont.innerHTML = `<p>Numero totale fermate: <strong>${data.num_stops}</strong></p>`;
        mediacaricata = true;
    } catch (err) {
        console.error("Errore media:", err);
        cont.innerHTML = `<p class="text-danger">Errore nel caricamento dell'media: ${err.message}</p>`;
    }
}






async function loadMap(tripId) {
    const mapContainer = document.getElementById("map");

    if (mappaCaricata) {
        // Nasconde e svuota la mappa
        mapContainer.style.display = "none";
        mapContainer.innerHTML = "";
        mappaCaricata = false;
        return;
    }

    try {
        const response = await fetch(`/api/stop_times/${tripId}/shape`);
        if (!response.ok) throw new Error("Errore nel caricamento dati");
        const data = await response.json();
       
        const shapeCoords = data.shape_coordinates;
        const stops = data.stops;

        if (!shapeCoords || shapeCoords.length === 0) throw new Error("Nessuna coordinate trovata");

        const lats = shapeCoords.map(c => c[0]);
        const lons = shapeCoords.map(c => c[1]);
        
        const stopLats = stops.map(s => s.stop_lat);
        const stopLons = stops.map(s => s.stop_lon);
        const stopNames = stops.map(s => s.stop_name);


        // Centro dinamico
        const centerLat = lats.reduce((a,b)=>a+b,0)/lats.length;
        const centerLon = lons.reduce((a,b)=>a+b,0)/lons.length;

        const traceShape = {
            type: "scattermapbox",
            mode: "lines",
            lat: lats,
            lon: lons,
            line: { width: 4, color: "blue" },
            name: "Percorso"
        };

        const traceStops = {
            type: "scattermapbox",
            mode: "markers",
            lat: stopLats,
            lon: stopLons,
            marker: { size: 8, color: "red" },
            text: stopNames, // mostra il nome della fermata al passaggio del mouse
            name: "Fermate"
        };


        const layout = {
            mapbox: {
                style: "open-street-map",
                center: { lat: centerLat, lon: centerLon },
                zoom: 13
            },
            margin: { t: 0, b: 0, l: 0, r: 0 }
        };

        // Mostra il div mappa
        mapContainer.style.display = "block";
        Plotly.newPlot("map", [traceShape, traceStops], layout);
        mappaCaricata = true;

    } catch (err) {
        console.error("Errore mappa:", err);
        mostraToast("Errore mappa: " + err.message, "danger");
    }
}