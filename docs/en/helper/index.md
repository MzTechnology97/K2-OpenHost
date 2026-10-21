# K2-OpenHost Helper

The **[K2-OpenHost Installer Helper](https://github.com/MzTechnology97/k2-openhost-installer-helper)** (`helper.sh`) turns an external Linux computer into a ready K2-OpenHost host and, from the same menu, prepares the printer's T113 board. It installs, updates, checks, backs up and flashes. Its menu is styled after the Creality Helper Script for the K2 series.

![Helper menu](../../images/helper/cli-menu.png)

## Start it

```bash
~/k2-openhost-installer-helper/helper.sh
```

Run it as your normal user (not root); it asks for `sudo` when needed. Installed entries show `[installed]`. If a step fails, the menu shows the error and stays open.

## Use it from the command line

Every menu entry is also a command, for scripts and remote sessions:

![Command line help](../../images/helper/cli-help.png)

| Command | Menu | What it does |
| --- | --- | --- |
| `install full` | 1 | Core install plus Moonraker timelapse and Shake&Tune |
| `install core` | 2 | Host preparation, Kalico, K2 Pro configuration, Moonraker, Mainsail |
| `install <part>` | 3–15, 36 | `system`, `kalico`, `config`, `moonraker`, `mainsail`, `cartographer`, `shaketune`, `timelapse`, `crowsnest`, `creality-cam`, `host-fan`, `hostmcu`, `spoolman`, `mobileraker`, `octoeverywhere` |
| `update` | 17 | Kalico, Moonraker and Mainsail |
| `doctor` | 16 | Read-only health check |
| `health` | — | Doctor with the report in the Klipper console |
| `config diff` | 18 | Your configuration against the K2 profile |
| `config serial-names` | 19 | Stable `/dev/k2-*` serial names in `printer.cfg` |
| `backup` / `restore` | 20 / 21 | Configuration backups in `~/k2-openhost-backups` |
| `t113 <command>` | 23–33 | `check`, `install`, `status`, `boot-b`, `commit`, `boot-a`, `host [IP]`, `mcu-fw <args>`, `link`, `update [--revert]`, `timezone` |
| `release status` / `release apply [--t113]` | 34 / 35 | Compare with and apply the validated release |
| `experimental-cfs` | 40 | Experimental CFS firmware menu |

Options:

- `--yes` answers yes to every question (unattended install). It **never** bypasses the experimental CFS firmware acknowledgement.
- Environment overrides: `KALICO_BRANCH`, `PRINTER_DATA`, `KLIPPER_DIR`, `KLIPPY_ENV`, `MAINSAIL_DIR`, `MAINSAIL_GH_REPO`, `K2OH_RELEASE_MANIFEST`, `K2OH_NO_UPDATE_CHECK=1`. Example: `KALICO_BRANCH=my-branch ./helper.sh install kalico`.

## Safety rules of the helper

- Nothing is deleted: existing folders are renamed (`<folder>.before-k2openhost-<date>`), files are backed up before changes, your configuration is never overwritten silently.
- Updates, Klipper restarts, restores and firmware flashing are refused while a print is running or paused.
- MCU firmware is flashed only after an explicit confirmation, with Creality's own tools, and only after Klipper on the host is stopped.

## More

- [Menu reference](menu.md): every entry explained.
- [Doctor and health check](doctor.md): what is checked and how to read it.
- [Installation](../installation/index.md): the helper in the install sequence.
