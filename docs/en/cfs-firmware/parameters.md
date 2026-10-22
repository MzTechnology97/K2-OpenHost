# Runtime parameters (CFG6)

The CFG6 v3.25 firmware exposes **28 parameters** of the stock CFS application. **23 are writable**; IDs 0, 4, 10, 25 and 26 are read-only (GET only). Kalico's `[box_cfs_runtime]` writes them from `box.cfg` at Klipper start.

!!! info "How to read the values"
    - Hub motor speeds `1–255` are **raw command values**. There is no proven conversion to mm/s or RPM: `220` is not 220 mm/s. The spool feeders are ON/OFF only.
    - `_ms` values are real milliseconds in `box.cfg`. ID 8 must be a multiple of 10, IDs 20 and 22 a multiple of 20 (the firmware counts in 10/20 ms ticks).
    - A **timeout** moves a failure deadline, a **delay** changes a wait, a **count** changes loop repetitions. None of them speeds up the toolhead extruder.

## All 28 parameters

| ID | `box.cfg` option | Stock | Range | Reference CM5 | Writable | What it does |
|---:|---|---:|---|---:|:---:|---|
| 0 | `feeder_forward_speed` | 255 | 1–255 | — | No | Spool feeder is ON/OFF: no speed to tune |
| 1 | `hub_forward_speed` | 100 | 1–255 | 100 | Yes | Hub speed on the initial forward push |
| 2 | `hub_transition_speed` | 200 | 1–255 | 220 | Yes | Hub speed while transferring to the buffer/toolhead: **the main transfer speed** |
| 3 | `hub_insert_speed` | 155 | 1–255 | 100 | Yes | Hub speed during sensor-guided final insertion |
| 4 | `feeder_reverse_speed` | 255 | 1–255 | — | No | Feeder reverse is ON/OFF |
| 5 | `hub_reverse_speed` | 80 | 1–255 | 150 | Yes | Hub speed while pulling filament back on unload |
| 6 | `reverse_detooth_enable` | 1 | 0/1 | True | Yes | Enables the gear-release (de-tooth) step during reverse |
| 7 | `hub_transition_wait_ms` | 3200 | 100–10000 | 3200 | Yes | Pause after the hub push, before the buffer path |
| 8 | `insert_sensor_timeout_ms` | 7000 | 1000–50000, step 10 | 7000 | Yes | Wait window for the insertion sensor |
| 9 | `hub_pullback_timeout_ms` | 5000 | 500–15000 | 5000 | Yes | Time limit of the unload pullback stage |
| 10 | `unload_sensor_timeout_ms` | 1000 | — | — | No | Not patched in CFG6 |
| 11 | `rfid_seek_speed` | 160 | 1–255 | 160 | Yes | Hub speed while looking for the RFID tag |
| 12 | `rfid_measure_speed` | 120 | 1–255 | 150 | Yes | Hub speed while the spool moves during the RFID read |
| 13 | `rfid_reposition_speed` | 100 | 1–255 | 100 | Yes | Hub speed when repositioning between RFID steps |
| 14 | `rfid_seek_move_ms` | 800 | 100–5000 | 800 | Yes | Duration of the tag-search movement |
| 15 | `rfid_seek_settle_ms` | 200 | 10–2000 | 200 | Yes | Pause after the search movement |
| 16 | `rfid_post_auth_wait_ms` | 1000 | 100–5000 | 1000 | Yes | Wait after tag authentication |
| 17 | `rfid_pre_measure_settle_ms` | 400 | 1–2000 | 400 | Yes | Pause before the RFID read |
| 18 | `rfid_neighbor_detect_delay_ms` | 400 | 50–2000 | 400 | Yes | Timing of the adjacent-spool detection movement |
| 19 | `rfid_neighbor_settle_ms` | 100 | 10–1000 | 100 | Yes | Settling pause after the adjacent-spool movement |
| 20 | `feed_total_timeout_ms` | 25000 | 5000–60000, step 20 | 25000 | Yes | Overall timeout of feeding toward the toolhead |
| 21 | `feed_recovery_timeout_ms` | 3000 | 500–10000 | 3000 | Yes | Time allowed for a feed recovery |
| 22 | `odometer_stall_timeout_ms` | 500 | 100–2000, step 20 | 500 | Yes | No odometer progress for this long = stall |
| 23 | `rfid_neighbor_retry_count` | 3 | 1–10 | 1 | Yes | Attempts in the adjacent-spool RFID search |
| 24 | `reverse_detooth_timeout_ms` | 1000 | 100–10000 | 1000 | Yes | Time threshold of the de-tooth step (works with ID 6) |
| 25 | `buffer_fill_timeout_ms` | 30000 | — | — | No | Not patched in CFG6 |
| 26 | `transition_detect_timeout_ms` | 300 | — | — | No | Not patched in CFG6 |
| 27 | `load_retry_count` | 3 | 1–10 | 1 | Yes | Forward/back **pretension cycles** while loading (not general retries) |

