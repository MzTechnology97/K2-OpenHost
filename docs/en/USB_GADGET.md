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

Notably, CDC ACM is not enabled in the current kernel configuration, but generic serial gadget support is available.

## 2. USB0 normal role

The Allwinner OTG manager exposes:

```text
/sys/devices/platform/soc@3000000/soc@3000000:usbc0@0/otg_role
```

In stock operation, USB0 is used in host mode for the internal chamber camera. The camera was observed as:

```text
Bus 003 Device 002: ID 1d6c:0103 Creality 3D Technology CREALITY CAM
```

through:

```text
4101000.ehci0-controller
```

with the corresponding OHCI controller at:

```text
4101400.ohci0-controller
```

## 3. Switching USB0 to device mode

The vendor OTG driver exposes read-triggered sysfs entries including:

```text
usb_host
usb_device
usb_null
otg_role
```

On the test unit:

```sh
ROLE=/sys/devices/platform/soc@3000000/soc@3000000:usbc0@0
cat $ROLE/usb_device
```

returned:

```text
device_chose finished!
```

The kernel logged:

```text
rmmod_host_driver
sunxi_usb_disable_ehci
4101000.ehci0-controller remove
usb 3-1: USB disconnect
sunxi_usb_disable_ohci
4101400.ohci0-controller remove
insmod_device_driver
```

This directly verifies that USB0 can be dynamically switched from host mode to device mode while Tina Linux is running.

## 4. Vendor USB gadget tooling

The stock filesystem contains:

```text
/bin/setusbconfig
```

The vendor tool exposes a Generic Serial (`gser`) configuration. Running:

```sh
/bin/setusbconfig gser
```

creates:

```text
/sys/kernel/config/usb_gadget/g1/functions/gser.usb0
/dev/ttyGS0
```

with:

```text
VID:     0x0525
PID:     0xa4a6
Product: Gadget Serial
UDC:     4100000.udc-controller
```

The active configuration links:

```text
configs/c.1/gser.usb0 -> .../functions/gser.usb0
```

## 5. Verified gadget state with external host attached

With a Raspberry Pi CM5 physically connected to the K2 Pro Micro-USB service/recovery connector, the K2 UDC reported:

```text
state:         configured
current_speed: high-speed
maximum_speed: high-speed
function:      g1
```

and the kernel logged:

```text
android_work: sent uevent USB_STATE=CONNECTED
configfs-gadget gadget: high-speed config #1: c
android_work: sent uevent USB_STATE=CONFIGURED
```

This confirms successful runtime enumeration of the gadget through the physical Micro-USB connector.

## 6. Raspberry Pi CM5 host-side enumeration

The external host used for the test was a Raspberry Pi CM5 running Debian Bookworm with Linux 6.12.

`lsusb` reported:

```text
0525:a4a6 Netchip Technology, Inc. Linux-USB Serial Gadget
```

The USB topology reported the link at:

```text
480M
```

The interface did not bind automatically to a serial driver, so the Linux generic usbserial driver was attached manually:

```sh
sudo modprobe usbserial
echo 0525 a4a6 | sudo tee /sys/bus/usb-serial/drivers/generic/new_id
```

The kernel then reported:

```text
usbserial_generic ... generic converter detected
usb ... generic converter now attached to ttyUSB0
```

and the host exposed:

```text
/dev/ttyUSB0
```

The `usbserial_generic` warning that the driver is intended for testing and one-off prototypes is expected for this development-stage setup.

## 7. Verified bidirectional serial transfer

### CM5 -> K2

K2:

```sh
cat /dev/ttyGS0
```

CM5:

```sh
printf 'K2_OPENHOST_CM5_TO_K2_001\n' | sudo tee /dev/ttyUSB0
```

The K2 successfully received:

```text
K2_OPENHOST_CM5_TO_K2_001
```

### K2 -> CM5

CM5:

```sh
sudo cat /dev/ttyUSB0
```

K2:

```sh
printf 'K2_OPENHOST_K2_TO_CM5_001\n' > /dev/ttyGS0
```

The CM5 successfully received:

```text
K2_OPENHOST_K2_TO_CM5_001
```

Therefore the following path is now directly verified:

```text
Raspberry Pi CM5 /dev/ttyUSB0
        ^
        | bidirectional serial
        v
USB 2.0 High-Speed (480M)
        ^
        |
        v
K2 Pro Micro-USB service/recovery connector
        ^
        |
        v
Allwinner T113 UDC / gser.usb0
        ^
        |
        v
K2 Pro /dev/ttyGS0
```

## 8. What remains unverified on the USB layer

The basic data transport is verified. Remaining USB-specific reliability tests include:

- disconnect/reconnect recovery;
- repeated host/device role switching;
- long idle operation;
- sustained serial traffic;
- boot-time automation;
- multi-function or multi-channel gadget configuration.

## 9. Returning to normal USB host mode

The runtime experiment does not require persistent configuration changes.

To unbind the gadget and return USB0 to host mode:

```sh
ROLE=/sys/devices/platform/soc@3000000/soc@3000000:usbc0@0

echo "" > /sys/kernel/config/usb_gadget/g1/UDC 2>/dev/null
cat $ROLE/usb_host
```

If needed, the vendor camera helper can be called:

```sh
/usr/bin/chamber_cam_power.sh restart
```

A reboot also restores the normal stock USB host behavior on the tested unit.

## 10. Why this matters for K2-OpenHost

The physical Micro-USB test is successful. The original T113 board can expose a virtual serial link to an external Linux host without an additional Arduino, RP2040, USB-UART bridge, or replacement mainboard.

The next target is therefore:

```text
External Kalico host /dev/ttyUSBx
        |
        v
Micro-USB -> T113 UDC -> /dev/ttyGSx
        |
        v
byte-transparent userspace bridge
        |
        v
T113 /dev/ttySx
        |
        v
Original K2 Main / Nozzle MCU
```

The next hardware investigation is to identify the exact K2 Pro Main MCU and Nozzle MCU UART devices and baud rates, then validate the bridge without altering the original MCU firmware.
