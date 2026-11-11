#!/usr/bin/env python3
"""Card «newsletter» KiRun disegnata da zero (nessuna foto, nessun diritto di terzi):
telefono con le notifiche della newsletter in arrivo, fondo blu notte, testo sotto.
Uso: python3 scripts/newsletter_card.py  → assets/social/newsletter-community-1-post.jpg
"""
from social import (BASE, BRAND, ARANCIO, ARANCIO2, BLU, BLU_NOTTE, AZZURRO, CARTA, BIANCO,
                    F, ensure_fonts, tracked, paste_logo)
from PIL import Image, ImageDraw, ImageFilter
import os

W, H, M = 1080, 1350, 72


def shadow(canvas, box, radius, blur=28, alpha=150, dy=18):
    x0, y0, x1, y1 = box
    pad = blur * 3
    lay = Image.new("RGBA", (x1 - x0 + pad * 2, y1 - y0 + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle([pad, pad, pad + x1 - x0, pad + y1 - y0], radius=radius,
                                          fill=(5, 12, 22, alpha))
    canvas.alpha_composite(lay.filter(ImageFilter.GaussianBlur(blur)), (x0 - pad, y0 - pad + dy))


def app_icon(size):
    ic = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(ic).rounded_rectangle([0, 0, size - 1, size - 1], radius=size // 4, fill=BLU_NOTTE + (255,))
    p = Image.open(os.path.join(BRAND, "pittogramma.png")).convert("RGBA")
    pw = int(size * 0.66)
    p = p.resize((pw, int(p.height * pw / p.width)), Image.LANCZOS)
    ic.alpha_composite(p, ((size - p.width) // 2, (size - p.height) // 2))
    return ic


def notifica(canvas, x, y, w, titolo, testo, quando, accento=False):
    h = 150
    shadow(canvas, (x, y, x + w, y + h), 34, blur=18, alpha=120, dy=10)
    card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=34, fill=BIANCO + (250,))
    if accento:
        d.rounded_rectangle([0, 0, 12, h - 1], radius=6, fill=ARANCIO + (255,))
    card.alpha_composite(app_icon(76), (28, 28))
    d.text((126, 24), "KiRun", font=F("SemiBold", 27), fill=BLU_NOTTE)
    qf = F("Regular", 23)
    d.text((w - 28 - qf.getlength(quando), 28), quando, font=qf, fill=AZZURRO)
    d.text((126, 60), titolo, font=F("SemiBold", 29), fill=BLU_NOTTE)
    d.text((126, 98), testo, font=F("Regular", 25), fill=(90, 110, 130))
    canvas.alpha_composite(card, (x, y))


def compose():
    canvas = Image.new("RGBA", (W, H), BLU_NOTTE + (255,))
    # alone morbido dietro il telefono
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([190, 220, 890, 920], fill=BLU + (255,))
    canvas.alpha_composite(glow.filter(ImageFilter.GaussianBlur(90)))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, 0, W, 10], fill=ARANCIO)
    paste_logo(canvas, f"{BRAND}/logo-orizzontale-bianco.png", M, M - 8, 330)

    # telefono
    px0, py0, px1, py1 = 330, 200, 750, 950
    shadow(canvas, (px0, py0, px1, py1), 64, blur=30, alpha=170, dy=24)
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle([px0, py0, px1, py1], radius=64, fill=(12, 22, 36, 255))
    d.rounded_rectangle([px0 + 14, py0 + 14, px1 - 14, py1 - 14], radius=52, fill=BLU + (255,))
    # schermo: sfumatura verso l'arancio in basso
    scr = Image.new("RGBA", (px1 - px0 - 28, py1 - py0 - 28), BLU + (255,))
    grad = Image.new("L", (1, scr.height))
    for yy in range(scr.height):
        grad.putpixel((0, yy), int(90 * max(0, (yy / scr.height) - 0.35) / 0.65))
    warm = Image.new("RGBA", scr.size, ARANCIO + (255,))
    warm.putalpha(grad.resize(scr.size))
    scr.alpha_composite(warm)
    mask = Image.new("L", scr.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, scr.width - 1, scr.height - 1], radius=52, fill=255)
    canvas.paste(scr, (px0 + 14, py0 + 14), mask)
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle([490, py0 + 30, 590, py0 + 58], radius=14, fill=(12, 22, 36, 255))  # isola
    cf = F("SemiBold", 110)
    ora = "7:30"
    d.text(((px0 + px1) / 2 - cf.getlength(ora) / 2, py0 + 80), ora, font=cf, fill=BIANCO)
    gf = F("Medium", 28)
    giorno = "giovedì"
    d.text(((px0 + px1) / 2 - gf.getlength(giorno) / 2, py0 + 208), giorno, font=gf, fill=CARTA)

    # notifiche che escono dai bordi del telefono
    nx, nw = 170, 740
    notifica(canvas, nx, 480, nw, "Prevendita riservata agli iscritti", "La nuova trasferta apre prima per te", "ora")
    notifica(canvas, nx, 650, nw, "Un'offerta per la community", "Solo via email, non la trovi sui social", "2 min")
    notifica(canvas, nx, 820, nw, "La newsletter del giovedì", "Gare, viaggi e consigli di allenamento", "7:30")

    # testo, stessa gerarchia delle card rubrica
    draw = ImageDraw.Draw(canvas)
    y = 1040
    tracked(draw, (M, y), "NEWSLETTER KIRUN", F("Medium", 33), ARANCIO2, tracking=4)
    y += 50
    tracked(draw, (M - 4, y), "Entra nella community", F("SemiBold", 78), BIANCO)
    y += 106
    tracked(draw, (M, y), "Offerte riservate e prevendite per gli iscritti", F("Regular", 37), CARTA)
    y += 52
    tracked(draw, (M, y), "Iscriviti gratis su ki-run.it/newsletter", F("Regular", 37), AZZURRO)
    return canvas


if __name__ == "__main__":
    ensure_fonts()
    out = os.path.join(BASE, "assets", "social", "newsletter-community-1-post.jpg")
    compose().convert("RGB").save(out, quality=92, optimize=True)
    print(out)
