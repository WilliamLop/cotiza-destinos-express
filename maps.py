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
    """
    origen_lower = origen.lower()
    ciudades = [
        ("bogot", "Bogotá"),
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
    return ""


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
    Llama a Distance Matrix + Geocoding para obtener:
    - km reales entre origen y destino
    - municipio del destino
    - zona (urbana / metropolitana / intermunicipal)
    - es_rural (heurística básica por tipo de vía)

    Retorna dict con los resultados, o None si la consulta falla.
    """
    try:
        gmaps = _get_client()

        # Incluir ciudad de origen como contexto para ambas consultas
        ciudad_origen = _extraer_ciudad(origen)
        destino_con_ctx = f"{destino}, {ciudad_origen}, Colombia" if ciudad_origen else f"{destino}, Colombia"

        # ── Distancia real ──────────────────────────────────────────────────
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
            logging.warning(f"[Maps] Distance Matrix status: {elemento['status']} | {origen} → {destino_con_ctx}")
            return None

        km = round(elemento["distance"]["value"] / 1000, 1)
        duracion_min = round(elemento["duration"]["value"] / 60)

        # ── Municipio del destino ───────────────────────────────────────────
        query_destino = destino_con_ctx
        geo = gmaps.geocode(query_destino, language="es", region="co")
        municipio = "desconocido"
        es_rural = False

        if geo:
            componentes = geo[0].get("address_components", [])
            for comp in componentes:
                tipos = comp.get("types", [])
                if "locality" in tipos or "administrative_area_level_2" in tipos:
                    municipio = comp["long_name"]
                    break

            # Heurística rural: si el resultado contiene "vereda", "corregimiento"
            # o el tipo de lugar es "route" fuera de zona urbana
            direccion_completa = geo[0].get("formatted_address", "").lower()
            if any(p in direccion_completa for p in ["vereda", "corregimiento", "inspección", "finca"]):
                es_rural = True

        zona = detectar_zona(municipio, km)

        resultado = {
            "km": km,
            "duracion_min": duracion_min,
            "municipio_destino": municipio,
            "zona": zona,
            "es_rural": es_rural,
        }

        logging.info(f"[Maps] {origen} → {destino}: {km} km, {municipio} ({zona})")
        return resultado

    except Exception as e:
        logging.error(f"[Maps] Error consultando ruta {origen} → {destino}: {type(e).__name__}: {e}")
        return None
