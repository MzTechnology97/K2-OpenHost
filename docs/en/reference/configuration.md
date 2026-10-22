# Configuration

The helper installs the **K2 Pro profile** from kalico-k2pro (`config/k2/`) into `~/printer_data/config/`. This page explains where each setting lives and which ones you are expected to change.

!!! tip "Where to put your changes"
    Put your own values in **`macros/overrides.cfg`** whenever possible: it is included last, so its sections win, and updates of the profile never touch it. The helper's [config diff](../helper/menu.md) (menu 18) shows what differs from the shipped profile before an update.

## File layout

```text
~/printer_data/config/
├── printer.cfg                 MCUs, serial links, kinematics, heaters, includes
├── moonraker.conf              Moonraker, update manager
├── cfs_filaments.json          your filament library (custom profiles)
├── k2_rfid_custom_materials.json  optional K2-RFID database to import
├── k2oh_t113.token             token for k2oh-ctl (never share it)
├── timelapse.cfg
└── macros/
    ├── system.cfg              print files, power-loss recovery, timeouts
    ├── sensors.cfg             MCU/host temperatures, filament sensor, accelerometer
    ├── leds.cfg                chamber light
    ├── print.cfg               START_PRINT, PAUSE, RESUME, CANCEL, END_PRINT
    ├── kamp.cfg                KAMP adaptive purge
    ├── fans.cfg                fans, tachometers, M106/M107/M141/M191
    ├── maintenance.cfg         PID, rail lubrication, motion tests
    ├── box.cfg                 CFS: [box], mapping, runtime parameters, notifications
    ├── box_rfid_*.cfg          third-party RFID (API7 CFS firmware only)
    ├── motor_control.cfg       closed-loop X/Y/E motors
    ├── k2_t113.cfg             T113: buzzer, MCU power, telemetry
    ├── prtouch.cfg             PRTouch probe (or cartographer.cfg)
    ├── host_fan.cfg            CM5 CPU fan (helper menu 36)
    ├── openhost_controls.cfg   Mainsail switches (optional)
    └── overrides.cfg           YOUR settings, included last
```

Runtime data outside the config folder: `~/printer_data/filament_box.json` (CFS state: slots, spool estimates, settings) and `~/printer_data/power_loss_recovery/`.

## Serial links (`printer.cfg`)

```ini
[mcu]
serial: /dev/k2-main          # T113 ttyGS0 -> Main MCU
[mcu nozzle_mcu]
serial: /dev/k2-nozzle        # T113 ttyGS1 -> Nozzle MCU
[serial_485 serial485]
serial: /dev/k2-rs485         # T113 ttyGS2 -> RS-485 (CFS, X/Y motors)
baud: 230400
link_lost_timeout: 10
link_lost_action: pause       # pause | warn | cancel | shutdown (during a print)
```

The `/dev/k2-*` names come from a udev rule installed by the helper (menu 19) and do not depend on USB enumeration order. Never use `/dev/ttyUSBn`: the numbers change after a USB reconnect.

## CFS (`macros/box.cfg`)

### `[box]`: the main options

| Option | Default | Meaning |
| --- | --- | --- |
| `box_count` | 1 | Number of connected CFS units (1–4). Set it in `overrides.cfg` |
| `hotend_feed_length` | 63 | mm pushed to the hotend after a CFS load |
| `retract_length` | 30 | mm retracted before the cut on unload |
| `fallback_purge_length` | 100 | Purge without a slicer flush matrix |
| `purge_speed`, `hotend_feed_speed` | 20 | Volumetric speeds, mm³/s |
| `clog_detection` | True | Default of the clog detection switch |
| `clog_extruder_length` | 80 | mm fed by the extruder without CFS refill before pausing (min 30) |
| `cfs_live_remaining` | True | Follow the CFS live remaining on CFG5T/CFG6 firmware |
| `humidity_warnings` | True | Warn at print start for spools in a too-humid CFS |
| `notify_macro` | `_BOX_NOTIFY` | Macro that receives CFS events; empty = off |
| `auto_register_rfid_filaments` | True | Create library profiles for known RFID materials |
| `auto_bambu_rfid_fallback`, `auto_mifare_rfid_fallback` | True | Third-party RFID decoders (API7 only) |
| `rfid_fallback_budget` / `_manual_budget` | 1 / 3 | CFS rereads for third-party tags |
| `publish_lane_data` | True | Publish slots for OrcaSlicer Sync |
| `wastebin_pos_x/y`, `clean_pad_*`, `cut_pos_*` | K2 Pro values | Service positions; `cut_pos_x` comes from `CALIBRATE_CUT_POS` |

