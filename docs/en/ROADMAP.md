# Roadmap

K2-OpenHost is being developed incrementally. Each phase should be validated before the next one becomes persistent or safety-critical.

## Phase 0 — Preserve recoverability

- Keep a known-good stock system image / boot slot.
- Avoid persistent changes until runtime tests are repeatable.
- Document every sysfs change and recovery command.

Status: **in progress / partially satisfied**.

## Phase 1 — Validate the Micro-USB runtime link

Goal: prove that the service/recovery Micro-USB connector can carry a normal Linux USB gadget at runtime.

Tasks:

1. Switch USB0 from host to device mode.
2. Run `/bin/setusbconfig gser`.
3. Connect Micro-USB to an external Linux host.
4. Verify `0525:a4a6 Gadget Serial` enumeration.
5. Bind the generic usbserial driver if required.
6. Verify `/dev/ttyUSB0` on the external host.
7. Perform bidirectional byte-transfer tests.
8. Test disconnect/reconnect behavior.

Status: **next test**.

## Phase 2 — Map the K2 Pro MCU links

Goal: identify exactly how stock Klipper reaches the printer MCU(s).

Tasks:

- identify the main MCU UART;
- identify the nozzle/toolhead MCU UART;
- confirm baud rates and flow-control settings;
- identify processes currently holding those ports;
- document reset lines and restart behavior;
- determine whether any other critical MCU/bus needs host-side access.

Status: **pending**.

## Phase 3 — Build a transparent serial bridge

Goal: forward Klipper protocol bytes without interpreting them.

First prototype:

```text
/dev/ttyGS0 <-> bridge process <-> /dev/ttySx
```

Requirements:

- raw mode;
- no line discipline transformations;
- minimal buffering;
- robust reconnect handling;
- statistics and debug logging that can be disabled for production;
- deterministic startup/shutdown behavior.

Candidate implementations may include a small native daemon or a carefully configured serial-forwarding utility. Timing and buffering must be measured before selecting the final implementation.

Status: **pending**.

## Phase 4 — External Kalico MCU handshake

Goal: run host-side Kalico on Raspberry Pi / external Linux while using the original K2 MCU firmware.

Tasks:

- install `Jacob10383/kalico` on the external host;
- create a minimal K2 configuration;
- connect only the main MCU initially;
- verify MCU identify/configure sequence;
- test non-motion commands first;
- validate heaters/fans/sensors only after pin/config review;
- add nozzle MCU after the main link is stable.

Status: **pending**.

## Phase 5 — Multi-MCU transport

Goal: expose all required MCU links simultaneously.

Possible target:

```text
/dev/ttyUSB0 -> main MCU
/dev/ttyUSB1 -> nozzle MCU
```

Tasks:

- test multiple `gser` functions;
- verify stable enumeration names;
- create udev rules on the external host;
- test concurrent traffic and reconnects.

Status: **pending**.

## Phase 6 — HelixScreen on original display

Goal: remove dependence on the Creality UI while retaining the original physical screen and touch hardware.

Tasks:

- install/test HelixScreen on the T113;
- verify framebuffer output and touch input;
- point HelixScreen to remote Moonraker;
- validate basic controls, print state, temperatures and file selection;
- determine required T113 services after Creality UI services are disabled.

Status: **pending**.

## Phase 7 — Cartographer external-host integration

Goal: connect Cartographer directly to the Raspberry Pi or other external host.

Tasks:

- move USB connection if needed;
- validate MCU enumeration;
- validate probe/homing/mesh workflows under Jacob10383 Kalico;
- remove redundant T113-side dependencies.

Status: **pending**.

## Phase 8 — Closed-loop motors and K2-specific extras

Goal: preserve the K2 closed-loop functionality and other proprietary hardware features.

Tasks:

- map the actual command path used by K2 motor-control extras;
- decide whether the existing MCU transparent forwarding can be reused;
- validate X/Y controller communication;
- validate tuning/status telemetry;
- test fault behavior;
- document parameters and dependencies.

Status: **pending**.

## Phase 9 — CFS

Goal: restore/retain CFS support without the Creality host stack where possible.

Tasks:

- identify which bus and userspace components are required;
- reuse existing public reverse-engineering work where appropriate;
- validate state reporting and filament operations;
- integrate with Moonraker/HelixScreen.

Status: **pending**.

## Phase 10 — Camera strategy

Because USB0 is used by the internal camera in stock host mode, OpenHost needs a final camera solution.

Options to evaluate:

- connect the original camera directly to the external host;
- reroute through another USB host path;
- replace only the camera connection while retaining the camera module;
- leave the camera disabled.

Status: **open design decision**.

## Phase 11 — Boot automation and fail-safe recovery

Only after the runtime architecture is proven:

- automate USB role switching;
- start gadget functions automatically;
- start bridge daemon(s);
- start HelixScreen;
- implement health checks;
- define recovery behavior if the Raspberry Pi is absent;
- preserve a simple path back to stock operation.

Status: **future**.

## Phase 12 — Long-duration validation

Required before calling the project usable:

- idle link endurance;
- repeated USB reconnects;
- repeated printer reboots;
- cold boots;
- multi-hour prints;
- high-segment-count G-code;
- high acceleration / command-rate workloads;
- thermal safety tests;
- MCU restart handling;
- external-host crash/reboot handling.

Status: **future**.
