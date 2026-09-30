# USB Gadget and Micro-USB Investigation

> Scope: Creality K2 Pro test unit. This document separates direct hardware observations from assumptions still awaiting validation.

## 1. Initial discovery

The K2 Pro stock Linux image exposes an Allwinner USB Device Controller:

```text
/sys/class/udc/4100000.udc-controller
```

Kernel configuration on the tested unit includes:

```text
CONFIG_USB_GADGET=y
CONFIG_USB_LIBCOMPOSITE=y
CONFIG_USB_F_SERIAL=y
CONFIG_USB_CONFIGFS=y
CONFIG_USB_CONFIGFS_UEVENT=y
CONFIG_USB_CONFIGFS_SERIAL=y
CONFIG_USB_CONFIGFS_F_FS=y
```

CDC ACM is not enabled in the tested kernel, but Generic Serial is built in and usable.

## 2. USB0 normal role

In stock operation USB0 is a host path for the internal chamber camera. The host controllers are:

```text
4101000.ehci0-controller
4101400.ohci0-controller
```

Switching USB0 to device mode cleanly disconnects the camera and removes those host controllers.

## 3. Switching USB0 to device mode

The vendor OTG driver exposes runtime role-selection nodes under:

```text
/sys/devices/platform/soc@3000000/soc@3000000:usbc0@0
```

Reading `usb_device` switches USB0 to device mode. On the tested unit this returned:

```text
device_chose finished!
```

The operation is runtime-only; a reboot restores stock USB-host behavior.

## 4. Vendor Generic Serial gadget

The stock utility:

```text
/bin/setusbconfig
```

supports `gser`. Running:

```sh
/bin/setusbconfig gser
```

creates the initial function:

```text
functions/gser.usb0
/dev/ttyGS0
```

with:

```text
VID:     0x0525
PID:     0xa4a6
Product: Gadget Serial
UDC:     4100000.udc-controller
```

## 5. Physical Micro-USB link

With an external Linux host connected to the K2 Pro service/recovery Micro-USB connector, the gadget enumerates successfully at USB 2.0 High-Speed:

```text
480M
```

Host-side enumeration uses the Linux `usbserial_generic` driver. The development host exposes `/dev/ttyUSB*` devices after binding VID:PID `0525:a4a6`.

Bidirectional transfer was verified between `/dev/ttyUSB0` and `/dev/ttyGS0`.

## 6. Three simultaneous Generic Serial functions

ConfigFS was extended at runtime with two additional serial functions:

```text
gser.usb0  port_num=0  -> /dev/ttyGS0
gser.usb1  port_num=1  -> /dev/ttyGS1
gser.usb2  port_num=2  -> /dev/ttyGS2
```

All three functions were linked into the same configuration and rebound to the same UDC.

The external Linux host then enumerated one USB device with three vendor-specific interfaces:

```text
If 0 -> usbserial_generic -> /dev/ttyUSB0
If 1 -> usbserial_generic -> /dev/ttyUSB1
If 2 -> usbserial_generic -> /dev/ttyUSB2
```

The full device remained negotiated at 480M.

This directly verifies that the stock K2 Pro kernel and ConfigFS implementation can expose at least three simultaneous Generic Serial channels through the single physical Micro-USB connection.

## 7. Verified UART mapping through the gadget

Runtime byte-transparent bridges were used on the T113:

```text
/dev/ttyGS0 <-> /dev/ttyS2   Main MCU
/dev/ttyGS1 <-> /dev/ttyS3   Nozzle MCU
/dev/ttyGS2 <-> /dev/ttyS5   RS-485 bus
```

All three underlying UARTs are used at 230400 baud in the tested stock configuration.

Main and Nozzle MCU protocol sessions were verified simultaneously from external Kalico. The original MCU firmware was not reflashed.

## 8. RS-485 through the third USB serial channel

`/dev/ttyS5` was first tested locally on the T113 and then through the complete external-host path.

Linux RS-485 ioctl state was read as disabled:

```text
SER_RS485_ENABLED = false
```

Despite this, normal 230400 8N1 userspace serial I/O works correctly for the tested bus traffic. No explicit RTS toggling or `TIOCSRS485` configuration was required.

A read-only closed-loop X controller query sent directly on `/dev/ttyS5` returned:

```text
TX: f7 81 04 00 0e 02 80
RX: f7 81 04 00 0e 81 00
```

The same query then succeeded from the external host through:

```text
/dev/ttyUSB2
  -> gser.usb2
  -> /dev/ttyGS2
  -> byte-transparent bridge
  -> /dev/ttyS5
  -> RS-485
  -> X controller
```

The Y controller also replied correctly:

```text
TX: f7 82 04 00 0e 02 80
RX: f7 82 04 00 0e 82 09
```

This confirms end-to-end third-channel access to the K2 Pro RS-485 bus from the external host.

## 9. CFS status

The same `/dev/ttyS5` bus is used by the CFS path in the stock configuration.

Initial `A2` online-check and `A1` discovery probes received no reply, but the CFS unit was physically disconnected during those tests. These results are therefore not considered transport failures.

Connected-CFS validation remains pending.

## 10. Gadget rebind behavior

Unbinding the ConfigFS gadget removes the host interfaces and invalidates currently open `/dev/ttyGS*` file descriptors. As a result, active byte-bridge processes exit when the gadget is unbound.

After rebinding, `/dev/ttyGS0`, `/dev/ttyGS1`, and `/dev/ttyGS2` are recreated and the host re-enumerates `/dev/ttyUSB0`, `/dev/ttyUSB1`, and `/dev/ttyUSB2`. The bridge processes must then be restarted.

This behavior is expected and must be handled by the future OpenHost service manager.

## 11. Current verified transport

```text
External Linux host

/dev/ttyUSB0
    |
    v
T113 gser.usb0 / ttyGS0
    |
    v
/dev/ttyS2 -> Main MCU

/dev/ttyUSB1
    |
    v
T113 gser.usb1 / ttyGS1
    |
    v
/dev/ttyS3 -> Nozzle MCU

/dev/ttyUSB2
    |
    v
T113 gser.usb2 / ttyGS2
    |
    v
/dev/ttyS5 -> RS-485 -> X/Y verified, CFS pending
```

## 12. Remaining USB-layer work

The core transport is now verified. Remaining work includes:

- sustained multi-channel traffic;
- long idle operation;
- repeated disconnect/reconnect cycles;
- repeated role switching;
- deterministic bridge restart after USB rebind;
- stable host naming/udev rules;
- boot-time gadget and bridge automation;
- failure recovery when the external host is absent or rebooting.

## 13. Returning to stock USB host mode

The current test procedure remains runtime-only. To unbind the gadget and return USB0 to host mode:

```sh
ROLE=/sys/devices/platform/soc@3000000/soc@3000000:usbc0@0

echo "" > /sys/kernel/config/usb_gadget/g1/UDC 2>/dev/null
cat $ROLE/usb_host
```

If needed:

```sh
/usr/bin/chamber_cam_power.sh restart
```

A reboot remains the authoritative recovery path during development.
