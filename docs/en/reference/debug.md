# Debug and diagnostics

Every command on this page is **read-only**: it prints information and changes nothing, so you can run it at any time, also while printing, unless the table says otherwise.

## Start here

On the host:

```bash
cd ~/k2-openhost-installer-helper
./helper.sh doctor
```

The [doctor](../helper/doctor.md) checks the cable, the three channels, other processes on the serial ports, Klipper, the CFS, the motors and the RS-485 link, and suggests the fix for each problem.

In the Klipper console (Mainsail):

| Command | Shows |
| --- | --- |
| `BOARD_STATUS` | T113: slot, MCU power rail, SoC temperature, uptime, free UDISK, USB gadget state, each bridge up or down |
| `SERIAL_STATUS` | RS-485 link `ok`/`lost`, frames, timeouts, CRC errors |
| `MOTOR_STATUS [VERBOSE=1]` | Closed-loop motors: startup, readiness, calibration, protection, temperatures |
| `BOX_DEBUG [RAW=1]` | CFS units online, live state, sensors, change engine, clog detection |

## By area

### Serial links and T113

| Command | Use |
| --- | --- |
| `BOARD_STATUS` | Bridges and gadget state on the T113 |
| `SERIAL_STATUS` | RS-485 counters and link state |
| `LINK_MONITOR_REPORT` | Round-trip percentiles of every link since start (needs `[link_monitor]`, see `printer.cfg`) |

### CFS

| Command | Use |
| --- | --- |
| `BOX_DEBUG [RAW=1]` | Full CFS report; `RAW=1` adds the raw replies |
| `BOX_ENV_DEBUG` | CFS versions, hardware, temperature and humidity |
| `BOX_PRINT_INFO [FILENAME=...]` | Tools a file uses and how they would map, without starting anything |
| `_BOX_RFID_REMAINING_DIAG SLOT=<n>` | Raw remaining value the CFS returns for a slot |
| `_BOX_RFID_FALLBACK_CACHE` | Third-party RFID decoders, budgets and UID cache |
| `BOX_CFS_TRACE_START` → operation → `BOX_CFS_TRACE_SHOW` | Timeline of a load/unload from Kalico's cached state (needs `[box_cfs_trace]`; no extra bus traffic) |

### Experimental CFS firmware

| Command | Use |
| --- | --- |
| `BOX_CFS_CONFIG_INFO` | Firmware identity, startup apply result, all values |
| `BOX_CFS_CONFIG_DIAG ALL=1` | GET of the 28 parameters with range check |
| `BOX_RFID_DIAG_INFO` | RFID API (API7 / `caps=0xE8`) |
| `BOX_RFID_DIAG_INTERNAL SLOT=<0-3>` | UID, ATQA, SAK of the tag in a slot |

### Motors

| Command | Use |
| --- | --- |
| `MOTOR_STATUS VERBOSE=1` | Full state |
| `MOTOR_EVENTS [COUNT=n] [VERBOSE=1]` | Protection events (stall, overcurrent); `VERBOSE=1` gives JSON for a bug report |
| `MOTOR_QUERY_FAULTS` | Error, warning and status codes, read now |
| `MOTOR_CFG_OVERRIDE_STATUS` | Configured vs actual motor parameters |

### Host

| Command | Use |
| --- | --- |
| `HOST_FAN_STATUS` | CM5 fan mode, temperature, speed, RPM |
| `FAN_FEEDBACK_STATUS` | Printer fans with a tachometer |

## Shell commands

On the **host**:

```bash
lsusb | grep 0525:a4a6                 # the T113 gadget is on the bus
ls -l /dev/k2-*                        # the three stable channel names
ls /dev/serial/by-id/                  # the raw gadget names
sudo fuser -v /dev/k2-*                # who holds the channels (only Klipper should)
systemctl status klipper moonraker
journalctl -u klipper -b --no-pager | tail -50
vcgencmd get_throttled                 # 0x0 = no under-voltage or throttling (Raspberry Pi)
```

On the **T113** (`ssh root@<printer-ip>`):

```bash
logread | grep -E "k2oh|bridge"        # bridges and K2-OpenHost services
k2oh-mcu-fw status                     # board firmware versions
fw_printenv -n boot_partition          # slot the T113 boots (bootA or bootB)
df -h /mnt/UDISK
```

## Logs

| File | Content |
| --- | --- |
| `~/printer_data/logs/klippy.log` | Kalico: everything, including CFS, RFID decoders and motors |
| `~/printer_data/logs/moonraker.log` | Moonraker, update manager, API |
| `~/printer_data/logs/k2oh-health.log` | Automatic health check after boot and apt |
| `~/printer_data/logs/crowsnest.log` | Camera |
| `~/printer_data/logs/link_monitor.csv` | Link round trips, with `[link_monitor]` |
| T113: `logread` | Bridges, `k2oh-ctl`, HelixScreen |
| T113: `/tmp/mcu_update.log` | Last MCU/CFS firmware flash |
| OrcaSlicer plugin: `k2oh_cfs.log` | In the plugin's folder |

In Mainsail all `printer_data/logs` files are under **Machine → logs**.

## What to attach when asking for help

1. The output of `./helper.sh doctor`.
2. `klippy.log` (after the problem, before restarting Klipper again if possible).
3. The output of the console commands for the area: `BOARD_STATUS`, `SERIAL_STATUS`, `BOX_DEBUG`, `MOTOR_STATUS VERBOSE=1`.
4. Versions: `./helper.sh release status` or Mainsail → Machine → Update Manager.
5. What you did, what you expected, what happened, and whether a print was running.

Never post the contents of `k2oh_t113.token`, `~/klipper-backup/.env` or Moonraker API keys.
