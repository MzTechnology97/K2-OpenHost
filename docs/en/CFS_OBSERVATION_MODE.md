# CFS observation mode

This document describes the protected observation mode used to validate Jacob10383's CFS stack through K2-OpenHost without allowing mutating commands to reach the Material Box.

## Goal

Observation mode performs discovery, existing-address validation, and CFS state polling through Jacob's native stack while physically preventing mutating functions from reaching the bus.

```text
Jacob box/box_protocol
  -> /dev/ttyUSB2 on CM5
  -> K2 USB gadget / ttyGS2
  -> byte-transparent bridge
  -> T113 /dev/ttyS5 @ 230400 8N1
  -> CFS
```

The protection is applied only to the CFS stack and not globally to `serial_485.py`, because the same RS-485 bus is shared with closed-loop controllers.

## Verified read-only guard

The CFS proxy only permits the read-only functions required by discovery and polling and blocks all others before the underlying serial transport.

The self-test attempted RFID write function `0x0D`:

```text
blocked: addr=0x01 func=0x0D
tx_frames before: 2
tx_frames after:  2
```

The unchanged TX counter proves the mutating frame was not transmitted.

## Real Jacob `box.py` verified

The volatile Jacobean 6.18 copy was extended with `observation_mode`, and the real `Box()` object was run through K2-OpenHost.

Verified bootstrap:

```text
observation_mode: True
state_path: /dev/shm/k2-openhost-filament_box.json
registered gcode: ['SERIAL_STATUS']
operational Box G-code: NONE

drivers: [1]
address_errors: []
rfid_presence: {1: '0x0E'}
serial_proxy: _ReadOnlyCFSProxy
```

`SERIAL_STATUS` belongs to the `serial_485` transport; no operational `BOX_LOAD`, `BOX_UNLOAD`, `BOX_CUT`, `Tn`, or equivalent command was registered by `box.py` in observation mode.

The protected bootstrap also:

- uses `box_count=1`;
- uses a volatile `state_path` under `/dev/shm`;
- does not register the `nozzle_mcu:PB9` cut sensor;
- does not send RFID policy write `0x0D` from `_initialize_rfid()`;
- does not register `Tn` commands;
- does not install the automatic runout handler;
- keeps enumeration, snapshots, and read-only polling active.

## Native `Box.read_live_state()` polling

Ten consecutive cycles were executed through Jacob's real `Box.read_live_state()`.

Every cycle returned:

```text
data_ready: True
loaded_slot: -1
loaded_mask: 0x0
slot_mask: 0x0E
tracking: False
buffer_state: 2
box_status: 0x00
substatus: 0
load_flag: 0
firmware_base: 0x1E22
```

`loaded_slot=-1` is intentional and conservative: the K2 Pro four-byte steady format does not contain the Jacobean six-byte model's `downstream_mask`, so OpenHost does not fabricate a loaded path.

The standalone harness showed `sensor_error_present=True` because the Fake Klippy environment intentionally did not instantiate the real `filament_switch_sensor`; this is not a CFS error.

A real `Box._poll()` cycle also updated the snapshot correctly with `slot_mask=0x0E` and `buffer_state=2`.

## Final `Box()` test statistics

```text
allowed requests: 35
blocked requests: 1
blocked funcs: [addr=0x01 func=0x0D]

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

This validates native `box.py` polling end-to-end behind the CFS read-only barrier.

## Fork and reproducible patchset

The validated changes are now stored in the public fork:

```text
MzTechnology97/k2-pro-custom-firmware
branch: k2-openhost
```

`main` remains on the Jacob base, while `k2-openhost` directly contains:

- `extras/box_protocol.py`: K2 Pro four-byte `BOX_STATE` compatibility;
- `extras/box.py`: protected `observation_mode`.

The fork also preserves:

```text
patches/k2-openhost/0001-k2-pro-box-state-4byte.patch
patches/k2-openhost/0002-cfs-observation-mode.patch
patches/k2-openhost/apply.py
patches/k2-openhost/apply.sh
```

The applicator is SHA-gated against the original Jacobean 6.18 files. GitHub Actions also verifies that both unified diffs apply to a clean `origin/main` worktree and that the resulting modules pass `py_compile`.

Primary source commits:

```text
58438be54af474138c4f85eb6084edd8c0bc1096
k2-openhost: support K2 Pro 4-byte CFS BOX_STATE

7132f263c1706ad6810d8ec22c7a848e909b438a
k2-openhost: apply validated K2 Pro compatibility patches
```

## Status

**Jacob's real `box.py` is hardware-verified in observation mode through K2-OpenHost.**

The next milestone is to start a real Klippy/Kalico instance on the CM5 with `[serial_485 serial485]` on `/dev/ttyUSB2` and `[box] observation_mode: True`, while keeping load/unload disabled until K2 Pro loaded-path semantics are correlated reliably.
