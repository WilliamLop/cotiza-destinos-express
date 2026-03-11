"""
Estructura tarifaria oficial - Destinos Express
Transporte especial de pasajeros
"""

# 1. TARIFAS BASE — valores reales (camioneta). Van y bus se derivan con % después.
TARIFAS = {
    "camioneta": {
        "nombre": "Camioneta Ejecutiva / SUV",
        "capacidad": "1 – 4 pasajeros",
        "tarifa_minima_urbana": 32_000,
        "km_ciudad_diurno": 1_800,
        "km_ciudad_nocturno": 2_200,
        "km_intermunicipal": 2_300,
        "hora": 52_000,
        "espera_30min": 25_000,
        "incremento_aeropuerto": 8_000,
    },
    # van_ejecutiva, van_grande, bus → se derivan después con %
}

# 2. MODELO COMERCIAL — 3 niveles de precio
MODELO_COMERCIAL = {
    "corporativo": 0.08,   # Particular + 8%
    "urgente": 0.15,       # Particular + 15%
}

# 3. RECARGOS operativos
RECARGOS = {
    "nocturno": 0.10,     # 10% entre 10pm - 5am
    "festivo": 0.10,      # 10% en festivos
    "rural_min": 0.10,    # 10% mínimo en zonas rurales
    "rural_max": 0.20,    # 20% máximo en zonas rurales
}

# 4. AEROPUERTO BOGOTÁ — por zona, precio particular
AEROPUERTO_BOGOTA = {
    "camioneta": {
        "Primera de Mayo": 65_000,
        "Ciudad Bolívar": 78_000,
        "San Cristóbal Sur": 75_000,
        "Usme": 86_000,
        "Soacha Centro": 86_000,
        "San Mateo": 88_000,
        "Compartir": 98_000,
        "Centro hasta Cll 80": 60_000,
        "Cra 1": 65_000,
        "Calle 90": 70_000,
        "Calle 127": 75_000,
        "Cll 153": 82_000,
        "Cll 170": 90_000,
        "Cll 200": 95_000,
        "Guaymaral": 105_000,
    }
}

# 5. CONDUCTOR BILINGÜE — pendiente de confirmar con gerente
CONDUCTOR_BILINGUE = {
    "anticipacion_horas": 72,
    "costo_por_hora": 95_000,
    "traslado_aeropuerto_adicional": 130_000,
}

# 6. RUTAS (solo ida) — precio particular
RUTAS = {
    "camioneta": {
        # Sabana Norte
        "chia": 143_000,
        "cajica": 165_000,
        "zipaquira": 195_000,
        "sopo": 210_000,
        "tocancipa": 225_000,
        # Sabana Occidente
        "mosquera": 105_000,
        "funza": 98_000,
        "madrid": 115_000,
        "facatativa": 199_000,
        "el_rosal": 135_000,
        # Sabana Sur
        "sibate": 175_000,
        "fusagasuga": 320_000,
        "silvania": 275_000,
        # Corredor Tolima
        "girardot": 464_000,
        "melgar": 420_000,
        "ibague": 520_000,
        "espinal": 470_000,
        # Meta
        "villavicencio": 480_000,
        "restrepo": 500_000,
        "cumaral": 530_000,
        # Boyacá
        "tunja": 460_000,
        "paipa": 510_000,
        "duitama": 540_000,
        "sogamoso": 590_000,
        "villa_de_leyva": 520_000,
        "chiquinquira": 490_000,
        # Ciudades principales
        "medellin": 1_100_000,
        "cali": 1_450_000,
        "pereira": 1_100_000,
        "armenia": 900_000,
        "manizales": 1_050_000,
    }
}

# 7. RUTAS IDA Y VUELTA MISMO DÍA — precio particular
RUTAS_IDA_VUELTA = {
    "camioneta": {
        "chia": 380_000,
        "cajica": 420_000,
        "zipaquira": 460_000,
        "sopo": 440_000,
        "la_calera": 440_000,
        "funza": 380_000,
        "mosquera": 400_000,
        "madrid": 400_000,
        "facatativa": 480_000,
        "el_rosal": 380_000,
        "soacha_centro": 390_000,
        "soacha_san_mateo": 410_000,
        "soacha_compartir": 420_000,
        "sibate": 480_000,
        "silvania": 495_000,
        "fusagasuga": 540_000,
        "melgar": 560_000,
        "girardot": 590_000,
        "espinal": 630_000,
        "ibague": 680_000,
        "villavicencio": 680_000,
        "restrepo": 710_000,
        "cumaral": 750_000,
        "chiquinquira": 620_000,
        "tunja": 680_000,
        "villa_de_leyva": 740_000,
        "paipa": 770_000,
        "duitama": 800_000,
        "sogamoso": 880_000,
        "ubate": 520_000,
        "simijaca": 560_000,
        "choachi": 630_000,
        "fomeque": 680_000,
        "ubaque": 620_000,
        "sasaima": 640_000,
        "la_vega": 650_000,
        "villeta": 680_000,
    }
}

# 8. SERVICIOS MULTI-DÍA
SERVICIOS_MULTI_DIA = {
    "alimentacion_conductor": 17_600,   # por comida
    "hospedaje_conductor": 49_500,      # por noche
    "disponibilidad_vehiculo": 200_000, # por día
    "alimentos_por_dia": {1: 2, "completo": 3, "ultimo": 2},
}

# 9. VARIABLES OPERATIVAS (para destinos no cargados en tarifario)
VARIABLES_OPERATIVAS = {
    "combustible_km": 650,
    "desgaste_km": 350,
    "conductor_porcentaje": 0.26,
    "logistica_operativa": 0.06,
}

# 10. FISCAL
FISCAL = {
    "iva": 0,           # exento
    "retefuente": 0.035,
    "clientes_con_retencion": [
        "ANDI", "Banco Popular", "Skechers", "Merz", "HDI Seguros"
    ],
}

# Ciudades/municipios que se consideran zona metropolitana de Bogotá
ZONA_METROPOLITANA_BOGOTA = [
    "chia", "soacha", "funza", "mosquera", "madrid", "facatativa",
    "zipaquira", "cajica", "tocancipa", "gachancipa", "sopó", "sopo",
    "la calera", "sibate", "bojaca"
]


def formatear_precio(valor):
    """Convierte 380000 a '$380.000'"""
    return f"${valor:,.0f}".replace(",", ".")


def precio_corporativo(particular):
    """Precio particular + 8% para clientes corporativos."""
    return round(particular * 1.08)


def precio_urgente(particular):
    """Precio particular + 15% para servicios urgentes."""
    return round(particular * 1.15)


def precio_con_nivel(particular, nivel="particular"):
    """Devuelve el precio según el nivel comercial: particular, corporativo o urgente."""
    if nivel == "corporativo":
        return precio_corporativo(particular)
    if nivel == "urgente":
        return precio_urgente(particular)
    return particular
