# 3. First start and checks

Go through these checks in order, with the printer supervised, before the first real print.

## 1. Doctor

```bash
~/k2-openhost-installer-helper/helper.sh doctor
```

Every line should be green. Red `✘` lines say what is wrong and how to fix it.

![Doctor output](../../images/helper/cli-doctor.png)

The same check runs by itself after every boot: `K2-OpenHost check after boot: OK.` appears in the Klipper console. See [Doctor and health check](../helper/doctor.md).

## 2. Mainsail

Open `http://k2host.local/` (or `http://<ip>/`). The dashboard shows the printer state, temperatures, the **CFS** panel with the filament path, and the **Motors** panel. In the console, check:

```text
BOARD_STATUS        ; T113 bridges up, MCU power on
SERIAL_STATUS       ; RS-485 link ok
MOTOR_STATUS        ; X, Y, E motors ready
BOX_DEBUG           ; CFS online
```

## 3. Motion and homing

1. Clear the bed. Keep a hand near the emergency stop (Mainsail's **Emergency stop**, or power).
2. `G28`. With `[z_align]` the bed first drops to the bottom switch, then X/Y home sensorless and Z homes with the nozzle (PRTouch).
3. Move each axis a few millimetres from Mainsail and check the direction.

If homing is refused because a motor calibration is flagged as suspicious: `MOTOR_STATUS`, then `MOTOR_CALIBRATE AXIS=XY` (two calls: the first one asks you to centre the printhead and lower the bed).

## 4. Heaters

| Check | Command |
| --- | --- |
| Bed PID (100 °C) | `BEDPID` (saves and restarts Klipper) |
| Nozzle PID (230 °C, part fan on) | `NOZZLE_PID` |
| High-temperature nozzle PID (280 °C) | `NOZZLE_PID_HIGH` |
| Chamber | `M141 S45`, watch it rise, then `M141 S0` |

## 5. Filament cutter

The CFS cuts the filament at the toolhead before every unload. Find the cutter position once:

```text
CALIBRATE_CUT_POS
```

It homes X/Y if needed and saves `cut_pos_x`. Run it again after changing the cutter or the toolhead.

## 6. CFS

1. Insert a spool: the CFS reads its RFID tag (Creality tags, or third-party tags with the API7 CFS firmware). Spools without a tag: set the filament with the ✎ button of the slot ([slot editor](../usage/cfs.md#spools-without-rfid)).
2. Load a slot from the CFS panel (▶), then unload (**Unload**). Watch the filament path.
3. Turn on **Runout swap** in the CFS settings menu if you have identical spools.

## 7. Input shaper (optional)

Shake&Tune is installed by the full install. Run the resonance test with the bed clear; see the [Klippain Shake&Tune documentation](https://github.com/Frix-x/klippain-shaketune).

## 8. Slicer and first print

1. Set up [OrcaSlicer](../ORCASLICER.md) with the Moonraker host and the `START_PRINT` start G-code ([Printing](../usage/printing.md#slicer-start-and-end-g-code)).
2. Print a small single-colour part, supervised.
3. Then a two-colour part, still supervised.

The full validation procedure, test by test, is the [hardware test plan](../HARDWARE_TEST_PLAN.md).

!!! warning "Never unattended"
    Never leave the printer unattended while it is controlled by the external host. Keep smoke detection and a fire extinguisher near it.
