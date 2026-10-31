# Test status

Last updated: 2026-10-31.

The reference K2 Pro (CM5 host, one CFS) prints every day on K2-OpenHost. This page lists what has been verified on that printer and what is still open. Only the modified CFS firmware and the OrcaSlicer plugin are still experimental. The procedures for the open tests are in the [hardware test plan](HARDWARE_TEST_PLAN.md).

## Verified

| Area | What works | First verified |
| --- | --- | --- |
| Host | Kalico, Moonraker and Mainsail on the CM5 (AArch64); Klipper waits for the K2 serial channels at boot; after a CM5 reboot everything comes back by itself in about 15 s | 2026-10-03 |
| USB link to the T113 | Three serial channels at USB 2.0 High-Speed (main MCU, nozzle MCU, RS-485). Over long prints: no bytes lost on the T113 bridges, no CRC errors, about one RS-485 timeout every 100,000 requests, always recovered. Measurements in [USB bridge](USB_BRIDGE.md) | 2026-10-05 |
| Motion and homing | CoreXY moves, sensorless X/Y homing, Z with PRTouch, closed-loop X/Y/E motors with no faults | 2026-10-03 |
| Bottom-switch Z alignment (`z_align`) | First attempt every time, delta 0, at 16 Z microsteps. The reference printer now runs without it because it sits on a UPS (see [Configuration](reference/configuration.md)) | 2026-10-03 |
| Heaters and safety | Nozzle, bed and chamber heaters, PID tuning, emergency shutdown with all heaters on | 2026-10-03 |
| Resonance | Klippain ShakeTune with the nozzle accelerometer | 2026-10-04 |
| CFS basics | Discovery and addressing, slot and buffer state, temperature and humidity, load and unload (also from unhomed axes), notifications to Mobileraker and Telegram | 2026-10-05 |
| CFS RFID | Creality tags, Bambu tags, a known tag reapplied from the UID cache without a reread; unknown tags are reported with their code | 2026-10-08 |
| Remaining filament | Kalico estimate, the CFS live count, spool geometry per vendor (R3 firmware); the R4 millimetre count advances during prints | 2026-10-08 |
| Automatic mapping | OrcaSlicer files mapped to the loaded slots at print start; with identical spools the print starts from the loaded one or the first in runout order | 2026-10-05 |
| Runout swap | The print moves to the next identical spool by itself: 2026-10-06, 10-15 and 10-16 (about 45 s each), and several times since | 2026-10-06 |
| External spool | Loading by hand into the head sensor: Kalico grabs it, asks for the profile, heats and purges | 2026-10-29 |
| Long prints | 18 h 44 min (2026-10-05), two of 30 h 12 min (2026-10-15 and 10-17), and daily prints since | 2026-10-05 |
| Cartographer | Mixed mode: PRTouch homes Z, the Cartographer scans the mesh over direct USB. Details in [Cartographer3D](CARTOGRAPHER.md) | 2026-10-26 |
| T113 slot B | Boot without the Creality services, boards started by `k2oh-mcu`, MCU firmware update to Creality 1.1.7.0 from slot B | 2026-10-06 |
| HelixScreen | The K2-OpenHost fork on the printer screen: CFS page and print view, colours after a reinsert, remaining filament, runout swap seen live, update check from the fork | 2026-10-29 |
| Host fan and camera | CM5 fan driven by Klipper; Creality CAM at 25 fps on the CM5 | 2026-10-15 |
| RS-485 watchdog | A 30 s loss with the printer idle was reported and recovered by itself | 2026-10-05 |

## Open

- **Two-colour print** started from the Mainsail mapping dialog: tool change with the file's purge matrix and per-tool temperatures (T2).
- **Pause with a slot change**, then resume at the new filament's temperature (second half of T1).
- **Power-loss recovery** with `PLR_RECOVER`, single colour and two colours (T4). The reference printer runs on a UPS with recovery turned off, so this needs another printer or a supervised test.
- **Cartographer as the only probe** (`register_as_probe: True`, T5).
- **RS-485 watchdog during a print**: so far only the idle case has happened.
- **CFS discovery when RS-485 is down at Klipper start** (kalico-k2pro #24): covered by tests, not seen live.
- **CFS firmware**: R4 through a complete spool runout; CFG6 Bambu reads with the stock RFID timings.
- **HelixScreen 1.0.6-k2oh.8** on the screen: the filament list from Kalico and saving a new filament, the touch card with the fixed configuration, the load and unload stage on the CFS page, the external spool card, excluding an object from the bed map, the recovery card, an in-app update and `k2oh-setup helix-restore` (T6).
- **Mapping from Jacob10383's OrcaSlicer fork**: its fields match the Box status, not tried with a print.
- **Nozzle load cell pressure advance** (kalico-k2pro #29): archived, the module is off.