The "Reference CM5" column is what the reference machine runs, verified by readback on 18 October 2026: it is **not a recommendation**. The full per-parameter analysis (ARM addresses of the hooks, risks, evidence) is in [CFS_RUNTIME_CFG6_PARAMETERS_EN.md](https://github.com/MzTechnology97/kalico-k2pro/blob/k2-pro-openhost/docs/CFS_RUNTIME_CFG6_PARAMETERS_EN.md).

!!! tip "CFS speed vs toolhead speed"
    IDs 1, 2, 3 and 5 move the **CFS hub motor**. The toolhead extruder is set in `[box]`: `hotend_feed_speed` (mm³/s), `retract_velocity` and `external_feed_velocity` (mm/min).

## Enable the values

The shipped `box.cfg` keeps everything commented, so a fresh install never writes to the CFS. On a CFS verified as CFG6 (`BOX_CFS_CONFIG_INFO`):

```ini
[box_cfs_runtime]
auto_apply: True
hub_transition_speed: 220
hub_insert_speed: 100
hub_reverse_speed: 150
rfid_measure_speed: 150
rfid_neighbor_retry_count: 1
load_retry_count: 1
#reverse_detooth_enable: True
#hub_pullback_timeout_ms: 5000
```

1. Edit `box.cfg` with the printer idle.
2. Restart **Klipper** (not a firmware restart during a print).
3. The console prints `applied N value(s)`. Any refused option is listed with the reason.
4. Check with `BOX_CFS_CONFIG_DIAG ALL=1`: each configured value must match the CFS readback.

Change **one parameter at a time** and watch a few loads, unloads and RFID reads before the next one.

## Rules Kalico enforces

| Rule | Why |
| --- | --- |
| Exact identity `K2OH` / `v323-cfg6` / `0xE3`, API 2, 28 IDs | Stock, CFG4, CFG5T and OpenCFS never receive CFG6 writes |
| Writes only at Klipper start, printer idle | [Issue #9](https://github.com/MzTechnology97/k2-cfs-rfid-tools/issues/9): the CFS can report IDLE while still feeding |
| No `SET`/`RESET`/`APPLY` console commands | Values come only from `box.cfg` |
| Every SET followed by a GET | A mismatch is reported, never silently kept |
| Values in CFS RAM only | A CFS power cycle restores stock values until the next Klipper start |

## Commands

| Command | Use |
| --- | --- |
| `BOX_CFS_CONFIG_INFO [ADDRESS=1-4]` | Firmware identity (`0x7A`), result of the startup apply, every value by group |
| `BOX_CFS_CONFIG_DIAG [ALL=1]` | Read-only GET with expected value, range and `OK`/`INVALID`; without `ALL=1` only IDs 0, 6, 7, 8, 11, 20, 27 |
| `BOX_CFS_CONFIG_SNAPSHOT` | Read-only internal state snapshot; only on `0xD7` firmware (v3.22, CFG4) |

See also [G-code commands](../GCODE_COMMANDS.md) and [Debug](../reference/debug.md).
