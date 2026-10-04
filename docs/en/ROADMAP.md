# K2-OpenHost roadmap

The roadmap is validation-driven. A later phase does not start merely because the code exists; the previous layer must be proven on the K2 Pro.

Updated: **2026-10-02**.

## Completed foundation

- identify T113 USB Device Controller and gadget support;
- verify service Micro-USB as runtime gadget path;
- expose three Generic Serial functions;
- bridge Main MCU, Nozzle MCU and RS-485 UARTs;
- run simultaneous external Kalico MCU sessions;
- rebuild the Kalico C helper natively for AArch64;
- verify closed-loop X/Y communication and motor-control startup recovery;
- verify normal CoreXY movement;
- verify X/Y sensorless/stall homing and correct Z direction;
- complete full homing with the stock PRTouch path;
- validate bed/nozzle/chamber heaters and PID tuning;
- validate emergency shutdown with heater load removed;
- complete a Klippain-ShakeTune resonance test;
- validate CFS discovery/address/read traffic;
- validate Jacobean BoxDriver on the OpenHost transport;
- add/validate K2 Pro 4-byte Box-state decoding;
- add/validate CFS observation guard;
- run real Jacobean `Box()` in observation mode;
- run the Box stack in operational mode in the full Kalico service, including load-path state, per-slot RFID reads and forced reread;
- validate persistent filament inventory, K2-RFID material-database resolution and remaining-percentage tracking;
- validate `BOX_PRINT_INFO` and backend auto-mapping against the real slot inventory;
- version the deltas in `k2-pro-custom-firmware:k2-openhost`;
- assemble `kalico-k2pro:k2-pro-openhost` with the K2 Pro baseline and K2 extras;
- ~~create `cartographer3d-plugin-k2openhost`~~ superseded: the official Cartographer plugin now covers K2/Kalico and `register_as_probe` (fork retired 2026-10-04); direct-USB guidance moved to [CARTOGRAPHER.md](CARTOGRAPHER.md);
- prove Cartographer MCU traffic through an experimental T113 MUX/DEMUX path, then retire that path in favour of direct USB after reset/re-enumeration complexity was observed.

## Phase 1 — direct Cartographer USB on the CM5

- connect Cartographer directly to the CM5 USB host;
- configure a persistent `/dev/serial/by-id/...` path;
- validate clean cold boot, automated reset and reconnect;
- validate Cartographer standalone mode with `register_as_probe: true`;
- validate controlled probe/touch/scan operations before any unattended Z motion;
- validate a real bed mesh from the external host.

The three T113 gadget channels remain dedicated to Main MCU, Nozzle MCU and RS-485/CFS.

## Phase 2 — optional mixed PRTouch + Cartographer mode

Only after standalone Cartographer is stable:

- set `register_as_probe: false`;
- keep PRTouch as the canonical `probe` / physical nozzle-to-bed Z reference;
- keep Cartographer available for scanning/mesh under its separate endstop namespace;
- verify that standard probe commands remain owned by PRTouch;
- validate homing and mesh workflows independently before combining them in start-print automation.

Mixed mode is optional; it is not required for the first production-capable OpenHost profile.

## Phase 3 — first complete print-path validation

- verify extruder operation and temperature safeguards;
- validate pressure advance / retraction values migrated from the known-good machine configuration;
- run homing + heating + mesh/probing + extrusion in one controlled workflow;
- execute the first supervised print from the CM5 OpenHost stack;
- verify pause/resume, cancel and emergency-stop behaviour during a real print;
- verify shutdown/restart recovery and configuration persistence.

## Phase 4 — controlled CFS mutations

Operational-mode Box state, RFID reads and auto-mapping are already validated (see the completed foundation). Remaining work:

- validate loaded-path transitions during real load/unload;
- validate a controlled single-tool `BOX_PRINT_START`, then a mapped multimaterial tool change;
- enable one state-changing function at a time;
- test load/unload with mechanical supervision;
- validate cutter, buffer and runout recovery;
- keep transport/error counters and rollback procedures visible.

## Phase 5 — UI split

- keep Moonraker and the main planner on the CM5;
- evaluate HelixScreen or another lightweight UI on the T113 using the stock LCD/touch hardware;
- minimize T113 responsibilities to UI and hardware bridge services.

## Phase 6 — persistent deployment

Only after the full runtime and print stack is proven:

- package persistent bridge startup;
- define boot/recovery behaviour;
- preserve a known-good stock slot;
- document upgrade/rebase procedures for Jacob/Kalico/Jacobean/Cartographer upstream changes;
- define a reproducible installation procedure for a second K2 Pro.

## Non-goals for now

- reflashing original Creality Main/Nozzle MCUs without a demonstrated need;
- replacing working K2 electronics unnecessarily;
- publishing private CFS identifiers/RFID data;
- claiming K2 Plus behavior is automatically identical to K2 Pro behavior;
- treating the experimental Cartographer MUX/DEMUX path as the production transport.