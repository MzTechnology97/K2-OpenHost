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

Before testing, it reported:

```text
usb_host
```

`lsusb` showed:

```text
Bus 003 Device 002: ID 1d6c:0103 Creality 3D Technology CREALITY CAM
```

The camera was physically attached through:

```text
4101000.ehci0-controller
```

with the corresponding OHCI controller at:

```text
4101400.ohci0-controller
```

This verifies that USB0 is normally used as a host bus for the internal chamber camera.

## 3. Switching USB0 to device mode

The vendor OTG driver exposes read-triggered sysfs entries including:

```text
usb_host
usb_device
usb_null
otg_role
```

On the test unit, executing:

```sh
ROLE=/sys/devices/platform/soc@3000000/soc@3000000:usbc0@0
cat $ROLE/usb_device
```

returned:

```text
device_chose finished!
```

The kernel then logged the expected transition:

```text
rmmod_host_driver
sunxi_usb_disable_ehci
4101000.ehci0-controller remove
usb 3-1: USB disconnect
sunxi_usb_disable_ohci
4101400.ohci0-controller remove
insmod_device_driver
```

The internal `CREALITY CAM` disconnected as part of the switch.

This is a direct hardware verification that USB0 can be dynamically moved from host mode to device mode under the running Tina Linux system.

## 4. Vendor USB gadget tooling

The stock filesystem includes:

```text
/bin/setusbconfig
```

Inspection of the script/binary strings shows built-in support for multiple USB gadget functions, including:

- ADB;
- MTP;
- mass storage;
- RNDIS;
- NCM;
- HID;
- loopback;
- printer gadget;
- generic serial (`gser`).

For generic serial, the vendor implementation creates:

```text
/sys/kernel/config/usb_gadget/g1/functions/gser.usb0
```

and uses:

```text
VID: 0x0525
PID: 0xa4a6
Product: Gadget Serial
```

The utility automatically binds the gadget to the available UDC.

## 5. Verified generic serial gadget creation

After switching USB0 to device mode, the command:

```sh
/bin/setusbconfig gser
```

completed successfully with exit status `0`.

The following were then verified:

```text
/dev/ttyGS0
```

exists as a character device.

ConfigFS contains:

```text
/sys/kernel/config/usb_gadget/g1/functions/gser.usb0
```

The active configuration links that function:

```text
configs/c.1/gser.usb0 -> .../functions/gser.usb0
```

The gadget IDs are:

```text
idVendor  = 0x0525
idProduct = 0xa4a6
product   = Gadget Serial
```

The UDC binding is:

```text
4100000.udc-controller
```

and the UDC `function` field reports:

```text
g1
```

## 6. Current endpoint state

Before connecting an external USB host, the UDC correctly reports:

```text
state:         not attached
current_speed: UNKNOWN
maximum_speed: high-speed
function:      g1
```

This is expected: the gadget is configured and bound, but there is no external host connected yet.

## 7. Physical Micro-USB connector

The K2 mainboard contains a Micro-USB service/recovery connector known to be used for full-memory recovery/flashing workflows.

The working hypothesis is that this connector is physically connected to the same USB0 device path used by the Allwinner UDC.

### Important status

This physical runtime data path is **not yet confirmed**.

The next test is to connect the Micro-USB port to a Linux host after enabling `gser` and verify enumeration as:

```text
0525:a4a6 Gadget Serial
```

Expected host-side setup if the generic usbserial driver does not bind automatically:

```sh
sudo modprobe usbserial
echo 0525 a4a6 | sudo tee /sys/bus/usb-serial/drivers/generic/new_id
```

A device such as `/dev/ttyUSB0` should then appear.

## 8. Planned bidirectional test

K2 side:

```sh
cat /dev/ttyGS0
```

External Linux host:

```sh
echo "TEST_HOST_TO_K2" > /dev/ttyUSB0
```

Reverse direction:

External host:

```sh
cat /dev/ttyUSB0
```

K2:

```sh
echo "TEST_K2_TO_HOST" > /dev/ttyGS0
```

This test is still pending.

## 9. Returning to normal USB host mode

The runtime experiment does not currently require persistent configuration changes.

To unbind the gadget and return USB0 to host mode:

```sh
ROLE=/sys/devices/platform/soc@3000000/soc@3000000:usbc0@0

echo "" > /sys/kernel/config/usb_gadget/g1/UDC 2>/dev/null
cat $ROLE/usb_host
```

The vendor camera helper may also be used if needed:

```sh
/usr/bin/chamber_cam_power.sh restart
```

A reboot of the tested machine restores the normal stock USB host behavior as well.

## 10. Why this matters for K2-OpenHost

If the physical Micro-USB enumeration test succeeds, the original T113 board can expose virtual serial links to an external Linux host without additional Arduino/RP2040 bridge hardware.

The next target becomes:

```text
External host /dev/ttyUSBx
        |
        v
Micro-USB -> T113 UDC -> /dev/ttyGSx
        |
        v
userspace byte-transparent bridge
        |
        v
T113 /dev/ttySx
        |
        v
Original K2 MCU
```

That would allow the external Kalico host to communicate with the original MCU architecture while preserving the K2 mainboard.
