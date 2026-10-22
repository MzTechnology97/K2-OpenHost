# OrcaSlicer and the CFS

Updated: **2026-10-09**. [Italiano](../it/ORCASLICER.md)

K2-OpenHost works with the **official OrcaSlicer**: no modified build is needed. Two things connect them:

1. **Filament sync** — the printer publishes its CFS slots in Moonraker's `lane_data` database namespace, the convention used by AFC and Happy Hare. OrcaSlicer 2.3.2 and later reads it when you press its filament **Sync** button on a Moonraker printer.
2. **Automatic mapping** — when a G-code starts (from OrcaSlicer, Mainsail or the Moonraker API), the backend maps each slicer tool to a CFS slot by material and colour, with warnings for spools that may run out. See [CFS print mapping](CFS_PRINT_MAPPING.md) and the Mainsail guide.

## Set up the printer in OrcaSlicer

1. Use OrcaSlicer **2.4.0 or later** (native "Moonraker (Klipper)" host type). 2.3.2 also reads `lane_data`.
2. Select or create the K2 Pro printer profile, then open its **physical printer / connection** settings.
3. **Host type:** `Moonraker (Klipper)`. **Hostname, IP or URL:** the external host, for example `k2host.local` or `192.168.1.50`.
4. Test the connection and save.

