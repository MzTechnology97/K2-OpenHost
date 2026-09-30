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
| Identify K2 Pro main MCU serial device | ⏳ | Pending |
| Identify K2 Pro nozzle MCU serial device | ⏳ | Pending |
| Confirm baud rates | ⏳ | Pending |
| Stop stock Klipper without disturbing hardware services | ⏳ | Pending |
| Open MCU UART directly from test process | ⏳ | Pending |
| Transparent `ttyGSx <-> ttySx` bridge | ⏳ | Pending |
| Kalico handshake with original main MCU | ⏳ | Pending |
| Kalico handshake with original nozzle MCU | ⏳ | Pending |

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
| 1-hour idle link test | ⏳ | Pending |
| Long print | ⏳ | Pending |
| Reboot recovery | 🟡 | Stock USB host behavior observed after reboot; full OpenHost boot automation not implemented |
| Watchdog/fail-safe behavior | ⏳ | Pending |

## Current milestone

The project has completed its second major platform milestone:

> **The K2 Pro Micro-USB service/recovery connector has been verified as a working runtime USB device path. A Raspberry Pi CM5 successfully enumerates the stock T113 ConfigFS Generic Serial gadget at `0525:a4a6`, binds it as `/dev/ttyUSB0`, negotiates USB 2.0 High-Speed (480M), and exchanges data bidirectionally with the K2-side `/dev/ttyGS0`.**

The next milestone is to identify the K2 Pro Main MCU and Nozzle MCU UARTs and validate a byte-transparent `ttyGSx <-> ttySx` bridge without modifying the original MCU firmware.
