"""Analyze bridge benchmark windows.

    python bench_analyze.py bench_a.json [bench_b.json ...]

Needs (fetched beforehand into this folder):
  link_rtt_raw.csv   CM5 raw RTT samples: wall_time,channel,rtt_s
  linkstat.csv       T113 sampler rows (local T113 time)
  t113_tz.txt        T113 `date +%z`
"""
import csv
import datetime
import json
import math
import sys

CHANNELS = ("mcu", "nozzle_mcu", "rpi", "rs485")


def pct(values, q):
    if not values:
        return None
    k = max(1, int(math.ceil(q * len(values))))
    return values[min(k, len(values)) - 1]


def load_raw():
    rows = []
    with open("link_rtt_raw.csv") as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) == 3:
                try:
                    rows.append((float(parts[0]), parts[1], float(parts[2])))
                except ValueError:
                    pass
    return rows


def tz_offset():
    text = open("t113_tz.txt").read().strip()
    sign = -1 if text.startswith("-") else 1
    return sign * (int(text[1:3]) * 3600 + int(text[3:5]) * 60)


def load_linkstat():
    off = tz_offset()
    rows = []
    with open("linkstat.csv") as f:
        for row in csv.DictReader(f):
            try:
                naive = datetime.datetime.strptime(row["time"], "%Y-%m-%dT%H:%M:%S")
            except (ValueError, KeyError):
                continue
            epoch = naive.replace(tzinfo=datetime.timezone.utc).timestamp() - off
            rows.append((epoch, row))
    return rows


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def cpu_line(text):
    lines = text.splitlines()
    vals = [int(v) for v in lines[0].split()[1:8]]
    ctxt = int(lines[1].split()[1])
    return sum(vals), vals[3] + vals[4], ctxt


def irq_total(text):
    parts = text.split()
    return sum(int(p) for p in parts[1:5] if p.isdigit())


def hist_pct(hist, q):
    total = sum(hist)
    if not total:
        return None
    target = q * total
    run = 0
    for bucket, count in enumerate(hist):
        run += count
        if run >= target:
            return (1 << bucket) if bucket else 0  # upper bound in us
    return 1 << (len(hist) - 1)


def pooled(raw, stat, paths):
    """Repeated runs of the same variant pooled: RTT percentiles over all
    their samples, bridge CPU averaged."""
    groups = {}
    for path in paths:
        for rec in json.load(open(path)):
            groups.setdefault(rec["variant"], []).append((rec["cm5_start"], rec["cm5_end"]))
    print("=" * 78)
    print("POOLED  %-16s %3s  %-26s %-26s %-18s %s" % (
        "variant", "n", "mcu p50/p99/p99.9/max", "nozzle p50/p99/p99.9/max",
        "rs485 p50/p99", "bridge cpu main/noz/485"))
    for variant, wins in groups.items():
        inside = lambda t: any(a <= t <= b for a, b in wins)
        cells = []
        for ch in ("mcu", "nozzle_mcu", "rs485"):
            vals = sorted(r for t, c, r in raw if c == ch and inside(t) and (ch != "rs485" or r <= 0.5))
            if ch == "rs485":
                cells.append("%.2f/%.2f" % (1000 * pct(vals, .5), 1000 * pct(vals, .99)))
            else:
                cells.append("%.2f/%.2f/%.2f/%.1f" % tuple(1000 * x for x in (
                    pct(vals, .5), pct(vals, .99), pct(vals, .999), vals[-1])))
        rows = [r for t, r in stat if inside(t)]
        cpu = []
        for k in ("main_cpu_pct", "nozzle_cpu_pct", "rs485_cpu_pct"):
            v = [num(r.get(k)) for r in rows]
            v = [x for x in v if x is not None]
            cpu.append("%.2f" % (sum(v) / len(v)) if v else "-")
        print("        %-16s %3d  %-26s %-26s %-18s %s" % (
            variant, len(wins), cells[0], cells[1], cells[2], "/".join(cpu)))


