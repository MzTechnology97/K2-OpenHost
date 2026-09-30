# CFS observation mode

This document describes the protected observation mode used to validate Jacob10383's CFS stack through K2-OpenHost without allowing mutating commands to reach the Material Box.

## Goal

Observation mode is intended to run discovery, existing-address validation, and CFS state polling through Jacob's native transport while physically preventing write functions from reaching the bus.

The CFS transport path is:

```text
Jacob box/box_protocol
  -> /dev/ttyUSB2 on CM5
  -> K2 USB gadget / ttyGS2
  -> byte-transparent bridge
  -> T113 /dev/ttyS5 @ 230400 8N1
  -> CFS
```

## Verified read-only guard

A proxy was placed in front of the CFS transport. It allows only the read-only functions needed for validation and rejects everything else before `_write_frame()` is called.

During the self-test, `set_rfid_insert_reading(False)` attempted `FUNC=0x0D`. The guard blocked it correctly:

```text
blocked: addr=0x01 func=0x0D
tx_frames before: 1
tx_frames after:  1
```

The unchanged TX counter proves that the mutating frame never reached the CFS.

## Verified hardware snapshot

With slot A empty, slot B containing an RFID spool, and C/D containing non-RFID filament:

```text
online addresses: [1]
slot_mask: 0x0E
hub_mask:  0x00
buffer:    2
RFID:      A=none, B=RFID_RECORD, C=unknown, D=unknown
remaining: [0, 13, 100, 100]
```

The CFS identity and raw RFID payload are intentionally not published.

## Protected polling

Ten consecutive read-only polling cycles were completed. Every cycle returned the same steady state:

```text
status=0x00
firmware_base=0x1E23
substatus=0x00
load_flag=0x00
slot_mask=0x0E
hub_mask=0x00
buffer=2
```

`firmware_base` remains an opaque value and is not used for operational decisions.

Final transport statistics:

```text
allowed requests: 46
blocked requests: 1
tx_frames: 46
rx_frames: 46
crc_errors: 0
invalid_len: 0
unmatched: 0
stale_dropped: 0
timeouts: 0
send_errors: 0
reader_errors: 0
```

This validates both OpenHost transport stability and the effectiveness of the CFS read-only guard.

## Planned `box.py` integration

The protection must not be added globally to `serial_485.py`, because the same RS-485 bus is shared with closed-loop motor controllers. Observation mode will therefore be implemented only inside the CFS stack.

The protected bootstrap must:

- use `box_count: 1`;
- use a `state_path` under `/dev/shm`;
- wrap the transport used by `AutoAddressClient` and `BoxDriver` with a read-only proxy;
- skip `set_rfid_insert_reading()` during `_initialize_rfid()`;
- avoid registering `Tn` material-change commands;
- disable load, unload, buffer retract, cut, runout recovery, and other operational commands;
- avoid installing the automatic runout handler during observation;
- keep polling and diagnostics available.

The shared RS-485 transport remains unchanged for other devices.

## Status

**CFS read-only guard: hardware verified.**

The next milestone is to start Jacob's real `box.py` in `observation_mode` and let its own internal polling maintain the CFS snapshot while remaining behind the read-only barrier.