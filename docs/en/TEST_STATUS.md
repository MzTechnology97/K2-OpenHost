# Test Status

This document tracks the current validation state of K2-OpenHost.

Legend:

- ✅ Verified on hardware
- 🟡 Partially verified / intermediate result
- ⏳ Planned / not yet tested
- ❌ Failed / disproved

## Platform identification

| Item | Status | Notes |
|---|---:|---|
| Tina Linux 5.0 / OpenWrt 21.02-SNAPSHOT confirmed | ✅ | Verified on K2 Pro test unit |
| Linux kernel 5.4.61 confirmed | ✅ | Verified on K2 Pro test unit |
| Allwinner USB0 dual-role infrastructure present | ✅ | UDC and OTG manager visible in sysfs |

## USB0 / camera path

| Test | Status | Result |
|---|---:|---|
| Identify USB0 host controller | ✅ | `4101000.ehci0-controller` |
| Identify USB0 OHCI controller | ✅ | `4101400.ohci0-controller` |
| Identify internal camera on USB0 | ✅ | `1d6c:0103 CREALITY CAM` on Bus 003 |
| Verify camera disconnect during role switch | ✅ | Clean disconnect observed in dmesg |
| Verify host controllers are removed | ✅ | EHCI0 and OHCI0 removed |

## USB gadget support

| Test | Status | Result |
|---|---:|---|
| UDC exists | ✅ | `4100000.udc-controller` |
| `CONFIG_USB_GADGET=y` | ✅ | Present |
| `CONFIG_USB_CONFIGFS=y` | ✅ | Present |
| `CONFIG_USB_F_SERIAL=y` | ✅ | Present |
| `CONFIG_USB_CONFIGFS_SERIAL=y` | ✅ | Present |
| `CONFIG_USB_CONFIGFS_F_FS=y` | ✅ | Present |
| Switch USB0 to device mode | ✅ | `cat .../usb_device` returned `device_chose finished!` |
| Create ConfigFS gadget with vendor tool | ✅ | `/bin/setusbconfig gser` returned exit 0 |
| Create `/dev/ttyGS0` | ✅ | Character device created |
| Create `gser.usb0` function | ✅ | Verified in ConfigFS |
| Bind gadget to UDC | ✅ | `4100000.udc-controller` |
| Verify VID/PID | ✅ | `0525:a4a6` |
| Verify product string | ✅ | `Gadget Serial` |

## Physical Micro-USB link

| Test | Status | Result |
|---|---:|---|
| Confirm Micro-USB is runtime USB0 device connector | ✅ | CM5 enumerated the K2 gadget through the service/recovery Micro-USB connector |
| Enumerate `0525:a4a6` on Linux host | ✅ | `Netchip Technology, Inc. Linux-USB Serial Gadget` detected |
| Create host `/dev/ttyUSB0` | ✅ | Bound with Linux `usbserial_generic` via `new_id` |
| Host -> K2 serial transfer | ✅ | `K2_OPENHOST_CM5_TO_K2_001` received on `/dev/ttyGS0` |
| K2 -> host serial transfer | ✅ | `K2_OPENHOST_K2_TO_CM5_001` received on `/dev/ttyUSB0` |
| High-speed negotiation | ✅ | USB tree reports 480M; K2 UDC reports `current_speed: high-speed` |
| K2 UDC reaches configured state | ✅ | `state: configured`, `function: g1` |
| Disconnect/reconnect recovery | ⏳ | Pending |
| Repeated role-switch stability | ⏳ | Pending |

## MCU mapping

| Test | Status | Result |
|---|---:|---|
| Identify K2 Pro main MCU serial device | ✅ | `/dev/ttyS2` |
| Identify K2 Pro nozzle MCU serial device | ✅ | `/dev/ttyS3` |
| Identify RS-485 / CFS serial device | ✅ | `/dev/ttyS5` via `[serial_485 serial485]` in `box.cfg` |
| Confirm baud rates | ✅ | Main, nozzle and RS-485 paths are configured at 230400 baud |
| Stop stock Klipper without disturbing hardware services | ✅ | `/etc/init.d/klipper stop`; `klipper_mcu -r` remained active while UARTs were released |
| Open main MCU UART directly from test process | ✅ | `/dev/ttyS2` opened successfully after stock Klippy stop |
| Open nozzle MCU UART directly from test process | ✅ | `/dev/ttyS3` opened successfully after stock Klippy stop |
| Transparent `ttyGS0 <-> ttyS2` bridge | ✅ | Volatile Python raw bridge active at 230400 baud |
| Transparent `ttyGS0 <-> ttyS3` bridge | ✅ | Same volatile bridge reused successfully for the Nozzle MCU |
| Kalico handshake with original main MCU | ✅ | CM5 Kalico console connected through USB gadget bridge and decoded live MCU traffic |
| Kalico handshake with original nozzle MCU | ✅ | CM5 Kalico console retrieved the Nozzle MCU dictionary and decoded live telemetry |

