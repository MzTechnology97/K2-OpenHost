# USB gadget transport on the K2 Pro

## Verified facts

The K2 Pro T113 exposes a USB Device Controller at `4100000.udc-controller`. Its kernel includes ConfigFS/libcomposite and Generic Serial gadget support.

The stock helper can create a Generic Serial gadget, and direct ConfigFS configuration has been verified with **three simultaneous serial functions**:

- `gser.usb0` -> `/dev/ttyGS0`
- `gser.usb1` -> `/dev/ttyGS1`
- `gser.usb2` -> `/dev/ttyGS2`

The CM5/external host sees the same composite device as three `usbserial_generic` interfaces, currently mapped to `/dev/ttyUSB0..2`. Enumeration is USB 2.0 High-Speed (**480M**).

## Verified mapping

```text
/dev/ttyUSB0 <-> ttyGS0 <-> ttyS2 <-> Main MCU
/dev/ttyUSB1 <-> ttyGS1 <-> ttyS3 <-> Nozzle MCU
/dev/ttyUSB2 <-> ttyGS2 <-> ttyS5 <-> RS-485 / CFS
```

Main and nozzle UARTs use 230400 baud. The RS-485 path is also operated at 230400 8N1.

## Role-switch caveat

USB0 is dual-role. In stock operation it participates in the internal USB-host topology, including the chamber-camera path. Switching USB0 into device/gadget mode therefore changes the stock USB topology and can disconnect the camera. Runtime tests are designed to be reboot-reversible.

Unbinding/rebinding the gadget recreates the `ttyGS*` endpoints. Any bridge processes holding those devices must be restarted after a rebind.

## Bridge model

The current bridge is intentionally byte-transparent. The T113 should not parse Klipper or CFS frames unless a future hardware-specific service proves necessary.

This separation makes it possible to keep the CM5 as the planner/Python host while using the T113 only as a hardware gateway.

## Planned fourth channel

The tested K2 Pro uses the internal toolhead/nozzle-camera USB route for Cartographer. A future test will identify the Cartographer serial device on the T113 and expose it through a fourth `gser` function (`ttyGS3` -> external `ttyUSB3`).

Normal Cartographer traffic is expected to be bridgeable, but firmware-update/bootloader operations may rely on USB control-line semantics that a simple serial-to-gser bridge does not automatically preserve. That must be validated separately.

## What is not claimed

- The final physical USB topology of every external/internal connector is not yet fully mapped.
- A fourth gadget serial interface for Cartographer has not yet been hardware-validated.
- Gadget operation is not yet packaged as the final persistent boot configuration.