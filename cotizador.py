"""
Módulo de cálculo de precios — Destinos Express
Python calcula exactamente; Claude solo extrae parámetros.
"""

from dataclasses import dataclass
from typing import Optional
from tarifas import (
    TARIFAS, RECARGOS, AEROPUERTO_BOGOTA, AEROPUERTO_EL_DORADO_HOTELES,
    RUTAS, RUTAS_IDA_VUELTA,
    SERVICIOS_MULTI_DIA, VARIABLES_OPERATIVAS, formatear_precio, precio_con_nivel,
)


@dataclass
class ResultadoCotizacion:
    precio_particular: int
    precio_final: int
    nivel: str                    # "particular" | "corporativo" | "ultima_hora"
    desglose: list                # [{"concepto": str, "valor": str}] — listo para PDF
    recargos_aplicados: list      # ["Recargo nocturno +10%", ...]
    notas: Optional[str]
    tipo_servicio: str            # para trazabilidad en logs


# ─── UTILIDADES ────────────────────────────────────────────────────────────────

def normalizar_destino(texto: str) -> str:
    """'Villa de Leyva' → 'villa_de_leyva', 'Chía' → 'chia'"""
    return (
        texto.lower().strip()
        .replace("á", "a").replace("é", "e").replace("í", "i")
        .replace("ó", "o").replace("ú", "u").replace("ñ", "n")
        .replace(" ", "_").replace("-", "_")
    )


def buscar_clave_destino(destino_raw: str, tabla: dict) -> Optional[str]:
    """Busca la clave del destino en una tabla RUTAS. Exacto primero, luego substring."""
    clave = normalizar_destino(destino_raw)
    if clave in tabla:
        return clave
    for k in tabla:
        if clave in k or k in clave:
            return k
    return None


def _aplicar_recargos(precio_base: int, nocturno: bool, festivo: bool, rural: bool):
    """
    Aplica recargos acumulativos sobre el precio base.
    Retorna (precio_final, [(descripcion, monto), ...])
    """
    precio = precio_base
    recargos = []

    if nocturno:
        nuevo = round(precio * (1 + RECARGOS["nocturno"]))
        recargos.append(("Recargo nocturno +10%", nuevo - precio))
        precio = nuevo

    if festivo:
        nuevo = round(precio * (1 + RECARGOS["festivo"]))
        recargos.append(("Recargo festivo +10%", nuevo - precio))
        precio = nuevo

    if rural:
        pct_rural = (RECARGOS["rural_min"] + RECARGOS["rural_max"]) / 2  # 15%
        nuevo = round(precio * (1 + pct_rural))
        recargos.append(("Recargo zona rural +15%", nuevo - precio))
        precio = nuevo

    return precio, recargos


def _construir_resultado(
    precio_base_particular: int,
    nivel: str,
    nocturno: bool,
    festivo: bool,
    rural: bool,
    tipo_servicio: str,
    concepto_base: str,
    notas: str = None,
) -> ResultadoCotizacion:
    """Factory compartida por todas las funciones de cálculo."""
    precio_nivel = precio_con_nivel(precio_base_particular, nivel)
    precio_final, recargos_con_monto = _aplicar_recargos(precio_nivel, nocturno, festivo, rural)

    desglose = [{"concepto": concepto_base, "valor": formatear_precio(precio_base_particular)}]

    if nivel != "particular":
        pct = 8 if nivel == "corporativo" else 15
        diferencia = precio_nivel - precio_base_particular
        desglose.append({
            "concepto": f"Tarifa {nivel} +{pct}%",
            "valor": formatear_precio(diferencia),
        })

    for descripcion, monto in recargos_con_monto:
        desglose.append({"concepto": descripcion, "valor": formatear_precio(monto)})

    desglose.append({"concepto": "Total", "valor": formatear_precio(precio_final)})

    return ResultadoCotizacion(
        precio_particular=precio_base_particular,
        precio_final=precio_final,
        nivel=nivel,
        desglose=desglose,
        recargos_aplicados=[d for d, _ in recargos_con_monto],
        notas=notas,
        tipo_servicio=tipo_servicio,
    )


