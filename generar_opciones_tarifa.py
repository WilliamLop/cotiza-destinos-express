"""
Documento de opciones tarifarias — Destinos Express S.A.S.
Para revisión con el gerente: rebalanceo de fórmula urbana.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ─── COLORES ──────────────────────────────────────────────────────────────────
NEGRO      = colors.HexColor('#0D0D0D')
DORADO     = colors.HexColor('#FCA311')
DORADO_OSC = colors.HexColor('#E08E00')
BLANCO     = colors.white
GRIS       = colors.HexColor('#F5F5F5')
GRIS_MED   = colors.HexColor('#D0D0D0')
GRIS_TEXT  = colors.HexColor('#555555')
VERDE      = colors.HexColor('#2E7D32')
ROJO       = colors.HexColor('#C62828')

# ─── FUENTES ──────────────────────────────────────────────────────────────────
FONTS_DIR = os.path.join(os.path.dirname(__file__), 'fonts')

def registrar_fuentes():
    fuentes = {
        'Montserrat-Bold': 'Montserrat-Bold.ttf',
        'Montserrat':      'Montserrat-Regular.ttf',
        'Poppins':         'Poppins-Regular.ttf',
        'Poppins-Bold':    'Poppins-Bold.ttf',
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
        'titulo': 'Montserrat-Bold' if 'Montserrat-Bold' in registradas else 'Helvetica-Bold',
        'cuerpo': 'Poppins'         if 'Poppins' in registradas          else 'Helvetica',
        'bold':   'Poppins-Bold'    if 'Poppins-Bold' in registradas     else 'Helvetica-Bold',
    }

# ─── DATOS ────────────────────────────────────────────────────────────────────
OPCIONES = [
    # (etiqueta, base, km_diurno, min, destacado)
    ("0 — Actual",  8_000, 4_600, 300, False),
    ("A",          12_000, 4_200, 300, False),
    ("B",          16_000, 3_800, 300, False),
    ("C",          20_000, 3_400, 300, False),
    ("D",          24_000, 3_000, 300, False),
]

VIAJES = [
    # (descripcion, km, min)
    ("Viaje corto\n(ej: Chapinero → Parque 93)",          3,  10),
    ("Viaje medio — REFERENCIA\n(ej: Usaquén → Salitre)", 10, 25),
    ("Viaje largo\n(ej: Suba → Centro)",                  20, 45),
    ("Viaje muy largo\n(ej: Bosa → Usaquén)",             25, 50),
]

def calcular(base, km_rate, min_rate, km, minutos):
    return base + km * km_rate + minutos * min_rate

def fmt(valor):
    return f"${valor:,.0f}".replace(",", ".")

# ─── GENERACIÓN PDF ───────────────────────────────────────────────────────────
def generar():
    F = registrar_fuentes()

    def E(name, **kwargs):
        return ParagraphStyle(name, **kwargs)

    S = {
        'titulo':    E('titulo',    fontName=F['titulo'], fontSize=18, textColor=NEGRO,     spaceAfter=4),
        'subtitulo': E('subtitulo', fontName=F['cuerpo'], fontSize=10, textColor=GRIS_TEXT,  spaceAfter=2),
        'seccion':   E('seccion',   fontName=F['titulo'], fontSize=10, textColor=DORADO_OSC, spaceBefore=18, spaceAfter=6),
        'nota':      E('nota',      fontName=F['cuerpo'], fontSize=8.5, textColor=GRIS_TEXT, spaceAfter=3, leading=13),
        'nota_bold': E('nota_bold', fontName=F['bold'],   fontSize=8.5, textColor=NEGRO,     spaceAfter=3, leading=13),
        'formula':   E('formula',   fontName=F['bold'],   fontSize=10, textColor=NEGRO,      spaceAfter=2, alignment=TA_CENTER),
        'cell_h':    E('cell_h',    fontName=F['titulo'], fontSize=8.5, textColor=BLANCO,     alignment=TA_CENTER),
        'cell_hL':   E('cell_hL',   fontName=F['titulo'], fontSize=8.5, textColor=BLANCO,     alignment=TA_LEFT),
        'cell':      E('cell',      fontName=F['cuerpo'], fontSize=9,   textColor=NEGRO,      alignment=TA_CENTER, leading=13),
        'cell_L':    E('cell_L',    fontName=F['cuerpo'], fontSize=8.5, textColor=NEGRO,      alignment=TA_LEFT,   leading=13),
        'cell_b':    E('cell_b',    fontName=F['bold'],   fontSize=9,   textColor=NEGRO,      alignment=TA_CENTER, leading=13),
        'cell_ref':  E('cell_ref',  fontName=F['bold'],   fontSize=9,   textColor=DORADO_OSC, alignment=TA_CENTER, leading=13),
        'verde':     E('verde',     fontName=F['bold'],   fontSize=8.5, textColor=VERDE,      alignment=TA_CENTER, leading=13),
        'rojo':      E('rojo',      fontName=F['bold'],   fontSize=8.5, textColor=ROJO,       alignment=TA_CENTER, leading=13),
    }

    output = os.path.join(os.path.dirname(__file__), 'opciones_tarifa_urbana.pdf')
    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=1.8*cm, rightMargin=1.8*cm,
        topMargin=1.8*cm,  bottomMargin=1.8*cm,
    )

    story = []

    # ── Encabezado ──
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Destinos Express S.A.S.", S['titulo']))
    story.append(Paragraph("Opciones de rebalanceo — Fórmula tarifaria urbana", S['subtitulo']))
    story.append(Paragraph("Documento interno · Para revisión con gerencia · Abril 2026", S['subtitulo']))

    # Línea separadora dorada
    story.append(Spacer(1, 0.4*cm))
    linea = Table([['']], colWidths=[doc.width])
    linea.setStyle(TableStyle([('LINEABOVE', (0,0), (-1,0), 2, DORADO)]))
    story.append(linea)
    story.append(Spacer(1, 0.5*cm))

    # ── Contexto ──
    story.append(Paragraph("CONTEXTO", S['seccion']))
    story.append(Paragraph(
        "La fórmula actual de precios urbanos funciona correctamente. "
        "El objetivo es presentar opciones donde la <b>tarifa base sea más alta</b>, "
        "ajustando el precio por kilómetro para que el <b>precio final sea equivalente</b> "
        "en un viaje de referencia (10 km · 25 min).",
        S['nota']
    ))

    # ── Fórmula ──
    story.append(Paragraph("FÓRMULA", S['seccion']))
    story.append(Paragraph("precio = BASE  +  km × TARIFA/KM  +  minutos × 300", S['formula']))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "El componente <b>min × 300</b> (precio por minuto) <b>no cambia</b> en ninguna opción. "
        "Solo varían BASE y TARIFA/KM.",
        S['nota']
    ))

    # ── Tabla de opciones ──
    story.append(Paragraph("LAS 4 OPCIONES", S['seccion']))

    col_etiq  = 3.5*cm
    col_base  = 2.8*cm
    col_km    = 2.8*cm
    col_min   = 2.2*cm
    col_check = 4.2*cm
    col_widths_op = [col_etiq, col_base, col_km, col_min, col_check]

    tabla_op_data = [[
        Paragraph("Opción", S['cell_h']),
        Paragraph("Base", S['cell_h']),
        Paragraph("Tarifa/km", S['cell_h']),
        Paragraph("Tarifa/min", S['cell_h']),
        Paragraph("Verificación (10km · 25min)", S['cell_h']),
    ]]

    for etiq, base, km_rate, min_rate, _ in OPCIONES:
        precio = calcular(base, km_rate, min_rate, 10, 25)
        check = f"{fmt(base)} + {fmt(km_rate*10)} + {fmt(min_rate*25)} = {fmt(precio)}"
        is_actual = etiq.startswith("0")
        estilo = S['cell_b'] if not is_actual else S['cell']
        tabla_op_data.append([
            Paragraph(etiq, estilo),
            Paragraph(fmt(base), estilo),
            Paragraph(fmt(km_rate), estilo),
            Paragraph(fmt(min_rate), estilo),
            Paragraph(check, S['cell_ref'] if not is_actual else S['cell']),
        ])

    tabla_op = Table(tabla_op_data, colWidths=col_widths_op)
    tabla_op.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0,0), (-1,0), NEGRO),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [GRIS, BLANCO]),
        # Fila "Actual" con fondo diferente
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#EEEEEE')),
        ('TEXTCOLOR', (0,1), (-1,1), GRIS_TEXT),
        # Bordes
        ('BOX', (0,0), (-1,-1), 0.5, GRIS_MED),
        ('INNERGRID', (0,0), (-1,-1), 0.3, GRIS_MED),
        ('LINEBELOW', (0,0), (-1,0), 1.5, DORADO),
        # Padding
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(tabla_op)
    story.append(Spacer(1, 0.8*cm))

    # ── Tabla comparativa de precios ──
    story.append(Paragraph("COMPARATIVA DE PRECIOS POR TIPO DE VIAJE", S['seccion']))
    story.append(Paragraph(
        "La fila de referencia (10km · 25min) arroja el mismo precio en todas las opciones. "
        "Las diferencias aparecen en viajes más cortos o más largos.",
        S['nota']
    ))

    # Calcular precios
    col_viaje = 4.5*cm
    col_precio = (doc.width - col_viaje) / len(OPCIONES)
    col_widths_cmp = [col_viaje] + [col_precio] * len(OPCIONES)

    headers_cmp = [Paragraph("Viaje", S['cell_hL'])]
    for etiq, *_ in OPCIONES:
        headers_cmp.append(Paragraph(etiq, S['cell_h']))

    tabla_cmp_data = [headers_cmp]
    precios_actuales = []

    for desc, km, min_v in VIAJES:
        fila = [Paragraph(desc, S['cell_L'])]
        es_ref = km == 10 and min_v == 25
        precios_fila = [calcular(b, k, m, km, min_v) for _, b, k, m, _ in OPCIONES]
        if not precios_actuales:
            precios_actuales = [calcular(b, k, m, vkm, vmin) for _, b, k, m, _ in OPCIONES for vkm, vmin in [(3, 10)]]

        precio_actual = precios_fila[0]  # Opción 0 = actual

        for i, precio in enumerate(precios_fila):
            if es_ref:
                fila.append(Paragraph(fmt(precio), S['cell_ref']))
            elif i == 0:
                fila.append(Paragraph(fmt(precio), S['cell_b']))
            else:
                diff = precio - precio_actual
                if abs(diff) < 500:
                    fila.append(Paragraph(fmt(precio), S['cell_b']))
                elif diff > 0:
                    pct = round(diff / precio_actual * 100)
                    fila.append(Paragraph(f"{fmt(precio)}\n+{pct}%", S['verde']))
                else:
                    pct = round(abs(diff) / precio_actual * 100)
                    fila.append(Paragraph(f"{fmt(precio)}\n-{pct}%", S['rojo']))
        tabla_cmp_data.append(fila)

    # Índices de filas de referencia (1-based, row 2 = km=10)
    ref_row = next(i+1 for i, (_, km, _) in enumerate(VIAJES) if km == 10)

    tabla_cmp = Table(tabla_cmp_data, colWidths=col_widths_cmp)
    tabla_cmp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NEGRO),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [GRIS, BLANCO]),
        # Fila referencia
        ('BACKGROUND', (0, ref_row), (-1, ref_row), colors.HexColor('#FFF8E1')),
        ('LINEABOVE',  (0, ref_row), (-1, ref_row), 1, DORADO),
        ('LINEBELOW',  (0, ref_row), (-1, ref_row), 1, DORADO),
        # Columna actual (gris)
        ('BACKGROUND', (1,1), (1,-1), colors.HexColor('#F0F0F0')),
        # Bordes
        ('BOX', (0,0), (-1,-1), 0.5, GRIS_MED),
        ('INNERGRID', (0,0), (-1,-1), 0.3, GRIS_MED),
        ('LINEBELOW', (0,0), (-1,0), 1.5, DORADO),
        # Padding
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(tabla_cmp)
    story.append(Spacer(1, 0.8*cm))

    # ── Análisis / Recomendación ──
    story.append(Paragraph("ANÁLISIS PARA LA DECISIÓN", S['seccion']))

    analisis = [
        ["", "Viajes cortos (<10km)", "Viaje de referencia (10km)", "Viajes largos (>10km)"],
        ["Base más alta (C / D)", "Cobran MÁS → mejor margen", "Precio idéntico", "Cobran MENOS → menor margen"],
        ["Base más baja (A / B)", "Cobran MENOS → menor margen", "Precio idéntico", "Cobran MÁS → mejor margen"],
    ]

    col_w_a = [3.5*cm, 5*cm, 4.5*cm, 4.5*cm]
    t_analisis = Table(analisis, colWidths=col_w_a)
    t_analisis.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NEGRO),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [GRIS, BLANCO]),
        ('LINEBELOW', (0,0), (-1,0), 1.5, DORADO),
        ('BOX', (0,0), (-1,-1), 0.5, GRIS_MED),
        ('INNERGRID', (0,0), (-1,-1), 0.3, GRIS_MED),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,0), F['titulo']),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('TEXTCOLOR', (0,0), (-1,0), BLANCO),
        ('FONTNAME', (0,1), (0,-1), F['bold']),
        ('FONTSIZE', (0,1), (-1,-1), 8.5),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
    ]))
    story.append(t_analisis)
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph(
        "<b>Recomendación:</b> Si la mayoría de servicios son traslados cortos dentro de Bogotá "
        "(aeropuertos, hoteles, reuniones &lt;15km), la Opción C o D mejoran el margen sin que "
        "el cliente lo note en viajes medios. Si hay muchos destinos largos (&gt;20km), "
        "la Opción A o B conserva mejor esos márgenes.",
        S['nota']
    ))

    # ── Pie ──
    story.append(Spacer(1, 0.5*cm))
    linea2 = Table([['']], colWidths=[doc.width])
    linea2.setStyle(TableStyle([('LINEABOVE', (0,0), (-1,0), 1, GRIS_MED)]))
    story.append(linea2)
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "Documento interno — Destinos Express S.A.S. · NIT 900.982.154-2 · "
        "comercial@destinosexpress.com · www.destinosexpress.com",
        E('pie', fontName=F['cuerpo'], fontSize=7.5, textColor=GRIS_TEXT, alignment=TA_CENTER)
    ))

    doc.build(story)
    print(f"✅ PDF generado: {output}")
    return output


if __name__ == '__main__':
    generar()
