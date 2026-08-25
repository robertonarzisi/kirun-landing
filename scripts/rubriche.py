#!/usr/bin/env python3
"""Grafiche per le rubriche editoriali KiRun (progetto social-rubriche).
Due template: card consigli (foto evento + titolo) e quote card (fondo brand).
Riusa palette, font e helper di social.py. Output in assets/social/.
Uso: python3 scripts/rubriche.py  (rigenera tutte le card in CARDS)
"""
from social import (BASE, BRAND, HERO_DIR, ARANCIO, ARANCIO2, BLU_NOTTE, AZZURRO,
                    CARTA, BIANCO, F, ensure_fonts, tracked, tracked_len,
                    crop_cover, gradient_overlay, paste_logo)
from PIL import Image, ImageDraw
import os

# Il nome file è l'identità della card: cambiarlo crea un asset nuovo.
CARDS = {
    "rubrica-allenamento-cardiff-2026": {
        "template": "tip",
        "hero": "cardiff-half-marathon-2026.jpg",
        "kicker": "CONSIGLI PER RUNNER",
        "title": ["Il lungo che fa", "la differenza"],
        "info1": "Meno di sei settimane alla Cardiff Half",
        "info2": "Un lungo a settimana, ritmo comodo, testa alla gara",
    },
    "rubrica-allenamento-valencia-half-2026": {
        "template": "tip",
        "hero": "valencia-half-marathon-2026.jpg",
        "kicker": "CONSIGLI PER RUNNER",
        "title": ["Otto settimane", "alla mezza"],
        "info1": "Valencia Half Marathon · gara domenica 25 ottobre",
        "info2": "Prima i chilometri, poi il ritmo, infine lo scarico",
    },
    "rubrica-motivazione-ritmo": {
        "template": "quote",
        "quote": ["Il ritmo giusto", "è quello che puoi", "tenere anche domani."],
        "kicker": "MOTIVAZIONE",
    },
}


def compose_tip(name, card):
    W, H = 1080, 1350
    M = 72
    hero = Image.open(os.path.join(HERO_DIR, card["hero"])).convert("RGB")
    canvas = Image.new("RGBA", (W, H))
    canvas.paste(crop_cover(hero, W, H).convert("RGBA"), (0, 0))
    # velo più profondo dei post evento: qui il testo è il protagonista
    canvas.alpha_composite(gradient_overlay((W, H), BLU_NOTTE, 0.18, 255))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, 0, W, 10], fill=ARANCIO)
    paste_logo(canvas, f"{BRAND}/logo-orizzontale-bianco.png", M, M - 8, 330)

    shadow = (10, 20, 32, 160)
    kicker_f = F("Medium", 33)
    head_f = F("SemiBold", 97)
    info_f = F("Regular", 37)

    block = 62 + 112 * len(card["title"]) + 18 + 56 + 56
    y = H - block - 72
    tracked(draw, (M, y), card["kicker"], kicker_f, ARANCIO2, tracking=4, shadow=shadow)
    y += 62
    for line in card["title"]:
        tracked(draw, (M - 4, y), line, head_f, BIANCO, shadow=shadow)
        y += 112
    y += 18
    tracked(draw, (M, y), card["info1"], info_f, CARTA, shadow=shadow)
    y += 56
    tracked(draw, (M, y), card["info2"], info_f, AZZURRO, shadow=shadow)
    return canvas


def compose_quote(name, card):
    W, H = 1080, 1350
    M = 72
    canvas = Image.new("RGBA", (W, H), BLU_NOTTE + (255,))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, 0, W, 10], fill=ARANCIO)
    paste_logo(canvas, f"{BRAND}/logo-orizzontale-bianco.png", M, M - 8, 330)

    kicker_f = F("Medium", 33)
    quote_f = F("SemiBold", 88)
    # virgolette grandi come elemento grafico, in arancio
    mark_f = F("SemiBold", 260)

    lines = card["quote"]
    block = 260 + 62 + 118 * len(lines)
    y = (H - block) // 2 + 40
    draw.text((M - 10, y - 120), "“", font=mark_f, fill=ARANCIO)
    y += 170
    tracked(draw, (M, y), card["kicker"], kicker_f, ARANCIO2, tracking=4)
    y += 72
    for line in lines:
        tracked(draw, (M - 4, y), line, quote_f, BIANCO)
        y += 118
    return canvas


if __name__ == "__main__":
    ensure_fonts()
    import sys
    names = sys.argv[1:] or list(CARDS)
    for name in names:
        card = CARDS[name]
        canvas = compose_tip(name, card) if card["template"] == "tip" else compose_quote(name, card)
        out = os.path.join(BASE, "assets", "social", f"{name}-post.jpg")
        canvas.convert("RGB").save(out, quality=92, optimize=True)
        print(out)
