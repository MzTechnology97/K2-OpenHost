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

The first validation patch kept the first two bytes opaque as `firmware_base` and exposed `substatus` / `load_flag`. Firmware analysis of the CFS 1.1.3 image and live captures later established the layout, now decoded by the `box_k2pro` adapter:

- signed temperature in °C;
- humidity in %;
- event byte;
- box state.

The values once recorded as opaque bases (`0x1E22`, `0x1E23`, `0x1F23`) are consistent with this: 30–31 °C and 34–35 % humidity. The opaque fields remain only as a fallback in `box_protocol.py` when `[box_k2pro]` is not loaded. The legacy 6-byte decoder path and asynchronous `STATUS=0x30` slot-event path remain available.

### CFS firmware 1.5.3: back to 6 bytes

After the boards were updated to Creality 1.1.7.0 (CFS application `cfs0_000_153`, reported as 1.5.3), the same CFS answers command `0x0A` with the original 6-byte payload. Checked on 2026-10-07 through `boxes[].state_payload_bytes` (kalico-k2pro PR #35), which reports the length of the last reply per unit: `6`, with 29 °C and 38 % humidity.

The 6-byte reply is decoded by the original Jacobean path in `box_protocol.py`: signed temperature, humidity, box state and slot mask. `box_k2pro` handles only 4-byte replies and passes every other length through, so both firmware versions work with the same configuration.

Raw replies read with `BOX_DEBUG RAW=1` on the same day: idle and empty `1d 26 00 00 00 00` (29 °C, 38 %, event 0, state IDLE, slot mask 0); with slot 1 loaded to the nozzle `1d 26 00 02 01 00` (state PRINT, slot mask `0x01`). The loaded slot therefore comes from the CFS itself; the printhead sensor is only the fallback used when no unit reports a loaded slot. The 4-byte path is still needed for a CFS on 1.1.3, for example after booting slot A, which flashes its own 1.1.0.94 firmware files.

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

This observation-mode milestone remains the read-only safety baseline.

## Operational-mode validation

The complete CM5 Kalico process is now running the Box stack with `observation_mode: false`. On the real K2 Pro we have verified:

- CFS enumeration and normalized state reach `driver_ready=true` / `data_ready=true`;
- K2 Pro environment reporting including temperature and humidity;
- persistent filament inventory and K2-RFID/Creality material-database import;
- automatic resolution of custom K2-RFID material IDs without treating spool color as a new material profile;
- per-slot forced RFID reread;
- hardware remaining-material percentage;
- independent remaining estimates for different physical spools even when K2-RFID tags use the same `000001` serial;
- runout-group ordering by lowest known compatible remaining percentage.

A live custom Bambulab PLA Basic RFID material ID was resolved on two different colored spools. The CFS reported 9% and 10% respectively; OpenHost tracked them independently as about 29.7 m and 33.0 m from a 330 m tagged length.

The live remaining estimator also subtracts positive `print_stats.filament_used` deltas from the active RFID spool and persists the estimate. This logic is implemented and source-tested; a complete supervised print is still required to validate the real-time estimate over a full print.

## Next validation

The next CFS milestone is a controlled mapped `BOX_PRINT_START`, followed by a real multimaterial tool change, runout/recovery test and complete supervised print.