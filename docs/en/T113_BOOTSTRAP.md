# T113 bootstrap (slot B)

Updated: **2026-10-04**. [Italiano](../it/T113_BOOTSTRAP.md)

Status: **built and tested offline; not yet booted on a printer.** Read the [disclaimer](DISCLAIMER.md) first.

> [!IMPORTANT]
> This work was prepared and tested on the K2 Pro stock firmware **1.1.0.94**, the version on the reference printer. Newer Creality releases are accepted with a warning, but **on firmware other than 1.1.0.94 the correct operation of the bootstrap and of the T113 USB gadget (OTG) mode is not guaranteed.** The slot B build refuses a release whose boot scripts it changes differ from the reviewed ones; they are identical in 1.1.7.0.

The T113 bootstrap prepares the K2 Pro's own T113 board for K2-OpenHost. It is developed in its own repository, **[k2-openhost-t113-bootstrap](https://github.com/MzTechnology97/k2-openhost-t113-bootstrap)**, which holds the complete step-by-step guide. It is installed from the external host with the [K2-OpenHost Installer Helper](https://github.com/MzTechnology97/k2-openhost-installer-helper): menu 23 or `./helper.sh t113 install` clones the bootstrap repository and runs everything over SSH.

## Design

| Decision | Why |
| --- | --- |
| Uses the T113's **slot B** and never writes **slot A** | Slot A, the printer's current system, stays a fallback. The switch uses the same two U-Boot variables as Creality's OTA. |
| Slot B is a **stock Creality system** (by default slot A's release, or a newer one) with minimal changes, built on the host from the OTA downloaded from Creality's CDN | The stock kernel already has the USB gadget drivers validated on the reference printer ([USB gadget transport](USB_GADGET.md)). No Creality file is redistributed. |
| Writable layer on UDISK (`/mnt/UDISK/.k2openhost/overlay`) | `rootfs_data` belongs to slot A. Slot B never mounts, checks or formats it, and never formats, checks or wipes UDISK. |
| **Trial boot** | The first thing slot B's boot does is point the next boot back at slot A. A power cycle recovers from any failure; `k2oh-slot commit` keeps slot B. |
| Strict model check | The host installer, the printer-side installer and the firmware tool all require a K2 Pro: Creality model `F012`, board `CR0CN200400C10`. |

## What slot B runs

- **USB gadget:** three Generic Serial functions (`0525:a4a6`).
- **Bridges:** one bridge per bus (`ttyGS0↔ttyS2` Main MCU, `ttyGS1↔ttyS3` Nozzle MCU, `ttyGS2↔ttyS5` RS-485/CFS/motors), 230400 8N1. It is the bridge validated on the reference printer, restarted by procd.
- **Stock `mcu_update`:** starts the Main and Nozzle MCU applications at every boot.
- **Wi-Fi:** works without Creality's `wifi-server`, using the networks copied from slot A.
- **HelixScreen:** installed at the first boot and pointed at the external host's Moonraker.
- **`k2oh-mcu-fw`:** manual MCU, motor and CFS firmware updates (below).

Disabled:
- Creality Klipper, klipper_mcu, Moonraker and nginx;
- the UI/cloud apps;
- ADB (it would take the USB controller);
- the WebRTC camera;
- USB-stick OTA (an OTA from slot B would overwrite slot A);
- the factory reset (`wipe_data`);
- the chamber-camera restart (on the K2 Pro it switches USB0 back to host mode).

## Peripheral firmware updates

Updates are manual on purpose and use **Creality's own tools** (`mcu_util`, `mcu_util_485`, `/etc/init.d/mcu_update`): the same sequence as a stock OTA, with the MCU power rail cycled through `mcu_reset.sh` (GPIO140 `MCU_PWR_EN`, see [T113 service GPIOs](T113_GPIO.md)). Steps:

The short way is `k2oh-mcu-fw update` (installer menu 30). It downloads the **latest** Creality release, stages it, shows the changes and flashes only if you confirm. Step by step:

1. `k2oh-mcu-fw list` reads Creality's public firmware index.
2. `k2oh-mcu-fw download` fetches a release from Creality's CDN, checks its rootfs against the image's own MD5 list and keeps only `fw/F012` and `fw/cfs`.
3. `k2oh-mcu-fw stage` puts them in slot B.
4. `k2oh-mcu-fw apply` flashes them, only while the host Klipper is stopped.

**CFS:** `apply --cfs` adds a second pass through `/tmp/cfs_update.json`. Its format was recovered from `mcu_util_485`:

```json
{"CFSs": [{"uuid": "<12-byte UniID, lowercase hex, space separated>", "fw": "<file>"}]}
```

- The UniID and the exact loader identity (`cfs0_050_G32-…`) come from Creality's own updater output (`/tmp/.485_mcu_version`) after the first pass.
- The file is picked by the exact hardware token. G30 and G32 differ from 1.1.7.0 on (150 and 153).

[K2-OpenHost Firmware Tools](https://github.com/MzTechnology97/k2-openhost-firmware-tools) documents the protocols. Its read-only probes are the independent check.

**Why Creality's tools rather than Jacob10383's `motor_updater.py`:**
- they are the tools validated for this hardware and already present in slot B at slot A's version;
- they match the K2 Pro topology: two RS-485 motors plus the extruder through the nozzle board, and belt and RFID boards;
- they handle the CFS the way Creality's OTA does.

`motor_updater.py` targets K2/K2 Plus layouts and Jacob's own kernel. It stays a good reference.

Slot A flashes its own release's files back at its next boot (the stock script reflashes on any version difference).

## Status

| Item | State |
| --- | --- |
| Slot B build (file-by-file vs stock), stock OTA download/MD5, scripts on the printer's own BusyBox/Python 3.9 | verified offline on 1.1.0.94 |
| Newer release 1.1.7.0 | same boot scripts, services and gadget-capable kernel; slot B builds with the "not tested" warning; not booted |
| Bridge with pseudo-terminals, firmware extraction vs `unsquashfs`, release download 1.1.7.0, CFS planning, HelixScreen install (chroot) | verified offline |
| Writing slot B, trial boot, gadget/bridges on slot B, HelixScreen on the panel, `k2oh-mcu-fw apply` | **pending hardware validation** |

A control plane for the other T113 service GPIOs ([T113 service GPIOs](T113_GPIO.md)) can live in slot B later. It is not part of this release.
