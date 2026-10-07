# Piano dei test hardware

Elenco delle prove da fare **di persona, accanto alla stampante**. Ogni prova dice cosa preparare, cosa fare, cosa deve succedere e quando fermarsi. In fondo c'è la tabella dei risultati da compilare.

Creato il 2026-10-03. Il codice da provare è il ramo `cfs-upstream-071c813` di `kalico-k2pro` (commit `c1b8613d`), che integra l'aggiornamento 071c813 di Jacob10383. Su richiesta del proprietario il ramo è stato **unito a `k2-pro-openhost` il 2026-10-03, prima di queste prove** (merge `b8a69639`; mirror firmware `k2-openhost` `b8dc5af`). Il CM5 usa `k2-pro-openhost`, quindi le prove qui sotto validano ora il ramo principale.

## Prima di iniziare

- [ ] Sei accanto alla stampante e puoi raggiungere l'interruttore di alimentazione.
- [ ] La stampante è ferma: `print_stats` in `standby`, nessuna pausa attiva.
- [ ] Sul CM5 gira il ramo da provare:
  ```bash
  ssh cm5 'cd ~/klipper && git log --oneline -1'
  ```
  deve essere su `k2-pro-openhost` (era `c1b8613d` quando è stato scritto questo piano; `d2a30105` il 6 ottobre 2026).
- [ ] `macros/print.cfg` sul CM5 contiene `_BOX_RESUME_PREPARE` (le macro nuove; prima del riordino del 7 ottobre 2026: `macros.cfg`).
- [ ] Nessun checkpoint di ripresa in sospeso: `PLR_STATUS` deve riportare `recoverable=False`. Altrimenti `PLR_DISCARD`.
- [ ] CFS (indici slot come in Mainsail, etichette come nei messaggi):

  | Indice | Etichetta | Contenuto attuale |
  |---|---|---|
  | 0 | Box 1, slot 1 | PETG-CF nero |
  | 1 | Box 1, slot 2 | presente, senza profilo |
  | 2 | Box 1, slot 3 | PETG-CF nero |
  | 3 | Box 1, slot 4 | PLA marrone `#6C4E43` |

- [ ] Cambio bobina automatico attivo: `box.runout_swap_enabled = true`.
- [ ] Ricorda che `idle_timeout` è praticamente disattivato: in pausa i riscaldatori restano accesi. Non lasciare la stampante in pausa senza sorveglianza.
- [ ] Console di Mainsail aperta. Annota l'ora d'inizio di ogni prova, così poi si ritrova il punto giusto in `klippy.log`.

### Tornare indietro

Se qualcosa va storto e vuoi tornare alla versione precedente:

```bash
ssh cm5 'cd ~/klipper && git checkout k2-pro-openhost && cp ~/printer_data/config/macros.cfg.before-071c813-* ~/printer_data/config/macros.cfg && curl -s -X POST "http://127.0.0.1:7125/machine/services/restart?service=klipper"'
```

## Ordine delle prove

Vanno fatte in quest'ordine: ogni prova usa cose verificate da quella prima.

| # | Prova | Durata indicativa |
|---|---|---|
| T0 | Homing con `z_align` dopo l'unione | 5 min |
| T1 | Stampa monocolore con associazione automatica, pausa e cambio slot | 30 min |
| T2 | Stampa a due colori con `BOX_PRINT_START`, pausa e ripresa | 45 min |
| T3 | Cambio bobina automatico a fine filamento (due PETG-CF nere) | 40 min |
| T4 | Ripresa dopo interruzione di corrente (monocolore, poi due colori) | 60 min |
| T5 | Cartographer collegato direttamente in USB | sessione a parte |

---

## T0 — Homing con `z_align` dopo l'unione

**Scopo:** l'unione ha toccato `z_align.py` (tolti `ZDOWN`, cambiati i messaggi). Verificare che l'homing sul sensore inferiore funzioni come il 2026-10-03.

**Passi**
1. Piatto libero sotto e sopra.
2. `G28`, attendi la fine, poi `M84`.
3. Ripeti 3 volte.

**Risultato atteso**
- Ogni ciclo riesce al primo tentativo. Il messaggio ora è `MCU z-align attempt 1/5: delta 0.0000mm` (senza "steps").
- Nessun "photoelectric error", nessun rumore anomalo del motore Z.

**Fermati se:** l'homing fallisce o il motore Z fa rumore. Torna indietro e segnalalo.

---

## T1 — Stampa monocolore con associazione automatica, pausa e cambio slot

