"""
Tabla de distancias entre ciudades colombianas (km por carretera).
Evita búsquedas web innecesarias y reduce costos de API.
Fuente: distancias reales aproximadas por carretera.
"""

# Distancias en kilómetros por carretera (no en línea recta)
# Formato: (ciudad_a, ciudad_b): km
DISTANCIAS = {
    # Desde Bogotá
    ("bogota", "tunja"):          147,
    ("bogota", "girardot"):       134,
    ("bogota", "paipa"):          190,
    ("bogota", "duitama"):        210,
    ("bogota", "sogamoso"):       230,
    ("bogota", "yopal"):          390,
    ("bogota", "villavicencio"):  89,
    ("bogota", "ibague"):         204,
    ("bogota", "armenia"):        300,
    ("bogota", "pereira"):        335,
    ("bogota", "manizales"):      310,
    ("bogota", "medellin"):       415,
    ("bogota", "cali"):           462,
    ("bogota", "bucaramanga"):    395,
    ("bogota", "cucuta"):         590,
    ("bogota", "neiva"):          298,
    ("bogota", "pasto"):          795,
    ("bogota", "popayan"):        615,
    ("bogota", "cartagena"):      1050,
    ("bogota", "barranquilla"):   1010,
    ("bogota", "santa marta"):    1060,
    ("bogota", "monteria"):       770,
    ("bogota", "sincelejo"):      855,
    ("bogota", "valledupar"):     930,
    ("bogota", "riohacha"):       1110,
    ("bogota", "leticia"):        None,  # Solo aéreo
    ("bogota", "chia"):           32,
    ("bogota", "zipaquira"):      49,
    ("bogota", "cajica"):         38,
    ("bogota", "soacha"):         18,
    ("bogota", "facatativa"):     42,
    ("bogota", "funza"):          28,
    ("bogota", "mosquera"):       25,
    ("bogota", "madrid"):         35,
    ("bogota", "la calera"):      22,
    ("bogota", "tocancipa"):      55,
    ("bogota", "gachancipa"):     60,
    ("bogota", "guasca"):         55,
    ("bogota", "choachi"):        45,
    ("bogota", "ubate"):          95,
    ("bogota", "ubaté"):          95,
    ("bogota", "chiquinquira"):   155,
    ("bogota", "honda"):          175,
    ("bogota", "melgar"):         110,
    ("bogota", "fusagasuga"):     72,
    ("bogota", "arbelaez"):       95,
    ("bogota", "silvania"):       80,
    ("bogota", "anapoima"):       95,
    ("bogota", "la mesa"):        65,
    ("bogota", "apulo"):          100,
    ("bogota", "tocaima"):        115,
    ("bogota", "villeta"):        98,
    ("bogota", "puerto salgar"):  140,
    ("bogota", "guaduas"):        130,
    ("bogota", "san gil"):        340,
    ("bogota", "barichara"):      360,
    # Desde Medellín
    ("medellin", "cali"):         415,
    ("medellin", "bucaramanga"):  420,
    ("medellin", "pereira"):      176,
    ("medellin", "manizales"):    190,
    ("medellin", "armenia"):      238,
    ("medellin", "cartagena"):    634,
    ("medellin", "barranquilla"): 700,
    ("medellin", "monteria"):     290,
    ("medellin", "quibdo"):       282,
    # Desde Cali
    ("cali", "pasto"):            338,
    ("cali", "popayan"):          138,
    ("cali", "neiva"):            261,
    ("cali", "pereira"):          191,
    ("cali", "buenaventura"):     115,
    ("cali", "buga"):             74,
    ("cali", "palmira"):          30,
    # Desde Bucaramanga
    ("bucaramanga", "cucuta"):    198,
    ("bucaramanga", "barrancabermeja"): 119,
    ("bucaramanga", "san gil"):   98,
}

def normalizar(ciudad: str) -> str:
    """Normaliza el nombre de una ciudad para búsqueda."""
    return (ciudad.lower()
            .strip()
            .replace("á", "a").replace("é", "e")
            .replace("í", "i").replace("ó", "o")
            .replace("ú", "u"))

def buscar_distancia(origen: str, destino: str):
    """
    Busca la distancia entre dos ciudades en la tabla local.
    Retorna km o None si no está en la tabla.
    """
    o = normalizar(origen)
    d = normalizar(destino)

    # Busca en ambas direcciones
    return (DISTANCIAS.get((o, d)) or
            DISTANCIAS.get((d, o)))
