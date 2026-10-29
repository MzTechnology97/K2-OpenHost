# HelixScreen (printer screen)

In slot B the printer's own touch screen runs **HelixScreen**, connected to Moonraker on the host. The T113 bootstrap installs it on the first boot of slot B, already pointed at the host.

K2-OpenHost uses its own fork, **[MzTechnology97/helixscreen](https://github.com/MzTechnology97/helixscreen)** (branch `k2-openhost`), based on prestonbrown's [HelixScreen](https://github.com/prestonbrown/helixscreen). Fork versions are the base version plus our build number: `1.0.6-k2oh.1` is the first build on 1.0.6.

## What works

- Printer status, temperatures, movement, files, print start/pause/cancel.
- The CFS: HelixScreen reads the `slots[]` shape Kalico publishes in `box` (Fork dialect, `api_version` 1) and sends the K2 commands (`BOX_MODIFY_TN`, `CR_BOX_*`, ...), which Kalico runs with its own change engine.
- The filament pickers show **only the host's filament library** (see below).

## What the fork changes

| | HelixScreen 1.0.6 | K2-OpenHost fork |
| --- | --- | --- |
| Colour after a spool is reinserted | Often grey, in OrcaSlicer too: HelixScreen wrote its own `lane_data` before the RFID read | The tag's: only Kalico writes `lane_data` |
| Tools T0–T3 on the slots | Always T*n* = slot *n* | During a print, the print's mapping (`print_mapping`); otherwise the CFS map (`box.map`). The active tool is the one routed through the loaded slot |
| Remaining filament | Not shown | Remaining metres and fill bar, from the CFS or Kalico's estimate (see [Remaining filament](../cfs-firmware/remaining.md)) |
| Moonraker wait at boot | `127.0.0.1:7125`, fixed again after every update | The Moonraker host in HelixScreen's settings |
| Camera server on the T113 (`ustreamer`) | Always installed | Skipped when the T113 has no `/dev/video0`: in OpenHost the cameras are on the host |
| In-app updates | From upstream's releases | Only from the fork's releases |

## K2-OpenHost interface

From `1.0.6-k2oh.5` the fork has its own interface for the K2, with the `k2-openhost` theme (Settings → Display). It shows when HelixScreen is connected to Kalico's CFS; with other printers HelixScreen's own interface stays.

- **Home**: the running job (preview, progress, time left and end, Pause/Tune/Stop) or, when idle, Print a file, the queue, reprint of the last job and preheat; temperatures, CFS, light (tap = on/off, drag = brightness) and fans. Home stays customisable as in HelixScreen.
- **CFS on Home**: the four spools with colour and remaining. While printing the spool in use reads **IN USE** and names the slot the runout swap goes to (`9% » 2`).
- **Print status**: progress ring with the preview, times, the spool in use with the swap order, temperatures, speed, flow and fan. **Exclude objects** shows the bed full width: tap the object to exclude.
- **CFS page**: the four spools, the filament path (slot, buffer, encoder, clog detection, head sensor, nozzle), the runout swap and the **external spool card** with the **Bypass** switch to turn bypass mode on or off. During a load or unload the header names the stage (`Loading 2 · to the head 3/5`).
- **Spool profile** (Edit → Change filament): the list opens on the slot's current profile. A profile from Kalico's library is assigned whole with `_BOX_SLOT_ASSIGN` (temperature, pressure advance, max flow, Orca id), the external spool included. Slots with a read RFID tag are not edited by hand.
- **Touch & Input** (Settings): sensitivity and debounce filter of the GT911 touch controller, with a test pad. It only changes with the printer idle; the first change saves the original configuration (Restore original).

Planned work is in the [fork roadmap](https://github.com/MzTechnology97/helixscreen/blob/k2-openhost/docs/k2-openhost/ROADMAP.md) (Italian).

## Installing or updating the fork

- **New install:** the helper downloads the fork's latest release (menu 24, answer **yes** to HelixScreen).
- **Slot B running upstream HelixScreen:** with the printer idle, download the release on the host, copy it to the printer and install it with `k2oh-setup helix-update`:

  ```sh
  # on the host
  curl -fLO https://github.com/MzTechnology97/helixscreen/releases/download/v1.0.6-k2oh.5/helixscreen-k2-v1.0.6-k2oh.5.tar.gz
  scp -O helixscreen-k2-v1.0.6-k2oh.5.tar.gz root@<printer-IP>:/mnt/UDISK/
  # on the printer (SSH)
  k2oh-setup helix-update /mnt/UDISK/helixscreen-k2-v1.0.6-k2oh.5.tar.gz
  ```

  `helix-update` refuses while the printer is printing or when the host does not answer. It saves HelixScreen (settings included) and its init scripts to `/mnt/UDISK/.k2openhost/helix-backup/<date>`, runs the release's installer, then puts back the wait on the host's Moonraker and turns the camera server off. HelixScreen restarts two or three times within a few seconds.
- **Later updates:** from HelixScreen's own update on the screen, which now reads only the fork's releases.
- **Going back:** `k2oh-setup helix-restore`, with the printer idle. It puts the last saved version back and moves the replaced one to `/mnt/UDISK/.k2openhost/trash/` (nothing is deleted).

## Filament list from the host

HelixScreen ships a catalog of about 360 presets. In slot B the service `k2oh-helix-filaments` replaces it with the library Mainsail and Kalico use: the CFS system filaments and your custom ones from `cfs_filaments.json`.

- **Host → screen**: every 30 s the service reads the library from Moonraker and, when it changed, rewrites HelixScreen's catalog. The original is kept as `filaments.json.helix-orig`. After a HelixScreen update the service picks up the new catalog and replaces it again.
- **Screen → host**: a filament created in HelixScreen is sent to Kalico (`_BOX_FILAMENT_SET ID=HXnnnn …`) while the printer is idle.
- **During a print** the service only reads.

Settings in `/mnt/UDISK/.k2openhost/k2openhost.conf` on the printer: `HELIX_FILAMENTS=off` turns the service off; `RESTART_HELIX=never` disables HelixScreen's restart after a library change.

Back to HelixScreen's own presets:

```sh
/etc/init.d/k2oh-helix-filaments stop
/etc/init.d/k2oh-helix-filaments disable
k2oh-helix-filaments --restore
```

Log: `logread -e k2oh-helix`.

## Useful commands

| Where | Command | What it does |
| --- | --- | --- |
| Klipper console | `SCREEN_RESTART` | Restarts HelixScreen (needs `[k2_t113]` linked) |
| Helper | `./helper.sh t113 host <IP>` (menu 29) | Points HelixScreen at another host address |
| Printer SSH | `k2oh-setup --host <IP>` | Same, on the printer |
| Printer SSH | `k2oh-setup status` | First-boot setup state |
| Printer SSH | `k2oh-setup helix-update <archive>` | Installs another HelixScreen release, printer idle only, with a backup |
| Printer SSH | `k2oh-setup helix-restore` | Puts the last saved version back |

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| The screen stays on the boot logo | `k2oh-setup status`, `cat /mnt/UDISK/.k2openhost/setup.log`, then `k2oh-setup` again. |
| HelixScreen cannot reach Moonraker | Wrong host IP (menu 29), or the printer cannot reach the host on port 7125. |
| A new filament does not appear | Wait 30 s; the service syncs while the printer is idle. `logread -e k2oh-helix`. |
| A reinserted spool stays grey, in OrcaSlicer too | Upstream HelixScreen: install the fork. To fix the slot now, `_BOX_RFID_READ_SLOT SLOT=<n>` from the console. |
| The tools on the slots do not follow the mapping | Upstream HelixScreen: install the fork. |
| `helix-update` answers `printer state is printing` | Wait for the print to end. With `unreachable` the printer cannot reach Moonraker on the host. |
| Something is wrong after an update | `k2oh-setup helix-restore`, and report it on the [fork](https://github.com/MzTechnology97/helixscreen/issues). |
