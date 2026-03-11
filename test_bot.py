"""
Test automatizado del flujo completo — sin Telegram.
Prueba procesar_cotizacion() con la API real de Claude.
"""

import asyncio
import os
import json
from dotenv import load_dotenv
load_dotenv()

# Cargar bot sin levantar Telegram
import bot
from cotizador import cotizar

VERDE  = "\033[92m"
ROJO   = "\033[91m"
AMARILLO = "\033[93m"
AZUL   = "\033[94m"
RESET  = "\033[0m"
NEGRITA = "\033[1m"

CASOS = [
    {
        "id": 1,
        "descripcion": "Saludo simple — sin cotización",
        "historial": [{"role": "user", "content": "Hola, buenas tardes"}],
        "espera_pdf": False,
        "precio_esperado": None,
    },
    {
        "id": 2,
        "descripcion": "Ruta sencilla particular — Bogotá → Tunja",
        "historial": [{"role": "user", "content":
            "Necesito una camioneta de Bogotá a Tunja para 2 personas "
            "el viernes 20 de marzo a las 7:00 am"}],
        "espera_pdf": True,
        "precio_esperado": 460_000,
    },
    {
        "id": 3,
        "descripcion": "Aeropuerto nocturno — Calle 127",
        "historial": [{"role": "user", "content":
            "Necesito transporte desde la Calle 127 al aeropuerto El Dorado "
            "mañana 12 de marzo a las 4:00 am, para 1 persona en camioneta"}],
        "espera_pdf": True,
        "precio_esperado": round(75_000 * 1.10),  # nocturno +10%
    },
    {
        "id": 4,
        "descripcion": "Ida y vuelta mismo día — Tunja",
        "historial": [{"role": "user", "content":
            "Buenos días, necesito una camioneta para ir a Tunja y regresar "
            "el mismo día, el sábado 21 de marzo a las 6 am, somos 2 personas"}],
        "espera_pdf": True,
        "precio_esperado": 680_000,
    },
    {
        "id": 5,
        "descripcion": "Corporativo — empresa cliente",
        "historial": [{"role": "user", "content":
            "Somos de la empresa ANDI, necesitamos cotización para traslado "
            "de Bogotá a Tunja el lunes 23 de marzo a las 8 am, 1 pasajero ejecutivo"}],
        "espera_pdf": True,
        "precio_esperado": 496_800,  # Tunja corporativo +8%
    },
    {
        "id": 6,
        "descripcion": "Destino no cargado — solicita datos faltantes",
        "historial": [{"role": "user", "content":
            "Necesito transporte de Bogotá a Honda el próximo jueves"}],
        "espera_pdf": False,  # Falta hora y pasajeros → Claude debe preguntar
        "precio_esperado": None,
    },
    {
        "id": 7,
        "descripcion": "Por horas — servicio urbano",
        "historial": [{"role": "user", "content":
            "Necesito una camioneta disponible por 4 horas en Bogotá "
            "el martes 24 de marzo a partir de las 9 am, para 2 personas"}],
        "espera_pdf": True,
        "precio_esperado": round(4 * 52_000),  # 4h × $52.000
    },
]


def separador(char="─", ancho=60):
    print(char * ancho)


async def ejecutar_caso(caso):
    separador()
    print(f"{NEGRITA}{AZUL}Caso {caso['id']}: {caso['descripcion']}{RESET}")
    print(f"  Mensaje: \"{caso['historial'][-1]['content'][:70]}...\"")
    print()

    try:
        texto, datos_pdf = await bot.procesar_cotizacion(caso["historial"])

        # Mostrar respuesta de Claude (primeras 300 chars)
        print(f"{NEGRITA}  Respuesta Claude:{RESET}")
        for linea in texto[:400].split("\n"):
            print(f"    {linea}")
        if len(texto) > 400:
            print("    [...]")
        print()

        # Evaluar resultado
        tiene_pdf = datos_pdf is not None and datos_pdf.get("total")

        if caso["espera_pdf"] and tiene_pdf:
            precio_real = datos_pdf["total"]
            precio_ok = (caso["precio_esperado"] is None or
                         abs(precio_real - caso["precio_esperado"]) < 100)

            if precio_ok:
                print(f"  {VERDE}✅ PDF generado — Total: ${precio_real:,.0f}{RESET}")
            else:
                print(f"  {AMARILLO}⚠️  PDF generado pero precio inesperado:{RESET}")
                print(f"     Esperado: ${caso['precio_esperado']:,.0f}")
                print(f"     Recibido: ${precio_real:,.0f}")

            print(f"  {AZUL}Desglose:{RESET}")
            for d in datos_pdf.get("desglose", []):
                print(f"    • {d['concepto']}: {d['valor']}")
            if datos_pdf.get("recargos"):
                print(f"    Recargos: {datos_pdf['recargos']}")

        elif not caso["espera_pdf"] and not tiene_pdf:
            print(f"  {VERDE}✅ Sin PDF — correcto (Claude pide más info o es saludo){RESET}")

        elif caso["espera_pdf"] and not tiene_pdf:
            print(f"  {AMARILLO}⚠️  Se esperaba PDF pero Claude no generó datos suficientes{RESET}")
            print(f"     datos_pdf: {datos_pdf}")

        else:
            print(f"  {AMARILLO}⚠️  PDF generado pero no se esperaba{RESET}")
            if datos_pdf:
                print(f"     Total: ${datos_pdf.get('total', 0):,.0f}")

    except Exception as e:
        print(f"  {ROJO}❌ Error: {e}{RESET}")
        import traceback
        traceback.print_exc()

    print()


async def main():
    separador("═")
    print(f"{NEGRITA}  TEST AUTOMATIZADO — BOT DESTINOS EXPRESS{RESET}")
    print(f"  {len(CASOS)} casos de prueba con API real de Claude")
    separador("═")
    print()

    resultados = {"ok": 0, "warn": 0, "error": 0}

    for caso in CASOS:
        await ejecutar_caso(caso)

    separador("═")
    print(f"{NEGRITA}  Test completado — revisa los resultados arriba{RESET}")
    separador("═")


if __name__ == "__main__":
    asyncio.run(main())
