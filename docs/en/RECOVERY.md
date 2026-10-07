# Recovery runbook

Updated: **2026-10-05**. [Italiano](../it/RECOVERY.md)

What to do when the external host loses the printer, in one place. The causes and the measurements behind each step are in [Serial link loss](SERIAL_LINK_LOSS.md), [USB bridge](USB_BRIDGE.md) and [USB gadget](USB_GADGET.md).

## Before anything

- **Not while printing.** `USB_BRIDGES_RESTART`, `MCU_POWER_CYCLE`, the helper's updates and Klipper restarts are refused during a print. If the print paused on its own, find the cause first, then `RESUME`.
- **Read the state first.** On the host, `./helper.sh doctor` (installer helper) checks the cable, the channels, other readers, Klipper, the CFS, the motors and the RS-485 link without changing anything. In the Klipper console:

| Command | Shows |
| --- | --- |
| `BOARD_STATUS` | T113: MCU power rail, USB gadget state, whether each bridge is up |
| `SERIAL_STATUS` | RS-485 link `ok` or `lost`, frames, timeouts, CRC errors |
| `MOTOR_STATUS` | closed-loop motor startup, readiness, calibration, faults |
| `BOX_DEBUG` | CFS units online and their state |

Attach the doctor output and `~/printer_data/logs/klippy.log` when asking for help.

## Escalation order

Go to the next step only if the previous one did not help.

1. `FIRMWARE_RESTART`.
2. `FIRMWARE_RESTART` a second time. After a lost MCU link the MCU may never have received the shutdown, and the first try ends with `Failed automated reset of MCU`. The second one has always worked.
3. `USB_BRIDGES_RESTART CONFIRM=1`. Restarts the three bridges on the T113 in under 5 s. Klipper normally stays connected; if it goes into shutdown, `FIRMWARE_RESTART`.
4. `MCU_POWER_CYCLE CONFIRM=1`. Cuts the MCU power rail for 2 s, then runs `FIRMWARE_RESTART`. It also works while Klipper is in shutdown. Measured: Klipper ready in 9 s, CFS in 16 s, motors in 21 s.
5. `sudo systemctl restart klipper` on the host.
6. Switch the printer off and on. Without `[k2_t113]` this replaces step 4.

## By symptom

### Klipper never connects after a host boot

| Seen | Cause | Fix |
| --- | --- | --- |
| `lsusb` has no `0525:a4a6 Linux-USB Serial Gadget` | the gadget is not on the bus | Data cable in the K2 **service** Micro-USB port; the T113 bridges running (`BOARD_STATUS` once Klipper answers, or SSH to the T113). |
| `lsusb` shows `0525:a4a6`, but no `/dev/ttyUSB0..2` and Klipper waits in its start gate | the host's `usbserial` driver did not claim the gadget | `sudo sh ~/k2-openhost-t113-bootstrap/host/k2oh-host-usbserial install`. It persists the binding and binds the live gadget; other serial devices are not touched. |
| The channels exist, Main and Nozzle connect, RS-485 stays `lost` | another process reads the RS-485 channel next to Klipper (on 2026-10-05 the retired Cartographer demux took 77 of 90 bytes) | The doctor names the process. For the old demux: `scripts/system.sh retire-demux`, then restart Klipper. |

After a kernel update, check that the new kernel still has `usbserial` before rebooting: `modinfo -k <version> usbserial`.

### `Lost communication with MCU`

Klipper is in shutdown. The heaters are already off: their outputs have a 3 s `max_duration`, so the MCU switches them off when the host stops updating them.

1. Escalation steps 1 and 2 (`FIRMWARE_RESTART` twice).
2. Still failing: `BOARD_STATUS`. A bridge `DOWN` → step 3. Bridges up → step 4.
3. `auto_power_cycle: True` in `[k2_t113]` does step 4 by itself, while no print was running, at most once every 10 minutes. Off by default.

### Serial ports renumbered (`/dev/ttyUSB3/4/5`)

After a USB reconnect the ports come back with new numbers while Klipper still holds the old ones.

- With `serial: /dev/serial/by-id/usb-Allwinner_Technology_Inc._Gadget_Serial-if0N-port0` (if00 Main, if01 Nozzle, if02 RS-485), `FIRMWARE_RESTART` reconnects (the second try, as above).
- With `serial: /dev/ttyUSBn`, `FIRMWARE_RESTART` keeps failing. Stop Klipper, unplug and replug the service cable, start Klipper. Then switch to the `by-id` names for good: installer menu 19, or `config/k2/printer.cfg` in kalico-k2pro.

### RS-485 link lost: the CFS and the motors stop answering

Klipper does not shut down for this, because the MCUs still answer. The `[serial_485]` watchdog reports `RS-485 link lost` after 10 s without any answer.

- **During a print**, `link_lost_action` decides: `pause` (default), `warn`, or `shutdown`. kalico-k2pro [#30](https://github.com/MzTechnology97/kalico-k2pro/pull/30) adds `cancel`. When idle it only warns.
- Motor stalls are still caught: the X/Y/E stall lines go to the MCUs, not over RS-485.

Fix:
1. The doctor: another reader on the RS-485 channel? (see above)
2. `BOARD_STATUS`: RS-485 bridge `DOWN` → `USB_BRIDGES_RESTART CONFIRM=1`.
3. CFS powered and connected.
4. The bus recovers by itself when the bridge is back; `RS-485 link restored` appears in the console. No restart needed.
5. If the print paused: check `SERIAL_STATUS` shows `ok`, then `RESUME`.

### CFS not found

| Situation | What happens |
| --- | --- |
| Klipper started while RS-485 was down | Since kalico-k2pro [#24](https://github.com/MzTechnology97/kalico-k2pro/pull/24) the Box retries the discovery when the link comes back, then with a growing delay. `CFS found after the RS-485 link came back` appears in the console. |
| Still not found once `SERIAL_STATUS` is `ok` | `RESTART`. |
| Not found right after start | Discovery takes a few seconds. Check the CFS power and cable. |

### Closed-loop motors not ready

`MOTOR_STATUS` shows the startup failed, so homing is refused.

1. `SERIAL_STATUS` must be `ok` first: the X/Y motors are on RS-485.
2. `MOTOR_RETRY_STARTUP`.
3. A latched fault: `MOTOR_QUERY_FAULTS`, then `MOTOR_CLEAR_ERROR`.
4. A calibration flagged as suspicious: `MOTOR_CALIBRATE`, or `MOTOR_ACCEPT_CALIBRATION` only if you know it is good.

kalico-k2pro [#31](https://github.com/MzTechnology97/kalico-k2pro/pull/31) makes step 2 automatic when the startup failed because RS-485 was down: it retries when the link comes back, and otherwise every 30 s up to 5 min apart, only while idle.

### The T113 rebooted or froze

- **Reboot:** the host's ports disappear and Klipper shuts down. Wait for the bridges (`lsusb` shows the gadget, `/dev/serial/by-id/` has three entries), then `FIRMWARE_RESTART`.
- **No answer at all** (no `BOARD_STATUS`, no SSH): power-cycle the printer. On slot B a failed trial boot falls back to slot A at the next power cycle.

### After a host update or reboot

Installer helper [#9](https://github.com/MzTechnology97/k2-openhost-installer-helper/pull/9) runs the doctor by itself at every boot and after every apt change. The result goes to the Klipper console and `printer_data/logs/k2oh-health.log`. After apt it also warns when a reboot is pending, and when the newest kernel has no `usbserial`. By hand: `./helper.sh health`.
