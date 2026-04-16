"""
Módulo de cálculo de precios — Destinos Express
Python calcula exactamente; Claude solo extrae parámetros.
"""

from dataclasses import dataclass
from typing import Optional
from tarifas import (
    TARIFAS, TARIFAS_ZONA, RECARGOS, AEROPUERTO_BOGOTA, AEROPUERTO_EL_DORADO_HOTELES,
    RUTAS, RUTAS_IDA_VUELTA, CORREDORES,
    SERVICIOS_MULTI_DIA, VARIABLES_OPERATIVAS, formatear_precio, precio_con_nivel,
    redondear_precio,
)
from maps import consultar_ruta


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


def _detectar_corredor(via_resumen: str) -> Optional[dict]:
    """
    Detecta el corredor de salida de Bogotá a partir del municipio destino.
    Busca coincidencia en destinos_ref de cada corredor.
    Retorna el dict del corredor o None si no hay coincidencia.
    """
    if not via_resumen:
        return None
    texto = via_resumen.lower().strip()
    # Normalización básica de tildes
    texto = (texto
             .replace("á", "a").replace("é", "e").replace("í", "i")
             .replace("ó", "o").replace("ú", "u"))
    for corredor in CORREDORES.values():
        for dest in corredor["destinos_ref"]:
            if dest.replace("_", " ") in texto or texto in dest.replace("_", " "):
                return corredor
    return None


def calcular_intermunicipal_corredor(
    km: float,
    via_resumen: str,
    vehiculo: str,
    nivel: str,
    nocturno: bool,
    festivo: bool,
    rural: bool,
) -> Optional["ResultadoCotizacion"]:
    """
    Interpola el precio para un destino intermunicipal o metropolitano que no está
    en RUTAS, usando la lógica del gerente:

        precio = km_nuevo × (precio_ref / km_ref)

    La ciudad de referencia se elige por el corredor de salida detectado a partir
    del nombre del municipio destino ('via_resumen' contiene el municipio).
    """
    corredor = _detectar_corredor(via_resumen)
    if corredor is None:
        return None

    ref_key  = corredor["referencia"]
    km_ref   = corredor["km_ref"]
    precio_ref = RUTAS.get(vehiculo, {}).get(ref_key)

    if not precio_ref or km_ref <= 0:
        return None

    precio_km  = precio_ref / km_ref
    precio_base = round(km * precio_km / 1000) * 1000   # redondea al millar

    nombre_ref = ref_key.replace("_", " ").title()
    concepto   = (
        f"Traslado estimado — {corredor['nombre']} · {km:.0f} km"
    )
    notas = (
        f"Estimado por corredor — referencia: {nombre_ref} "
        f"({km_ref} km = {formatear_precio(precio_ref)}) → "
        f"{precio_km:.0f} COP/km · "
        f"⚠️ Sujeto a confirmación del gerente"
    )

    return _construir_resultado(
        precio_base, nivel, nocturno, festivo, rural,
        "corredor_intermunicipal", concepto, notas=notas,
    )


def _aplicar_recargos(precio_base: int, nocturno: bool, festivo: bool, rural: bool):
    """
    Aplica recargos acumulativos sobre el precio base.
    Retorna (precio_final, [(descripcion, monto), ...])
    """
    precio = precio_base
    recargos = []

    if nocturno:
        nuevo = round(precio * (1 + RECARGOS["nocturno"]))
        recargos.append(("Recargo nocturno +15%", nuevo - precio))
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


