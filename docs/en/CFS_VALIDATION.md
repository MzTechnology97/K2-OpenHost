# CFS validation

This document tracks hardware validation of the Creality Filament System (CFS) through the K2-OpenHost transport path.

## Verified transport path

```text
External Linux host / CM5
  -> /dev/ttyUSB2
  -> K2 USB gadget gser.usb2 / ttyGS2
  -> byte-transparent userspace bridge
  -> T113 /dev/ttyS5 @ 230400 8N1
  -> shared RS-485 bus
  -> CFS
```

The path is verified bidirectionally on hardware. No MCU reflashing is required.

## Addressing and discovery

The following CFS protocol operations have been verified end-to-end from the external host:

| Operation | Code | Status | Result |
|---|---:|---:|---|
| Discover material box | `A1` | ✅ | Material Box discovered in application mode |
| Assign address | `A0` | ✅ | Address `0x01` accepted |
| Online check | `A2` | ✅ | Valid reply from address `0x01` |
| Address-table query | `A3` | ✅ | Valid reply from address `0x01` |

The 12-byte CFS UniID is intentionally not published.

## Read-only operational commands

| Operation | Code | Status | Hardware result |
|---|---:|---:|---|
| Box state | `0x0A` | ✅ | Steady state and async slot-event replies verified |
| Version / serial query | `0x14` | ✅ | Valid 22-byte ASCII reply; device identifier is not published |
| Hardware status | `0x08` | ✅ | Stable flag reply observed |
| Buffer state | `0x05` | ✅ | `0x02` observed with buffer physically empty |
| RFID/material records | `0x02` | ✅ | Empty, non-RFID and RFID slots distinguished correctly |
| Remaining value | `0x03` | ✅ | Positional A-D values track slot state |

## Slot-state correlation

A controlled physical test was performed with:

- slot A empty;
- slot B containing an RFID spool;
- slots C and D containing filament without RFID.

Observed protocol state:

```text
READ_MATERIAL:
A:none;B:<40-character RFID record>;C:unknown;D:unknown;

READ_REMAIN:
A=0, B=13, C=100, D=100
```

This verifies on the K2 Pro test unit that:

- `none` represents an empty selected slot;
- `unknown` represents filament present without an identified RFID record;
- a valid RFID spool produces the expected 40-character record;
- `READ_REMAIN` reports `0` for the emptied slot and a non-zero remaining value for occupied slots.

The raw RFID record is intentionally redacted from public documentation.

## Async slot event

Immediately after changing the slot configuration, `CMD_BOX_STATE (0x0A)` returned:

```text
STATUS = 0x30
DATA   = 02 03 00 00
```

Public reverse-engineering of the Jacob10383 CFS stack identifies `0x30` as `SLOT_EVENT`, with the four data bytes representing per-slot event phases. Phase `0x03` means insert complete. In this test, the second byte corresponds to slot B and matches the newly inserted RFID spool.

## Jacob10383 Kalico extras

K2-OpenHost will not reimplement the CFS protocol. The target integration is the existing Jacob10383 GPLv3 CFS stack:

- `serial_485.py`
- `box.py`
- `box_addr.py`
- `box_catalog.py`
- `box_change.py`
- `box_protocol.py`

These modules are not necessarily tracked in Jacob's Kalico repository: the custom firmware distributes them as separate extras and they may appear as untracked files. The temporary Kalico clone used by OpenHost did not yet contain them at the tested commit/runtime state.

The important OpenHost-specific work is the transport substitution:

```text
Jacob serial_485 / box stack
        -> /dev/ttyUSB2 on CM5
        -> K2 OpenHost USB/serial bridge
        -> T113 /dev/ttyS5
        -> CFS RS-485 bus
```

`serial_485.py` already accepts a configurable serial device and defaults to 230400 8N1, so the expected CM5 configuration is simply `serial: /dev/ttyUSB2`.

## First transport-only attempt

Initial bootstrap of the temporary Kalico instance:

- observed Kalico commit: `aa6bf7d`;
- PySerial `3.4` available;
- Jacob K2/CFS extras were not present in the clone;
- Klippy started but did not open `/dev/ttyUSB2`;
- the log reported a `ModuleNotFoundError` for a missing K2 extra and an incomplete MCU configuration.

This is not classified as a bridge or `serial_485` failure: Jacob's transport module was not yet present in the runtime tree, so the native path was never exercised.

## Next validation step

Fetch the K2/CFS extras from Jacobean's content-addressed firmware store, verify their SHA-256 digests against the manifest, and copy them only into the volatile `/dev/shm/k2-openhost-kalico` clone.

Then repeat the native `serial_485.py` test against `/dev/ttyUSB2`. The full `[box]` module will only be enabled after transport succeeds, because `box.py` startup performs CFS initialization and RFID policy writes in addition to state reads.
