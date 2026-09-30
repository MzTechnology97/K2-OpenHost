# K2-OpenHost roadmap

The roadmap is validation-driven. A later phase does not start merely because the code exists; the previous layer must be proven on the K2 Pro.

## Completed foundation

- identify T113 USB Device Controller and gadget support;
- verify service Micro-USB as runtime gadget path;
- expose three Generic Serial functions;
- bridge Main MCU, Nozzle MCU and RS-485 UARTs;
- run simultaneous external Kalico MCU sessions;
- verify closed-loop X/Y read traffic;
- validate CFS discovery/address/read traffic;
- validate Jacobean BoxDriver on the OpenHost transport;
- add/validate K2 Pro 4-byte Box-state decoding;
- add/validate CFS observation guard;
- run real Jacobean `Box()` in observation mode;
- version the deltas in `k2-pro-custom-firmware:k2-openhost`;
- assemble `kalico-k2pro:k2-pro-openhost` with the K2 Pro baseline and K2 extras.

## Phase 1 — full CM5 Kalico observation instance

- install/run `kalico-k2pro:k2-pro-openhost` as a real service on the CM5;
- use `ttyUSB0`, `ttyUSB1`, `ttyUSB2` for the validated bridges;
- keep CFS in `observation_mode`;
- validate real Klippy startup, MCU telemetry, heaters/sensors without movement;
- validate real filament sensor and Box status objects.

The final tuned printer `.cfg` files are intentionally postponed until the host/transport stack is stable.

## Phase 2 — Cartographer bridge

- identify the T113-side Cartographer USB serial device;
- add a fourth gadget serial function;
- verify normal Cartographer MCU communication through the T113 bridge;
- separately determine whether bootloader/firmware-update operations require direct USB access.

## Phase 3 — machine configuration migration

Import the already-working K2 Pro configuration from the current printer installation:

- Cartographer settings;
- tuned `motor_control.cfg` values;
- PID/thermal values;
- extruder/pressure-advance settings;
- machine macros and other proven `.cfg` values.

Only host-specific paths and serial devices should be changed where necessary.

## Phase 4 — controlled CFS mutations

After observation mode is stable in the full service:

- validate loaded-path semantics;
- validate RFID policy behavior;
- enable one state-changing function at a time;
- test load/unload with mechanical supervision;
- validate cutter, buffer and runout recovery;
- keep transport/error counters and rollback procedures visible.

## Phase 5 — UI split

- run Moonraker and the main planner on the CM5;
- evaluate HelixScreen on the T113 using the stock LCD/touch hardware;
- minimize T113 responsibilities to UI and hardware bridge services.

## Phase 6 — persistent deployment

Only after the full runtime stack is proven:

- package bridge startup;
- define boot/recovery behavior;
- preserve a known-good stock slot;
- document upgrade/rebase procedures for Jacob/Kalico/Jacobean upstream changes.

## Non-goals for now

- reflashing original Creality Main/Nozzle MCUs;
- replacing working K2 electronics unnecessarily;
- publishing private CFS identifiers/RFID data;
- claiming K2 Plus behavior is automatically identical to K2 Pro behavior.