# ─── CALCULADORAS POR TIPO DE SERVICIO ────────────────────────────────────────

def calcular_ruta_sencilla(destino: str, vehiculo: str, nivel: str,
                            nocturno: bool, festivo: bool, rural: bool) -> Optional[ResultadoCotizacion]:
    rutas_vehiculo = RUTAS.get(vehiculo, {})
    clave = buscar_clave_destino(destino, rutas_vehiculo)
    if clave is None:
        return None
    precio_base = rutas_vehiculo[clave]
    return _construir_resultado(
        precio_base, nivel, nocturno, festivo, rural,
        "ruta_sencilla", f"Traslado a {clave.replace('_', ' ').title()} (solo ida)",
    )


def calcular_ruta_ida_vuelta(destino: str, vehiculo: str, nivel: str,
                              nocturno: bool, festivo: bool, rural: bool) -> Optional[ResultadoCotizacion]:
    rutas_vehiculo = RUTAS_IDA_VUELTA.get(vehiculo, {})
    clave = buscar_clave_destino(destino, rutas_vehiculo)
    if clave is None:
        return None
    precio_base = rutas_vehiculo[clave]
    return _construir_resultado(
        precio_base, nivel, nocturno, festivo, rural,
        "ida_vuelta", f"Ida y vuelta mismo día a {clave.replace('_', ' ').title()}",
    )


def _calcular_aeropuerto_hotel(zona_encontrada, datos_zona, nivel, nocturno, festivo):
    """Usa precios fijos del tarifario — nocturno y corporativo ya incluidos en tabla."""
    prefijo = "nocturno" if nocturno else "diurno"
    particular = datos_zona[f"{prefijo}_particular"]

    if nivel == "corporativo":
        precio_base = datos_zona[f"{prefijo}_corporativo"]
        desglose = [{"concepto": f"Traslado aeropuerto — {zona_encontrada} ({prefijo}, corporativo)", "valor": formatear_precio(precio_base)}]
    elif nivel == "ultima_hora":
        precio_base = round(particular * 1.15)
        desglose = [
            {"concepto": f"Traslado aeropuerto — {zona_encontrada} ({prefijo})", "valor": formatear_precio(particular)},
            {"concepto": "Recargo última hora +15%", "valor": formatear_precio(precio_base - particular)},
        ]
    else:
        precio_base = particular
        desglose = [{"concepto": f"Traslado aeropuerto — {zona_encontrada} ({prefijo})", "valor": formatear_precio(precio_base)}]

    recargos_aplicados = []
    if festivo:
        nuevo = round(precio_base * 1.10)
        desglose.append({"concepto": "Recargo festivo +10%", "valor": formatear_precio(nuevo - precio_base)})
        recargos_aplicados.append("Recargo festivo +10%")
        precio_base = nuevo

    desglose.append({"concepto": "Total", "valor": formatear_precio(precio_base)})
    return ResultadoCotizacion(
        precio_particular=particular,
        precio_final=precio_base,
        nivel=nivel,
        desglose=desglose,
        recargos_aplicados=recargos_aplicados,
        notas=None,
        tipo_servicio="aeropuerto",
    )


