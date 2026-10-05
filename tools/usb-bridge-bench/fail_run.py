"""USB bridge failure tests (T113 changes in RAM only).

    python fail_run.py setup|kill|kill_motion|host_close|missing|gadget|teardown

The bridges run as a transient procd service created over ubus (no files on
the T113 rootfs; it disappears with a reboot), with the bootstrap's respawn
policy "60 1 0", so the test exercises the same supervisor as slot B.
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

MOON = os.environ.get("K2_MOONRAKER", "http://127.0.0.1:7125")
SERVICE = "k2ohbench"
CHANNELS = (("main", "ttyGS0", "ttyS2"), ("nozzle", "ttyGS1", "ttyS3"),
            ("rs485", "ttyGS2", "ttyS5"))
BRIDGE = "/tmp/k2oh-bench/k2oh-bridge"


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def ssh(host, cmd, timeout=60):
    out = subprocess.run(["ssh", host, cmd], capture_output=True, text=True, timeout=timeout)
    return "\n".join(l for l in (out.stdout + out.stderr).splitlines()
                     if "WARNING" not in l and "vulnerable" not in l and "upgraded" not in l).strip()


def t113(cmd, timeout=60):
    return ssh("k2t113", cmd, timeout)


def gcode(script, timeout=120):
    req = urllib.request.Request(
        MOON + "/printer/gcode/script", data=json.dumps({"script": script}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode()


def service(action):
    # sudo on the CM5 asks a password; Moonraker manages the service
    req = urllib.request.Request(MOON + "/machine/services/%s?service=klipper" % action,
                                 data=b"", method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode()


def query(objs):
    try:
        with urllib.request.urlopen(MOON + "/printer/objects/query?" + objs, timeout=10) as r:
            return json.load(r)["result"]["status"]
    except Exception as exc:  # klippy not connected
        return {"error": repr(exc)}


def state():
    s = query("webhooks=state,state_message&print_stats=state")
    if "error" in s:
        return "moonraker:" + s["error"][:60]
    return "%s (%s)" % (s["webhooks"]["state"], s["webhooks"]["state_message"].splitlines()[0][:80])


def pids():
    out = t113("ps w | grep '[k]2oh-bench/k2oh-bridge'")
    found = {}
    for line in out.splitlines():
        for name, gs, _ in CHANNELS:
            if "/dev/%s " % gs in line:
                found[name] = int(line.split()[0])
    return found


def bridge_cpu(seconds=10):
    """CPU % of each bridge over a window, from /proc/<pid>/stat."""
    p = pids()
    if not p:
        return {}
    cmd = "for p in %s; do echo $p $(cut -d' ' -f14,15 /proc/$p/stat); done" % " ".join(map(str, p.values()))
    a = t113(cmd)
    time.sleep(seconds)
    b = t113(cmd)
    ticks = lambda txt: {int(l.split()[0]): int(l.split()[1]) + int(l.split()[2]) for l in txt.splitlines() if len(l.split()) == 3}
    ta, tb = ticks(a), ticks(b)
    return {n: round(100.0 * (tb.get(pid, 0) - ta.get(pid, 0)) / (100 * seconds), 1) for n, pid in p.items()}


def wait_ready(timeout=90):
    end = time.time() + timeout
    while time.time() < end:
        s = query("webhooks=state")
        if s.get("webhooks", {}).get("state") == "ready":
            return True
        time.sleep(1)
    return False


def firmware_restart():
    for attempt in (1, 2, 3):
        try:
            gcode("FIRMWARE_RESTART", timeout=30)
        except Exception:
            pass
        if wait_ready(60):
            log("ready after FIRMWARE_RESTART #%d" % attempt)
            return True
        log("not ready after FIRMWARE_RESTART #%d: %s" % (attempt, state()))
    return False


def setup():
    t113("for i in 0 1 2; do [ -f /tmp/k2bridge$i.pid ] && kill $(cat /tmp/k2bridge$i.pid); done; sleep 1")
    inst = {}
    for name, gs, uart in CHANNELS:
        inst[name] = {"command": ["/usr/bin/python3", BRIDGE, "/dev/" + gs, "/dev/" + uart],
                      "respawn": ["60", "1", "0"], "stdout": True, "stderr": True}
    t113("ubus call service set '%s'" % json.dumps({"name": SERVICE, "instances": inst}))
    time.sleep(2)
    log("procd bridges:", pids(), "klipper:", state())


def teardown():
    t113("ubus call service delete '{\"name\":\"%s\"}'; sleep 1; /tmp/k2oh-bench/switch.sh orig" % SERVICE)
    log("restored user bridges; klipper:", state())


def kill_one(name, motion=False):
    before = pids()
    log("kill -9 %s bridge pid %s%s" % (name, before[name], " during motion" if motion else ""))
    t0 = time.time()
    t113("kill -9 %d" % before[name])
    new = None
    while time.time() - t0 < 10:
        p = pids()
        if p.get(name) and p[name] != before[name]:
            new = p[name]
            break
        time.sleep(0.1)
    back = time.time() - t0
    # the bridge is serving again once it has written its first stats file
    serving = None
    while new and time.time() - t0 < 15:
        out = t113("cat /tmp/k2oh-bridge/%s.json 2>/dev/null" % dict((n, g) for n, g, _ in CHANNELS)[name])
        try:
            if json.loads(out)["pid"] == new:
                serving = time.time() - t0
                break
        except (ValueError, KeyError):
            pass
        time.sleep(0.1)
    log("  new pid %s after %.1f s (procd respawn seen), serving after %s s" % (
        new, back, "%.1f" % serving if serving else "?"))
    return back, serving


def kill_test():
    res = {}
    for name, _, _ in CHANNELS:
        res[name] = kill_one(name)
        time.sleep(8)
        s = state()
        r485 = query("serial_485=link_state").get("serial_485", {})
        log("  klipper after 8 s: %s; serial_485: %s" % (s, r485 or "-"))
        if "ready" not in s.split()[0]:
            firmware_restart()
    return res


def kill_motion():
    if query("toolhead=homed_axes")["toolhead"]["homed_axes"] != "xyz":
        gcode("G28", timeout=300)
    moves = ["G90", "G1 Z50 F600"] + ["G1 X%d Y%d F6000" % (40 if i % 2 else 260, 40 + 10 * i) for i in range(20)]
    import threading
    th = threading.Thread(target=lambda: _safe_gcode("\n".join(moves + ["M400"])))
    th.start()
    time.sleep(3)
    kill_one("main", motion=True)
    th.join(120)
    time.sleep(3)
    log("  klipper after motion: %s" % state())
    if not state().startswith("ready"):
        firmware_restart()


def _safe_gcode(script):
    try:
        gcode(script, timeout=180)
        log("  motion script completed")
    except Exception as exc:
        log("  motion script error: %s" % exc)


def host_close():
    log("bridge CPU with Klipper connected:", bridge_cpu())
    log("stopping klipper on the CM5 (host closes ttyUSB0-2)")
    service("stop")
    time.sleep(3)
    log("bridge CPU with the host port closed:", bridge_cpu())
    log("udc / bridge stats:", t113("cat /sys/class/udc/*/state"))
    service("start")
    log("klipper ready:", wait_ready(90), state())


def missing():
    inst = {"ghost": {"command": ["/usr/bin/python3", BRIDGE, "/dev/ttyGS9", "/dev/ttyS9"],
                      "respawn": ["60", "1", "0"], "stdout": True, "stderr": True}}
    t113("ubus call service set '%s'" % json.dumps({"name": SERVICE + "ghost", "instances": inst}))
    time.sleep(35)
    pid = t113("ps w | grep '[t]tyGS9' | awk '{print $1}'")
    cpu = t113("cut -d' ' -f14,15 /proc/%s/stat" % pid) if pid else "-"
    log("ghost bridge pid %s ticks utime/stime after 35 s: %s" % (pid, cpu))
    log("log:", t113("logread | grep -i 'ttyGS9' | tail -3"))
    t113("ubus call service delete '{\"name\":\"%sghost\"}'" % SERVICE)


def gadget():
    udc = t113("cat /sys/kernel/config/usb_gadget/g1/UDC")
    log("gadget UDC:", udc, "| CM5 ttyUSB:", ssh("cm5", "ls /dev/ttyUSB*"))
    log("unbinding the gadget for 10 s")
    t0 = time.time()
    t113("echo '' > /sys/kernel/config/usb_gadget/g1/UDC")
    time.sleep(2)
    log("  T113 bridges:", pids(), "| CM5 ttyUSB:", ssh("cm5", "ls /dev/ttyUSB* 2>&1"))
    log("  bridge CPU while unbound:", bridge_cpu(5))
    log("  klipper:", state())
    time.sleep(max(0, 10 - (time.time() - t0)))
    t113("echo %s > /sys/kernel/config/usb_gadget/g1/UDC" % udc)
    log("rebound; waiting for the CM5 to enumerate")
    for _ in range(30):
        out = ssh("cm5", "ls /dev/ttyUSB* 2>/dev/null | wc -l")
        if out.strip() == "3":
            break
        time.sleep(1)
    log("  CM5 ttyUSB:", ssh("cm5", "ls -l /dev/serial/by-id/ | tail -3"))
    log("  T113 bridges:", pids())
    log("  T113 log:", t113("logread | grep -i 'bridge' | tail -6"))
    log("  CM5 dmesg:", ssh("cm5", "dmesg | tail -12"))
    if firmware_restart():
        log("klipper:", state())
        return
    # Klipper kept the old ttyUSB nodes open, so the re-enumerated ports may
    # have new numbers: stop Klipper (closes them), re-enumerate, start.
    log("recovering: stop klipper, rebind the gadget, start klipper")
    service("stop")
    time.sleep(2)
    t113("echo '' > /sys/kernel/config/usb_gadget/g1/UDC; sleep 2; echo %s > /sys/kernel/config/usb_gadget/g1/UDC" % udc)
    time.sleep(5)
    log("  CM5 ttyUSB:", ssh("cm5", "ls -l /dev/serial/by-id/ | tail -3"))
    service("start")
    log("klipper ready:", wait_ready(90), state())
    if not state().startswith("ready"):
        firmware_restart()


if __name__ == "__main__":
    for step in sys.argv[1:]:
        log("=== %s" % step)
        {"setup": setup, "kill": kill_test, "kill_motion": kill_motion, "host_close": host_close,
         "missing": missing, "gadget": gadget, "teardown": teardown}[step]()
