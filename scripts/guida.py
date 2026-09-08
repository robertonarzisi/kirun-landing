#!/usr/bin/env python3
"""Renderer delle GUIDE EVENTO KiRun (la «guida del runner» che accompagna il voucher).

Diverso dal renderer delle landing commerciali (render.py): qui non ci sono prezzi né CTA
di prenotazione, i contenuti sono scritti a mano in un JSON bilingue e la pagina viene
committata in guide/<slug>/ e en/guide/<slug>/ (fuori dai percorsi scritti da n8n).

Uso:
    python3 scripts/guida.py scripts/guide-data/<slug>.json          # IT + EN
    python3 scripts/guida.py scripts/guide-data/<slug>.json --lang it

Il JSON ha la forma {"slug": ..., "updated_at": ..., "hero_credit": ..., "it": {...}, "en": {...}}.
Ogni lingua: hero (eyebrow, titolo, strillo, chips[]), aside (in_breve[], link_ufficiali[],
assistenza), sezioni[] fatte di blocchi tipizzati (p, h3, ul, ol, box, tabella, timeline,
link, fatti, schede). L'HTML inline nei testi è fidato: viene dal repo, non da utenti.
"""

import html
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

ETICHETTE = {
    "it": {"indice": "In questa guida", "in_breve": "In breve", "link": "Link ufficiali",
           "assistenza": "Assistenza KiRun", "alt": "English version", "alt_lang": "en",
           "aggiornato": "Informazioni verificate sul sito ufficiale il",
           "disclaimer": "Orari e regole possono cambiare fino al giorno della gara: fanno fede i canali ufficiali dell'organizzatore.",
           "community": "entra nella community", "credit": "Foto"},
    "en": {"indice": "In this guide", "in_breve": "At a glance", "link": "Official links",
           "assistenza": "KiRun support", "alt": "Versione italiana", "alt_lang": "it",
           "aggiornato": "Information checked on the official website on",
           "disclaimer": "Times and rules can change up to race day: the organiser's official channels take precedence.",
           "community": "join the community", "credit": "Photo"},
}


def esc(s):
    return html.escape(str(s or ""), quote=True)


def url_pagina(slug, lang):
    return f"https://go.ki-run.it/{'en/' if lang == 'en' else ''}guide/{slug}/"


def blocco(b):
    t = b["tipo"]
    if t == "p":
        return f"<p>{b['html']}</p>"
    if t == "h3":
        return f"<h3>{esc(b['testo'])}</h3>"
    if t in ("ul", "ol"):
        voci = "".join(f"<li>{v}</li>" for v in b["voci"])
        return f"<{t} class='lista'>{voci}</{t}>"
    if t == "box":
        stile = b.get("stile", "nota")
        titolo = f"<strong class='box-titolo'>{esc(b['titolo'])}</strong>" if b.get("titolo") else ""
        return f"<div class='box box-{stile}'>{titolo}{b['html']}</div>"
    if t == "tabella":
        head = "".join(f"<th>{esc(c)}</th>" for c in b["intestazione"])
        righe = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in b["righe"])
        nota = f"<p class='tabella-nota'>{b['nota']}</p>" if b.get("nota") else ""
        return f"<div class='tabella-scroll'><table><thead><tr>{head}</tr></thead><tbody>{righe}</tbody></table></div>{nota}"
    if t == "timeline":
        voci = "".join(
            f"<li><span class='quando'>{esc(v['quando'])}</span>"
            f"<div><strong>{esc(v['titolo'])}</strong>{v.get('html', '')}</div></li>"
            for v in b["voci"])
        return f"<ol class='timeline'>{voci}</ol>"
    if t == "link":
        voci = "".join(
            f"<li><a href='{esc(v['url'])}' target='_blank' rel='noopener'>{esc(v['label'])}</a>"
            + (f"<span>{v['desc']}</span>" if v.get("desc") else "") + "</li>"
            for v in b["voci"])
        return f"<ul class='link-ufficiali'>{voci}</ul>"
    if t == "fatti":
        voci = "".join(f"<div><dt>{esc(v['k'])}</dt><dd>{v['v']}</dd></div>" for v in b["voci"])
        return f"<dl class='fatti'>{voci}</dl>"
    if t == "schede":
        voci = "".join(f"<div class='scheda'><h3>{esc(v['titolo'])}</h3>{v['html']}</div>" for v in b["voci"])
        return f"<div class='schede'>{voci}</div>"
    raise SystemExit(f"tipo di blocco sconosciuto: {t}")