def main():
    raw = load_raw()
    stat = load_linkstat()
    if sys.argv[1] == "--pool":
        pooled(raw, stat, sys.argv[2:])
        return
    for path in sys.argv[1:]:
        for rec in json.load(open(path)):
            a, b = rec["cm5_start"], rec["cm5_end"]
            dur = b - a
            print("=" * 78)
            print("%s   %.0f s, %d chunks, errors=%s, klipper=%s" % (
                rec["variant"], dur, rec["chunks"], rec["errors"] or "-",
                rec["klipper"]["state"]))
            print("  %-11s %7s %8s %8s %8s %8s %8s" % (
                "RTT ms", "n", "p50", "p95", "p99", "p99.9", "max"))
            for ch in CHANNELS:
                vals = sorted(r for t, c, r in raw if c == ch and a <= t <= b)
                slow = 0
                if ch == "rs485":
                    # RFID reads answer when the CFS has turned the slot and
                    # read the tag (tens of seconds): application time, not
                    # link latency. Counted apart.
                    slow = sum(1 for v in vals if v > 0.5)
                    vals = [v for v in vals if v <= 0.5]
                if not vals:
                    continue
                if slow:
                    print("  rs485: %d responses > 0.5 s (RFID reads) left out" % slow)
                print("  %-11s %7d %8.3f %8.3f %8.3f %8.3f %8.3f" % (
                    ch, len(vals), *(1000 * pct(vals, q) for q in (.5, .95, .99, .999)),
                    1000 * vals[-1]))
            t0, i0, c0 = cpu_line(rec["cm5_stat_start"])
            t1, i1, c1 = cpu_line(rec["cm5_stat_end"])
            busy = 100.0 * ((t1 - t0) - (i1 - i0)) / max(1, t1 - t0)
            irq = (irq_total(rec["cm5_irq_end"]) - irq_total(rec["cm5_irq_start"])) / dur
            print("  CM5: cpu %.1f%% (4 cores avg), ctxt %.0f/s, dwc2 irq %.0f/s" % (
                busy, (c1 - c0) / dur, irq))
            rows = [r for t, r in stat if a <= t <= b]
            if rows:
                def avg(key):
                    v = [num(r.get(key)) for r in rows]
                    v = [x for x in v if x is not None]
                    return sum(v) / len(v) if v else float("nan")

                def total(key):
                    return sum(num(r.get(key)) or 0 for r in rows)

                def mx(key):
                    v = [num(r.get(key)) for r in rows]
                    v = [x for x in v if x is not None]
                    return max(v) if v else float("nan")
                print("  T113: cpu0 %.1f%% cpu1 %.1f%% (max %.0f/%.0f), ctxt %.0f/s, udc irq %.0f/s, "
                      "uart irq main/noz/485 %.0f/%.0f/%.0f per s" % (
                          avg("cpu0_pct"), avg("cpu1_pct"), mx("cpu0_pct"), mx("cpu1_pct"),
                          avg("ctxt_per_s"), avg("sunxi_usb_udc_irq_per_s"),
                          avg("uart2_irq_per_s"), avg("uart3_irq_per_s"), avg("uart5_irq_per_s")))
                print("  T113 bridges cpu%% main/noz/485: %.2f/%.2f/%.2f, ctx vol/s %.0f/%.0f/%.0f, "
                      "invol/s %.1f/%.1f/%.1f" % (
                          avg("main_cpu_pct"), avg("nozzle_cpu_pct"), avg("rs485_cpu_pct"),
                          total("main_ctx_vol") / dur, total("nozzle_ctx_vol") / dur,
                          total("rs485_ctx_vol") / dur, total("main_ctx_invol") / dur,
                          total("nozzle_ctx_invol") / dur, total("rs485_ctx_invol") / dur))
                errs = {k: total(k) for k in rows[0]
                        if k.startswith("uart_") and k.rsplit("_", 1)[1] in ("fe", "oe", "bo", "brk")}
                print("  UART errors in window:", {k: int(v) for k, v in errs.items() if v} or "none",
                      " udc:", sorted({r.get("udc_state") for r in rows}))
            for blob in filter(None, rec.get("bridge_stats", "").replace("}{", "}\n{").splitlines()):
                try:
                    s = json.loads(blob)
                except ValueError:
                    continue
                parts = []
                for d in ("to_uart", "to_host"):
                    x = s.get(d)
                    if not x:
                        continue
                    parts.append("%s: %dB short=%d eagain=%d drop=%d maxq=%d delay p99<=%sus max=%dus" % (
                        d, x["bytes"], x["short_writes"], x["eagain"], x["dropped"],
                        x["max_pending"], hist_pct(x["delay_hist_log2_us"], 0.99),
                        x["max_delay_us"]))
                print("  bridge %s  %s" % (s["usb"][-6:], " | ".join(parts)))


if __name__ == "__main__":
    main()
