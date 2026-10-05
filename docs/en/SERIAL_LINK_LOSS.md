# Losing a serial link behind the T113

Updated: **2026-10-04**. [Italiano](../it/SERIAL_LINK_LOSS.md)

The external host reaches the K2 Pro's three buses through USB gadget serial ports that the T113 bridges to its UARTs. If a bridge, the USB cable or the T113 fails, what does the host do? Klipper stops, or does it keep printing without noticing? These tests answer that. They were made on the development K2 Pro, in standby with the heaters off, by stopping one T113 bridge at a time.

## What was measured

| Lost | Host behaviour | Assessment |
| --- | --- | --- |
| Nozzle MCU bridge (ttyGS1 ↔ ttyS3) | shutdown after **5.2 s**: `Lost communication with MCU 'nozzle_mcu'` | Safe. Klipper's MCU protocol notices. The heater outputs are configured with a 3 s `max_duration`, so an MCU that stops getting host updates switches its heaters off by itself. |
| Main MCU bridge | same mechanism, also seen in the logs | Safe, as above. |
| RS-485 bridge (ttyGS2 ↔ ttyS5: CFS, X/Y motor boards) | **no reaction**: Klipper stayed `ready`, `motor_ready` stayed true, the log only showed request timeouts | **Not noticed.** A print would go on with the CFS (feeding, runout) and the motor diagnostics silent. |
| USB cable or T113 crash | the host's serial devices disappear and the MCU links are lost | Safe: shutdown as above. |

Also observed:
- **After a lost MCU link the MCU may not be in shutdown,** because it never received the command. The first `FIRMWARE_RESTART` can then fail with `Failed automated reset of MCU`. A second one worked here. A power cycle of the MCU rail always resets the MCUs cleanly.
- **Motor faults still stop the printer during an RS-485 outage.** The X/Y/E stall pins are wired to the Main and Nozzle MCUs, not to RS-485. A stall whose protection query fails is handled as an unverified fault, and X/Y shut down.
- **The RS-485 bus recovers on its own** when the bridge comes back, with no restart.
- **Restarting all three bridges takes under 5 s,** so Klipper stays connected. It is a useful first remedy for a stuck bridge.

## What K2-OpenHost does about it

1. **RS-485 link watchdog** in kalico-k2pro (`[serial_485 serial485]`):
   - the link is lost when no device has answered for `link_lost_timeout` (10 s) with 3 timeouts in a row; one absent device does not count;
   - during a print, `link_lost_action` pauses (the default), warns or shuts down; when idle it warns;
   - when the link comes back, it is reported.
2. **Recovery controls through the T113** (`k2oh-ctl` + `[k2_t113]`):
   - `USB_BRIDGES_RESTART CONFIRM=1`;
   - `MCU_POWER_CYCLE CONFIRM=1`, which also works while Klipper is shut down and restarts the firmware afterwards;
   - the Moonraker power device `K2_MCU_Power`, locked while printing.
3. **Optional hardware stop:** `estop_on_shutdown: m112` cuts the MCU power rail on an emergency stop, so heaters and motors lose power even if an MCU stopped answering.
4. **Optional automatic recovery:** `auto_power_cycle: True` power-cycles the MCUs and restarts after a lost MCU link while no print was running, at most once every 10 minutes.

Both options are off by default.

## Bridge crashes and USB reconnects

A crashed bridge restarted by procd within 1.5 s kept Klipper `ready`, also during motion. A USB reconnect needs `serial: /dev/serial/by-id/...` on the host to recover with `FIRMWARE_RESTART`. See the failure tests in [USB bridge](USB_BRIDGE.md#failure-tests).

## Still to test

- The watchdog's pause during a real print. In the standby tests Klipper is not printing, so only the warning path ran.
- The same tests with slot B instead of slot A's hand-started bridges.
