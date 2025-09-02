
import pandas as pd
from pymongo import MongoClient
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional




client = MongoClient("mongodb://localhost:27017/") # Connessione al database MongoDB locale
db = client["gtfs_db"] # Database GTFS
routes_collection = db["routes"] # Collezione delle routes
trips_collection = db["trips"] # Collezione delle trips
stop_times_collection = db["stop_times"] # Collezione delle stop_times 
stops_collection = db["stops"] # Collezione delle stops 
shapes_collection = db["shapes"] # Collezione delle shapes 










# le classi BaseModel (pydantic) servono a definire e validare la struttura dei dati JSON che vengono inviati/ricevuti fra backend e frontend 

class Route(BaseModel): 
    route_id: int
    route_short_name: str
    route_long_name: str


class Trip(BaseModel):
    trip_id: str
    route_id: int
    trip_headsign: str 
    trip_short_name: str
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None


class StopTime(BaseModel):
    trip_id: Optional[str] = None
    arrival_time: str
    departure_time: str
    stop_sequence: int
    stop_name: str












# metodo per eliminare i trips e le stop_times associate a una route che viene eliminata
def elimina_trips_e_stop_times_per_route(route_id: int):
    # Recupera tutti i trip_id della route
    trip_ids = [t["trip_id"] for t in trips_collection.find(
        {"route_id": route_id}, {"trip_id": 1}
    )]

    # Elimina tutte le stop_times collegate a quei trip_id
    stop_times_collection.delete_many({"trip_id": {"$in": trip_ids}})

    # Elimina i trips
    trips_collection.delete_many({"route_id": route_id})






# metodo per creare il database MongoDB se non esiste già, e caricare i dati GTFS 
def carica_gtfs_su_mongo():

    # Controlla se il database 'gtfs_db' esiste già
    if "gtfs_db" in client.list_database_names():
        print("Il database gtfs_db esiste già. Nessun caricamento necessario.")
        return

    # Se il database non esiste verrà creato e i dati GTFS verranno caricati
    print("Database gtfs_db non trovato. Caricamento dei dati GTFS in corso...")

 
    # Carica i file GTFS in MongoDB
    files = {
        "routes": "gtfs_data/routes.txt",
        "trips": "gtfs_data/trips.txt",
        "stops": "gtfs_data/stops.txt",
        "stop_times": "gtfs_data/stop_times.txt",
        "shapes": "gtfs_data/shapes.txt"
    }

    # Crea le collezioni
    for nome_collezione, path_txt in files.items():
        print(f"Caricamento: {nome_collezione}")
        df = pd.read_csv(path_txt)
        db[nome_collezione].insert_many(df.to_dict(orient="records"))  #trasforma il DataFrame in una lista di dizionari in cui ogni dizionario rappresenta un documento(record)
        print(f"{nome_collezione}: {len(df)} record inseriti.")




# metodo per ottenere tutte le routes dal database
def routes_get(): 
    df_routes = pd.DataFrame(list(routes_collection.find({}, {"_id": 0}))) # Recupera tutte le routes senza l'ID usato di default da MongoDB
    if df_routes.empty:
        return []   # <-- lista vuota se non ci sono route

    df_routes = df_routes.sort_values("route_id") # Ordina per route_id
    return df_routes.to_dict(orient="records") # # Converte in lista di dizionari


# metodo per creare una nuova route
def route_create(route):

    route_id = route.route_id 
    route_short_name = route.route_short_name
    route_long_name = route.route_long_name

    # Controlla se esiste già un route_id uguale
    if routes_collection.find_one({"route_id": route_id}):
        raise HTTPException(status_code=400, detail="Route ID già esistente") 

    # Controlla se esiste già un route_short_name uguale
    if routes_collection.find_one({"route_short_name": route_short_name}):
        raise HTTPException(status_code=400, detail="Route short name già esistente")
    
    # Controlla se esiste già un route_short_name uguale
    if routes_collection.find_one({"route_long_name": route_long_name}):
        raise HTTPException(status_code=400, detail="Route long name già esistente")

    doc = route.model_dump() # Converte l'oggetto Pydantic in dizionario
    routes_collection.insert_one(doc) # Inserisce il documento nella collezione

    return {"message": "Route creata", "route_id": route_id} # ritorna un messaggio di conferma e l'ID della route creata


