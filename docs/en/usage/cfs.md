# Using the CFS

The Creality Filament System is driven by Kalico's `box` module through the RS-485 channel. This page explains what you do with it every day. The UI is the [Mainsail CFS panel](mainsail.md#cfs-panel); every action is also a [G-code command](../GCODE_COMMANDS.md).

## Slots and names

| | One CFS | Several CFS |
| --- | --- | --- |
| Slot numbers in commands | 0–3 (`SLOT=0` is slot 1) | box 1: 0–3, box 2: 4–7, box 3: 8–11, box 4: 12–15 |
| Names in the UI and console | `Box 1, slot 3` / `Slot 3` | `Box 2, slot 4` / `B2·S4` |
| External spool | the slot after the last CFS slot (4 with one CFS) | same |

Slicer tools keep their names `T0`, `T1`…: a tool is **logical**, mapped to a physical slot when the print starts.

## Loading and unloading

| Action | Panel | Command |
| --- | --- | --- |
| Load a slot into the printhead | ▶ on the tile | `BOX_SELECT_SLOT SLOT=<n>` (full change with cut, unload of the current filament and purge) or `BOX_LOAD SLOT=<n>` (hotend empty, no cut or purge) |
| Unload | **Unload** under the path | `BOX_UNLOAD` (heats, cuts, parks at the wastebin, pulls back to the CFS) |
| Pull back only, cold | — | `BOX_UNLOAD MANUAL=1` |
| Cut | — | `BOX_CUT` (needs `cut_pos_x`, see `CALIBRATE_CUT_POS`) |

During a load or unload the filament path shows each step: `Feeding to buffer`, `Feeding to printhead`, `Seating in the extruder`, `Retracting to CFS`… Manual loads are disabled while printing.

!!! tip "RFID reread on a loaded slot"
    A slot loaded toward the printhead cannot be reread: the CFS pulls the filament back past its reader and stalls against the extruder gears. Unload it first.

## RFID spools

When a spool is inserted, the CFS reads its tag and Kalico fills the slot automatically (source `RFID`). The read-only sheet shows the tag data and the remaining filament.

![RFID information](../../images/mainsail/cfs-rfid-info.png){ width="520" }

| Tag | Supported |
| --- | --- |
| Creality RFID (stock spools, K2-RFID app tags) | Yes, with any CFS firmware |
| Bambu Lab | With the API7 CFS firmware ([third-party RFID](../cfs-firmware/third-party-rfid.md)) |
| QIDI and other MIFARE Classic vendors | With the API7 CFS firmware |

Commands: `BOX_RFID_SCAN` (all populated slots), `_BOX_RFID_READ_SLOT SLOT=<n>` (one slot).

### Unknown tags

A tag with a material code that is not in the library shows `Unknown RFID` and an orange outline. Press the tag button: the library opens a new profile already filled with the tag code and colour. Complete it and save: every spool with that code resolves at once.

| Tile | New profile from the tag |
| --- | --- |
| ![Unknown RFID tile](../../images/mainsail/cfs-unknown-rfid-tile.png){ width="200" } | ![Profile prefilled from the tag](../../images/mainsail/cfs-unknown-rfid-editor.png) |

## Spools without RFID

Press ✎ on the tile, choose **brand → material → filament profile**, then the **colour of this spool**, and **Save** (`_BOX_SLOT_ASSIGN`). The colour belongs to the slot, not to the profile. **Reset slot** clears it (`_BOX_SLOT_CLEAR`).

![Slot editor](../../images/mainsail/cfs-slot-editor-filled.png)

The **external spool** (fed from the back of the printer) uses the same editor; **Read external RFID** reads a tagged spool with the external reader.

## Filament library

The library holds the read-only **system catalog** (61 Creality and Generic profiles from the public K2-RFID database) and **your profiles**, saved in `~/printer_data/config/cfs_filaments.json`.

![Filament library](../../images/mainsail/cfs-library-list.png)

Each profile has: brand, material, name (ideally the OrcaSlicer preset name), a 5-digit ID (`90001` and up for yours; tag code `1` + ID), temperatures, default colour, pressure advance, max flow, nominal spool length, RFID code, Spoolman ID and the **OrcaSlicer preset**.

- **New filament** → start from a similar profile → fill in → **Create filament** (`_BOX_FILAMENT_SET`).
- **Use in slot** assigns it without opening the slot editor.
- System profiles are read-only: **Create custom from this** makes an editable copy.
- The file can be edited from Mainsail's file manager; `_BOX_FILAMENT_RELOAD` reloads it.

![Filament editor](../../images/mainsail/cfs-library-editor.png)

### Pressure advance and max flow

When a slot is loaded, the box applies the slot's pressure advance to the extruder (unless the slicer sets PA itself in the file). Source order: slot profile → library filament → material default. `_BOX_SLOT_PA_SET SLOT=<n> PRESSURE_ADVANCE=<v>` saves a calibrated value into the slot's filament profile. `apply_pressure_advance: False` in `[box]` turns this off.

