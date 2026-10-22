# How it works

## The stock K2 Pro

On a stock K2 Pro the **T113** board runs Creality's Linux system: Klipper, Moonraker, the touch UI and the cloud apps. Klipper talks to the printer's microcontrollers over three UARTs:

| T113 UART | Device |
| --- | --- |
| `ttyS2` | Main MCU (bed, chamber, fans, Z, sensors) |
| `ttyS3` | Nozzle MCU (hotend, part fan, extruder motor through the nozzle board) |
| `ttyS5` | RS-485 bus: the CFS units and the closed-loop X/Y motor controllers |

## K2-OpenHost

K2-OpenHost keeps the same boards and firmware, but moves Klipper to an **external host**:

```text
K2 stock screen + touch
        |
Allwinner T113 (slot B: K2-OpenHost system)
  - HelixScreen on the stock screen
  - USB gadget: three Generic Serial functions
  - byte-transparent bridges:
      ttyGS0 <-> ttyS2  Main MCU
      ttyGS1 <-> ttyS3  Nozzle MCU
      ttyGS2 <-> ttyS5  RS-485 (CFS, X/Y motors)
        |
        | service Micro-USB, USB 2.0 High-Speed
        v
External Linux host (Raspberry Pi CM5)
  - Kalico (kalico-k2pro, k2-pro-openhost)
  - Moonraker, Mainsail K2-OpenHost, Crowsnest
  - /dev/k2-main, /dev/k2-nozzle, /dev/k2-rs485
  - direct USB: chamber camera, Cartographer3D (optional)
```

- **No MCU is reflashed** for the transport: the original Creality MCU firmware stays in place and talks at 230400 baud through the bridges.
- **The T113 is not a computer any more**, only a screen and a bridge. Its service port switches to USB device mode, which is why the cameras and the external USB port stop working through it: the chamber camera is rewired to the host, the nozzle camera is not used (see [limits](../DISCLAIMER.md#hardware-limitations-in-openhost-mode)).
- **Slot A is never written.** The K2-OpenHost system lives in the T113's spare slot B, built from Creality's own firmware. A power cycle during a trial boot returns to slot A, and you can go back at any time.

## What runs on the host

| Component | Role |
| --- | --- |
| **Kalico** `k2-pro-openhost` | Motion planning, heaters, the K2 extras: closed-loop motor control, PRTouch, `[z_align]`, the CFS stack (`box`), power-loss recovery, KAMP, link watchdog |
| **Moonraker** | API for Mainsail, OrcaSlicer, HelixScreen, Home Assistant, Mobileraker |
| **Mainsail K2-OpenHost** | Web UI with the CFS and motors panels |
| **Crowsnest** | Camera streams (cameras plugged into the host) |
| **Start gate** | `klipper.service` waits up to 60 s for the three gadget channels before Klipper starts |
| **Health check** | Runs the helper's doctor after every boot and apt upgrade, reports in the Klipper console |

## What runs on the T113 (slot B)

| Service | Role |
| --- | --- |
| `k2oh-gadget` | Creates the USB gadget with three serial functions |
| `k2oh-bridge` | One bridge process per bus, restarted within 1 s if it crashes |
| `k2oh-mcu` | At boot: power-cycles the MCU rail, runs Creality's `mcu_update`, then starts the bridges |
| `k2oh-ctl` | Control service for the host: telemetry, buzzer, MCU power rail, bridge restart, HelixScreen restart |
| HelixScreen | Touch UI on the stock screen, connected to Moonraker on the host |
| `k2oh-helix-filaments` | Shows the host's filament library in HelixScreen's pickers |
| `k2oh-mcu-fw` | Manual MCU, motor and CFS firmware updates with Creality's own tools |

Creality's Klipper, Moonraker, nginx, cloud apps, ADB and USB-stick OTA are disabled in slot B.

## The CFS on K2-OpenHost

The CFS is driven by Kalico's `box` module through the RS-485 channel. Kalico keeps a persistent inventory of the slots and a filament library, reads RFID tags (Creality, and Bambu/QIDI/MIFARE with the API7 CFS firmware), estimates the remaining filament, maps slicer tools to physical slots when a print starts and swaps to an identical spool when one runs out. Everything is published as `printer.objects.box`, which Mainsail, HelixScreen, OrcaSlicer and Home Assistant read. See [Using the CFS](../usage/cfs.md).

## Safety layers

- Heater outputs have a 3 s `max_duration`: if the host stops updating an MCU, the MCU switches its heaters off by itself.
- A lost Main or Nozzle link shuts Klipper down within about 5 s.
- The RS-485 bus has its own watchdog (`[serial_485]`): a lost CFS/motor link pauses the print.
- `[k2_t113]` can cut the MCU power rail on an emergency stop (`estop_on_shutdown: m112`).
- Updates, restarts and firmware flashing are refused while printing.

Details in [Serial link loss](../SERIAL_LINK_LOSS.md) and [Architecture](../ARCHITECTURE.md).
