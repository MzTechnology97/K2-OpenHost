# USB bridge between the host and the T113: analysis and measurements

Updated: **2026-10-05**. [Italiano](../it/USB_BRIDGE.md)

The external host reaches the K2 Pro's three buses through the T113. This page covers:
- how the link really works;
- what was wrong with it;
- what changed in the [T113 bootstrap](T113_BOOTSTRAP.md);
- the measurements behind each decision.

All tests ran on the development K2 Pro: CM5 host, slot A, bridges started by hand in RAM, bed empty, heaters off.

## The path, as it is

```text
Klipper (CM5)
  serialqueue -> /dev/ttyUSB0/1/2   usbserial_generic, 0525:a4a6
  -> CM5 dwc2 USB 2.0 controller -> 4-port hub -> cable
T113 (2x Cortex-A7, kernel 5.4.61 PREEMPT)
  sunxi_usb_udc (high speed) -> configfs gadget g1: 3x gser (Generic Serial, not CDC ACM)
  -> /dev/ttyGS0/1/2 -> one bridge process per channel (Python 3.9)
  -> /dev/ttyS2 / ttyS3 / ttyS5, 230400 8N1 -> Main MCU / Nozzle MCU / RS-485
```

| Item | Found |
| --- | --- |
| socat, PTYs | **none**. The only user-space hop is the Python bridge on the T113. |
| Gadget function | `gser` (Generic Serial). No line coding or control lines are negotiated, so the host's baud setting has no effect on the USB side. |
| Kalico ports | `serial: /dev/ttyUSB0/1/2` in `printer.cfg`: numbers given by enumeration order |
| CM5 controller | `dwc2` (IRQ 34, CPU0), about **8 100 interrupts/s** even when idle (one per microframe). The CM5's RP1 `xhci` ports are unused. |
| T113 interrupts | USB device controller (IRQ 55) and all three UARTs on **CPU0**. IRQ 55 can be moved to CPU1 (checked with `effective_affinity_list`); the UART interrupts were not moved. |
| Tools on the T113 | no socat, no chrt. `taskset` is there, and Python's `os.sched_setscheduler` / `sched_setaffinity` work. |

## Problems found

1. **Blocking write in the original bridge.** The loop is `select`, `read(4096)`, then a write that retries until everything is written. When one side stops taking data (Klipper stopped, a full UART FIFO), the other direction is not read either.
   - The nozzle UART `ttyS3` showed **2 239 272 buffer overruns** (`bo`) accumulated over earlier days.
   - None appeared during any benchmark window.
2. **Dead after a USB reconnect.** After a gadget rebind (or a USB reconnect) the old `ttyGS*` descriptor only returns EOF, and writes fail with EIO.
   - On EIO the original bridge dies, and nothing restarts it.
   - On EOF it goes straight back to `select`: **104% of a T113 core**, forever, without forwarding anything again (measured, see the failure tests).
   - Klipper merely closing the ports does not cause this: `gser` does not tell the gadget.
