"""
Generador de guía comercial — Bot de Cotizaciones Destinos Express
PDF de uso interno para el equipo comercial.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, HRFlowable, KeepTogether
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ─── COLORES CORPORATIVOS ─────────────────────────────────────────────────────
NEGRO      = colors.HexColor('#0D0D0D')
DORADO     = colors.HexColor('#FCA311')
DORADO_OSC = colors.HexColor('#E08E00')
DORADO_CLARO = colors.HexColor('#FFF3D6')
BLANCO     = colors.white
GRIS       = colors.HexColor('#F5F5F5')
GRIS_MED   = colors.HexColor('#D0D0D0')
GRIS_TEXT  = colors.HexColor('#555555')
VERDE      = colors.HexColor('#2E7D32')
VERDE_CLARO = colors.HexColor('#E8F5E9')
ROJO_CLARO = colors.HexColor('#FFEBEE')
ROJO       = colors.HexColor('#C62828')
AZUL       = colors.HexColor('#1565C0')
AZUL_CLARO = colors.HexColor('#E3F2FD')

PAGE_W, PAGE_H = A4
FONTS_DIR = os.path.join(os.path.dirname(__file__), 'fonts')
LOGO_PATH = os.path.join(os.path.dirname(__file__), 'logo.png')


# ─── FUENTES ─────────────────────────────────────────────────────────────────
def registrar_fuentes():
    fuentes = {
        'Montserrat-Bold': 'Montserrat-Bold.ttf',
        'Montserrat':      'Montserrat-Regular.ttf',
        'Poppins':         'Poppins-Regular.ttf',
        'Poppins-Bold':    'Poppins-Bold.ttf',
        'Poppins-Italic':  'Poppins-Italic.ttf',
    }
    registradas = []
    for nombre, archivo in fuentes.items():
        ruta = os.path.join(FONTS_DIR, archivo)
        if os.path.exists(ruta):
            try:
                pdfmetrics.registerFont(TTFont(nombre, ruta))
                registradas.append(nombre)
            except Exception:
                pass
    return {
        'titulo':        'Montserrat-Bold' if 'Montserrat-Bold' in registradas else 'Helvetica-Bold',
        'titulo_light':  'Montserrat'      if 'Montserrat' in registradas      else 'Helvetica',
        'cuerpo':        'Poppins'         if 'Poppins' in registradas          else 'Helvetica',
        'cuerpo_bold':   'Poppins-Bold'    if 'Poppins-Bold' in registradas     else 'Helvetica-Bold',
        'cuerpo_italic': 'Poppins-Italic'  if 'Poppins-Italic' in registradas   else 'Helvetica-Oblique',
    }


F = registrar_fuentes()


def E(name, **kw):
    return ParagraphStyle(name, **kw)


def estilos():
    return {
        'portada_titulo':   E('portada_titulo',  fontName=F['titulo'],      fontSize=26, textColor=BLANCO, alignment=TA_CENTER, leading=32),
        'portada_sub':      E('portada_sub',     fontName=F['cuerpo'],      fontSize=13, textColor=DORADO, alignment=TA_CENTER, spaceBefore=8),
        'portada_meta':     E('portada_meta',    fontName=F['cuerpo'],      fontSize=10, textColor=colors.HexColor('#CCCCCC'), alignment=TA_CENTER, spaceBefore=4),
        'seccion':          E('seccion',         fontName=F['titulo'],      fontSize=13, textColor=BLANCO, spaceBefore=2, spaceAfter=2),
        'h2':               E('h2',              fontName=F['cuerpo_bold'], fontSize=11, textColor=NEGRO, spaceBefore=10, spaceAfter=4),
        'h3':               E('h3',              fontName=F['cuerpo_bold'], fontSize=9.5, textColor=GRIS_TEXT, spaceBefore=6, spaceAfter=2),
        'cuerpo':           E('cuerpo',          fontName=F['cuerpo'],      fontSize=9.5, textColor=NEGRO, leading=15, spaceAfter=3),
        'cuerpo_italic':    E('cuerpo_italic',   fontName=F['cuerpo_italic'], fontSize=9, textColor=GRIS_TEXT, leading=14),
        'label':            E('label',           fontName=F['cuerpo_bold'], fontSize=9,  textColor=NEGRO),
        'label_gris':       E('label_gris',      fontName=F['cuerpo'],      fontSize=9,  textColor=GRIS_TEXT),
        'ejemplo_bien':     E('ejemplo_bien',    fontName=F['cuerpo_italic'], fontSize=9.5, textColor=VERDE, leading=14),
        'ejemplo_mal':      E('ejemplo_mal',     fontName=F['cuerpo_italic'], fontSize=9.5, textColor=ROJO, leading=14),
        'codigo':           E('codigo',          fontName='Courier',        fontSize=9,  textColor=NEGRO, leading=14, backColor=GRIS),
        'nota':             E('nota',            fontName=F['cuerpo_italic'], fontSize=9, textColor=AZUL, leading=14),
        'tabla_header':     E('tabla_header',    fontName=F['cuerpo_bold'], fontSize=8.5, textColor=BLANCO, alignment=TA_CENTER),
        'tabla_cel':        E('tabla_cel',       fontName=F['cuerpo'],      fontSize=8.5, textColor=NEGRO),
        'tabla_cel_c':      E('tabla_cel_c',     fontName=F['cuerpo'],      fontSize=8.5, textColor=NEGRO, alignment=TA_CENTER),
        'bullet':           E('bullet',          fontName=F['cuerpo'],      fontSize=9.5, textColor=NEGRO, leading=14, leftIndent=12),
        'footer':           E('footer',          fontName=F['cuerpo'],      fontSize=7.5, textColor=GRIS_TEXT, alignment=TA_CENTER),
    }


# ─── HELPERS DE CONSTRUCCIÓN ──────────────────────────────────────────────────

def separador(color=DORADO, grosor=1.5, margen_v=6):
    return [Spacer(1, margen_v), HRFlowable(width='100%', thickness=grosor, color=color), Spacer(1, margen_v)]


def banner_seccion(texto, ST):
    """Banda negra con texto dorado — encabezado de sección."""
    tabla = Table([[Paragraph(texto, ST['seccion'])]], colWidths=[PAGE_W - 4*cm])
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), NEGRO),
        ('TOPPADDING',    (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING',   (0, 0), (-1, -1), 12),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 12),
    ]))
    return [Spacer(1, 10), tabla, Spacer(1, 8)]


def caja_color(contenido_rows, color_fondo, ST, padding=8):
    """Caja con fondo de color para destacar contenido."""
    tabla = Table(contenido_rows, colWidths=[PAGE_W - 4*cm])
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), color_fondo),
        ('TOPPADDING',    (0, 0), (-1, -1), padding),
        ('BOTTOMPADDING', (0, 0), (-1, -1), padding),
        ('LEFTPADDING',   (0, 0), (-1, -1), 12),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 0, colors.transparent),
    ]))
    return tabla


def tabla_dos_cols(filas, ancho_col1, ancho_col2, ST, estilo_extra=None):
    tabla = Table(filas, colWidths=[ancho_col1, ancho_col2])
    estilo = [
        ('BACKGROUND', (0, 0), (-1, 0), NEGRO),
        ('TEXTCOLOR',  (0, 0), (-1, 0), BLANCO),
        ('FONTNAME',   (0, 0), (-1, 0), F['cuerpo_bold']),
        ('FONTSIZE',   (0, 0), (-1, -1), 8.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BLANCO, GRIS]),
        ('GRID',       (0, 0), (-1, -1), 0.4, GRIS_MED),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
    ]
    if estilo_extra:
        estilo += estilo_extra
    tabla.setStyle(TableStyle(estilo))
    return tabla


# ─── SECCIONES DEL DOCUMENTO ──────────────────────────────────────────────────

def portada(ST):
    elementos = []

    # Bloque negro superior con logo y título
    logo_cell = ''
    if os.path.exists(LOGO_PATH):
        logo_cell = Image(LOGO_PATH, width=3.5*cm, height=3.5*cm)

    tabla_portada = Table(
        [[logo_cell], [Paragraph('Guia de Uso', ST['portada_titulo'])],
         [Paragraph('Bot de Cotizaciones — Destinos Express', ST['portada_sub'])],
         [Paragraph('Herramienta interna para el area comercial', ST['portada_meta'])]],
        colWidths=[PAGE_W - 4*cm]
    )
    tabla_portada.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), NEGRO),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING',    (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elementos.append(tabla_portada)
    elementos.append(Spacer(1, 16))

    # Intro rápida
    intro = (
        "Este documento explica como usar el bot de Telegram para generar cotizaciones "
        "de forma rapida y precisa. Aqui encontraras los tipos de servicio disponibles, "
        "como redactar los mensajes para obtener el mejor resultado, ejemplos practicos "
        "y todo lo que necesitas saber antes de la primera prueba con un cliente."
    )
    elementos.append(Paragraph(intro, ST['cuerpo']))
    elementos += separador()

    return elementos


def seccion_como_funciona(ST):
    elementos = []
    elementos += banner_seccion('1. Como funciona el bot', ST)

    elementos.append(Paragraph(
        'El bot combina inteligencia artificial con un motor de precios propio. '
        'No improvisa valores: cada precio sale directamente del tarifario oficial de Destinos Express.',
        ST['cuerpo']
    ))
    elementos.append(Spacer(1, 8))

    # Flujo visual en tabla
    filas = [
        [Paragraph('Paso', ST['tabla_header']), Paragraph('Que ocurre', ST['tabla_header'])],
        [Paragraph('1', ST['tabla_cel_c']),
         Paragraph('Usted escribe el mensaje con los datos del servicio.', ST['tabla_cel'])],
        [Paragraph('2', ST['tabla_cel_c']),
         Paragraph('La IA lee el mensaje e identifica: origen, destino, pasajeros, fecha, hora y tipo de servicio.', ST['tabla_cel'])],
        [Paragraph('3', ST['tabla_cel_c']),
         Paragraph('El sistema busca el precio exacto en el tarifario oficial usando Python. La IA no calcula precios.', ST['tabla_cel'])],
        [Paragraph('4', ST['tabla_cel_c']),
         Paragraph('La IA redacta la cotizacion con el precio calculado y la envia por Telegram.', ST['tabla_cel'])],
        [Paragraph('5', ST['tabla_cel_c']),
         Paragraph('El bot genera y adjunta el PDF profesional con numero de cotizacion (DX-2026-XXXX).', ST['tabla_cel'])],
        [Paragraph('6', ST['tabla_cel_c']),
         Paragraph('La cotizacion queda guardada automaticamente en la base de datos interna.', ST['tabla_cel'])],
    ]
    t = tabla_dos_cols(filas, 1.5*cm, PAGE_W - 4*cm - 1.5*cm, ST)
    elementos.append(t)
    elementos.append(Spacer(1, 8))

    elementos.append(caja_color(
        [[Paragraph(
            'TIP CLAVE: Mientras mas datos incluya en el mensaje, mas precisa y completa sera la cotizacion. '
            'Si falta informacion, el bot la pedira antes de cotizar — no inventa datos.',
            ST['nota']
        )]],
        AZUL_CLARO, ST
    ))

    return elementos


def seccion_datos_clave(ST):
    elementos = []
    elementos += banner_seccion('2. Los 4 datos que siempre necesita el bot', ST)

    elementos.append(Paragraph(
        'Para generar una cotizacion completa el bot necesita como minimo estos cuatro datos. '
        'Si alguno falta, lo preguntara antes de dar el precio.',
        ST['cuerpo']
    ))
    elementos.append(Spacer(1, 8))

    filas = [
        [Paragraph('Dato', ST['tabla_header']), Paragraph('Que informar', ST['tabla_header']), Paragraph('Ejemplo', ST['tabla_header'])],
        [Paragraph('Origen y destino', ST['label']),
         Paragraph('Ciudad o direccion de recogida y llegada', ST['tabla_cel']),
         Paragraph('De Bogota a Tunja', ST['cuerpo_italic'])],
        [Paragraph('Pasajeros', ST['label']),
         Paragraph('Numero de personas que viajan', ST['tabla_cel']),
         Paragraph('3 personas', ST['cuerpo_italic'])],
        [Paragraph('Fecha', ST['label']),
         Paragraph('Dia del servicio (incluir si es festivo o domingo)', ST['tabla_cel']),
         Paragraph('sabado 12 de abril', ST['cuerpo_italic'])],
        [Paragraph('Hora', ST['label']),
         Paragraph('Hora de recogida (relevante para recargo nocturno)', ST['tabla_cel']),
         Paragraph('a las 6:00 am', ST['cuerpo_italic'])],
    ]
    ancho = PAGE_W - 4*cm
    t = Table(filas, colWidths=[ancho*0.22, ancho*0.40, ancho*0.38])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), NEGRO),
        ('TEXTCOLOR',     (0, 0), (-1, 0), BLANCO),
        ('FONTNAME',      (0, 0), (-1, 0), F['cuerpo_bold']),
        ('FONTSIZE',      (0, 0), (-1, -1), 8.5),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [BLANCO, GRIS]),
        ('GRID',          (0, 0), (-1, -1), 0.4, GRIS_MED),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elementos.append(t)
    elementos.append(Spacer(1, 8))

    elementos.append(Paragraph('Datos opcionales que mejoran la cotizacion:', ST['h3']))
    opcionales = [
        'Si el destino es zona rural, vereda o finca (aplica recargo del 10-15%).',
        'Si es un cliente corporativo (empresa con cuenta) o si el servicio es de ultima hora.',
        'Si necesita ida y regreso el mismo dia (tarifa diferente a solo ida).',
        'Si el servicio dura varios dias (incluye viaticos del conductor).',
    ]
    for op in opcionales:
        elementos.append(Paragraph(f'• {op}', ST['bullet']))

    return elementos


def seccion_vehiculos(ST):
    elementos = []
    elementos += banner_seccion('3. Vehiculos disponibles', ST)

    elementos.append(Paragraph(
        'El bot selecciona el vehiculo automaticamente segun el numero de pasajeros. '
        'Usted puede especificarlo si el cliente lo prefiere.',
        ST['cuerpo']
    ))
    elementos.append(Spacer(1, 8))

    filas = [
        [Paragraph('Vehiculo', ST['tabla_header']),
         Paragraph('Pasajeros', ST['tabla_header']),
         Paragraph('Tipo de servicio tipico', ST['tabla_header'])],
        [Paragraph('Camioneta Ejecutiva / SUV', ST['label']),
         Paragraph('1 a 4', ST['tabla_cel_c']),
         Paragraph('Traslados ejecutivos, familias, aeropuerto', ST['tabla_cel'])],
        [Paragraph('Van Ejecutiva', ST['label']),
         Paragraph('5 a 10', ST['tabla_cel_c']),
         Paragraph('Grupos medianos, equipos corporativos', ST['tabla_cel'])],
        [Paragraph('Van / Microbus', ST['label']),
         Paragraph('11 a 16', ST['tabla_cel_c']),
         Paragraph('Grupos grandes, congresos, eventos', ST['tabla_cel'])],
        [Paragraph('Bus Especial', ST['label']),
         Paragraph('17 a 40', ST['tabla_cel_c']),
         Paragraph('Grupos numerosos, paseos empresariales', ST['tabla_cel'])],
    ]
    ancho = PAGE_W - 4*cm
    t = Table(filas, colWidths=[ancho*0.38, ancho*0.18, ancho*0.44])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), NEGRO),
        ('TEXTCOLOR',     (0, 0), (-1, 0), BLANCO),
        ('FONTNAME',      (0, 0), (-1, 0), F['cuerpo_bold']),
        ('FONTSIZE',      (0, 0), (-1, -1), 8.5),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [BLANCO, GRIS]),
        ('GRID',          (0, 0), (-1, -1), 0.4, GRIS_MED),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elementos.append(t)

    return elementos


def seccion_tipos_servicio(ST):
    elementos = []
    elementos += banner_seccion('4. Tipos de servicio y como pedirlos', ST)

    servicios = [
        {
            'nombre': 'Ruta sencilla (solo ida)',
            'descripcion': 'Traslado de una ciudad a otra, sin regreso. El precio cubre el trayecto de ida completo.',
            'como': 'Mencione claramente que es "solo ida" o no mencione el regreso.',
            'ejemplo_bien': '"Necesito transporte de Bogota a Villavicencio para 3 personas el viernes 18 de abril a las 8am. Solo ida."',
            'ejemplo_mal': '"Llevar gente a Villa"  (muy vago, falta fecha, hora y pasajeros)',
        },
        {
            'nombre': 'Ida y vuelta mismo dia',
            'descripcion': 'El vehiculo va al destino, espera y regresa el mismo dia. Precio especial (mas economico que contratar dos servicios).',
            'como': 'Indique explicitamente "ida y vuelta" o "regresa el mismo dia".',
            'ejemplo_bien': '"Transporte a Chia para 4 personas el sabado 19 a las 9am. Ida y vuelta el mismo dia."',
            'ejemplo_mal': '"Quiero ir y volver a Chia el fin de semana"  (no dice cuantos son ni la hora)',
        },
        {
            'nombre': 'Aeropuerto El Dorado',
            'descripcion': 'Traslado desde cualquier zona de Bogota hasta el aeropuerto El Dorado (o viceversa). Tarifa fija por zona.',
            'como': 'Indique la zona o barrio de origen (o destino) dentro de Bogota.',
            'ejemplo_bien': '"Recogida en Chapinero para una persona el lunes 21 de abril a las 4am. Traslado al aeropuerto."',
            'ejemplo_mal': '"Traslado aeropuerto manana"  (sin zona, sin hora exacta)',
        },
        {
            'nombre': 'Servicio urbano por kilometro',
            'descripcion': 'Para movilizacion dentro de Bogota o el area metropolitana cuando se conoce la distancia aproximada.',
            'como': 'Mencione que es dentro de la ciudad e indique los kilometros aproximados o direcciones.',
            'ejemplo_bien': '"Recorrido urbano en Bogota, aproximadamente 25 km. Camioneta para 2 personas el jueves a las 7pm."',
            'ejemplo_mal': '"Mover a alguien en Bogota"  (sin distancia ni direcciones)',
        },
        {
            'nombre': 'Servicio por horas',
            'descripcion': 'El vehiculo queda a disposicion del cliente por un numero de horas determinado. Ideal para eventos o reuniones.',
            'como': 'Especifique cuantas horas necesita el vehiculo disponible.',
            'ejemplo_bien': '"Necesito una camioneta por 4 horas en Bogota el miercoles 23 de abril a partir de las 2pm."',
            'ejemplo_mal': '"Una camioneta un rato"  (sin numero de horas)',
        },
        {
            'nombre': 'Servicio multidia (pernocta)',
            'descripcion': 'El vehiculo y conductor se desplazan a otro municipio y pernoctan alli. Incluye viaticos del conductor (alimentacion y hospedaje).',
            'como': 'Indique el destino, el numero de dias y que el servicio requiere pernocta o que regresa en dias distintos.',
            'ejemplo_bien': '"Transporte a Medellin para 3 personas. Salen el martes 22 y regresan el jueves 24. Necesitan el vehiculo los 3 dias."',
            'ejemplo_mal': '"Un viaje largo a Medellin varios dias"  (sin fechas ni si el conductor se queda)',
        },
    ]

    for srv in servicios:
        elementos += [KeepTogether([
            Paragraph(srv['nombre'], ST['h2']),
            Paragraph(srv['descripcion'], ST['cuerpo']),
            Spacer(1, 4),
            Paragraph(f'Como pedirlo: {srv["como"]}', ST['h3']),
            caja_color(
                [[Paragraph(f'BIEN: {srv["ejemplo_bien"]}', ST['ejemplo_bien'])]],
                VERDE_CLARO, ST, padding=6
            ),
            Spacer(1, 3),
            caja_color(
                [[Paragraph(f'EVITAR: {srv["ejemplo_mal"]}', ST['ejemplo_mal'])]],
                ROJO_CLARO, ST, padding=6
            ),
            Spacer(1, 10),
        ])]

    return elementos


def seccion_niveles_precio(ST):
    elementos = []
    elementos += banner_seccion('5. Niveles de precio', ST)

    elementos.append(Paragraph(
        'El bot maneja tres niveles de precio segun el tipo de cliente o urgencia del servicio.',
        ST['cuerpo']
    ))
    elementos.append(Spacer(1, 8))

    filas = [
        [Paragraph('Nivel', ST['tabla_header']),
         Paragraph('Cuando aplica', ST['tabla_header']),
         Paragraph('Ajuste', ST['tabla_header']),
         Paragraph('Como indicarlo', ST['tabla_header'])],
        [Paragraph('Particular', ST['label']),
         Paragraph('Cliente natural, sin empresa', ST['tabla_cel']),
         Paragraph('Sin recargo', ST['tabla_cel_c']),
         Paragraph('Es el nivel por defecto. No necesita especificarlo.', ST['tabla_cel'])],
        [Paragraph('Corporativo', ST['label']),
         Paragraph('Empresa o cliente con cuenta', ST['tabla_cel']),
         Paragraph('+8%', ST['tabla_cel_c']),
         Paragraph('Mencione: "cliente corporativo", "empresa X", "cuenta empresarial".', ST['tabla_cel'])],
        [Paragraph('Ultima hora', ST['label']),
         Paragraph('Solicitud el mismo dia o muy urgente', ST['tabla_cel']),
         Paragraph('+15%', ST['tabla_cel_c']),
         Paragraph('Mencione: "para hoy", "urgente", "mismo dia". El bot lo detecta automaticamente.', ST['tabla_cel'])],
    ]
    ancho = PAGE_W - 4*cm
    t = Table(filas, colWidths=[ancho*0.17, ancho*0.25, ancho*0.12, ancho*0.46])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), NEGRO),
        ('TEXTCOLOR',     (0, 0), (-1, 0), BLANCO),
        ('FONTNAME',      (0, 0), (-1, 0), F['cuerpo_bold']),
        ('FONTSIZE',      (0, 0), (-1, -1), 8.5),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [BLANCO, GRIS]),
        ('GRID',          (0, 0), (-1, -1), 0.4, GRIS_MED),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elementos.append(t)

    return elementos


def seccion_recargos(ST):
    elementos = []
    elementos += banner_seccion('6. Recargos automaticos', ST)

    elementos.append(Paragraph(
        'El bot aplica estos recargos automaticamente cuando detecta las condiciones. '
        'Usted solo necesita mencionar los detalles del servicio con precision.',
        ST['cuerpo']
    ))
    elementos.append(Spacer(1, 8))

    filas = [
        [Paragraph('Recargo', ST['tabla_header']),
         Paragraph('%', ST['tabla_header']),
         Paragraph('Cuando aplica', ST['tabla_header']),
         Paragraph('Como mencionarlo', ST['tabla_header'])],
        [Paragraph('Nocturno', ST['label']),
         Paragraph('+15%', ST['tabla_cel_c']),
         Paragraph('Servicios entre las 7:00pm y las 7:00am', ST['tabla_cel']),
         Paragraph('"a las 10pm", "a las 5am", "de madrugada"', ST['tabla_cel'])],
        [Paragraph('Festivo', ST['label']),
         Paragraph('+10%', ST['tabla_cel_c']),
         Paragraph('Domingos y festivos oficiales colombianos', ST['tabla_cel']),
         Paragraph('Indique la fecha exacta; el bot identifica si es festivo.', ST['tabla_cel'])],
        [Paragraph('Zona rural', ST['label']),
         Paragraph('+10% a +15%', ST['tabla_cel_c']),
         Paragraph('Veredas, fincas, carreteras destapadas', ST['tabla_cel']),
         Paragraph('"vereda X", "finca en Y", "carretera destapada"', ST['tabla_cel'])],
    ]
    ancho = PAGE_W - 4*cm
    t = Table(filas, colWidths=[ancho*0.15, ancho*0.12, ancho*0.35, ancho*0.38])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), NEGRO),
        ('TEXTCOLOR',     (0, 0), (-1, 0), BLANCO),
        ('FONTNAME',      (0, 0), (-1, 0), F['cuerpo_bold']),
        ('FONTSIZE',      (0, 0), (-1, -1), 8.5),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [BLANCO, GRIS]),
        ('GRID',          (0, 0), (-1, -1), 0.4, GRIS_MED),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elementos.append(t)
    elementos.append(Spacer(1, 8))

    elementos.append(caja_color(
        [[Paragraph(
            'IMPORTANTE: Los recargos se acumulan. Un servicio nocturno en festivo a zona rural '
            'puede tener hasta 3 recargos aplicados. El desglose aparece detallado en el PDF.',
            ST['nota']
        )]],
        AZUL_CLARO, ST
    ))

    return elementos


def seccion_destinos(ST):
    elementos = []
    elementos += banner_seccion('7. Destinos en el tarifario oficial', ST)

    elementos.append(Paragraph(
        'Estos destinos tienen precio fijo en el tarifario. '
        'Para cualquier otro destino, el bot estima el precio con base en kilometraje.',
        ST['cuerpo']
    ))
    elementos.append(Spacer(1, 8))

    zonas = [
        ('Sabana Norte', 'Chia, Cajica, Zipaquira, Sopo, Tocancipa'),
        ('Sabana Occidente', 'Mosquera, Funza, Madrid, Facatativa, El Rosal'),
        ('Sabana Sur', 'Sibate, Fusagasuga, Silvania, Guasca, La Calera'),
        ('Corredor Tolima', 'Girardot, Melgar, Ibague, Espinal'),
        ('Meta', 'Villavicencio, Restrepo, Cumaral'),
        ('Boyaca', 'Tunja, Paipa, Duitama, Sogamoso, Villa de Leyva, Chiquinquira'),
        ('Ciudades principales', 'Medellin, Cali, Pereira, Armenia, Manizales'),
        ('Soacha (ida y vuelta)', 'Soacha Centro, San Mateo, Compartir'),
        ('Otras rutas i/v', 'Ubate, Simijaca, Choachi, Fomeque, Ubaque, Sasaima, La Vega, Villeta'),
    ]

    filas = [[Paragraph('Zona', ST['tabla_header']), Paragraph('Municipios / Destinos', ST['tabla_header'])]]
    for zona, destinos in zonas:
        filas.append([Paragraph(zona, ST['label']), Paragraph(destinos, ST['tabla_cel'])])

    ancho = PAGE_W - 4*cm
    t = Table(filas, colWidths=[ancho*0.30, ancho*0.70])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), NEGRO),
        ('TEXTCOLOR',     (0, 0), (-1, 0), BLANCO),
        ('FONTNAME',      (0, 0), (-1, 0), F['cuerpo_bold']),
        ('FONTSIZE',      (0, 0), (-1, -1), 8.5),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [BLANCO, GRIS]),
        ('GRID',          (0, 0), (-1, -1), 0.4, GRIS_MED),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elementos.append(t)

    return elementos


def seccion_aeropuerto(ST):
    elementos = []
    elementos += banner_seccion('8. Zonas de aeropuerto El Dorado', ST)

    elementos.append(Paragraph(
        'El traslado al aeropuerto tiene tarifa fija segun la zona de Bogota. '
        'Para cotizar correctamente, indique el barrio o sector de recogida (o entrega).',
        ST['cuerpo']
    ))
    elementos.append(Spacer(1, 8))

    zonas_fijas = [
        ('Calle 26 / Salitre / Modelia', '$34.000', '$36.000', '$39.000', '$41.000'),
        ('Chapinero / Quinta Paredes',   '$60.000', '$63.000', '$69.000', '$72.000'),
        ('Zona T / Parque 93',           '$64.000', '$67.000', '$74.000', '$77.000'),
        ('Calle 100',                    '$64.000', '$67.000', '$74.000', '$77.000'),
        ('Usaquen',                      '$68.000', '$71.000', '$78.000', '$82.000'),
        ('Cedritos / Colina',            '$72.000', '$75.000', '$83.000', '$87.000'),
        ('Suba',                         '$75.000', '$79.000', '$86.000', '$91.000'),
        ('Chia',                         '$125.000', '$131.000', '$144.000', '$151.000'),
        ('Tocancipa',                    '$165.000', '$173.000', '$190.000', '$199.000'),
    ]

    filas = [[
        Paragraph('Zona', ST['tabla_header']),
        Paragraph('Diurno\nParticular', ST['tabla_header']),
        Paragraph('Diurno\nCorporativo', ST['tabla_header']),
        Paragraph('Nocturno\nParticular', ST['tabla_header']),
        Paragraph('Nocturno\nCorporativo', ST['tabla_header']),
    ]]
    for row in zonas_fijas:
        filas.append([
            Paragraph(row[0], ST['tabla_cel']),
            Paragraph(row[1], ST['tabla_cel_c']),
            Paragraph(row[2], ST['tabla_cel_c']),
            Paragraph(row[3], ST['tabla_cel_c']),
            Paragraph(row[4], ST['tabla_cel_c']),
        ])

    # Zonas con tarifa base (no fija)
    zonas_base = [
        'Primera de Mayo: $65.000',
        'Ciudad Bolivar: $78.000',
        'San Cristobal Sur: $75.000',
        'Usme: $86.000',
        'Soacha Centro: $86.000',
        'San Mateo: $88.000',
        'Compartir: $98.000',
        'Centro hasta Cll 80: $60.000',
        'Cra 1: $65.000',
        'Calle 90: $70.000',
        'Calle 127: $75.000',
        'Cll 153: $82.000',
        'Cll 170: $90.000',
        'Cll 200: $95.000',
        'Guaymaral: $105.000',
    ]

    ancho = PAGE_W - 4*cm
    t = Table(filas, colWidths=[ancho*0.36, ancho*0.16, ancho*0.16, ancho*0.16, ancho*0.16])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), NEGRO),
        ('TEXTCOLOR',     (0, 0), (-1, 0), BLANCO),
        ('FONTNAME',      (0, 0), (-1, 0), F['cuerpo_bold']),
        ('FONTSIZE',      (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [BLANCO, GRIS]),
        ('GRID',          (0, 0), (-1, -1), 0.4, GRIS_MED),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elementos.append(t)
    elementos.append(Spacer(1, 8))

    elementos.append(Paragraph('Otras zonas (tarifa base particular, camioneta):', ST['h3']))
    texto_base = '  |  '.join(zonas_base[:8]) + '\n' + '  |  '.join(zonas_base[8:])
    elementos.append(Paragraph(texto_base, ST['cuerpo_italic']))
    elementos.append(Spacer(1, 6))
    elementos.append(caja_color(
        [[Paragraph(
            'Nocturno en aeropuerto: aplica de 7:00pm a 7:00am. '
            'Si el vuelo o la recogida es de madrugada, mencione la hora exacta.',
            ST['nota']
        )]],
        AZUL_CLARO, ST
    ))

    return elementos


def seccion_comandos(ST):
    elementos = []
    elementos += banner_seccion('9. Comandos del bot', ST)

    filas = [
        [Paragraph('Comando', ST['tabla_header']), Paragraph('Que hace', ST['tabla_header'])],
        [Paragraph('/start', ST['label']),
         Paragraph('Inicia una nueva sesion y muestra el mensaje de bienvenida. Usar al abrir el bot por primera vez.', ST['tabla_cel'])],
        [Paragraph('/reset', ST['label']),
         Paragraph('Borra la conversacion actual e inicia una en blanco. Util cuando se quiere cotizar un servicio diferente sin mezclar informacion.', ST['tabla_cel'])],
    ]
    t = tabla_dos_cols(filas, 2.5*cm, PAGE_W - 4*cm - 2.5*cm, ST)
    elementos.append(t)
    elementos.append(Spacer(1, 8))

    elementos.append(caja_color(
        [[Paragraph(
            'Use /reset entre cotizaciones distintas. El bot recuerda el contexto de la conversacion, '
            'por lo que mezclar dos servicios en el mismo chat puede generar confusiones.',
            ST['nota']
        )]],
        AZUL_CLARO, ST
    ))

    return elementos


def seccion_ejemplos_completos(ST):
    elementos = []
    elementos += banner_seccion('10. Ejemplos de mensajes completos', ST)

    elementos.append(Paragraph(
        'A continuacion, ejemplos reales de mensajes que generan cotizaciones precisas al primer intento.',
        ST['cuerpo']
    ))
    elementos.append(Spacer(1, 8))

    ejemplos = [
        {
            'caso': 'Ruta sencilla — cliente particular',
            'msg': 'Necesito transporte de Bogota a Tunja para 3 personas el sabado 19 de abril a las 6:30am. Solo ida.',
        },
        {
            'caso': 'Ida y vuelta — cliente corporativo',
            'msg': 'Buenos dias, cotizacion para cliente corporativo (empresa Merz). Transporte Bogota a Chia para 2 personas, ida y vuelta el mismo dia, lunes 21 de abril a las 9am.',
        },
        {
            'caso': 'Aeropuerto — nocturno',
            'msg': 'Recogida en Usaquen para 1 persona el martes 22 de abril a las 3:30am. Traslado al aeropuerto El Dorado. Vuelo internacional.',
        },
        {
            'caso': 'Servicio por horas — evento',
            'msg': 'Necesito una van ejecutiva para 8 personas disponible 5 horas en Bogota el miercoles 23 de abril a partir de las 2pm. Es para un evento corporativo.',
        },
        {
            'caso': 'Multidia — pernocta',
            'msg': 'Transporte a Villavicencio para 4 personas. Salen el jueves 24 de abril a las 7am y regresan el sabado 26 en la tarde. El conductor debe quedarse esos dias.',
        },
        {
            'caso': 'Zona rural — festivo',
            'msg': 'Servicio a una finca en vereda de Fusagasuga para 4 personas el domingo 20 de abril a las 8am. La via de acceso a la finca es destapada.',
        },
    ]

    for ej in ejemplos:
        elementos.append(KeepTogether([
            Paragraph(ej['caso'], ST['h3']),
            caja_color(
                [[Paragraph(ej['msg'], ST['cuerpo_italic'])]],
                DORADO_CLARO, ST, padding=8
            ),
            Spacer(1, 8),
        ]))

    return elementos


def seccion_tips(ST):
    elementos = []
    elementos += banner_seccion('11. Tips para sacar el mejor provecho', ST)

    tips = [
        ('Sea especifico con la hora',
         'La diferencia entre las 6pm y las 8pm puede significar un recargo nocturno. '
         'Siempre incluya la hora exacta.'),
        ('Mencione si es festivo o domingo',
         'El bot identifica festivos por fecha, pero si tiene duda, puede escribir '
         '"es festivo" o "es domingo" directamente.'),
        ('Indique si es zona rural o finca',
         'Si el destino final es una vereda, finca o carretera destapada, '
         'mencionelo. Afecta el precio y permite dar informacion precisa al conductor.'),
        ('Corporativo es diferente a particular',
         'Si el cliente tiene una empresa o cuenta corporativa, indicarlo ajusta '
         'el precio correctamente y aparece en el PDF.'),
        ('Use /reset entre cotizaciones',
         'El bot recuerda el contexto. Si pasa de una cotizacion de aeropuerto a una '
         'ruta intermunicipal sin hacer reset, puede haber confusion.'),
        ('El PDF sale automaticamente',
         'No hay que pedirle al bot que genere el PDF. Lo genera solo cuando la '
         'cotizacion esta completa. Lleva numero, fecha de validez y todos los detalles.'),
        ('Puede preguntar libremente',
         'Si el cliente hace preguntas adicionales (incluye peajes, que vehiculo es, etc.), '
         'escribalas en el chat. El bot responde y vuelve a la cotizacion cuando corresponde.'),
        ('Destinos fuera del tarifario',
         'Si el destino no esta en la lista, el bot igual cotiza con base en kilometraje. '
         'El precio sera estimado y el PDF lo indica claramente.'),
    ]

    for i, (titulo, desc) in enumerate(tips, 1):
        elementos.append(KeepTogether([
            Paragraph(f'{i}. {titulo}', ST['h2']),
            Paragraph(desc, ST['cuerpo']),
            Spacer(1, 4),
        ]))

    return elementos


def pie_pagina(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(GRIS_TEXT)
    canvas.drawCentredString(PAGE_W / 2, 1.2*cm, 'Destinos Express S.A.S.  |  NIT 900.982.154-2  |  Uso interno — area comercial')
    canvas.drawCentredString(PAGE_W / 2, 0.9*cm, f'Pagina {doc.page}')
    canvas.restoreState()


# ─── MAIN ────────────────────────────────────────────────────────────────────

def generar_guia(ruta_salida='guia_bot_comercial.pdf'):
    doc = SimpleDocTemplate(
        ruta_salida,
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2.5*cm,
        title='Guia Bot Cotizaciones — Destinos Express',
        author='Destinos Express S.A.S.',
    )

    ST = estilos()

    historia = []
    historia += portada(ST)
    historia += seccion_como_funciona(ST)
    historia += seccion_datos_clave(ST)
    historia += seccion_vehiculos(ST)
    historia += seccion_tipos_servicio(ST)
    historia += seccion_niveles_precio(ST)
    historia += seccion_recargos(ST)
    historia += seccion_destinos(ST)
    historia += seccion_aeropuerto(ST)
    historia += seccion_comandos(ST)
    historia += seccion_ejemplos_completos(ST)
    historia += seccion_tips(ST)

    doc.build(historia, onFirstPage=pie_pagina, onLaterPages=pie_pagina)
    print(f'PDF generado: {ruta_salida}')


if __name__ == '__main__':
    generar_guia()
