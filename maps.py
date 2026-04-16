"""
Módulo Google Maps — Destinos Express
Calcula km reales y detecta zona (urbana / metropolitana / intermunicipal).
"""

import os
import logging
import googlemaps
from dotenv import load_dotenv

load_dotenv()

_client = None

def _get_client():
    global _client
    if _client is None:
        key = os.environ.get("GOOGLE_MAPS_KEY")
        if not key:
            raise RuntimeError("GOOGLE_MAPS_KEY no está configurada en .env")
        _client = googlemaps.Client(key=key)
    return _client


# ─── MUNICIPIOS METROPOLITANOS (fuera de Bogotá pero área cercana) ────────────
MUNICIPIOS_METROPOLITANOS = {
    "chía", "chia",
    "cajicá", "cajica",
    "zipaquirá", "zipaquira",
    "sopó", "sopo",
    "tocancipá", "tocancipa",
    "gachancipá", "gachancipa",
    "mosquera",
    "funza",
    "madrid",
    "facatativá", "facatativa",
    "el rosal",
    "bojacá", "bojaca",
    "sibaté", "sibate",
    "soacha",
    "la calera",
    "guasca",
    "tabio",
    "tenjo",
    "cota",
    "choconta", "chocontá",
    "suesca",
    "nemocon", "nemocón",
}


def _extraer_ciudad(origen: str) -> str:
    """
    Extrae la ciudad principal del texto de origen para usarla como contexto
    al geocodificar el destino.
    Cuando no se detecta otra ciudad, retorna "Bogotá" como default porque
    Destinos Express opera desde Bogotá.
    """
    origen_lower = origen.lower()
    ciudades = [
        ("medellin", "Medellín"), ("medellín", "Medellín"),
        ("cali", "Cali"),
        ("barranquilla", "Barranquilla"),
        ("cartagena", "Cartagena"),
        ("bucaramanga", "Bucaramanga"),
        ("pereira", "Pereira"),
        ("manizales", "Manizales"),
        ("ibague", "Ibagué"), ("ibagué", "Ibagué"),
        ("villavicencio", "Villavicencio"),
        ("tunja", "Tunja"),
    ]
    for clave, nombre in ciudades:
        if clave in origen_lower:
            return nombre
    # Por defecto Bogotá — todos los servicios parten de la capital
    return "Bogotá"


def detectar_zona(municipio: str, km: float = 0) -> str:
    """
    Recibe el nombre del municipio y los km reales y devuelve la zona:
    'urbana' | 'metropolitana' | 'intermunicipal'

    Los km sirven como corrección cuando la geocodificación devuelve
    un municipio incorrecto (ej: La Mesa detectada como Bogotá a 73 km).
    """
    m = municipio.lower().strip()

    # Detección por nombre de municipio
    if m in ("bogotá", "bogota", "bogotá d.c.", "bogota d.c."):
        zona = "urbana"
    elif m in MUNICIPIOS_METROPOLITANOS:
        zona = "metropolitana"
    else:
        zona = "intermunicipal"

    # Corrección por distancia: si la geocodificación dijo "urbana"
    # pero la distancia real es muy larga, probablemente es un error de geocoding
    if zona == "urbana" and km > 45:
        zona = "metropolitana"
    if zona in ("urbana", "metropolitana") and km > 120:
        zona = "intermunicipal"

    return zona


def consultar_ruta(origen: str, destino: str) -> dict:
    """
    Obtiene km reales, tiempo, municipio, zona y vía principal entre origen y destino.

    Intenta Directions API primero (devuelve `via_resumen` con el nombre de la vía,
    necesario para detectar el corredor de salida de Bogotá). Si falla, cae a
    Distance Matrix (mismo resultado pero sin `via_resumen`).

    Retorna dict con los resultados, o None si ambas consultas fallan.
    """
    try:
        gmaps = _get_client()

        ciudad_origen = _extraer_ciudad(origen)
        destino_con_ctx = f"{destino}, {ciudad_origen}, Colombia" if ciudad_origen else f"{destino}, Colombia"

        km = None
        duracion_min = None
        via_resumen = ""

        # ── Intento 1: Directions API (da summary / nombre de vía) ──────────
        try:
            rutas = gmaps.directions(
                origin=f"{origen}, Colombia",
                destination=destino_con_ctx,
                mode="driving",
                language="es",
                region="co",
            )
            if rutas and rutas[0].get("legs"):
                leg = rutas[0]["legs"][0]
                km = round(leg["distance"]["value"] / 1000, 1)
                duracion_min = round(leg["duration"]["value"] / 60)
                via_resumen = rutas[0].get("summary", "")
                logging.info(f"[Maps/Directions] {origen} → {destino}: {km} km · vía: '{via_resumen}'")
        except Exception as e_dir:
            logging.warning(f"[Maps] Directions API falló ({type(e_dir).__name__}), usando Distance Matrix")

        # ── Intento 2: Distance Matrix (fallback sin via_resumen) ────────────
        if km is None:
            matriz = gmaps.distance_matrix(
                origins=[f"{origen}, Colombia"],
                destinations=[destino_con_ctx],
                mode="driving",
                language="es",
                units="metric",
                region="co",
            )
            elemento = matriz["rows"][0]["elements"][0]
            if elemento["status"] != "OK":
                logging.warning(
                    f"[Maps] Distance Matrix status: {elemento['status']} | {origen} → {destino_con_ctx}"
                )
                return None
            km = round(elemento["distance"]["value"] / 1000, 1)
            duracion_min = round(elemento["duration"]["value"] / 60)
            logging.info(f"[Maps/DistMatrix] {origen} → {destino}: {km} km")

        # ── Municipio del destino (geocoding) ────────────────────────────────
        geo = gmaps.geocode(destino_con_ctx, language="es", region="co")
        municipio = "desconocido"
        es_rural = False

        if geo:
            componentes = geo[0].get("address_components", [])
            for comp in componentes:
                tipos = comp.get("types", [])
                if "locality" in tipos or "administrative_area_level_2" in tipos:
                    municipio = comp["long_name"]
                    break

            direccion_completa = geo[0].get("formatted_address", "").lower()
            if any(p in direccion_completa for p in ["vereda", "corregimiento", "inspección", "finca"]):
                es_rural = True

        zona = detectar_zona(municipio, km)

        return {
            "km": km,
            "duracion_min": duracion_min,
            "municipio_destino": municipio,
            "zona": zona,
            "es_rural": es_rural,
            "via_resumen": via_resumen,   # nombre de vía (ej: "Autopista Norte")
        }

    except Exception as e:
        logging.error(f"[Maps] Error consultando ruta {origen} → {destino}: {type(e).__name__}: {e}")
        return None