### `[box_print_mapping]`

| Option | Default | Meaning |
| --- | --- | --- |
| `auto_map_prints` | true | Map slicer tools to slots automatically when a print starts without an explicit map |
| `auto_map_block_unresolved` | true | Refuse a start when a tool cannot be matched safely |

A `; K2OH_TOOL_MAP = tool:slot,...` line in the file (OrcaSlicer plugin) is used even with `auto_map_prints: false`.

### `[box_cfs_runtime]`

Only for the [experimental CFS firmware](../cfs-firmware/parameters.md). Commented out by default; `auto_apply: True` plus the values you want, applied at Klipper start with the printer idle.

### Notifications

`[gcode_macro _BOX_NOTIFY]`: `variable_events`, `variable_mobileraker`, `variable_telegram`. See [Notifications](../usage/notifications.md).

## T113 (`macros/k2_t113.cfg`)

| Option | Default | Meaning |
| --- | --- | --- |
| `host` | empty | Printer (T113) IP address; empty disables the module |
| `port` | 7130 | `k2oh-ctl` port |
| `token_file` | `~/printer_data/config/k2oh_t113.token` | Shared token, written by the helper |
| `poll_interval` | 10 | Telemetry period (s), 0 = off |
| `estop_on_shutdown` | `m112` | Cut the MCU power rail on an emergency stop (`m112`), on any shutdown (`any`) or never (`off`) |
| `estop_power` | `cycle` | After the cut: restore power (MCU reset, `cycle`) or keep it off (`off`) |
| `auto_power_cycle` | False | Power-cycle the MCUs by itself after a lost link (idle only, at most every 10 min) |
| `sound_*` | stock patterns | Buzzer patterns `on,off,on,...` in ms; empty = silent |

## Start print (`macros/overrides.cfg`)

```ini
[gcode_macro _START_PRINT_VARS]
variable_heat_soak: 0                    # bed heat soak, minutes
variable_offset_DEFAULT: 0.00            # Z offset, mm
variable_offset_ASA: 0                   # per-material Z offset (offset_<MATERIAL>)
variable_adaptive_axis_twist_comp: 0     # default of START_PRINT_ATC
variable_prtouch_scrub: 0                # scrub the nozzle on the bed tab before PRTouch
```

## Host fan (`macros/host_fan.cfg`)

```ini
[host_fan cm5_fan]
control: target         # target | manual | kernel
target_temp: 55
ramp_delta: 15
min_speed: 0.3
max_speed: 1.0
full_speed_temp: 75
```

See [Host hardware](../HOST.md#cpu-fan).

## Power-loss recovery (`macros/system.cfg`)

`[power_loss_recovery]` writes checkpoints to `~/printer_data/power_loss_recovery` and re-references Z with `[z_align]` (bottom switch), like stock. Recovery only starts with `PLR_RECOVER CONFIRM=1`. Validate it with a supervised power cut before relying on it. If your host and printer are on a UPS you may prefer to disable both, as the reference printer does.

## Kalico telemetry

The profile sets `[telemetry] enabled: False`: Kalico sends no usage data.

## Reference machine

`config/k2/reference/k2pro-cm5/` in kalico-k2pro is the live configuration of the reference printer (CM5 host, CFG6 CFS, third-party RFID, host fan, UPS). Use it as an example, not as a drop-in: some choices are specific to that machine.
