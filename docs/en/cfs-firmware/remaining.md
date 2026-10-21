# Live remaining filament

Every spool in the CFS shows a **remaining percentage**. K2-OpenHost has two sources for it and picks the best one per slot.

| Source | Where it is computed | Available on |
| --- | --- | --- |
| **CFS** (`cfs`) | In the CFS: the odometer measures the filament actually drawn and the stock "type-4" accounting turns it into a percentage, live during the print | **CFG5T v3.24** and **CFG6 v3.25** |
| **Kalico** (`kalico`) | On the host: nominal spool length, minus the filament measured by the CFS path encoder (or `print_stats` when the encoder is not available), saved by tag UID | Any CFS firmware |

The Kalico estimate is always running: it is the **fallback** when the CFS gives no live value.

## Why type-4

The stock CFS 1.5.3 firmware has a RAM-only remaining path (`runtime_type = 4`) that updates the remaining byte from the physical path encoder and never writes back to the tag. Stock enables it only together with Creality's secure RFID chip. CFG5T and CFG6 open that gate for the other spools, without writing anything to the tag:

```text
consumed_percent = floor(used_mm * 100 / total_mm)
remaining        = max(initial_percent - consumed_percent, 0)
```

The CFS captures the encoder baseline when the spool is loaded and closes the interval on unload.

## How Kalico merges the two

```mermaid
flowchart TD
    V["CFS reports a remaining %"] --> Q{"Valid 0-100?"}
    Q -- "No (255, e.g. after a CFS restart)" --> K["Keep the Kalico estimate<br/>source = kalico"]
    Q -- Yes --> L{"Live firmware<br/>(CFG5T/CFG6) and<br/>cfs_live_remaining: True?"}
    L -- Yes --> C["The CFS leads: on every change<br/>the estimate restarts from its value;<br/>between 1 % steps the local<br/>consumption keeps lowering it<br/>source = cfs"]
    L -- No --> M["The CFS value can only lower<br/>the local estimate (min)<br/>source = kalico"]
```

- With live firmware the CFS value wins **up or down**, so a correction made by the CFS is followed.
- The last CFS value (`cfs_percent`) is saved with the estimate, so a Klipper restart does not re-anchor the spool needlessly.
- With other firmware the CFS value is only the one measured at load: it can lower the estimate, never raise it.

## Configuration

```ini
[box]
cfs_live_remaining: True   # default; False = always use the Kalico estimate
```

The live source is used only when `[box_cfs_runtime]` has identified the CFS as `v323-cfg5t` (`0xE5`) or `v323-cfg6` (`0xE3`). `auto_apply` does **not** need to be on: identification is read-only.

## Check which source a slot uses

In the box status of each slot (Mainsail CFS panel, Moonraker `box` object):

| Field | Meaning |
| --- | --- |
| `rfid_percent` | Percentage shown |
| `rfid_remaining_source` | `cfs` or `kalico` |
| `rfid_usage_source` | Kalico consumption: `cfs_encoder` or `print_stats` |
| `rfid_total_m`, `rfid_remaining_m` | Nominal and remaining length |

And per CFS unit in `box_cfs_runtime`: `live_remaining: true` when the firmware keeps the value live.

In the console:

```text
_BOX_RFID_REMAINING_DIAG SLOT=<global-slot>
```

prints the raw remaining value the CFS returns for that slot.

## Nominal length

Kalico needs the spool length in metres. In order of preference:

1. the length read from the tag (when a decoder reads it);
2. the **Nominal length** of the filament profile (Mainsail filament editor);
3. the reference length of the material for a 1 kg, 1.75 mm spool (PLA 335 m, PETG 327 m, ABS 400 m, ASA 390 m, …).

For one spool that differs (part-used, 3 kg):

```text
_BOX_RFID_SPOOL_NEW SLOT=<global-slot> TOTAL_M=<metres> REMAINING=<0..100>
```

!!! note "Status"
    The CFS SET/GET contract and the identity are verified on hardware. The type-4 values during a **real long print** are still being validated: keep `cfs_live_remaining: True` and compare `cfs` with what the spool actually holds. If something looks wrong, `cfs_live_remaining: False` goes back to the Kalico estimate.
