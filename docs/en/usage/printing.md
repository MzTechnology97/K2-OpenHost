# Printing

## Slicer start and end G-code

The K2 profile does the whole start sequence in `START_PRINT`. In the slicer's printer settings use:

=== "Start G-code (OrcaSlicer)"

    ```text
    START_PRINT EXTRUDER_TEMP=[nozzle_temperature_initial_layer] BED_TEMP=[bed_temperature_initial_layer_single] MATERIAL={filament_type[initial_tool]} CHAMBER_TEMP=[overall_chamber_temperature] MIN_CHAMBER_TEMP=[chamber_minimal_temperature]
    T[initial_no_support_extruder]
    ```

    The reference printer adds a purge line after the `T` command; `LINE_PURGE` (KAMP) is an alternative.

=== "End G-code"

    ```text
    END_PRINT
    ```

=== "Pause G-code"

    ```text
    PAUSE
    ```

Leave *Change filament G-code* empty: the slicer's `T<n>` commands go to the CFS through the print's tool map. Set the G-code flavour to **Klipper**.

## What `START_PRINT` does

1. Heats bed and chamber (`BED_TEMP`, `CHAMBER_TEMP`; `MIN_CHAMBER_TEMP` waits for a minimum), optional bed heat soak.
2. Homes the axes that are not homed (`[z_align]` drops the bed to the bottom switch first).
3. Cleans the nozzle hot over the wastebin (print temperature − 10 °C), cools to the probing temperature (140 °C) with the part fan, cleans again.
4. Adaptive bed mesh and, if enabled, axis twist compensation.
5. Z home with the nozzle touch (PRTouch) at print temperature.
6. Heats the nozzle to `EXTRUDER_TEMP`.

Settings in `macros/overrides.cfg` (`_START_PRINT_VARS`):

| Variable | Default | Meaning |
| --- | --- | --- |
| `variable_heat_soak` | 0 | Bed heat-soak time, minutes |
| `variable_offset_<MATERIAL>` | 0 | Z offset per material, e.g. `variable_offset_ASA` |
| `variable_offset_DEFAULT` | 0.00 | Fallback Z offset |
| `variable_hot_clean` | 1 | Clean the nozzle hot before cooling to the probing temperature |
| `variable_hot_clean_offset` | 10 | Hot clean temperature = print temperature − this |
| `variable_prtouch_scrub` | 0 | Scrub the nozzle on the plate tab |
| `variable_adaptive_axis_twist_comp` | 0 | Default of the axis twist switch (`START_PRINT_ATC`) |

The **Axis Twist Compensation** switch in Mainsail (or `START_PRINT_ATC ENABLE=0|1`) turns the calibration at print start on or off; it is skipped when PRTouch is the probe.

## Starting a print

| From | What happens |
| --- | --- |
| Mainsail → G-code files → **Print** | The [print dialog](mainsail.md#print-dialog-with-cfs-mapping) maps each tool to a CFS slot |
| OrcaSlicer → **Upload and print** | Kalico maps the tools automatically, or uses the slots chosen in the [plugin panel](orca-plugin.md) |
| OrcaSlicer → **Upload** only | The file waits in Mainsail; start it from the print dialog |
| HelixScreen | Starts the file; automatic mapping applies |

The external USB port of the printer does not work in OpenHost mode: send files over the network.

## During a print

- **Tool changes**: `T<n>` cuts, unloads, loads the mapped slot and purges at the wastebin (flush volumes from the slicer's matrix).
- **Runout**: with runout swap on, the box continues on an identical spool; otherwise the print pauses and the buzzer sounds.
- **Clog detection**: pauses if the extruder feeds while the CFS does not refill.
- **RS-485 link lost** (CFS and X/Y motors silent for 10 s): the print pauses (`link_lost_action: pause`).
- **Live filament check**: every minute, the filament each tool still needs against what its spool has left.

## Pause, resume, cancel

| Command | What it does |
| --- | --- |
| `PAUSE` | Saves the temperature, lowers the nozzle to 140 °C, retracts and wipes, raises Z, cleans and parks at the wastebin, part cooling off |
| `RESUME` | Finishes any interrupted CFS operation, heats and primes at the wastebin, restores the fans, returns to the print |
| `CANCEL_PRINT` | Cancels and runs `END_PRINT` |
| `END_PRINT` | Retracts if hot, heaters and fans off, raises Z, parks at the wastebin |

If a CFS operation blocked the print, the CFS panel shows a recovery alert with the reason; fix the cause, then `RESUME`.

## Power-loss recovery

The profile enables `[power_loss_recovery]`, which saves checkpoints during the print and re-references Z on the bottom switch (`[z_align]`).

| Command | What it does |
| --- | --- |
| `PLR_STATUS` | Whether a print can be resumed and from where |
| `PLR_RECOVER CONFIRM=1` | Resumes from the checkpoint: drops the bed to the switch, homes X/Y, restores heaters, CFS, mesh and position |
| `PLR_DISCARD` | Deletes the checkpoint |

!!! note
    `PLR_RECOVER` has not yet been validated with a real supervised power cut. With a UPS you can disable `[power_loss_recovery]` and `[z_align]`; without them, Z can run at 64 microsteps (the MCU-driven `z_align` loses steps at 64). Without a UPS keep both, with Z at 16 microsteps.

## Calibration commands

| Command | When |
| --- | --- |
| `CALIBRATE_CUT_POS` | After changing the cutter or the toolhead |
| `MOTOR_CALIBRATE AXIS=XY` | When `MOTOR_STATUS` flags a motor calibration, or after mechanical work on X/Y |
| `BEDPID`, `NOZZLE_PID`, `NOZZLE_PID_HIGH` | After changing a heater or a thermistor |
| `PRTOUCH_HOME` | Z home with several touches, more accurate than a single `G28 Z` |
| `LUBRICATE_RAILS` | Spreads the rail lubricant |
| `TEST_SPEED`, `ACCELL_TEST_X/Y`, `WARMUP` | Skipped-step and motion stress tests |

All commands: [G-code reference](../GCODE_COMMANDS.md).
