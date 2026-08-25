#!/usr/bin/env python3
"""Grafiche social KiRun — genera assets/social/<slug>-{post,story}.jpg.
Uso: python3 scripts/social.py  (rigenera tutti gli eventi in EVENTS)
Font: scarica Poppins in scripts/fonts/ al primo run (licenza OFL).

Grafiche social KiRun — post 1080x1350 e story 1080x1920, parametriche per evento.
Palette e componenti dal brand manual / kirun.css della landing.
Il nastro evidenza viene dal campo Airtable Eventi."Evidenza Social" (passato qui a mano
finché la generazione non è agganciata al giro Cora)."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # radice repo
FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
BRAND = os.path.join(BASE, "assets", "brand")
HERO_DIR = os.path.join(BASE, "assets", "hero")

ARANCIO = (247, 103, 22)
ARANCIO2 = (248, 132, 15)
BLU = (32, 58, 93)
BLU_NOTTE = (22, 41, 63)
AZZURRO = (145, 171, 189)
CARTA = (247, 249, 251)
BIANCO = (255, 255, 255)

EVENTS = {
    "cardiff-half-marathon-2026": {
        "kicker": "RUN + TRAVEL · MEZZA MARATONA",
        "title": ["Cardiff Half", "Marathon 2026"],
        "info1": "2–5 ottobre 2026 · 4 giorni / 3 notti",
        "info2": "Clayton Hotel Cardiff · staff KiRun al seguito",
        "ribbon": "ULTIMI 2 PETTORALI DISPONIBILI",   # Eventi."Evidenza Social"
        "ribbon_style": "evidenza",
        "cta": "Prenota",
        "superhalfs": True,
    },
    "sevilla-marathon-2027": {
        "kicker": "RUN + TRAVEL · MARATONA",
        "title": ["Sevilla", "Marathon 2027"],
        "info1": "19–22 febbraio 2027 · 4 giorni / 3 notti",
        "info2": "Catalonia Santa Justa · staff KiRun al seguito",
        "ribbon": None,
        "ribbon_style": None,
        "cta": "Prenota",
        "superhalfs": False,
    },
    "valencia-marathon-2026": {
        "kicker": "RUN + TRAVEL · MARATONA",
        "title": ["Valencia", "Marathon 2026"],
        "info1": "4–7 dicembre 2026 · 4 giorni / 3 notti",
        "info2": "Scrivici per la lista d'attesa",
        "ribbon": "SOLD OUT",
        "ribbon_style": "sold_out",
        "cta": None,
        "superhalfs": False,
    },
    "valencia-half-marathon-2026": {
        "kicker": "RUN + TRAVEL · MEZZA MARATONA",
        "title": ["Valencia Half", "Marathon 2026"],
        "info1": "23–26 ottobre 2026 · 4 giorni / 3 notti",
        "info2": "Holiday Inn Ciudad de las Ciencias · staff KiRun",
        "ribbon": None,
        "ribbon_style": None,
        "cta": "Prenota",
        "superhalfs": True,
    },
    "lisbon-half-marathon-2027": {
        "kicker": "RUN + TRAVEL · MEZZA MARATONA",
        "title": ["Lisbona Half", "Marathon 2027"],
        "info1": "5–8 marzo 2027 · 4 giorni / 3 notti",
        "info2": "Hotel 3K Barcelona · staff KiRun al seguito",
        "ribbon": None,
        "ribbon_style": None,
        "cta": "Prenota",
        "superhalfs": True,
    },
    "prague-half-marathon-2027": {
        "kicker": "RUN + TRAVEL · MEZZA MARATONA",
        "title": ["Prague Half", "Marathon 2027"],
        "info1": "2–5 aprile 2027 · 4 giorni / 3 notti",
        "info2": "B&B Hotel Prague City 3* · staff KiRun al seguito",
        "ribbon": None,
        "ribbon_style": None,
        "cta": "Prenota",
        "superhalfs": True,
    },
}

def ensure_fonts():
    os.makedirs(FONTS, exist_ok=True)
    import urllib.request
    for w in ("Regular", "Medium", "SemiBold"):
        dest = os.path.join(FONTS, f"Poppins-{w}.ttf")
        if not os.path.exists(dest):
            urllib.request.urlretrieve(
                f"https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-{w}.ttf", dest)

def F(weight, size):
    return ImageFont.truetype(os.path.join(FONTS, f"Poppins-{weight}.ttf"), size)

def tracked(draw, xy, text, font, fill, tracking=0, shadow=None):
    """Testo con letterspacing e ombra morbida opzionale (come drop-shadow della landing)."""
    x, y = xy
    if shadow:
        for ch in text:
            draw.text((x + 2, y + 3), ch, font=font, fill=shadow)
            x += font.getlength(ch) + tracking
        x = xy[0]
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += font.getlength(ch) + tracking
    return x

def tracked_len(text, font, tracking=0):
    return sum(font.getlength(c) + tracking for c in text) - (tracking if text else 0)

def crop_cover(img, w, h, focus_y=0.58):
    """Ritaglia l'immagine per coprire w x h, fuoco verticale come nella landing (center 58%)."""
    sw, sh = img.size
    scale = max(w / sw, h / sh)
    nw, nh = int(sw * scale + 0.5), int(sh * scale + 0.5)
    img = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - w) // 2
    top = int((nh - h) * focus_y)
    top = max(0, min(top, nh - h))
    return img.crop((left, top, left + w, top + h))

