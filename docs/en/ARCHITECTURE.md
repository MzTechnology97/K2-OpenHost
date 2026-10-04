# K2-OpenHost architecture

Status: **experimental, hardware-validated in stages**. Target printer: **Creality K2 Pro**.

Last architecture update: **2026-10-02**.

## Design goal

The project keeps the original K2 Pro electronics and moves the main Kalico/Klipper planning workload to an external Linux host. The T113 remains useful as the physical display/touch platform and as a transparent bridge to the original Main MCU, Nozzle MCU and RS-485 bus.

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
    |-- Kalico (kalico-k2pro:k2-pro-openhost)
    |-- Moonraker
    |-- Mainsail/Fluidd
    |-- K2-specific extras
    `-- direct USB host <-> Cartographer
```

## Why Cartographer is now direct USB

A T113-side Cartographer bridge plus host-side MUX/DEMUX was prototyped and carried real Cartographer MCU traffic. It also exposed two undesirable properties for a final design:

1. Cartographer reset/re-enumeration can replace the T113-side PTY and requires robust reopen/reconnect logic;
2. the shared gadget channel is unnecessary when Cartographer can connect natively to the CM5 USB host.

The project therefore keeps the three gadget serial functions dedicated to the original K2 hardware paths and treats **direct Cartographer USB to the CM5** as the preferred final topology. Use a persistent `/dev/serial/by-id/...` path on the host.

## Repository layers

### K2-OpenHost

Canonical architecture, hardware observations, validation results and roadmap.

### kalico-k2pro

`MzTechnology97/kalico-k2pro`, active branch `k2-pro-openhost`, is the integrated external-host Kalico target. It combines:

- the Jacob/Kalico core lineage;
- K2 Pro configuration baseline and machine-specific integration;
- K2/Jacobean extras required by the machine;
- external-host motor-control startup hardening;
- the tracked Cartographer loader used by the separate Cartographer plugin package.

### k2-pro-custom-firmware

Fork of `Jacob10383/k2-plus-custom-firmware`, **archived on 2026-10-04**. Its `k2-openhost` branch keeps the history of the first K2 Pro/OpenHost changes to Jacobean's K2 extras. The extras are now maintained only in `kalico-k2pro` (no mirror). Upstream changes are reviewed directly against `Jacob10383/k2-plus-custom-firmware` and `Jacob10383/kalico`.

### k2-openhost-t113-bootstrap

The printer side: a K2-OpenHost system for the T113's slot B (USB gadget bridges, HelixScreen, Creality MCU/motor/CFS firmware updates), installed from the installer helper. See [T113 bootstrap](T113_BOOTSTRAP.md).

### Cartographer3D plugin (official)

The official [cartographer3d-plugin](https://github.com/Cartographer3D/cartographer3d-plugin) is used unchanged: it detects Kalico, handles non-critical MCU reconnection and provides `register_as_probe`. The former `cartographer3d-plugin-k2openhost` fork was archived on 2026-10-04. See [Cartographer3D](CARTOGRAPHER.md).

## Verified transport

| External host | T113 gadget | T113 UART | Target | Status |
|---|---|---|---|---|
| `/dev/ttyUSB0` | `/dev/ttyGS0` | `/dev/ttyS2` | Main MCU | verified |
| `/dev/ttyUSB1` | `/dev/ttyGS1` | `/dev/ttyS3` | Nozzle MCU | verified |
| `/dev/ttyUSB2` | `/dev/ttyGS2` | `/dev/ttyS5` | RS-485/CFS/closed-loop | verified |
| `/dev/serial/by-id/...` | n/a | n/a | Cartographer via CM5 USB | target topology; final hardware validation pending |

The three verified T113 channels operate through one composite USB gadget at USB 2.0 High-Speed.

## External host runtime

The validated host is an AArch64 CM5-class Linux system. Kalico's C helper has been rebuilt natively as ELF64/AArch64, avoiding reuse of binaries from the original 32-bit T113 environment.

The host waits for the K2 transport devices before starting Kalico. Motor-control startup also includes an explicit startup delay and retry policy so the external host may boot faster than the K2 peripheral controllers without causing a permanent initialization failure.

## Motion and homing

The K2 Pro closed-loop X/Y controllers are handled through the shared RS-485 transport. Normal CoreXY G-code motion has been verified, as have X/Y sensorless/stall homing and correct Z direction.

A complete homing cycle has been executed successfully using the original **PRTouch** stack as the active Z probe. This provides a known-good non-Cartographer baseline before Cartographer is reintroduced on direct USB.

## Thermal and safety path

Bed, nozzle and chamber heaters have been exercised from external Kalico, including PID tuning. An emergency shutdown test was performed while the heaters were active; heater load was removed and measured printer consumption returned to near-idle. This validates the host-side emergency-stop path for the tested heater outputs.

## Resonance tooling

A real resonance measurement has completed through **Klippain-ShakeTune** on the OpenHost stack, confirming that the nozzle accelerometer path and host-side analysis workflow operate with the external Kalico deployment.

## RS-485 and CFS

`ttyS5` works with ordinary serial userspace access at 230400 8N1 for the tested frames. It carries both CFS and motor-control traffic, so protections remain scoped to the CFS layer rather than globally blocking the transport.

The CFS layer uses Jacobean K2 extras as the implementation baseline. K2-OpenHost adds only the compatibility/safety deltas required by K2 Pro testing, including K2 Pro 4-byte steady `BOX_STATE` decoding and protected observation mode.

Observation mode was the first, read-only validation layer. The full Kalico service now runs the Box stack in operational mode (`observation_mode: false`), with RFID inventory and print-mapping metadata exposed through the native `box` object. Mapped printing with real tool changes is still pending validation.

## Cartographer modes

The official Cartographer plugin supports two integration roles:

- `register_as_probe: true` — Cartographer owns the canonical `probe` object and `probe:z_virtual_endstop`;
- `register_as_probe: false` — intended mixed mode where PRTouch remains the primary Z-reference probe and Cartographer stays available for scanning/mesh functions under its separate endstop namespace.

Mixed mode support is implemented but not yet hardware-validated as a complete automatic Z workflow on OpenHost.

## UI split

The intended UI architecture remains HelixScreen or another lightweight UI on the T113 talking to Moonraker on the CM5. The external host stays authoritative for planning/control while the T113 handles display/touch and hardware bridging.

## Safety model

The project moves from least invasive to more invasive tests:

1. passive observation;
2. read-only protocol queries;
3. guarded runtime integration;
4. controlled motion/thermal tests;
5. full homing and resonance validation;
6. only after validation, narrowly-scoped state-changing CFS functions;
7. persistent deployment and unattended printing only after the complete print path is proven.

No Main/Nozzle MCU reflashing has been required for the validated OpenHost transport.

Using OpenHost voids the manufacturer's warranty and carries risks of irreparable damage, firmware brick and fire; it is intended for experienced users only. The cameras and the external USB port also change role. See [Disclaimer and hardware limitations](DISCLAIMER.md).

## T113 service GPIOs

The T113 is not only a serial bridge: stock firmware uses local Linux GPIOs for motherboard service functions. The verified map includes `GPIO140/PE12 = MCU_PWR_EN`, `GPIO162/PF2 = nozzle-camera power`, `GPIO164/PF4 = buzzer`, `GPIO165/PF5 = USB_HUB_RST`, and `GPIO210/PG18 = UDISK power`.

These are **not CM5 GPIOs**. The CM5 can only command them through a control plane running on the T113. The three `ttyGS0..2` gadget streams remain byte-transparent and must not be multiplexed with GPIO commands. See [T113 GPIOs](T113_GPIO.md).