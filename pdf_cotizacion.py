"""
Generador de PDF profesional — Destinos Express S.A.S.
Diseño premium: Negro · Dorado · Blanco
Tipografías: Montserrat (títulos) · Poppins (cuerpo)
"""

import io
import os
import json
import glob as glob_module
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, Image, PageBreak
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ─── COLORES CORPORATIVOS ─────────────────────────────────────────────────────
NEGRO      = colors.HexColor('#0D0D0D')
DORADO     = colors.HexColor('#FCA311')
DORADO_OSC = colors.HexColor('#E08E00')
BLANCO     = colors.white
GRIS       = colors.HexColor('#F5F5F5')
GRIS_MED   = colors.HexColor('#D0D0D0')
GRIS_TEXT  = colors.HexColor('#555555')

PAGE_W, PAGE_H = A4
FONTS_DIR = os.path.join(os.path.dirname(__file__), 'fonts')
ICONS_DIR = os.path.join(os.path.dirname(__file__), 'icons')


def _icono(nombre: str, size: float):
    """Carga un ícono PNG. Retorna Image o None si no existe."""
    ruta = os.path.join(ICONS_DIR, f'{nombre}.png')
    if os.path.exists(ruta):
        try:
            return Image(ruta, width=size, height=size)
        except Exception:
            pass
    return None

# ─── REGISTRO DE FUENTES ──────────────────────────────────────────────────────
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
        'titulo':        'Montserrat-Bold'  if 'Montserrat-Bold' in registradas else 'Helvetica-Bold',
        'titulo_light':  'Montserrat'       if 'Montserrat' in registradas       else 'Helvetica',
        'cuerpo':        'Poppins'          if 'Poppins' in registradas           else 'Helvetica',
        'cuerpo_bold':   'Poppins-Bold'     if 'Poppins-Bold' in registradas      else 'Helvetica-Bold',
        'cuerpo_italic': 'Poppins-Italic'   if 'Poppins-Italic' in registradas    else 'Helvetica-Oblique',
    }

F = registrar_fuentes()

# ─── ESTILOS ──────────────────────────────────────────────────────────────────
def E(name, **kw):
    return ParagraphStyle(name, **kw)

def estilos():
    return {
        # Header
        'h_empresa':   E('h_empresa',   fontName=F['titulo'],       fontSize=14,  textColor=BLANCO),
        'h_nit':       E('h_nit',       fontName=F['cuerpo_bold'],  fontSize=8.5, textColor=DORADO, spaceBefore=5),
        'h_sub':       E('h_sub',       fontName=F['cuerpo'],       fontSize=8,   textColor=colors.HexColor('#CCCCCC')),
        'h_dorado':    E('h_dorado',    fontName=F['cuerpo_bold'],  fontSize=8,   textColor=DORADO),
        # Documento
        'titulo_doc':  E('titulo_doc',  fontName=F['titulo'],       fontSize=15,  textColor=NEGRO, spaceAfter=2),
        'seccion':     E('seccion',     fontName=F['titulo'],       fontSize=9,   textColor=DORADO, spaceBefore=6, spaceAfter=3),
        'etiqueta':    E('etiqueta',    fontName=F['cuerpo_bold'],  fontSize=7.5, textColor=GRIS_TEXT),
        'campo':       E('campo',       fontName=F['cuerpo'],       fontSize=10,  textColor=NEGRO),
        'highlight':   E('highlight',   fontName=F['titulo'],       fontSize=10,  textColor=NEGRO),
        'cuerpo':      E('cuerpo',      fontName=F['cuerpo'],       fontSize=8.5, textColor=NEGRO, spaceAfter=2, leading=12),
        'legal':       E('legal',       fontName=F['cuerpo'],       fontSize=7.5, textColor=GRIS_TEXT, spaceAfter=2, leading=11),
        'pequeño':     E('pequeño',     fontName=F['cuerpo_italic'],fontSize=7.5, textColor=GRIS_TEXT),
        # Precio
        'p_label':     E('p_label',     fontName=F['cuerpo'],       fontSize=8.5, textColor=NEGRO,  alignment=TA_CENTER),
        'p_divisa':    E('p_divisa',    fontName=F['cuerpo_bold'],  fontSize=9.5, textColor=NEGRO,  alignment=TA_CENTER),
        'p_valor':     E('p_valor',     fontName=F['titulo'],       fontSize=22,  textColor=NEGRO,  alignment=TA_CENTER),
        'p_nota':      E('p_nota',      fontName=F['cuerpo'],       fontSize=7.5, textColor=colors.HexColor('#444444'), alignment=TA_CENTER),
        # Tabla
        'tabla_h':     E('tabla_h',     fontName=F['titulo'],       fontSize=8.5, textColor=BLANCO),
        'tabla_hR':    E('tabla_hR',    fontName=F['titulo'],       fontSize=8.5, textColor=BLANCO, alignment=TA_RIGHT),
        'tabla_vR':    E('tabla_vR',    fontName=F['cuerpo'],       fontSize=8.5, textColor=NEGRO,  alignment=TA_RIGHT),
        # Footer
        'f_empresa':   E('f_empresa',   fontName=F['titulo'],       fontSize=9,   textColor=DORADO),
        'f_sub':       E('f_sub',       fontName=F['cuerpo'],       fontSize=7.5, textColor=colors.HexColor('#AAAAAA')),
        'f_frase':     E('f_frase',     fontName=F['cuerpo_italic'],fontSize=7.5, textColor=colors.HexColor('#AAAAAA'), alignment=TA_RIGHT),
    }