def gradient_overlay(size, color, y_start_frac, max_alpha):
    """Velo scuro che sale dal basso, trasparente sopra y_start_frac."""
    w, h = size
    mask = Image.new("L", (1, h), 0)
    y0 = int(h * y_start_frac)
    for y in range(y0, h):
        t = (y - y0) / max(1, h - y0)
        mask.putpixel((0, y), int(max_alpha * (t ** 1.25)))
    mask = mask.resize((w, h))
    layer = Image.new("RGBA", (w, h), color + (255,))
    layer.putalpha(mask)
    return layer

def paste_logo(canvas, path, x, y, width):
    logo = Image.open(path).convert("RGBA")
    ratio = width / logo.width
    logo = logo.resize((width, int(logo.height * ratio)), Image.LANCZOS)
    alpha = logo.split()[3].point(lambda a: int(a * 0.45))
    black = Image.new("RGBA", logo.size, (10, 20, 32, 255))
    black.putalpha(alpha)
    sh = black.filter(ImageFilter.GaussianBlur(6))
    canvas.alpha_composite(sh, (x + 2, y + 4))
    canvas.alpha_composite(logo, (x, y))
    return logo.size

def cta_pill(canvas, draw, x, y, text, font, pad_x=64, pad_y=24):
    tw = tracked_len(text, font)
    w, h = int(tw + pad_x * 2), int(font.size + pad_y * 2)
    pill = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(pill).rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=ARANCIO + (255,))
    canvas.alpha_composite(pill, (x, y))
    ImageDraw.Draw(canvas).text((x + pad_x, y + pad_y - 4), text, font=font, fill=BIANCO)
    return h

