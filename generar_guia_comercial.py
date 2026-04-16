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

    logo_cell = ''
    if os.path.exists(LOGO_PATH):
        logo_cell = Image(LOGO_PATH, width=3.5*cm, height=3.5*cm)

    tabla_portada = Table(
        [[logo_cell],
         [Paragraph('Como usar el Bot de Cotizaciones', ST['portada_titulo'])],
         [Paragraph('Guia rapida — Equipo Comercial Destinos Express', ST['portada_sub'])],
         [Paragraph('En 5 minutos sabras todo lo que necesitas', ST['portada_meta'])]],
        colWidths=[PAGE_W - 4*cm]
    )
    tabla_portada.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), NEGRO),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING',    (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elementos.append(tabla_portada)
    elementos.append(Spacer(1, 14))

    elementos.append(caja_color(
        [[Paragraph(
            'TU NO CALCULAS NADA. El bot hace todo el trabajo: calcula el precio, '
            'redacta la cotizacion y genera el PDF automaticamente.',
            ST['nota']
        )]],
        DORADO_CLARO, ST, padding=10
    ))
    elementos.append(Spacer(1, 6))
    return elementos


def seccion_flujo(ST):
    elementos = []
    elementos += banner_seccion('1. Asi funciona — 3 pasos', ST)

    ancho = PAGE_W - 4*cm
    filas = [[
        Paragraph('PASO 1\nEl cliente te pide un servicio', ST['tabla_header']),
        Paragraph('PASO 2\nTu escribes en el bot con los 4 datos', ST['tabla_header']),
        Paragraph('PASO 3\nEl bot calcula, cotiza y envia el PDF', ST['tabla_header']),
    ]]
    t = Table(filas, colWidths=[ancho/3, ancho/3, ancho/3])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), NEGRO),
        ('TEXTCOLOR',     (0, 0), (-1, -1), DORADO),
        ('FONTNAME',      (0, 0), (-1, -1), F['cuerpo_bold']),
        ('FONTSIZE',      (0, 0), (-1, -1), 10),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 16),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
        ('GRID',          (0, 0), (-1, -1), 1, DORADO_OSC),
        ('LEADING',       (0, 0), (-1, -1), 16),
    ]))
    elementos.append(t)
    elementos.append(Spacer(1, 10))
    elementos.append(Paragraph(
        'El bot no improvisa precios. Cada valor sale del tarifario oficial. '
        'Tu trabajo es darle la informacion completa.',
        ST['cuerpo']
    ))
    return elementos


