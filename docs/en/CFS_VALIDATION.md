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

| Operation | Code | Status | Result |
|---|---:|---:|---|
| Discover material box | `A1` | ✅ | Material Box discovered in application mode |
| Assign address | `A0` | ✅ | Address `0x01` accepted |
| Online check | `A2` | ✅ | Valid reply from address `0x01` |
| Address-table query | `A3` | ✅ | Valid reply from address `0x01` |

The 12-byte CFS UniID is intentionally not published.

## Verified read-only operational commands

| Operation | Code | Status | Hardware result |
|---|---:|---:|---|
| Box state | `0x0A` | ✅ | 4-byte steady format and `STATUS=0x30` slot events verified |
| Version / serial query | `0x14` | ✅ | Valid 22-byte ASCII reply; identifier not published |
| Slot / hardware mask | `0x08` | ✅ | `0x0F` with A-D present; `0x0E` with A empty and B-D present |
| Buffer state | `0x05` | ✅ | `0x02` with buffer physically empty |
| RFID/material records | `0x02` | ✅ | Empty, non-RFID and RFID slots distinguished correctly |
| Remaining value | `0x03` | ✅ | Positional A-D values track physical state |

## Slot-state correlation

Controlled physical test:

- slot A empty;
- slot B containing an RFID spool;
- slots C and D containing filament without RFID.

Observed state:

```text
READ_MATERIAL:
A:none;B:<40-character RFID record>;C:unknown;D:unknown;

READ_REMAIN:
A=0, B=13, C=100, D=100

SLOT_MASK:
0x0E
```

This verifies on the K2 Pro test unit that:

- `none` = empty slot;
- `unknown` = filament present without identified RFID;
- a valid tag produces the 40-character RFID record;
- `READ_REMAIN=0` follows the emptied slot;
- command `0x08`, channel `0x00`, exposes a slot-presence bitmask.

The raw RFID record is intentionally redacted.

## Async slot event

After changing the physical slot state, `CMD_BOX_STATE (0x0A)` returned:

```text
STATUS = 0x30
DATA   = 02 03 00 00
```

Public reverse-engineering identifies `0x30` as `SLOT_EVENT`; the four data bytes represent A/B/C/D event phases and `0x03` means insert complete. In this test the second byte matches insertion of the RFID spool into slot B.

## Jacob10383 Kalico extras

K2-OpenHost reuses Jacob10383's GPLv3 CFS stack instead of reimplementing the protocol:

- `serial_485.py`
- `box.py`
- `box_addr.py`
- `box_catalog.py`
- `box_change.py`
- `box_protocol.py`

The Jacobean firmware 6.18 extras were downloaded from its content-addressed store and SHA-256 verified inside the volatile `/dev/shm/k2-openhost-kalico` clone. The firmware installer was not executed and no persistent K2 system state was modified.

## Native Jacob transport verified

`Serial_485_Wrapper` was connected directly to `/dev/ttyUSB2` without patches:

```text
connected: true
port: /dev/ttyUSB2
baud: 230400
A2 response: valid
CRC: valid
crc_errors: 0
timeouts: 0
unmatched: 0
send_errors: 0
reader_errors: 0
```

This validates Jacob's native transport end-to-end through K2-OpenHost.

## Jacob AutoAddressManager and BoxDriver

Jacobean 6.18 `AutoAddressClient`, `AutoAddressManager`, and `BoxDriver` were run directly over the OpenHost transport.

```text
AutoAddressManager:
online addresses: [1]
known addresses: [1]
errors: []

query_slot_mask:
status: 0x00
value: 0x0E

query_hub_mask:
status: 0x00
value: 0x00

query_buffer:
status: 0x00
value: 2

query_rfid_records:
A: none
B: RFID_RECORD_40_CHARS
C: unknown
D: unknown

query_rfid_remaining:
[0, 13, 100, 100]
```

`hub_mask=0x00` is verified only in the current state with no loaded CFS path; its semantics under load still need correlation.

The complete test produced:

```text
tx_frames: 6
rx_frames: 6
crc_errors: 0
invalid_len: 0
unmatched: 0
stale_dropped: 0
timeouts: 0
send_errors: 0
reader_errors: 0
```

Transport, addressing, A2 decoding, slot mask, hub mask, buffer, RFID, and remaining queries therefore work unmodified.

## BOX_STATE compatibility delta: Jacobean 6.18 vs K2 Pro

The first actual compatibility delta is `CMD_GET_BOX_STATE (0x0A)`.

The K2 Pro CFS returns this steady-state form:

```text
STATUS = 0x00
DATA   = 1f 23 00 00
```

Public wire-correct reverse-engineering describes it as:

```text
[b0][b1][b2][b3]
 b0/b1 = opaque firmware base
 b2    = substatus
 b3    = load flag
         0x00 = feed/change
         0x02 = loaded/print-locked
```

`b0/b1` vary between reads and must not be treated as state.

Jacobean 6.18 `box_protocol.py`, however, expects a 6-byte steady payload and raises:

```text
ProtocolError: box-state payload has the wrong shape
```

The K2 Pro frame is complete and CRC-valid. This is a decoder incompatibility, not a transport failure.

## Compatibility strategy

The first OpenHost patch will intentionally be conservative:

1. accept the 4-byte steady `0x0A` form as well;
2. keep `b0/b1` opaque;
3. expose the real `substatus` and `load_flag`;
4. do not fabricate missing temperature, humidity, `box_state`, or `downstream_mask` values;
5. keep `STATUS=0x30` slot-event parsing unchanged;
6. validate the patch in `/dev/shm` before enabling full `box.py`.

That is sufficient for monitoring. Before automatic load/unload is enabled, the loaded slot/path must be derived reliably, likely by correlating the load flag with separate bus queries instead of synthesizing the Jacobean 6-byte model.
