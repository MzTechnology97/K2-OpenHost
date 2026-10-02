# Mappatura CFS delle stampe su K2-OpenHost

Aggiornato: **2026-10-02**.

## Obiettivo

K2-OpenHost segue il modello CFS corrente di Jacob/Jacobean: i tool dello slicer (`T0`, `T1`, ...) sono **tool logici**, non slot fisici CFS assegnati in modo permanente.

Prima di avviare una stampa mappata, la UI analizza il G-code e chiede quale slot fisico deve fornire ciascun tool logico.

Esempio:

```text
T0 logico Orca -> slot fisico CFS T1
T1 logico Orca -> slot fisico CFS T3
```

La richiesta di avvio diventa:

```text
BOX_PRINT_START FILENAME="cartella/file.gcode" MAP="0:1,1:3"
```

## Riferimenti upstream

Il comportamento deriva dal lavoro pubblico corrente in:

- `Jacob10383/k2-plus-custom-firmware` — `box.py`, `box_change.py`, `box_gcode.py` e workflow `BOX_PRINT_INFO` / `BOX_PRINT_START`;
- `Jacob10383/fluidd` — esperienza Filament Box e mappatura CFS prima della stampa.

`HimAndRobot/creality-cfs-mainsail-integration` viene inoltre usato come riferimento visuale/interazione per card slot e presentazione filamenti. K2-OpenHost **non** usa il suo trasporto diretto tramite `web-server` Creality / porta `9999`.

## Architettura OpenHost

```text
mainsail-k2openhost
        |
        | WebSocket Moonraker
        v
printer.objects.box
        |
        | BOX_PRINT_INFO / BOX_PRINT_START
        v
kalico-k2pro
        |
        | tool logico -> slot fisico
        v
BoxChangeEngine
        |
        v
RS-485 / CFS
```

Il frontend non interpreta RS-485 e non comunica direttamente con un web service CFS Creality.

## API backend

Caricare l'helper additivo dopo `[box]`:

```ini
[box]
# ...

[box_print_mapping]
```

Aggiunge:

```text
BOX_PRINT_INFO FILENAME="cartella/file.gcode"
BOX_PRINT_START FILENAME="cartella/file.gcode" MAP="0:1,1:3"
```

e amplia l'oggetto `box` esistente con:

```json
{
  "print_mapping_version": 1,
  "print_mapping_enabled": true,
  "print_info": {
    "filename": "cartella/file.gcode",
    "tools": [
      {
        "tool": 0,
        "color": "#FFFFFF",
        "material": "PLA",
        "name": "Generic PLA"
      }
    ]
  },
  "print_mapping": {
    "filename": null,
    "map": {},
    "active_tool": null,
    "active_slot": null
  }
}
```

## Lettura metadata

`BOX_PRINT_INFO` legge la parte finale di un G-code in stile Orca e usa gli stessi campi dell'implementazione corrente di Jacob:

- `filament used [mm]`;
- `filament_colour`;
- `filament_type`;
- `filament_settings_id`;
- `flush_volumes_matrix`;
- `nozzle_temperature`;
- `nozzle_temperature_initial_layer`.

Vengono presentati per la mappatura soltanto i tool con consumo filamento maggiore di zero.

## Workflow Mainsail

Quando si apre la normale finestra **Print** di Mainsail e `print_mapping_version >= 1`:

1. Mainsail invia `BOX_PRINT_INFO` per il file selezionato.
2. Kalico pubblica i tool logici in `printer.objects.box.print_info`.
3. Mainsail mostra una riga di mappatura CFS per ogni tool usato.
4. **Auto map** preferisce uno slot presente con materiale + colore corrispondenti. Tra candidati RFID altrimenti equivalenti preferisce quello con la percentuale residua conosciuta più bassa, poi applica lo scoring esistente su materiale/nome/colore; l'utente può cambiare ogni scelta.
5. Gli slot fisici vuoti sono disabilitati. La bobina esterna resta selezionabile.
6. Il pulsante Print resta disabilitato durante la lettura metadata o finché un tool richiesto non ha uno slot valido.
7. Mainsail avvia il job mappato tramite `BOX_PRINT_START` invece del normale `printer.print.start`.
8. Se il G-code non contiene metadata filamento supportati, Mainsail torna automaticamente al normale percorso di stampa.

