# Hardware test plan

Tests that must be run **in person, next to the printer**. Each test lists what to prepare, what to do, what must happen and when to stop. A results table to fill in is at the end.

Created on 2026-10-03. The code under test is the `kalico-k2pro` branch `cfs-upstream-071c813` (commit `c1b8613d`), which integrates Jacob10383's firmware sync 071c813. At the owner's request the branch was **merged into `k2-pro-openhost` on 2026-10-03, before these tests** (merge `b8a69639`; firmware mirror `k2-openhost` `b8dc5af`). The CM5 runs `k2-pro-openhost`, so the tests below now validate the main branch.

## Before starting

- [ ] You are next to the printer and can reach the power switch.
- [ ] The printer is idle: `print_stats` is `standby` and nothing is paused.
- [ ] The CM5 runs the branch under test:
  ```bash
  ssh cm5 'cd ~/klipper && git log --oneline -1'
  ```
  must show `c1b8613d feat(cfs): integrate upstream firmware sync 071c813 ...`.
- [ ] `macros.cfg` on the CM5 contains `_BOX_RESUME_PREPARE` (the new macros).
- [ ] No pending recovery checkpoint: `PLR_STATUS` must report `recoverable=False`. Otherwise run `PLR_DISCARD`.
- [ ] CFS (slot indices as in Mainsail, labels as in the messages):

  | Index | Label | Current content |
  |---|---|---|
  | 0 | Box 1, slot 1 | black PETG-CF |
  | 1 | Box 1, slot 2 | present, no profile |
  | 2 | Box 1, slot 3 | black PETG-CF |
  | 3 | Box 1, slot 4 | brown PLA `#6C4E43` |

- [ ] Automatic runout swap is enabled: `box.runout_swap_enabled = true`.
- [ ] Remember that `idle_timeout` is effectively disabled: heaters stay on while paused. Do not leave the printer paused unattended.
- [ ] Mainsail console open. Note the start time of each test so the right part of `klippy.log` can be found later.

### Rolling back

If something goes wrong and you want the previous version back:

```bash
ssh cm5 'cd ~/klipper && git checkout k2-pro-openhost && cp ~/printer_data/config/macros.cfg.before-071c813-* ~/printer_data/config/macros.cfg && curl -s -X POST "http://127.0.0.1:7125/machine/services/restart?service=klipper"'
```

## Test order

Run them in this order: each test relies on what the previous one verified.

| # | Test | Approx. time |
|---|---|---|
| T0 | `z_align` homing after the merge | 5 min |
| T1 | Single-colour print with automatic mapping, pause and slot change | 30 min |
| T2 | Two-colour print with `BOX_PRINT_START`, pause and resume | 45 min |
| T3 | Automatic runout swap (two black PETG-CF spools) | 40 min |
| T4 | Power-loss recovery (single colour, then two colours) | 60 min |
| T5 | Cartographer on direct USB | separate session |

---

## T0 — `z_align` homing after the merge

**Goal:** the merge touched `z_align.py` (`ZDOWN` removed, messages changed). Check that homing on the bottom sensor still works as on 2026-10-03.

**Steps**
1. Bed clear above and below.
2. `G28`, wait for it to finish, then `M84`.
3. Repeat 3 times.

**Expected**
- Every cycle succeeds at the first attempt. The message is now `MCU z-align attempt 1/5: delta 0.0000mm` (no "steps").
- No "photoelectric error" and no unusual Z motor noise.

**Stop if:** homing fails or the Z motor makes noise. Roll back and report it.

---

## T1 — Single-colour print with automatic mapping, pause and slot change

**Goal**
- Check that a normally started print is mapped to the right slot by itself.
- Check the new pause and resume.
- Check that after a slot change during the pause, resume heats to the new filament's temperature.

**Preparation**
- In OrcaSlicer, a small object (20 mm cube or similar) in **PLA** with a colour close to brown. Upload it to Mainsail.
- Load a PLA spool in slot 2 (index 1) and give it a profile with a **different temperature** from the file (for example file at 220 °C, slot 2 profile at 210 °C). If you have no second PLA spool, skip steps 5–7.

**Steps**
1. Start the print **normally** from Mainsail, not from the mapping dialog.
2. Check: `box.auto_mapping.state = active`, `box.print_mapping.map = {"0": 3}`. The console must show `T0 (Box 1, slot 4)` being loaded.
3. After a few layers press **PAUSE**.
4. Expected while paused: the head lifts, cleans the nozzle and parks at the wastebin; nozzle at 140 °C, fans off.
5. While paused, load the other PLA: `BOX_SELECT_SLOT SLOT=1`.
6. Press **RESUME**.
7. Expected on resume:
   - the head stays at the wastebin and heats to the **slot 2 profile** temperature: check the extruder target in Mainsail;
   - it prepares the filament, then returns to the part **only once** and the print continues.
8. Let the print finish. At the end the filament is unloaded (`unload_after_print` is enabled).

**Check**
- No `Unknown command` errors in the console.
- No traceback in `klippy.log`.
- `box.recovery.blocked = false` at the end.

**Stop if:** RESUME errors out and the print stays paused. Note the exact message, do not cancel the print right away, and ask before intervening.

---

## T2 — Two-colour print with `BOX_PRINT_START`, pause and resume

**Goal**
- Explicit mapping from the Mainsail dialog.
- Tool change with the purge taken from the file's matrix.
- Per-tool temperatures from the file.
- Pause and resume after a colour change.

