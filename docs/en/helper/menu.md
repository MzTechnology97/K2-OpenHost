# Menu reference

## Host install

| # | Entry | What it does |
| --- | --- | --- |
| 1 | **Full install** | Core install plus Moonraker timelapse and Shake&Tune. Recommended for a new host. |
| 2 | Core install | Host preparation, Kalico, K2 Pro configuration, Moonraker and Mainsail, then starts Klipper. |
| 3 | Host preparation | Packages, serial groups, udev names `/dev/k2-*`, ModemManager and brltty, the automatic health check. Safe to run again. |
| 4 | Kalico K2-OpenHost | Installs or updates `~/klipper` (`kalico-k2pro`, `k2-pro-openhost`), `~/klippy-env`, `klipper.service` and the start gate. |
| 5 | K2 Pro configuration | Copies the profile files you do not have yet; for changed files it saves the profile version as `<file>.k2oh-new`. |
| 6 | Moonraker | Installs Moonraker and adds the missing `moonraker.conf` sections. |
| 7 | Mainsail K2-OpenHost | Installs or updates the web interface and the nginx site, including the rule that lets OrcaSlicer 2.4.2's placeholder API key through. |

## Optional components

| # | Entry | What it does |
| --- | --- | --- |
| 8 | Cartographer3D | The official plugin (pip package plus loader), connected by direct USB. PRTouch stays the validated probe. See [Cartographer3D](../CARTOGRAPHER.md). |
| 9 | Shake&Tune | Klippain Shake&Tune resonance tools. |
| 10 | Timelapse | Moonraker timelapse (the K2 profile ships its macros). |
| 11 | Crowsnest | Webcam streaming. With the K2 Plus 1080p Creality CAM connected it also sets `max_fps: 25` and the camera controls (`install creality-cam` does only that step). See [Camera](../CAMERA.md). |
| 12 | Host MCU | `[mcu rpi]`: GPIO, accelerometer and temperature of the host board. |
| 13 | Spoolman | Connection to an existing Spoolman server. |
| 14 | Mobileraker | Mobileraker companion (phone notifications). |
| 15 | OctoEverywhere | Remote access. |
| 36 | Host fan from Klipper | The CM5 CPU fan driven by `[host_fan]`: udev rule, `klipper.service` drop-in, `macros/host_fan.cfg`. See [Host and CPU fan](../HOST.md#cpu-fan). |

## Maintenance

| # | Entry | What it does |
| --- | --- | --- |
| 16 | Doctor | Read-only health check. See [Doctor](doctor.md). |
| 17 | Update | Updates Kalico, Moonraker and Mainsail. Refused while printing. |
| 18 | Compare config | Differences between your configuration and the K2 profile. |
| 19 | Serial names | Switches `printer.cfg` and the start gate to the `/dev/k2-*` names, independent of USB enumeration order. |
| 20 / 21 | Backup / Restore | Configuration, CFS filament library, CFS state and Moonraker database. See [Backup](../installation/backup.md). |
| 22 | Restart | Restarts Klipper and Moonraker. Refused while printing. |

## Printer (T113)

| # | Entry | What it does |
| --- | --- | --- |
| 23 | Check the printer | Read-only: model, running slot, free space, slot A's firmware, the Creality release slot B would use. |
| 24 | Install the T113 bootstrap | Builds slot B from Creality's OTA, adds HelixScreen, writes slot B (slot A untouched), offers the trial boot. |
| 25 | T113 status | Running slot, next boot, trial flag, first-boot setup, HelixScreen. |
| 26 | Trial boot slot B | Boots slot B once; a power cycle returns to slot A. |
| 27 | Keep slot B | Makes slot B the default. |
| 28 | Boot slot A | Back to the printer's original system. |
| 29 | Change the host address | Updates the host used by HelixScreen and `k2oh-mcu-fw`. |
| 30 | MCU firmware status | Board versions and the firmware files slot B would flash. |
| 31 | Update MCU firmware | Latest Creality release: download, stage, show the changes, flash only on confirmation. |
| 32 | Link the T113 controls | Token, `[k2_t113]` host, Moonraker power device `K2_MCU_Power`. |
| 33 | Update the T113 programs | Updates K2-OpenHost's programs on the running slot B without reinstalling; `--revert` goes back. |

## Releases

| # | Entry | What it does |
| --- | --- | --- |
| 34 | Release status | Each component against the latest validated release. Read-only. |
| 35 | Apply the release | Fast-forwards Kalico and installs the release's Mainsail build. Nothing is downgraded. |

## Experimental

| # | Entry | What it does |
| --- | --- | --- |
| 40 | Experimental CFS firmware | Lists the manifest-approved CFS images present in `firmware/custom-cfs/`, verifies SHA-256 and the hardware/application target, shows the risks, and flashes only after you type `FLASH EXPERIMENTAL CFS`. See [Flash and roll back](../cfs-firmware/flash.md). |