**OrcaSlicer 2.4.2: Sync cannot connect.** That release sends the placeholder header `X-Api-Key: 88888888` to Moonraker, whatever you type in the API key field ([OrcaSlicer PR #15550](https://github.com/OrcaSlicer/OrcaSlicer/pull/15550), not released yet). Moonraker accepts a trusted LAN client without a key but rejects a wrong one, so `moonraker.log` shows:

```text
401 GET /server/database/item?namespace=lane_data (<your PC>): Invalid API Key
```

Fix on the printer: let nginx drop only that placeholder, so OrcaSlicer is treated like Mainsail and other trusted LAN clients; real keys pass unchanged. The [K2-OpenHost Installer Helper](https://github.com/MzTechnology97/k2-openhost-installer-helper) installs this rule with Mainsail (menu 7 to add it to an existing host). By hand, add to `/etc/nginx/conf.d/k2openhost-orca-api-key.conf`:

```nginx
map $http_x_api_key $k2oh_api_key {
    "88888888" "";
    default    $http_x_api_key;
}
```

then add `proxy_set_header X-Api-Key $k2oh_api_key;` after both `proxy_pass http://apiserver...` lines of the Mainsail site, check with `sudo nginx -t` and reload with `sudo systemctl reload nginx`. Verified on the reference machine with OrcaSlicer 2.4.2.

## Ready-made profile for the K2 Pro

[`tools/orcaslicer/profiles`](https://github.com/MzTechnology97/K2-OpenHost/tree/main/tools/orcaslicer/profiles) has the printer preset and seven process presets (0.08 to 0.28 mm) the reference K2 Pro prints with: Klipper flavour, `START_PRINT`/`END_PRINT`/`PAUSE`, no change-filament G-code, thumbnails for Mainsail, `accel_to_decel` off, and the K2-OpenHost CFS plugin already selected. Filament presets are not included.

Download the [`.orca_printer` bundle](https://github.com/MzTechnology97/K2-OpenHost/raw/main/tools/orcaslicer/profiles/Creality%20K2%20Pro%200.4%20nozzle%20-%20newpurge-Kalico.orca_printer) and import it with **File → Import → Import Configs…**, then enter your host address with the Moonraker port (`k2host.local:7125`) in the printer's connection settings: address and API key are empty in the files. Details in the folder's [README](https://github.com/MzTechnology97/K2-OpenHost/tree/main/tools/orcaslicer/profiles#readme).

## Sync the filaments

Press **Sync** (the arrows button at the top of the filament list in the Prepare tab). OrcaSlicer creates one filament per occupied CFS slot, grouped four by four like CFS units:

| CFS | OrcaSlicer |
| --- | --- |
| Box 1, slot 1 … slot 4 | filaments 1–4 (tools T0–T3) |
| Box 2, slot 1 … slot 4 | filaments 5–8 (tools T4–T7) |
| empty slot | empty placeholder |

Each synced filament gets the slot's **material** and **colour**. Slice as usual: T0 prints from Box 1 slot 1, T1 from slot 2, and so on, and the automatic mapping confirms the match when the print starts.

Sync again after changing spools: the printer updates `lane_data` within a few seconds of any slot change (RFID read, slot editor, Use in slot).

**HelixScreen** keeps its own slot overrides in the same `lane_data` namespace and removes a lane when it clears one, for example after a spool swap. The printer republishes the slot at its next change, and a lane HelixScreen already removed is not an error. If OrcaSlicer misses a slot right after a swap, press **Sync** again once the new spool is read.

## What is published

One entry per occupied CFS slot with a material (the external spool is not published):

```json
"lane2": {
  "lane": "1",
  "material": "PLA",
  "color": "#B1BEC6",
  "nozzle_temp": 215,
  "bed_temp": null,
  "spool_id": null,
  "name": "Bambulab PLA Basic",
  "vendor": "Bambulab",
  "filament_id": "05628",
  "orca_filament_id": "OFoiVqVM",
  "scan_time": ""
}
```

`lane` is the tool number (0-based physical slot). OrcaSlicer currently reads `lane`, `material`, `color`, `nozzle_temp` and `bed_temp`. `filament_id` is the CFS filament (library) ID and `orca_filament_id` the OrcaSlicer preset ID (below); with `name`, `vendor` and `spool_id` they are there for brand-specific preset matching, which OrcaSlicer does not do yet for Moonraker printers ([#13006](https://github.com/OrcaSlicer/OrcaSlicer/issues/13006)).

Check what the printer publishes, with the same request OrcaSlicer makes:

```bash
curl -s "http://k2host.local:7125/server/database/item?namespace=lane_data"
```

## OrcaSlicer preset of each filament

Every CFS filament carries the OrcaSlicer `filament_id` of its preset, the ID OrcaSlicer matches presets with. It never changes the filament's own ID, name, brand or RFID codes.

- **Default** (Kalico, generated from OrcaSlicer's profiles): the K2 Pro preset of a Creality or Generic catalog filament (`Hyper PLA` → "Hyper PLA @K2 Pro-all"), the OrcaSlicer filament-library product of a Bambu tag (`Bambulab PETG HF` → "Bambu PETG HF @System"), or a preset named like the profile.
- **Your choice**: in Mainsail's filament library, a card's menu → **OrcaSlicer preset…** (system profiles included), or the OrcaSlicer section of the editor; `_BOX_FILAMENT_ORCA_ID` from the console.
- **Your own OrcaSlicer preset**: create it from scratch (Filament → **+** → *Create filament*), then copy `"filament_id"` (`P…`) from `%APPDATA%\OrcaSlicer\user\<account>\filament\base\<name>.json`. A preset saved from another one ("Save as") has no ID of its own: it shares its parent's, and OrcaSlicer would select the parent.

OrcaSlicer 2.4.2 and the built-in Moonraker agent of 2.5 do not read the ID: their sync picks the generic preset per material. The [K2-OpenHost CFS plugin](#orcaslicer-25-the-k2-openhost-cfs-plugin) for OrcaSlicer 2.5 sends it. [OrcaSlicer PR #16208](https://github.com/OrcaSlicer/OrcaSlicer/pull/16208) reads a lane's `filament_id`; the IDs Kalico assigns follow OrcaSlicer's current profiles (`OF…`), which replaced the 2.4.2 ones (Bambu PLA Basic: `OGFA00` in 2.4.2, `OFoiVqVM` now).

## OrcaSlicer 2.5: the K2-OpenHost CFS plugin

OrcaSlicer 2.5 (alpha since 2026-10-16) loads Python plugins. [`tools/orcaslicer/k2_openhost_cfs.py`](../../tools/orcaslicer/k2_openhost_cfs.py) is one plugin with three parts. It talks to the same Moonraker as the built-in Moonraker agent:

- **Printer agent: sync by preset ID.** Each CFS slot reaches OrcaSlicer with the `orca_filament_id` Kalico keeps per filament (above), so Sync selects that preset, for example Bambu PLA Basic for a Bambu PLA Basic spool, not Generic PLA. A slot without an ID falls back to OrcaSlicer's `Generic <material>` preset. The Device tab also works through the agent (state, temperatures, progress, pause/resume/stop, G-code line).
- **CFS panel: the slot of each filament.** A panel beside the 3D view draws each CFS with its four spools: colour, material, name, RFID remaining, and the unit's temperature and humidity. Below it are the project's filaments. The plugin proposes a slot by material, then closest colour; click a filament, then a spool, to change it before sending.
- **CFS panel: runout order.** The same panel switches the automatic change to an identical spool (`_BOX_SET_RUNOUT_SWAP`) on and off. It also lists every group of identical spools (same material and colour) in the order Kalico will use them, with ▲▼ to change the order and **Automatic order** to go back to Kalico's own (lowest remaining first). Changes are saved on the printer with `_BOX_SET_RUNOUT_ORDER`, as Mainsail does, and apply to the next runout.
- **G-code map.** When OrcaSlicer exports or uploads the G-code, the plugin writes that choice after the first line, for example `; K2OH_TOOL_MAP = 0:1,2:0`. Kalico (`box_print_mapping`) uses it when the print starts, instead of its automatic mapping.
  - The map is written only for the printer preset and filament list it was chosen for, and only when every filament the plate uses has a slot. Otherwise nothing is written and Kalico maps the print automatically.
  - Kalico also ignores, with a console message, a map whose slot is empty or offline, and falls back to its automatic mapping.

This works with the classic **Upload and print** of the Moonraker print host. OrcaSlicer's global option *Use printer agents instead of print hosts* is not needed. In 2.5-alpha that option changes the print flow and the Device tab of every non-Bambu printer, so keep it off if you have others. With it on, OrcaSlicer's own Bambu-style print dialog maps the slots instead, and the plugin starts the job with `BOX_PRINT_START … MAP=`.

**Install** (OrcaSlicer 2.5 or later; Kalico with `box_print_mapping` slicer-map support):

1. Download `k2_openhost_cfs.py`.
2. In OrcaSlicer open the plugin manager and install it as a local plugin. OrcaSlicer copies it to `%APPDATA%\OrcaSlicer\orca_plugins\`.
3. In the printer preset (**Printer settings → Basic information → Advanced**), set **Printer Agent** to **K2-OpenHost CFS**. Set the print host to the Moonraker address **with its port**, for example `10.10.1.97:7125`, then save the preset.
   - A printer OrcaSlicer already knows under the plain address stays bound to the built-in Moonraker agent.
   - The new address makes OrcaSlicer add it under this agent.
   - **Device UI** (advanced mode): `http://10.10.1.97`, the plain address. The Device tab opens this field when it is set, so it keeps showing Mainsail while the print host carries the port.
4. OrcaSlicer asks to let the plugin create a thread and connect to the Moonraker address: allow both. The first connection is refused while the question is open; the plugin retries every 2 s.
5. In the process preset, switch to **Advanced** mode, open **Others → Slicing Pipeline Plugin**, add **K2-OpenHost CFS G-code map** and save the preset; do it in every process preset you use with the K2. OrcaSlicer writes into the G-code only with the capabilities listed there: enabling the plugin is not enough. Until it is listed, the CFS panel shows a warning.
6. Press **Sync** in the filament list.
7. Slice: when slicing finishes for the K2, the CFS panel opens by itself beside the 3D view (or comes back if you closed it) with the slots refreshed. Changing presets or the project refreshes an open panel, and it hides for other printers. You can also open it from the plugin manager (**K2-OpenHost CFS slots**). Its setting `auto_open: false` turns the opening after slicing off.
8. Check the slots, then **Upload and print**. The map is written when the file is uploaded or exported, so choosing the slots after slicing is fine.

The panel keeps your choice until the project's filaments change. Then it proposes again: press **Refresh** after changing filaments, and **Propose** to start over.

Sync selects **root presets** only: system presets, and your own presets made with **Create filament**, which have their own `P…` ID. A preset saved from another one (it shows a parent under *Dependencies*) is never picked, by any agent: OrcaSlicer takes its parent instead. The CFS panel has no such limit: it maps whatever filament presets the project uses. To make Sync pick your tuned preset, create it with **Create filament** (vendor, type, based on the same system preset), copy your settings into it, and give its `P…` ID to the CFS filament in Mainsail.

The **Filament ID Fixer** plugin (OrcaSlicer plugin catalogue) does this for you: filter `@K2`, select your presets, **Apply**, restart OrcaSlicer. Each preset is detached from its parent and gets its own `U…` ID (a backup zip is made first). Give that ID to the CFS filament in Mainsail (filament library → **OrcaSlicer preset…**, or `_BOX_FILAMENT_ORCA_ID ID=<filament> ORCA_ID=<U…>`). A detached preset no longer follows changes made to its parent.

The agent has three settings:
- `poll_interval_s`: status refresh, default 2 s;
- `model_id`: the printer model sent to OrcaSlicer, by default the preset's model with `_`, here `Creality_K2_Pro`;
- `use_slot_map`: false makes prints started through the agent always skip the dialog's map.

Its log lines (`[k2oh-cfs]`) are in `%APPDATA%\OrcaSlicer\log\python_*.log`.

**Tested so far**
- With OrcaSlicer's own Python (3.12), against the reference printer's Moonraker: the four slots with their IDs, the printer state, and the panel's slot list and proposal.
- In OrcaSlicer: Sync through the agent.

The panel inside OrcaSlicer and a print started with its map are not tested yet. The OrcaSlicer plugin API is still alpha and may change.

## Slot mapping when sending

Official OrcaSlicer shows a filament → slot dialog when sending only for the **CrealityPrint** host type (stock firmware). [Jacob10383's OrcaSlicer fork](https://github.com/Jacob10383/OrcaSlicer) adds it for Moonraker printers that publish `box.print_mapping_version: 1`, which K2-OpenHost does: each project filament gets a **Load from: Box 1, slot n** choice, and the job starts with `BOX_PRINT_START` and that map, as Mainsail's print dialog does. Its filament sync reads the `box` object directly and picks presets by name. Builds are in its `Nightly-Rolling` release (a Windows portable zip runs next to an installed OrcaSlicer). The fields were checked against the reference printer; it has not been used for a print yet.

Without the fork or the plugin above, slice and upload as usual: the automatic mapping matches tools to slots when the print starts.

## accel_to_decel

Kalico has no `ACCEL_TO_DECEL`: its `SET_VELOCITY_LIMIT` drops the parameter silently and uses `minimum_cruise_ratio` from `printer.cfg` (0.5 in the K2 profile, the old 50 %). With OrcaSlicer's **accel_to_decel** option on, every acceleration change adds an `ACCEL_TO_DECEL=` that does nothing. Turn the option off in the process presets of the Kalico printer; to change the ratio, set `minimum_cruise_ratio` in `printer.cfg` or add `SET_VELOCITY_LIMIT MINIMUM_CRUISE_RATIO=<0..0.99>` to the start G-code.

## Limits

- OrcaSlicer picks a **generic preset per material** ("Generic PLA" for a PLA slot) with the slot colour, not the brand preset, unless you use the K2-OpenHost CFS plugin of OrcaSlicer 2.5. Choose your own preset afterwards if you need its settings; the CFS mapping still works.
- The filament profiles have no bed temperature, so `bed_temp` is empty and OrcaSlicer keeps the preset's.
- The external spool is not part of the sync; map it in Mainsail's print dialog when needed.

## Turn it off

In `macros/box.cfg`:

```ini
[box]
publish_lane_data: false
```

Restart Klipper. Existing lanes then stay in the Moonraker database until removed; delete the `lane_data` namespace from Mainsail's database settings if needed.