def seccion_4_datos(ST):
    elementos = []
    elementos += banner_seccion('2. Los 4 datos que SIEMPRE necesitas', ST)

    ancho = PAGE_W - 4*cm
    datos = [
        ('1.  De donde sale?', 'Nombre del lugar o direccion exacta', 'Hotel Estelar Calle 100'),
        ('2.  A donde va?',    'Nombre del lugar o direccion exacta', 'MedPlus de la Calle 127'),
        ('3.  Cuantas personas?', 'Numero de pasajeros', '3 personas'),
        ('4.  Que dia y a que hora?', 'Fecha y hora de recogida', '8 de abril a las 4pm'),
    ]
    filas = [[
        Paragraph('Dato', ST['tabla_header']),
        Paragraph('Que informar', ST['tabla_header']),
        Paragraph('Ejemplo', ST['tabla_header']),
    ]]
    for dato, que, ej in datos:
        filas.append([
            Paragraph(dato, ST['label']),
            Paragraph(que, ST['tabla_cel']),
            Paragraph(ej, ST['cuerpo_italic']),
        ])
    t = Table(filas, colWidths=[ancho*0.28, ancho*0.38, ancho*0.34])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), NEGRO),
        ('TEXTCOLOR',     (0, 0), (-1, 0), DORADO),
        ('FONTNAME',      (0, 0), (-1, 0), F['cuerpo_bold']),
        ('FONTSIZE',      (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [DORADO_CLARO, BLANCO]),
        ('GRID',          (0, 0), (-1, -1), 0.4, GRIS_MED),
        ('TOPPADDING',    (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elementos.append(t)
    elementos.append(Spacer(1, 8))
    elementos.append(Paragraph(
        'Si no tienes estos 4 datos, el bot te los va a pedir antes de cotizar. '
        'Mejor tenerlos listos desde el principio.',
        ST['cuerpo_italic']
    ))
    return elementos


def seccion_ejemplos(ST):
    elementos = []
    elementos += banner_seccion('3. Asi se escribe — ejemplos reales', ST)

    ancho = PAGE_W - 4*cm
    bien = (
        '"Necesito un traslado desde el Hotel Estelar Calle 100 hasta el '
        'MedPlus de la Calle 127, el 8 de abril a las 4pm, son 3 pasajeros."'
    )
    mal = (
        '"cuanto vale un carro para bogota"\n'
        '(falta: destino exacto, hora y numero de pasajeros)'
    )
    filas = [
        [Paragraph('BIEN — escribe asi:', ST['tabla_header']),
         Paragraph('MAL — evita esto:', ST['tabla_header'])],
        [Paragraph(bien, ST['ejemplo_bien']),
         Paragraph(mal,  ST['ejemplo_mal'])],
    ]
    t = Table(filas, colWidths=[ancho*0.5, ancho*0.5])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1,  0), NEGRO),
        ('BACKGROUND',    (0, 1), (0,   1), VERDE_CLARO),
        ('BACKGROUND',    (1, 1), (1,   1), ROJO_CLARO),
        ('GRID',          (0, 0), (-1, -1), 0.5, GRIS_MED),
        ('TOPPADDING',    (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ]))
    elementos.append(t)
    elementos.append(Spacer(1, 8))

    elementos.append(caja_color(
        [[Paragraph(
            'REGLA DE ORO: Escribe como si le explicaras a alguien por WhatsApp. '
            'Completo y claro. El bot entiende lenguaje natural.',
            ST['nota']
        )]],
        VERDE_CLARO, ST, padding=8
    ))
    elementos.append(Spacer(1, 10))

    # Más ejemplos por tipo
    elementos.append(Paragraph('Mas ejemplos por tipo de servicio:', ST['h2']))
    ejemplos = [
        ('Bogota → Tunja, solo ida',
         '"Cotizacion de Bogota a Tunja para 2 personas el viernes 11 de abril a las 7am. Solo ida."'),
        ('Aeropuerto — madrugada',
         '"Recogida en Chapinero para 1 persona el lunes a las 3:30am. Traslado al aeropuerto El Dorado."'),
        ('Ida y vuelta mismo dia',
         '"Transporte a Chia para 4 personas el sabado a las 9am. Ida y vuelta el mismo dia."'),
        ('Por horas — evento',
         '"Necesito una camioneta disponible 4 horas en Bogota el miercoles a partir de las 2pm."'),
        ('Cliente corporativo',
         '"Cotizacion para cliente Merz (corporativo). Bogota a Chia, 2 personas, lunes a las 9am."'),
    ]
    for caso, msg in ejemplos:
        elementos.append(KeepTogether([
            Paragraph(caso, ST['h3']),
            caja_color([[Paragraph(msg, ST['cuerpo_italic'])]], DORADO_CLARO, ST, padding=6),
            Spacer(1, 6),
        ]))
    return elementos


