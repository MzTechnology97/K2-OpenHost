# G-code commands added by K2-OpenHost

Updated: **2026-10-09**. [Italiano](../it/GCODE_COMMANDS.md)

This page lists every G-code command that K2-OpenHost adds to Kalico, grouped by type. They come from two places:
- the K2 modules of [kalico-k2pro](https://github.com/MzTechnology97/kalico-k2pro) (`klippy/extras`), branch `k2-pro-openhost`;
- the macros of the K2 profile in `config/k2/macros/` (`print.cfg`, `kamp.cfg`, `fans.cfg`, `maintenance.cfg`, `openhost_controls.cfg`).

The standard Klipper and Kalico commands (`G28`, `PID_CALIBRATE`, `BED_MESH_CALIBRATE`, `SET_FAN_SPEED`…) are not repeated here: see the [Kalico G-code reference](https://docs.kalico.gg/G-Codes.html).

**How to read the tables**
- Parameters in `[brackets]` are optional; the value after `=` is the default.
- ⚠ = the command moves the printer, heats, cuts filament, writes to a board or cuts power. Run it only with the printer idle and the bed clear, unless the description says otherwise.
- Commands that start with `_` are used by Mainsail, HelixScreen or the profile macros. You can type them, but you normally use the panel that sends them.
- Slots are numbered from 0: box 1 has slots 0–3 (T0–T3), box 2 has 4–7, and so on. The external spool is the slot after the last CFS slot (T4 with one box).

## Contents

1. [CFS: loading, unloading and tool change](#1-cfs-loading-unloading-and-tool-change)
2. [CFS: print start and filament mapping](#2-cfs-print-start-and-filament-mapping)
3. [CFS: slots, filament library and RFID](#3-cfs-slots-filament-library-and-rfid)
4. [CFS: settings](#4-cfs-settings)
5. [CFS: HelixScreen and Creality compatibility](#5-cfs-helixscreen-and-creality-compatibility)
6. [Calibration](#6-calibration)
7. [Closed-loop motors: status and maintenance](#7-closed-loop-motors-status-and-maintenance)
8. [Power-loss recovery](#8-power-loss-recovery)
9. [T113 board (buzzer, MCU power, USB bridges, screen)](#9-t113-board-buzzer-mcu-power-usb-bridges-screen)
10. [Diagnostics](#10-diagnostics)
11. [Fans, chamber, lights and motion limits](#11-fans-chamber-lights-and-motion-limits)
12. [Print macros of the K2 profile](#12-print-macros-of-the-k2-profile)

## 1. CFS: loading, unloading and tool change

| Command | Parameters | What it does |
| --- | --- | --- |
| `T0`, `T1`, … ⚠ | `[FLUSH=1]` | Selects a tool. During a print started with a filament map, the tool goes to the mapped slot; otherwise it uses the tool-to-slot assignment kept for HelixScreen. If a different filament is loaded, it runs a full change (cut, unload, load, purge at the wastebin; `FLUSH=0` skips the purge). If the print's map has no slot for that tool, the print pauses so you can choose one. |
| `BOX_SELECT_SLOT` ⚠ | `SLOT=<n>` `[FLUSH=1]` | Full change to a physical slot: cut and unload the current filament, load the new one and purge it at the wastebin. `FLUSH=0` skips the purge. |
| `BOX_LOAD` ⚠ | `[SLOT=0]` | Feeds the filament of a slot to the toolhead and starts tracking it. It does not cut or purge: use it when the hotend is empty. If the slot is already loaded, it only resumes tracking. |
| `BOX_UNLOAD` ⚠ | `[MANUAL=0]` | Full unload of the loaded filament: heats, homes if needed, cuts, moves to the wastebin and pulls the filament back into the CFS, then turns the heater off. It also handles the external spool. `MANUAL=1` only pulls the filament back into the CFS, without heating or cutting. |
| `BOX_CUT` ⚠ | `[FORCE=0]` | Moves to the cutter and cuts the filament. Without `FORCE=1` it skips the cut when the sensor sees no filament. Needs `cut_pos_x` in `[box]` (see `CALIBRATE_CUT_POS`). |
| `BOX_BUFFER_RETRACT` | — | Runs only the buffer retract phase of the CFS feeding the loaded slot. |
| `BOX_GO_TO_WASTEBIN` ⚠ | — | Moves the toolhead to the wastebin (purge chute). |
| `NOZZLE_CLEAN` ⚠ | — | Goes to the wastebin and wipes the nozzle on the cleaning pad, with reduced speed and acceleration. The previous motion limits are restored afterwards. |
| `BOX_NOZZLE_CLEAN` ⚠ | — | Same as `NOZZLE_CLEAN` (name used by HelixScreen). |

## 2. CFS: print start and filament mapping

| Command | Parameters | What it does |
| --- | --- | --- |
| `BOX_PRINT_INFO` | `[FILENAME=<file>]` | Reads the slicer metadata of a file and publishes the tools it uses (material, color, filament amount) in the `box` status, where Mainsail's CFS print dialog shows them. It starts nothing. |
| `BOX_PRINT_START` ⚠ | `MAP=<tool:slot,…>` `[FILENAME=<file>]` | Starts a print with an explicit tool-to-slot map, e.g. `MAP=0:2,1:0`. Every tool used by the file must be mapped, and each slot must be online and hold filament. Mainsail's CFS print dialog sends it. |
| `PARSE_FLUSH_VOLUMES` | — | Reads the flush (purge) matrix and print temperatures from the slicer metadata of the loaded file. Called by the print start sequence. |
| `BOX_RUNOUT_CHECK` ⚠ | — | Handles a CFS filament runout: switches to an identical spool if runout swap is on, otherwise pauses. Called by the runout sensor, not by hand. |

## 3. CFS: slots, filament library and RFID

The CFS panel in Mainsail sends these commands. The data is saved on the host and survives restarts.

| Command | Parameters | What it does |
| --- | --- | --- |
| `BOX_RFID_SCAN` | `[ADDR=<box>]` `[NUM=0x0F]` | Rereads the RFID tags of all populated slots (or of one box; `NUM` is a slot mask, bit 0 = slot A). |
| `_BOX_RFID_READ_SLOT` | `SLOT=<n>` | Forces an RFID reread of one slot. A tag the CFS leaves unknown goes to the third-party decoders (Bambu, QIDI; API7 CFS firmware), up to 3 extra rereads; a known third-party tag goes straight to its decoder. |
| `_BOX_RFID_SPOOL_NEW` | `SLOT=<n>` `[REMAINING=100]` | Declares the spool in a slot new and resets its remaining-filament estimate to `REMAINING` percent. Needed for tags with the generic serial: a new spool would otherwise inherit the estimate of a used one with the same brand, material, color and length. |
| `_BOX_SLOT_SET` | `SLOT=<n>` `MATERIAL=<type>` `COLOR=#RRGGBB` `[TARGET_TEMP]` `[BRAND]` `[NAME]` `[SPOOLMAN_ID]` | Saves the filament data of a slot by hand (for spools without RFID). |
| `_BOX_SLOT_CLEAR` | `SLOT=<n>` | Clears the filament data of a slot. |
| `_BOX_SLOT_ASSIGN` | `SLOT=<n>` `FILAMENT_ID=<id>` `[COLOR=#RRGGBB]` | Assigns a profile from the filament library to a slot, optionally with another color. Refused while a live RFID tag controls the slot. |
| `_BOX_FILAMENT_SET` | `ID=<id>` `MATERIAL=<type>` `[COLOR]` `[TARGET_TEMP]` `[MIN_TEMP]` `[MAX_TEMP]` `[PRESSURE_ADVANCE]` `[MAX_FLOW]` `[NOMINAL_LENGTH_M]` `[BRAND]` `[NAME]` `[SPOOLMAN_ID]` | Creates or updates a reusable filament profile in the library (`cfs_filaments.json`). `NOMINAL_LENGTH_M` is the spool length used for third-party RFID spools; empty = the material's reference length. |
| `_BOX_FILAMENT_DELETE` | `ID=<id>` | Deletes a custom filament profile. |
| `_BOX_FILAMENT_ORCA_ID` | `ID=<id>` `[ORCA_ID=<id>]` `[RESET=1]` | OrcaSlicer preset ID (`filament_id`) of a filament, also of a read-only system profile; kept apart from the profile. Without parameters it shows the current and default value; `RESET=1` goes back to the default. Also **OrcaSlicer preset…** in Mainsail's filament library. |
| `_BOX_FILAMENT_RELOAD` | — | Reloads the filament library file and the K2-RFID import from disk, for example after editing the file. |
| `_BOX_MATERIAL_SET` | `MATERIAL=<type>` `TARGET_TEMP=<170–350>` | Saves the default print temperature of a material type. |
| `_BOX_RFID_MAP_SET` | `CODE=<rfid code>` `MATERIAL` `BRAND` `NAME` `[TARGET_TEMP]` | Teaches the system an unknown RFID code: from now on that code shows this material, brand and name. |
| `_BOX_RFID_MAP_DELETE` | `CODE=<rfid code>` | Removes a learned RFID code. |
| `_BOX_RFID_ASSOCIATE` | `SLOT=<n>` `FILAMENT_ID=<id>` | Binds the tag currently in a slot (Creality or third-party) to an existing library profile. |
| `_BOX_RFID_FALLBACK_CACHE` | `[CLEAR=1]` `[UID=<hex>]` | Shows the third-party decoders, reread budgets and UID cache; `CLEAR=1` empties the cache (or one UID). |
| `RFID_READER_READ` | — | Shows the last record read by the standalone RFID reader of the external spool. |

## 4. CFS: settings

Switches of the CFS panel. They are saved and stay set after a restart.

| Command | Parameters | What it does |
| --- | --- | --- |
| `_BOX_SET_RUNOUT_SWAP` | `[ENABLE=1]` | When a spool runs out, continue automatically with an identical spool in another slot. |
| `_BOX_SET_RUNOUT_ORDER` | `[ORDER=<slots>]` | Order in which identical spools are used for runout swap, e.g. `ORDER=2,1,0`. Empty = automatic order. |
| `_BOX_SET_UNLOAD_AFTER_PRINT` | `[ENABLE=0]` | Unload the filament automatically when a print ends. |
| `_BOX_SET_RFID_INSERT_READING` | `[ENABLE=0]` | Read the RFID tag every time a spool is inserted. |
| `_BOX_SET_RFID_STARTUP_READING` | `[ENABLE=0]` | Read all RFID tags when Klipper starts. |
| `_BOX_SET_CLOG_DETECTION` | `[ENABLE=1]` | Clog detection: pause when the extruder feeds `clog_extruder_length` (80 mm) while the CFS does not refill. Saved by the CFS; `clog_detection` in `box.cfg` is the default. Also the **Clog detection** switch in Mainsail's CFS settings menu. |

Set in `box.cfg`, not by command:

| Macro or option | Parameters | What it does |
| --- | --- | --- |
| `_BOX_NOTIFY` | `EVENT` `TITLE` `MESSAGE` | Called by Box for CFS events (`runout_swap`, `runout`, `clog`, `cfs_error`, `rfid_unknown`, `low_filament`, `humidity`); sends them to Mobileraker (`MR_NOTIFY:`) and moonraker-telegram-bot (`RESPOND PREFIX=tgnotify`). `variable_events`, `variable_mobileraker` and `variable_telegram` choose what goes where; `notify_macro:` in `[box]` names the macro (empty = off). |
| `humidity_warnings`, `humidity_limits` | `PA:15, PLA:45` | Print-start warning when a mapped spool sits in a CFS more humid than its material tolerates (PLA 55 %, PETG 50 %, TPU 40 %, PC 35 %, PA 25 %, PVA 20 %); `humidity_limits` overrides single materials. |

CFS runtime configuration (`[box_cfs_runtime]`), only with a CFS firmware that has the runtime-config API (v3.13 and later). Values live in the CFS RAM: they are lost when the CFS restarts and `auto_apply` sends the configured ones again. Nothing is written to the CFS EEPROM or to tags, and a change is refused while the CFS reads a tag.

| Command | Parameters | What it does |
| --- | --- | --- |
| `BOX_CFS_CONFIG_INFO` | — | Current values, marking those changed from stock. |
| `BOX_CFS_CONFIG_SET` | `PARAM=<name>` `VALUE=<n>` | Sets one parameter (names as in `box.cfg`, e.g. `hub_forward_speed`); the CFS checks the range. |
| `BOX_CFS_CONFIG_RESET` | `[PARAM=ALL]` | Back to stock for one parameter or all. |
| `BOX_CFS_CONFIG_APPLY` | — | Sends the values configured in `box.cfg` again. |

## 5. CFS: HelixScreen and Creality compatibility

HelixScreen and Creality's own tools send the stock K2 commands. K2-OpenHost accepts them, so the screen keeps working with the external host. You do not need to type them.

| Command | Parameters | What it does |
| --- | --- | --- |
| `BOX_INFO_REFRESH` | `[ADDR]` `[NUM]` | Same as `BOX_RFID_SCAN` (Creality name). |
| `BOX_MODIFY_TN` | `T1A=T1B …` | Changes the tool-to-slot assignment with Creality slot names (box number + letter A–D). |
| `BOX_MODIFY_TN_DATA` | `ADDR=<1–4>` `NUM=<A–D>` `PART=color_value` `DATA=<color>` | Changes the color of a slot from the screen. Only the color can be changed this way. |
| `BOX_ENABLE_AUTO_REFILL` | `[ENABLE=1]` | Same as `_BOX_SET_RUNOUT_SWAP` (Creality name). |
| `CR_BOX_EXTRUDE` ⚠ | `TNN=<slot>` | Load stage of a stock change: runs a full change to that slot. |
| `CR_BOX_RETRUDE` ⚠ | — | Unload stage of a stock change: runs `BOX_UNLOAD`. |
| `CR_BOX_PRE_OPT`, `CR_BOX_CUT`, `CR_BOX_WASTE`, `CR_BOX_FLUSH`, `CR_BOX_END_OPT`, `BOX_GO_TO_EXTRUDE_POS`, `BOX_MODE_WAIT`, `BOX_MOVE_TO_SAFE_POS`, `BOX_SAVE_FAN`, `BOX_RESTORE_FAN` | — | Accepted and ignored on purpose: the K2-OpenHost change sequence already parks, cuts, purges and handles the fans. |

## 6. Calibration

| Command | Parameters | What it does |
| --- | --- | --- |
| `MOTOR_CALIBRATE` ⚠ | `AXIS=X`, `Y` or `XY` `[DETAIL=raw]` | Calibrates the closed-loop X/Y motors (encoder and electrical offset). The first call only asks you to put the printhead in the middle and the bed at the bottom and switches the motors off; the second call runs it. |
| `MOTOR_CALIBRATE AXIS=E` ⚠ | `STAGE=encoder\|offset\|1\|2` `[DETAIL=raw]` | Calibrates the closed-loop extruder motor, one stage at a time. |
| `MOTOR_ACCEPT_CALIBRATION` | `AXIS=X`, `Y` or `X,Y` | Allows homing with a motor calibration that the startup check flagged as suspicious, until the next Klipper start. Use it only if you know the calibration is good; otherwise run `MOTOR_CALIBRATE`. |
| `CALIBRATE_CUT_POS` ⚠ | — | Finds the X position of the filament cutter (homes XY if needed) and saves it as `cut_pos_x`. Run it after changing the cutter or the toolhead. |
| `PRTOUCH_HOME` ⚠ | `[PRINT_TEMP]` `[SAMPLES]` `[TRAVEL_SPEED]` `[Z_HOP]` … | Z home with several touches of the nozzle (pressure sensor): more accurate than a single `G28 Z`. With `PRINT_TEMP` it compensates the nozzle's thermal expansion at that temperature. |
| `PRTOUCH_SCRUB` ⚠ | — | Finds the flexible tab at the back of the bed and scrubs the nozzle on it before probing. |
| `PRTOUCH_SCAN_CALIBRATE` ⚠ | `[MODEL=default]` `[SAMPLES]` … | Calibrates the Cartographer scan model, using the nozzle touch as Z=0. Needs Cartographer. |
| `PRTOUCH_AXIS_TWIST_COMPENSATION` ⚠ | `[SAMPLES]` `[LIFT_SPEED]` … | Measures X axis twist by comparing Cartographer scans with nozzle touches. Needs Cartographer. |
| `BEDPID` ⚠ (macro) | — | PID tuning of the bed at 100 °C, then `SAVE_CONFIG` (restarts Klipper). |
| `NOZZLE_PID` ⚠ (macro) | — | PID tuning of the nozzle at 230 °C with the part fan on, then `SAVE_CONFIG`. |
| `NOZZLE_PID_HIGH` ⚠ (macro) | — | Same at 280 °C, for high-temperature filaments. |

## 7. Closed-loop motors: status and maintenance

The X, Y and E motors of the K2 Pro are closed-loop motors with their own controller on the RS-485 bus.

| Command | Parameters | What it does |
| --- | --- | --- |
| `MOTOR_STATUS` | `[VERBOSE=1]` `[REFRESH=1]` | Readable state of the motors: startup, readiness, calibration, protection, temperatures. `REFRESH=1` rereads the calibration from the motors. |
| `MOTOR_EVENTS` | `[COUNT=n]` `[VERBOSE=1]` | History of the protection events (stall, overcurrent, faults). `VERBOSE=1` gives JSON to attach to a bug report. |
| `MOTOR_QUERY_FAULTS` | — | Asks every motor now for its error, warning and status codes. |
| `MOTOR_CLEAR_ERROR` | — | Reads the active motor faults, clears them and reports the result. |
| `MOTOR_RETRY_STARTUP` | — | Runs the motor startup sequence again (for example after the RS-485 link came back). |
| `REQUIRE_EXTRUDER_CLEAR` | — | Stops the running macro (normally `RESUME`) if the extruder motor has a latched protection fault. It tries one clear first. |
| `MOTOR_CFG_OVERRIDE_STATUS` | `[AXIS=XYE]` `[DETAIL=raw]` | Compares the motor parameters set in `macros/motor_control.cfg` with the values the motors hold now. |
| `MOTOR_READ_PARAM` | `PARAM=<name>` | Reads one motor parameter, e.g. `PARAM=x_param_stall_cur_A`. |
| `MOTOR_FLASH_PARAM` ⚠ | `PARAM=<name>` `[VALUE]` `[COMMIT=0]` | Writes one motor parameter and checks it. Without `COMMIT=1` the value is only live until the motor restarts; with `COMMIT=1` it is saved in the motor's flash. Service use only. |
| `MOTOR_READ_ALL_PIN_IO` | — | Reads the step, direction and stall lines of the motors. |

## 8. Power-loss recovery

| Command | Parameters | What it does |
| --- | --- | --- |
| `PLR_STATUS` | — | Shows whether a print can be resumed after a power loss, and from where. |
| `PLR_RECOVER` ⚠ | `CONFIRM=1` | Resumes the interrupted print from the saved checkpoint, restoring temperatures, position and the CFS state. It refuses without `CONFIRM=1`, during another print or without a checkpoint. |
| `PLR_DISCARD` | — | Deletes the saved checkpoint, so the print cannot be resumed. |

## 9. T113 board (buzzer, MCU power, USB bridges, screen)

They talk to `k2oh-ctl` on the printer's T113 board (`[k2_t113]` in `macros/k2_t113.cfg`).

| Command | Parameters | What it does |
| --- | --- | --- |
| `BOARD_STATUS` | — | Shows the last T113 telemetry: slot, MCU power rail, SoC temperature, uptime, free UDISK space, USB gadget state and whether each bridge is up. |
| `BUZZER` | `[MS=200]` `[COUNT=1]` or `PATTERN=on,off,…` or `SOUND=<name>` | Sounds the printer buzzer. `SOUND` plays one of the configured sounds: `print_complete`, `pause`, `error`, `cancel`, `shutdown`, `rfid`. |
| `M300` | `[P=200]` | Standard beep for slicers (duration in ms; the buzzer has a fixed tone). Only if no other `M300` macro exists. |
| `USB_BRIDGES_RESTART` ⚠ | `CONFIRM=1` | Restarts the three USB bridges on the T113. The MCU links drop for a moment, so Klipper usually goes into shutdown: run `FIRMWARE_RESTART` afterwards. Only when idle. |
| `MCU_POWER_CYCLE` ⚠ | `CONFIRM=1` | Cuts the power of the printer MCUs for 2 seconds, then runs `FIRMWARE_RESTART`. Works even while Klipper is in shutdown. Only when idle. |
| `SCREEN_RESTART` | — | Restarts HelixScreen on the printer's display. |

## 10. Diagnostics

Read-only: they print information and change nothing.

| Command | Parameters | What it does |
| --- | --- | --- |
| `BOX_DEBUG` | `[RAW=0]` | Full CFS report: boxes online, live state, sensors, change engine, clog detection, per-box registers. `RAW=1` adds the raw replies. |
| `BOX_ENV_DEBUG` | — | CFS versions, hardware, temperature and humidity, read now. |
| `SERIAL_STATUS` | — | State and counters of the RS-485 link (frames, timeouts, CRC errors, link lost/ok). |
| `LINK_MONITOR_REPORT` | — | Round-trip percentiles of every serial link (MCUs and RS-485) since Klipper started. Needs `[link_monitor]`. |
| `FAN_FEEDBACK_STATUS` | — | Speed of the fans that have a tachometer. |
| `EXTENDED_ZONE_TRANSFORM_STATUS` | — | State of the extended-zone routing: the Y area beyond the normal bed limit (wastebin and cutter) is reached only inside a safe X window. |

## 11. Fans, chamber, lights and motion limits

| Command | Parameters | What it does |
| --- | --- | --- |
| `M106` (macro) | `[P=0]` `[S=255]` | Fan speed: `P0` toolhead part fan, `P2` side part fan (`aux_fans`), `P3` chamber exhaust/filter fans (as a minimum speed). Mainsail labels them **Toolhead Part Fan**, **Side Part Fan** and **Chamber Exhaust Fans**. |
| `M107` (macro) | `[P=0]` | Turns off the fan selected with `P` (same numbers as `M106`). |
| `M141` (macro) | `S=<°C>` | Chamber temperature: above 40 °C it uses the chamber heater, from 1 to 40 °C the exhaust fans keep the chamber below that value, 0 turns both off. |
| `M191` (macro) | `S=<°C>` | Like `M141`, then waits for the chamber to reach the temperature. |
| `SET_TEMPERATURE_FAN_MANUAL_SPEED` | `TEMPERATURE_FAN=<name>` `SPEED=<0–1>` | Sets a minimum speed for a temperature-controlled fan (used for the chamber filter). The automatic control can still run it faster. |
| `SET_FAN_SPEED FAN=chamber_exhaust_fans` | `SPEED=<0–1>` | The **Chamber Exhaust Fans** slider in Mainsail: sets the same minimum speed (`generic_fan: True` on `[temperature_fan_manual_floor chamber_exhaust_fans]`); `M106 P3` moves the slider. |
| `LED_IDLE_MANAGER_ON` / `LED_IDLE_MANAGER_OFF` | — | Turns the automatic light off on or off for this Klipper session (the light stays on while printing and turns off after a while without activity). |
| `SET_LED_IDLE_MANAGER` | `[ENABLE=1]` | Same, with a parameter. |
| `LED_IDLE_MANAGER_STATUS` | — | Shows the state of the automatic light off. |
| `SAVE_MOTION_LIMITS` | `[NAME=default]` `[INCLUDE_GCODE=0]` | Saves the current speed and acceleration limits under a name (`INCLUDE_GCODE=1` also saves the G-code state). |
| `RESTORE_MOTION_LIMITS` | `[NAME=default]` `[INCLUDE_GCODE=0]` `[MOVE=0]` | Restores limits saved with `SAVE_MOTION_LIMITS`. With `INCLUDE_GCODE=1` it also restores the G-code state, and `MOVE=1` returns to the saved position. |
| `M205` (macro) | `[X]` `[Y]` | Slicer jerk command: sets Kalico's square corner velocity to the `X` value (or `Y`). |

## 12. Print macros of the K2 profile

| Command | Parameters | What it does |
| --- | --- | --- |
| `START_PRINT` ⚠ | `[BED_TEMP=60]` `[EXTRUDER_TEMP=220]` `[CHAMBER_TEMP=0]` `[MIN_CHAMBER_TEMP]` `[MATERIAL]` `[SOAK_TIME]` `[ATC]` | Start of a print, called from the slicer start G-code: heats bed and chamber, optional heat soak, homes, cleans the nozzle hot over the wastebin and again at the probing temperature, adaptive bed mesh and axis twist compensation, Z home with the nozzle touch at print temperature, then heats the nozzle. |
| `END_PRINT` ⚠ | — | End of a print: retracts if the nozzle is hot, turns heaters and fans off, raises Z and parks at the wastebin. |
| `PAUSE` ⚠ | `[SKIP_RETRACT_WIPE=0]` | Pause: saves the temperature to resume at, lowers the nozzle to 140 °C, retracts and wipes, raises Z, cleans and parks at the wastebin, turns the part cooling off. |
| `RESUME` ⚠ | `[VELOCITY]` | Resume: finishes any interrupted CFS operation, heats and primes at the wastebin, restores the fans and returns to the print. |
| `CANCEL_PRINT` ⚠ | — | Cancels the print and runs `END_PRINT`. |
| `HOME_IF_NEEDED` ⚠ | `[AXIS=XYZ]` | Homes only the axes that are not homed yet. |
| `BED_MESH_CALIBRATE` ⚠ | as Kalico | The standard command, run with reduced speed and acceleration; the previous limits are restored afterwards. |
| `LUBRICATE_RAILS` ⚠ | `[ITERATIONS=1]` `[SPEED=500]` | Moves the head corner to corner over the whole bed to spread the rail lubricant. |
| `LINE_PURGE` ⚠ | — | KAMP purge line next to the printed objects. |
| `STATUS_MSG` | `MSG=<text>` `[TYPE]` `[PREFIX]` `[DISPLAY]` | Shows a message in the console and on the display. |
| `START_PRINT_ATC` | `[ENABLE=0\|1]` | Axis twist calibration at print start on or off, saved across restarts (also the **Axis Twist Compensation** switch in Mainsail); without `ENABLE` it shows the state. Skipped when PRTouch is the probe. |
| `WARMUP` ⚠ | `[LOOPS=3]` `[X_ACCEL_MAX=10000]` `[Y_ACCEL_MAX=10000]` | Motion stress test: X, Y and diagonal sweeps over the bed area (Y up to 301 mm), then restores the configured limits. |
| `AUTO_WARMUP` ⚠ | `[CYCLES=3]` | Long burn-in: `WARMUP` at three accelerations with 20 min pauses, `CYCLES` times. |
| `TEST_SPEED` ⚠ | `[SPEED]` `[ACCEL]` `[ITERATIONS=5]` `[BOUND=25]` `[SMALLPATTERNSIZE=20]` | Skipped-step test: `GET_POSITION` after homing X/Y, fast patterns on the bed, then homing and `GET_POSITION` again. |
| `ACCELL_TEST_X` / `ACCELL_TEST_Y` ⚠ | `[STEPS=20]` `[ACCEL_START=10000]` `[ACCEL_STEP=1000]` `[VELOCITY=500]` `[VELOCITY_STEP=0]` | One axis back and forth (X at mid Y, Y at mid X); each pass raises acceleration (and velocity) above the configured limits and is logged; the limits are restored at the end. |

Internal macros, used by the ones above: `_START_PRINT_VARS` (start print settings, set in `macros/overrides.cfg`), `_NOZZLE_HOT_CLEAN`, `_MOTION_TEST_RESTORE`, `_PAUSE_CONTEXT`, `_PAUSE_Z_MOVE`, `_RETRACT_WIPE`, `_END_PRINT_Z_MOVE`, `_RESET_PRINT_STATE`, `_KAMP_Settings`, `_BOX_PAUSE_CAPTURE`, `_BOX_RESUME_PREPARE`, `_BOX_RESUME_COMMIT`.
