"""
╔══════════════════════════════════════════════════════════╗
║     BOT DE COTIZACIONES — DESTINOS EXPRESS               ║
║     Telegram + Claude AI + PDF profesional               ║
╚══════════════════════════════════════════════════════════╝
"""

import anthropic
import json
import logging
import os
import re
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from tarifas import TARIFAS, AEROPUERTO_BOGOTA, RUTAS, RUTAS_IDA_VUELTA, FISCAL, formatear_precio
from cotizador import cotizar
from pdf_cotizacion import generar_pdf
from distancias import buscar_distancia

# ─── CONFIGURACION ────────────────────────────────────────────────────────────
TELEGRAM_TOKEN    = os.environ["TELEGRAM_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
LOGO_PATH         = "logo.jpeg"
MAX_TURNOS        = 12   # Máximo de pares usuario/bot por conversación (~24 mensajes)
# ──────────────────────────────────────────────────────────────────────────────

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
cliente_claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ─── MEMORIA DE CONVERSACIONES (en RAM, por chat_id) ──────────────────────────
# Formato: {chat_id: [{"role": "user"|"assistant", "content": "..."}]}
historiales = {}


# ─── LOG DE CONVERSACIONES (en disco) ────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
LOG_ARCHIVO = os.path.join("logs", "conversaciones.jsonl")

def registrar_log(chat_id: int, nombre_usuario: str, rol: str, texto: str, pdf_numero: str = None):
    """
    Guarda cada intercambio en logs/conversaciones.jsonl
    Una línea JSON por evento → fácil de leer y analizar después.
    """
    entrada = {
        "ts":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "chat_id": chat_id,
        "usuario": nombre_usuario,
        "rol":     rol,          # "cliente" o "bot"
        "texto":   texto[:500],  # primeros 500 caracteres
        "pdf":     pdf_numero,   # número de cotización si se generó PDF
    }
    with open(LOG_ARCHIVO, "a", encoding="utf-8") as f:
        f.write(json.dumps(entrada, ensure_ascii=False) + "\n")


# ─── INFO PARA SISTEMA ────────────────────────────────────────────────────────
def construir_info_vehiculos():
    """Info de vehículos y destinos para el prompt de Claude (referencia conversacional)."""
    texto = "=== VEHÍCULOS DISPONIBLES ===\n\n"
    for clave, t in TARIFAS.items():
        texto += f"• {t['nombre']} ({t['capacidad']}) — clave: \"{clave}\"\n"

    texto += "\n=== DESTINOS EN TARIFARIO ===\n"
    texto += "Sabana Norte: Chía, Cajicá, Zipaquirá, Sopó, Tocancipá\n"
    texto += "Sabana Occidente: Mosquera, Funza, Madrid, Facatativá, El Rosal\n"
    texto += "Sabana Sur: Sibaté, Fusagasugá, Silvania\n"
    texto += "Tolima: Girardot, Melgar, Ibagué, Espinal\n"
    texto += "Meta: Villavicencio, Restrepo, Cumaral\n"
    texto += "Boyacá: Tunja, Paipa, Duitama, Sogamoso, Villa de Leyva, Chiquinquirá\n"
    texto += "Ciudades principales: Medellín, Cali, Pereira, Armenia, Manizales\n"
    texto += "Para otros destinos el sistema estima con variables operativas.\n"

    texto += "\n=== AEROPUERTO EL DORADO ===\n"
    texto += "Zonas Sur: Primera de Mayo, Ciudad Bolívar, San Cristóbal Sur, Usme\n"
    texto += "Zonas Soacha: Soacha Centro, San Mateo, Compartir\n"
    texto += "Zonas Centro: Centro hasta Cll 80, Cra 1\n"
    texto += "Zonas Norte: Calle 90, Calle 127, Cll 153, Cll 170, Cll 200, Guaymaral\n"

    texto += "\n=== FISCAL ===\n"
    texto += f"IVA: exento. Retención en la fuente: {FISCAL['retefuente']*100:.1f}%\n"
    texto += f"Clientes con retención: {', '.join(FISCAL['clientes_con_retencion'])}\n"

    texto += "\n=== RECARGOS ===\n"
    texto += "Horario nocturno (10pm–5am): +10%\n"
    texto += "Festivos y domingos: +10%\n"
    texto += "Zona rural / vereda / carretera destapada: +10% a +20%\n"

    return texto


SISTEMA_EXTRACCION = """
Eres un extractor de parámetros para un sistema de cotizaciones de transporte ejecutivo.

Analiza el historial y determina si hay suficiente información para calcular un precio.
Si la hay, responde SOLO con el bloque [PARAMS]. Si no, responde SOLO con: NO_PARAMS

[PARAMS]
{
  "tipo_servicio": "ruta_sencilla" | "ida_vuelta" | "aeropuerto" | "urbano_km" | "por_horas" | "multi_dia",
  "destino": "nombre_sin_tildes_guion_bajo",
  "vehiculo_clave": "camioneta" | "van_ejecutiva" | "van_grande" | "bus",
  "nivel_comercial": "particular" | "corporativo" | "urgente",
  "km": null,
  "horas": null,
  "dias": null,
  "nocturno": false,
  "festivo": false,
  "zona_aeropuerto": null,
  "rural": false
}
[/PARAMS]

Reglas:
- vehiculo_clave: camioneta (1-4 pax), van_ejecutiva (5-10 pax), van_grande (11-16 pax), bus (17-40 pax)
- destino: minúsculas sin tildes, espacios→guion_bajo (ej: "villa_de_leyva", "tunja", "chia")
- nocturno: true SOLO si hora entre 22:00 y 05:00
- festivo: true SOLO si es domingo o festivo oficial colombiano (NO sábados, NO fines de semana regulares)
- zona_aeropuerto: solo si tipo_servicio="aeropuerto" (ej: "Calle 127", "Guaymaral", "Compartir")
- nivel_comercial: "corporativo" si menciona empresa/cliente corporativo, "urgente" si es mismo día o muy urgente, "particular" por defecto
- tipo_servicio "ida_vuelta" si explícitamente menciona ir y regresar el mismo día
""".strip()


SISTEMA = f"""
Eres el asistente comercial virtual de DESTINOS EXPRESS S.A.S., empresa líder en transporte
ejecutivo y corporativo en Colombia.

Tu misión es generar cotizaciones precisas, profesionales y confiables para los clientes.
Siempre habla de usted. Sé cordial, seguro y conciso.

{construir_info_vehiculos()}

═══════════════════════════════════════════════════════
PROCESO PARA GENERAR UNA COTIZACIÓN
═══════════════════════════════════════════════════════

PASO 1 — Recopilar información
Si el cliente no menciona alguno de estos datos, pregúntelos antes de cotizar:
• Origen y destino (ciudad / dirección)
• Número de pasajeros
• Fecha y hora del servicio
• Si el destino es zona rural, vereda o finca

PASO 2 — Determinar tipo de servicio
• Urbano: mismo municipio o área metropolitana de Bogotá
• Intermunicipal: entre ciudades distintas
• Rural: veredas, fincas, carreteras destapadas (recargo 10–20%)
• Aeropuerto: traslado al aeropuerto El Dorado (indica la zona de origen)

PASO 3 — Recomendar vehículo
• 1–4 pasajeros   → Camioneta Ejecutiva / SUV
• 5–10 pasajeros  → Van Ejecutiva
• 11–16 pasajeros → Van / Microbus
• 17–40 pasajeros → Bus Especial

PASO 4 — Distancia en km
Si el mensaje del sistema incluye la distancia confirmada, úsala directamente.
Si no, usa tu conocimiento de geografía colombiana para estimarla. Indica si es estimación.

PASO 5 — Precio
El sistema Python calcula el precio exacto y te lo entrega en [PRECIO_CALCULADO] del contexto.
Usa EXACTAMENTE ese valor. No hagas cálculos propios de precios.

PASO 6 — Presentar la cotización al cliente con este formato exacto:

✅ *Cotización de Servicio — Destinos Express*

Buenos días / tardes / noches, [saludo cordial de 1 línea].

🔹 *Servicio:* [Origen] → [Destino]
🔹 *Pasajeros:* [n]
🔹 *Fecha:* [fecha]
🔹 *Hora:* [hora]
🔹 *Vehículo:* [nombre] · [capacidad]
🔹 *Distancia aprox.:* [km] km  _(si aplica)_

💰 *Valor del servicio:*
   *$[valor] COP*

_[Nota si hay recargos aplicados]_

✅ *Incluye:* conductor profesional, combustible, peajes y póliza de seguro.

Adjunto encontrará la cotización formal en PDF con todos los detalles.
Para confirmar la reserva, contáctenos por WhatsApp o responda este mensaje.

═══════════════════════════════════════════════════════
BLOQUE DE DATOS PARA PDF (NO mostrar al cliente)
═══════════════════════════════════════════════════════

Al final de CADA cotización completa, incluye obligatoriamente este bloque JSON.
El sistema sobreescribirá 'total' y 'desglose' con los valores calculados por Python.

[PDF_DATA]
{{
  "origen": "...",
  "destino": "...",
  "fecha_servicio": "...",
  "hora_servicio": "...",
  "pasajeros": 0,
  "vehiculo": "...",
  "capacidad": "...",
  "vehiculo_clave": "camioneta",
  "tipo_servicio": "...",
  "distancia_km": null,
  "desglose": [],
  "total": 0,
  "recargos": [],
  "notas": null
}}
[/PDF_DATA]

IMPORTANTE sobre vehiculo_clave: usa exactamente uno de estos valores:
• "camioneta"     → Camioneta Ejecutiva / SUV (1–4 pasajeros)
• "van_ejecutiva" → Van Ejecutiva (5–10 pasajeros)
• "van_grande"    → Van / Microbus (11–16 pasajeros)
• "bus"           → Bus Especial (17–40 pasajeros)

REGLAS IMPORTANTES:
- Si falta información, PREGUNTA antes de cotizar. No inventes datos.
- Usa SIEMPRE el precio del [PRECIO_CALCULADO] del contexto. Nunca calcules tú.
- SOLO menciona recargos (nocturno, festivo, rural) si aparecen en el [PRECIO_CALCULADO]. Si no están, NO los menciones.
- Festivo = domingo o festivo oficial colombiano. Los sábados NO son festivos.
- Sé profesional pero humano. No seas robótico.
- Responde siempre en español formal.
- Si preguntan algo distinto a cotizaciones, responde brevemente y redirige.
"""


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def extraer_params(texto: str):
    """Extrae [PARAMS]{JSON}[/PARAMS] del texto. Retorna (texto_sin_bloque, dict|None)."""
    patron = r'\[PARAMS\](.*?)\[/PARAMS\]'
    match  = re.search(patron, texto, re.DOTALL)
    if not match:
        return texto, None
    texto_limpio = texto[:match.start()].strip()
    try:
        params = json.loads(match.group(1).strip())
        return texto_limpio, params
    except json.JSONDecodeError:
        return texto_limpio, None


def extraer_pdf_data(texto: str):
    """Extrae el bloque [PDF_DATA]...[/PDF_DATA] del texto de Claude."""
    patron = r'\[PDF_DATA\](.*?)\[/PDF_DATA\]'
    match  = re.search(patron, texto, re.DOTALL)
    if not match:
        return texto, None
    texto_limpio = texto[:match.start()].strip()
    try:
        datos = json.loads(match.group(1).strip())
        return texto_limpio, datos
    except json.JSONDecodeError:
        return texto_limpio, None


def buscar_distancia_en_historial(historial: list):
    """
    Busca origen/destino en todos los mensajes del usuario en el historial.
    Así funciona aunque la ruta venga en mensajes anteriores.
    """
    texto = " ".join(
        m["content"].lower()
        for m in historial
        if m["role"] == "user"
    )
    palabras = texto.split()
    for i, palabra in enumerate(palabras):
        if palabra in ["a", "hacia", "hasta", "para"] and i > 0:
            origen  = palabras[i - 1]
            destino = palabras[i + 1] if i + 1 < len(palabras) else None
            if destino:
                dist = buscar_distancia(origen, destino)
                if dist:
                    return dist
    return None


def construir_mensajes_claude(historial: list, resultado=None) -> list:
    """
    Toma el historial limpio y construye la lista de mensajes para Claude.
    Inyecta fecha, distancia y (opcionalmente) el precio calculado por Python
    en el ÚLTIMO mensaje del usuario, sin contaminar el historial guardado.
    """
    fecha_hoy       = datetime.now().strftime("%A %d de %B del %Y, %H:%M horas")
    distancia_local = buscar_distancia_en_historial(historial)

    contexto = f"[CONTEXTO DEL SISTEMA]\nFecha y hora actual: {fecha_hoy}\n"
    if distancia_local:
        contexto += f"Distancia confirmada en tabla local: {distancia_local} km. No necesitas estimarla.\n"

    if resultado is not None:
        contexto += "\n[PRECIO_CALCULADO_POR_SISTEMA]\n"
        contexto += "El módulo Python calculó el precio exacto con tarifas oficiales:\n"
        for d in resultado.desglose:
            contexto += f"- {d['concepto']}: {d['valor']}\n"
        if resultado.recargos_aplicados:
            contexto += f"- Recargos: {', '.join(resultado.recargos_aplicados)}\n"
        if resultado.notas:
            contexto += f"- Notas: {resultado.notas}\n"
        contexto += "Usa EXACTAMENTE este precio en tu respuesta. No recalcules.\n"
        contexto += "[/PRECIO_CALCULADO]\n"

    contexto += (
        "\nSi el cliente menciona una dirección exacta (carrera, calle, avenida, etc.), "
        "úsala como referencia para el conductor pero determina la ciudad/municipio "
        "de origen y destino para calcular la tarifa. No preguntes por la dirección.\n"
        "[FIN CONTEXTO]\n\n"
    )

    mensajes = []
    for i, msg in enumerate(historial):
        if i == len(historial) - 1 and msg["role"] == "user":
            mensajes.append({"role": "user", "content": contexto + msg["content"]})
        else:
            mensajes.append(msg)
    return mensajes


# ─── CLAUDE ───────────────────────────────────────────────────────────────────

async def procesar_cotizacion(historial: list) -> tuple:
    """
    Flujo de dos llamados:
    1. Claude extrae parámetros [PARAMS] (rápido, max_tokens=400)
    2. Python calcula el precio exacto con cotizador.py
    3. Claude genera la respuesta completa con el precio inyectado en contexto
    Fallback graceful: si cotizar() retorna None, el segundo llamado va sin precio inyectado.
    """
    mensajes = construir_mensajes_claude(historial)

    # ── Paso 1: extraer parámetros del servicio ──
    resp_extraccion = cliente_claude.messages.create(
        model="claude-haiku-4-5",
        max_tokens=400,
        system=SISTEMA_EXTRACCION,
        messages=mensajes,
    )
    _, params = extraer_params(resp_extraccion.content[0].text)

    # ── Paso 2: Python calcula precio exacto ──
    resultado = cotizar(params) if params else None
    if resultado:
        logging.info(f"Cotizador: {resultado.tipo_servicio} → {formatear_precio(resultado.precio_final)}")

    # ── Paso 3: Claude genera respuesta con precio inyectado ──
    mensajes_con_precio = construir_mensajes_claude(historial, resultado)
    respuesta_completa = ""

    with cliente_claude.messages.stream(
        model="claude-haiku-4-5",
        max_tokens=1500,
        system=[{
            "type": "text",
            "text": SISTEMA,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=mensajes_con_precio,
    ) as stream:
        for texto in stream.text_stream:
            respuesta_completa += texto

    texto_final, datos_pdf = extraer_pdf_data(respuesta_completa)

    # ── Sobreescribir total y desglose con valores de Python ──
    if datos_pdf and resultado:
        datos_pdf["total"]    = resultado.precio_final
        datos_pdf["desglose"] = resultado.desglose
        datos_pdf["recargos"] = resultado.recargos_aplicados
        if resultado.notas:
            datos_pdf.setdefault("notas", resultado.notas)

    return texto_final, datos_pdf


# ─── COMANDOS TELEGRAM ────────────────────────────────────────────────────────

async def comando_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    historiales.pop(chat_id, None)   # limpia historial al iniciar

    bienvenida = (
        "👋 Bienvenido a *Destinos Express*\n"
        "_Transporte ejecutivo y corporativo con cobertura nacional_\n\n"
        "Estoy aquí para generarle su cotización de servicio de forma inmediata.\n\n"
        "📝 *Para cotizar, indíqueme:*\n"
        "• Ciudad de origen y destino\n"
        "• Número de pasajeros\n"
        "• Fecha y hora del servicio\n\n"
        "_Ejemplo: Necesito transporte de Bogotá a Tunja para 6 personas "
        "el sábado 15 de marzo a las 7:00 am._\n\n"
        "Con gusto le atenderé. 🚐\n\n"
        "💡 _Use /reset para iniciar una cotización nueva en cualquier momento._"
    )
    await update.message.reply_text(bienvenida, parse_mode="Markdown")


async def comando_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id      = update.effective_chat.id
    tenia_historial = chat_id in historiales and len(historiales[chat_id]) > 0

    historiales.pop(chat_id, None)
    logging.info(f"[{chat_id}] Conversación reiniciada por /reset")

    msg = (
        "🔄 *Conversación reiniciada.*\n\n"
        "Puede comenzar una nueva cotización cuando guste.\n\n"
        "📝 *Indíqueme:*\n"
        "• Origen y destino\n"
        "• Número de pasajeros\n"
        "• Fecha y hora del servicio"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


# ─── MANEJADOR PRINCIPAL ──────────────────────────────────────────────────────

async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje  = update.message.text
    chat_id  = update.effective_chat.id
    usuario  = update.effective_user.full_name or str(chat_id)

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    logging.info(f"[{chat_id}] {usuario}: {mensaje[:80]}")

    # ── Inicializar historial si es la primera vez ──
    if chat_id not in historiales:
        historiales[chat_id] = []

    # ── Agregar mensaje del usuario al historial ──
    historiales[chat_id].append({"role": "user", "content": mensaje})

    # ── Registrar en log ──
    registrar_log(chat_id, usuario, "cliente", mensaje)

    # ── Llamar a Claude con el historial completo ──
    texto, datos_pdf = await procesar_cotizacion(historiales[chat_id])

    # ── Guardar respuesta de Claude en el historial ──
    historiales[chat_id].append({"role": "assistant", "content": texto})

    # ── Limitar tamaño del historial (evita crecimiento infinito) ──
    # Mantiene los últimos MAX_TURNOS pares de mensajes
    limite = MAX_TURNOS * 2
    if len(historiales[chat_id]) > limite:
        historiales[chat_id] = historiales[chat_id][-limite:]

    # ── Enviar respuesta al cliente ──
    await update.message.reply_text(texto, parse_mode="Markdown")

    # ── Generar y enviar PDF si la cotización está completa ──
    pdf_numero = None
    if datos_pdf and datos_pdf.get('total'):
        try:
            await context.bot.send_chat_action(chat_id=chat_id, action="upload_document")

            pdf_bytes, pdf_numero = generar_pdf(datos_pdf, logo_path=LOGO_PATH)
            nombre_archivo = f"Cotizacion_{pdf_numero}_DestinosExpress.pdf"

            await update.message.reply_document(
                document=pdf_bytes,
                filename=nombre_archivo,
                caption=(
                    f"📄 *Cotización {pdf_numero}*\n"
                    f"Destinos Express S.A.S.\n"
                    f"_Válida por 48 horas_"
                ),
                parse_mode="Markdown"
            )
            logging.info(f"[{chat_id}] PDF generado: {nombre_archivo}")

        except Exception as e:
            logging.error(f"Error generando PDF: {e}")
            await update.message.reply_text(
                "⚠️ La cotización fue procesada pero hubo un inconveniente al generar el PDF. "
                "Por favor contáctenos directamente para recibirlo.",
                parse_mode="Markdown"
            )

    # ── Registrar respuesta del bot en log ──
    registrar_log(chat_id, usuario, "bot", texto, pdf_numero)


# ─── ARRANQUE ─────────────────────────────────────────────────────────────────

def main():
    print("\n" + "═"*52)
    print("  🚐  BOT DESTINOS EXPRESS — ACTIVO")
    print("  Esperando mensajes de Telegram...")
    print("═"*52 + "\n")

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", comando_inicio))
    app.add_handler(CommandHandler("reset", comando_reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
