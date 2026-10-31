# Hardware test plan

Tests to run next to the printer. Each one says what to prepare, what to do, what must happen and when to stop. The [test status](TEST_STATUS.md) says which ones have passed.

## Before starting

- You can reach the power switch.
- The printer is idle: `print_stats` is `standby` and nothing is paused.
- The CM5 runs `k2-pro-openhost`: `ssh cm5 'cd ~/klipper && git log --oneline -1'`.
- No old recovery checkpoint: `PLR_STATUS` reports `recoverable=False`, otherwise run `PLR_DISCARD`.
- Automatic runout swap is on: `box.runout_swap_enabled = true`.
- Heaters stay on while paused (`idle_timeout` is effectively off), so never leave a paused print alone.
- Keep the Mainsail console open and note the start time of each test, to find it in `klippy.log` later.

## Tests

| # | Test | Time | State |
| --- | --- | --- | --- |
| T0 | `z_align` homing | 5 min | passed 2026-10-05 |
| T1 | Single colour with automatic mapping, pause and slot change | 30 min | mapping passed, pause still open |
| T2 | Two colours with `BOX_PRINT_START`, pause and resume | 45 min | open |
| T3 | Automatic runout swap | 40 min | passed 2026-10-06, 10-15, 10-16 |
| T4 | Power-loss recovery | 60 min | open |
| T5 | Cartographer | separate session | mixed mode passed 2026-10-26, sole probe open |
| T6 | HelixScreen 1.0.6-k2oh.8 on the screen | 30 min | open |

## T1: pause and slot change

Automatic mapping is already verified; what is left is the pause.

**Prepare:** a small PLA object, and a second PLA spool whose profile has a different temperature from the file (file 220 °C, spool 210 °C).

1. Start the print normally from Mainsail.
2. After a few layers press **Pause**. The head lifts, cleans the nozzle and parks at the wastebin; the nozzle drops to 140 °C.
3. Load the other PLA: `BOX_SELECT_SLOT SLOT=<index>`.
4. Press **Resume**. The head stays at the wastebin, heats to the new spool's temperature, prepares the filament, returns to the part once and the print goes on.
5. Let it finish: the filament is unloaded at the end.

**Check:** no `Unknown command`, no traceback in `klippy.log`, `box.recovery.blocked = false` at the end.

**Stop if** Resume fails and the print stays paused. Note the message and do not cancel straight away.

## T2: two colours

**Prepare:** an object that changes colour by height (lower half T0, upper half T1), two PLA spools with different temperatures per filament in OrcaSlicer.

1. In Mainsail open the CFS mapping dialog on the file, map T0 and T1 to two slots and start (`BOX_PRINT_START FILENAME=<file> MAP=0:<slot>,1:<slot>`).
2. `box.print_mapping` shows the file name and the chosen map.
3. At the colour change the console shows `Changing T0 (...) -> T1 (...)` and `Purging ... (slicer matrix T0 -> T1)`, and the extruder target moves to T1's temperature.
4. A few layers later press **Pause**, wait a minute or two, then **Resume**: the print goes on with T1 at its temperature, with no blob on the part.

**Check:** `box.print_mapping.active_tool = 1` after the change.

**Stop if** the change loads a slot other than the mapped one, or the purge is clearly wrong (none, or huge).

## T4: power-loss recovery

The reference printer is on a UPS with `[power_loss_recovery]` and `z_align` turned off, so this test needs a printer with the generic profile.

**Prepare:** note whether the host is powered from the printer or separately. `PLR_STATUS` reports `enabled=True` and no old checkpoint. Nothing under the bed: recovery lowers it to the bottom sensor.

**A, single colour**
1. Start a print of at least 15 minutes and wait until Z is above 3 mm.
2. Switch the printer off, wait 30 s, switch it on.
3. When Klipper is ready, `PLR_STATUS` reports `recoverable=True` with the file and the position.
4. With a hand on the switch run `PLR_RECOVER CONFIRM=1`. The bed goes down to the bottom sensor, X/Y home, the nozzle heats, the CFS reloads the slot, and the print resumes at the saved line with no layer shift.

**B, two colours:** repeat with the T2 file and cut the power after the first colour change. After `PLR_RECOVER`, `box.print_mapping` shows the file and the map again, and the next colour change uses the mapped slot.

**Switch off at once if** the head goes too low or Z is clearly wrong before it reaches the part, then run `PLR_DISCARD`.

## T5: Cartographer as the only probe

Mixed mode (PRTouch for Z, Cartographer for the mesh) is verified. To use the Cartographer alone, follow [Cartographer3D](CARTOGRAPHER.md): `register_as_probe: True`, scan and touch calibration, then homing, mesh and a first layer.

## T6: HelixScreen 1.0.6-k2oh.8

On the printer screen, with the printer idle.

1. **Filament list:** open a slot's editor, then *Change filament*. The list is Kalico's library, with *Orca: ...* under the profiles that have a preset.
2. **New filament:** add one from the list. It appears in Mainsail's library and on the screen without a restart.
3. **Unknown tag:** with a spool whose tag Kalico does not know, the CFS card shows the code. Adding a filament from that slot's editor applies it to the slot at once.
4. **Touch:** Settings > Touch & input, tap a sensitivity preset once. The card says the configuration is fixed and the presets disappear.
5. **CFS page:** load and unload a slot and watch the stage text (for example "Loading 2 · to the head 3/5"); check the external spool card.
6. **Print view:** during a print with several objects, exclude one from the bed map.
7. **Updates:** `k2oh-setup helix-restore` puts the previous version back; the update check in the app finds the next release.

**Check:** `/mnt/UDISK/helixscreen/logs/helix.log` has no errors and contains `catalog from the host library`.

## After the tests

Write the results in the [test status](TEST_STATUS.md). Fix any failure on `k2-pro-openhost` (Kalico) or `k2-openhost` (HelixScreen).
