# USB gadget transport on the K2 Pro

Updated: **2026-10-01**.

## Verified facts

The K2 Pro T113 exposes a USB Device Controller at `4100000.udc-controller`. Its kernel includes ConfigFS/libcomposite and Generic Serial gadget support.

Direct ConfigFS configuration has been verified with **three simultaneous serial functions**:

- `gser.usb0` -> `/dev/ttyGS0`
- `gser.usb1` -> `/dev/ttyGS1`
- `gser.usb2` -> `/dev/ttyGS2`

The CM5/external host sees the same composite device as three `usbserial_generic` interfaces, currently mapped to `/dev/ttyUSB0..2`. Enumeration is USB 2.0 High-Speed (**480M**).

## Verified mapping

```text
/dev/ttyUSB0 <-> ttyGS0 <-> ttyS2 <-> Main MCU
/dev/ttyUSB1 <-> ttyGS1 <-> ttyS3 <-> Nozzle MCU
/dev/ttyUSB2 <-> ttyGS2 <-> ttyS5 <-> RS-485 / CFS / closed-loop
```

Main, Nozzle and RS-485 operate at 230400 baud in the validated configuration.

## Final gadget role

The three gadget serial functions are now intentionally dedicated to the original K2 hardware paths above.

A fourth Cartographer channel was prototyped through a custom MUX/DEMUX path. The experiment demonstrated that live Cartographer MCU data could traverse the T113 and service-port gadget, but reset/re-enumeration changed the T113-side PTY and added unnecessary reconnect complexity.

The project therefore **does not plan to use `ttyGS3` / `/dev/ttyUSB3` for Cartographer in the final architecture**. Cartographer should connect directly to the CM5 USB host and use a persistent `/dev/serial/by-id/...` path.

## Process ownership requirement

Each UART/gadget pair must have exactly one bridge process. During the Cartographer multiplexing experiment, a duplicate GS2 bridge was found opening the same `ttyGS2`/`ttyS5` path while another transport process was active. This produced RS-485/motor-control failures.

After removing the duplicate and restoring one direct GS2 bridge, closed-loop motor communication returned to normal.

For the stable topology:

```text
one process: ttyGS0 <-> ttyS2
one process: ttyGS1 <-> ttyS3
one process: ttyGS2 <-> ttyS5
```

Do not run the old Cartographer MUX on GS2 at the same time.

## Role-switch caveat

USB0 is dual-role. In stock operation it participates in the internal USB-host topology, including the chamber-camera path. Switching USB0 into device/gadget mode therefore changes the stock USB topology and can disconnect the camera. Runtime tests are designed to be reboot-reversible.

Unbinding/rebinding the gadget recreates the `ttyGS*` endpoints. Any bridge processes holding those devices must be restarted after a rebind.

## Bridge model

The stable bridge is intentionally byte-transparent. The T113 should not parse Klipper or CFS frames unless a future hardware-specific service proves necessary.

This separation keeps the CM5 as the planner/Python host while the T113 acts as the hardware gateway for the original K2 buses.

## Validated downstream use

Using these three channels, the real K2 Pro has now completed external-host tests for:

- Main + Nozzle MCU simultaneous sessions;
- closed-loop X/Y motor communication;
- normal CoreXY movement;
- X/Y stall homing;
- full PRTouch homing;
- bed/nozzle/chamber heater operation;
- emergency heater shutdown;
- Klippain-ShakeTune resonance measurement;
- protected CFS observation traffic.

## What is not claimed

- The physical USB topology of every internal connector is not fully mapped for every K2 variant.
- Persistent boot packaging is still evolving.
- Cartographer direct-USB validation is a separate remaining milestone and is not provided by the three gadget channels.