# ─── CONTADOR ─────────────────────────────────────────────────────────────────
def numero_cotizacion():
    archivo = os.path.join(os.path.dirname(__file__), 'contador.json')
    anio    = datetime.now().year
    if os.path.exists(archivo):
        with open(archivo) as f:
            data = json.load(f)
        data = {'anio': anio, 'n': 1} if data.get('anio') != anio else {**data, 'n': data['n'] + 1}
    else:
        data = {'anio': anio, 'n': 1}
    with open(archivo, 'w') as f:
        json.dump(data, f)
    return f"DX-{anio}-{data['n']:04d}"

def cop(valor):
    try:
        return f"${int(valor):,}".replace(",", ".")
    except:
        return str(valor)

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _logo_imagen(logo_path, target_width=3.8*cm, max_height=2.4*cm):
    """Carga el logo preservando el aspect ratio natural de la imagen."""
    if not (logo_path and os.path.exists(logo_path)):
        return None
    try:
        img     = Image(logo_path)
        nat_w   = img.imageWidth
        nat_h   = img.imageHeight
        if nat_w and nat_h:
            ratio = nat_h / nat_w
            w = target_width
            h = w * ratio
            # Si la altura excede el máximo, escala por altura
            if h > max_height:
                h = max_height
                w = h / ratio
            return Image(logo_path, width=w, height=h)
        return Image(logo_path, width=target_width, height=target_width * 0.5)
    except Exception:
        return None


# ─── BLOQUES ──────────────────────────────────────────────────────────────────

def bloque_header(ES, logo_path):
    """
    Encabezado negro.
    - Logo con aspect ratio correcto
    - Nombre de empresa en línea propia
    - NIT en línea propia (resaltado en dorado)
    - Ciudad y contacto en líneas separadas
    """
    logo_obj = _logo_imagen(logo_path, target_width=3.8*cm, max_height=2.4*cm)
    logo_cell = logo_obj if logo_obj else Paragraph("DESTINOS<br/>EXPRESS", ES['h_empresa'])

    info = [
        Paragraph("DESTINOS EXPRESS S.A.S.", ES['h_empresa']),
        Paragraph("NIT: 900.982.154-2", ES['h_nit']),
        Paragraph("Bogotá D.C., Colombia", ES['h_sub']),
        Paragraph("comercial@destinosexpress.com  ·  +57 302 4060101  ·  www.destinosexpress.com", ES['h_dorado']),
    ]

    t = Table([[logo_cell, info]], colWidths=[4.5*cm, 13.5*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), NEGRO),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN',         (0, 0), (0,  0),  'CENTER'),
        ('LEFTPADDING',   (0, 0), (0,  0),  12),
        ('LEFTPADDING',   (1, 0), (1,  0),  14),
        ('TOPPADDING',    (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    return t


def linea_dorada():
    t = Table([['']], colWidths=[18*cm], rowHeights=[0.22*cm])
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), DORADO)]))
    return t


