# Configurazione

L'helper installa il **profilo K2 Pro** di kalico-k2pro (`config/k2/`) in `~/printer_data/config/`. Questa pagina spiega dove si trova ogni impostazione e quali è previsto che tu cambi.

!!! tip "Dove mettere le tue modifiche"
    Metti i tuoi valori in **`macros/overrides.cfg`** quando possibile: è incluso per ultimo, quindi le sue sezioni vincono, e gli aggiornamenti del profilo non lo toccano mai. Il [confronto della configurazione](../helper/menu.md) dell'helper (menu 18) mostra cosa differisce dal profilo distribuito prima di un aggiornamento.

## Struttura dei file

```text
~/printer_data/config/
├── printer.cfg                 MCU, collegamenti seriali, cinematica, riscaldatori, include
├── moonraker.conf              Moonraker, update manager
├── cfs_filaments.json          la tua libreria filamenti (profili personalizzati)
├── k2_rfid_custom_materials.json  database K2-RFID opzionale da importare
├── k2oh_t113.token             token per k2oh-ctl (non condividerlo mai)
├── timelapse.cfg
└── macros/
    ├── system.cfg              file di stampa, ripresa dopo interruzione di corrente, timeout
    ├── sensors.cfg             temperature di MCU/host, sensore filamento, accelerometro
    ├── leds.cfg                luce della camera
    ├── print.cfg               START_PRINT, PAUSE, RESUME, CANCEL, END_PRINT
    ├── kamp.cfg                spurgo adattivo KAMP
    ├── fans.cfg                ventole, tachimetri, M106/M107/M141/M191
    ├── maintenance.cfg         PID, lubrificazione delle guide, test di movimento
    ├── box.cfg                 CFS: [box], abbinamento, parametri runtime, notifiche
    ├── box_rfid_*.cfg          RFID di terze parti (solo firmware CFS API7)
    ├── motor_control.cfg       motori closed-loop X/Y/E
    ├── k2_t113.cfg             T113: cicalino, alimentazione MCU, telemetria
    ├── prtouch.cfg             sonda PRTouch (oppure cartographer.cfg)
    ├── host_fan.cfg            ventola della CPU della CM5 (menu 36 dell'helper)
    ├── openhost_controls.cfg   interruttori di Mainsail (opzionale)
    └── overrides.cfg           le TUE impostazioni, incluso per ultimo
```

Dati di esercizio fuori dalla cartella di configurazione: `~/printer_data/filament_box.json` (stato del CFS: slot, stime delle bobine, impostazioni) e `~/printer_data/power_loss_recovery/`.

## Collegamenti seriali (`printer.cfg`)

```ini
[mcu]
serial: /dev/k2-main          # T113 ttyGS0 -> Main MCU
[mcu nozzle_mcu]
serial: /dev/k2-nozzle        # T113 ttyGS1 -> Nozzle MCU
[serial_485 serial485]
serial: /dev/k2-rs485         # T113 ttyGS2 -> RS-485 (CFS, motori X/Y)
baud: 230400
link_lost_timeout: 10
link_lost_action: pause       # pause | warn | cancel | shutdown (durante una stampa)
```

I nomi `/dev/k2-*` vengono da una regola udev installata dall'helper (menu 19) e non dipendono dall'ordine di enumerazione USB. Non usare mai `/dev/ttyUSBn`: i numeri cambiano dopo una riconnessione USB.

## CFS (`macros/box.cfg`)

### `[box]`: le opzioni principali

| Opzione | Predefinito | Significato |
| --- | --- | --- |
| `box_count` | 1 | Numero di unità CFS collegate (1–4). Impostalo in `overrides.cfg` |
| `hotend_feed_length` | 63 | mm spinti verso l'hotend dopo un caricamento dal CFS |
| `retract_length` | 30 | mm ritratti prima del taglio allo scaricamento |
| `fallback_purge_length` | 100 | Spurgo senza matrice di spurgo dello slicer |
| `purge_speed`, `hotend_feed_speed` | 20 | Velocità volumetriche, mm³/s |
| `clog_detection` | True | Valore predefinito dell'interruttore del rilevamento intasamenti |
| `clog_extruder_length` | 80 | mm spinti dall'estrusore senza ricarica dal CFS prima della pausa (minimo 30) |
| `cfs_live_remaining` | True | Segue il residuo in tempo reale del CFS con firmware CFG5T/CFG6 |
| `humidity_warnings` | True | Avvisa all'avvio della stampa per bobine in un CFS troppo umido |
| `notify_macro` | `_BOX_NOTIFY` | Macro che riceve gli eventi del CFS; vuoto = spento |
| `auto_register_rfid_filaments` | True | Crea profili in libreria per i materiali RFID noti |
| `auto_bambu_rfid_fallback`, `auto_mifare_rfid_fallback` | True | Decoder RFID di terze parti (solo API7) |
| `rfid_fallback_budget` / `_manual_budget` | 1 / 3 | Riletture del CFS per i tag di terze parti |
| `publish_lane_data` | True | Pubblica gli slot per il Sync di OrcaSlicer |
| `wastebin_pos_x/y`, `clean_pad_*`, `cut_pos_*` | valori K2 Pro | Posizioni di servizio; `cut_pos_x` arriva da `CALIBRATE_CUT_POS` |