# metodo per aggiornare una route
def route_update(route_id, route):

    route_short_name = route.route_short_name
    route_long_name = route.route_long_name

    # Controlla se esiste una route con quel route_id
    if not routes_collection.find_one({"route_id": route_id}):
        raise HTTPException(status_code=404, detail="Route non trovata")
    
    # Controlla unicità route_short_name su altre route
    if routes_collection.find_one({"route_short_name": route_short_name, "route_id": {"$ne": route_id}}):
        raise HTTPException(status_code=400, detail="Route short name già esistente")
    
    # Controlla unicità route_long_name su altre route
    if routes_collection.find_one({"route_long_name": route_long_name, "route_id": {"$ne": route_id}}):
        raise HTTPException(status_code=400, detail="Route long name già esistente")


    update_data = route.model_dump() # Converte l'oggetto Pydantic in dizionario


    # Esegue aggiornamento nel database
    result = routes_collection.update_one(
        {"route_id": route_id},  # filtro
        {"$set": update_data}    # aggiornamento dei campi
    )

    # Controlla se è stata fatta almeno una modifica
    if result.modified_count == 1:
        return {"message": "Route aggiornata"} # ritorna un messaggio di conferma
    else:
        raise HTTPException(status_code=400, detail="Nessuna modifica effettuata")


# metodo per eliminare una route
def route_delete(route_id):
    result = routes_collection.delete_one({"route_id": route_id}) # Elimina la route con quel route_id

    # Controlla se la route è stata effettivamente eliminata
    if result.deleted_count == 1:
        elimina_trips_e_stop_times_per_route(route_id) # Elimina anche i trips e le stop_times associate a quella route
        return
    else:
        raise HTTPException(status_code=404, detail="Route non trovata")


# metodo per visualizzare il grafico del numero di corse per linea
def grafico_numero_corse_per_linea():
    # Recupera tutte le corse
    trips = list(trips_collection.find({}, {"route_id": 1})) # Recupera solo route_id dalle trips
    df_trips = pd.DataFrame(trips) 

    # Conta le corse per route_id
    if not df_trips.empty:
        counts = df_trips.groupby("route_id").size().reset_index(name="num_trips") # Conta le corse per ogni route_id
    else:
        counts = pd.DataFrame(columns=["route_id", "num_trips"]) # crea un DataFrame vuoto se non ci sono corse

    # Recupera i nomi brevi delle linee
    routes = list(routes_collection.find({}, {"route_id": 1, "route_short_name": 1})) #
    df_routes = pd.DataFrame(routes) 

    # Merge mantenendo tutte le linee
    df_final = df_routes.merge(counts, on="route_id", how="left") # Unisce i conteggi con le routes
    df_final["num_trips"] = df_final["num_trips"].fillna(0).astype(int) # Riempi i NaN con 0 e converte in interi

    # Ordina per route_id 
    df_final = df_final.sort_values("route_id")

    # Converte in lista di dizionari
    result = df_final[["route_id", "route_short_name", "num_trips"]].to_dict(orient="records")
    return result


# metodo per visualizzare il grafico del numero di fermate per linea
def grafico_numero_fermate_per_linea():
    # Recupera tutti i trips
    trips = list(trips_collection.find({}, {"route_id": 1, "trip_id": 1})) # Recupera route_id e trip_id dalle trips
    df_trips = pd.DataFrame(trips)

    # Recupera tutte le stop_times
    stop_times = list(stop_times_collection.find({}, {"trip_id": 1, "stop_id": 1})) # Recupera trip_id e stop_id dalle stop_times
    df_stop_times = pd.DataFrame(stop_times)

    # Merge stop_times con route_id e conta le fermate uniche
    if not df_stop_times.empty and not df_trips.empty: 
        df = df_stop_times.merge(df_trips, on="trip_id") 
        df_counts = df.groupby("route_id")["stop_id"].nunique().reset_index(name="num_stops") # Conta le fermate uniche per ogni route_id
    else:
        df_counts = pd.DataFrame(columns=["route_id", "num_stops"]) # crea un DataFrame vuoto se non ci sono fermate o corse

    # Recupera i nomi brevi delle linee
    routes = list(routes_collection.find({}, {"route_id": 1, "route_short_name": 1})) # Recupera route_id e route_short_name dalle routes
    df_routes = pd.DataFrame(routes)

    # Merge mantenendo tutte le linee
    df_final = df_routes.merge(df_counts, on="route_id", how="left") # Unisce i conteggi con le routes
    df_final["num_stops"] = df_final["num_stops"].fillna(0).astype(int) # Riempi i NaN con 0 e converte in interi

    # Ordina per route_id 
    df_final = df_final.sort_values("route_id")

    # Converte in lista di dizionari
    result = df_final[["route_id", "route_short_name", "num_stops"]].to_dict(orient="records")
    return result






