# FAQ

## General

??? question "Does K2-OpenHost work on the K2 Plus or the K2 base model?"
    No. It is built and tested for the **Creality K2 Pro** only, and the tools check the model (`F012`) and board before changing anything.

??? question "Do I lose the stock firmware?"
    No. K2-OpenHost runs from the T113's **slot B**; Creality's system stays untouched in **slot A**. `./helper.sh t113 boot-a` boots it again. See [Back to stock](../installation/uninstall.md).

??? question "Is it stable enough for daily use?"
    Yes: the reference K2 Pro runs it every day on a print farm, with no crashes caused by the host or K2-OpenHost. The [modified CFS firmware](../cfs-firmware/index.md) and the OrcaSlicer 2.5 plugin are the parts still marked experimental.

??? question "Why not just run Klipper on the T113?"
    The T113 is a dual-core Cortex-A7 at 1.2 GHz with about 512 MB of RAM, shared on stock with Moonraker, the web server, the UI, Creality's cloud apps and the camera. An external host has many times the CPU and RAM, runs current Kalico and Mainsail, and leaves the T113 only the bridges and the screen. See [Why an external host](../index.md#why-an-external-host).

??? question "Does the printer still talk to Creality Cloud?"
    No. In slot B Creality's cloud and UI apps are not started. The printer talks to your host on your network.

## Hardware

??? question "Which host should I buy?"
    A Raspberry Pi CM5 on a carrier with USB 3.0 ports (the reference uses a Waveshare CM5-IO-BASE-A), or a Pi 5. A Pi 4 works. Any 64-bit Debian/Ubuntu computer works too. See [Requirements](../getting-started/requirements.md).

??? question "Which cable do I need?"
    A **data** Micro-USB to USB-A cable, ideally with a **90° plug**, from the host to the T113 service port. Charge-only cables do not work.

??? question "What about the cameras and the USB stick port?"
    The **chamber camera** is disconnected from the T113 and rewired to the host. The **nozzle camera cannot be used** in OpenHost mode. The printer's USB port stops working: upload files through Mainsail.

??? question "Can I use Cartographer3D?"
    Yes, connected directly to the host. See [Cartographer3D](../CARTOGRAPHER.md).

??? question "What happens if the host crashes or loses power during a print?"
    The print stops: the MCUs shut down and switch the heaters off by themselves. Use the host's official power supply; a UPS for host and printer is a good idea.

## CFS

??? question "Do I need the modified CFS firmware?"
    No. The stock CFS firmware is fully supported: loading, RFID of Creality spools, mapping, runout swap, remaining estimate. The modified firmware adds tunable parameters, live remaining on the CFS and third-party RFID.

??? question "Are RFID tags ever written?"
    No. Neither Kalico nor the CFS firmware writes tags. The remaining filament is kept on the host (or computed live in the CFS RAM with CFG5T/CFG6).

??? question "Can I use Bambu Lab spools with their tags?"
    Yes, with an API7 CFS firmware and the `box_rfid_bambu` include. See [Third-party RFID](../cfs-firmware/third-party-rfid.md).

??? question "How many CFS units?"
    Up to four (16 slots) plus the external spool. Set `box_count` in `overrides.cfg`.

## Slicer and apps

??? question "Which slicer?"
    OrcaSlicer, with the K2 Pro printer profile pointing at the host's Moonraker. Sync reads the CFS filaments; the OrcaSlicer 2.5 plugin adds a CFS panel and maps slots before sending. See [OrcaSlicer](../ORCASLICER.md).

??? question "Can I still use Creality Print?"
    Creality Print expects Creality's own services on the printer, which do not run in slot B. Use OrcaSlicer with Moonraker.

??? question "Does Home Assistant work?"
    Yes, with the [K2-OpenHost CFS integration](../usage/home-assistant.md) and any Moonraker integration.

## Updates

??? question "How do I update?"
    Mainsail → Machine → Update Manager for Kalico, Moonraker, Mainsail and the helper, or `./helper.sh update`. `./helper.sh release status` / `release apply` bring everything to a tested combination. See [Updates](../installation/updates.md).

??? question "Can I install a Creality OTA?"
    Not from slot B: an OTA there would overwrite slot A, so it is disabled. From slot A (`./helper.sh t113 boot-a`) a Creality OTA writes the inactive slot, which is K2-OpenHost's slot B: K2-OpenHost is replaced and must be installed again with the helper. You rarely need an OTA: the Main, Nozzle, motor and CFS firmware are updated from slot B with `k2oh-mcu-fw` (helper menu 31).