**Scopo**
- Verificare che una stampa avviata normalmente venga associata da sola allo slot giusto.
- Verificare la nuova pausa e ripresa.
- Verificare che, cambiando slot in pausa, la ripresa scaldi alla temperatura del filamento nuovo.

**Preparazione**
- In OrcaSlicer, un oggetto piccolo (cubo 20 mm o simile) in **PLA** con colore vicino al marrone. Carica il file su Mainsail.
- Nello slot 2 (indice 1) carica una bobina PLA e assegnale un profilo con **temperatura diversa** dal file (per esempio file a 220 °C, profilo slot 2 a 210 °C). Se non hai una seconda bobina PLA, salta i passi 5–7.

**Passi**
1. Avvia la stampa **normalmente** da Mainsail, non dal dialogo di associazione.
2. Controlla: `box.auto_mapping.state = active`, `box.print_mapping.map = {"0": 3}`. In console deve comparire il caricamento di `T0 (Box 1, slot 4)`.
3. Dopo qualche layer premi **PAUSE**.
4. Atteso in pausa: la testa si alza, pulisce l'ugello e va al cestino; ugello a 140 °C, ventole spente.
5. In pausa, carica l'altro PLA: `BOX_SELECT_SLOT SLOT=1`.
6. Premi **RESUME**.
7. Atteso alla ripresa:
   - la testa resta al cestino e scalda alla temperatura del **profilo dello slot 2**: controlla il target dell'estrusore in Mainsail;
   - prepara il filamento, poi torna **una sola volta** sul pezzo e la stampa riprende.
8. Lascia finire la stampa. A fine stampa il filamento viene scaricato (`unload_after_print` è attivo).

**Da controllare**
- Nessun errore `Unknown command` in console.
- In `klippy.log` nessun traceback.
- `box.recovery.blocked = false` a fine stampa.

**Fermati se:** RESUME dà errore e la stampa resta in pausa. Annota il messaggio esatto, non cancellare subito la stampa e chiedi prima di intervenire.

---

## T2 — Stampa a due colori con `BOX_PRINT_START`, pausa e ripresa

**Scopo**
- Associazione esplicita dal dialogo di Mainsail.
- Cambio utensile con spurgo calcolato dalla matrice del file.
- Temperature per utensile del file.
- Pausa e ripresa dopo un cambio colore.

**Preparazione**
- Oggetto a due colori **a cambio per altezza** (es. metà inferiore T0, metà superiore T1), così anche materiali diversi danno solo un pezzo di prova.
- Consigliato: due PLA (slot 4 e slot 2) con **temperature diverse per filamento** in OrcaSlicer (es. 215 °C e 225 °C).
- Alternativa: PLA slot 4 + PETG-CF slot 1. L'adesione tra i due sarà scarsa, ma va bene per la prova.

**Passi**
1. In Mainsail apri il dialogo di associazione CFS sul file (esegue `BOX_PRINT_INFO`).
2. Associa T0 → slot 4 e T1 → slot 2 e avvia. Equivale a `BOX_PRINT_START FILENAME=<file> MAP=0:3,1:1`.
3. Controlla `box.print_mapping`: `filename` impostato e la mappa scelta.
4. Al cambio colore, atteso in console:
   - `Changing T0 (Box 1, slot 4) -> T1 (Box 1, slot 2)`;
   - `Purging ... (slicer matrix T0 -> T1)`;
   - il target dell'estrusore passa alla temperatura di T1.
5. Qualche layer dopo il cambio premi **PAUSE**, attendi 1–2 minuti, poi **RESUME**.
6. Atteso: ripresa alla temperatura di T1, nessuna macchia sul pezzo, la stampa continua con T1.

**Da controllare:** `box.print_mapping.active_tool = 1` e `active_slot = 1` dopo il cambio.

**Fermati se:**
- il cambio carica uno slot diverso da quello associato;
- lo spurgo è palesemente sbagliato (zero o enorme).

---

## T3 — Cambio bobina automatico a fine filamento

**Scopo:** con due bobine uguali (PETG-CF nero negli slot 1 e 3), quando finisce il filamento la stampa deve passare da sola all'altra bobina senza fermarsi. È la correzione del 2026-10-03 più l'aggiornamento della mappa.

**Preparazione**
- Stampa monocolore in **PETG-CF nero** di almeno 30–40 minuti.
- Verifica `box.runout_swap_enabled = true`.
- Forbici o tronchesino a portata di mano.

