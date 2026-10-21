# Installation

The whole install is driven from the host by the **[K2-OpenHost Helper](../helper/index.md)**. It sets up the host and, over SSH, the printer's T113 board. Follow the steps in order.

!!! tip "Before you start"
    - Read [Requirements](../getting-started/requirements.md) and the [disclaimer](../DISCLAIMER.md).
    - Note the printer's IP address (screen: network settings) and enable root SSH on the printer.
    - Use a spare SD card or eMMC image for the host, so your current setup stays intact.

| Step | What you do | Page |
| --- | --- | --- |
| 1 | Write Raspberry Pi OS, run the helper's **Full install**, reboot | [Prepare the host](host.md) |
| 2 | Connect the cable; menu **23** check, **24** install the T113 bootstrap, **26** trial boot, **27** keep slot B, **32** link the T113 controls | [Prepare the printer](printer.md) |
| 3 | `doctor`, Mainsail, homing, heaters, motor and cutter calibration, CFS, first supervised print | [First start and checks](first-start.md) |

Later:

- [Updates and releases](updates.md): Mainsail's update manager, `helper.sh update`, releases, T113 programs, Creality board firmware.
- [Backup and restore](backup.md): the helper's local backups and a GitHub backup of the configuration.
- [Back to stock](uninstall.md): slot A, at any time.

## Quick start (experienced users)

```bash
sudo apt update && sudo apt install -y git
git clone https://github.com/MzTechnology97/k2-openhost-installer-helper.git ~/k2-openhost-installer-helper
~/k2-openhost-installer-helper/helper.sh
```

Choose **1) Full install**, reboot, connect the K2, run menu **23**, **24**, **26**, then **27** and **32**, then:

```bash
~/k2-openhost-installer-helper/helper.sh doctor
```

Open `http://<host-name-or-ip>/`.
