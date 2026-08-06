# Regola unica di selezione del listino

Questa è la regola che il **Landing Builder** applica per decidere quali righe di
Servizi Evento mostrare in pagina e come. È scritta qui una volta sola perché è la
stessa regola dei flussi contratto (Alice-dati): se un giorno diverge, è un bug.

## Selezione righe

Una riga di Servizi Evento entra in pagina se **tutte** queste condizioni sono vere:

1. `active` è spuntato.
2. La finestra di validità comprende OGGI:
   - `Valido Dal` vuoto o ≤ oggi, **e** `Valido Al` vuoto o ≥ oggi.
3. Ha `Prezzo per Persona` valorizzato (> 0).

Se dopo il filtro **non resta nessuna riga con `service_code = package`**, la pagina
esce **senza sezione prezzi** ("Quote su richiesta"), il builder manda un alert a
Roberto e lo stato passa a `da_aggiornare`. Mai pubblicare prezzi parziali di un
listino scaduto.

## Presentazione

- Ordinamento per `order` crescente.
- La riga con `mandatory` (il pacchetto) è **la quota**, evidenziata, con etichetta
  "a persona in camera doppia" — è la convenzione dei listini KiRun.
- Le altre righe sono "Servizi su richiesta", con unità derivata da `quantity_basis`:

  | quantity_basis | Etichetta unità |
  | --- | --- |
  | `numero_partecipanti` | a persona |
  | `numero_runner` | per runner |
  | `per_pratica` | per pratica |
  | `fixed` | importo fisso |

- Prezzi in euro, formato italiano: `€ 390` (senza decimali se interi, altrimenti
  due decimali con virgola).

## Warning (il builder non tace mai)

Il contratto oggi salta in silenzio le righe anomale; il builder invece **logga e avvisa**:

- `quantity_basis = fixed` o `per_pratica` **senza** `quantity_fixed` → warning
  (nel contratto quella riga può sparire: trappola nota n. 2 di KIRUN-STATO).
- Due righe attive con lo stesso `service_name` → warning (in pagina risultano
  indistinguibili: differenziare i nomi in Airtable).
- Un importo in euro (regex `€|EUR|\d+\s*euro`) trovato nei campi editoriali
  (`landing_headline`, `landing_intro`, `Dettaglio *`) → warning: i prezzi vivono
  solo nel listino.

## Sold out

`landing_sold_out` (formula su Eventi) è l'unica fonte: contingente pettorali esaurito
(quando tracciato) oppure Stato Evento `sold_out`/`chiuso`. Se true: badge sold out
nell'hero, sezione prezzi conservata (trasparenza), CTA sostituita da "lista d'attesa"
verso il contatto KiRun.
