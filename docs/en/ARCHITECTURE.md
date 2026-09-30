# K2-OpenHost architecture

Status: **experimental, hardware-validated in stages**. Target printer: **Creality K2 Pro**.

## Design goal

The project keeps the original K2 Pro electronics and moves the main Kalico/Klipper planning workload to an external Linux host. The T113 remains useful as the physical display/touch platform and as a transparent bridge to internal UART/RS-485 devices.

```text
K2 LCD/touch
    |
Allwinner T113 (Tina Linux)
    |-- UI / future HelixScreen
    |-- USB ConfigFS gadget
    |-- ttyGS0 <-> ttyS2  Main MCU
    |-- ttyGS1 <-> ttyS3  Nozzle MCU
    `-- ttyGS2 <-> ttyS5  RS-485 / CFS / closed-loop
           |
           | service Micro-USB
           v
External Linux host / Raspberry Pi CM5
    |-- Kalico
    |-- Moonraker
    |-- Mainsail/Fluidd
    `-- K2-specific extras
```

A fourth Generic Serial interface is planned for Cartographer after its internal T113-side USB serial device is validated for transparent bridging.

## Repository layers

### K2-OpenHost

Canonical architecture, hardware observations, validation results and roadmap.

### kalico-k2pro

`MzTechnology97/kalico-k2pro` is a fork of `Jacob10383/kalico`. The active `k2-pro-openhost` branch currently combines:

- the upstream Kalico core;
- a K2 Pro configuration baseline derived from the public `luketot/kalico-for-K2-Pro` work;
- Jacobean K2 extras synchronized from `MzTechnology97/k2-pro-custom-firmware:k2-openhost`.

Final machine-specific `.cfg` values will be migrated from the already-working K2 Pro only after the transport/control tests are complete.

### k2-pro-custom-firmware

Fork of `Jacob10383/k2-plus-custom-firmware`. The `k2-openhost` branch is the versioned source for K2 extras and OpenHost/K2 Pro compatibility changes. It preserves the upstream lineage while keeping our deltas auditable.

## Verified transport

| External host | T113 gadget | T113 UART | Target | Status |
|---|---|---|---|---|
| `/dev/ttyUSB0` | `/dev/ttyGS0` | `/dev/ttyS2` | Main MCU | verified |
| `/dev/ttyUSB1` | `/dev/ttyGS1` | `/dev/ttyS3` | Nozzle MCU | verified |
| `/dev/ttyUSB2` | `/dev/ttyGS2` | `/dev/ttyS5` | RS-485/CFS | verified |
| planned `/dev/ttyUSB3` | planned `ttyGS3` | internal Cartographer USB serial | Cartographer | pending |

All three verified channels operate through one composite USB gadget at USB 2.0 High-Speed.

## Main and nozzle MCU

Stock configuration uses 230400 baud on both MCU UARTs. External Kalico successfully established simultaneous sessions with both original Creality MCUs without firmware replacement.

## RS-485

`ttyS5` works with ordinary serial userspace access at 230400 8N1 for the tested frames; Linux RS-485 ioctl mode is not required for the observed traffic. The path carries CFS and other K2 peripherals, so protections must be scoped to the CFS layer rather than globally blocking the transport.

## CFS integration

The CFS layer uses Jacobean K2 extras as the implementation baseline. K2-OpenHost adds only the compatibility/safety deltas actually required by the K2 Pro tests:

1. decode K2 Pro steady `BOX_STATE` replies with a 4-byte payload while preserving the existing 6-byte path;
2. add `observation_mode` in `box.py`;
3. wrap only the CFS stack in a read-only proxy, leaving the shared RS-485 transport available to closed-loop devices;
4. suppress operational Box G-code, T commands, automatic RFID-policy write and runout hooks while observing.

## UI split

The intended UI architecture is HelixScreen on the T113 talking to Moonraker on the CM5. This avoids forcing the display stack onto the external host while still keeping the external host authoritative for printer planning/control.

## Safety model

The project moves from least invasive to more invasive tests:

1. passive observation;
2. read-only protocol queries;
3. guarded runtime integration;
4. only after validation, narrowly-scoped state-changing commands;
5. persistent installation only after the runtime architecture is proven.

No MCU reflashing is required for the transport tests documented so far.