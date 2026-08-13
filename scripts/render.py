#!/usr/bin/env python3
"""Renderer di riferimento delle landing evento KiRun.

La STESSA logica va portata nel Code node del workflow n8n "KiRun — Landing Builder":
questo file esiste per poterla sviluppare, testare e rivedere fuori da n8n.

Uso:
    python3 scripts/render.py <dati-evento.json> <output.html> [--soldout]

Il JSON in ingresso è il dato Airtable normalizzato (vedi scripts/sample-data/).
Le regole di selezione e presentazione del listino sono in docs/REGOLE-LISTINO.md.
"""

import html
import json
import re
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

MESI = ["", "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
        "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]

GIORNI = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]


def data_gara_it(iso):
    """'2027-02-21' -> 'domenica 21 febbraio' (l'anno lo dicono già le date del viaggio)."""
    y, m, d = (int(x) for x in iso.split("-"))
    return f"{GIORNI[date(y, m, d).weekday()]} {d} {MESI[m]}"

UNITA = {
    "numero_partecipanti": "a persona",
    "numero_runner": "per runner",
    "per_pratica": "per pratica",
    "fixed": "importo fisso",
}

RE_PREZZO_NEL_TESTO = re.compile(r"€|EUR\b|\b\d+[.,]?\d*\s*euro\b", re.IGNORECASE)


def esc(s):
    return html.escape(str(s or ""), quote=True)