### `[box_print_mapping]`

| Opzione | Predefinito | Significato |
| --- | --- | --- |
| `auto_map_prints` | true | Abbina automaticamente i tool dello slicer agli slot quando una stampa parte senza una mappa esplicita |
| `auto_map_block_unresolved` | true | Rifiuta l'avvio quando un tool non si può abbinare in modo sicuro |

Una riga `; K2OH_TOOL_MAP = tool:slot,...` nel file (plugin OrcaSlicer) viene usata anche con `auto_map_prints: false`.

### `[box_cfs_runtime]`

Solo per il [firmware CFS sperimentale](../cfs-firmware/parameters.md). Commentato per impostazione predefinita; `auto_apply: True` più i valori che vuoi, applicati all'avvio di Klipper con la stampante ferma.

### Notifiche

`[gcode_macro _BOX_NOTIFY]`: `variable_events`, `variable_mobileraker`, `variable_telegram`. Vedi [Notifiche](../usage/notifications.md).

## T113 (`macros/k2_t113.cfg`)

| Opzione | Predefinito | Significato |
| --- | --- | --- |
| `host` | vuoto | Indirizzo IP della stampante (T113); vuoto disattiva il modulo |
| `port` | 7130 | Porta di `k2oh-ctl` |
| `token_file` | `~/printer_data/config/k2oh_t113.token` | Token condiviso, scritto dall'helper |
| `poll_interval` | 10 | Periodo della telemetria (s), 0 = spento |
| `estop_on_shutdown` | `m112` | Toglie l'alimentazione alle MCU su arresto di emergenza (`m112`), su qualsiasi shutdown (`any`) o mai (`off`) |
| `estop_power` | `cycle` | Dopo il taglio: ripristina l'alimentazione (reset delle MCU, `cycle`) o la lascia spenta (`off`) |
| `auto_power_cycle` | False | Spegne e riaccende da solo le MCU dopo un collegamento perso (solo a riposo, al massimo ogni 10 min) |
| `sound_*` | schemi stock | Schemi del cicalino `acceso,spento,acceso,...` in ms; vuoto = muto |

## Avvio stampa (`macros/overrides.cfg`)

```ini
[gcode_macro _START_PRINT_VARS]
variable_heat_soak: 0                    # heat soak del piatto, minuti
variable_offset_DEFAULT: 0.00            # Z offset, mm
variable_offset_ASA: 0                   # Z offset per materiale (offset_<MATERIALE>)
variable_adaptive_axis_twist_comp: 0     # valore predefinito di START_PRINT_ATC
variable_prtouch_scrub: 0                # strofina il nozzle sulla linguetta del piatto prima di PRTouch
```

## Ventola dell'host (`macros/host_fan.cfg`)

```ini
[host_fan cm5_fan]
control: target         # target | manual | kernel
target_temp: 55
ramp_delta: 15
min_speed: 0.3
max_speed: 1.0
full_speed_temp: 75
```

Vedi [Hardware host](../HOST.md#ventola-della-cpu).

## Ripresa dopo un'interruzione di corrente (`macros/system.cfg`)

`[power_loss_recovery]` scrive i checkpoint in `~/printer_data/power_loss_recovery` e ritrova Z con `[z_align]` (finecorsa in basso), come lo stock. Il recupero parte solo con `PLR_RECOVER CONFIRM=1`. Validalo con un'interruzione di corrente sorvegliata prima di farci affidamento. Se host e stampante sono sotto UPS puoi preferire di disattivarli entrambi, come fa la stampante di riferimento.

## Telemetria di Kalico

Il profilo imposta `[telemetry] enabled: False`: Kalico non invia dati di utilizzo.

## Macchina di riferimento

`config/k2/reference/k2pro-cm5/` in kalico-k2pro è la configurazione reale della stampante di riferimento (host CM5, CFS CFG6, RFID di terze parti, ventola dell'host, UPS). Usala come esempio, non da copiare così com'è: alcune scelte sono specifiche di quella macchina.
