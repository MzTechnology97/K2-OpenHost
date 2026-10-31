# USB bridge between the host and the T113

[Italiano](../it/USB_BRIDGE.md)

The host reaches the K2 Pro's three buses through the T113. This page describes the path, what the slot B bridge does, how it was measured and how it behaves when something fails.

## The path

```text
Klipper (host)
  serialqueue -> /dev/serial/by-id/...-if00/01/02   usbserial_generic, 0525:a4a6
  -> host USB controller -> cable
T113 (2x Cortex-A7, kernel 5.4 PREEMPT)
  USB device controller -> configfs gadget: 3x gser (Generic Serial)
  -> /dev/ttyGS0/1/2 -> one k2oh-bridge process per channel
  -> /dev/ttyS2 / ttyS3 / ttyS5, 230400 8N1 -> Main MCU / Nozzle MCU / RS-485
```

There is no socat and no PTY: the only user-space hop is the bridge on the T113. `gser` negotiates no line coding, so the baud rate set on the host has no effect; the UART speed is fixed on the T113. Use the `by-id` names in `printer.cfg` (if00 Main, if01 Nozzle, if02 RS-485): they do not change when the gadget reconnects, while `ttyUSBn` numbers can.

## What `k2oh-bridge` does

The bridge in [slot B](T113_BOOTSTRAP.md) replaces Creality's original one, which had two faults: a blocking write (a stalled side stopped the other direction too) and no recovery after a USB reconnect (it died on EIO, or spun at 104 % of a core on a dead descriptor).

| Behaviour | Why |
| --- | --- |
| A non-blocking output queue per direction; past 64 KiB it drops the oldest bytes and counts them | a stalled side never stops the other, and the kernel buffers never overrun |
| On EOF from the gadget it reopens the port, waiting 50 ms up to 1 s between tries | after a reconnect the old descriptor is dead; no busy loop |
| Exits on EIO/ENODEV and procd restarts it after 1 s | Klipper tolerates about 5 s without its MCU, so the bridge is back first |
| Waits for ports that are missing at boot | `ttyGS*` appear late; no restart loop |
| Writes its counters only in a quiet moment (no data for 20 ms) | writing them right after a request delayed the MCU's answer |
| Reads 4096 bytes at a time | smaller reads made the tail latency worse |
| `BRIDGE_OPTS` in `k2openhost.conf` (`--nice`, `--rr`, `--cpu`) | tuning without editing the service; off by default |

## Measurements

Round trips were measured with `[link_monitor]` in Kalico (10 extra `get_uptime` queries per second per MCU), the T113 with `k2oh-linkstat`, 10 minutes per variant with X/Y moves, the extruder and RFID reads on all three channels at once.

On a clean host the slot B bridge and the original one are equal within the spread between identical runs:

| Channel | p50 | p99 | p99.9 |
| --- | --- | --- | --- |
| Main MCU | 0.97 ms | 2.45 ms | about 8 ms |
| Nozzle MCU | 0.89 ms | 1.89 ms | about 7 ms |
| RS-485 | 1.97 ms | | |

The round trip is set by the UART (43 µs per byte at 230400 baud, both ways) and the USB microframes; the tails come from scheduling on the T113 and the host, not from the bridge. The bridge uses about 1 % of a core on the Main channel, 0.7 % on the Nozzle channel and under 0.1 % on RS-485, and never queued. No UART errors, short writes or dropped bytes in any run.

Over the 18 h 44 min print of 2026-10-05 (930 one-minute rows per channel):

| Channel | p50 | p99 (median of rows) | worst sample | Errors |
| --- | --- | --- | --- | --- |
| Main MCU | 1.17 ms | 5.25 ms | 18.8 ms | 0 retransmitted bytes |
| Nozzle MCU | 1.04 ms | 3.01 ms | 16.4 ms | 0 retransmitted bytes |
| RS-485 | 1.87 ms | 3.36 ms | 4.4 s (an RFID read) | 0 timeouts, 0 CRC errors |

`nice`, real-time scheduling and moving the USB interrupt to the second core did not give a difference larger than that spread, so they stay off.

## Failure tests

| Test | Result with `k2oh-bridge` under procd |
| --- | --- |
| `kill -9` of one bridge, also during motion | back in about 1.5 s; Klipper stays `ready`, the move finishes |
| Klipper closes the ports for 15 s | nothing changes on the T113 (`gser` has no line state) |
| A port missing at start | the bridge waits and logs every 30 s, at about 0 % CPU |
| Gadget unbound for 10 s, then bound again | the bridges reopen or restart by themselves; with `by-id` paths `FIRMWARE_RESTART` recovers Klipper (the first try may report "Failed automated reset", the second works) |
| Host reboot | the bridges reopen with the same PIDs; the host is back in about 15 s with Klipper `ready`, RS-485, CFS and motors |

If Klipper starts while the RS-485 link is down, kalico-k2pro #24 rediscovers the CFS once it returns (covered by tests, not seen live yet).

## Decisions

- **gser rather than CDC ACM.** ACM would give `ttyACM*` names and line coding, which nothing here uses. Same bulk path and packet size, so no latency gain; changing it would touch the gadget, the udev rules and the Kalico paths for nothing.
- **No native C bridge.** It would use a fraction of the CPU, but the bridge is not the limit: its forwarding time is far below the run-to-run spread and the tails do not come from it.
- **Host USB.** Give the T113 a USB controller of its own if the carrier allows it; on the reference CM5-IO-BASE-A it is alone on one RP1 controller (see [Host hardware](HOST.md#usb)). Never move the cable while printing.

## Measuring a long print

On the host, in `printer.cfg`:

```ini
[link_monitor]
interval: 60      # one CSV row per channel per minute
# probe_hz: 0     # extra round trips; keep 0 for prints (10 only for benchmarks)
# raw_path:       # every sample to a file; benchmarks only
```

`LINK_MONITOR_REPORT` prints the percentiles since start; the rows go to `~/printer_data/logs/link_monitor.csv`.

On the T113 (slot B), during the print:

```sh
k2oh-linkstat --interval 10 --out /tmp/k2oh-linkstat.csv &
```

It only reads `/proc` and `/sys`: CPU, interrupts, UART error deltas, gadget state and the bridges' counters. The file is in RAM, so copy it before rebooting.