def bloque_meta(ES, numero, fecha_emision, vence):
    data = [[
        Paragraph(f"<b>N° Cotización:</b>  {numero}", ES['cuerpo']),
        Paragraph(f"<b>Fecha de emisión:</b>  {fecha_emision}", ES['cuerpo']),
        Paragraph(f"<b>Vigencia:</b>  48 horas · Vence: {vence}", ES['cuerpo']),
    ]]
    t = Table(data, colWidths=[6*cm, 6*cm, 6*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), GRIS),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('BOX',           (0, 0), (-1, -1), 0.5, GRIS_MED),
        ('LINEBELOW',     (0, 0), (-1,  0), 2,   DORADO),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return t


def bloque_servicio(ES, datos):
    origen   = datos.get('origen',         '—')
    destino  = datos.get('destino',        '—')
    fecha    = datos.get('fecha_servicio', '—')
    hora     = datos.get('hora_servicio',  '—')
    pax      = str(datos.get('pasajeros',  '—'))
    vehiculo = datos.get('vehiculo',       '—')
    cap      = datos.get('capacidad',      '—')
    tipo     = datos.get('tipo_servicio',  '—')
    dist     = datos.get('distancia_km')
    dist_txt = f"{dist} km aprox." if dist else "A confirmar"

    def _etiq(texto, icono_nombre, ancho_col):
        """Etiqueta con ícono a la izquierda, centrado verticalmente."""
        ico = _icono(icono_nombre, 0.34*cm)
        if ico is None:
            return Paragraph(texto, ES['etiqueta'])
        t = Table([[ico, Paragraph(texto, ES['etiqueta'])]],
                  colWidths=[0.44*cm, ancho_col - 0.44*cm],
                  rowHeights=[0.42*cm])
        t.setStyle(TableStyle([
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN',         (0, 0), (0,  0),  'CENTER'),
            ('LEFTPADDING',   (0, 0), (-1, -1), 0),
            ('RIGHTPADDING',  (0, 0), (0,   0), 4),
            ('RIGHTPADDING',  (1, 0), (1,   0), 0),
            ('TOPPADDING',    (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        return t

    est_or = E('or', fontName=F['titulo'], fontSize=13, textColor=NEGRO)
    est_ds = E('de', fontName=F['titulo'], fontSize=13, textColor=NEGRO, alignment=TA_RIGHT)
    est_fl = E('fl', fontName=F['titulo'], fontSize=18, textColor=DORADO, alignment=TA_CENTER)

    ruta = Table(
        [[Paragraph(origen, est_or), Paragraph("→", est_fl), Paragraph(destino, est_ds)]],
        colWidths=[7*cm, 4*cm, 7*cm]
    )
    ruta.setStyle(TableStyle([
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW',     (0, 0), (-1, -1), 1.5, DORADO),
    ]))

    detalles = Table([
        [_etiq("Fecha del servicio",   "fecha",      4.8*cm),
         _etiq("Hora de salida",       "hora",       4.0*cm),
         _etiq("Pasajeros",            "pasajeros",  4.5*cm),
         _etiq("Distancia",            "distancia",  4.7*cm)],
        [Paragraph(fecha,    ES['campo']),
         Paragraph(hora,     ES['campo']),
         Paragraph(pax,      ES['campo']),
         Paragraph(dist_txt, ES['campo'])],
        [_etiq("Vehiculo recomendado", "vehiculo",   4.8*cm),
         _etiq("Capacidad",            "pasajeros",  4.0*cm),
         _etiq("Tipo de servicio",     "detalles",   4.5*cm),
         Paragraph("",                 ES['etiqueta'])],
        [Paragraph(vehiculo, ES['highlight']),
         Paragraph(cap,      ES['campo']),
         Paragraph(tipo,     ES['campo']),
         Paragraph("",       ES['campo'])],
    ], colWidths=[4.8*cm, 4*cm, 4.5*cm, 4.7*cm])

    detalles.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), GRIS),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('LINEBELOW',     (0, 1), (-1,  1), 0.5, GRIS_MED),
        ('BOX',           (0, 0), (-1, -1), 0.5, GRIS_MED),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    return [ruta, Spacer(1, 0.25*cm), detalles]


def bloque_precio(ES, total, recargos):
    """
    Caja dorada con precio + sección negra con 4 tarjetas de lo que incluye.
    Retorna lista de elementos.
    """
    precio_txt = cop(total)
    rec_txt = ("Recargos aplicados: " + "  |  ".join(recargos)) if recargos else ""

    # ── Caja dorada: precio ───────────────────────────────────────────────────
    precio_filas = [
        [Paragraph("VALOR TOTAL DEL SERVICIO", ES['p_label'])],
        [Paragraph("PESOS COLOMBIANOS (COP)  ·  NO DÓLARES", ES['p_divisa'])],
        [Paragraph(f"<b>{precio_txt}</b>", ES['p_valor'])],
        [Paragraph("No incluye IVA salvo indicación expresa", ES['p_nota'])],
    ]
    if rec_txt:
        precio_filas.append([Paragraph(rec_txt, ES['p_nota'])])

    t_precio = Table(precio_filas, colWidths=[18*cm])
    t_precio.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), DORADO),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (0,  0),  12),
        ('TOPPADDING',    (1, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LINEBELOW',     (0, 1), (-1,  1), 0.8, NEGRO),
    ]))

    # ── Tarjetas negras: lo que incluye ──────────────────────────────────────
    est_sec = E('inc_sec', fontName=F['titulo'],      fontSize=8.5, textColor=DORADO,                          alignment=TA_CENTER)
    est_tit = E('inc_tit', fontName=F['titulo'],      fontSize=11,  textColor=DORADO,  leading=14,             alignment=TA_CENTER)
    est_sub = E('inc_sub', fontName=F['cuerpo'],      fontSize=6.5, textColor=colors.HexColor('#999999'), leading=9, alignment=TA_CENTER)

    items = [
        ("CONDUCTOR",   "profesional certificado", "conductor"),
        ("COMBUSTIBLE", "incluido en tarifa",       "combustible"),
        ("PEAJES",      "todos incluidos",           "peajes"),
        ("SEGURO",      "póliza incluida",           "seguridad"),
    ]
    col_w = 18 * cm / 4

    def _card(titulo, sub, icono_nombre=None):
        filas = []
        ico = _icono(icono_nombre, 0.65*cm) if icono_nombre else None
        if ico:
            filas.append([ico])
        filas += [
            [Paragraph(titulo, est_tit)],
            [Paragraph(sub,   est_sub)],
        ]
        t = Table(filas, colWidths=[col_w - 0.4*cm])
        t.setStyle(TableStyle([
            ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',    (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING',   (0, 0), (-1, -1), 4),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 4),
        ]))
        return t

    t_header = Table(
        [[Paragraph("LO QUE INCLUYE SU SERVICIO", est_sec)]],
        colWidths=[18*cm]
    )
    t_header.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), NEGRO),
        ('TOPPADDING',    (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LINEBELOW',     (0, 0), (-1, -1), 0.5, colors.HexColor('#2A2A2A')),
    ]))

    t_cards = Table(
        [[_card(*item) for item in items]],
        colWidths=[col_w] * 4
    )
    t_cards.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), NEGRO),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LINEBEFORE',    (1, 0), (3, 0),   0.5, colors.HexColor('#2A2A2A')),
        ('LINEBELOW',     (0, 0), (-1, -1), 2,   DORADO),
    ]))

    return [t_precio, t_header, t_cards]