def ribbon_tag(canvas, x, y, text, style):
    """Nastro a parallelogramma, stile pettorale: evidenza = bianco con bordo arancio,
    sold_out = arancio pieno."""
    font = F("SemiBold", 31)
    tr = 3
    tw = tracked_len(text, font, tr)
    pad_x, h, skew = 36, 62, 14
    w = int(tw + pad_x * 2 + skew)
    tag = Image.new("RGBA", (w + 8, h + 10), (0, 0, 0, 0))
    d = ImageDraw.Draw(tag)
    pts = [(skew, 0), (w, 0), (w - skew, h), (0, h)]
    if style == "sold_out":
        d.polygon(pts, fill=ARANCIO + (255,))
        fg = BIANCO
    else:
        d.polygon(pts, fill=BIANCO + (247,))
        d.polygon([(skew, 0), (skew + 10, 0), (10, h), (0, h)], fill=ARANCIO + (255,))
        fg = BLU
    sh = Image.new("RGBA", tag.size, (0, 0, 0, 0))
    mask = Image.new("L", tag.size, 0)
    ImageDraw.Draw(mask).polygon(pts, fill=120)
    dark = Image.new("RGBA", tag.size, (10, 20, 32, 255))
    dark.putalpha(mask)
    canvas.alpha_composite(dark.filter(ImageFilter.GaussianBlur(7)), (x + 2, y + 5))
    canvas.alpha_composite(tag, (x, y))
    tracked(ImageDraw.Draw(canvas), (x + skew + pad_x - 4, y + (h - font.size) // 2 - 4), text, font, fg, tracking=tr)
    return h

def compose(slug, fmt):
    ev = EVENTS[slug]
    W, H = (1080, 1350) if fmt == "post" else (1080, 1920)
    M = 72
    hero = Image.open(os.path.join(HERO_DIR, f"{slug}.jpg")).convert("RGB")

    if fmt == "post":
        canvas = Image.new("RGBA", (W, H))
        canvas.paste(crop_cover(hero, W, H).convert("RGBA"), (0, 0))
        canvas.alpha_composite(gradient_overlay((W, H), BLU_NOTTE, 0.30, 250))
        photo_bottom = H
    else:
        ph = 1150
        canvas = Image.new("RGBA", (W, H), BLU_NOTTE + (255,))
        canvas.paste(crop_cover(hero, W, ph).convert("RGBA"), (0, 0))
        canvas.alpha_composite(gradient_overlay((W, ph), BLU_NOTTE, 0.55, 255))
        photo_bottom = ph

    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, 0, W, 10], fill=ARANCIO)

    paste_logo(canvas, f"{BRAND}/logo-orizzontale-bianco.png", M, M - 8, 330)
    if ev["superhalfs"]:
        badge = Image.open(f"{BRAND}/superhalfs-bianco.png").convert("RGBA")
        bw = 150
        badge = badge.resize((bw, int(badge.height * bw / badge.width)), Image.LANCZOS)
        canvas.alpha_composite(badge, (W - M - bw, M - 8))

    shadow = (10, 20, 32, 160)
    kicker_f = F("Medium", 33)
    head_f = F("SemiBold", 97)
    info_f = F("Regular", 37)
    cta_f = F("SemiBold", 34)

    # altezza del blocco testo, per ancorarlo in basso (post) o nel pannello (story)
    block = 62 + 112 * len(ev["title"]) + 18 + 56
    block += 76 + 82 if ev["cta"] else 56
    if ev["ribbon"]:
        block += 62 + 26

    if fmt == "post":
        y = H - block - 62
    else:
        y = photo_bottom + max(56, (H - photo_bottom - block) // 3)

    if ev["ribbon"]:
        ribbon_tag(canvas, M, y, ev["ribbon"], ev["ribbon_style"])
        y += 62 + 26

    tracked(draw, (M, y), ev["kicker"], kicker_f, ARANCIO2, tracking=4, shadow=shadow)
    y += 62
    for line in ev["title"]:
        tracked(draw, (M - 4, y), line, head_f, BIANCO, shadow=shadow)
        y += 112

    y += 18
    tracked(draw, (M, y), ev["info1"], info_f, CARTA, shadow=shadow)
    y += 56
    tracked(draw, (M, y), ev["info2"], info_f, AZZURRO, shadow=shadow)

    if ev["cta"]:
        y += 76
        cta_pill(canvas, draw, M, y, ev["cta"], cta_f)

    out = os.path.join(BASE, "assets", "social", f"{slug}-{fmt}.jpg")
    canvas.convert("RGB").save(out, quality=92, optimize=True)
    print(out)

ensure_fonts()
import sys
slugs = sys.argv[1:] or list(EVENTS)
for slug in slugs:
    for fmt in ("post", "story"):
        compose(slug, fmt)
