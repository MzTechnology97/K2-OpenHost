# Piano dei test hardware

Test da fare accanto alla stampante. Ognuno dice cosa preparare, cosa fare, cosa deve succedere e quando fermarsi. Lo [stato dei test](TEST_STATUS.md) dice quali sono già passati.

## Prima di iniziare

- Puoi raggiungere l'interruttore.
- La stampante è ferma: `print_stats` è `standby` e niente è in pausa.
- Il CM5 è su `k2-pro-openhost`: `ssh cm5 'cd ~/klipper && git log --oneline -1'`.
- Nessun vecchio punto di ripresa: `PLR_STATUS` riporta `recoverable=False`, altrimenti esegui `PLR_DISCARD`.
- Il cambio automatico a fine bobina è attivo: `box.runout_swap_enabled = true`.
- In pausa i riscaldatori restano accesi (`idle_timeout` è di fatto spento): non lasciare mai una stampa in pausa da sola.
- Tieni aperta la console di Mainsail e annota l'ora di inizio di ogni test, per ritrovarlo poi in `klippy.log`.

## Test

| # | Test | Tempo | Stato |
| --- | --- | --- | --- |
| T0 | Homing con `z_align` | 5 min | passato il 05/10/2026 |
| T1 | Un colore con mappatura automatica, pausa e cambio di slot | 30 min | mappatura passata, pausa ancora da fare |
| T2 | Due colori con `BOX_PRINT_START`, pausa e ripresa | 45 min | da fare |
| T3 | Cambio automatico a fine bobina | 40 min | passato il 06/10, 15/10 e 16/10 |
| T4 | Ripresa dopo un'interruzione di corrente | 60 min | da fare |
| T5 | Cartographer | sessione a parte | modalità mista passata il 26/10/2026, sonda unica da fare |
| T6 | HelixScreen 1.0.6-k2oh.8 sullo schermo | 30 min | da fare |

## T1: pausa e cambio di slot

La mappatura automatica è già verificata; resta la pausa.

**Prepara:** un piccolo oggetto in PLA e una seconda bobina di PLA il cui profilo ha una temperatura diversa da quella del file (file 220 °C, bobina 210 °C).

1. Avvia la stampa normalmente da Mainsail.
2. Dopo qualche strato premi **Pausa**. La testa si alza, pulisce l'ugello e si parcheggia sul cestino; l'ugello scende a 140 °C.
3. Carica l'altro PLA: `BOX_SELECT_SLOT SLOT=<indice>`.
4. Premi **Riprendi**. La testa resta sul cestino, scalda alla temperatura della nuova bobina, prepara il filamento, torna sul pezzo una volta sola e la stampa prosegue.
5. Lasciala finire: alla fine il filamento viene scaricato.

**Controlla:** nessun `Unknown command`, nessun traceback in `klippy.log`, `box.recovery.blocked = false` alla fine.

**Fermati se** Riprendi fallisce e la stampa resta in pausa. Annota il messaggio e non annullare subito.

## T2: due colori

**Prepara:** un oggetto che cambia colore in altezza (metà inferiore T0, metà superiore T1) e due bobine di PLA con temperature diverse per filamento in OrcaSlicer.

1. In Mainsail apri sul file la finestra di mappatura della CFS, assegna T0 e T1 a due slot e avvia (`BOX_PRINT_START FILENAME=<file> MAP=0:<slot>,1:<slot>`).
2. `box.print_mapping` mostra il nome del file e la mappa scelta.
3. Al cambio colore la console mostra `Changing T0 (...) -> T1 (...)` e `Purging ... (slicer matrix T0 -> T1)`, e la temperatura dell'estrusore passa a quella di T1.
4. Qualche strato dopo premi **Pausa**, aspetta un paio di minuti, poi **Riprendi**: la stampa prosegue con T1 alla sua temperatura, senza grumi sul pezzo.

**Controlla:** `box.print_mapping.active_tool = 1` dopo il cambio.

**Fermati se** il cambio carica uno slot diverso da quello mappato, o se lo spurgo è chiaramente sbagliato (assente o enorme).

## T4: ripresa dopo un'interruzione di corrente

La stampante di riferimento è sotto UPS con `[power_loss_recovery]` e `z_align` disattivati, quindi questo test richiede una stampante con il profilo generico.

**Prepara:** annota se l'host è alimentato dalla stampante o a parte. `PLR_STATUS` riporta `enabled=True` e nessun vecchio punto di ripresa. Niente sotto il piatto: la ripresa lo abbassa fino al sensore inferiore.

**A, un colore**
1. Avvia una stampa di almeno 15 minuti e aspetta che Z superi i 3 mm.
2. Spegni la stampante, aspetta 30 s, riaccendila.
3. Quando Klipper è pronto, `PLR_STATUS` riporta `recoverable=True` con il file e la posizione.
4. Con una mano sull'interruttore esegui `PLR_RECOVER CONFIRM=1`. Il piatto scende al sensore inferiore, X/Y fanno l'homing, l'ugello scalda, la CFS ricarica lo slot e la stampa riprende dalla riga salvata senza spostamenti degli strati.

**B, due colori:** ripeti con il file di T2 e togli corrente dopo il primo cambio colore. Dopo `PLR_RECOVER`, `box.print_mapping` mostra di nuovo il file e la mappa, e il cambio colore successivo usa lo slot mappato.

**Spegni subito se** la testa scende troppo o Z è chiaramente sbagliato prima di arrivare sul pezzo, poi esegui `PLR_DISCARD`.

## T5: Cartographer come unica sonda

La modalità mista (PRTouch per Z, Cartographer per la mesh) è verificata. Per usare solo il Cartographer segui [Cartographer3D](CARTOGRAPHER.md): `register_as_probe: True`, calibrazione di scansione e di contatto, poi homing, mesh e un primo strato.

## T6: HelixScreen 1.0.6-k2oh.8

Sullo schermo della stampante, a stampante ferma.

1. **Elenco filamenti:** apri l'editor di uno slot, poi *Cambia filamento*. L'elenco è la libreria di Kalico, con *Orca: ...* sotto i profili che hanno un preset.
2. **Filamento nuovo:** aggiungine uno dall'elenco. Compare nella libreria di Mainsail e sullo schermo senza riavvii.
3. **Tag sconosciuto:** con una bobina il cui tag Kalico non conosce, la scheda CFS mostra il codice. Aggiungendo un filamento dall'editor di quello slot, viene applicato subito allo slot.
4. **Touch:** Impostazioni > Touch e input, tocca una volta un preset di sensibilità. La scheda dice che la configurazione è fissa e i preset spariscono.
5. **Pagina CFS:** carica e scarica uno slot e guarda il testo della fase (per esempio "Caricamento 2 · verso la testa 3/5"); controlla la scheda della bobina esterna.
6. **Vista di stampa:** durante una stampa con più oggetti, escludine uno dalla mappa del piatto.
7. **Aggiornamenti:** `k2oh-setup helix-restore` rimette la versione precedente; il controllo aggiornamenti nell'app trova la release successiva.

**Controlla:** `/mnt/UDISK/helixscreen/logs/helix.log` non ha errori e contiene `catalog from the host library`.

## Dopo i test

Scrivi i risultati nello [stato dei test](TEST_STATUS.md). Correggi gli eventuali errori su `k2-pro-openhost` (Kalico) o `k2-openhost` (HelixScreen).