def calcular_aeropuerto(zona: str, vehiculo: str, nivel: str,
                         nocturno: bool, festivo: bool) -> Optional[ResultadoCotizacion]:
    zona_norm = normalizar_destino(zona)

    # 1. Buscar en tabla de hoteles (precios fijos por horario y nivel)
    hoteles_vehiculo = AEROPUERTO_EL_DORADO_HOTELES.get(vehiculo, {})
    for z, datos in hoteles_vehiculo.items():
        if normalizar_destino(z) == zona_norm or zona_norm in normalizar_destino(z):
            return _calcular_aeropuerto_hotel(z, datos, nivel, nocturno, festivo)

    # 2. Fallback: tabla antigua con precio base + fórmulas
    zonas_vehiculo = AEROPUERTO_BOGOTA.get(vehiculo, {})
    zona_encontrada = None
    for z in zonas_vehiculo:
        if normalizar_destino(z) == zona_norm or zona_norm in normalizar_destino(z):
            zona_encontrada = z
            break
    if zona_encontrada is None:
        return None
    precio_base = zonas_vehiculo[zona_encontrada]
    return _construir_resultado(
        precio_base, nivel, nocturno, festivo, False,
        "aeropuerto", f"Traslado aeropuerto — zona {zona_encontrada}",
    )


def calcular_urbano_km(km: float, vehiculo: str, nivel: str,
                        nocturno: bool, festivo: bool) -> Optional[ResultadoCotizacion]:
    t = TARIFAS.get(vehiculo)
    if t is None:
        return None
    tarifa_km = t["km_ciudad_nocturno"] if nocturno else t["km_ciudad_diurno"]
    precio_base = max(t["tarifa_minima_urbana"], round(km * tarifa_km))
    concepto = f"Servicio urbano {km:.0f} km ({'nocturno' if nocturno else 'diurno'})"
    return _construir_resultado(
        precio_base, nivel, nocturno, festivo, False, "urbano_km", concepto,
    )


def calcular_por_horas(horas: float, vehiculo: str, nivel: str,
                        nocturno: bool, festivo: bool) -> Optional[ResultadoCotizacion]:
    t = TARIFAS.get(vehiculo)
    if t is None:
        return None
    precio_base = round(horas * t["hora"])
    concepto = f"Servicio por horas ({horas:.0f} h)"
    return _construir_resultado(
        precio_base, nivel, nocturno, festivo, False, "por_horas", concepto,
    )


def calcular_multi_dia(destino: str, vehiculo: str, nivel: str, dias: int,
                        nocturno: bool, festivo: bool, rural: bool) -> Optional[ResultadoCotizacion]:
    # Precio base: ruta sencilla (día 1, sin recargos — se aplican al final)
    rutas_vehiculo = RUTAS.get(vehiculo, {})
    clave = buscar_clave_destino(destino, rutas_vehiculo)
    if clave is None:
        return None

    precio_ruta = rutas_vehiculo[clave]
    s = SERVICIOS_MULTI_DIA

    # Noches y disponibilidad: (dias - 1) veces
    noches = dias - 1
    costo_hospedaje = noches * s["hospedaje_conductor"]
    costo_disponibilidad = noches * s["disponibilidad_vehiculo"]

    # Comidas del conductor
    alimentos = s["alimentos_por_dia"]
    if dias == 1:
        comidas = alimentos[1]
    elif dias == 2:
        comidas = alimentos[1] + alimentos["ultimo"]
    else:
        comidas = alimentos[1] + (dias - 2) * alimentos["completo"] + alimentos["ultimo"]
    costo_alimentacion = comidas * s["alimentacion_conductor"]

    precio_base_particular = precio_ruta + costo_hospedaje + costo_disponibilidad + costo_alimentacion
    precio_nivel = precio_con_nivel(precio_base_particular, nivel)
    precio_final, recargos_con_monto = _aplicar_recargos(precio_nivel, nocturno, festivo, rural)

    desglose = [
        {"concepto": f"Traslado a {clave.replace('_', ' ').title()} (solo ida)", "valor": formatear_precio(precio_ruta)},
        {"concepto": f"Disponibilidad vehículo ({noches} día(s))", "valor": formatear_precio(costo_disponibilidad)},
        {"concepto": f"Hospedaje conductor ({noches} noche(s))", "valor": formatear_precio(costo_hospedaje)},
        {"concepto": f"Alimentación conductor ({comidas} comidas)", "valor": formatear_precio(costo_alimentacion)},
    ]

    if nivel != "particular":
        pct = 8 if nivel == "corporativo" else 15
        diferencia = precio_nivel - precio_base_particular
        desglose.append({"concepto": f"Tarifa {nivel} +{pct}%", "valor": formatear_precio(diferencia)})

    for descripcion, monto in recargos_con_monto:
        desglose.append({"concepto": descripcion, "valor": formatear_precio(monto)})

    desglose.append({"concepto": "Total", "valor": formatear_precio(precio_final)})

    return ResultadoCotizacion(
        precio_particular=precio_base_particular,
        precio_final=precio_final,
        nivel=nivel,
        desglose=desglose,
        recargos_aplicados=[d for d, _ in recargos_con_monto],
        notas=f"Servicio {dias} días — incluye viáticos del conductor",
        tipo_servicio="multi_dia",
    )