**Passi**
1. Avvia normalmente. L'associazione automatica sceglie lo slot 1 o lo slot 3: annota quale in `box.print_mapping.map`.
2. Dopo qualche layer **taglia il filamento dello slot attivo tra la bobina e l'ingresso del CFS** e lascia che la coda venga trascinata dentro.
3. Atteso, senza intervento:
   - quando la coda passa il sensore compare `Auto runout swap: Box 1, slot 1 -> Box 1, slot 3` (o viceversa);
   - retrazione e pulizia, la testa va al cestino;
   - viene caricata l'altra bobina, segue uno spurgo, la testa torna sul pezzo e la stampa continua;
   - `Auto runout swap complete: Box 1, slot 3 active`.
4. Controlla:
   - `box.print_mapping.map` ora punta al nuovo slot (es. `{"0": 2}`);
   - lo slot di partenza tiene il suo profilo finché il cambio non è deciso (era il bug corretto), poi lo slot vuoto viene azzerato.

**Fermati se:** la stampa va in pausa invece di cambiare bobina. Annota il motivo mostrato e lo stato di `box.recovery`, poi prova **RESUME**: deve ritentare da solo.

**Dopo la prova:** togli il pezzo di filamento rimasto nel percorso dello slot svuotato e ricarica la bobina.

---

## T4 — Ripresa dopo interruzione di corrente

**Scopo:** verificare che `PLR_RECOVER` riprenda la stampa dopo un vero taglio di corrente:
- riferimento di Z ritrovato con il sensore inferiore (`z_align`);
- per una stampa a due colori, ripristino anche dell'associazione utensile → slot.

**Preparazione**
- Verifica se il CM5 è alimentato dall'alimentatore della stampante o separatamente, e annotalo: cambia cosa succede al taglio.
- `PLR_STATUS`: `enabled=True`, nessun checkpoint vecchio.
- Sotto il piatto non deve esserci niente: alla ripresa scende fino al sensore inferiore.

**Parte A — monocolore**
1. Avvia una stampa monocolore di almeno 15 minuti.
2. Aspetta almeno 10 layer (Z > 3 mm).
3. **Togli corrente alla stampante** dall'interruttore. Aspetta 30 secondi e riaccendi.
4. Quando Klipper è pronto, `PLR_STATUS` deve riportare `recoverable=True` con file e posizione.
5. Tieni la mano vicino all'interruttore e lancia `PLR_RECOVER CONFIRM=1`.
6. Atteso:
   - il piatto scende al sensore inferiore, poi homing X/Y;
   - riscaldamento, il CFS ricarica lo slot e prepara il filamento al cestino;
   - la stampa riprende alla riga salvata senza spostamento di layer visibile.

**Parte B — due colori:** ripeti con il file di T2 e la stessa associazione. Togli corrente **dopo** il primo cambio colore. Dopo `PLR_RECOVER`:
- `box.print_mapping` deve avere di nuovo `filename` e mappa;
- il cambio colore successivo deve usare lo slot associato, non lo slot con lo stesso numero dell'utensile.

**Fermati subito (interruttore) se:** prima di avvicinarsi al pezzo la testa scende troppo in basso o la posizione Z è palesemente sbagliata. Poi `PLR_DISCARD`.

---

## T5 — Cartographer collegato direttamente in USB

Sessione a parte, guidata passo passo: collegamento al CM5, controllo di `/dev/serial/by-id/...`, modifica della configurazione, reset e riconnessione automatici, probing, touch e scan. Dettagli in [Cartographer3D](CARTOGRAPHER.md).

---

## Risultati

| Prova | Data | Esito | Note (messaggi, ora nel log) |
|---|---|---|---|
| T0 homing `z_align` | 2026-10-05 | superata | 16 homing nella giornata, tutti `MCU z-align attempt 1/5: delta 0.0000mm`, nessun errore fotoelettrico |
| T1 associazione automatica + pausa/cambio slot | 2026-10-05 | associazione superata; pausa non provata | avvio normale di una stampa PLA da 18 h: `map = {"0": 3}`, T0 caricato da Box 1, slot 4 |
| T2 `BOX_PRINT_START` due colori + pausa | | | |
| T3 cambio bobina automatico | 2026-10-06 | superata | fine naturale della bobina PLA nello slot 4 invece del taglio; cambio allo slot 2 al primo `gap infill`, mappa `{"0": 1}`, la stampa è proseguita |
| T4A ripresa dopo interruzione, monocolore | | | |
| T4B ripresa dopo interruzione, due colori | | | |
| T5 Cartographer USB diretto | | | |

## Dopo le prove

L'integrazione è già unita (2026-10-03). Dopo le prove:
1. Aggiornare [TEST_STATUS](TEST_STATUS.md) con i risultati.
2. Correggere eventuali errori su `k2-pro-openhost` (gli extra K2 si mantengono solo lì).
