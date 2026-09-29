# K2-OpenHost Architecture

> Status: design in progress. Some layers are verified on hardware, others are planned.

## 1. Design objective

K2-OpenHost aims to preserve the original Creality K2 electronics while moving the main host-side Klipper/Kalico workload to an external Linux system.

The current preferred split is:

```text
K2 original LCD + touch
        |
        v
Allwinner T113 mainboard
- Tina Linux
- framebuffer/touch drivers
- HelixScreen
- USB gadget transport
- MCU/UART bridge services
        |
        | USB 2.0
        v
External Linux host
- Raspberry Pi / CM / other SBC
- Jacob10383 Kalico
- Moonraker
- Mainsail / Fluidd
- Cartographer
- K2-specific extras
        |
        v
Original K2 MCU(s)
```

The T113 remains part of the system, but its role changes from primary host to a lightweight hardware-facing companion.

## 2. Why retain the T113 board

The original mainboard already provides direct access to hardware that would otherwise require significant rewiring or reverse engineering:

- original LCD panel;
- original touchscreen;
- main motion MCU;
- nozzle/toolhead MCU;
- camera and internal USB topology;
- closed-loop motor infrastructure;
- printer-specific I/O and power-control paths.

Keeping the T113 allows K2-OpenHost to avoid replacing the display or mainboard.

## 3. Display strategy

The project currently intends to use **HelixScreen** on the original K2 display rather than preserving the complete Creality userspace UI stack.

The display remains electrically attached to the T113. The Raspberry Pi does not need to drive the LCD directly.

Planned UI path:

```text
Original LCD/touch
      |
      v
T113 + HelixScreen
      |
      | network
      v
Moonraker on external host
      |
      v
Kalico
```

This avoids the need to emulate Creality's `display-server`, `app-server` and `master-server` interfaces.

## 4. Motion-control strategy

The external host is intended to run the real host-side motion stack:

- Kalico / Klippy;
- Moonraker;
- K2 extras;
- Cartographer integration;
- higher-level planning and Python extensions.

The original MCU firmware is expected to remain responsible for real-time MCU work, as in normal Klipper architecture.

The target transport is conceptually:

```text
Kalico on Raspberry Pi
        |
        | USB serial gadget transport
        v
T113 /dev/ttyGSx
        |
        | byte-transparent bridge
        v
T113 UART /dev/ttySx
        |
        v
Original K2 MCU
```

## 5. USB transport

The K2 Pro test unit exposes an Allwinner USB Device Controller as:

```text
/sys/class/udc/4100000.udc-controller
```

The stock Tina image includes generic serial gadget support and `/bin/setusbconfig gser` successfully creates:

```text
/dev/ttyGS0
```

The planned use is to expose one or more logical serial channels from the T113 to the external host.

Potential final mapping:

```text
External host
/dev/ttyUSB0  <---->  /dev/ttyGS0  <---->  Main MCU UART
/dev/ttyUSB1  <---->  /dev/ttyGS1  <---->  Nozzle MCU UART
```

Multi-channel gadget transport is not yet verified.

## 6. USB0 conflict with the internal camera

Hardware testing confirmed that USB0 is normally used in host mode for the internal `CREALITY CAM`.

Normal mode:

```text
T113 USB0
  |
  +-- EHCI0 / OHCI0
          |
          +-- CREALITY CAM
```

Device mode:

```text
T113 USB0
  |
  +-- UDC 4100000.udc-controller
          |
          +-- Micro-USB service/recovery connector (expected physical path)
```

When switching USB0 to device mode, the internal camera disconnects. Therefore, the final K2-OpenHost architecture will need one of these approaches:

1. move the camera to the external host;
2. use another USB path for the camera;
3. accept loss of the stock camera;
4. investigate whether board-level switching or alternate routing exists.

No final decision has been made yet.

## 7. Cartographer

On the tested K2 Pro, Cartographer appears on USB1 through the internal USB hub, not on USB0.

This is useful because the USB0 host-to-device switch does not affect Cartographer.

The preferred final architecture is still to connect Cartographer directly to the external host if practical, reducing proxy layers.

## 8. Services expected to remain on the T113

Minimal target set:

- kernel and hardware drivers;
- framebuffer/display driver;
- touchscreen driver;
- HelixScreen;
- USB gadget configuration;
- UART/MCU bridge daemon(s);
- only required power/reset/control helpers.

## 9. Services expected to move off the T113

Planned external-host services:

- Kalico / Klippy;
- Moonraker;
- Mainsail and/or Fluidd;
- Cartographer host-side support;
- custom K2 extras and diagnostics;
- logging and development tools.

## 10. Open design questions

Still unresolved:

- exact K2 Pro main MCU UART device;
- exact nozzle MCU UART device;
- whether all required serial channels can be exposed simultaneously with ConfigFS `gser`;
- buffering/latency behavior under real Klipper traffic;
- whether the closed-loop motor path requires direct serial access, MCU transparent forwarding, or an additional transport;
- CFS transport requirements;
- long-term reliability of USB gadget mode;
- camera relocation strategy;
- boot sequencing and automatic recovery.

See [TEST_STATUS.md](TEST_STATUS.md) and [ROADMAP.md](ROADMAP.md) for current progress.