def calcular_destino_no_cargado(km: float, vehiculo: str, nivel: str,
                                  nocturno: bool, festivo: bool, rural: bool) -> Optional[ResultadoCotizacion]:
    if km is None or km <= 0:
        return None
    v = VARIABLES_OPERATIVAS
    costo_variable = v["combustible_km"] + v["desgaste_km"]
    margen = 1 - v["conductor_porcentaje"] - v["logistica_operativa"]
    precio_base = round((km * costo_variable * 2) / margen)  # × 2 para cubrir ida y operación
    return _construir_resultado(
        precio_base, nivel, nocturno, festivo, rural,
        "destino_no_cargado", f"Servicio estimado ({km:.0f} km aprox.)",
        notas="Estimación — destino no cargado en tarifario oficial",
    )


# ─── DISPATCHER PRINCIPAL ──────────────────────────────────────────────────────

def cotizar(params: dict) -> Optional[ResultadoCotizacion]:
    """
    Recibe el dict extraído del bloque [PARAMS] de Claude y despacha
    a la función de cálculo correspondiente.
    Retorna None si faltan parámetros mínimos (fallback graceful).
    """
    if not params:
        return None

    tipo     = params.get("tipo_servicio", "")
    vehiculo = params.get("vehiculo_clave", "camioneta")
    nivel    = params.get("nivel_comercial", "particular")
    destino  = params.get("destino", "")
    nocturno = bool(params.get("nocturno", False))
    festivo  = bool(params.get("festivo", False))
    rural    = bool(params.get("rural", False))
    km       = params.get("km")
    horas    = params.get("horas")
    dias     = params.get("dias")
    zona     = params.get("zona_aeropuerto", "")

    if tipo == "ruta_sencilla":
        resultado = calcular_ruta_sencilla(destino, vehiculo, nivel, nocturno, festivo, rural)
        if resultado is None and km:
            resultado = calcular_destino_no_cargado(km, vehiculo, nivel, nocturno, festivo, rural)
        return resultado

    if tipo == "ida_vuelta":
        resultado = calcular_ruta_ida_vuelta(destino, vehiculo, nivel, nocturno, festivo, rural)
        if resultado is None and km:
            resultado = calcular_destino_no_cargado(km, vehiculo, nivel, nocturno, festivo, rural)
        return resultado

    if tipo == "aeropuerto":
        return calcular_aeropuerto(zona or destino, vehiculo, nivel, nocturno, festivo)

    if tipo == "urbano_km":
        if km:
            return calcular_urbano_km(km, vehiculo, nivel, nocturno, festivo)
        return None

    if tipo == "por_horas":
        if horas:
            return calcular_por_horas(horas, vehiculo, nivel, nocturno, festivo)
        return None

    if tipo == "multi_dia":
        if destino and dias:
            return calcular_multi_dia(destino, vehiculo, nivel, dias, nocturno, festivo, rural)
        return None

    return None
