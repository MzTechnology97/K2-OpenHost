# K2-OpenHost test status

Last updated: **2026-10-02**.

## Summary

K2-OpenHost has moved beyond transport-only validation. The real K2 Pro now reaches a working external-Kalico baseline with Main MCU, Nozzle MCU, RS-485 motor control, PRTouch homing, heaters and resonance measurement operating from the CM5/external host. The Jacobean CFS/Box stack now runs in operational mode (`observation_mode: false`) in the full Kalico service.

The remaining major hardware integration items are Cartographer on the preferred **direct USB to CM5** path, a controlled mapped `BOX_PRINT_START` with real tool changes, and full print-path validation.

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
- `BOX_PRINT_INFO` on real Orca-sliced files and backend auto-mapping against the real slot inventory.

Details: [CFS validation](CFS_VALIDATION.md) and [CFS print mapping](CFS_PRINT_MAPPING.md).

### Cartographer plugin / experimental bridge

The K2/OpenHost Cartographer plugin has been installed as an editable package and its Kalico adapter loads correctly. During the experimental T113 MUX/DEMUX test:

- Cartographer V4 MCU communication was established;
- live `cartographer_data` and ADC/temperature traffic reached external Kalico;
- plugin configuration and `register_as_probe: true` loading were validated.

The experimental bridge is **not** the final transport. Cartographer reset/re-enumeration and PTY lifecycle made that path unnecessarily fragile, and one test was additionally affected by a duplicate GS2 bridge process. The preferred topology is now direct Cartographer USB to the CM5.

The Cartographer fork also contains `register_as_probe: false` support for a future mixed PRTouch + Cartographer mode. That mixed automatic-Z workflow remains unvalidated on hardware.

## Repository integration verified

`MzTechnology97/k2-pro-custom-firmware:k2-openhost` contains the versioned K2/Jacobean extra history and OpenHost patches.

`MzTechnology97/kalico-k2pro:k2-pro-openhost` contains the integrated external-host Kalico tree, including K2-specific motor-control work and tracked loader modules.

`MzTechnology97/cartographer3d-plugin-k2openhost` contains the K2/OpenHost Cartographer plugin, direct-USB guidance, mixed-mode support and Moonraker update-manager documentation.

## Pending

- connect Cartographer directly to the CM5 USB host and validate persistent `/dev/serial/by-id/...` operation;
- validate Cartographer automated reset/reconnect on direct USB;
- validate Cartographer standalone probing/touch/scan on the external host;
- optionally validate PRTouch + Cartographer mixed mode after standalone Cartographer is stable;
- validate the real filament sensor and loaded-path transitions during supervised load/unload;
- validate a controlled single-tool `BOX_PRINT_START`, then a mapped multimaterial tool change including purge matrix and temperatures;
- validate runout/recovery during a mapped job and the live RFID remaining estimate over a complete print;
- adopt the upstream Box pause/resume flow together with its matching `box.py`; until then the K2 Pro macros keep the existing `_BOX_RESUME_CHECK` path (the imported K2 Plus macros were reverted on 2026-10-03 because they called commands missing from the current Box engine);
- implement a K2 Pro-safe power-loss recovery; upstream `power_loss_recovery` requires the K2 Plus-only `[z_align]` and is disabled;
- complete first full print-path validation from homing through heating, mesh/probing, extrusion and print completion;
- continue UI split work, including the eventual T113 screen path.

## Not production-ready

The current milestone demonstrates substantially more than transport viability: real motion, full PRTouch homing, heaters, emergency shutdown and resonance analysis work from the external host. The project is still pre-production until Cartographer direct USB, mapped CFS printing and a complete print workflow are validated.