# metodo per ottenere i trips di una specifica route
def trips_get(route_id):
     # Carica i trips del route_id
    df_trips = pd.DataFrame(list(trips_collection.find({"route_id": route_id}))) # Recupera i trips per route_id

    if df_trips.empty:
        return [] # lista vuota se non ci sono trips per quella route_id
    
    # Carica tutte le stop_times relative ai trip
    df_stop_times = pd.DataFrame(list(stop_times_collection.find({"trip_id": {"$in": df_trips['trip_id'].tolist()}}))) 
    
    # Se non ci sono stop_times, ritorna i trips con campi vuoti per orari
    if df_stop_times.empty:
        df_trips['departure_time'] = None
        df_trips['arrival_time'] = None
        return df_trips.to_dict(orient="records")

    # Ordina per trip_id e stop_sequence
    df_stop_times = df_stop_times.sort_values(['trip_id', 'stop_sequence']) 

    # Calcola departure e arrival usando groupby.agg
    df_times = df_stop_times.groupby('trip_id').agg(
        departure_time=('departure_time', 'first'),
        arrival_time=('arrival_time', 'last')
    ).reset_index()


    # Unisci gli orari ai trips
    df_trips = df_trips.merge(df_times, on='trip_id', how='left')
    
    # Ordina per orario di partenza
    df_trips = df_trips.sort_values("departure_time")
    

    # Converti in lista di dizionari
    return df_trips.to_dict(orient="records")


# metodo per creare un nuovo trip di una specifica route
def trip_create(trip):
    trip_id = trip.trip_id
    # Controlla se esiste già un trip_id uguale
    if trips_collection.find_one({"trip_id": trip_id}): 
        raise HTTPException(status_code=400, detail="Trip ID già esistente")
    
    
    doc = {
            "trip_id": trip.trip_id,
            "route_id": trip.route_id,
            "trip_headsign": trip.trip_headsign,
            "trip_short_name": trip.trip_short_name
    }   

    # Inserisce il nuovo trip nel database
    trips_collection.insert_one(doc)

    return {"message": "Corsa creata", "trip_id": trip_id} # ritorna un messaggio di conferma e l'ID del trip creato


# metodo per aggiornare un trip di una specifica route
def trip_update(trip_id: str, trip: Trip):
    if not trips_collection.find_one({"trip_id": trip_id}): # Controlla se esiste un trip con quel trip_id
        raise HTTPException(status_code=404, detail="Corsa non trovata")
    
    update_data = {
        "trip_headsign": trip.trip_headsign,
        "trip_short_name": trip.trip_short_name,
        "route_id": trip.route_id,
    }

    
    result = trips_collection.update_one({"trip_id": trip_id}, {"$set": update_data}) # Esegue l'aggiornamento del trip nel database
    
    # Controlla se è stata fatta almeno una modifica
    if result.modified_count == 1:
        return {"message": "Corsa aggiornata"} # ritorna un messaggio di conferma
    else:
        raise HTTPException(status_code=400, detail="Nessuna modifica effettuata")


# metodo per eliminare un trip di una specifica route
def trip_delete(trip_id: str):
    result = trips_collection.delete_one({"trip_id": trip_id}) # Elimina il trip con quel trip_id

    # Controlla se il trip è stato effettivamente eliminato
    if result.deleted_count == 1:
        stop_times_collection.delete_many({"trip_id": trip_id})
        return
    else:
        raise HTTPException(status_code=404, detail="Corsa non trovata")


# metodo per calcolare la durata media delle trips per una specifica route
def get_durata_media_trips(route_id: int):
    trips = list(trips_collection.find({"route_id": route_id}, {"trip_id": 1, "_id": 0})) # Recupera tutti i trip_id della route

    # Se non ci sono trips, ritorna durata media 0
    if not trips:
        return {"durata_media_minuti": 0}

    
    trip_ids = [t["trip_id"] for t in trips] # Recupera la lista dei trip_id
    df_stop_times = pd.DataFrame(list(stop_times_collection.find({"trip_id": {"$in": trip_ids}}))) # Recupera tutte le stop_times dei trip_id
    if df_stop_times.empty:
        return {"durata_media_minuti": 0} # Se non ci sono stop_times, ritorna durata media 0

    # Ordina e aggrega
    df_stop_times = df_stop_times.sort_values(["trip_id", "stop_sequence"])
    df_times = df_stop_times.groupby('trip_id').agg(
        departure_time=('departure_time', 'first'),
        arrival_time=('arrival_time', 'last')
    ).reset_index()

    # Calcola la durata in minuti
    df_times['durata_minuti'] = (
        pd.to_datetime(df_times['arrival_time']) - pd.to_datetime(df_times['departure_time'])
    ).dt.total_seconds() / 60

    # Filtra durate positive
    valid = df_times[df_times['durata_minuti'] > 0]['durata_minuti']

    media = int(valid.mean()) if not valid.empty else 0 # Calcola la durata media in minuti, se non ci sono durate valide ritorna 0

    return {"durata_media_minuti": media} # ritorna un dizionario con la durata media in minuti