## Remaining filament

Every RFID spool shows how much filament is left, as a ring sector, a percentage and metres.

- **Kalico's estimate** starts from the tag's spool length and decreases with the filament used during prints (CFS encoder, else `print_stats`). It is saved in `~/printer_data/filament_box.json` and survives restarts.
- **The CFS's own percentage** is read every 30 s. With stock firmware it can only lower the estimate. With the experimental **CFG5T/CFG6** firmware the CFS counts type-4 consumption live and **leads** the estimate: see [Live remaining filament](../cfs-firmware/remaining.md).
- **Tags without a serial** (stock `000000`, K2-RFID `000001`): the estimate belongs to the bay. Removing the spool drops it; the next insertion starts a new spool at 100 % (or the CFS value).
- **A new spool with an old estimate**: `_BOX_RFID_SPOOL_NEW SLOT=<n> [REMAINING=100]`.

## Runout swap

With **Runout swap** on, spools of **exactly the same material and colour** form a group. When the loaded spool runs out during a print, the box continues on the next spool of the group without pausing. Without a replacement the print pauses.

![Runout swap](../../images/mainsail/cfs-runout-single.png){ width="420" }

The order of the spools is:

1. your **manual order**, if set;
2. otherwise the **lowest RFID remaining first**;
3. otherwise slot order.

### Choosing the order

Useful for spools without RFID (a full 1 kg spool, a 300 g one and a nearly empty one): in the group press **Order**, move the spools with ↑ ↓ and **Save**.

| Editor | Saved |
| --- | --- |
| ![Order editor](../../images/mainsail/cfs-runout-order-2-editor.png) | ![Saved order](../../images/mainsail/cfs-runout-order-4-saved.png) |

Command: `_BOX_SET_RUNOUT_ORDER ORDER=2,1,0` (0-based slots), `ORDER=AUTO` to reset. It can be changed during a print; the next runout follows it. The same order is editable from the [OrcaSlicer plugin's CFS panel](orca-plugin.md#runout-order).

## Mapping a print to the slots

A slicer file uses logical tools (`T0`, `T1`…). When a print starts, each tool is mapped to a physical slot:

| How the print starts | Who maps |
| --- | --- |
| Mainsail **Print** dialog | You, in the dialog (auto map proposed): `BOX_PRINT_START ... MAP=` |
| OrcaSlicer upload-and-print, Moonraker API | Kalico's **automatic mapping** (`auto_map_prints: true`), by material and colour |
| OrcaSlicer with the [K2-OpenHost plugin](orca-plugin.md) | The slots you chose in the plugin's CFS panel (`; K2OH_TOOL_MAP` in the file), else automatic |

The automatic matcher never pairs a base material with its filled variant (PETG with PETG-CF). A tool that cannot be matched blocks the start (`auto_map_block_unresolved: true`) instead of guessing. Details: [CFS print mapping](../CFS_PRINT_MAPPING.md).

### Warnings

Warnings never block the print. They appear in the dialog, in the console at start and in the panel while printing:

| Warning | When |
| --- | --- |
| **May run out** | The RFID remaining of the chosen spool (plus identical spools with runout swap) is below what the slicer expects + 10 % + 1 m |
| **Material variant** | A base material on its filled variant, or the reverse (chosen by hand) |
| **Humid CFS** | The CFS is more humid than the material tolerates: PVA 20 %, PA 25 %, PC 35 %, TPU 40 %, PETG-CF 45 %, PETG/ABS/ASA 50 %, PLA 55 % (`humidity_limits` overrides) |

During the print a live check compares, every minute, the filament each tool still needs with what its spool has left (`low_filament_live`).

## Clog detection

Pauses the print when the extruder feeds `clog_extruder_length` (80 mm) while the CFS does not refill. Switch: **Clog detection** in the CFS settings menu, or `_BOX_SET_CLOG_DETECTION ENABLE=0|1`.

## Other settings

| Setting | Command | Default |
| --- | --- | --- |
| Unload after print | `_BOX_SET_UNLOAD_AFTER_PRINT ENABLE=1` | off |
| Read RFID on insert | `_BOX_SET_RFID_INSERT_READING ENABLE=1` | on |
| Read RFID at startup | `_BOX_SET_RFID_STARTUP_READING ENABLE=1` | off: cached slots are restored without rereading |

## Where the data lives

| File | Content |
| --- | --- |
| `~/printer_data/config/cfs_filaments.json` | Your filament profiles and OrcaSlicer preset overrides |
| `~/printer_data/filament_box.json` | Slot assignments, remaining estimates, settings, runout order, box identities |
| `~/klipper/config/k2/cfs_system_filaments.json` | The read-only system catalog |

Both `printer_data` files are included in the helper's [backup](../installation/backup.md).
