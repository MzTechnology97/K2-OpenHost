# OrcaSlicer and the CFS

Updated: **2026-10-04**. [Italiano](../it/ORCASLICER.md)

K2-OpenHost works with the **official OrcaSlicer**: no modified build is needed. Two things connect them:

1. **Filament sync** — the printer publishes its CFS slots in Moonraker's `lane_data` database namespace, the convention used by AFC and Happy Hare. OrcaSlicer 2.3.2 and later reads it when you press its filament **Sync** button on a Moonraker printer.
2. **Automatic mapping** — when a G-code starts (from OrcaSlicer, Mainsail or the Moonraker API), the backend maps each slicer tool to a CFS slot by material and colour, with warnings for spools that may run out. See [CFS print mapping](CFS_PRINT_MAPPING.md) and the Mainsail guide.

## Set up the printer in OrcaSlicer

1. Use OrcaSlicer **2.4.0 or later** (native "Moonraker (Klipper)" host type). 2.3.2 also reads `lane_data`.
2. Select or create the K2 Pro printer profile, then open its **physical printer / connection** settings.
3. **Host type:** `Moonraker (Klipper)`. **Hostname, IP or URL:** the external host, for example `k2host.local` or `192.168.1.50`.
4. Test the connection and save.

**OrcaSlicer 2.4.2: Sync cannot connect.** That release always sends a fixed access key, even with the field empty ([OrcaSlicer #13236](https://github.com/OrcaSlicer/OrcaSlicer/issues/13236)). Moonraker accepts a trusted LAN client without a key, but rejects a wrong one, so `moonraker.log` shows:

```text
401 GET /server/database/item?namespace=lane_data (<your PC>): Invalid API Key
```

Fix: open `http://<host>:7125/access/api_key` in a browser on the PC, copy the key from `"result"` (keep it private), paste it into the **API Key / Password** field of the OrcaSlicer connection, save and press Sync again.

## Sync the filaments

Press **Sync** (the arrows button at the top of the filament list in the Prepare tab). OrcaSlicer creates one filament per occupied CFS slot, grouped four by four like CFS units:

| CFS | OrcaSlicer |
| --- | --- |
| Box 1, slot 1 … slot 4 | filaments 1–4 (tools T0–T3) |
| Box 2, slot 1 … slot 4 | filaments 5–8 (tools T4–T7) |
| empty slot | empty placeholder |

Each synced filament gets the slot's **material** and **colour**. Slice as usual: T0 prints from Box 1 slot 1, T1 from slot 2, and so on, and the automatic mapping confirms the match when the print starts.

Sync again after changing spools: the printer updates `lane_data` within a few seconds of any slot change (RFID read, slot editor, Use in slot).

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
  "scan_time": ""
}
```

`lane` is the tool number (0-based physical slot). OrcaSlicer currently reads `lane`, `material`, `color`, `nozzle_temp` and `bed_temp`; `name`, `vendor`, `filament_id` and `spool_id` are there for brand-specific preset matching, which OrcaSlicer does not do yet for Moonraker printers ([#13006](https://github.com/OrcaSlicer/OrcaSlicer/issues/13006)).

Check what the printer publishes, with the same request OrcaSlicer makes:

```bash
curl -s "http://k2host.local:7125/server/database/item?namespace=lane_data"
```

## Limits

- OrcaSlicer picks a **generic preset per material** ("Generic PLA" for a PLA slot) with the slot colour, not the brand preset. Choose your own preset afterwards if you need its settings; the CFS mapping still works.
- The filament profiles have no bed temperature, so `bed_temp` is empty and OrcaSlicer keeps the preset's.
- The external spool is not part of the sync; map it in Mainsail's print dialog when needed.

## Turn it off

In `box.cfg`:

```ini
[box]
publish_lane_data: false
```

Restart Klipper. Existing lanes then stay in the Moonraker database until removed; delete the `lane_data` namespace from Mainsail's database settings if needed.
