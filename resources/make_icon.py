#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Genera el icono de SchematicBuq (resources/icons/app.ico)."""
import os
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(__file__), "icons", "app.ico")
SIZE = 512


def rounded_rect(draw, box, radius, fill, outline=None, width=0):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def make(size=SIZE):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    s = size / 512.0

    # Fondo: cuadrado redondeado con degradado simulado
    rounded_rect(d, [8 * s, 8 * s, 504 * s, 504 * s], 96 * s, (16, 24, 40, 255))
    # Borde
    rounded_rect(d, [8 * s, 8 * s, 504 * s, 504 * s], 96 * s, None, (56, 189, 248, 255), int(8 * s))

    # Pistas de circuito (verde)
    green = (52, 211, 153, 255)
    lw = int(16 * s)
    # pistas horizontales/verticales
    d.line([(70 * s, 150 * s), (210 * s, 150 * s)], fill=green, width=lw)
    d.line([(210 * s, 150 * s), (210 * s, 250 * s)], fill=green, width=lw)
    d.line([(70 * s, 330 * s), (150 * s, 330 * s)], fill=green, width=lw)
    d.line([(150 * s, 330 * s), (150 * s, 400 * s)], fill=green, width=lw)
    d.line([(150 * s, 400 * s), (300 * s, 400 * s)], fill=green, width=lw)

    # Pads (círculos) en los extremos de las pistas
    def pad(cx, cy, r=22):
        d.ellipse([(cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s],
                  fill=(250, 204, 21, 255), outline=(120, 90, 0, 255), width=int(4 * s))

    pad(70, 150)
    pad(210, 250)
    pad(300, 400)

    # Símbolo de resistencia (zigzag) arriba a la derecha
    amber = (251, 191, 36, 255)
    zw = int(12 * s)
    pts = [(300 * s, 120 * s), (330 * s, 95 * s), (360 * s, 145 * s),
           (390 * s, 95 * s), (420 * s, 145 * s), (450 * s, 120 * s)]
    d.line(pts, fill=amber, width=zw, joint="curve")

    # Lupa (magnifier) en la parte inferior derecha
    cx, cy, r = 360 * s, 320 * s, 95 * s
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(56, 189, 248, 255), width=int(20 * s))
    # cristal
    d.ellipse([cx - r + 8 * s, cy - r + 8 * s, cx + r - 8 * s, cy + r - 8 * s],
              fill=(56, 189, 248, 45))
    # mango
    d.line([(cx + r * 0.7, cy + r * 0.7), (cx + r * 1.6, cy + r * 1.6)],
           fill=(56, 189, 248, 255), width=int(26 * s))

    return img


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    base = make(512)
    sizes = [256, 128, 64, 48, 32, 16]
    base.save(OUT, format="ICO", sizes=[(x, x) for x in sizes])
    # También PNG para vista previa
    base.save(os.path.join(os.path.dirname(OUT), "app.png"))
    print("Icono generado:", OUT)


if __name__ == "__main__":
    main()