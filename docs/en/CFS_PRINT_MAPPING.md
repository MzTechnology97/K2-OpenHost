# CFS print mapping on K2-OpenHost

Updated: **2026-10-02**.

## Goal

K2-OpenHost follows the current Jacob/Jacobean CFS model: slicer tools (`T0`, `T1`, ...) are **logical tools**, not permanently bound to physical CFS slots.

Before a mapped print starts, the UI inspects the G-code and asks which physical slot should supply each logical tool.

Example:

```text
Orca logical T0 -> physical CFS slot T1
Orca logical T1 -> physical CFS slot T3
```

The resulting start request is:

```text
BOX_PRINT_START FILENAME="folder/file.gcode" MAP="0:1,1:3"
```

## Upstream behavior used as reference

The behavior is derived from the current public work in:

- `Jacob10383/k2-plus-custom-firmware` — `box.py`, `box_change.py`, `box_gcode.py` and the `BOX_PRINT_INFO` / `BOX_PRINT_START` workflow;
- `Jacob10383/fluidd` — Filament Box and pre-print CFS mapping experience.

`HimAndRobot/creality-cfs-mainsail-integration` is also used as a visual/interaction reference for slot cards and filament presentation. K2-OpenHost does **not** use its direct Creality `web-server` / port `9999` transport.

## OpenHost architecture

```text
mainsail-k2openhost
        |
        | Moonraker WebSocket
        v
printer.objects.box
        |
        | BOX_PRINT_INFO / BOX_PRINT_START
        v
kalico-k2pro
        |
        | logical tool -> physical slot
        v
BoxChangeEngine
        |
        v
RS-485 / CFS
```

The frontend does not parse RS-485 and does not talk directly to a Creality CFS web service.

## Backend API

Load the additive mapping helper after `[box]`:

```ini
[box]
# ...

[box_print_mapping]
```

It adds:

```text
BOX_PRINT_INFO FILENAME="folder/file.gcode"
BOX_PRINT_START FILENAME="folder/file.gcode" MAP="0:1,1:3"
```

and extends the existing `box` status object with:

```json
{
  "print_mapping_version": 1,
  "print_mapping_enabled": true,
  "print_info": {
    "filename": "folder/file.gcode",
    "tools": [
      {
        "tool": 0,
        "color": "#FFFFFF",
        "material": "PLA",
        "name": "Generic PLA"
      }
    ]
  },
  "print_mapping": {
    "filename": null,
    "map": {},
    "active_tool": null,
    "active_slot": null
  }
}
```

## Metadata reader

`BOX_PRINT_INFO` reads the tail of an Orca-style G-code and uses the same metadata fields as Jacob's current implementation:

- `filament used [mm]`;
- `filament_colour`;
- `filament_type`;
- `filament_settings_id`;
- `flush_volumes_matrix`;
- `nozzle_temperature`;
- `nozzle_temperature_initial_layer`.

Only tools with non-zero filament usage are presented for mapping.

## Mainsail workflow

When the normal Mainsail **Print** dialog opens and `print_mapping_version >= 1`:

1. Mainsail sends `BOX_PRINT_INFO` for the selected file.
2. Kalico publishes the logical tools through `printer.objects.box.print_info`.
3. Mainsail shows a CFS mapping row for every used tool.
4. **Auto map** prefers a present slot with matching material + color. Among otherwise equivalent RFID candidates it prefers the lowest known remaining percentage, then falls back to the existing material/name/color scoring; the user can override every choice.
5. Physical empty slots are disabled. The external spool remains a selectable mapping target.
6. The Print button remains disabled while metadata is being read or while a required tool has no valid slot.
7. Mainsail starts the mapped job with `BOX_PRINT_START` instead of the normal `printer.print.start` call.
8. If the G-code contains no supported filament-usage metadata, Mainsail falls back to the normal print path.

## Backend validation before start

`BOX_PRINT_START` requires an exact mapping for every used logical tool and checks:

- Box/CFS driver readiness;
- valid target slot;
- physical slot online/present state;
- complete logical-tool map.

The mapping is installed after Virtual SD load/reset events and before the file is resumed, matching the ordering used by Jacob's current implementation.

## Compatibility with the validated OpenHost Box engine

The current hardware-validated OpenHost `BoxChangeEngine` predates Jacob's newer logical-tool-aware engine and indexes purge/temperature data using **physical slot numbers**.

For that reason `box_print_mapping.py` translates the Orca metadata before handing it to the existing engine:

```text
logical tool matrix/temperatures
          |
          v
logical tool -> physical slot map
          |
          v
physical-slot matrix/temperatures
```

The helper also wraps `PARSE_FLUSH_VOLUMES`. This is required because the current K2 `START_PRINT` macro calls that command; without the wrapper, the older parser would overwrite the translated physical-slot metadata with logical-tool-indexed data.

This compatibility layer is intentionally additive so the already validated K2 Pro RS-485, Box protocol, observation guard and motor-control work are not replaced wholesale while adopting the newer Jacob frontend/backend contract.

## Observation mode

When:

```ini
[box]
observation_mode: True
```

`print_mapping_enabled` is false.

`BOX_PRINT_INFO` remains useful because it only reads a G-code file. `BOX_PRINT_START` deliberately refuses to run because it would enable mutating CFS operations.

This was the first validation step on the real K2 Pro and remains the safe fallback configuration. Hardware validation has since moved to operational Box mode (`observation_mode: false`), where `BOX_PRINT_INFO` and auto-mapping are verified (see below).

## Validation status

### Implemented / source-reviewed

- Orca footer metadata parser;
- `BOX_PRINT_INFO`;
- `BOX_PRINT_START` mapping/slot validation;
- mapping fields in `printer.objects.box`;
- logical `Tn` to physical slot routing;
- translated purge matrix and nozzle temperatures;
- preservation of translated metadata through `PARSE_FLUSH_VOLUMES`;
- native CFS mapping UI in `mainsail-k2openhost`.

### Hardware-validated

- `BOX_PRINT_INFO` against real Orca-sliced files on the CM5;
- real `box.slots` inventory and CFS metadata in operational Box mode;
- backend auto-map against real slot metadata;
- fail-safe unresolved behavior when no compatible physical inventory exists;
- lowest-known-RFID-remaining preference between otherwise equivalent candidates;
- automatic mapping on a normal start during a real print: T0 → Box 1, slot 4 (2026-10-05);
- automatic runout swap during that print: slot 4 → slot 2, with the map updated to `{"0": 1}` (2026-10-06).

A two-tool PETG `cubo.gcode` was inspected successfully. With temporary black and cyan PETG physical-slot metadata, the backend produced `{0:1, 1:2}`; after those temporary profiles were removed, both logical tools correctly returned unresolved instead of silently selecting an incompatible source.

### Still to validate on hardware

1. single-tool `BOX_PRINT_START` started from the Mainsail mapping dialog (the automatic mapping on a normal start is done);
2. controlled multi-material tool change including purge matrix and temperature handling;
3. pause/resume with a slot change during a mapped job (the runout swap without a pause is done);
4. real-time RFID remaining estimate over a complete print, and the complete print itself: an 18-hour single-colour print was at 89 % with no errors on 2026-10-06.

Do not classify the mapped CFS print path as production-ready until those hardware tests are complete.
