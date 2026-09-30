# CFS validation on K2 Pro

This document records only results validated on the project K2 Pro or directly derived from the cited public implementations. Private device identifiers and RFID payloads are intentionally omitted.

## Public implementation baseline

The CFS work uses public sources as implementation/reference material, especially:

- Creality K2-series Klipper extras;
- Jacob10383 / Jacobean K2 custom firmware extras;
- `gitstonelabs/creality-cfs-klipper` reverse engineering;
- related public K2/CFS work listed in `REFERENCES.md`.

Public reverse engineering is treated as an implementation baseline, not as proof that every K2 Pro behavior is identical. Hardware tests are used only where K2 Pro/OpenHost differences need validation.

## Transport

CFS shares the K2 RS-485 bus exposed by the stock system on `/dev/ttyS5` at 230400 baud. K2-OpenHost bridges it as:

```text
CM5 /dev/ttyUSB2 <-> T113 /dev/ttyGS2 <-> /dev/ttyS5 <-> CFS/RS-485
```

## Addressing verified

- frame head `0xF7`;
- CFS/MB broadcast address `0xFE`;
- A1 discovery verified repeatedly with a stable 12-byte private identifier;
- A0 assignment to address `0x01` verified;
- A2 online check verified;
- A3 table query verified.

## Read queries verified

The current physical setup has been read successfully for:

- slot-presence mask;
- buffer state;
- RFID state/records;
- remaining material;
- Box state.

No private RFID record is published in this repository.

## K2 Pro BOX_STATE delta

The Jacobean decoder originally expected a 6-byte steady payload. The tested K2 Pro returns a valid 4-byte steady payload.

K2-OpenHost keeps the first two bytes opaque as `firmware_base`, then exposes:

- `substatus`;
- `load_flag`.

The legacy 6-byte decoder path and asynchronous `STATUS=0x30` slot-event path remain available.

Repeated steady reads have produced changing opaque base values (for example `0x1E22`, `0x1E23`, `0x1F23`) while `substatus/load_flag` remained stable. This is why the first two bytes are not assigned an unsupported semantic meaning.

## Native Jacobean tests

### Serial_485_Wrapper

Direct operation over `/dev/ttyUSB2` is verified.

### AutoAddressManager + BoxDriver

With one connected CFS unit, read-only enumeration found address 1 without errors. Read queries returned the expected slot/buffer/RFID/remaining-material state.

### BoxStateReply compatibility patch

The patched native `box_protocol.py` successfully decoded both:

- K2 Pro steady 4-byte state;
- existing asynchronous slot events.

## Observation guard

A CFS-only proxy allows the known read/discovery function set and blocks all other CFS function codes before they reach `_write_frame`.

This guard is intentionally not implemented globally in `serial_485.py`, because the same bus also carries closed-loop motor/belt devices.

A direct self-test proved that function `0x0D` is blocked with no increase in the serial transport TX counter.

## Real Box() observation test

The actual Jacobean `Box()` class was instantiated with `observation_mode: True` and the real `/dev/ttyUSB2` transport.

Verified behavior:

- only transport diagnostic G-code was registered;
- one CFS driver was enumerated;
- CFS proxy active;
- RFID presence initialized by reads only;
- no runout observer installed;
- ten live state polls remained stable;
- internal `_poll()` completed;
- guard blocked `0x0D` before TX;
- **35 TX / 35 RX**;
- all transport error counters were zero.

This is the current strongest end-to-end CFS milestone.

## Next validation

The next CFS step is the same observation mode inside a complete CM5 Kalico/Klippy process rather than the standalone harness. State-changing CFS commands will remain disabled until the full host integration is stable.