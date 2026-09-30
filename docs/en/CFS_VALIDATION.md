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

The K2/CFS extras are not necessarily stored in the Kalico repository itself; Jacobean firmware distributes them separately. They were initially absent from the volatile Kalico clone used by OpenHost, so the first transport-only bootstrap could not load `serial_485`/`motor_control`. The Jacobean firmware 6.18 extras were then downloaded from its content-addressed store and verified by SHA-256 without executing the firmware installer or changing persistent system state.

The important OpenHost-specific work is the transport substitution:

```text
Jacob serial_485 / box stack
        -> /dev/ttyUSB2 on CM5
        -> K2 OpenHost USB/serial bridge
        -> T113 /dev/ttyS5
        -> CFS RS-485 bus
```

`serial_485.py` already accepts a configurable serial device and uses 230400 8N1, so the expected CM5 configuration is simply `serial: /dev/ttyUSB2`.

## Native Jacob transport verified

Jacob10383's original `Serial_485_Wrapper` was loaded directly from the volatile Kalico tree and connected to `/dev/ttyUSB2` without patches. The wrapper opened the port correctly at 230400 baud, and a native A2 query to the CFS at address `0x01` returned a valid response:

```text
connected: true
port: /dev/ttyUSB2
baud: 230400
A2 response: valid
CRC: valid
tx_frames: 1
rx_frames: 1
crc_errors: 0
timeouts: 0
unmatched: 0
send_errors: 0
reader_errors: 0
```

The identity payload from the A2 response is intentionally redacted. This validates Jacob's native RS-485 transport end-to-end through K2-OpenHost with no changes to `serial_485.py`.

## Next validation step

Use Jacob's original `box_protocol.AutoAddressClient` and `box_addr.AutoAddressManager` over the validated transport. With one box already online at `0x01`, the initial test remains read-only: A2 should identify the box before the manager has any need to discover or assign an address. Then instantiate `BoxDriver` and compare slot mask, buffer, box state, RFID records and remaining values against the raw results already verified.