def seccion_tipos_servicio(ST):
    elementos = []
    elementos += banner_seccion('4. Tipos de servicio', ST)

    ancho = PAGE_W - 4*cm
    filas = [
        [Paragraph('Tipo', ST['tabla_header']),
         Paragraph('Cuando usarlo', ST['tabla_header']),
         Paragraph('Que decir en el mensaje', ST['tabla_header'])],
        [Paragraph('Urbano (Bogota)', ST['label']),
         Paragraph('Dentro de Bogota o area metropolitana', ST['tabla_cel']),
         Paragraph('Origen y destino dentro de la ciudad', ST['tabla_cel'])],
        [Paragraph('Intermunicipal', ST['label']),
         Paragraph('A otro municipio o ciudad', ST['tabla_cel']),
         Paragraph('"solo ida" si no regresa', ST['tabla_cel'])],
        [Paragraph('Aeropuerto', ST['label']),
         Paragraph('Al o desde el aeropuerto El Dorado', ST['tabla_cel']),
         Paragraph('Menciona el barrio o zona de recogida', ST['tabla_cel'])],
        [Paragraph('Ida y vuelta', ST['label']),
         Paragraph('Va y regresa el mismo dia', ST['tabla_cel']),
         Paragraph('"ida y vuelta el mismo dia"', ST['tabla_cel'])],
        [Paragraph('Por horas', ST['label']),
         Paragraph('Vehiculo disponible para eventos o diligencias', ST['tabla_cel']),
         Paragraph('"necesito X horas de servicio"', ST['tabla_cel'])],
        [Paragraph('Varios dias', ST['label']),
         Paragraph('Conductor pernocta en destino', ST['tabla_cel']),
         Paragraph('Fechas de salida y regreso', ST['tabla_cel'])],
    ]
    t = Table(filas, colWidths=[ancho*0.22, ancho*0.38, ancho*0.40])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), NEGRO),
        ('TEXTCOLOR',     (0, 0), (-1, 0), DORADO),
        ('FONTNAME',      (0, 0), (-1, 0), F['cuerpo_bold']),
        ('FONTSIZE',      (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [BLANCO, GRIS]),
        ('GRID',          (0, 0), (-1, -1), 0.4, GRIS_MED),
        ('TOPPADDING',    (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elementos.append(t)
    return elementos


def seccion_errores(ST):
    elementos = []
    elementos += banner_seccion('5. Errores comunes — evitalos', ST)

    errores = [
        (
            'Error 1: Destino ambiguo',
            '"MedPlus" sin decir cual. Hay varios en Bogota y el bot puede encontrar el equivocado.',
            'Escribe el nombre completo o la direccion: "MedPlus Calle 127" o "MedPlus Coliseo".'
        ),
        (
            'Error 2: Olvidar la hora',
            'Sin hora el bot no sabe si aplica recargo nocturno (despues de 7pm).',
            'Siempre incluye la hora: "a las 4pm", "a las 5:30am", "a las 10 de la noche".'
        ),
        (
            'Error 3: No decir cuantas personas van',
            'El numero de pasajeros define que vehiculo se recomienda.',
            'Siempre di cuantos son: "son 3 personas", "somos 2", "4 pasajeros".'
        ),
    ]

    for titulo, problema, solucion in errores:
        elementos.append(KeepTogether([
            caja_color(
                [[Paragraph(f'X  {titulo}', ST['h2'])]],
                ROJO_CLARO, ST, padding=6
            ),
            Spacer(1, 3),
            Paragraph(f'Problema: {problema}', ST['cuerpo']),
            Paragraph(f'Solucion: {solucion}', ST['ejemplo_bien']),
            Spacer(1, 8),
        ]))

    return elementos


def seccion_referencia(ST):
    elementos = []
    elementos += banner_seccion('6. Referencia rapida — ten esto a mano', ST)

    ancho = PAGE_W - 4*cm

    # Recargos
    elementos.append(Paragraph('Recargos que aplica el bot automaticamente:', ST['h2']))
    filas_rec = [
        [Paragraph('Recargo', ST['tabla_header']),
         Paragraph('Cuando aplica', ST['tabla_header']),
         Paragraph('Cuanto sube el precio', ST['tabla_header'])],
        [Paragraph('Nocturno', ST['label']),
         Paragraph('Despues de 7pm o antes de 7am', ST['tabla_cel']),
         Paragraph('+15%', ST['tabla_cel_c'])],
        [Paragraph('Festivo / Domingo', ST['label']),
         Paragraph('Domingos y festivos oficiales', ST['tabla_cel']),
         Paragraph('+10%', ST['tabla_cel_c'])],
        [Paragraph('Corporativo', ST['label']),
         Paragraph('Cliente con empresa o cuenta', ST['tabla_cel']),
         Paragraph('+8%', ST['tabla_cel_c'])],
        [Paragraph('Zona rural', ST['label']),
         Paragraph('Veredas, fincas, carreteras destapadas', ST['tabla_cel']),
         Paragraph('+10% a +15%', ST['tabla_cel_c'])],
    ]
    t = Table(filas_rec, colWidths=[ancho*0.22, ancho*0.50, ancho*0.28])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), NEGRO),
        ('TEXTCOLOR',     (0, 0), (-1, 0), DORADO),
        ('FONTNAME',      (0, 0), (-1, 0), F['cuerpo_bold']),
        ('FONTSIZE',      (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [BLANCO, GRIS]),
        ('GRID',          (0, 0), (-1, -1), 0.4, GRIS_MED),
        ('TOPPADDING',    (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN',         (2, 1), (2, -1), 'CENTER'),
    ]))
    elementos.append(t)
    elementos.append(Spacer(1, 12))

    # Vehiculos
    elementos.append(Paragraph('Vehiculo segun numero de pasajeros:', ST['h2']))
    filas_veh = [
        [Paragraph('Pasajeros', ST['tabla_header']),
         Paragraph('Vehiculo asignado', ST['tabla_header'])],
        [Paragraph('1 a 4', ST['tabla_cel_c']), Paragraph('Camioneta Ejecutiva / SUV', ST['tabla_cel'])],
        [Paragraph('5 a 10', ST['tabla_cel_c']), Paragraph('Van Ejecutiva', ST['tabla_cel'])],
        [Paragraph('11 a 16', ST['tabla_cel_c']), Paragraph('Van / Microbus', ST['tabla_cel'])],
        [Paragraph('17 a 40', ST['tabla_cel_c']), Paragraph('Bus Especial', ST['tabla_cel'])],
    ]
    t2 = Table(filas_veh, colWidths=[ancho*0.25, ancho*0.75])
    t2.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), NEGRO),
        ('TEXTCOLOR',     (0, 0), (-1, 0), DORADO),
        ('FONTNAME',      (0, 0), (-1, 0), F['cuerpo_bold']),
        ('FONTSIZE',      (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [BLANCO, GRIS]),
        ('GRID',          (0, 0), (-1, -1), 0.4, GRIS_MED),
        ('TOPPADDING',    (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN',         (0, 1), (0, -1), 'CENTER'),
    ]))
    elementos.append(t2)
    elementos.append(Spacer(1, 12))

    # Comando reset
    elementos.append(caja_color(
        [[Paragraph(
            '/reset  —  Escribe esto en el bot para borrar la conversacion y empezar de cero. '
            'Usalo entre cotizaciones distintas. El bot no se cansa.',
            ST['nota']
        )]],
        DORADO_CLARO, ST, padding=10
    ))

    return elementos


def seccion_aeropuerto(ST):
    elementos = []
    elementos += banner_seccion('Tarifas aeropuerto El Dorado (camioneta, particular)', ST)

    elementos.append(Paragraph(
        'Tarifa fija segun zona de Bogota. Menciona el barrio o sector al pedir la cotizacion.',
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
    historia += seccion_flujo(ST)
    historia += seccion_4_datos(ST)
    historia += seccion_ejemplos(ST)
    historia += seccion_tipos_servicio(ST)
    historia += seccion_errores(ST)
    historia += seccion_referencia(ST)
    historia += seccion_aeropuerto(ST)

    doc.build(historia, onFirstPage=pie_pagina, onLaterPages=pie_pagina)
    print(f'PDF generado: {ruta_salida}')


if __name__ == '__main__':
    generar_guia()
