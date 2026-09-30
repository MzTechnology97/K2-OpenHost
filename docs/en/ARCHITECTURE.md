# K2-OpenHost Architecture

> Status: design in progress. The core external-host transport is now verified on hardware; UI, boot automation, CFS and long-duration validation remain in progress.

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
- future HelixScreen
- USB gadget transport
- byte-transparent UART bridge services
        |
        | USB 2.0 High-Speed
        v
External Linux host
- Kalico / Klippy
- Moonraker
- Mainsail / Fluidd
- K2-specific extras
        |
        +-------------------+-------------------+
        |                   |                   |
        v                   v                   v
     Main MCU           Nozzle MCU          RS-485 bus
                                            X/Y + CFS
```

The T113 remains part of the system, but its role changes from primary host to a lightweight hardware-facing companion.

## 2. Why retain the T113 board

The original mainboard already provides direct access to hardware that would otherwise require significant rewiring or reverse engineering:

- original LCD panel;
- original touchscreen;
- Main MCU;
- Nozzle MCU;
- internal USB topology;
- RS-485 path used by closed-loop/CFS infrastructure;
- printer-specific I/O and power-control paths.

Keeping the T113 allows K2-OpenHost to preserve the original display/mainboard while moving host-side compute elsewhere.

## 3. Display strategy

The preferred UI design remains:

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

The display remains electrically attached to the T113. The external Linux host does not need to drive the panel directly.

## 4. Motion-control strategy

The external host is intended to run:

- Kalico / Klippy;
- Moonraker;
- K2 extras;
- higher-level planning and Python extensions;
- Cartographer host-side support.

The original K2 MCU firmware remains responsible for real-time MCU work.

## 5. Verified three-channel USB transport

The K2 Pro T113 can expose three simultaneous ConfigFS Generic Serial functions through the service/recovery Micro-USB connector:

```text
gser.usb0 -> /dev/ttyGS0
gser.usb1 -> /dev/ttyGS1
gser.usb2 -> /dev/ttyGS2
```

The external Linux host enumerates three independent serial interfaces at USB 2.0 High-Speed (480M):

```text
/dev/ttyUSB0
/dev/ttyUSB1
/dev/ttyUSB2
```

Verified mapping:

```text
External host               T113                       Hardware

/dev/ttyUSB0 <--------> /dev/ttyGS0 <--------> /dev/ttyS2 <--> Main MCU
/dev/ttyUSB1 <--------> /dev/ttyGS1 <--------> /dev/ttyS3 <--> Nozzle MCU
/dev/ttyUSB2 <--------> /dev/ttyGS2 <--------> /dev/ttyS5 <--> RS-485
```

The bridge layer is currently a runtime Python byte-transparent prototype. A production daemon/service is still required.

## 6. Main and Nozzle MCU validation

External Kalico has successfully established real protocol sessions with both original K2 Pro MCUs through the T113 bridge:

- Main MCU: `gd32f303xe` via `/dev/ttyS2`, 230400 baud;
- Nozzle MCU: `gd32f303xb` via `/dev/ttyS3`, 230400 baud.

Both channels have been operated simultaneously without reflashing either MCU.

## 7. RS-485 and closed-loop path

The third bridge channel exposes `/dev/ttyS5` directly to the external host.

Read-only address queries were verified end-to-end for both closed-loop controllers:

```text
X (0x81): response verified
Y (0x82): response verified
```

For the tested traffic, `/dev/ttyS5` works as normal 230400 8N1 serial I/O without Linux `TIOCSRS485` configuration or explicit userspace RTS toggling.

This proves that the external host can directly reach the X/Y controller bus through the T113 without requiring a separate RS-485 proxy protocol.

The original MCU dictionaries also expose Creality's transparent serial commands. Historical stock logs confirm use of that path, but the direct third-channel `/dev/ttyS5` bridge is the currently verified external-host route for X/Y read-only communication.

## 8. CFS path

The stock configuration maps CFS communication to the same `/dev/ttyS5` RS-485 UART.

The external host therefore already has a verified transport path to the relevant bus. Connected-CFS protocol validation is still pending. Initial no-response probes were performed while the CFS was physically disconnected and are not considered failures.

## 9. USB0 conflict and unresolved physical USB topology

USB0 is normally used as a host path for the internal `CREALITY CAM`. Switching it to device mode disconnects that camera.

One additional hardware question remains open: the exact relationship between the printer's externally exposed USB-A port, the internal `CREALITY CAM`, and the service/recovery Micro-USB connector used for the external OpenHost link. It is not yet confirmed whether the external USB-A port shares the same physical hub/controller branch or sits on a separate USB path.

This must be mapped before finalizing the camera/external-USB strategy.

## 10. Cartographer wiring on the current test unit

The current K2 Pro test unit intentionally repurposes the internal USB connection originally intended for the nozzle camera on the Nozzle MCU/toolhead assembly.

Current wiring choice:

```text
Nozzle MCU / toolhead internal camera USB connector
                     |
                     v
                Cartographer
```

The stock nozzle camera is therefore not installed/used on this test unit. That camera is associated with Creality's automatic flow/pressure-related calibration workflow, which is not required for this machine's current configuration.

This choice provides two practical advantages:

- Cartographer uses an existing internal USB route instead of requiring another cable outside the printer;
- the printer's single externally exposed USB port remains available for other uses.

This is a **test-unit implementation choice**, not a requirement for all K2-OpenHost installations. Other installations may retain the nozzle camera and route Cartographer differently.

The exact upstream hub/controller relationship of this internal path versus the external USB-A port and OpenHost Micro-USB link still requires topology verification.

## 11. Services expected to remain on the T113

Minimal target set:

- kernel and hardware drivers;
- framebuffer/display driver;
- touchscreen driver;
- HelixScreen;
- USB gadget configuration;
- byte-transparent UART bridge daemon(s);
- only required hardware-specific power/reset/control helpers.

## 12. Services expected to move off the T113

- Kalico / Klippy;
- Moonraker;
- Mainsail and/or Fluidd;
- Cartographer host-side support;
- K2 extras and diagnostics;
- logging and development tools.

## 13. Reconnect behavior

A ConfigFS gadget unbind/rebind recreates `/dev/ttyGS*` endpoints. Existing bridge processes therefore exit and must be restarted after the rebind.

The production OpenHost service manager must handle:

- gadget creation;
- host enumeration;
- bridge startup;
- bridge restart after USB reconnect;
- deterministic naming;
- fail-safe fallback when the external host is unavailable.

## 14. Open design questions

Core UART identification and multi-channel exposure are no longer open questions. Remaining work includes:

- CFS validation with connected hardware;
- map the physical USB topology between external USB-A, `CREALITY CAM`, nozzle-camera/Cartographer path, and service/recovery Micro-USB;
- sustained multi-channel load and printing traffic;
- stable reconnect/re-enumeration handling;
- production bridge implementation;
- boot sequencing and automatic recovery;
- HelixScreen integration;
- validate the current Cartographer internal USB route during full OpenHost operation;
- final camera strategy;
- validation of motor tuning/write operations;
- long-duration safety and reliability testing.

See [TEST_STATUS.md](TEST_STATUS.md) and [ROADMAP.md](ROADMAP.md) for current progress.