def bloque_galeria_vehiculo(ES, vehiculo_clave):
    """
    Galería de hasta 3 fotos del vehículo asignado.
    Las imágenes se leen de: vehiculos/{vehiculo_clave}/*.jpg/png
    Si no hay fotos o la carpeta no existe, retorna lista vacía.
    """
    if not vehiculo_clave:
        return []

    carpeta = os.path.join(os.path.dirname(__file__), 'vehiculos', vehiculo_clave)
    if not os.path.exists(carpeta):
        return []

    fotos = []
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp', '*.JPG', '*.JPEG', '*.PNG', '*.WEBP']:
        fotos.extend(glob_module.glob(os.path.join(carpeta, ext)))
    fotos = sorted(fotos)[:3]

    if not fotos:
        return []

    COL_W = 18 * cm / 3   # 6 cm por columna
    MAX_W = 5.6 * cm      # ancho máximo dentro de la celda
    MAX_H = 5.6 * cm      # alto máximo (limita fotos muy verticales)

    celdas = []
    for foto in fotos:
        try:
            from PIL import Image as PILImage
            with PILImage.open(foto) as pil:
                pw, ph = pil.size
            ratio = pw / ph
            img_w = MAX_W
            img_h = MAX_W / ratio
            if img_h > MAX_H:
                img_h = MAX_H
                img_w = MAX_H * ratio
            celdas.append(Image(foto, width=img_w, height=img_h))
        except Exception:
            celdas.append(Paragraph("", ES['cuerpo']))

    # Completar hasta 3 celdas
    while len(celdas) < 3:
        celdas.append(Paragraph("", ES['cuerpo']))

    titulo = Paragraph("VEHICULO ASIGNADO PARA SU SERVICIO", ES['seccion'])

    t = Table([celdas], colWidths=[COL_W, COL_W, COL_W])
    t.setStyle(TableStyle([
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND',    (0, 0), (-1, -1), NEGRO),
        ('TOPPADDING',    (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING',   (0, 0), (-1, -1), 4),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 4),
        ('LINEABOVE',     (0, 0), (-1,  0), 2,   DORADO),
        ('LINEBELOW',     (0, 0), (-1,  0), 0.5, DORADO),
    ]))

    return [titulo, t, Spacer(1, 0.35*cm)]


def bloque_pagos(ES):
    ico = _icono("metodos-pagos", 0.45*cm)
    if ico:
        t_tit = Table([[ico, Paragraph("MÉTODOS DE PAGO DISPONIBLES", ES['seccion'])]],
                      colWidths=[0.6*cm, 17*cm])
        t_tit.setStyle(TableStyle([
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING',   (0, 0), (-1, -1), 0),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
            ('TOPPADDING',    (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        titulo = t_tit
    else:
        titulo = Paragraph("MÉTODOS DE PAGO DISPONIBLES", ES['seccion'])
    data = [[
        Paragraph("<b>Facturación Empresarial</b><br/>Pago a 30 días<br/>Corte mensual 1–30",   ES['cuerpo']),
        Paragraph("<b>Pago Inmediato</b><br/>Transferencia bancaria<br/>Nequi · Daviplata",     ES['cuerpo']),
        Paragraph("<b>Tarjeta de Crédito</b><br/>Datáfono (Bogotá)<br/>Link de pago (+8%)",     ES['cuerpo']),
    ]]
    t = Table(data, colWidths=[6*cm, 6*cm, 6*cm])
    t.setStyle(TableStyle([
        ('GRID',          (0, 0), (-1, -1), 0.5, GRIS_MED),
        ('BACKGROUND',    (0, 0), (-1, -1), GRIS),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING',    (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('LINEABOVE',     (0, 0), (-1,  0), 2, DORADO),
    ]))
    return [titulo, t]


def _desglose_cliente(desglose: list) -> list:
    """
    Versión simplificada para el cliente: oculta tarifas internas (base/km/min).
    Muestra: descripción del servicio + subtotal, recargos si aplican, total.
    """
    if not desglose:
        return desglose

    def _parse(s):
        try:
            return int(str(s).replace('$', '').replace('.', '').strip())
        except Exception:
            return 0

    recargos = [d for d in desglose if str(d.get('concepto', '')).startswith('Recargo')]
    total_item = next((d for d in desglose if d.get('concepto', '') == 'Total'), None)
    servicio = dict(desglose[0])  # primera línea = descripción del servicio

    if total_item:
        total_val = _parse(total_item['valor'])
        recargos_sum = sum(_parse(r['valor']) for r in recargos)
        subtotal = total_val - recargos_sum
        servicio['valor'] = f"${subtotal:,}".replace(',', '.')

    resultado = [servicio] + recargos
    if total_item:
        resultado.append(total_item)
    return resultado


def bloque_desglose(ES, desglose):
    if not desglose:
        return []
    titulo = Paragraph("DESGLOSE DE TARIFA", ES['seccion'])
    filas = [[
        Paragraph("Concepto",    ES['tabla_h']),
        Paragraph("Valor (COP)", ES['tabla_hR']),
    ]]
    for item in _desglose_cliente(desglose):
        filas.append([
            Paragraph(str(item.get('concepto', '')), ES['cuerpo']),
            Paragraph(str(item.get('valor',    '')), ES['tabla_vR']),
        ])
    t = Table(filas, colWidths=[13*cm, 5*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1,  0), NEGRO),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [GRIS, BLANCO]),
        ('GRID',          (0, 0), (-1, -1), 0.3, GRIS_MED),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('LINEBELOW',     (0, 0), (-1,  0), 2, DORADO),
    ]))
    return [titulo, t]


def bloque_terminos(ES):
    elementos = [Paragraph("CONDICIONES DEL SERVICIO", ES['seccion'])]
    for c in [
        "Los servicios están sujetos a disponibilidad de vehículos al momento de la confirmación.",
        "Las tarifas incluyen conductor profesional, combustible, peajes e impuestos.",
        "Servicios con espera adicional podrán generar cargos según tabla de tiempos.",
        "Cancelaciones con menos de 6 horas: cargo del 50% del valor del servicio.",
        "Cancelaciones con menos de 2 horas: cargo del 100% del valor del servicio.",
        "El cliente es responsable de informar cambios en itinerarios o vuelos con anticipación.",
    ]:
        elementos.append(Paragraph(f"•  {c}", ES['legal']))
    return elementos


def bloque_certificaciones(ES):
    elementos = [Paragraph("GARANTÍAS DE SEGURIDAD Y CALIDAD", ES['seccion'])]
    for c in [
        "✓  Habilitación vigente del Ministerio de Transporte de Colombia",
        "✓  Cumplimiento del Plan Estratégico de Seguridad Vial (PESV)",
        "✓  Conductores certificados con experiencia y antecedentes verificados",
        "✓  Vehículos asegurados con póliza de responsabilidad civil extracontractual",
        "✓  Control documental activo y monitoreo GPS en tiempo real",
    ]:
        elementos.append(Paragraph(c, ES['cuerpo']))
    return elementos


def bloque_contacto(ES):
    titulo = Paragraph("PARA CONFIRMAR SU RESERVA", ES['seccion'])

    def _celda_contacto(icono_nombre, texto):
        ico = _icono(icono_nombre, 0.5*cm)
        filas = []
        if ico:
            filas.append([ico])
        filas.append([Paragraph(texto, ES['cuerpo'])])
        t = Table(filas, colWidths=[5.5*cm])
        t.setStyle(TableStyle([
            ('ALIGN',         (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING',   (0, 0), (-1, -1), 0),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
            ('TOPPADDING',    (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        return t

    data = [[
        _celda_contacto("whatsapp", "<b>WhatsApp / Llamadas</b><br/>+57 302 4060101"),
        _celda_contacto("mail",     "<b>Correo electrónico</b><br/>comercial@destinosexpress.com"),
        _celda_contacto("web",      "<b>Página web</b><br/>www.destinosexpress.com"),
    ]]
    t = Table(data, colWidths=[6*cm, 6*cm, 6*cm])
    t.setStyle(TableStyle([
        ('GRID',          (0, 0), (-1, -1), 0.5, GRIS_MED),
        ('BACKGROUND',    (0, 0), (-1, -1), GRIS),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING',    (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('LINEABOVE',     (0, 0), (-1,  0), 2, DORADO),
    ]))
    return [titulo, t]


def bloque_footer(ES):
    data = [[
        [Paragraph("DESTINOS EXPRESS S.A.S.", ES['f_empresa']),
         Paragraph("NIT: 900.982.154-2  ·  Bogotá D.C., Colombia", ES['f_sub']),
         Paragraph("comercial@destinosexpress.com  ·  +57 302 4060101  ·  www.destinosexpress.com", ES['f_sub'])],
        [Paragraph("Transporte ejecutivo y corporativo con cobertura nacional.", ES['f_frase']),
         Paragraph("Seguridad, puntualidad y confianza en cada trayecto.", ES['f_frase'])],
    ]]
    t = Table(data, colWidths=[10*cm, 8*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), NEGRO),
        ('LINEABOVE',     (0, 0), (-1,  0), 3, DORADO),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING',   (0, 0), (0,  -1), 12),
        ('RIGHTPADDING',  (-1,0), (-1, -1), 12),
    ]))
    return t


# ─── FUNCIÓN PRINCIPAL ────────────────────────────────────────────────────────

def generar_pdf(datos: dict, logo_path: str = "logo.jpeg") -> tuple:
    """
    Genera el PDF de cotización y devuelve (BytesIO, numero_cotizacion).

    Campos esperados en datos:
      origen, destino, fecha_servicio, hora_servicio, pasajeros,
      vehiculo, capacidad, tipo_servicio, distancia_km (opcional),
      total_min, total_max, recargos (lista), desglose (lista),
      vehiculo_clave (ej: "camioneta", "van_ejecutiva", "van_grande", "bus"),
      notas (opcional)
    """
    numero        = numero_cotizacion()
    buffer        = io.BytesIO()
    fecha_emision = datetime.now().strftime("%d/%m/%Y  %H:%M")
    vence         = (datetime.now() + timedelta(hours=48)).strftime("%d/%m/%Y  %H:%M")

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=1.5*cm, leftMargin=1.5*cm,
        topMargin=1.5*cm,   bottomMargin=1.5*cm,
    )

    ES             = estilos()
    S              = Spacer
    vehiculo_clave = datos.get('vehiculo_clave', '')
    story          = []

    # ── PÁGINA 1 ──────────────────────────────────────────────────────────────
    story += [
        bloque_header(ES, logo_path),
        linea_dorada(),
        S(1, 0.25*cm),
        Paragraph("COTIZACIÓN DE SERVICIO DE TRANSPORTE ESPECIAL", ES['titulo_doc']),
        S(1, 0.08*cm),
        bloque_meta(ES, numero, fecha_emision, vence),
        S(1, 0.28*cm),
        Paragraph("DETALLE DEL SERVICIO SOLICITADO", ES['seccion']),
        *bloque_servicio(ES, datos),
        S(1, 0.28*cm),
        *bloque_precio(ES, datos['total'], datos.get('recargos', [])),
    ]

    if datos.get('notas'):
        story += [S(1, 0.12*cm), Paragraph(datos['notas'], ES['pequeño'])]

    story += [
        S(1, 0.3*cm),
        *bloque_pagos(ES),
        S(1, 0.25*cm),
        bloque_footer(ES),
    ]

    # ── PÁGINA 2 ──────────────────────────────────────────────────────────────
    story += [PageBreak(), bloque_header(ES, logo_path), linea_dorada(), S(1, 0.4*cm)]

    # Galería del vehículo (si hay fotos en la carpeta)
    story += bloque_galeria_vehiculo(ES, vehiculo_clave)

    story += bloque_desglose(ES, datos.get('desglose', []))
    story += [S(1, 0.4*cm)]
    story += bloque_terminos(ES)
    story += [S(1, 0.4*cm)]
    story += bloque_certificaciones(ES)
    story += [S(1, 0.4*cm)]
    story += bloque_contacto(ES)
    story += [S(1, 0.5*cm), bloque_footer(ES)]

    doc.build(story)
    buffer.seek(0)
    return buffer, numero
