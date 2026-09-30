# Roadmap

K2-OpenHost is being developed incrementally. Each phase should be validated before the next one becomes persistent or safety-critical.

## Phase 0 — Preserve recoverability

- Keep a known-good stock system image / boot slot.
- Avoid persistent changes until runtime tests are repeatable.
- Document every sysfs change and recovery command.

Status: **in progress / partially satisfied**.

## Phase 1 — Validate the Micro-USB runtime link

Goal: prove that the service/recovery Micro-USB connector can carry a normal Linux USB gadget at runtime.

Completed:

- USB0 host -> device switch;
- `0525:a4a6 Gadget Serial` enumeration;
- Linux `usbserial_generic` binding;
- bidirectional byte transfer;
- USB 2.0 High-Speed 480M link.

Status: **completed for basic transport**.

Remaining reliability work moved to Phase 12.

## Phase 2 — Map the K2 Pro hardware links

Completed mapping:

```text
/dev/ttyS2 -> Main MCU @ 230400
/dev/ttyS3 -> Nozzle MCU @ 230400
/dev/ttyS5 -> RS-485 / closed-loop / CFS path @ 230400
```

Status: **completed for required UART identification**.

## Phase 3 — Build a transparent serial bridge

Runtime Python prototype verified for:

```text
/dev/ttyGS0 <-> /dev/ttyS2
/dev/ttyGS1 <-> /dev/ttyS3
/dev/ttyGS2 <-> /dev/ttyS5
```

Status: **prototype completed**.

Remaining:

- replace prototype with production service/daemon;
- deterministic reconnect handling;
- health checks/statistics;
- clean startup/shutdown behavior.

## Phase 4 — External Kalico MCU handshake

Completed:

- external Kalico connects to original Main MCU;
- original Main MCU dictionary and live telemetry decoded;
- external Kalico connects to original Nozzle MCU;
- original Nozzle MCU dictionary and live telemetry decoded;
- no MCU reflashing required.

Status: **completed for protocol connectivity**.

## Phase 5 — Multi-MCU / multi-bus transport

Verified mapping:

```text
/dev/ttyUSB0 -> gser.usb0 -> ttyGS0 -> ttyS2 -> Main MCU
/dev/ttyUSB1 -> gser.usb1 -> ttyGS1 -> ttyS3 -> Nozzle MCU
/dev/ttyUSB2 -> gser.usb2 -> ttyGS2 -> ttyS5 -> RS-485
```

Completed:

- three simultaneous ConfigFS `gser` functions;
- three host-side `usbserial_generic` interfaces;
- Main + Nozzle simultaneous protocol sessions;
- third RS-485 channel active at the same time.

Status: **completed for functional validation**.

Remaining:

- stable host naming / udev rules;
- reconnect automation;
- sustained concurrent traffic.

## Phase 6 — HelixScreen on original display

Goal: remove dependence on the Creality UI while retaining the original physical screen and touch hardware.

Tasks:

- install/test HelixScreen on the T113;
- verify framebuffer output and touch input;
- point HelixScreen to remote Moonraker;
- validate basic controls, print state, temperatures and file selection;
- determine required T113 services after Creality UI services are disabled.

Status: **pending**.

## Phase 7 — Cartographer integration

Current test-unit wiring is already established:

```text
Nozzle MCU/toolhead internal nozzle-camera USB connector -> Cartographer
```

The stock nozzle camera is intentionally not used on this machine because its automatic flow/pressure-related calibration workflow is not required for the current setup. Reusing that internal USB path avoids an additional external USB cable and keeps the printer's single exposed USB port available.

Remaining tasks:

- validate Cartographer enumeration and stability with the complete OpenHost runtime stack;
- validate probe/homing/mesh workflows under Kalico;
- map the upstream USB topology of this path relative to the external USB-A port, chamber camera and service/recovery Micro-USB;
- document alternative wiring for users who want to retain the stock nozzle camera.

Status: **wiring implemented; full OpenHost validation pending**.

## Phase 8 — Closed-loop motors and K2-specific extras

Completed:

- stock Main and Nozzle MCU dictionaries confirmed to expose `config_transparent` / `transparent_send`;
- stock logs confirmed to contain real `transparent_response` traffic;
- `/dev/ttyS5` opened directly at 230400 8N1;
- no Linux `TIOCSRS485` mode required for tested traffic;
- X controller (`0x81`) read-only address query verified directly on T113;
- X controller query verified end-to-end from external host;
- Y controller (`0x82`) query verified end-to-end from external host.

Status: **transport and read-only X/Y access verified**.

Remaining:

- map/write only the minimum required motor-control operations;
- validate tuning/status telemetry;
- validate fault handling;
- avoid persistent parameter writes until protocol behavior is fully understood.

## Phase 9 — CFS

Goal: retain CFS support without depending on the complete Creality host stack.

Current state:

- physical host UART identified as `/dev/ttyS5`;
- external-host transport to that UART is already verified;
- initial A1/A2 probes were performed while the CFS unit was physically disconnected and are therefore inconclusive.

Next tasks:

- connect CFS hardware;
- repeat online-check/discovery;
- capture and document replies;
- validate state reporting before any address-changing or filament-motion command;
- later integrate with Moonraker/HelixScreen.

Status: **next hardware validation**.

## Phase 10 — USB and camera topology

The chamber-camera/USB strategy cannot be finalized until the physical USB topology is mapped.

Required checks:

- determine whether the externally exposed USB-A port shares the same hub/controller path as the internal `CREALITY CAM`;
- determine its relationship to the service/recovery Micro-USB used by OpenHost;
- determine how the Nozzle MCU/toolhead camera USB path now used by Cartographer connects upstream;
- observe USB trees before/after controlled device connect/disconnect and USB0 role switching.

The current test unit intentionally sacrifices the stock nozzle camera in favor of Cartographer on that internal connector. The chamber camera remains a separate design question because USB0 device mode currently disconnects it.

Status: **hardware topology mapping pending**.

## Phase 11 — Boot automation and fail-safe recovery

Only after the runtime architecture is proven:

- automate USB role switching;
- create all three gadget functions automatically;
- start/restart bridge services;
- detect external-host presence;
- add health checks;
- preserve simple stock recovery.

Status: **future**.

## Phase 12 — Long-duration validation

Required before calling the project usable:

- idle link endurance;
- sustained traffic on all three channels;
- repeated USB reconnects;
- repeated gadget unbind/rebind cycles;
- repeated printer reboots and cold boots;
- multi-hour prints;
- high command-rate workloads;
- MCU restart handling;
- external-host crash/reboot handling;
- thermal and fail-safe validation.

Status: **future**.
