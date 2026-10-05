# USB bridge benchmark and failure tests

These scripts produced the measurements in [USB bridge](../../docs/en/USB_BRIDGE.md) ([Italiano](../../docs/it/USB_BRIDGE.md)). They are kept so the same method can be repeated, for example after moving the T113 cable to another CM5 USB port.

They drive the printer through Moonraker and reach the two boards over SSH:
- `K2_MOONRAKER`, default `http://127.0.0.1:7125`;
- SSH aliases `cm5` (the host) and `k2t113` (the printer).

On the T113 everything stays in RAM: `/tmp/k2oh-bench/` holds `switch.sh`, the bridge under test (`k2oh-bridge` from the bootstrap) and `k2oh-linkstat`.

**The printer moves.** The bed must be empty and the heaters off. `bench_run.py` checks that the print state is `standby` and both targets are 0 before every block.

| File | What it does |
| --- | --- |
| `switch.sh` (on the T113) | switches the three bridges between the original `/tmp/k2-openhost-dual-bridge.py` (`orig`) and `k2oh-bridge` (`new [options]`), with the same pid files |
| `bench_run.py OUT.json [--full] VARIANT...` | for each variant: switch the bridges, settle 20 s, run 10 minutes of load, record the CM5 and T113 counters. `--full` adds the cold extruder (`M302 P1` for the run) and RFID reads. A variant prefixed `irq=2` moves the USB device interrupt to CPU1 for that window. |
| `bench_analyze.py OUT.json...` / `--pool OUT.json...` | percentiles per window, or repeated variants pooled |
| `fail_run.py setup kill kill_motion host_close missing gadget teardown` | failure tests, with the bridges under a transient procd service (`ubus`, RAM only) using the bootstrap's respawn policy |

## Before a run

1. On the host, `printer.cfg`:

   ```ini
   [link_monitor]
   probe_hz: 10
   raw_path: ~/printer_data/logs/link_rtt_raw.csv
   ```

   Restart Klipper while idle.
2. On the T113, start the sampler:

   ```sh
   k2oh-linkstat --out /tmp/k2oh-bench/linkstat.csv &
   ```

3. Stop `k2oh-ctl` during the failure tests: the tests shut Klipper down, and its shutdown sound would play.

## Analysis

Copy `link_rtt_raw.csv` (host), `linkstat.csv` (T113) and the output of `date +%z` on the T113 (as `t113_tz.txt`) next to the JSON files, then run `bench_analyze.py`.

## After a run

1. Set `probe_hz` back to 0, remove `raw_path`, and restart Klipper while idle.
2. Stop `k2oh-linkstat`; its file grows in RAM.
3. `switch.sh orig` to go back to the hand-started bridges.
