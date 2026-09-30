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
| Identify internal camera on USB0 | ✅ | `1d6c:0103 CREALITY CAM` |
| Verify camera disconnect during role switch | ✅ | Clean disconnect observed in dmesg |
| Verify host controllers are removed | ✅ | EHCI0 and OHCI0 removed |
| Map external USB-A port against camera/Micro-USB topology | ⏳ | Need to determine whether the exposed USB-A port shares the same hub/controller path as `CREALITY CAM` and/or the service/recovery Micro-USB used by the external host |

## USB gadget support

| Test | Status | Result |
|---|---:|---|
| UDC exists | ✅ | `4100000.udc-controller` |
| `CONFIG_USB_GADGET=y` | ✅ | Present |
| `CONFIG_USB_CONFIGFS=y` | ✅ | Present |
| `CONFIG_USB_F_SERIAL=y` | ✅ | Present |
| `CONFIG_USB_CONFIGFS_SERIAL=y` | ✅ | Present |
| `CONFIG_USB_CONFIGFS_F_FS=y` | ✅ | Present |
| Switch USB0 to device mode | ✅ | Runtime switch verified |
| Create initial gadget with vendor tool | ✅ | `/bin/setusbconfig gser` works |
| Create `gser.usb0` / `/dev/ttyGS0` | ✅ | Verified |
| Add `gser.usb1` / `/dev/ttyGS1` | ✅ | ConfigFS function and port 1 verified |
| Add `gser.usb2` / `/dev/ttyGS2` | ✅ | ConfigFS function and port 2 verified |
| Bind three serial functions to one gadget | ✅ | All three linked to `configs/c.1` |
| Bind gadget to UDC | ✅ | `4100000.udc-controller` |
| Verify VID/PID | ✅ | `0525:a4a6` |
| Verify product string | ✅ | `Gadget Serial` |

## Physical Micro-USB link

| Test | Status | Result |
|---|---:|---|
| Confirm Micro-USB is runtime USB0 device connector | ✅ | External Linux host enumerated K2 gadget through service/recovery connector |
| High-speed negotiation | ✅ | 480M |
| Expose one serial interface | ✅ | `/dev/ttyUSB0` |
| Expose two serial interfaces | ✅ | `/dev/ttyUSB0` + `/dev/ttyUSB1` |
| Expose three serial interfaces | ✅ | `/dev/ttyUSB0` + `/dev/ttyUSB1` + `/dev/ttyUSB2` |
| Host driver binding | ✅ | All three interfaces bind to `usbserial_generic` |
| Bidirectional byte transfer | ✅ | Verified |
| Disconnect/reconnect recovery | 🟡 | Re-enumeration works; bridge daemons must be restarted after gadget unbind/rebind |
| Repeated role-switch stability | ⏳ | Pending endurance test |

## MCU mapping

| Test | Status | Result |
|---|---:|---|
| Main MCU serial device | ✅ | `/dev/ttyS2` |
| Nozzle MCU serial device | ✅ | `/dev/ttyS3` |
| RS-485 / CFS serial device | ✅ | `/dev/ttyS5` |
| Baud rates | ✅ | Main, Nozzle and RS-485 are 230400 baud |
| Stop stock Klipper and free UARTs | ✅ | Runtime-only test successful |
| `ttyGS0 <-> ttyS2` raw bridge | ✅ | Main MCU |
| `ttyGS1 <-> ttyS3` raw bridge | ✅ | Nozzle MCU |
| `ttyGS2 <-> ttyS5` raw bridge | ✅ | RS-485 bus |
| Kalico handshake with Main MCU | ✅ | Dictionary and live telemetry decoded |
| Kalico handshake with Nozzle MCU | ✅ | Dictionary and live telemetry decoded |
| Main + Nozzle sessions simultaneously | ✅ | Two concurrent host serial interfaces verified |

### Verified Main MCU identity

- MCU: `gd32f303xe`
- Clock: `120000000`
- Serial baud: `230400`
- Receive window: `192`
- Firmware build: `1.1.0.48-312-gcd5c2b81-dirty-20241227_092331-ubuntu`

### Verified Nozzle MCU identity

- MCU: `gd32f303xb`
- Clock: `120000000`
- Serial baud: `230400`
- Receive window: `192`
- Firmware build: `1.1.0.48-293-g493f9a0f-dirty-20241220_143931-ubuntu1804`

Kalico standalone `console.py` may emit `DangerOptions has not been loaded yet!`, but protocol connections and live telemetry continue. This is tracked as a console-tool compatibility issue, not a transport failure.

## Multi-channel transport

| Test | Status | Result |
|---|---:|---|
| Create `gser.usb1` | ✅ | Port number 1 |
| Create `gser.usb2` | ✅ | Port number 2 |
| Expose three host serial ports | ✅ | Interfaces 0/1/2 enumerate at 480M |
| Run Main + Nozzle links simultaneously | ✅ | Concurrent sessions verified |
| Run RS-485 as third simultaneous channel | ✅ | `ttyUSB2 -> ttyGS2 -> ttyS5` verified |
| Stress all channels during printing | ⏳ | Pending |

## Closed-loop motors / RS-485

