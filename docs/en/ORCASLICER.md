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

Released OrcaSlicer (2.4.2) does not read the ID yet: the sync still picks the generic preset per material. [OrcaSlicer PR #16208](https://github.com/OrcaSlicer/OrcaSlicer/pull/16208) reads a lane's `filament_id`; the IDs Kalico assigns follow OrcaSlicer's current profiles (`OF…`), which replaced the 2.4.2 ones (Bambu PLA Basic: `OGFA00` in 2.4.2, `OFoiVqVM` now).

## Slot mapping when sending

Official OrcaSlicer shows a filament → slot dialog when sending only for the **CrealityPrint** host type (stock firmware). [Jacob10383's OrcaSlicer fork](https://github.com/Jacob10383/OrcaSlicer) adds it for Moonraker printers that publish `box.print_mapping_version: 1`, which K2-OpenHost does: each project filament gets a **Load from: Box 1, slot n** choice, and the job starts with `BOX_PRINT_START` and that map, as Mainsail's print dialog does. Its filament sync reads the `box` object directly and picks presets by name. Builds are in its `Nightly-Rolling` release (a Windows portable zip runs next to an installed OrcaSlicer). The fields were checked against the reference printer; it has not been used for a print yet.

Without it, slice and upload as usual: the automatic mapping matches tools to slots when the print starts.

## accel_to_decel

Kalico has no `ACCEL_TO_DECEL`: its `SET_VELOCITY_LIMIT` drops the parameter silently and uses `minimum_cruise_ratio` from `printer.cfg` (0.5 in the K2 profile, the old 50 %). With OrcaSlicer's **accel_to_decel** option on, every acceleration change adds an `ACCEL_TO_DECEL=` that does nothing. Turn the option off in the process presets of the Kalico printer; to change the ratio, set `minimum_cruise_ratio` in `printer.cfg` or add `SET_VELOCITY_LIMIT MINIMUM_CRUISE_RATIO=<0..0.99>` to the start G-code.

## Limits

- OrcaSlicer picks a **generic preset per material** ("Generic PLA" for a PLA slot) with the slot colour, not the brand preset, until it reads the preset ID above. Choose your own preset afterwards if you need its settings; the CFS mapping still works.
- The filament profiles have no bed temperature, so `bed_temp` is empty and OrcaSlicer keeps the preset's.
- The external spool is not part of the sync; map it in Mainsail's print dialog when needed.

## Turn it off

In `macros/box.cfg`:

```ini
[box]
publish_lane_data: false
```

Restart Klipper. Existing lanes then stay in the Moonraker database until removed; delete the `lane_data` namespace from Mainsail's database settings if needed.
