# CFS observation mode

`observation_mode` is a K2-OpenHost safety layer added to the Jacobean `box.py` integration for K2 Pro/OpenHost validation.

## Purpose

The goal is to exercise the real CFS stack in Kalico while preventing accidental filament movement, RFID-policy writes, cutter actions, tool changes or runout automation during early transport tests.

## Scope

The protection is deliberately scoped to the **Box/CFS layer**. `serial_485.py` remains usable by other devices on the shared RS-485 bus, including closed-loop controllers.

## Behavior in observation mode

- wraps the Box transport with a CFS read-only proxy;
- keeps enumeration and known read queries available;
- blocks all non-whitelisted CFS function codes before TX;
- does not register operational `BOX_*` G-code;
- does not register `T0`, `T1`, ... tool commands;
- does not configure the Box cut-sensor/button hooks;
- does not install the runout-source observer;
- does not perform the normal startup RFID insertion-policy write (`0x0D`);
- defaults state storage to a volatile `/dev/shm` path unless explicitly overridden.

## K2 Pro protocol compatibility

Observation mode is paired with the `box_protocol.py` compatibility change that accepts the tested K2 Pro 4-byte steady `BOX_STATE` payload while preserving the existing Jacobean 6-byte and slot-event paths.

## Hardware-validated result

The real Jacobean `Box()` class completed:

- enumeration of address 1;
- read-only RFID/slot initialization;
- ten consecutive live-state reads;
- one internal `_poll()` call;
- a deliberate guard test of mutation function `0x0D`.

The guard test proved that the blocked request never incremented the underlying transport TX counter.

Transport totals at the end of the test:

```text
tx_frames: 35
rx_frames: 35
crc_errors: 0
invalid_len: 0
unmatched: 0
stale_dropped: 0
timeouts: 0
send_errors: 0
reader_errors: 0
```

## Harness caveats

The standalone test harness does not instantiate a real filament-switch object, so `sensor_error_present=True` is expected there.

`loaded_slot=-1` is intentionally conservative until loaded-path semantics are validated on hardware.

## Source location

The validated implementation is versioned in:

- `MzTechnology97/k2-pro-custom-firmware`, branch `k2-openhost`;
- synchronized into `MzTechnology97/kalico-k2pro`, branch `k2-pro-openhost`.

The original implementation lineage remains credited to Jacob10383/Jacobean; K2-OpenHost changes are limited to the K2 Pro compatibility and observation-safety deltas documented here.