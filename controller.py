
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.wsgi import WSGIMiddleware
from flask import Flask, render_template
from model import *
from typing import List







# Carica i dati GTFS su mongo se ancora non esiste il database
carica_gtfs_su_mongo()



# Flask app 
flask_app = Flask(__name__, template_folder="templates") 


# renderizza alla pagina home.html
@flask_app.route("/")
def home():
    return render_template("home.html")


# renderizza alla pagina routes.html
@flask_app.route("/routes")
def routes_page():
    return render_template("routes.html")


# renderizza alla pagina trips.html per una specifica route
@flask_app.route("/routes/<route_id>/trips")
def trips_page(route_id: int):
    return render_template("trips.html", route_id=route_id)


# renderizza alla pagina stop_times.html per una specifica trip
@flask_app.route("/trip/<trip_id>")
def trip_details_page(trip_id: str):
    return render_template("stop_times.html", trip_id=trip_id)









# FastAPI app 
app = FastAPI() 





# CORS Middleware per fetch JS
app.add_middleware( 
    CORSMiddleware, 
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"], # Permetti le origini del frontend
    allow_methods=["GET", "POST", "PUT", "DELETE"], # Permetti i metodi HTTP
)










# API fastapi per visualizzare le routes
@app.get("/api/routes", response_model=List[Route])    # status_code=200 di default
def get_routes():
    return routes_get()  # Recupera tutte le routes dal database



# API fastapi per creare una routes
@app.post("/api/routes", status_code=201) # status_code=201 per indicare che la risorsa è stata creata
def create_route(route: Route):
    return route_create(route) # Crea una nuova route nel database



# API fastapi per modificare una routes
@app.put("/api/routes/{route_id}")   # status_code=200 di default
def update_route(route_id: int, route: Route):
    return route_update(route_id, route) # Modifica una route esistente nel database
    



# API fastapi per eliminare una routes
@app.delete("/api/routes/{route_id}", status_code=204) # status_code=204 per indicare che la risorsa è stata eliminata
def delete_route(route_id: int):
    return route_delete(route_id) # Elimina una route dal database



# API fastapi per visualizzare grafico numero corse per linea
@app.get("/api/routes/num_trips") # status_code=200 di default
async def numero_corse_per_linea():
    return grafico_numero_corse_per_linea() # Visualizza il grafico del numero di corse per linea



# API fastapi per visualizzare grafico numero fermate per linea
@app.get("/api/routes/num_stops") # status_code=200 di default
async def numero_fermate_per_linea():
    return grafico_numero_fermate_per_linea() # Visualizza il grafico del numero di fermate per linea












# API fastapi per visualizzare le trips
@app.get("/api/trips", response_model=List[Trip]) # status_code=200 di default
def get_trips(route_id: int):
    return trips_get(route_id) # Recupera tutte le trips per una specifica route dal database




# API fastapi per creare una trips
@app.post("/api/trips", status_code=201) # status_code=201 per indicare che la risorsa è stata creata
def create_trip(trip: Trip):
    return trip_create(trip) # Crea una nuova trip nel database




# API fastapi per modificare una trips
@app.put("/api/trips/{trip_id}")     # status_code=200 di default
def update_trip(trip_id: str, trip: Trip):
    return trip_update(trip_id, trip) # Modifica una trip esistente nel database




# API fastapi per eliminare una trip
@app.delete("/api/trips/{trip_id}", status_code=204) # status_code=204 per indicare che la risorsa è stata eliminata
def delete_trip(trip_id: str):
    return trip_delete(trip_id) # Elimina una trip dal database




# API fastapi per visualizzare la durata media delle trips per una route
@app.get("/api/trips/{route_id}/durata_media", response_model=dict[str, int]) # status_code=200 di default
def durata_media_trips(route_id: int):
    return get_durata_media_trips(route_id) # Recupera la durata media delle trips per una specifica route dal database



# API fastapi per visualizzare il grafico delle corse per ora
@app.get("/api/trips/{route_id}/corse_per_ora") # status_code=200 di default
def corse_per_ora(route_id: int):
    return grafico_corse_per_ora(route_id) # Visualizza il grafico delle corse per ora per una specifica route










# API fastapi per visualizzare le stop_times
@app.get("/api/stop_times", response_model=List[StopTime]) # status_code=200 di default
def get_stop_times(trip_id: str):
    return stop_times_get(trip_id) # Recupera tutte le stop_times per una specifica trip dal database



# API fastapi per visualizzare il numero di fermate per una trip
@app.get("/api/stop_times/{trip_id}/num_stops") # status_code=200 di default
async def numero_fermate(trip_id: str):
    return get_numero_fermate(trip_id) # Recupera il numero di fermate per una specifica trip dal database



#API fastapi per prendere le coordinate delle fermate e del percorso di una trip
@app.get("/api/stop_times/{trip_id}/shape") # status_code=200 di default
async def mappa_percorso(trip_id: str):
    return get_mappa_percorso(trip_id) # Recupera le coordinate delle fermate e del percorso di una specifica trip dal database









# MOUNT: Flask dentro FastAPI
app.mount("/", WSGIMiddleware(flask_app))

