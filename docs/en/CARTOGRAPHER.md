# Cartographer3D on K2-OpenHost

Updated: **2026-10-04**. [Italiano](../it/CARTOGRAPHER.md)

K2-OpenHost uses the **official** [Cartographer3D plugin](https://github.com/Cartographer3D/cartographer3d-plugin), the same one Jacob10383's K2 firmware uses. The official plugin supports Kalico and the K2 directly: Kalico environment detection and adapters, non-critical MCU reconnection, the latest Kalico homing API and `register_as_probe`.

The former `cartographer3d-plugin-k2openhost` fork (official base of March 2026 plus Jacob's earlier K2 port, made for k2-improvements) was retired and archived (read-only) on 2026-10-04.

> Cartographer on direct USB is **not hardware-validated yet** on K2-OpenHost (test T5 of the [hardware test plan](HARDWARE_TEST_PLAN.md)). The validated probe is the stock **PRTouch**. Read the [disclaimer](DISCLAIMER.md) first.

## Topology

The three T113 USB gadget channels stay dedicated to the K2 buses. Cartographer connects **directly to a USB port of the external host**:

```text
T113 ttyS2 -> ttyGS0 -> host /dev/ttyUSB0  (Main MCU)
T113 ttyS3 -> ttyGS1 -> host /dev/ttyUSB1  (Nozzle MCU)
T113 ttyS5 -> ttyGS2 -> host /dev/ttyUSB2  (RS-485 / CFS / closed loop)
Cartographer USB ----------------------> host USB  (/dev/k2-cartographer)
```

Cartographer is a Klipper MCU that streams continuously and re-enumerates when it resets. An earlier experiment carried it through the T113 with a PTY multiplexer on the third gadget channel: data arrived, but resets and a duplicate GS2 bridge made it fragile. Direct USB avoids that layer and keeps GS2 for RS-485 only.

## Install

- **K2-OpenHost Installer Helper:** menu **8) Cartographer3D**, or `./helper.sh install cartographer`. It runs the official install script (pip package in `~/klippy-env` and a one-line loader in `~/klipper/klippy/plugins/cartographer.py`, which Git ignores), adds the Moonraker updater and migrates a host that still has the former fork.
- **By hand:** clone the official repository and run `scripts/install.sh -k ~/klipper -e ~/klippy-env`.

Moonraker updates it as a Python package:

```ini
[update_manager cartographer]
type: python
channel: stable
virtualenv: ~/klippy-env
project_name: cartographer3d-plugin
is_system_service: False
managed_services: klipper
info_tags:
    desc=Cartographer3D Plugin
```

`./helper.sh doctor` checks that the official plugin is installed and that exactly one loader exists (Kalico refuses to start when a loader is both in `klippy/extras` and `klippy/plugins`).

## Configure

The K2 Pro profile ships `cartographer.cfg`, not included by default. The installer's udev rule names the device `/dev/k2-cartographer`; `/dev/serial/by-id/...` works too. Never copy a serial identifier from another printer.

```ini
[mcu cartographer]
serial: /dev/k2-cartographer
restart_method: command
is_non_critical: True
reconnect_interval: 2.0

[cartographer]
mcu: cartographer
x_offset: 0
y_offset: -15            # measure on your printer
register_as_probe: true  # or false for mixed mode, see below
```

Enable it with `[include cartographer.cfg]` in `printer.cfg` only for the validation session.

## Probe roles

| `register_as_probe` | Cartographer | PRTouch |
| --- | --- | --- |
| `true` | owns `probe`, `probe:z_virtual_endstop`, `PROBE`, `PROBE_ACCURACY`, `QUERY_PROBE`, `Z_OFFSET_APPLY_PROBE` | must not register a `probe` object |
| `false` (mixed mode) | keeps its own commands and bed mesh; its endstop is `cartographer_probe:z_virtual_endstop` | keeps `probe` and `probe:z_virtual_endstop` for Z homing and the nozzle reference |

In mixed mode `[stepper_z]` keeps the PRTouch endstop; do not point it at `cartographer_probe:z_virtual_endstop` unless Z should home with Cartographer. A typical mixed workflow: home X/Y, take Z with PRTouch, move to scan height, run the Cartographer mesh. Change print-start macros only after both probes are validated separately.

## Validation sequence (T5)

1. Keep the validated PRTouch-only configuration as the rollback baseline.
2. Confirm `/dev/ttyUSB0..2` stay stable, then connect Cartographer to the host.
3. Check the device (`lsusb`, `ls -l /dev/k2-cartographer /dev/serial/by-id/`).
4. Include `cartographer.cfg`, restart Klipper and confirm Cartographer identifies without reconnect loops:

   ```bash
   grep -Ei 'cartographer|identify_response|Timeout on connect|Unable to connect' ~/printer_data/logs/klippy.log | tail -50
   ```

5. Non-motion checks: `CARTOGRAPHER_QUERY` (and `QUERY_PROBE` when it owns the probe).
6. Verify that readings change with distance.
7. Test an automatic restart and reconnection.
8. Only then run controlled probe, touch and scan operations; mixed mode last.