# metodo per visualizzare il grafico delle corse per ora per una specifica route
def grafico_corse_per_ora(route_id: int):
    # Recupera tutti i trip della route
    trips = list(trips_collection.find({"route_id": route_id}, {"trip_id": 1})) # Recupera i trip_id della route
    if not trips:
        return [] # lista vuota se non ci sono trips per quella route_id

    trip_ids = [t["trip_id"] for t in trips] # Recupera la lista dei trip_id

    
    stop_times = list(stop_times_collection.find({"trip_id": {"$in": trip_ids}})) # Recupera tutte le stop_times dei trip_id
    df_stop_times = pd.DataFrame(stop_times) 
    if df_stop_times.empty:
        return [] # lista vuota se non ci sono stop_times per quei trip_id

    df_first_stop = df_stop_times.sort_values("stop_sequence").groupby("trip_id").first().reset_index() # Recupera la prima fermata per ogni trip_id
    
    # Estrai l'ora
    df_first_stop["hour"] = pd.to_datetime(df_first_stop["departure_time"], format="%H:%M:%S").dt.hour

    # Conta le corse per ogni ora
    counts = df_first_stop.groupby("hour").size().reindex(range(24), fill_value=0).reset_index(name="num_trips")

    # Converte in lista di dizionari
    return counts.to_dict(orient="records")






# metodo per ottenere tutte le stop_times di una specifica trip
def stop_times_get(trip_id: str):
    # Recupera stop_times e ordina subito per stop_sequence
    df_stop_times = pd.DataFrame(list(stop_times_collection.find({"trip_id": trip_id}))) # Recupera tutte le stop_times per il trip_id specificato
    
    if df_stop_times.empty:
        return [] # lista vuota se non ci sono stop_times per quel trip_id
    
    stop_ids = df_stop_times['stop_id'].tolist()

    # Recupera fermate
    df_stops = pd.DataFrame(list(stops_collection.find({"stop_id": {"$in": stop_ids}})))

    # Merge per avere stop_name
    df = df_stop_times.merge(df_stops[['stop_id', 'stop_name']], on='stop_id')

    # Ordina e seleziona colonne necessarie
    df = df.sort_values("stop_sequence")[['stop_sequence', 'arrival_time', 'departure_time', 'stop_name']]

    return df.to_dict(orient="records")


# metodo per ottenere il numero di fermate per una specifica trip
def get_numero_fermate(trip_id: str):
    stop_times_cursor = stop_times_collection.find({"trip_id": trip_id}) # Recupera tutte le stop_times per il trip_id specificato
    stop_times_list = list(stop_times_cursor) # Converte il cursore in lista

    # Se non ci sono stop_times, ritorna errore 404
    if not stop_times_list:
        raise HTTPException(status_code=404, detail="Trip non trovato")
    return {"trip_id": trip_id, "num_stops": len(stop_times_list)} # ritorna un dizionario con il trip_id e il numero di fermate


# metodo per ottenere le coordinate delle fermate e del percorso di una specifica trip
def get_mappa_percorso(trip_id: str):
    shape_doc = db.trips.find_one({"trip_id": trip_id}, {"shape_id": 1}) # Recupera il shape_id della trip specificata

    # Se non esiste, ritorna errore 404
    if not shape_doc:
        raise HTTPException(status_code=404, detail="Trip non trovato")

    shape_id = shape_doc["shape_id"] # Recupera lo shape_id

    # Recupera le coordinate del percorso
    cursor = db.shapes.find(
        {"shape_id": shape_id},
        {"_id": 0, "shape_pt_lat": 1, "shape_pt_lon": 1, "shape_pt_sequence": 1}
    )
    df = pd.DataFrame(list(cursor))

    # Se non ci sono coordinate, ritorna errore 404
    if df.empty:
        raise HTTPException(status_code=404, detail="Shape non trovata")

    
    df = df.sort_values(by="shape_pt_sequence") # Ordina per sequence
    coordinates = df[["shape_pt_lat", "shape_pt_lon"]].values.tolist() # Estrae le coordinate in una lista di liste




    # Recupera stop_times della trip
    df_stop_times = pd.DataFrame(list(stop_times_collection.find({"trip_id": trip_id})))
    stop_coords = []
    if not df_stop_times.empty:
        stop_ids = df_stop_times['stop_id'].tolist()
        df_stops = pd.DataFrame(list(stops_collection.find(
            {"stop_id": {"$in": stop_ids}},
            {"_id": 0, "stop_id": 1, "stop_name": 1, "stop_lat": 1, "stop_lon": 1}
        )))
        df_merged = df_stop_times.merge(df_stops, on="stop_id")
        df_merged = df_merged.sort_values("stop_sequence")
        stop_coords = df_merged[["stop_lat", "stop_lon", "stop_name"]].to_dict(orient="records")


    return {
        "trip_id": trip_id,
        "shape_coordinates": coordinates,  # ex coordinates
        "stops": stop_coords
    }

























