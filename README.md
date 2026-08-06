# kirun-landing

Landing page pubbliche degli eventi KiRun, pubblicate su **https://go.ki-run.it** via GitHub Pages.

## Come funziona

- I dati vivono in Airtable ("KiRun — Operations" → Eventi + Servizi Evento). Questo repo
  contiene solo l'output HTML e gli asset: **nessuna logica di business**.
- Il workflow n8n **"KiRun — Landing Builder"** legge Airtable, renderizza `templates/evento.html`
  e committa qui. Ogni publish è un commit: la storia git è l'audit trail di cosa era
  online e quando. Rollback = revert.
- `landing_status` su Airtable è il gate: `pubblicata` → `/eventi/<slug>/`,
  `pronta_per_verifica` → `/anteprima/<slug>/` (noindex), `ritirata` → pagina di cortesia.

## Chi scrive dove

| Percorso | Chi lo tocca |
| --- | --- |
| `eventi/`, `anteprima/` | **Solo n8n** (output del builder — non editare a mano) |
| `templates/`, `assets/`, `docs/` | Persone (Roberto + Claude Code) |
| `scripts/` | Implementazione di riferimento del renderer (la stessa logica del Code node n8n) |

## Regole

1. **Repo pubblico: solo contenuti già pubblici.** Mai dati personali, mai clienti,
   mai credenziali, mai margini/costi fornitore (il builder pubblica solo i prezzi di vendita).
2. I prezzi arrivano **solo** da Servizi Evento secondo `docs/REGOLE-LISTINO.md`.
   Mai prezzi scritti a mano nell'HTML o nei campi testo di Airtable.
3. Il logo KiRun si usa solo come asset originale del Brand Manual (mai ridisegnato).
   Finché l'asset non è nel repo, il template usa un wordmark testuale segnaposto.
4. Fase 1–2: tutte le pagine hanno `noindex` (la landing serve la conversione da email).

## Sviluppo locale

```bash
python3 scripts/render.py scripts/sample-data/valencia-marathon-2026.json anteprima/valencia-marathon-2026/index.html
```
