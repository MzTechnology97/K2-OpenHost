# Notifiche

## Eventi del CFS

Il box passa ogni evento del CFS alla macro G-code indicata da `notify_macro` in `[box]` (predefinita `_BOX_NOTIFY`, in `macros/box.cfg`), con `EVENT`, `TITLE` e `MESSAGE`. La macro gira dopo il comando che ha generato l'evento, quindi una macro lenta o in errore non blocca mai il cambio bobina o la pausa.

| `EVENT` | Quando |
| --- | --- |
| `runout_swap` | Un fine filamento gestito passando alla bobina successiva del gruppo |
| `runout` | Un fine filamento senza sostituta: la stampa va in pausa |
| `clog` | Il rilevamento intasamenti ha messo in pausa la stampa |
| `cfs_error` | Il CFS ha segnalato un errore durante un cambio |
| `rfid_unknown` | Un tag che né il CFS né un decoder di terze parti ha riconosciuto |
| `low_filament` | All'avvio della stampa, una bobina abbinata potrebbe non bastare |
| `humidity` | All'avvio della stampa, una bobina abbinata è in un CFS più umido di quanto il suo materiale tolleri |

La `_BOX_NOTIFY` inclusa inoltra gli eventi di `variable_events` a:

- **Mobileraker** (`mobileraker_companion`, menu 14 dell'helper): `MR_NOTIFY:titolo|messaggio`, mostrato come notifica sul telefono;
- **moonraker-telegram-bot**: `RESPOND PREFIX=tgnotify MSG="titolo: messaggio"`.

```ini
[gcode_macro _BOX_NOTIFY]
variable_events: "runout_swap,runout,clog,cfs_error,rfid_unknown,low_filament,humidity"
variable_mobileraker: True
variable_telegram: True
```

Spegni un canale con `variable_mobileraker: False` / `variable_telegram: False`, togli eventi da `variable_events`, oppure sostituisci il corpo della macro con il tuo (apprise, un webhook tramite `[gcode_shell_command]`, …). `notify_macro:` vuoto disattiva le notifiche.

## Cicalino

Con `[k2_t113]` collegato, il cicalino della stampante suona come con il firmware stock:

| Suono | Quando |
| --- | --- |
| `print_complete` | Stampa finita |
| `pause` | Stampa in pausa (anche per fine filamento) |
| `error` | Stampa fermata da un errore |
| `cancel` | Stampa annullata |
| `shutdown` | Shutdown di Klipper o arresto di emergenza |
| `rfid` | Lettura RFID della bobina esterna |

Ogni suono è `acceso,spento,acceso,...` in millisecondi in `macros/k2_t113.cfg` (`sound_print_complete: 150,100,150,100,150,100,600`); vuoto = muto. Provane uno con `BUZZER SOUND=print_complete`, o un qualsiasi schema con `BUZZER PATTERN=200,100,200`. `M300 P200` emette un beep per gli slicer.

## Controllo di salute

Il controllo di salute automatico dell'host riporta nella console di Klipper dopo ogni avvio e aggiornamento apt, e può chiamare un tuo comando: vedi [Doctor e controllo di salute](../helper/doctor.md#automatic-health-check).
