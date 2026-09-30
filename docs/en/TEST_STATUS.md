# K2-OpenHost test status

Last updated: **2026-09-30**.

## Summary

The project has moved beyond basic serial transport validation. Main MCU, Nozzle MCU, RS-485 closed-loop devices and the real CFS stack have all been exercised through the T113 USB gadget path from an external Kalico host.

## Verified

### USB gadget

- service Micro-USB works as the runtime device path to the external host;
- composite Generic Serial gadget at 480M;
- three simultaneous `gser` interfaces verified;
- bidirectional byte transport verified on all three channels.

### Main MCU

- path: external `ttyUSB0` -> `ttyGS0` -> `ttyS2`;
- 230400 baud;
- original Creality GD32 MCU firmware;
- live Kalico protocol/telemetry verified.

### Nozzle MCU

- path: external `ttyUSB1` -> `ttyGS1` -> `ttyS3`;
- 230400 baud;
- live Kalico protocol/telemetry verified simultaneously with Main MCU.

### RS-485 / closed-loop devices

- path: external `ttyUSB2` -> `ttyGS2` -> `ttyS5`;
- 230400 8N1;
- X controller address `0x81` verified;
- Y controller address `0x82` verified;
- no Linux RS-485 ioctl mode required for tested traffic.

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
- no operational Box G-code registered (transport diagnostic `SERIAL_STATUS` remains);
- mutation function `0x0D` blocked before TX;
- ten consecutive live-state polls stable;
- internal `_poll()` completed;
- transport result: **35 TX / 35 RX, all error counters zero**.

## Repository integration verified

`MzTechnology97/k2-pro-custom-firmware:k2-openhost` contains the versioned K2 extras and OpenHost patches.

`MzTechnology97/kalico-k2pro:k2-pro-openhost` now contains:

- current Jacob Kalico base from the fork point;
- K2 Pro `.cfg` baseline;
- the validated K2 extras synchronized into `klippy/extras/`;
- a CI sync workflow that compiles the synchronized Python extras.

No core Kalico module was modified for the K2 Pro/OpenHost integration at this stage.

## Expected harness-only artefacts

During standalone `Box()` testing, `filament_sensor_error` is true because the fake printer harness intentionally does not instantiate the real `filament_switch_sensor`. This is not a CFS transport failure.

`loaded_slot = -1` is currently conservative/intentional until the loaded-path semantics are validated on real hardware.

## Pending

- run a full real Klippy instance on the CM5 with CFS still in observation mode;
- adapt host paths (`ttyUSB0..2`, printer-data paths) without importing final machine calibration yet;
- validate Cartographer as a fourth T113 gadget channel;
- validate the real filament sensor and loaded-path semantics;
- only then enable controlled CFS mutation/load/unload tests;
- migrate the proven production `.cfg` values from the currently-working K2 Pro;
- integrate Moonraker/UI and eventually HelixScreen on the T113.

## Not production-ready

The project should not yet be treated as a drop-in production firmware replacement. Current results prove the architecture and several protocol layers, not the complete print workflow.