**Preparation**
- A two-colour object that **changes colour by height** (e.g. lower half T0, upper half T1), so even different materials only give a test part.
- Recommended: two PLA spools (slot 4 and slot 2) with **different temperatures per filament** in OrcaSlicer (e.g. 215 °C and 225 °C).
- Alternative: PLA slot 4 + PETG-CF slot 1. Adhesion between the two will be poor, which is fine for the test.

**Steps**
1. In Mainsail open the CFS mapping dialog on the file (it runs `BOX_PRINT_INFO`).
2. Map T0 → slot 4 and T1 → slot 2 and start. This is `BOX_PRINT_START FILENAME=<file> MAP=0:3,1:1`.
3. Check `box.print_mapping`: `filename` is set and the map is the one chosen.
4. At the colour change, expected in the console:
   - `Changing T0 (Box 1, slot 4) -> T1 (Box 1, slot 2)`;
   - `Purging ... (slicer matrix T0 -> T1)`;
   - the extruder target switches to T1's temperature.
5. A few layers after the change press **PAUSE**, wait 1–2 minutes, then **RESUME**.
6. Expected: resume at T1's temperature, no blob on the part, the print continues with T1.

**Check:** `box.print_mapping.active_tool = 1` and `active_slot = 1` after the change.

**Stop if:**
- the change loads a different slot from the mapped one;
- the purge is clearly wrong (zero or huge).

---

## T3 — Automatic runout swap

**Goal:** with two identical spools (black PETG-CF in slots 1 and 3), when the filament runs out the print must switch to the other spool by itself without stopping. This covers the 2026-10-03 fix plus the map update.

**Preparation**
- A single-colour **black PETG-CF** print of at least 30–40 minutes.
- Check `box.runout_swap_enabled = true`.
- Scissors or flush cutters at hand.

**Steps**
1. Start normally. Automatic mapping picks slot 1 or slot 3: note which one in `box.print_mapping.map`.
2. After a few layers **cut the filament of the active slot between the spool and the CFS inlet** and let the tail be pulled in.
3. Expected, without intervention:
   - when the tail passes the sensor, `Auto runout swap: Box 1, slot 1 -> Box 1, slot 3` (or the reverse);
   - retract and wipe, the head goes to the wastebin;
   - the other spool is loaded, a purge follows, the head returns to the part and the print continues;
   - `Auto runout swap complete: Box 1, slot 3 active`.
4. Check:
   - `box.print_mapping.map` now points to the new slot (e.g. `{"0": 2}`);
   - the source slot is marked empty, and its profile has **not** disappeared (that was the bug that was fixed).

**Stop if:** the print pauses instead of swapping. Note the reason shown and the `box.recovery` state, then try **RESUME**: it should retry by itself.

**After the test:** remove the leftover filament piece from the emptied slot's path and reload the spool.

---

## T4 — Power-loss recovery

**Goal:** check that `PLR_RECOVER` resumes the print after a real power cut:
- the Z reference is re-established with the bottom sensor (`z_align`);
- for a two-colour print, the tool → slot map is also restored.

**Preparation**
- Check whether the CM5 is powered from the printer PSU or separately, and note it: it changes what happens at the cut.
- `PLR_STATUS`: `enabled=True`, no old checkpoint.
- Nothing must be under the bed: on recovery it moves down to the bottom sensor.

**Part A — single colour**
1. Start a single-colour print of at least 15 minutes.
2. Wait for at least 10 layers (Z > 3 mm).
3. **Cut power to the printer** with the switch. Wait 30 seconds and power it back on.
4. When Klipper is ready, `PLR_STATUS` must report `recoverable=True` with file and position.
5. Keep a hand near the switch and run `PLR_RECOVER CONFIRM=1`.
6. Expected:
   - the bed moves down to the bottom sensor, then X/Y homing;
   - heating, the CFS reloads the slot and prepares the filament at the wastebin;
   - the print resumes at the saved line with no visible layer shift.

**Part B — two colours:** repeat with the T2 file and the same map. Cut power **after** the first colour change. After `PLR_RECOVER`:
- `box.print_mapping` must again show `filename` and the map;
- the next colour change must use the mapped slot, not the slot with the same number as the tool.

**Stop immediately (power switch) if:** before reaching the part the head goes too low or the Z position is clearly wrong. Then run `PLR_DISCARD`.

---

## T5 — Cartographer on direct USB

A separate, step-by-step guided session: connection to the CM5, check of `/dev/serial/by-id/...`, configuration change, automatic reset and reconnect, probing, touch and scan. Details are in [Cartographer3D](CARTOGRAPHER.md).

---

## Results

| Test | Date | Result | Notes (messages, log time) |
|---|---|---|---|
| T0 `z_align` homing | | | |
| T1 automatic mapping + pause/slot change | | | |
| T2 two-colour `BOX_PRINT_START` + pause | | | |
| T3 automatic runout swap | | | |
| T4A power-loss recovery, single colour | | | |
| T4B power-loss recovery, two colours | | | |
| T5 Cartographer direct USB | | | |

## After the tests

The integration is already merged (2026-10-03). After the tests:
1. Update [TEST_STATUS](TEST_STATUS.md) with the results.
2. Fix any failure on `k2-pro-openhost`, mirroring CFS extras into `k2-pro-custom-firmware:k2-openhost` first.
