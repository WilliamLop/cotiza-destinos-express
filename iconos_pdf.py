"""
iconos_pdf.py — Íconos PNG para el PDF de Destinos Express
Generados con Pillow, guardados en icons/ y reutilizados en cada build.
"""

import io
import os
from PIL import Image, ImageDraw

DORADO_RGB = (252, 163, 17)
ICONS_DIR  = os.path.join(os.path.dirname(__file__), 'icons')


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _canvas(px=160):
    return Image.new('RGBA', (px, px), (0, 0, 0, 0))

def _c(rgb):
    return rgb + (255,)

def _aa(img):
    """Anti-alias reduciendo a la mitad."""
    return img.resize((img.width // 2, img.height // 2), Image.LANCZOS)

def _save(img, nombre):
    os.makedirs(ICONS_DIR, exist_ok=True)
    ruta = os.path.join(ICONS_DIR, f'{nombre}.png')
    _aa(img).save(ruta, 'PNG')
    return ruta


# ─── ÍCONO: CONDUCTOR (silueta de persona) ────────────────────────────────────

def _gen_conductor(color=DORADO_RGB):
    img = _canvas(160)
    d   = ImageDraw.Draw(img)
    c   = _c(color)

    # Cabeza
    d.ellipse([52, 6, 108, 62], fill=c)

    # Cuello
    d.rectangle([70, 57, 90, 74], fill=c)

    # Hombros + cuerpo (trapecio: ancho arriba, estrecho abajo)
    d.polygon([(20, 74), (140, 74), (120, 152), (40, 152)], fill=c)

    return img


# ─── ÍCONO: COMBUSTIBLE (bomba de gasolina) ───────────────────────────────────

def _gen_combustible(color=DORADO_RGB):
    img = _canvas(160)
    d   = ImageDraw.Draw(img)
    c   = _c(color)

    # Cuerpo principal
    d.rectangle([14, 30, 88, 150], fill=c)

    # Tapa superior
    d.rectangle([8,  16, 94,  36], fill=c)

    # Brazo horizontal (manguera)
    d.rectangle([88, 40, 136, 54], fill=c)

    # Brazo vertical (caída)
    d.rectangle([122, 54, 136, 104], fill=c)

    # Boquilla
    d.rectangle([106, 98, 136, 112], fill=c)

    # Ventana / pantalla en el cuerpo (recorte interno blanco para dar detalle)
    d.rectangle([24, 48, 78, 96], fill=(0, 0, 0, 0))

    return img


# ─── ÍCONO: PEAJES (barrera de peaje) ────────────────────────────────────────

def _gen_peajes(color=DORADO_RGB):
    img = _canvas(160)
    d   = ImageDraw.Draw(img)
    c   = _c(color)

    # Poste izquierdo
    d.rectangle([8,  22, 34, 152], fill=c)

    # Poste derecho
    d.rectangle([126, 22, 152, 152], fill=c)

    # Remate redondeado en postes
    d.ellipse([2,  10, 40,  36], fill=c)
    d.ellipse([120, 10, 158, 36], fill=c)

    # Viga horizontal de la barrera
    d.rectangle([8, 72, 152, 92], fill=c)

    # Marcas de carretera (rayas punteadas abajo)
    for i in range(3):
        lx = 46 + i * 28
        d.rectangle([lx, 132, lx + 16, 150], fill=c)

    return img


# ─── ÍCONO: SEGURO (escudo con checkmark) ────────────────────────────────────

def _gen_seguro(color=DORADO_RGB):
    img = _canvas(160)
    d   = ImageDraw.Draw(img)
    c   = _c(color)

    # Escudo (polígono 7 puntos)
    d.polygon([
        (16, 12),   # esquina superior-izq
        (144, 12),  # esquina superior-der
        (144, 90),  # lado derecho medio
        (124, 122), # derecha-abajo
        (80,  156), # punta inferior
        (36,  122), # izquierda-abajo
        (16,  90),  # lado izquierdo medio
    ], fill=c)

    # Checkmark interior en blanco
    d.line([(44, 86), (66, 110), (116, 52)], fill=(255, 255, 255, 255), width=14)

    return img


# ─── EXPORTAR / ACCEDER ───────────────────────────────────────────────────────

_GENERADORES = {
    'conductor':   _gen_conductor,
    'combustible': _gen_combustible,
    'peajes':      _gen_peajes,
    'seguro':      _gen_seguro,
}

def ruta_icono(nombre: str) -> str | None:
    """Retorna la ruta PNG del ícono, generándolo si no existe."""
    ruta = os.path.join(ICONS_DIR, f'{nombre}.png')
    if not os.path.exists(ruta):
        gen = _GENERADORES.get(nombre)
        if gen is None:
            return None
        ruta = _save(gen(), nombre)
    return ruta

def generar_todos():
    """Genera (o regenera) todos los íconos."""
    return {n: _save(fn(), n) for n, fn in _GENERADORES.items()}
