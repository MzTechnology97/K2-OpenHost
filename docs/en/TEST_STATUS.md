# K2-OpenHost test status

Last updated: **2026-10-08**.

## Summary

K2-OpenHost has moved beyond transport-only validation. The real K2 Pro now reaches a working external-Kalico baseline with Main MCU, Nozzle MCU, RS-485 motor control, PRTouch homing, heaters and resonance measurement operating from the CM5/external host. The Jacobean CFS/Box stack now runs in operational mode (`observation_mode: false`) in the full Kalico service.

The first long print ran on 2026-10-05/06 (PLA, 18 h 44 min estimate), with automatic mapping, CFS loading and an automatic runout swap halfway through. Still to do on hardware: Cartographer on **direct USB to the CM5**, a multi-colour print with tool changes, pause/resume with a slot change, and power-loss recovery.

## Verified

### External host / Kalico runtime

- Kalico runs as the main host service on an AArch64 CM5-class Debian/MainsailOS system;
- the Kalico C helper has been rebuilt natively as **ELF64/AArch64**;
- the active source tree is `MzTechnology97/kalico-k2pro`, branch `k2-pro-openhost`;
- Moonraker/Mainsail integration is active;
- host startup waits for the K2 transport devices before starting Klippy.

### USB gadget

- service Micro-USB works as the runtime device path to the external host;
- composite Generic Serial gadget operates at USB 2.0 High-Speed;
- three simultaneous `gser` interfaces are verified;
- bidirectional byte transport is verified on all three channels.

### Main MCU

- path: external `/dev/ttyUSB0` -> `ttyGS0` -> `ttyS2`;
- 230400 baud;
- original Creality GD32 firmware retained;
- live Kalico protocol/telemetry verified.

### Nozzle MCU

- path: external `/dev/ttyUSB1` -> `ttyGS1` -> `ttyS3`;
- 230400 baud;
- live Kalico protocol/telemetry verified simultaneously with Main MCU.

### RS-485 / motor control

- path: external `/dev/ttyUSB2` -> `ttyGS2` -> `ttyS5`;
- 230400 8N1;
- K2 Pro closed-loop topology uses X/Y/E, with X/Y kinematic controllers discovered at `0x81`/`0x82`;
- external-host startup timing hardened with retry/startup delays so transient first-attempt failures recover automatically;
- normal CoreXY G-code moves verified;
- X and Y sensorless/stall homing verified on hardware;
- Z direction verified;
- motor fault queries returned zero active X/Y/E faults during the validated runs.

A duplicate GS2 bridge/process-contention condition was discovered during the experimental Cartographer MUX work. After returning GS2 to a single direct RS-485 bridge, motor-control communication returned to normal. The final architecture therefore keeps GS2 dedicated to RS-485/CFS.

### Bottom-switch Z alignment (`[z_align]`)

Verified on 2026-10-03: integrated `G28` drops the bed onto the K2 Pro bottom photoelectric switch (`PA15`), rises 255 mm and homes Z with PRTouch. Three consecutive `G28` / `M84` cycles each aligned on the first MCU attempt (delta 0 steps). This required stock Creality MCU step units (gear ratio ignored), the stock 16 Z microsteps (at 64 the MCU-driven routine lost steps and failed with photoelectric errors) and a slower drop (`quick_speed`/`slow_speed` 6, about 1.9 mm/s).

Since then every homing in the logs aligned at the first attempt with delta 0: 16 times on 2026-10-05, including the start of the long print.

### Complete homing with PRTouch

A complete homing cycle has been executed successfully with the original **PRTouch** path active and Cartographer disabled. This validates the machine coordinate/homing baseline independently of Cartographer.

### Thermal outputs and emergency shutdown

The following outputs have been exercised successfully from external Kalico:

- nozzle heater;
- bed heater;
- chamber heater;
- associated PID tuning workflow.

An emergency shutdown was deliberately triggered while all heater loads were active. Measured printer consumption dropped back to near-idle, confirming that the tested heater outputs were disabled correctly by the Klipper emergency path.

### Resonance / accelerometer path

A real resonance test using **Klippain-ShakeTune** completed successfully on the external-host stack. This validates the nozzle accelerometer data path and host-side resonance analysis workflow.

### CFS protocol

Verified on the real K2 Pro:

- A1 discovery;
- A0 address assignment to address 1;
- A2 online check;
- A3 address table;
- slot mask query;
- buffer query;
- RFID/remaining-material read paths;
- K2 Pro steady `BOX_STATE` 4-byte payload;
- asynchronous slot-event decoding preserved.

Private CFS identifiers/RFID data are intentionally not published.

### Jacobean CFS extras

