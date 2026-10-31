# CFS protocol on the K2 Pro

What the K2 Pro's CFS does on the RS-485 bus, as verified on the reference printer. The Box stack comes from Jacob10383's K2 firmware; K2-OpenHost adds the K2 Pro differences described here. Private identifiers and RFID payloads are not published.

## Transport

The CFS shares the RS-485 bus with the closed-loop X/Y motors, at 230400 baud. K2-OpenHost carries it on the third gadget channel:

```text
host /dev/serial/by-id/...-if02 <-> T113 /dev/ttyGS2 <-> /dev/ttyS5 <-> CFS and motors
```

## Addressing

- Frame head `0xF7`, broadcast address `0xFE`.
- A1 discovery returns a stable 12-byte identifier; A0 assigns address `0x01`; A2 checks the unit is online; A3 reads the address table.
- After a power cycle the CFS answers at `0xFE` until it is enumerated again, so Kalico probes its runtime configuration only after `box:ready`.

## Box state (command `0x0A`)

The reply length depends on the CFS firmware:

| CFS firmware | Reply | Decoded by |
| --- | --- | --- |
| 1.1.3 | 4 bytes: temperature (signed, °C), humidity (%), event, box state | `box_k2pro` |
| 1.5.3 (`cfs0_000_153`, with the 1.1.7.0 boards) | 6 bytes: temperature, humidity, event, box state, slot mask | the original path in `box_protocol.py` |

`box_k2pro` handles only 4-byte replies and passes every other length on, so both firmware versions work with the same configuration. `boxes[].state_payload_bytes` reports the length of the last reply per unit.

Raw replies from 1.5.3 (`BOX_DEBUG RAW=1`): idle and empty `1d 26 00 00 00 00` (29 °C, 38 %, state IDLE, no slot); slot 1 loaded to the nozzle `1d 26 00 02 01 00` (state PRINT, slot mask `0x01`). The loaded slot therefore comes from the CFS itself; the printhead sensor is only the fallback when no unit reports one.

## Observation mode

`observation_mode: True` in `[box]` runs the real CFS stack read-only, for a first test on a new printer or after a firmware change:

- a proxy lets through only discovery and known read queries, and blocks every other CFS function code before it is sent (checked: a blocked `0x0D` never reached the transport);
- no `BOX_*` or `T0`, `T1`... commands, no cut sensor or runout hooks, no RFID write at start;
- state is kept in `/dev/shm` unless set otherwise.

The guard covers only the CFS: the motors on the same bus keep working. On the reference printer it enumerated address 1, read the slots and RFID, and ran ten state polls with 35 frames sent and 35 received, no errors. Normal operation is `observation_mode: False`.

## Source

The code is in [kalico-k2pro](https://github.com/MzTechnology97/kalico-k2pro), branch `k2-pro-openhost`. Public reverse engineering (Creality's K2 extras, Jacob10383's firmware, `gitstonelabs/creality-cfs-klipper`) was the starting point; the printer confirmed where the K2 Pro differs. What else has been verified with the CFS is in the [test status](TEST_STATUS.md).