3. **Port names depend on enumeration order.** `ttyUSB0/1/2` keep their numbers only if nothing else enumerates first and the old nodes are closed. `/dev/serial/by-id/...-if00/01/02-port0` names the interface instead.
4. **CM5 USB controller.** The bridge's traffic goes through `dwc2` and a hub. `dwc2` in host mode interrupts the CM5 about 8 100 times a second.
5. **A measurement bug of my own,** found and fixed during this work. `link_monitor.get_status()` re-sorted every sample since start on each Moonraker query.
   - After three hours, klippy's main thread used about 55% of a core and the CM5 reached 85 °C (thermal throttling).
   - Fixed in kalico-k2pro [#19](https://github.com/MzTechnology97/kalico-k2pro/pull/19): constant-cost histogram, status computed once per interval.

## What changed in the bootstrap (`k2oh-bridge`)

| Change | Why |
| --- | --- |
| Per-direction non-blocking output queues | a stalled side never stops the other. A queue past 64 KiB drops its oldest bytes and counts them, so the kernel buffers behind it never overrun. |
| `poll` registered once; masks change only when a queue starts or empties | the normal pass is poll, read, write: no list building, no clock read |
| EOF from the gadget port: reopen it, waiting 50 ms doubling up to 1 s between tries | the old descriptor is dead after a reconnect; no busy loop, at most one reopen per second |
| Counters written every 5 s **in a quiet moment** (no data for 20 ms), every 30 s when nothing changed | writing the JSON costs about 3.5 ms on the T113. Done right after forwarding a request, it delayed the MCU's answer: nozzle p99 went from about 2 to about 4 ms (batch B). |
| Delay timed only for queued data | timing every write cost more CPU than the forwarding |
| Waits for missing ports (logs every 30 s, polls every 0.5 s) | ttyGS* appear late at boot and after a gadget rebind; no restart loop |
| Exits with a reason on `EIO`/`ENODEV`; procd restarts it after 1 s (`respawn 60 1 0`) | Klipper tolerates about 5 s without its MCU, so a crashed bridge comes back first. At most one restart per second, never a tight loop. |
| `BRIDGE_OPTS` in `k2openhost.conf` (`--chunk`, `--nice`, `--rr`, `--cpu`) | tuning without editing the service. Default: none, see below. |
| `k2oh-linkstat` | sampler for long prints, see below |

## How it was measured

- **Round trips on the host:** `[link_monitor]` in kalico-k2pro, benchmark mode with `probe_hz: 10` and `raw_path`.
  - Each MCU gets 10 extra `get_uptime` queries per second, plus the `clock` answers clocksync already asks for.
  - The time is the serial layer's `#receive_time - #sent_time`.
  - RS-485: the time from writing a request to its matched answer.
  - `rpi` (the host MCU over a local socket) is the floor of the method: p50 0.04 ms.
- **T113:** `k2oh-linkstat` every 10 s.
  - per-core CPU and context switches;
  - IRQ rates of the USB controller and UARTs;
  - UART error deltas (fe, oe, bo, brk);
  - gadget state;
  - per-bridge CPU, context switches and RSS, plus the bridges' own counters.
- **CM5:** `/proc/stat` and the `dwc2` IRQ count at the start and end of each window.
- **Load**, 10 minutes per variant after a 20 s settle, through Moonraker:
  - **A**: XY only. Arcs and zig-zags at 300 mm/s, 19 blocks per window.
  - **B, C, D**: all channels at once.
    - XY as in A.
    - The extruder turning cold with each zig-zag line. `M302 P1` while the run lasts, no filament, nozzle cold.
    - RFID reads of the 4 CFS slots and of the external reader over RS-485, sent while the queued motion still runs.
    - RS-485 answers longer than 0.5 s are RFID reads (the CFS turns the slot first). They are application time and are counted apart.
- **Bridge variants:** the original bridge (`orig`) against `k2oh-bridge` (`new`), switched on the T113 between windows.
- **Run-to-run spread:** each run is about 5 800 samples per MCU, so p99.9 rests on about 6 samples. `orig` was repeated in each batch to see the spread between identical runs.

## Results

Round trip in ms, Main MCU (mcu) and Nozzle MCU (noz); bridge CPU in % of one T113 core.

### A: XY only

| Variant | mcu p50 | p95 | p99 | p99.9 | max | noz p99 | bridge CPU main/noz | T113 involuntary ctx/s (main) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| orig | 1.014 | 1.862 | 3.612 | 7.737 | 12.3 | 1.949 | 1.83 / 0.74 | 7.0 |
| first new, chunk 4096 | 1.070 | 2.196 | 4.229 | 8.663 | 16.2 | 3.525 | 3.09 / 1.44 | 22.4 |
| first new, chunk 1024 | 1.078 | 2.367 | 4.559 | 7.978 | 17.8 | 3.804 | 3.05 / 1.43 | 21.7 |
| first new, chunk 256 | 1.080 | 3.091 | 5.418 | 10.37 | 14.6 | 4.324 | 3.03 / 1.40 | 21.2 |
| first new, chunk 64 | 1.075 | 3.270 | 5.464 | 9.047 | 14.3 | 4.775 | 3.07 / 1.37 | 20.6 |

- The first rewrite read the clock and built lists on every pass: twice the CPU and worse tails. It was rewritten (the hot path above).
- Smaller reads only make p95/p99 worse: messages get split across more USB packets and passes. **4096 stays the default.**

### B: all channels, `new` with counters written every second

| Variant | mcu p50 | p99 | p99.9 | max | noz p99 | p99.9 | rs485 p50/p95 | bridge CPU main/noz/485 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| orig | 1.021 | 3.053 | 8.444 | 15.6 | 2.248 | 5.799 | 1.94 / 2.85 | 1.15 / 0.68 / 0.04 |
| new | 1.020 | 3.797 | 6.740 | 16.5 | 4.073 | 7.032 | 1.95 / 3.18 | 1.21 / 0.77 / 0.35 |
| new `--nice -10` | 1.023 | 3.905 | 8.381 | 13.3 | 4.077 | 7.740 | 1.96 / 3.06 | 1.21 / 0.76 / 0.35 |
| new `--rr 10` | 1.014 | 3.492 | 5.663 | 8.7 | 4.052 | 6.763 | 1.93 / 2.92 | 1.28 / 0.78 / 0.35 |
| orig (repeat) | 1.035 | 2.524 | 6.940 | 8.9 | 2.091 | 7.304 | 1.97 / 3.23 | 1.14 / 0.68 / 0.04 |

- Nozzle p99 is about 4.05 ms in every `new` variant, against 2.1–2.25 ms for `orig`: a real difference, not noise.
- The cause is the 3.5 ms JSON write each second, done right after forwarding a request. The quiet RS-485 bridge shows that cost (0.35% CPU for almost no traffic).

### C: all channels, `new` with counters written in quiet moments

| Variant | mcu p50 | p99 | p99.9 | max | noz p99 | p99.9 | bridge CPU main/noz/485 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| orig | 1.037 | 2.508 | 6.424 | 12.7 | 1.878 | 7.401 | 1.14 / 0.69 / 0.04 |
| new | 1.014 | 2.624 | 7.325 | 8.5 | 2.034 | 6.695 | 1.04 / 0.66 / 0.06 |
| new `--rr 10` | 1.019 | 2.502 | 8.369 | 14.4 | 1.791 | 7.613 | 1.12 / 0.68 / 0.06 |
| new, USB IRQ on CPU1 | 1.027 | 2.488 | 5.682 | 8.2 | 1.785 | 4.730 | 1.06 / 0.62 / 0.06 |
| orig (repeat) | 1.045 | 2.894 | 8.603 | 10.2 | 2.029 | 7.870 | 1.07 / 0.64 / 0.04 |

Batch C ran while the `link_monitor` bug was loading the CM5 more and more (CM5 CPU from 9.8% to 13.8%). The variants are interleaved, so the comparison holds, but batch D repeats it on a freshly restarted Klipper.

### D: all channels, clean host (Klipper restarted with the fix)

| Variant | mcu p50 | p95 | p99 | p99.9 | max | noz p50 | p99 | p99.9 | rs485 p50/p95 | bridge CPU main/noz/485 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| orig | 0.993 | 1.464 | 2.426 | 8.043 | 14.6 | 0.909 | 1.909 | 6.735 | 1.94 / 3.01 | 1.27 / 0.76 / 0.04 |
| new | 0.970 | 1.411 | 2.359 | 7.904 | 15.5 | 0.884 | 1.881 | 7.353 | 1.96 / 2.94 | 1.18 / 0.74 / 0.05 |
| orig | 0.995 | 1.521 | 2.500 | 8.030 | 15.2 | 0.909 | 1.832 | 7.946 | 1.98 / 3.11 | 1.27 / 0.75 / 0.04 |
| new | 0.982 | 1.531 | 2.525 | 11.89 | 16.3 | 0.887 | 1.903 | 7.246 | 1.97 / 2.89 | 1.18 / 0.72 / 0.06 |
| **orig, 2 runs pooled** | 0.99 | — | 2.46 | 8.03 | 15.2 | 0.91 | 1.87 | 7.18 | 1.96 / — | 1.27 / 0.76 / 0.04 |
| **new, 2 runs pooled** | 0.97 | — | 2.45 | 8.87 | 16.3 | 0.89 | 1.89 | 7.25 | 1.97 / — | 1.18 / 0.73 / 0.06 |

- p50 to p99 are the same within a few hundredths of a millisecond. p99.9 and max rest on a handful of samples and move as much between two `orig` runs as between `orig` and `new`.
- The new bridge uses about 7% less CPU.
- CM5: 0.7% CPU (4-core average), against 5–14% during batches B and C with the `link_monitor` bug. The mcu p95 also dropped from about 1.85 to about 1.5 ms: part of the tail was the host's own load.

### In every window of every batch

- UART errors (fe, oe, bo, brk): **0**.
- Short writes, EAGAIN, dropped bytes: **0**. The bridge queue was never used (`maxq 0`).
- Klipper `ready` at the end of every window.
- CM5 `dwc2` interrupts: about 8 075–8 130/s, whatever the load.

## Scheduling, affinity, interrupts

| Option | Measured | Decision |
| --- | --- | --- |
| `nice -10` | fewer involuntary switches (0.6/s instead of 2.3/s), tails not better | not by default |
| `SCHED_RR 10` | involuntary switches almost 0. One window with the best mcu tail (B), the next one (C) not better than `orig`. Within run-to-run spread. | not by default, available as `BRIDGE_OPTS="--rr 10"` |
| `SCHED_FIFO` | not tried | — |
| USB IRQ 55 on CPU1 | best p99.9 of batch C (mcu 5.7, noz 4.7 ms), from a single window | promising, not by default: one window is within spread. The mask is not persistent and the bootstrap does not set it. |
| Bridge CPU affinity | not measured separately: with the IRQs on CPU0 and two cores, pinning has nothing to win from without moving the IRQs | — |

The bridges use about 1% (Main) and 0.7% (Nozzle) of one core. The T113 is about 13% busy per core in total; the rest is other processes, not analysed here.

## USB gadget: gser or CDC ACM

- **gser** (current): no control requests, no line coding, raw bulk pipes. It is what the host's `usbserial_generic` binds to by VID/PID (`0525:a4a6`).
- **CDC ACM** would bring `cdc_acm` on the host, standard `ttyACM*` names, and a serial number in `by-id`. Its added features (line coding, DTR/RTS) are useless here: the UART speed is fixed on the T113, and nothing uses the control lines.
- The data path and the packet size are the same (bulk, 512 bytes at high speed), so no latency difference is expected.
- Changing it would mean changing the gadget script, the host udev rules and the Kalico `serial:` paths, without a measured gain. **Kept gser.**

## Failure tests

procd was emulated with a transient service created over `ubus` (RAM only, gone at reboot), with the bootstrap's `respawn 60 1 0`. Klipper idle unless stated; `k2oh-ctl` was stopped during the tests so Klipper's shutdown sound would not play at night.

| Test | Original bridges (slot A today) | `k2oh-bridge` under procd |
| --- | --- | --- |
| `kill -9` of one bridge, each channel | the bridge is gone until restarted by hand (no supervisor in slot A) | back and serving in **1.5 s**; Klipper stayed `ready` on Main, Nozzle and RS-485 |
| `kill -9` of the Main bridge **during motion** (100 mm/s zig-zag) | — | back in about 1.3 s, the motion finished, Klipper `ready` |
| Host closes the ports (Klipper stopped 15 s) | the gadget is not told (`gser` has no line state): nothing changes | nothing changes either: 0.4 / 0.1 / 0.0% CPU, no reopen; Klipper `ready` after start |
| Missing port at start (`ttyGS9`, `ttyS9`) | exits with a traceback (from the code, not run) | waits, logs every 30 s, about 0% CPU |
| Gadget unbound 10 s, then bound again | Main and Nozzle **die** on EIO and nothing restarts them; RS-485 **spins at 104% CPU** on a dead descriptor and never forwards again. Klipper could not recover until the bridges were restarted by hand. | Main and Nozzle exit on EIO and procd restarts them; all three reopen on EOF. RS-485 came back by itself. |
| Same, CM5 side, with `serial: /dev/ttyUSBn` | the ports come back as `ttyUSB2/3/4` because Klipper still holds the old ones: `FIRMWARE_RESTART` fails (three tries); recovery needs Klipper stopped and the gadget re-enumerated | same |
| Same, with `serial: /dev/serial/by-id/...` | — | **`FIRMWARE_RESTART` recovers** (the first try hits the known "Failed automated reset", the second works); RS-485 ok, X/Y motors verified |
| T113 or CM5 reboot | not run: rebooting needs your go-ahead | expected like the gadget test: a CM5 reboot drops the USB host (EOF on the gadget, the bridges reopen); a T113 reboot drops the device (host ports disappear, Klipper shuts down, `FIRMWARE_RESTART` after the bridges are up) |

Also seen: if Klipper starts while the RS-485 bridge is dead, the CFS is not discovered and stays so after the link returns; a Klipper `RESTART` fixes it.

## Native C bridge: comparison (not implemented)

| | Python (`k2oh-bridge`) | C (poll/epoll, same design) |
| --- | --- | --- |
| CPU (measured / estimated) | 1.0–1.2% Main, 0.6–0.7% Nozzle, under 0.1% RS-485 | about 5–10 times lower: a few tenths of a percent |
| Forwarding time per packet | tens of µs of interpreter work around two syscalls | a few µs |
| Share of the round trip | the round trip p50 is about 1 ms: UART time at 230400 baud (43 µs per byte, both ways) plus USB microframes plus MCU work | the saving is under 5% of p50 |
| Tails (p99.9, max) | 5–9 ms, the same with the original bridge, `nice`, RR or another IRQ CPU | unchanged: the tails come from scheduling and interrupts on the shared CPU0 and from the CM5 side, not from the interpreter |
| Risks | none new: same interpreter as the rest of the bootstrap | cross-compiling for the T113 (armhf, Tina's libc), a binary in the image, a second code base to test |

**Verdict: not justified now.**
- In every batch the bridge is not the limit. Its CPU is about 1%, it never queues, and its forwarding time is well under the spread between identical runs.
- A C bridge becomes worth it only if a future measurement shows otherwise, for example the bridge CPU rising with more traffic, or queueing appearing.

## Recommendations

1. **Use the slot B `k2oh-bridge`** (this change). Same latency as the original within measurement spread, slightly lower CPU, and no head-of-line blocking. It survives a USB reconnect, restarts in 1.5 s and waits for missing ports.
2. **Use `/dev/serial/by-id/usb-Allwinner_Technology_Inc._Gadget_Serial-if0N-port0`** instead of `/dev/ttyUSBn` in `printer.cfg` (if00 Main, if01 Nozzle, if02 RS-485). The interface number does not change when the gadget reconnects, and `FIRMWARE_RESTART` then recovers.
   - Done in kalico-k2pro [#20](https://github.com/MzTechnology97/kalico-k2pro/pull/20).
   - Done on the development CM5, with a backup of the old `printer.cfg`.
3. **Moving the T113 cable to an `xhci` port is not possible on the current carrier.** See [The CM5's USB 3.0 ports and the carrier board](#the-cm5s-usb-30-ports-and-the-carrier-board). Low priority: the expected gain is small.
4. **CM5 cooling.** The CM5 idled at 70–78 °C and throttled at 85 °C under a CPU-heavy bug. Check `vcgencmd get_throttled` after long prints.
5. **Leave `nice`, RR and IRQ affinity at the defaults** until a longer measurement shows a difference larger than the spread between identical runs.

## The CM5's USB 3.0 ports and the carrier board

Checked on 2026-10-05, read-only on the development CM5 during a print.

**What the CM5 sits on.** The CM5 is on a Waveshare **CM4-IO-BASE-A**. Its FE1.1S hub shows up as `1a40:0101 Terminus Technology Hub`.
- All of its USB ports are USB 2.0, behind that hub, on the CM5's `dwc2` controller: two Type-A ports, and two on an FFC connector that need an adapter cable.
- The two Type-A ports hold the T113 gadget and, for now, a spare camera (`364d:6366`, `uvcvideo`, MJPEG 1280×720 at 25 fps).
- The full setup needs three devices: the T113, the chamber camera and Cartographer (the nozzle camera was removed). With an FFC adapter for the third port, all three share one 480M hub.
- `dwc2` has taken 267 million interrupts, all on CPU0.
- The CM5's two RP1 `xhci` controllers (buses 2–5) have nothing attached.

**Why the RP1 ports cannot be reached.** The CM5's two USB 3.0 ports use the pins of the CM4's 2-lane CAM0 and DSI0 ports. The USB 2.0 pairs of those ports are pins 134/136 and 163/165 ([Raspberry Pi, *Transitioning from CM4 to CM5*](https://pip-assets.raspberrypi.com/categories/1261-transitioning/documents/RP-008924-WP-1-Transitioning%20from%20Compute%20Module%204%20to%20Compute%20Module%205.pdf)).
- A CM4 carrier wires those pins to camera or display FPC connectors.
- On the CM4-IO-BASE-A (two CSI connectors, one DSI) one CSI connector carries USB3-0, and its DSI connector may carry USB3-1. They have no VBUS and no USB connector, so they are not usable as USB ports.

**The CM4-to-Pi4 adapter.** Its four USB 3.0 ports come from a **VL805** on PCIe, as on a Pi 4, not from the CM5's RP1 ports.
- With a CM5 the VL805 would be a third `xhci` controller on the external PCIe x1. That PCIe is enabled on this CM5 (`pcie@1000110000` okay), and nothing is on it now.
- Waveshare does not document the adapter with a CM5, nor where the VL805 firmware comes from.
- It replaces the whole carrier, and it has no M.2 slot.
- Not recommended for this.

**Ways to an `xhci` port, from least to most change:**

| Option | What it gives | Cost and risk |
| --- | --- | --- |
| USB 3.0 controller card in the CM4-IO-BASE-A's **M.2 M-key** slot (empty: the CM5 boots from eMMC) | an `xhci` controller on PCIe for the T113 and Cartographer; the camera stays on the board's hub | one card, no carrier change. Pick a VL805 card, the controller already used on the Pi 4. Not tested here. |
| A carrier made for the CM5 with four USB ports, e.g. **Geekworm X1500** (2× USB 3.0, 2× USB 2.0, 2× M.2 NVMe, PWM fan header, RTC battery socket) | T113 and Cartographer each alone on one RP1 `xhci` controller, the camera on a USB 2.0 port | the whole carrier. It is larger (about 87 × 88 mm against 85 × 56 mm) and wants 5.1 V 5 A over USB-C PD. That its USB 3.0 ports are the RP1 ports is inferred: its only PCIe lane feeds the NVMe slots, and Geekworm does not say. Check with `lsusb -t` after the swap. |
| Waveshare **CM5-IO-BASE-A** (same bank-card size, 2× USB 3.2 Gen1) or the official CM5 IO Board | the CM5's own RP1 ports | the whole carrier; check the 5 V supply and the case. That its USB 3.2 ports are the RP1 ports is inferred: the CM5 has no other USB 3 source, and Waveshare does not say. |
| CM4-to-Pi4 adapter | VL805, as above | carrier change with undocumented CM5 support; no gain over the M.2 card |

**Is it worth it?**
- The gain is the ~8 000 `dwc2` interrupts/s on CPU0, and a T113 that no longer shares a hub with the camera. A UVC camera reserves periodic bandwidth in every microframe, and bulk traffic such as the T113's only gets what is left on that bus.
- The measurements above found the round trip limited by UART time, and the tails by scheduling. The CM5 used 0.7% CPU in batch D.
- With one camera, an FFC adapter on the current board is enough for the port count: T113 and camera on the Type-A ports, Cartographer on the FFC port. Measure the round trip with the camera off and streaming. Move the T113 to an `xhci` controller (M.2 card, or X1500) only if the tails grow.
- The gadget runs at 480M on any port, USB 3 or not.
- The `by-id` names in `printer.cfg` do not depend on the port, so moving the cable needs no configuration change.
- Never move the cable while printing.

## Long-print measurement mode

On the host, `printer.cfg`:

```ini
[link_monitor]
interval: 60      # one CSV row per channel per minute
# probe_hz: 0     # extra round trips; keep 0 for prints (10 only for benchmarks)
# raw_path:       # every sample to a file; benchmarks only
```

`LINK_MONITOR_REPORT` prints the percentiles since start. Rows go to `~/printer_data/logs/link_monitor.csv`.

On the T113 (slot B), during the print:

```sh
k2oh-linkstat --interval 10 --out /tmp/k2oh-linkstat.csv &
```

It only reads `/proc` and `/sys`: CPU, interrupts, UART error deltas, gadget state and the bridges' counters. The file is in RAM, so copy it before rebooting.
