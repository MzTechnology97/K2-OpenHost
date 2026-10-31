# Troubleshooting

Find your symptom, check the cause, apply the fix. Start with `./helper.sh doctor` on the host: it checks most of these for you. For lost links and restarts, the step-by-step escalation is in the [Recovery runbook](../RECOVERY.md).

!!! warning "Not while printing"
    Restarts, bridge restarts, MCU power cycles, updates and flashes are refused or unsafe during a print. If a print paused on its own, find the cause first, then `RESUME`.

## The host does not see the printer

| Seen | Cause | Fix |
| --- | --- | --- |
| `lsusb` has no `0525:a4a6` | Cable in the wrong port, charge-only cable, or the T113 is not on slot B | Data cable in the T113 **service** Micro-USB port ([photo](../getting-started/requirements.md#where-the-service-micro-usb-port-is)); `./helper.sh t113 status` must show slot B |
| `0525:a4a6` present, no `/dev/k2-*` | udev rule missing | Helper menu 19 (serial names) |
| `0525:a4a6` present, no `/dev/ttyUSB*` either | `usbserial` did not claim the gadget | `sudo sh ~/k2-openhost-t113-bootstrap/host/k2oh-host-usbserial install` |
| Gadget appears and disappears | Loose or poor cable, cable under strain | Use a short, good **90° data cable** and secure it |
| After a kernel update nothing works | New kernel without `usbserial` | `modinfo -k <version> usbserial`; the health check warns about it after apt |

## Klipper errors

| Message | Cause | Fix |
| --- | --- | --- |
| `Lost communication with MCU 'mcu'` / `'nozzle_mcu'` | Bridge restarted, cable moved, T113 rebooted | `FIRMWARE_RESTART` (twice if the first says `Failed automated reset`), then `BOARD_STATUS`; see [runbook](../RECOVERY.md#lost-communication-with-mcu) |
| `Unable to open serial port` | Wrong `serial:` path or another program holds the port | Use `/dev/k2-*`; `sudo fuser -v /dev/k2-*` shows who holds it |
| `RS-485 link lost` | RS-485 bridge down, CFS/motor bus fault | `BOARD_STATUS`, then `USB_BRIDGES_RESTART CONFIRM=1`; recovers by itself when the bus answers |
| `Timer too close` | Host overloaded or throttled | `vcgencmd get_throttled` (under-voltage), check CPU temperature (`HOST_FAN_STATUS`), stop heavy services |
| `MCU 'mcu' shutdown: ...` after a firmware update | MCU firmware mismatch | `./helper.sh t113 mcu-fw status`, update with menu 31 when idle |
| Option `xyz` is not valid | Config from a newer/older profile | `./helper.sh config diff` (menu 18) and compare with the shipped profile |

## Motion and probing

| Seen | Fix |
| --- | --- |
| Homing refused, motors not ready | `MOTOR_STATUS`; `SERIAL_STATUS` must be `ok`; `MOTOR_RETRY_STARTUP`; for a fault `MOTOR_QUERY_FAULTS` → `MOTOR_CLEAR_ERROR` |
| "Suspicious calibration" at startup | `MOTOR_CALIBRATE AXIS=XY` (printhead in the middle, bed at the bottom). `MOTOR_ACCEPT_CALIBRATION` only if you know it is good |
| Stall / overcurrent during a print | `MOTOR_EVENTS VERBOSE=1`; check belts, rails and obstructions; lubricate (`LUBRICATE_RAILS`) |
| First layer too high/low | Z offset in `_START_PRINT_VARS` (`variable_offset_DEFAULT` or per material), PRTouch clean nozzle (`variable_prtouch_scrub`) |
| Cutter misses | `CALIBRATE_CUT_POS` after changing the cutter or the toolhead |

## CFS

| Seen | Cause | Fix |
| --- | --- | --- |
| CFS not found | Started while RS-485 was down; power or cable | Waits and retries by itself; `SERIAL_STATUS` `ok` then `RESTART`; check the CFS cable |
| Print refused: tool not mapped | A slicer tool has no matching spool | Map it in Mainsail's print dialog or with the OrcaSlicer plugin; or `auto_map_block_unresolved: false` |
| Load stops halfway, `cfs_error` | Filament path friction, wrong spool position, buffer | Check the PTFE path and the spool; `BOX_DEBUG`; `BOX_UNLOAD MANUAL=1` then reload |
| Clog pause while printing fine | `clog_extruder_length` too short for the material | Raise it (min 30, default 80) or disable with `_BOX_SET_CLOG_DETECTION ENABLE=0` |
| Runout swap did not happen | Swap off, or no spool of the same filament | `_BOX_SET_RUNOUT_SWAP ENABLE=1`; same material and colour in another slot; check the order (`_BOX_SET_RUNOUT_ORDER`) |
| RFID unknown | Third-party tag on stock CFS firmware | Assign a library profile by hand; or [API7 firmware](../cfs-firmware/third-party-rfid.md) |
| Third-party tag never decoded | Not MIFARE Classic 1K, or cached as unknown | `_BOX_RFID_FALLBACK_CACHE`, `CLEAR=1 UID=<hex>`, then `_BOX_RFID_READ_SLOT SLOT=<n>` |
| "Another CFS RFID read is in progress" | Two reads at once | Wait about 45 s and retry |
| Remaining percentage looks wrong | Wrong nominal length, used spool marked new | Set the profile's Nominal length or `_BOX_RFID_SPOOL_NEW SLOT=<n> TOTAL_M=<m> REMAINING=<%>` |
| Humidity warning at start | CFS humidity above the material limit | Dry the spool or change `humidity_limits` |

## Experimental CFS firmware

| Seen | Fix |
| --- | --- |
| `BOX_CFS_CONFIG_INFO` shows no identity | Stock or older firmware: nothing is written, this is normal |
| Startup lists ignored options | Option not writable on this firmware (e.g. CFG6 option on CFG5T) or out of range: fix `box.cfg` |
| CFS stops answering after a flash | **Do not immediately retry the experimental image.** Check whether the device is still in loader mode (A2, during supervised maintenance), examine `/tmp/mcu_update.log`, and follow the [interrupted-flash recovery procedure](../cfs-firmware/flash.md#interrupted-flash). If the loader responds and the safety prerequisites are met, use a **known-good image with verified SHA-256** (previous CFG6 v3.25, v3.22 or stock, as appropriate for the hardware). |
| Flash interrupted / `send fw data ... failed` | The log may indicate an **incomplete transfer**, not an application crash. Do not blindly resend the failed BIN. Preserve `/tmp/mcu_update.log`, confirm loader/CFS address, printer and heaters idle, and a verified rollback image; see [Flash and roll back](../cfs-firmware/flash.md#interrupted-flash). |

## Mainsail, Moonraker, screen

| Seen | Fix |
| --- | --- |
| Mainsail shows no CFS panel | Mainsail K2-OpenHost not installed or a cached old version: `./helper.sh install mainsail`, then reload the page (Ctrl+F5) |
| Update Manager errors | Mainsail → Machine → Update Manager → **Recover** on that component; `./helper.sh update` |
| HelixScreen shows "disconnected" | Host IP changed: helper menu 29 (change host address); host must have a fixed IP |
| HelixScreen lists its own presets instead of Kalico's library | Needs HelixScreen 1.0.6-k2oh.8 or later, connected to Kalico; see [HelixScreen](../usage/helixscreen.md#filament-library) |
| Reinserted spool grey in HelixScreen and OrcaSlicer, wrong tools on the slots | Upstream HelixScreen: install the K2-OpenHost fork; see [HelixScreen](../usage/helixscreen.md#installing-or-updating-the-fork) |
| Camera black or 30 fps black frames | Crowsnest `max_fps: 25`, see [Camera](../CAMERA.md) |

## OrcaSlicer

| Seen | Fix |
| --- | --- |
| Sync sets "Generic" filaments | Filament presets must be **root** presets with the right OrcaSlicer ID; see [OrcaSlicer](../ORCASLICER.md) |
| Plugin cannot connect | Device host must include the port (`host:7125`); allow the plugin's permissions; see [plugin](../usage/orca-plugin.md) |
| Other printers misbehave after enabling the agent | Keep OrcaSlicer's global *use printer agents* **off**; the plugin works through its panel and the G-code map |

## Still stuck

Collect what [Debug: what to attach](debug.md#what-to-attach-when-asking-for-help) lists and open an issue on [K2-OpenHost](https://github.com/MzTechnology97/K2-OpenHost/issues).