## Validazione backend prima dell'avvio

`BOX_PRINT_START` richiede una mappatura esatta per ogni tool logico usato e controlla:

- disponibilità driver Box/CFS;
- validità dello slot target;
- presenza/online dello slot fisico;
- completezza della mappa tool logico -> slot.

La mappa viene installata dopo gli eventi di load/reset della Virtual SD e prima della ripresa del file, seguendo l'ordine dell'implementazione corrente di Jacob.

## Compatibilità con il Box engine OpenHost già validato

L'attuale `BoxChangeEngine` OpenHost, già validato sull'hardware, precede il nuovo engine di Jacob consapevole dei tool logici e indicizza purge/temperature usando i **numeri degli slot fisici**.

Per questo `box_print_mapping.py` traduce i metadata Orca prima di passarli all'engine esistente:

```text
matrice/temperature tool logici
          |
          v
mappa tool logico -> slot fisico
          |
          v
matrice/temperature per slot fisici
```

L'helper intercetta anche `PARSE_FLUSH_VOLUMES`. È necessario perché l'attuale macro K2 `START_PRINT` richiama quel comando; senza il wrapper il parser precedente sovrascriverebbe i metadata tradotti per slot fisici con dati indicizzati nuovamente per tool logico.

Questo layer resta volutamente additivo per non sostituire in blocco il lavoro già validato su RS-485 K2 Pro, protocollo Box, guard observation e motor control mentre viene adottato il nuovo contratto frontend/backend di Jacob.

## Observation mode

Con:

```ini
[box]
observation_mode: True
```

`print_mapping_enabled` è false.

`BOX_PRINT_INFO` rimane utilizzabile perché legge soltanto il G-code. `BOX_PRINT_START` rifiuta intenzionalmente l'esecuzione perché richiederebbe operazioni CFS mutanti.

Questo è il primo test consigliato sulla K2 Pro reale.

## Stato validazione

### Implementato / verificato sul codice sorgente

- parser metadata footer Orca;
- `BOX_PRINT_INFO`;
- `BOX_PRINT_START` e controlli mappa/slot;
- campi mapping in `printer.objects.box`;
- instradamento `Tn` logico -> slot fisico;
- traduzione matrice purge e temperature ugello;
- protezione della traduzione attraverso `PARSE_FLUSH_VOLUMES`;
- UI nativa di mappatura CFS in `mainsail-k2openhost`.

### Verificato sull'hardware

- `BOX_PRINT_INFO` con file Orca realmente sliciati sul CM5;
- inventario reale `box.slots` e metadata CFS in modalità Box operativa;
- auto-map backend contro metadata reali degli slot;
- comportamento fail-safe unresolved quando manca un inventario fisico compatibile;
- preferenza per la minore percentuale RFID nota tra candidati altrimenti equivalenti.

Un `cubo.gcode` PETG a due tool è stato analizzato correttamente. Con metadata temporanei PETG nero e ciano sugli slot fisici il backend ha prodotto `{0:1, 1:2}`; dopo la rimozione dei profili temporanei entrambi i tool sono tornati correttamente unresolved invece di selezionare una sorgente incompatibile.

### Da validare sull'hardware

1. `BOX_PRINT_START` controllato con singolo tool;
2. mappatura tool logico -> slot fisico differente durante una stampa reale;
3. tool change multimateriale controllato, inclusi purge matrix e temperature;
4. interazioni runout/recovery durante job mappato;
5. stima residua RFID real-time durante una stampa completa;
6. stampa completa supervisionata.

Il percorso di stampa CFS mappato non va considerato production-ready finché questi test hardware non sono conclusi.