### Verified Main MCU identity

The external CM5 successfully retrieved the Main MCU protocol dictionary through the transparent path. Reported values include:

- MCU: `gd32f303xe`
- Clock: `120000000`
- Serial baud: `230400`
- Receive window: `192`
- Firmware build string: `1.1.0.48-312-gcd5c2b81-dirty-20241227_092331-ubuntu`
- Toolchain: GNU Arm Embedded 9.2.1 / binutils 2.33.1

After the handshake, the CM5 received and decoded live messages such as `analog_in_state` and `stats`, confirming real bidirectional Klipper protocol communication with the original Creality Main MCU.

### Verified Nozzle MCU identity

The same USB gadget and byte-transparent bridge path was redirected from `/dev/ttyS2` to `/dev/ttyS3`. The CM5 successfully retrieved the original Nozzle MCU protocol dictionary. Reported values include:

- MCU: `gd32f303xb`
- Clock: `120000000`
- Serial baud: `230400`
- Receive window: `192`
- Firmware build string: `1.1.0.48-293-g493f9a0f-dirty-20241220_143931-ubuntu1804`
- Toolchain: GNU Arm Embedded 9.2.1 / binutils 2.33.1

After `connected`, the CM5 continued receiving and decoding `analog_in_state` and `stats`, confirming real bidirectional communication with the Nozzle MCU as well.

A `DangerOptions has not been loaded yet!` exception was emitted by Kalico's standalone `console.py` path, but both Main and Nozzle serial sessions completed successfully and live MCU traffic continued to decode. This is tracked as a standalone console-tool compatibility issue, not a transport failure.

## Multi-channel transport

| Test | Status | Result |
|---|---:|---|
| Create `gser.usb1` / second gadget serial | ⏳ | Pending |
| Expose two serial ports to Linux host | ⏳ | Pending |
| Run main + nozzle MCU links simultaneously | ⏳ | Pending |
| Stress-test both channels under printing traffic | ⏳ | Pending |

## Display / UI

| Test | Status | Result |
|---|---:|---|
| Keep original physical K2 display | 🟡 | Design choice confirmed; final OpenHost deployment pending |
| Run HelixScreen on K2 Pro original display | ⏳ | Planned |
| Connect HelixScreen to remote Moonraker | ⏳ | Planned |
| Remove dependency on Creality UI stack | ⏳ | Planned |

## Cartographer

| Test | Status | Result |
|---|---:|---|
| Cartographer visible on USB1 path | ✅ | `1d50:614e Cartographer stm32g431xx` via internal hub |
| USB0 role switch leaves Cartographer bus separate | ✅ | Cartographer is not on USB0 |
| Move Cartographer directly to external host | ⏳ | Planned |

## Closed-loop motors / CFS

| Test | Status | Result |
|---|---:|---|
| Reuse existing reverse-engineering references | 🟡 | Public documentation identified |
| Determine required transport for closed-loop motor control | ⏳ | Pending |
| Validate transparent motor-control path from external Kalico | ⏳ | Pending |
| Validate CFS from external host | ⏳ | Pending |

## Reliability

| Test | Status | Result |
|---|---:|---|
| Short serial gadget test | ✅ | Bidirectional CM5 <-> K2 traffic verified |
| Main MCU live-protocol session | ✅ | Kalico console remained connected and decoded recurring telemetry |
| Nozzle MCU live-protocol session | ✅ | Kalico console remained connected and decoded recurring telemetry |
| 1-hour idle link test | ⏳ | Pending |
| Long print | ⏳ | Pending |
| Reboot recovery | 🟡 | Stock USB host behavior observed after reboot; full OpenHost boot automation not implemented |
| Watchdog/fail-safe behavior | ⏳ | Pending |

## Safety policy during reverse engineering

All current experiments on the working stock slot are runtime-only and must be recoverable by reboot. No active-slot configuration, boot environment, MCU firmware, or persistent service state is modified during this validation phase.

## Current milestone

The project has completed its fourth major platform milestone:

> **A Raspberry Pi CM5 running Kalico has successfully established real Klipper protocol sessions with both original K2 Pro MCUs through the stock T113 and a byte-transparent bridge on the Generic Serial USB gadget: Main MCU `gd32f303xe` on `/dev/ttyS2` and Nozzle MCU `gd32f303xb` on `/dev/ttyS3`, both at 230400 baud. MCU dictionaries and live telemetry were recovered without reflashing or modifying either MCU firmware.**

The next validation step is to expose Main and Nozzle MCU links to the CM5 simultaneously, preferably with a second `gser` function, and verify two concurrent Klipper sessions before addressing the RS-485/CFS bus.
