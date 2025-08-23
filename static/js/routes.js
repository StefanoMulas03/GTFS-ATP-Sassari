
const routeModal = new bootstrap.Modal(document.getElementById("routeModal"));
let routeIdDaEliminare = null;

function mostraToast(testo, tipo = "success") {
    const toastContainer = document.getElementById("toastContainer");

    const toastEl = document.createElement("div");
    toastEl.className = `toast align-items-center text-white bg-${tipo} border-0`;
    toastEl.setAttribute("role", "alert");
    toastEl.setAttribute("aria-live", "assertive");
    toastEl.setAttribute("aria-atomic", "true");

    toastEl.innerHTML = `
    <div class="d-flex">
        <div class="toast-body">
        ${testo}
        </div>
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






async function caricaRoutes() {
    const btnCorse = document.querySelector('button[onclick="caricaGraficoCorse()"]');
    const btnFermate = document.querySelector('button[onclick="caricaGraficoFermate()"]');

    const res = await fetch("/api/routes");
    const routes = await res.json();

    const tbody = document.getElementById("routes-body");
    tbody.innerHTML = "";

    // Se non ci sono routes, nascondi pulsanti e mostra messaggio
    if (routes.length === 0) {
        btnCorse.style.display = "none";
        btnFermate.style.display = "none";

        const tr = document.createElement("tr");
        tr.innerHTML = `<td colspan="4" class="text-center fst-italic">Nessuna linea disponibile</td>`;
        tbody.appendChild(tr);

        return;
    }

    // Mostra pulsanti dei grafici se ci sono linee
    btnCorse.style.display = "inline-block";
    btnFermate.style.display = "inline-block";

    for (const r of routes) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
        <td>${r.route_id}</td>
        <td>${r.route_short_name}</td>
        <td>${r.route_long_name}</td>
        <td>
        <button class="btn btn-sm btn-action-modify" onclick='modificaLinea(${JSON.stringify(r)})'>Modifica</button>
        <button class="btn btn-sm btn-action-delete" onclick='eliminaLinea("${r.route_id}")'>Elimina</button>
        <a class="btn btn-sm btn-action-details" href="/routes/${r.route_id}/trips">Visualizza corse</a>
        </td>
    `;
    tbody.appendChild(tr);
    }
}




function apriModalNuovaLinea() {
    document.getElementById("modalTitle").textContent = "Nuova Linea";
    document.getElementById("modalMode").value = "create";
    document.getElementById("route_id").value = "";
    document.getElementById("route_id").disabled = false;
    document.getElementById("route_short_name").value = "";
    document.getElementById("route_long_name").value = "";
    routeModal.show();
}





function modificaLinea(route) {
    document.getElementById("modalTitle").textContent = "Modifica Linea";
    document.getElementById("modalMode").value = "edit";
    document.getElementById("originalRouteId").value = route.route_id;
    document.getElementById("route_id").value = route.route_id;
    document.getElementById("route_id").disabled = true;
    document.getElementById("route_short_name").value = route.route_short_name;
    document.getElementById("route_long_name").value = route.route_long_name;
    routeModal.show();
}





async function salvaLinea(event) {
    event.preventDefault();

    const mode = document.getElementById("modalMode").value;
    const route_id = document.getElementById("route_id").value.trim();
    const route_short_name = document.getElementById("route_short_name").value.trim();
    const route_long_name = document.getElementById("route_long_name").value.trim();

    const payload = { route_id, route_short_name, route_long_name };

    try {
    if (mode === "create") {
        const res = await fetch("/api/routes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        });

        if (!res.ok) throw await res.json();
        mostraToast("Linea creata con successo", "success");
    } else if (mode === "edit") {
        const res = await fetch(`/api/routes/${route_id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        });

        if (!res.ok) throw await res.json();
        mostraToast("Linea modificata con successo", "success");
    }

    routeModal.hide();
    await caricaRoutes();
    } catch (err) {
    mostraToast("Errore: " + (err.detail || "Impossibile salvare la linea"), "danger");
    }
}






function eliminaLinea(route_id) {
    routeIdDaEliminare = route_id;
    const deleteModal = new bootstrap.Modal(document.getElementById("confirmDeleteModal"));
    deleteModal.show();
}





async function confermaEliminazione() {
    try {
    const res = await fetch(`/api/routes/${routeIdDaEliminare}`, {
        method: "DELETE",
    });

    if (!res.ok) throw await res.json();
    mostraToast("Linea eliminata", "success");
    await caricaRoutes();
    } catch (err) {
    mostraToast("Errore: " + (err.detail || "Impossibile eliminare la linea"), "danger");
    }

    const deleteModalEl = document.getElementById("confirmDeleteModal");
    const deleteModal = bootstrap.Modal.getInstance(deleteModalEl);
    deleteModal.hide();
    routeIdDaEliminare = null;
}



// Carica le routes al caricamento della pagina
caricaRoutes();






// Contenitore grafico
const contenitoreGrafico = document.getElementById('contenitore-grafico');
let graficoAttivo = null; // variabile globale per sapere quale grafico è attivo

async function caricaGraficoCorse() {
    if (graficoAttivo === "corse") {
    contenitoreGrafico.innerHTML = "";
    graficoAttivo = null;
    return;
    }

    contenitoreGrafico.innerHTML = '<p>Caricamento grafico...</p>';
    try {
    const res = await fetch('/api/routes/num_trips');
    const data = await res.json();

    const labels = data.map(d => d.route_short_name);
    const values = data.map(d => d.num_trips);

    contenitoreGrafico.innerHTML = '';
    Plotly.newPlot(contenitoreGrafico, [{
        x: labels,
        y: values,
        type: 'bar',
        marker: {color: 'rgb(0,198,255)'}
    }], {
        margin: {t:30},
        yaxis: {title: 'Numero corse'},
        xaxis: {title: 'Linea'}
    });
    graficoAttivo = "corse";
    } catch (e) {
    contenitoreGrafico.innerHTML = '<p class="text-danger">Errore nel caricamento del grafico.</p>';
    graficoAttivo = null;
    }
}


async function caricaGraficoFermate() {
    if (graficoAttivo === "fermate") {
    contenitoreGrafico.innerHTML = "";
    graficoAttivo = null;
    return;
    }

    contenitoreGrafico.innerHTML = '<p>Caricamento grafico...</p>';
    try {
    const res = await fetch('/api/routes/num_stops');
    const data = await res.json();

    const labels = data.map(d => d.route_short_name);
    const values = data.map(d => d.num_stops);

    contenitoreGrafico.innerHTML = '';
    Plotly.newPlot(contenitoreGrafico, [{
        x: labels,
        y: values,
        type: 'bar',
        marker: {color: 'rgb(0,122,255)'}
    }], {
        margin: {t:30},
        yaxis: {title: 'Numero fermate'},
        xaxis: {title: 'Linea'}
    });
    graficoAttivo = "fermate";
    } catch (e) {
    contenitoreGrafico.innerHTML = '<p class="text-danger">Errore nel caricamento del grafico.</p>';
    graficoAttivo = null;
    }
}