- `Serial_485_Wrapper` verified over `/dev/ttyUSB2`;
- `AutoAddressManager` + `BoxDriver` read-only test verified;
- native `box_protocol.py` patched to support K2 Pro 4-byte steady state;
- physical read-only transport guard verified;
- real `Box()` class in `observation_mode` verified;
- no operational Box G-code registered while observing;
- mutation function `0x0D` blocked before TX;
- ten consecutive live-state polls stable;
- internal `_poll()` completed;
- reference observation run: **35 TX / 35 RX, all transport error counters zero**.

This observation run remains the read-only safety baseline.

### CFS operational mode

The complete CM5 Kalico service now runs the Box stack with `observation_mode: false`. Verified on the real K2 Pro:

- CFS enumeration and normalized state with `driver_ready=true` / `data_ready=true`;
- K2 Pro 4-byte `BOX_STATE` compatibility path and load-path state in the running service;
- CFS temperature/humidity reporting;
- persistent filament inventory and K2-RFID/Creality material-database import;
- per-slot RFID reads and per-slot forced RFID reread;
- hardware-reported remaining percentage and independent per-spool remaining estimates;
- runout-group ordering by lowest known compatible remaining percentage;
- `BOX_PRINT_INFO` on real Orca-sliced files and backend auto-mapping against the real slot inventory;
- the live remaining estimate followed the RFID spool during the long print (slot 2: 74 % estimated, while the tag still says 95 %).

Details: [CFS validation](CFS_VALIDATION.md) and [CFS print mapping](CFS_PRINT_MAPPING.md).

### First long print (2026-10-05/06)

`Sodastream-Terra-Lever v5` in PLA, slicer estimate 18 h 44 min, started normally from Mainsail on 2026-10-05 at 17:52. In order:

- X/Y sensorless homing, `z_align` on the bottom switch (first attempt, delta 0), PRTouch Z home with thermal compensation;
- adaptive 6×6 bed mesh with PRTouch;
- automatic mapping of T0 to Box 1, slot 4 (`print_mapping.map = {"0": 3}`), CFS load (1.48 m fed), 100 mm purge at the wastebin, T0 ready in 91 s;
- after about 7 h the spool in slot 4 ran out and the print went on from slot 2 by itself (next section).

At 89 % after 15 h there were no errors. The final result will be added when it ends.

Link figures during the print, from `link_monitor.csv` (930 one-minute rows per channel):

| Channel | p50 | p99 (median of the rows) | worst sample | Retransmits / errors |
| --- | --- | --- | --- | --- |
| Main MCU | 1.17 ms | 5.25 ms | 18.8 ms | 0 bytes |
| Nozzle MCU | 1.04 ms | 3.01 ms | 16.4 ms | 0 bytes |
| RS-485 | 1.87 ms | 3.36 ms | 4.4 s (an RFID read) | 0 timeouts, 0 CRC errors |

On the T113 the three bridges lost 0 bytes, had 0 write errors and never queued. The CM5 stayed at 73–76 °C. `vcgencmd get_throttled` reports `0xe0000`: since the boot (13:37, before the print) the CPU reached the soft temperature limit and was capped at least once; it was not capped when read.

### Automatic runout swap during a print (2026-10-06)

- The CFS reported the end of the spool in slot 4. About 14.5 minutes later the printhead sensor triggered, once the filament left in the tube had been printed.
- The swap waited for the next gap infill. Then: Box 1, slot 4 → Box 1, slot 2 (same PLA, RFID tag), 33 mm to clear the gears, CFS load, 63 mm to the hotend, 20 mm prime, back to the part.
- `print_mapping.map` became `{"0": 1}`. The source slot kept its profile until the swap was decided, then the empty bay was cleared, as designed.
- No intervention was needed.

### RS-485 link watchdog, live

On 2026-10-05 at 17:40, with the printer idle, no RS-485 device (CFS, X and Y motors) answered for about 30 s, followed by 2 CRC errors and a burst of unmatched frames. The watchdog reported `RS-485 link lost` and then `RS-485 link restored` by itself, and Klipper stayed `ready`. The T113 bridges lost nothing and no other process had the port open on either side. It probably happened while a USB webcam was being plugged into the CM5, on the same hub as the T113. Details in [Serial link loss](SERIAL_LINK_LOSS.md).

### CM5 reboot

On 2026-10-05 the CM5 was rebooted from Moonraker. It was back in about 15 s with the serial ports, Klipper `ready`, RS-485, CFS and motors, and the T113 bridges reopened by themselves (same PIDs). Idle CPU: klippy 1.3 %, each bridge 0.1–0.5 %. Details in [USB bridge](USB_BRIDGE.md).

### T113 slot B (2026-10-06)