def calcular_por_zona(origen: str, destino: str, vehiculo: str, nivel: str,
                       nocturno: bool, festivo: bool) -> Optional["ResultadoCotizacion"]:
    """
    Usa Google Maps para obtener km reales y municipio, detecta la zona
    y aplica la fórmula correspondiente (urbana o metropolitana).
    Para zona intermunicipal delega a la tabla RUTAS.
    """
    ruta = consultar_ruta(origen, destino)
    if ruta is None:
        return None

    km          = ruta["km"]
    minutos     = ruta["duracion_min"]
    zona        = ruta["zona"]
    rural       = ruta["es_rural"]
    municipio   = ruta["municipio_destino"]
    via_resumen = ruta.get("via_resumen", "")

    tarifas_vehiculo = TARIFAS_ZONA.get(zona, {}).get(vehiculo)

    if zona in ("urbana", "metropolitana") and tarifas_vehiculo:
        tarifa_km = tarifas_vehiculo["km_diurno"]
        base      = tarifas_vehiculo["base"]
        TARIFA_MIN = tarifas_vehiculo["min"]

        costo_km  = round(km * tarifa_km)
        costo_min = round(minutos * TARIFA_MIN)
        precio_base = base + costo_km + costo_min

        concepto = (
            f"Traslado {'urbano Bogotá' if zona == 'urbana' else municipio} — "
            f"{km:.1f} km · {minutos} min"
        )
        desglose_extra = [
            {"concepto": f"Base", "valor": formatear_precio(base)} if base > 0 else None,
            {"concepto": f"Recorrido {km:.1f} km × ${tarifa_km:,}", "valor": formatear_precio(costo_km)},
            {"concepto": f"Tiempo {minutos} min × $300", "valor": formatear_precio(costo_min)},
        ]
        desglose_extra = [d for d in desglose_extra if d]  # quitar None

        # Construir resultado manual para mostrar desglose detallado
        precio_con_recargos, recargos_con_monto = _aplicar_recargos(
            precio_base, nocturno, festivo, rural
        )
        if nivel == "corporativo":
            precio_final = round(precio_con_recargos * 1.08)
        else:
            precio_final = precio_con_recargos

        desglose = [{"concepto": concepto, "valor": ""}] + desglose_extra
        for desc, monto in recargos_con_monto:
            desglose.append({"concepto": desc, "valor": formatear_precio(monto)})
        if nivel == "corporativo":
            desglose.append({"concepto": "Tarifa corporativo +8%",
                             "valor": formatear_precio(precio_final - precio_con_recargos)})
        desglose.append({"concepto": "Total", "valor": formatear_precio(precio_final)})

        return ResultadoCotizacion(
            precio_particular=precio_base,
            precio_final=precio_final,
            nivel=nivel,
            desglose=desglose,
            recargos_aplicados=[d for d, _ in recargos_con_monto],
            notas=f"Google Maps: {km:.1f} km reales · {minutos} min estimados",
            tipo_servicio="urbano_km" if zona == "urbana" else "metropolitana",
        )

    # Zona intermunicipal: intentar corredor del gerente antes del fallback de costos
    resultado_corredor = calcular_intermunicipal_corredor(
        km, via_resumen, vehiculo, nivel, nocturno, festivo, rural
    )
    if resultado_corredor:
        return resultado_corredor

    # Último recurso: estimación por variables operativas
    return calcular_destino_no_cargado(km, vehiculo, nivel, nocturno, festivo, rural)


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
    # Nocturno y festivo aplican primero; corporativo se suma encima
    precio_con_recargos, recargos_con_monto = _aplicar_recargos(
        precio_base_particular, nocturno, festivo, rural
    )
    # Corporativo: +8% sobre el subtotal (ya con recargos nocturnos/festivos)
    if nivel == "corporativo":
        precio_final = round(precio_con_recargos * 1.08)
    else:
        precio_final = precio_con_recargos

    desglose = [{"concepto": concepto_base, "valor": formatear_precio(precio_base_particular)}]

    if nivel != "particular" and nivel != "ultima_hora":
        diferencia = precio_final - precio_con_recargos
        desglose_temp = []
        for descripcion, monto in recargos_con_monto:
            desglose_temp.append({"concepto": descripcion, "valor": formatear_precio(monto)})
        desglose += desglose_temp
        desglose.append({
            "concepto": "Tarifa corporativo +8%",
            "valor": formatear_precio(diferencia),
        })
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

    for descripcion, monto in recargos_con_monto:
        desglose.append({"concepto": descripcion, "valor": formatear_precio(monto)})

    desglose.append({"concepto": "Total", "valor": formatear_precio(precio_con_recargos)})

    return ResultadoCotizacion(
        precio_particular=precio_base_particular,
        precio_final=precio_con_recargos,
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


def _calcular_urbano_formula(km: float, vehiculo: str, nivel: str,
                              nocturno: bool, festivo: bool) -> Optional[ResultadoCotizacion]:
    """
    Fórmula urbana con TARIFAS_ZONA: base + km×4600 + min×300.
    Usada como fallback cuando Maps no está disponible.
    Asume ~3 min/km en Bogotá para la estimación de minutos.
    """
    tz = TARIFAS_ZONA.get("urbana", {}).get(vehiculo)
    if not tz:
        return None
    minutos_est = round(km * 3)
    base      = tz["base"]
    costo_km  = round(km * tz["km_diurno"])
    costo_min = round(minutos_est * tz["min"])
    precio_base = base + costo_km + costo_min

    precio_con_recargos, recargos_con_monto = _aplicar_recargos(precio_base, nocturno, festivo, False)
    precio_final = round(precio_con_recargos * 1.08) if nivel == "corporativo" else precio_con_recargos

    desglose = [
        {"concepto": f"Traslado urbano Bogotá — {km:.0f} km aprox. · {minutos_est} min est.", "valor": ""},
        {"concepto": f"Base", "valor": formatear_precio(base)},
        {"concepto": f"Recorrido {km:.0f} km × $4.600", "valor": formatear_precio(costo_km)},
        {"concepto": f"Tiempo {minutos_est} min × $300", "valor": formatear_precio(costo_min)},
    ]
    for desc, monto in recargos_con_monto:
        desglose.append({"concepto": desc, "valor": formatear_precio(monto)})
    if nivel == "corporativo":
        desglose.append({"concepto": "Tarifa corporativo +8%",
                         "valor": formatear_precio(precio_final - precio_con_recargos)})
    desglose.append({"concepto": "Total", "valor": formatear_precio(precio_final)})

    return ResultadoCotizacion(
        precio_particular=precio_base,
        precio_final=precio_final,
        nivel=nivel,
        desglose=desglose,
        recargos_aplicados=[d for d, _ in recargos_con_monto],
        notas="Distancia estimada — sin confirmación Google Maps",
        tipo_servicio="urbano_km",
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


def _precio_oneway_estimado(km: float, via_resumen: str, vehiculo: str) -> int:
    """
    Precio base estimado para UN trayecto (sin recargos, nivel particular).
    Intenta corredor primero (calibrado al tarifario real).
    Fallback: variables operativas sin factor deadhead.
    """
    corredor = _detectar_corredor(via_resumen)
    if corredor:
        ref_key   = corredor["referencia"]
        km_ref    = corredor["km_ref"]
        precio_ref = RUTAS.get(vehiculo, {}).get(ref_key)
        if precio_ref and km_ref > 0:
            return round(km * (precio_ref / km_ref) / 1000) * 1000

    # Variables operativas — un solo sentido (sin ×2 de deadhead)
    v = VARIABLES_OPERATIVAS
    costo_var = v["combustible_km"] + v["desgaste_km"]
    margen    = 1 - v["conductor_porcentaje"] - v["logistica_operativa"]
    return round((km * costo_var) / margen / 1000) * 1000


def calcular_ida_vuelta_con_espera(
    origen: str,
    destino: str,
    vehiculo: str,
    nivel: str,
    horas_espera: float,
    nocturno_ida: bool,
    festivo: bool,
    rural: bool,
) -> Optional[ResultadoCotizacion]:
    """
    Servicio compuesto: ida + disponibilidad en destino + vuelta mismo día.

    Desglose:
    - Ida (con recargo nocturno si aplica)
    - Disponibilidad en destino: horas × tarifa_hora del vehículo
    - Vuelta (se asume diurna)
    """
    ruta = consultar_ruta(origen, destino)
    if ruta is None:
        return None

    km          = ruta["km"]
    via_resumen = ruta.get("via_resumen", "")
    rural_real  = ruta.get("es_rural", False) or rural

    precio_oneway = _precio_oneway_estimado(km, via_resumen, vehiculo)

    precio_ida_base, recargos_ida     = _aplicar_recargos(precio_oneway, nocturno_ida, festivo, rural_real)
    precio_vuelta_base, recargos_vta  = _aplicar_recargos(precio_oneway, False,        festivo, rural_real)

    tarifa_hora   = TARIFAS.get(vehiculo, {}).get("hora", 52_000)
    precio_espera = round(horas_espera * tarifa_hora)

    subtotal = precio_ida_base + precio_espera + precio_vuelta_base

    if nivel == "corporativo":
        precio_final = round(subtotal * 1.08)
    else:
        precio_final = subtotal

    # ── Desglose ─────────────────────────────────────────────────────────────
    nombre_dest = destino.split(",")[0].strip()
    sfx_ida = " · nocturno" if nocturno_ida else ""

    desglose = [
        {"concepto": f"Ida: Bogotá → {nombre_dest} ({km:.0f} km{sfx_ida})",
         "valor": formatear_precio(precio_ida_base)},
    ]
    for desc, monto in recargos_ida:
        desglose.append({"concepto": desc, "valor": formatear_precio(monto)})

    if horas_espera > 0:
        desglose.append({
            "concepto": f"Disponibilidad en destino ({horas_espera:.0f} h × {formatear_precio(tarifa_hora)}/h)",
            "valor": formatear_precio(precio_espera),
        })

    desglose.append({
        "concepto": f"Vuelta: {nombre_dest} → Bogotá ({km:.0f} km · diurno)",
        "valor": formatear_precio(precio_vuelta_base),
    })
    for desc, monto in recargos_vta:
        desglose.append({"concepto": desc, "valor": formatear_precio(monto)})

    if nivel == "corporativo":
        desglose.append({"concepto": "Tarifa corporativo +8%",
                         "valor": formatear_precio(precio_final - subtotal)})

    desglose.append({"concepto": "Total", "valor": formatear_precio(precio_final)})

    all_recargos = [d for d, _ in recargos_ida] + [d for d, _ in recargos_vta]

    return ResultadoCotizacion(
        precio_particular=subtotal,
        precio_final=precio_final,
        nivel=nivel,
        desglose=desglose,
        recargos_aplicados=all_recargos,
        notas=(
            f"Ida + {horas_espera:.0f} h disponibilidad en destino + Vuelta · "
            f"{km:.1f} km c/trayecto · "
            f"⚠️ Precio estimado — sujeto a confirmación del gerente"
        ),
        tipo_servicio="ida_vuelta_espera",
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

def _aplicar_redondeo(resultado: Optional["ResultadoCotizacion"]) -> Optional["ResultadoCotizacion"]:
    """
    Redondea precio_final al millar más cercano y actualiza la línea 'Total'
    en el desglose. Se aplica una sola vez al salir del dispatcher.
    """
    if resultado is None:
        return None
    precio_r = redondear_precio(resultado.precio_final)
    desglose = [
        {"concepto": "Total", "valor": formatear_precio(precio_r)}
        if d["concepto"] == "Total" else d
        for d in resultado.desglose
    ]
    return ResultadoCotizacion(
        precio_particular=resultado.precio_particular,
        precio_final=precio_r,
        nivel=resultado.nivel,
        desglose=desglose,
        recargos_aplicados=resultado.recargos_aplicados,
        notas=resultado.notas,
        tipo_servicio=resultado.tipo_servicio,
    )


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
    origen   = params.get("origen", "Bogota")
    nocturno = bool(params.get("nocturno", False))
    festivo  = bool(params.get("festivo", False))
    rural    = bool(params.get("rural", False))
    km       = params.get("km")
    horas    = params.get("horas")
    dias     = params.get("dias")
    zona     = params.get("zona_aeropuerto", "")

    resultado = None

    if tipo == "ruta_sencilla":
        resultado = calcular_ruta_sencilla(destino, vehiculo, nivel, nocturno, festivo, rural)
        if resultado is None:
            resultado = calcular_por_zona(origen, destino, vehiculo, nivel, nocturno, festivo)
        if resultado is None and km:
            resultado = calcular_destino_no_cargado(km, vehiculo, nivel, nocturno, festivo, rural)

    elif tipo == "ida_vuelta":
        if horas and float(horas) > 0:
            resultado = calcular_ida_vuelta_con_espera(
                origen, destino, vehiculo, nivel,
                float(horas), nocturno, festivo, rural,
            )
        if resultado is None:
            resultado = calcular_ruta_ida_vuelta(destino, vehiculo, nivel, nocturno, festivo, rural)
        if resultado is None:
            # Destino fuera de tabla: calcular ambas piernas (ida + vuelta, 0h espera)
            resultado = calcular_ida_vuelta_con_espera(
                origen, destino, vehiculo, nivel, 0, nocturno, festivo, rural,
            )
        if resultado is None and km:
            resultado = calcular_destino_no_cargado(km, vehiculo, nivel, nocturno, festivo, rural)

    elif tipo == "aeropuerto":
        resultado = calcular_aeropuerto(zona or destino, vehiculo, nivel, nocturno, festivo)

    elif tipo == "urbano_km":
        if origen and destino:
            resultado = calcular_por_zona(origen, destino, vehiculo, nivel, nocturno, festivo)
        if resultado is None:
            km_calc = float(km) if km else 12.0
            resultado = _calcular_urbano_formula(km_calc, vehiculo, nivel, nocturno, festivo)

    elif tipo == "por_horas":
        if horas:
            resultado = calcular_por_horas(horas, vehiculo, nivel, nocturno, festivo)

    elif tipo == "multi_dia":
        if destino and dias:
            resultado = calcular_multi_dia(destino, vehiculo, nivel, dias, nocturno, festivo, rural)

    return _aplicar_redondeo(resultado)
