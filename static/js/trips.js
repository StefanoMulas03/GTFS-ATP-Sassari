const tripModal = new bootstrap.Modal(document.getElementById("tripModal")); 
let tripIdDaEliminare = null;


const routeId = document.body.dataset.routeId; // prende il valore da data-route-id
console.log("Route ID:", routeId);

function mostraToast(testo, tipo = "success") {
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

async function caricaTrips() {
    const btnDurata = document.querySelector('button[onclick="caricaDurataMedia()"]');
    const btnFascia = document.querySelector('button[onclick="caricaGraficoLinee()"]');

    const res = await fetch(`/api/trips?route_id=${routeId}`);
    const trips = await res.json();

    const tbody = document.getElementById("trips-body");
    tbody.innerHTML = "";

    // Se non ci sono trips, mostra messaggio
    if (trips.length === 0) {
    // Nascondi pulsanti dei grafici
    btnDurata.style.display = "none";
    btnFascia.style.display = "none";
    
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="6" class="text-center fst-italic">Nessuna corsa disponibile per questa linea</td>`;
    tbody.appendChild(tr);

    return;
    }


    // Mostra pulsanti dei grafici se ci sono corse
    btnDurata.style.display = "inline-block";
    btnFascia.style.display = "inline-block";


    for (const t of trips) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
        <td>${t.trip_id}</td>
        <td>${t.trip_headsign || ""}</td>
        <td>${t.trip_short_name || ""}</td>
        <td class="bg-warning">${t.departure_time || ""}</td>  
        <td>${t.arrival_time || ""}</td>
        <td>
        <button class="btn btn-sm btn-action-modify" onclick='modificaCorsa(${JSON.stringify(t)})'>Modifica</button>
        <button class="btn btn-sm btn-action-delete" onclick='eliminaCorsa("${t.trip_id}")'>Elimina</button>
        <a class="btn btn-sm btn-action-details" href="/trip/${t.trip_id}">Dettagli</a>
        </td>
    `;
    tbody.appendChild(tr);
    }
} 

function apriModalNuovaCorsa() {
    document.getElementById("modalTitle").textContent = "Nuova Corsa";
    document.getElementById("modalMode").value = "create";
    document.getElementById("trip_id").value = "";
    document.getElementById("trip_id").disabled = false;
    document.getElementById("trip_headsign").value = "";
    document.getElementById("trip_short_name").value = "";
    tripModal.show();
}

function modificaCorsa(trip) {
    document.getElementById("modalTitle").textContent = "Modifica Corsa";
    document.getElementById("modalMode").value = "edit";
    document.getElementById("originalTripId").value = trip.trip_id;
    document.getElementById("trip_id").value = trip.trip_id;
    document.getElementById("trip_id").disabled = true;
    document.getElementById("trip_headsign").value = trip.trip_headsign || "";
    document.getElementById("trip_short_name").value = trip.trip_short_name || "";
    tripModal.show();
}

async function salvaCorsa(event) {
    event.preventDefault();

    const mode = document.getElementById("modalMode").value;
    const trip_id = document.getElementById("trip_id").value.trim();
    const trip_headsign = document.getElementById("trip_headsign").value.trim();
    const trip_short_name = document.getElementById("trip_short_name").value.trim();

    const payload = {
    trip_id,
    route_id: routeId,
    trip_headsign: trip_headsign || null,
    trip_short_name: trip_short_name || null
    };

    try {
    if (mode === "create") {
        const res = await fetch("/api/trips", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        });

        if (!res.ok) throw await res.json();
        mostraToast("Corsa creata con successo", "success");
    } else if (mode === "edit") {
        const res = await fetch(`/api/trips/${trip_id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        });

        if (!res.ok) throw await res.json();
        mostraToast("Corsa modificata con successo", "success");
    }

    tripModal.hide();
    await caricaTrips();
    } catch (err) {
    mostraToast("Errore: " + (err.detail || "Impossibile salvare la corsa"), "danger");
    }
}

function eliminaCorsa(trip_id) {
    tripIdDaEliminare = trip_id;
    const deleteModal = new bootstrap.Modal(document.getElementById("confirmDeleteModal"));
    deleteModal.show();
}

async function confermaEliminazione() {
    try {
    const res = await fetch(`/api/trips/${tripIdDaEliminare}`, {
        method: "DELETE",
    });

    if (!res.ok) throw await res.json();
    mostraToast("Corsa eliminata", "success");
    await caricaTrips();
    } catch (err) {
    mostraToast("Errore: " + (err.detail || "Impossibile eliminare la corsa"), "danger");
    }

    const deleteModalEl = document.getElementById("confirmDeleteModal");
    const deleteModal = bootstrap.Modal.getInstance(deleteModalEl);
    deleteModal.hide();
    tripIdDaEliminare = null;
}

// Carica le corse al caricamento della pagina
caricaTrips();



let graficoDurataAttivo = false;
let graficoIntervalloAttivo = false;

async function caricaDurataMedia() {
const cont = document.getElementById("grafico-durata");
if (graficoDurataAttivo) { cont.innerHTML = ""; graficoDurataAttivo=false; return; }
cont.innerHTML = "<p>Caricamento...</p>";
try {
    const res = await fetch(`/api/trips/${routeId}/durata_media`);
    const data = await res.json();
    cont.innerHTML = `<p>Durata media corsa: <strong>${data.durata_media_minuti} minuti</strong></p>`;
    graficoDurataAttivo = true;
} catch { cont.innerHTML = '<p class="text-danger">Errore nel caricamento.</p>'; }
}




async function caricaGraficoLinee() {
const cont = document.getElementById("grafico-corse-ora");
if (graficoIntervalloAttivo) { cont.innerHTML = ""; graficoIntervalloAttivo=false; return; }
cont.innerHTML = "<p>Caricamento...</p>";

try {
    const res = await fetch(`/api/trips/${routeId}/corse_per_ora`);
    const data = await res.json();

    const x = data.map(d => d.hour + ":00");
    const y = data.map(d => d.num_trips);

    cont.innerHTML = '';
    Plotly.newPlot(cont, [{
        x: x,
        y: y,
        type: 'scatter',
        mode: 'lines+markers',
        line: { color: 'rgb(0,122,255)' }
    }], {
        margin: {t:30},
        xaxis: { title: 'Ora' },
        yaxis: { title: 'Numero corse' }
    });

    graficoIntervalloAttivo = true;
} catch {
    cont.innerHTML = '<p class="text-danger">Errore nel caricamento del grafico.</p>';
}
}
