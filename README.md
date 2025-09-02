# Webapp Gestione Dati GTFS - ATP Sassari

## Descrizione
Questa webapp permette di visualizzare e gestire i dati GTFS dell’ATP Sassari.
L’applicazione consente di visualizzare linee, corse e fermate, e di effettuare operazioni CRUD (Create, Read, Update, Delete) su linee e corse.

## Tecnologie utilizzate
- **Backend:** FastAPI 
- **Rendering HTML:** Flask (montato dentro FastAPI per gestire tutti gli endpoint non definiti da FastAPI e per evitare di avviare due server separati)
- **Frontend:** HTML, CSS, Bootstrap, JavaScript
- **Database:** MongoDB


## Modalità d’uso

### Installa le dipendenze Python:
```bash
pip install -r requirements.txt
```

### Avvia l’applicazione:
```bash
uvicorn controller:app
```

### Apri il browser e vai su:
```bash
http://127.0.0.1:8000
```

## Miglioramenti futuri

- **Separazione framework:** Attualmente Flask è montato dentro FastAPI per gestire gli endpoint non definiti da FastAPI e per evitare di dover avviare due server separati. Sarebbe più semplice utilizzare solo FastAPI o solo Flask con API integrate, semplificando la gestione del progetto.

- **CRUD per stop_times:** Aggiungere la possibilità di creare, modificare ed eliminare anche le fermate (stop_times) associando anche il giusto shape alla trip per la visualizzazione delle mappe.
- **Riduzione di codice ridondante:** Alcune parti di codice ripetono logiche simili per linee e corse; si potrebbero astrarre funzioni comuni per ridurre duplicazioni.
- **Gestione errori più dettagliata:** Mostrare messaggi più chiari sugli errori provenienti dal backend.
- **Gestire meglio orari partenza e arrivo nelle trip:** Viene preso l'orario di partenza della prima fermata e l'orario di arrivo dell'ultima fermata. Ma se si aggiunge una stop times manualmente su MongoDB, con una sola fermata crea problemi perchè prende l'orario di partenza e arrivo della stessa e unica fermata, quindi risulta che la trip arriva (cioè finisce la corsa) prima della partenza. (logicamente sbagliato).