def euro(n):
    """Formato italiano: € 390 oppure € 390,50."""
    if n == int(n):
        intero = f"{int(n):,}".replace(",", ".")
        return f"€ {intero}"
    return "€ " + f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def data_it(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    return f"{d} {MESI[m]} {y}"


def trip_dates(inizio, fine):
    yi, mi, di = (int(x) for x in inizio.split("-"))
    yf, mf, df = (int(x) for x in fine.split("-"))
    if (yi, mi) == (yf, mf):
        return f"{di}–{df} {MESI[mf]} {yf}"
    if yi == yf:
        return f"{di} {MESI[mi]} – {df} {MESI[mf]} {yf}"
    return f"{data_it(inizio)} – {data_it(fine)}"


def righe(testo):
    """Campo multiline Airtable → lista di voci non vuote."""
    return [r.strip() for r in (testo or "").splitlines() if r.strip()]


def paragrafi_html(testo):
    return "".join(f"<p>{esc(r)}</p>" for r in righe(testo))


def in_finestra(servizio, oggi):
    dal, al = servizio.get("valido_dal"), servizio.get("valido_al")
    if dal and dal > oggi:
        return False
    if al and al < oggi:
        return False
    return True


def build(dati, forza_soldout=False):
    """Dati Airtable normalizzati → (render model, warnings). Nessun dato inventato:
    le sezioni senza contenuto non compaiono."""
    ev = dati["evento"]
    oggi = dati.get("oggi") or date.today().isoformat()
    warnings = []

    # --- listino (docs/REGOLE-LISTINO.md) ---
    servizi = [s for s in dati["servizi"]
               if s.get("active") and (s.get("prezzo") or 0) > 0 and in_finestra(s, oggi)]
    servizi.sort(key=lambda s: s.get("order") or 999)

    nomi_visti = set()
    price_rows = []
    for s in servizi:
        if s["quantity_basis"] in ("fixed", "per_pratica") and not s.get("quantity_fixed"):
            warnings.append(f"'{s['service_name']}' ({s['service_code']}): quantity_basis "
                            f"{s['quantity_basis']} senza quantity_fixed — nel contratto la riga può sparire")
        chiave = s["service_name"].strip().lower()
        if chiave in nomi_visti:
            warnings.append(f"nome servizio duplicato in pagina: '{s['service_name']}' — differenziare in Airtable")
        nomi_visti.add(chiave)
        price_rows.append({
            "nome": s["service_name"],
            "prezzo": s["prezzo"],
            "unita": UNITA.get(s["quantity_basis"], ""),
            "quota": bool(s.get("mandatory")),
        })

    pacchetto = next((r for r in price_rows if r["quota"]), None)
    if not pacchetto:
        warnings.append("nessuna riga package valida: pagina senza prezzi (quote su richiesta)")

    # --- prezzi nei campi editoriali: mai ---
    for campo in ("landing_headline", "landing_intro", "dettaglio_titolo",
                  "dettaglio_periodo", "dettaglio_hotel"):
        if RE_PREZZO_NEL_TESTO.search(ev.get(campo) or ""):
            warnings.append(f"possibile prezzo nel campo editoriale '{campo}': i prezzi vivono solo nel listino")

    sold_out = bool(ev.get("landing_sold_out")) or forza_soldout

    # --- chips: solo dati presenti ---
    chips = []
    if ev.get("data_gara"):
        chips.append(f"Gara: {data_gara_it(ev['data_gara'])}")
    if ev.get("durata"):
        chips.append(ev["durata"])
    if ev.get("hotel"):
        chips.append(ev["hotel"])
    if not sold_out and ev.get("pettorali_garantiti"):
        chips.append("Pettorale garantito")

    condizioni = []
    def cond(titolo, corpo):
        if corpo and str(corpo).strip():
            condizioni.append((titolo, str(corpo).strip()))

    cond("Come si conferma la prenotazione", ev.get("condizioni_pagamento"))
    acconto = (ev.get("acconto_testo") or "").strip()
    if ev.get("saldo_entro"):
        acconto = (acconto + f"\nSaldo entro il {data_it(ev['saldo_entro'])}.").strip()
    cond("Acconto e saldo", acconto)
    cond("Penali di annullamento", ev.get("penali_testo"))
    cond("Numero minimo di partecipanti", ev.get("minimo_partecipanti_testo"))
    cond("Assicurazione annullamento", ev.get("polizza_annullamento_testo"))
    cond("Polizza medico/bagaglio", ev.get("polizza_medica_testo"))
    if ev.get("documenti_richiesti"):
        etichette = {"carta_identita": "carta d'identità valida per l'espatrio",
                     "passaporto": "passaporto",
                     "visto": "visto o autorizzazione d'ingresso elettronica (es. ETA), "
                              "da ottenere prima della partenza",
                     "vaccinazioni": "vaccinazioni"}
        voci = [etichette.get(d, d) for d in ev["documenti_richiesti"]]
        cond("Documenti richiesti", "Per questo viaggio serve: " + ", ".join(voci) + ".")

    anno = ev.get("anno") or ""
    titolo = ev["nome_evento"] if str(anno) in ev["nome_evento"] else f"{ev['nome_evento']} {anno}".strip()

    slug = (ev.get("landing_slug") or "").strip() or ev["event_key"].replace("_", "-")

    model = {
        "slug": slug,
        "page_url": f"https://go.ki-run.it/eventi/{slug}/",
        "superhalfs": bool(ev.get("superhalfs")),
        "titolo": titolo,
        "eyebrow": ev.get("landing_headline") or "Viaggio e gara con KiRun",
        "strillo": ev.get("landing_intro") or "",
        "pettorale_etichetta": "Il tuo weekend di gara",
        "trip_dates": trip_dates(ev["data_inizio"], ev["data_fine"]),
        "chips": chips,
        "sold_out": sold_out,
        "quota_da": euro(pacchetto["prezzo"]) if pacchetto else "",
        "nome_pacchetto": f"Pacchetto {ev['nome_pacchetto']}" if ev.get("nome_pacchetto") else "Il pacchetto",
        "dettaglio": ev.get("dettaglio_periodo") or ev.get("dettaglio_titolo") or "",
        "price_rows": price_rows,
        "hotel": ev.get("hotel") or "",
        "hotel_dettaglio": (ev.get("dettaglio_hotel") or "").strip(),
        "included": righe(ev.get("incluso")),
        "excluded": righe(ev.get("non_incluso")),
        "programma": ev.get("programma_testo") or "",
        "conditions": condizioni,
        "cta_url": dati.get("cta_url") or "",
        "contact_url": dati.get("contact_url") or "https://ki-run.it",
        "meta_description": ev.get("landing_meta_description")
            or f"{titolo} con KiRun: viaggio, hotel e assistenza per la tua gara.",
        "updated_at": data_it(oggi),
    }
    return model, warnings


def render(model):
    tpl = (REPO / "templates" / "evento.html").read_text(encoding="utf-8")

    if model["sold_out"]:
        cta_url, cta_label = model["contact_url"], "Sold out — lista d'attesa"
        chiusura_titolo = "Questo viaggio è sold out"
        chiusura_testo = ("I pettorali disponibili sono finiti. Scrivici per la lista "
                          "d'attesa o per la prossima edizione.")
    else:
        cta_url, cta_label = model["cta_url"], "Prenota"
        chiusura_titolo = "Pronto a partire?"
        chiusura_testo = "La prenotazione si completa online in pochi minuti."

    rows = []
    for r in model["price_rows"]:
        classe = "riga-prezzo quota" if r["quota"] else "riga-prezzo"
        unita = "a persona in camera doppia" if r["quota"] else r["unita"]
        unita_html = f'<span class="unita">{esc(unita)}</span>' if unita else ""
        rows.append(f'<div class="{classe}"><span class="nome">{esc(r["nome"])}{unita_html}</span>'
                    f'<span class="importo">{esc(euro(r["prezzo"]))}</span></div>')

    conds = "".join(
        f"<details><summary>{esc(t)}</summary><p>{esc(c)}</p></details>"
        for t, c in model["conditions"])

    valori = {
        "slug": model["slug"],
        "page_url": model["page_url"],
        "page_title": f"{model['titolo']} · KiRun",
        "meta_description": model["meta_description"],
        "eyebrow": model["eyebrow"],
        "titolo": model["titolo"],
        "strillo": model["strillo"],
        "pettorale_etichetta": model["pettorale_etichetta"],
        "trip_dates": model["trip_dates"],
        "chips_html": "".join(f'<span class="chip">{esc(c)}</span>' for c in model["chips"]),
        "quota_da": model["quota_da"],
        "cta_url": cta_url,
        "cta_label": cta_label,
        "nome_pacchetto": model["nome_pacchetto"],
        "dettaglio_html": paragrafi_html(model["dettaglio"]),
        "price_rows_html": "".join(rows),
        "hotel": model["hotel"],
        "hotel_dettaglio_html": paragrafi_html(model["hotel_dettaglio"]) or
                                "<p>Hotel selezionato da KiRun per la logistica di gara.</p>",
        "included_html": "".join(f"<li>{esc(v)}</li>" for v in model["included"]),
        "excluded_html": "".join(f"<li>{esc(v)}</li>" for v in model["excluded"]),
        "programma_html": paragrafi_html(model["programma"]),
        "conditions_html": conds,
        "chiusura_titolo": chiusura_titolo,
        "chiusura_testo": chiusura_testo,
        "updated_at": model["updated_at"],
    }

    blocchi = {
        "sold_out": model["sold_out"],
        "strillo": bool(model["strillo"]),
        "prezzi": bool(model["price_rows"]) and any(r["quota"] for r in model["price_rows"]),
        "no_prezzi": not any(r["quota"] for r in model["price_rows"]),
        "quota_da": bool(model["quota_da"]) and not model["sold_out"],
        "hotel": bool(model["hotel"]),
        "programma": bool(model["programma"].strip()),
        "condizioni": bool(model["conditions"]),
        "superhalfs": bool(model.get("superhalfs")),
    }
    for nome, attivo in blocchi.items():
        pattern = re.compile(rf"<!--IF:{nome}-->(.*?)<!--ENDIF:{nome}-->", re.DOTALL)
        tpl = pattern.sub(r"\1" if attivo else "", tpl)

    for chiave, valore in valori.items():
        tpl = tpl.replace("{{" + chiave + "}}", valore)

    residui = re.findall(r"{{\w+}}", tpl)
    if residui:
        raise SystemExit(f"segnaposto non sostituiti: {residui}")
    return tpl


def main():
    argv = [a for a in sys.argv[1:] if a != "--soldout"]
    forza_soldout = "--soldout" in sys.argv
    dati = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    model, warnings = build(dati, forza_soldout)
    out = Path(argv[1])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(model), encoding="utf-8")
    for w in warnings:
        print(f"WARNING: {w}", file=sys.stderr)
    print(f"OK: {out}")


if __name__ == "__main__":
    main()
