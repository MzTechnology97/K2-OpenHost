# OrcaSlicer profile: K2 Pro with K2-OpenHost (Kalico)

The OrcaSlicer presets the reference K2 Pro prints with, on K2-OpenHost (Kalico + Moonraker). [Italiano](#italiano)

| File | Preset |
| --- | --- |
| [`Creality K2 Pro 0.4 nozzle - newpurge-Kalico.orca_printer`](https://github.com/MzTechnology97/K2-OpenHost/raw/main/tools/orcaslicer/profiles/Creality%20K2%20Pro%200.4%20nozzle%20-%20newpurge-Kalico.orca_printer) | **Everything in one file**: the printer and the seven process presets, ready to import |
| `machine/Creality K2 Pro 0.4 nozzle - newpurge-Kalico.json` | Printer: K2 Pro, 0.4 mm hardened steel nozzle |
| `process/* @K2 Pro Kalico.json` | 7 process presets: 0.08 mm HueForge and SuperDetail, 0.12 Detail, 0.16 Optimal, 0.20 Standard, 0.24 Draft, 0.28 SuperDraft |

After changing a preset JSON, run `python3 build_bundle.py` to rebuild the bundle (CI checks it is up to date).

Filament presets are not included: use OrcaSlicer's own, or Sync from the CFS ([OrcaSlicer](../../../docs/en/ORCASLICER.md)).

## What differs from Creality's K2 Pro profile

**Printer**

- G-code flavour **Klipper**, relative E.
- Start G-code `START_PRINT EXTRUDER_TEMP=… BED_TEMP=… MATERIAL=… CHAMBER_TEMP=… MIN_CHAMBER_TEMP=…`, then `T[initial_no_support_extruder]` and a thick purge line at the left edge. End G-code `END_PRINT`, pause `PAUSE`. Every step of the start sequence is in Kalico's `START_PRINT` ([Printing](../../../docs/en/usage/printing.md)).
- No *Change filament G-code*: the CFS changes come from the slicer's `T<n>` through Kalico's tool map.
- Retraction 0.8 mm at 40 mm/s, Z hop 0.4 mm (auto lift), wipe 2 mm.
- 96×96 and 300×300 PNG thumbnails for Mainsail.
- **Printer agent** `k2_openhost_cfs`: the [K2-OpenHost CFS plugin](../../../docs/en/usage/orca-plugin.md) for OrcaSlicer 2.5. Without the plugin, set the printer agent back to the default.

**Process** (each one inherits Creality's preset of the same layer height)

- `accel_to_decel_enable` off: Kalico replaces `ACCEL_TO_DECEL` with `minimum_cruise_ratio`.
- Arc fitting off, object labels on (Kalico's `EXCLUDE_OBJECT`).
- Infill/wall overlap 15 %.
- **Slicing Pipeline Plugin** `K2-OpenHost CFS G-code map`: writes the slot choice of the CFS panel into the G-code. Without the plugin installed, OrcaSlicer skips it.

## Import

1. OrcaSlicer 2.5 or later. Install the K2-OpenHost CFS plugin first, if you use it.
2. Download the [`.orca_printer` bundle](https://github.com/MzTechnology97/K2-OpenHost/raw/main/tools/orcaslicer/profiles/Creality%20K2%20Pro%200.4%20nozzle%20-%20newpurge-Kalico.orca_printer), then **File → Import → Import Configs…**, choose it, **Open**. (Or select the printer JSON and the seven process JSON files together.)
3. Select the printer **Creality K2 Pro 0.4 nozzle - newpurge-Kalico**, open its connection settings and enter the address of your K2-OpenHost host **with the Moonraker port**, for example `k2host.local:7125`. In **Device UI** (advanced mode) put the plain address, `http://k2host.local`, so the Device tab keeps showing Mainsail. The address and the API key are empty in these files.
4. Save the printer preset.

---

## Italiano

I preset OrcaSlicer con cui stampa la K2 Pro di riferimento, su K2-OpenHost (Kalico + Moonraker).

| File | Preset |
| --- | --- |
| [`Creality K2 Pro 0.4 nozzle - newpurge-Kalico.orca_printer`](https://github.com/MzTechnology97/K2-OpenHost/raw/main/tools/orcaslicer/profiles/Creality%20K2%20Pro%200.4%20nozzle%20-%20newpurge-Kalico.orca_printer) | **Tutto in un file**: la stampante e i sette preset di processo, pronti da importare |
| `machine/Creality K2 Pro 0.4 nozzle - newpurge-Kalico.json` | Stampante: K2 Pro, ugello 0,4 mm in acciaio temprato |
| `process/* @K2 Pro Kalico.json` | 7 preset di processo: 0,08 mm HueForge e SuperDetail, 0,12 Detail, 0,16 Optimal, 0,20 Standard, 0,24 Draft, 0,28 SuperDraft |

Dopo aver cambiato un JSON, esegui `python3 build_bundle.py` per rigenerare il pacchetto (la CI controlla che sia aggiornato).

I preset dei filamenti non sono inclusi: usa quelli di OrcaSlicer, oppure il Sync dal CFS ([OrcaSlicer](../../../docs/it/ORCASLICER.md)).

### Cosa cambia rispetto al profilo K2 Pro di Creality

**Stampante**

- G-code flavour **Klipper**, E relativo.
- G-code di avvio `START_PRINT EXTRUDER_TEMP=… BED_TEMP=… MATERIAL=… CHAMBER_TEMP=… MIN_CHAMBER_TEMP=…`, poi `T[initial_no_support_extruder]` e una linea di spurgo spessa sul bordo sinistro. G-code di fine `END_PRINT`, pausa `PAUSE`. Tutta la sequenza di avvio è nella `START_PRINT` di Kalico ([Stampare](../../../docs/it/usage/printing.md)).
- Nessun *Change filament G-code*: i cambi del CFS arrivano dai `T<n>` dello slicer attraverso la mappa dei tool di Kalico.
- Retrazione 0,8 mm a 40 mm/s, Z hop 0,4 mm (auto lift), wipe 2 mm.
- Miniature PNG 96×96 e 300×300 per Mainsail.
- **Printer agent** `k2_openhost_cfs`: il [plugin K2-OpenHost CFS](../../../docs/it/usage/orca-plugin.md) per OrcaSlicer 2.5. Senza il plugin, rimetti il printer agent predefinito.

**Processo** (ognuno eredita il preset Creality con la stessa altezza layer)

- `accel_to_decel_enable` spento: Kalico sostituisce `ACCEL_TO_DECEL` con `minimum_cruise_ratio`.
- Arc fitting spento, etichette degli oggetti attive (`EXCLUDE_OBJECT` di Kalico).
- Sovrapposizione riempimento/pareti 15 %.
- **Slicing Pipeline Plugin** `K2-OpenHost CFS G-code map`: scrive nel G-code la scelta degli slot del pannello CFS. Senza il plugin installato, OrcaSlicer la salta.

### Importazione

1. OrcaSlicer 2.5 o successivo. Se lo usi, installa prima il plugin K2-OpenHost CFS.
2. Scarica il [pacchetto `.orca_printer`](https://github.com/MzTechnology97/K2-OpenHost/raw/main/tools/orcaslicer/profiles/Creality%20K2%20Pro%200.4%20nozzle%20-%20newpurge-Kalico.orca_printer), poi **File → Importa → Importa configurazioni…**, sceglilo, **Apri**. (Oppure seleziona insieme il JSON della stampante e i sette JSON di processo.)
3. Scegli la stampante **Creality K2 Pro 0.4 nozzle - newpurge-Kalico**, apri le impostazioni di connessione e inserisci l'indirizzo del tuo host K2-OpenHost **con la porta di Moonraker**, per esempio `k2host.local:7125`. In **Device UI** (modalità avanzata) metti l'indirizzo semplice, `http://k2host.local`, così la scheda Dispositivo continua a mostrare Mainsail. Indirizzo e chiave API in questi file sono vuoti.
4. Salva il preset della stampante.