The [T113 bootstrap](T113_BOOTSTRAP.md) runs on the reference printer: slot B 0.1.1 installed with the installer helper and kept as the default. After a full power cycle the printer came up by itself: `k2oh-mcu` started the boards, then the bridges, and Klipper on the CM5 was ready with no `FIRMWARE_RESTART` (CFS OK, `[k2_t113]` connected, HelixScreen on the panel). The first install (0.1.0) found six problems, all fixed; details in [T113 bootstrap](T113_BOOTSTRAP.md#status).

### MCU firmware update from slot B (2026-10-06)

`k2oh-mcu-fw update` brought the boards to Creality 1.1.7.0: X/Y motors and extruder `mot2_…071` → `081`, RFID `009` → `010`, Main and Nozzle unchanged. The CFS was flashed too (113 → 153) although no CFS pass was asked for: `mcu_util_485` follows `fw/cfs/version.json` at every run. A custom CFS image (v2.1 RFID diagnostics) did not start (`start_app NACK`) and the CFS was recovered with the stock 153. Both are fixed in bootstrap 0.1.2; details in [T113 bootstrap](T113_BOOTSTRAP.md#status).

### Reference printer, 2026-10-08

Third-party RFID and CFS slot display, with the CFS on the API7 RFID firmware ([kalico-k2pro `docs/CFS_RFID_BAMBU.md`](https://github.com/MzTechnology97/kalico-k2pro/blob/k2-pro-openhost/docs/CFS_RFID_BAMBU.md)):

- **Creality tag:** read by the normal CFS path; the third-party fallback does not run.
- **New Bambu spool:** recognised with one extra CFS reread. **A known spool**, put back or moved to another slot, is applied from the UID cache with no reread. **A manual reread of a known tag** goes straight to its decoder: 19 s instead of 64 s.
- **Remaining filament of Bambu spools:** the CFS percentage is read every 30 s and shown in Mainsail. Kalico now gives these spools the reference length of their material (PETG 327 m, PC 345 m, PETG-CF 320 m), decreases the estimate during printing and saves it by tag UID; after a Klipper restart it is restored and the CFS percentage is polled again without a reread.
- **A forced read could block the CFS RFID task** (`busy` on one slot) after interrupted reads. An MCU power cycle (`k2oh-ctl /mcu/cycle`) recovers it; it also restarts the CFS.
- **Slot display:** a spool swap faster than the 5 s idle poll kept the previous spool on screen (Mainsail, HelixScreen) for the whole CFS read. Fixed: the insertion clears the bay's RFID profile and Box polls every second while the new tag is read. After an MCU power cycle slot 1 briefly showed the external spool's profile until the CFS answered; fixed too.
- **HelixScreen** keeps its slot overrides in Moonraker's `lane_data`, the namespace Box also publishes for OrcaSlicer; see [OrcaSlicer](ORCASLICER.md).
- **Running, not yet exercised:** CFS notifications through `_BOX_NOTIFY` (Mobileraker, moonraker-telegram-bot) and the per-material humidity warning at print start (kalico-k2pro #54-#55, Mainsail #17). The printer runs kalico-k2pro `5fc622ca` (#55): Klipper loads the macro and the slots report `humidity_pct` and `humidity_limit_pct`, but no notification has been delivered yet.
- **The `box.py` split** into `box_materials`, `box_rfid_estimates` and `box_rfid_vendors` (kalico-k2pro #56-#58, code moved unchanged) runs on the printer since the evening of 2026-10-08, together with the CFS firmware v3.13 and its `box_cfs_runtime` extra: Klipper starts, all CFS commands are registered, the remaining estimates are restored from `filament_box.json`, the third-party decoder registry loads its tag cache, and `_BOX_RFID_REMAINING_DIAG` answers. On v3.13 the CFS reports remaining `255` (unknown) on every slot after the update; Kalico ignores values outside 0-100 and keeps its own estimates.
- **Releases:** [`releases/stable.json`](../../releases/stable.json) lists the commits validated together (release 2026.10.08-2: Kalico `769d1e07`, Mainsail `v2.19.0-k2oh.18`, helper `da8bc896`, bootstrap 0.1.3); `./helper.sh release status|apply` uses it.

### Reference printer, 2026-10-07

After a 9 h 22 min PLA print from slot B (no disconnection; 3 single RS-485 timeouts in 8.4 h, recovered):

- **CFS state on firmware 1.5.3:** command `0x0A` answers with 6 bytes, decoded by the original path. Raw replies: idle `1d 26 00 00 00 00`, slot 1 loaded `1d 26 00 02 01 00` (state PRINT, slot mask `0x01`): the loaded slot comes from the CFS. Details in [CFS validation](CFS_VALIDATION.md).
- **Load and unload from unhomed axes:** the nozzle heats while X/Y home, the head waits for the temperature over the wastebin, then cuts and unloads (or loads and purges). Before, the wait happened in the endstop corner.
- **RFID:** a reread of the slot loaded toward the printhead is refused; while a filament is loaded the CFS answers `BUSY` to RFID reads of any slot (also on 1.1.3).
- **Native fan tachometers:** part fan 8276 RPM at 50 % and 13599 RPM at 100 %, heatbreak fan ~11 900 RPM, chamber heater fan ~7 600 RPM.
- **Clog detection switch** off and on, kept across Klipper restarts.
- **Service moves with Z unhomed**, also with a bed mesh loaded: `BOX_GO_TO_WASTEBIN` and `NOZZLE_CLEAN` end exactly at the wastebin (124.000 / 329.000).
- **Bottom-switch Z drop** at `quick_speed: 30` (~9.4 mm/s instead of ~3.1 mm/s).
- **Mainsail controls:** Axis Twist Compensation switch and Chamber Exhaust Fans slider (minimum speed of the temperature-controlled fans), Toolhead / Side Part Fan labels.
- **Config layout:** the printer config moved to `printer.cfg` + `macros/`; the configuration Klipper loads is identical (checked section by section).

### Cartographer plugin / experimental bridge

The K2/OpenHost Cartographer plugin has been installed as an editable package and its Kalico adapter loads correctly. During the experimental T113 MUX/DEMUX test:

- Cartographer V4 MCU communication was established;
- live `cartographer_data` and ADC/temperature traffic reached external Kalico;
- plugin configuration and `register_as_probe: true` loading were validated.

The experimental bridge is **not** the final transport. Cartographer reset/re-enumeration and PTY lifecycle made that path unnecessarily fragile, and one test was additionally affected by a duplicate GS2 bridge process. The preferred topology is now direct Cartographer USB to the CM5.

The official Cartographer plugin provides `register_as_probe: false` for a future mixed PRTouch + Cartographer mode. That mixed automatic-Z workflow remains unvalidated on hardware.

## Repository integration verified

`MzTechnology97/k2-pro-custom-firmware:k2-openhost` contains the early versioned K2/Jacobean extra history and OpenHost patches. It was archived on 2026-10-04; the extras are maintained in `kalico-k2pro:k2-pro-openhost`.

`MzTechnology97/kalico-k2pro:k2-pro-openhost` contains the integrated external-host Kalico tree, including K2-specific motor-control work and tracked loader modules.

Cartographer uses the official `Cartographer3D/cartographer3d-plugin` (1.9.0 installed on the reference CM5 on 2026-10-04; the K2-OpenHost fork was retired). Direct-USB guidance and probe roles are in [CARTOGRAPHER.md](CARTOGRAPHER.md).

## Pending

The step-by-step procedures for the physical tests below are in the [hardware test plan](HARDWARE_TEST_PLAN.md).

- Cartographer on direct USB to the CM5: persistent `/dev/serial/by-id/...`, automatic reset/reconnect, standalone probing/touch/scan, then optionally PRTouch + Cartographer (T5);
- a multi-colour print started with `BOX_PRINT_START` from the Mainsail dialog: tool change with the file's purge matrix and per-tool temperatures (T2);
- pause and resume with a slot change during the pause (second half of T1), which also covers the 071c813 pause flow (`_BOX_PAUSE_CAPTURE` / `_BOX_RESUME_PREPARE` / `_BOX_RESUME_COMMIT`);
- `PLR_RECOVER` after a supervised power cut, single colour and two colours (T4);
- the RS-485 watchdog pausing a real print: so far only the standby path has run;
- CFS discovery when RS-485 is down at Klipper start (kalico-k2pro #24, merged, not seen live yet);
- a stock `k2oh-mcu-fw apply --cfs` with bootstrap 0.1.2's held CFS list, and installing the 0.1.2 image;
- a revised custom CFS image (the v2.1 RFID diagnostic image did not start, see above);
- nozzle load cell pressure advance (kalico-k2pro #29, draft): archived on 2026-10-06 as still to develop, the module is disabled; results in `docs/K2_Load_Cell_PA.md` of kalico-k2pro;
- a CFS notification delivered to the phone (runout swap, unknown tag) and the humid CFS warning with a real spool;
- UI split work, including the eventual T113 screen path.

## Not production-ready

The current milestone demonstrates substantially more than transport viability: real motion, full PRTouch homing, heaters, emergency shutdown and resonance analysis work from the external host. An 18-hour print with automatic mapping and a runout swap also ran. The project is still pre-production until Cartographer on direct USB, multi-colour CFS printing, pause/resume and power-loss recovery are validated.