def sezione(s):
    corpo = "".join(blocco(b) for b in s["blocchi"])
    etichetta = f"<span class='etichetta'>{esc(s['etichetta'])}</span>" if s.get("etichetta") else ""
    return f"<section id='{esc(s['id'])}'>{etichetta}<h2>{esc(s['titolo'])}</h2><div class='testo'>{corpo}</div></section>"


def aside(d, lang, sezioni):
    L = ETICHETTE[lang]
    a = d["aside"]
    fatti = "".join(f"<div><dt>{esc(v['k'])}</dt><dd>{v['v']}</dd></div>" for v in a["in_breve"])
    toc = "".join(f"<li><a href='#{esc(s['id'])}'>{esc(s['titolo'])}</a></li>" for s in sezioni)
    link = "".join(f"<li><a href='{esc(v['url'])}' target='_blank' rel='noopener'>{esc(v['label'])}</a></li>"
                   for v in a["link_ufficiali"])
    return (
        f"<span class='etichetta'>{L['in_breve']}</span><dl class='fatti fatti-card'>{fatti}</dl>"
        f"<span class='etichetta'>{L['indice']}</span><ol class='indice'>{toc}</ol>"
        f"<span class='etichetta'>{L['link']}</span><ul class='link-card'>{link}</ul>"
        f"<div class='box box-kirun box-card'><strong class='box-titolo'>{L['assistenza']}</strong>{a['assistenza']}</div>"
    )


def render(dati, lang):
    d = dati[lang]
    L = ETICHETTE[lang]
    tpl = (REPO / "templates" / "guida.html").read_text(encoding="utf-8")
    slug = dati["slug"]
    alt_lang = L["alt_lang"]
    valori = {
        "lang": lang,
        "slug": slug,
        "page_url": url_pagina(slug, lang),
        "page_title": f"{d['hero']['titolo']} · {d['hero']['eyebrow']} · KiRun",
        "meta_description": d["meta_description"],
        "eyebrow": d["hero"]["eyebrow"],
        "titolo": d["hero"]["titolo"],
        "strillo": d["hero"]["strillo"],
        "chips_html": "".join(f"<span class='chip{' evidenza' if i == 0 else ''}'>{esc(c)}</span>"
                              for i, c in enumerate(d["hero"]["chips"])),
        "alt_lang_url": url_pagina(slug, alt_lang).replace("https://go.ki-run.it", ""),
        "alt_lang_label": L["alt"],
        "aside_html": aside(d, lang, d["sezioni"]),
        "sezioni_html": "".join(sezione(s) for s in d["sezioni"]),
        "aggiornato_label": L["aggiornato"],
        "updated_at": dati["updated_at"][lang] if isinstance(dati["updated_at"], dict) else dati["updated_at"],
        "disclaimer": L["disclaimer"],
        "community": L["community"],
        "credit_label": L["credit"],
        "credit_html": dati.get("hero_credit", ""),
    }
    blocchi = {"has_alt": alt_lang in dati, "superhalfs": bool(dati.get("superhalfs")),
               "credit": bool(dati.get("hero_credit"))}
    for nome, attivo in blocchi.items():
        tpl = re.compile(rf"<!--IF:{nome}-->(.*?)<!--ENDIF:{nome}-->", re.DOTALL).sub(r"\1" if attivo else "", tpl)
    for k, v in valori.items():
        tpl = tpl.replace("{{" + k + "}}", v)
    residui = re.findall(r"{{\w+}}", tpl)
    if residui:
        raise SystemExit(f"segnaposto non sostituiti: {residui}")
    return tpl


def main():
    argv = sys.argv[1:]
    lingue = ["it", "en"]
    if "--lang" in argv:
        i = argv.index("--lang")
        lingue = [argv[i + 1]]
        del argv[i:i + 2]
    dati = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    for lang in lingue:
        if lang not in dati:
            continue
        out = REPO / ("en/guide" if lang == "en" else "guide") / dati["slug"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render(dati, lang), encoding="utf-8")
        print(f"OK: {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
