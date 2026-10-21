# HelixScreen (printer screen)

In slot B the printer's own touch screen runs **[HelixScreen](https://github.com/prestonbrown/helixscreen)**, connected to Moonraker on the host. The T113 bootstrap installs it on the first boot of slot B, already pointed at the host.

## What works

- Printer status, temperatures, movement, files, print start/pause/cancel.
- The CFS: HelixScreen reads the stock K2 `box` shape that K2-OpenHost publishes next to its own, and sends the stock K2 commands (`BOX_MODIFY_TN`, `CR_BOX_*`, ...), which K2-OpenHost accepts and runs with its own change engine.
- The filament pickers show **only the host's filament library** (see below).

## Filament list from the host

HelixScreen ships a catalog of about 360 presets. In slot B the service `k2oh-helix-filaments` replaces it with the library Mainsail and Kalico use: the CFS system filaments and your custom ones from `cfs_filaments.json`.

- **Host → screen**: every 30 s the service reads the library from Moonraker and, when it changed, rewrites HelixScreen's catalog. The original is kept as `filaments.json.helix-orig`.
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

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| The screen stays on the boot logo | `k2oh-setup status`, `cat /mnt/UDISK/.k2openhost/setup.log`, then `k2oh-setup` again. |
| HelixScreen cannot reach Moonraker | Wrong host IP (menu 29), or the printer cannot reach the host on port 7125. |
| A new filament does not appear | Wait 30 s; the service syncs while the printer is idle. `logread -e k2oh-helix`. |
