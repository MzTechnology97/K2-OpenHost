"""USB bridge benchmark driver: switch bridge variants on the T113 and run an
XY motion load (no extrusion, heaters off) through Moonraker.

    python bench_run.py OUT.json VARIANT_SPEC...    e.g.  orig "new --chunk 256"
"""
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

MOON = os.environ.get("K2_MOONRAKER", "http://127.0.0.1:7125")
RUN_SECONDS = 600
SETTLE_SECONDS = 20


def gcode(script, timeout=600):
    req = urllib.request.Request(
        MOON + "/printer/gcode/script",
        data=json.dumps({"script": script}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode()


def query(objs):
    with urllib.request.urlopen(MOON + "/printer/objects/query?" + objs, timeout=10) as r:
        return json.load(r)["result"]["status"]


def ssh(host, cmd, timeout=60):
    out = subprocess.run(["ssh", host, cmd], capture_output=True, text=True, timeout=timeout)
    return out.stdout.strip()


def chunk(full=False):
    # full: every channel busy at once. The E motor turns with each zigzag
    # line (M83; cold extrusion allowed in RAM by M302 P1, no filament,
    # nozzle cold) and RFID reads go to the CFS and the external reader over
    # RS-485 while the queued motion is still running (each block is sent
    # without M400, the reads follow as separate requests whose result is
    # ignored: an empty slot answers with an error, the traffic is the point).
    # Returns a list of (script, tolerate_error).
    e = " E3" if full else ""
    steps = []
    lines = ["G90", "G1 X150 Y150 F18000"]
    for _ in range(2):
        for r in (60, 40, 20):
            lines.append("G1 X%d Y150 F18000" % (150 - r))
            lines.append("G2 X%d Y150 I%d J0 F18000" % (150 - r, r))
        for i, y in enumerate(range(40, 261, 20)):
            lines.append("G1 X%d Y%d F18000" % (40 if i % 2 == 0 else 260, y))
            lines.append("G1 X%d Y%d%s F18000" % (260 if i % 2 == 0 else 40, y, e))
        for r in (50, 30):
            lines.append("G1 X%d Y150 F18000" % (150 + r))
            lines.append("G3 X%d Y150 I%d J0 F18000" % (150 + r, -r))
        if full:
            steps.append(("\n".join(lines), False))
            lines = []
            steps += [("_BOX_RFID_READ_SLOT SLOT=%d" % s, True) for s in (0, 1, 2, 3)]
            steps.append(("RFID_READER_READ", True))
    lines.append("M400")
    steps.append(("\n".join(lines), False))
    return steps


def safe_to_move():
    s = query("print_stats=state&extruder=target&heater_bed=target&webhooks=state")
    return (s["webhooks"]["state"] == "ready" and s["print_stats"]["state"] == "standby"
            and s["extruder"]["target"] == 0 and s["heater_bed"]["target"] == 0)


def main():
    out_path = sys.argv[1]
    variants = sys.argv[2:]
    full = "--full" in variants
    variants = [v for v in variants if v != "--full"]
    results = []
    if not safe_to_move():
        raise SystemExit("printer not idle and cold")
    homed = query("toolhead=homed_axes")["toolhead"]["homed_axes"]
    if homed != "xyz":
        print("homing", flush=True)
        gcode("G28", timeout=600)
    gcode("G90\nG1 Z50 F600\nM400", timeout=120)
    load = chunk(full)
    if full:
        gcode("M302 P1\nM83")
    try:
        run_variants(variants, load, results, out_path)
    finally:
        if full:
            gcode("M302 P0\nM82")
    print("finished", flush=True)


def run_variants(variants, load, results, out_path):
    for spec in variants:
        parts = spec.split()
        irq = [x for x in parts if x.startswith("irq=")]
        parts = [x for x in parts if not x.startswith("irq=")]
        print("variant", spec, flush=True)
        ssh("k2t113", "echo %s > /proc/irq/55/smp_affinity" % (irq[0][4:] if irq else "3"))
        print("irq55", ssh("k2t113", "cat /proc/irq/55/effective_affinity_list"), flush=True)
        print(ssh("k2t113", "/tmp/k2oh-bench/switch.sh " + " ".join(parts)), flush=True)
        time.sleep(SETTLE_SECONDS)
        rec = {"variant": spec,
               "cm5_start": float(ssh("cm5", "date +%s.%N")),
               "t113_start": ssh("k2t113", "date +%s"),
               "cm5_irq_start": ssh("cm5", "grep dwc2 /proc/interrupts"),
               "cm5_stat_start": ssh("cm5", "head -1 /proc/stat; grep ctxt /proc/stat")}
        end = time.time() + RUN_SECONDS
        chunks = 0
        errors = []
        rec_tolerated = [0]
        while time.time() < end:
            if not safe_to_move():
                errors.append("printer not ready at %s" % time.strftime("%H:%M:%S"))
                break
            try:
                for script, tolerate in load:
                    try:
                        gcode(script, timeout=300)
                    except urllib.error.HTTPError as exc:
                        if not tolerate:
                            raise
                        rec_tolerated[0] += 1
                chunks += 1
            except Exception as exc:
                errors.append(repr(exc))
                break
        rec.update(cm5_end=float(ssh("cm5", "date +%s.%N")),
                   t113_end=ssh("k2t113", "date +%s"),
                   cm5_irq_end=ssh("cm5", "grep dwc2 /proc/interrupts"),
                   cm5_stat_end=ssh("cm5", "head -1 /proc/stat; grep ctxt /proc/stat"),
                   bridge_stats=ssh("k2t113", "cat /tmp/k2oh-bridge/ttyGS*.json 2>/dev/null"),
                   chunks=chunks, errors=errors, rfid_errors=rec_tolerated[0],
                   klipper=query("webhooks=state,state_message")["webhooks"])
        results.append(rec)
        json.dump(results, open(out_path, "w"), indent=1)
        print("done", spec, "chunks", chunks, "errors", errors, flush=True)
        if irq:
            ssh("k2t113", "echo 3 > /proc/irq/55/smp_affinity")
        if errors:
            break


if __name__ == "__main__":
    main()
