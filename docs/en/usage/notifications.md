# Notifications

## CFS events

The box hands every CFS event to the G-code macro named by `notify_macro` in `[box]` (default `_BOX_NOTIFY`, in `macros/box.cfg`), with `EVENT`, `TITLE` and `MESSAGE`. The macro runs after the command that raised the event, so a slow or failing macro never blocks the swap or the pause.

| `EVENT` | When |
| --- | --- |
| `runout_swap` | A runout was handled by switching to the next spool of the group |
| `runout` | A runout with no replacement: the print pauses |
| `clog` | Clog detection paused the print |
| `cfs_error` | The CFS reported an error during a change |
| `rfid_unknown` | A tag that neither the CFS nor a vendor decoder recognised |
| `low_filament` | At print start, a mapped spool may not hold enough filament |
| `humidity` | At print start, a mapped spool sits in a CFS more humid than its material tolerates |

The shipped `_BOX_NOTIFY` forwards the events in `variable_events` to:

- **Mobileraker** (`mobileraker_companion`, helper menu 14): `MR_NOTIFY:title|message`, shown as a phone notification;
- **moonraker-telegram-bot**: `RESPOND PREFIX=tgnotify MSG="title: message"`.

```ini
[gcode_macro _BOX_NOTIFY]
variable_events: "runout_swap,runout,clog,cfs_error,rfid_unknown,low_filament,humidity"
variable_mobileraker: True
variable_telegram: True
```

Turn a channel off with `variable_mobileraker: False` / `variable_telegram: False`, drop events from `variable_events`, or replace the macro body with your own (apprise, a webhook through `[gcode_shell_command]`, …). `notify_macro:` empty turns notifications off.

## Buzzer

With `[k2_t113]` linked, the printer's buzzer sounds like the stock firmware:

| Sound | When |
| --- | --- |
| `print_complete` | Print finished |
| `pause` | Print paused (also filament runout) |
| `error` | Print stopped by an error |
| `cancel` | Print cancelled |
| `shutdown` | Klipper shutdown or emergency stop |
| `rfid` | External spool RFID read |

Each sound is `on,off,on,...` in milliseconds in `macros/k2_t113.cfg` (`sound_print_complete: 150,100,150,100,150,100,600`); empty = silent. Try one with `BUZZER SOUND=print_complete`, or any pattern with `BUZZER PATTERN=200,100,200`. `M300 P200` beeps for slicers.

## Health check

The host's automatic health check reports in the Klipper console after every boot and apt upgrade, and can call your own command: see [Doctor and health check](../helper/doctor.md#automatic-health-check).
