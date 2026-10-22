# Third-party RFID tags

Stock CFS firmware reads only Creality RFID tags. With an **API7** firmware the CFS lets Kalico identify **Bambu Lab** and other **MIFARE Classic 1K** spools (QIDI, OpenTag-style tags) **without ever writing the tag**.

## Which firmware has API7

API7 (stock-task capture, caps `0xE8`) was validated with v3.3 and is carried by v3.12. v3.22 keeps the v3.12 API7 capture, and the CFG4/CFG5T/CFG6 images are built from the v3.22 builder. Check your CFS:

```text
BOX_RFID_DIAG_INFO
```

Expected: `API=7`, `readers=2`, `slots/reader=2`, `caps=0xE8`. On a firmware without API7 the automatic fallback turns itself off until the next Klipper start: nothing breaks.

## How a read works

1. The CFS does its normal Creality read. **A Creality tag always wins.**
2. Only if the record is empty or unknown, Kalico looks at the UID, ATQA and SAK the CFS already captured (no extra RF). A slot with no tag, or a tag that is not MIFARE Classic 1K, stops here.
3. The vendor decoders run by priority (**Bambu**, then **MIFARE**/QIDI). Each try is a full stock CFS reread (about 45 s, RS-485 bus busy meanwhile).
4. The decoded material and colour select a filament profile from the library; the UID is cached, so the next insertion of that spool needs no reread.

Never during a print, a pause, another box operation, or with filament loaded toward the printhead.

## Enable it

The extras need API7, so the generic `printer.cfg` keeps their includes commented. On an API7 CFS uncomment:

```ini
[include macros/box_rfid_diag.cfg]
[include macros/box_rfid_bambu.cfg]
[include macros/box_rfid_mifare.cfg]
```

and in `[box]` (both default to `True`):

```ini
[box]
auto_bambu_rfid_fallback: True
auto_mifare_rfid_fallback: True
rfid_fallback_budget: 1          # rereads per spool insertion (0 = cache only)
rfid_fallback_manual_budget: 3   # rereads per slot on a manual reread
```

`allow_active_rf: false` in `[box_rfid_diag]` is intentional: the normal path uses Creality's own RFID task, not the old direct RF commands.

## Validated spools

Bambu Lab tags read on hardware: PLA Matte, PETG HF, PETG Basic, ABS, ASA, ASA-CF, PAHT-CF, ABS-GF, PETG-CF, PC. QIDI: PET-CF.

## Bind a tag to your own profile

```text
_BOX_RFID_ASSOCIATE SLOT=<global-slot> FILAMENT_ID=<library-id>
```

Future reads of that tag type (for example `BAMBU:PETG HF`) use your profile's temperatures, pressure advance and max flow, keeping the colour from the tag.

## Remaining filament

The stock CFS returns `0xFF` (no value) for third-party tags, so their percentage comes from the [Kalico estimate](remaining.md), or from the CFS itself on CFG5T/CFG6 with type-4 live accounting.

## Commands

| Command | Use |
| --- | --- |
| `_BOX_RFID_READ_SLOT SLOT=<n>` | Reread a slot (goes straight to the known decoder when the UID is cached) |
| `BOX_RFID_BAMBU_READ SLOT=<n>` | Force a Bambu read, with a detailed log line |
| `BOX_RFID_MIFARE_READ SLOT=<n>` | Force a generic MIFARE read |
| `_BOX_RFID_FALLBACK_CACHE [CLEAR=1] [UID=<hex>]` | Show or clear the UID cache |
| `BOX_RFID_DIAG_INFO`, `_RUNTIME`, `_STATE` | Passive diagnostics |

Full details: [CFS_RFID_BAMBU.md](https://github.com/MzTechnology97/kalico-k2pro/blob/k2-pro-openhost/docs/CFS_RFID_BAMBU.md).