| Test | Status | Result |
|---|---:|---|
| Confirm stock MCU dictionaries expose transparent serial commands | ✅ | Main and Nozzle dictionaries include `config_transparent` and `transparent_send` |
| Confirm stock logs use `transparent_send` | ✅ | Historical stock logs contain valid `transparent_response` traffic |
| Clean minimal transparent-channel probe | 🟡 | MCU accepted `config_transparent`, but test frame returned empty payload; downstream controller was not prepared through that path |
| Open `/dev/ttyS5` directly | ✅ | 230400 8N1 |
| Linux RS-485 ioctl required | ✅ | Not required for tested traffic; `TIOCGRS485` flags remain disabled |
| Direct X controller query on T113 | ✅ | Address `0x81` replied correctly |
| External-host X query through third USB channel | ✅ | End-to-end response verified |
| External-host Y query through third USB channel | ✅ | Address `0x82` replied correctly |
| Determine practical external-host motor transport | ✅ | Raw third-channel bridge to `/dev/ttyS5` works for X/Y read-only queries |
| Validate write/tuning operations | ⏳ | Pending; no tuning or persistent controller changes performed |

Verified read-only address-query results:

```text
X TX: f7 81 04 00 0e 02 80
X RX: f7 81 04 00 0e 81 00

Y TX: f7 82 04 00 0e 02 80
Y RX: f7 82 04 00 0e 82 09
```

## CFS

| Test | Status | Result |
|---|---:|---|
| Identify CFS/RS-485 host UART | ✅ | `/dev/ttyS5` |
| Expose CFS/RS-485 UART to external host | ✅ | Third gadget serial channel verified |
| CFS `A2` online-check probe | 🟡 | No reply, but CFS was physically disconnected during test |
| CFS `A1` discovery probe | 🟡 | No reply, but CFS was physically disconnected during test |
| Validate connected CFS from external host | ⏳ | Next CFS test once hardware is connected |

The no-response CFS tests are **not classified as failures** because the CFS unit was disconnected. The transport itself is independently validated by successful X/Y traffic on the same `/dev/ttyS5` path.

## Display / UI

| Test | Status | Result |
|---|---:|---|
| Keep original physical K2 display | 🟡 | Design choice confirmed; final OpenHost deployment pending |
| Run HelixScreen on K2 Pro original display | ⏳ | Planned |
| Connect HelixScreen to remote Moonraker | ⏳ | Planned |
| Remove dependency on Creality UI stack | ⏳ | Planned |

## Cartographer and nozzle-camera connector

The current K2 Pro test unit intentionally differs from stock wiring.

| Test / choice | Status | Result |
|---|---:|---|
| Cartographer installed on internal USB path | ✅ | Working on the test unit |
| Cartographer connected through Nozzle MCU camera connector | ✅ | The USB connection originally intended for the nozzle camera has been repurposed for Cartographer |
| Stock nozzle camera retained | ❌ | Intentionally removed/not used on this test unit |
| Additional external Cartographer USB cable required | ✅ | No; the internal nozzle-camera USB path avoids an additional external cable |
| Preserve the printer's single exposed external USB port for other uses | ✅ | Current wiring avoids consuming that port for Cartographer |

The stock nozzle camera is intended for Creality's automatic flow/pressure-related calibration workflow. That function is not required for the current test unit, so the connector was deliberately reassigned to Cartographer. This is a **test-unit wiring choice**, not a requirement for every K2-OpenHost installation.

The exact relationship between the externally exposed USB port, the internal `CREALITY CAM`, and the service/recovery Micro-USB path still needs hardware/topology verification.

## Reliability

| Test | Status | Result |
|---|---:|---|
| Short serial gadget test | ✅ | Bidirectional traffic verified |
| Main MCU live protocol session | ✅ | Verified |
| Nozzle MCU live protocol session | ✅ | Verified |
| Three-interface enumeration | ✅ | Verified |
| Gadget unbind/rebind behavior | 🟡 | Interfaces reappear; existing bridge processes exit and must be restarted |
| 1-hour idle link test | ⏳ | Pending |
| Long print | ⏳ | Pending |
| Reboot recovery | 🟡 | Stock USB host behavior returns after reboot; OpenHost boot automation not implemented |
| Watchdog/fail-safe behavior | ⏳ | Pending |

## Safety policy during reverse engineering

All current experiments on the working stock slot are runtime-only and reboot-reversible. No active-slot configuration, boot environment, MCU firmware, persistent service enable state, or persistent motor-controller parameters are modified during this validation phase.

## Current milestone

The current transport milestone is now verified on hardware:

> **One physical Micro-USB link exposes three independent Generic Serial interfaces from the K2 Pro T113 to an external Linux host. The channels have been validated as Main MCU (`ttyS2`), Nozzle MCU (`ttyS3`), and RS-485 (`ttyS5`). Main and Nozzle Klipper protocol sessions can run concurrently, and the third RS-485 channel has successfully queried both original closed-loop X and Y motor controllers end-to-end from the external host. No MCU reflashing was required.**

Next priorities are connected-CFS validation, USB topology mapping, reconnect/endurance testing, boot automation, and eventual HelixScreen/Moonraker integration.
