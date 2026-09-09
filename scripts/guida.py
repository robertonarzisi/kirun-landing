#!/usr/bin/env python3
"""Renderer delle GUIDE EVENTO KiRun (la «guida del runner» che accompagna il voucher).

Diverso dal renderer delle landing commerciali (render.py): qui non ci sono prezzi né CTA
di prenotazione, i contenuti sono scritti a mano in un JSON bilingue e la pagina viene
committata in guide/<slug>/ e en/guide/<slug>/ (fuori dai percorsi scritti da n8n).

Uso:
    python3 scripts/guida.py scripts/guide-data/<evento>.json                 # tutti gli hotel, tutte le lingue
    python3 scripts/guida.py scripts/guide-data/<evento>.json --hotel scandic --lang en

Struttura del JSON:
    {
      "slug": "<slug base>", "updated_at": {...}, "hero_credit": "...", "superhalfs": true,
      "hotels": {
        "<chiave>": {"slug": "<slug pagina>", "lingue": ["it","en"], "hero_slug": "<opz.>",
                     "it": {<snippet e blocchi dell'hotel>}, "en": {...}}
      },
      "it": {<contenuto condiviso>}, "en": {...}
    }

Il contenuto condiviso può contenere segnaposto `{{hotel:chiave}}` dentro le stringhe
(sostituiti con lo snippet dell'hotel nella stessa lingua) e blocchi
`{"tipo": "hotel_blocchi", "chiave": "..."}` che si espandono nella lista di blocchi
definita dall'hotel. Un segnaposto senza snippet fa fallire il build: ogni hotel deve
dichiarare tutte le chiavi, anche vuote. L'HTML inline è fidato: viene dal repo.
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

RE_TOKEN = re.compile(r"{{hotel:(\w+)}}")


def esc(s):
    return html.escape(str(s or ""), quote=True)


def url_pagina(slug, lang):
    return f"https://go.ki-run.it/{'en/' if lang == 'en' else ''}guide/{slug}/"


def sostituisci(valore, snippet):
    """Applica i segnaposto {{hotel:chiave}} ricorsivamente a stringhe, liste e dict."""
    if isinstance(valore, str):
        def rep(m):
            k = m.group(1)
            if k not in snippet:
                raise SystemExit(f"snippet hotel mancante: '{k}'")
            v = snippet[k]
            if not isinstance(v, str):
                raise SystemExit(f"lo snippet '{k}' non è una stringa (usa hotel_blocchi per i blocchi)")
            return v
        return RE_TOKEN.sub(rep, valore)
    if isinstance(valore, list):
        return [sostituisci(v, snippet) for v in valore]
    if isinstance(valore, dict):
        return {k: sostituisci(v, snippet) for k, v in valore.items()}
    return valore


def blocco(b, snippet):
    t = b["tipo"]
    if t == "hotel_blocchi":
        lista = snippet.get(b["chiave"])
        if not isinstance(lista, list):
            raise SystemExit(f"hotel_blocchi '{b['chiave']}' non definito dall'hotel")
        return "".join(blocco(sostituisci(x, snippet), snippet) for x in lista)
    if t == "p":
        return f"<p>{b['html']}</p>"
    if t == "h3":
        return f"<h3>{esc(b['testo'])}</h3>"
    if t in ("ul", "ol"):
        voci = "".join(f"<li>{v}</li>" for v in b["voci"] if v.strip())
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
        voci = "".join(f"<div><dt>{esc(v['k'])}</dt><dd>{v['v']}</dd></div>" for v in b["voci"] if v["v"].strip())
        return f"<dl class='fatti'>{voci}</dl>"
    if t == "schede":
        voci = "".join(f"<div class='scheda'><h3>{esc(v['titolo'])}</h3>{v['html']}</div>" for v in b["voci"])
        return f"<div class='schede'>{voci}</div>"
    raise SystemExit(f"tipo di blocco sconosciuto: {t}")


def sezione(s, snippet):
    corpo = "".join(blocco(b, snippet) for b in s["blocchi"])
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


def render(dati, hotel, lang):
    snippet = hotel[lang]
    d = sostituisci(dati[lang], snippet)
    L = ETICHETTE[lang]
    tpl = (REPO / "templates" / "guida.html").read_text(encoding="utf-8")
    slug = hotel["slug"]
    alt_lang = L["alt_lang"]
    has_alt = alt_lang in hotel["lingue"]
    valori = {
        "lang": lang,
        "hero_slug": hotel.get("hero_slug") or dati["slug"],
        "page_url": url_pagina(slug, lang),
        "page_title": f"{d['hero']['titolo']} · {d['hero']['eyebrow']} · KiRun",
        "meta_description": d["meta_description"],
        "eyebrow": d["hero"]["eyebrow"],
        "titolo": d["hero"]["titolo"],
        "strillo": d["hero"]["strillo"],
        "chips_html": "".join(f"<span class='chip{' evidenza' if i == 0 else ''}'>{esc(c)}</span>"
                              for i, c in enumerate(d["hero"]["chips"])),
        "alt_lang_url": url_pagina(slug, alt_lang).replace("https://go.ki-run.it", "") if has_alt else "",
        "alt_lang_label": L["alt"],
        "aside_html": aside(d, lang, d["sezioni"]),
        "sezioni_html": "".join(sezione(s, snippet) for s in d["sezioni"]),
        "aggiornato_label": L["aggiornato"],
        "updated_at": dati["updated_at"][lang] if isinstance(dati["updated_at"], dict) else dati["updated_at"],
        "disclaimer": L["disclaimer"],
        "community": L["community"],
        "credit_label": L["credit"],
        "credit_html": dati.get("hero_credit", ""),
    }
    blocchi = {"has_alt": has_alt, "superhalfs": bool(dati.get("superhalfs")),
               "credit": bool(dati.get("hero_credit"))}
    for nome, attivo in blocchi.items():
        tpl = re.compile(rf"<!--IF:{nome}-->(.*?)<!--ENDIF:{nome}-->", re.DOTALL).sub(r"\1" if attivo else "", tpl)
    for k, v in valori.items():
        tpl = tpl.replace("{{" + k + "}}", v)
    residui = re.findall(r"{{[\w:]+}}", tpl)
    if residui:
        raise SystemExit(f"segnaposto non sostituiti: {residui}")
    return tpl


def main():
    argv = sys.argv[1:]
    filtro = {}
    for opt in ("--lang", "--hotel"):
        if opt in argv:
            i = argv.index(opt)
            filtro[opt] = argv[i + 1]
            del argv[i:i + 2]
    dati = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    hotels = dati.get("hotels") or {"_": {"slug": dati["slug"], "lingue": [l for l in ("it", "en") if l in dati], "it": {}, "en": {}}}
    for chiave, hotel in hotels.items():
        if filtro.get("--hotel") and chiave != filtro["--hotel"]:
            continue
        for lang in hotel["lingue"]:
            if filtro.get("--lang") and lang != filtro["--lang"]:
                continue
            out = REPO / ("en/guide" if lang == "en" else "guide") / hotel["slug"] / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(render(dati, hotel, lang), encoding="utf-8")
            print(f"OK: {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
