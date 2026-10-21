# /// script
# requires-python = ">=3.12"
#
# [tool.orcaslicer.plugin]
# name = "K2-OpenHost CFS"
# description = "Creality K2 with K2-OpenHost (Kalico + Moonraker): CFS slots synced with their exact filament, a CFS panel to choose the slot of each filament, and that choice sent with the print."
# author = "K2-OpenHost"
# version = "0.6.0"
# ///
"""K2-OpenHost CFS plugin for OrcaSlicer 2.5 or later.

OrcaSlicer's built-in Moonraker agent matches a CFS slot to a preset by
material only ("Generic PLA" for every PLA), and its classic print-host
upload has no filament -> slot choice. This plugin has three capabilities:

- printer agent "K2-OpenHost CFS" (same Moonraker): each CFS slot is
  published with the OrcaSlicer filament_id Kalico keeps per filament
  (box.slots[].orca_filament_id), so Sync selects the slot's own root preset.
  With OrcaSlicer's global "Use printer agents" option on, the print dialog's
  map starts the job with BOX_PRINT_START MAP=tool:slot;
- script "K2-OpenHost CFS slots": a panel beside the 3D view to choose the
  CFS slot of each project filament (proposed by material, then colour);
- slicing-pipeline post-process: that choice is written after the first
  G-code line as "; K2OH_TOOL_MAP = tool:slot,...", which Kalico's
  box_print_mapping uses at print start instead of its automatic map. This
  works with the classic "Upload and print", without the global option.

Select the agent in the printer preset and put the Moonraker address with
its port (host:7125) in the print host field.
"""

import http.client
import json
import os
import ssl
import sys
import threading
import time
import uuid

try:
    import orca
except ImportError:  # unit tests and stand-alone checks
    orca = None

AGENT_ID = "k2_openhost_cfs"
AGENT_NAME = "K2-OpenHost CFS"
AGENT_VERSION = "0.6.0"

# Network status codes (slic3r/Utils/bambu_networking.hpp).
SUCCESS = 0
ERR_INVALID_HANDLE = -1
ERR_FILE_NOT_EXIST = -14
ERR_CANCELED = -18
ERR_UPLOAD_FAILED = -4020
ERR_START_FAILED = -4030
CONNECT_OK = 0

# PrintingStage values for update_fn.
STAGE_CREATE, STAGE_UPLOAD, STAGE_SENDING, STAGE_FINISHED, STAGE_ERROR = 0, 1, 3, 6, 7

SLOTS_PER_BOX = 4
# Value OrcaSlicer itself puts in an empty API key field.
PLACEHOLDER_KEYS = ("", "88888888")
STATUS_OBJECTS = ("print_stats", "virtual_sdcard", "extruder", "heater_bed",
                  "fan", "toolhead")
BOX_FIELDS = "slots,boxes,print_info"
FULL_PUSH_EVERY_S = 30.0
DEFAULTS = {"poll_interval_s": 2.0, "model_id": "", "use_slot_map": True}


LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "k2oh_cfs.log")
LOG_MAX_BYTES = 512 * 1024


def log(msg, *args):
    line = "%s [k2oh-cfs] %s" % (time.strftime("%Y-%m-%d %H:%M:%S"),
                                 msg % args if args else msg)
    print(line, file=sys.stderr, flush=True)
    if orca is None:  # unit tests
        return
    # OrcaSlicer does not keep plugin stderr; the plugin folder is writable.
    try:
        if os.path.exists(LOG_PATH) and os.path.getsize(LOG_PATH) > LOG_MAX_BYTES:
            os.replace(LOG_PATH, LOG_PATH + ".1")
        with open(LOG_PATH, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except OSError:
        pass


# ----------------------------------------------------------------------------
# Pure helpers (no OrcaSlicer, no network): unit tested.
# ----------------------------------------------------------------------------

def normalize_color(value):
    """'#B1BEC6' -> 'B1BEC6FF' (the AMS tray colour format)."""
    text = str(value or "").strip().lstrip("#").upper()
    if len(text) == 6 and all(c in "0123456789ABCDEF" for c in text):
        return text + "FF"
    if len(text) == 8 and all(c in "0123456789ABCDEF" for c in text):
        return text
    return "00000000"


def tray_info_idx(slot):
    """The filament_id OrcaSlicer matches the slot with.

    Kalico's own id when it has one. Otherwise an id no preset has, so
    OrcaSlicer falls back to its "Generic <material>" preset; an empty id
    would make it an unknown filament.
    """
    orca_id = str(slot.get("orca_filament_id") or "").strip()
    if orca_id:
        return orca_id
    return "K2OH_" + str(slot.get("material") or "UNKNOWN").strip().upper()


def build_ams(slots, boxes=None):
    """The AMS block of a push_status message from Kalico's box.slots.

    Every online CFS is one 4-tray unit with ams_id = address - 1, so the
    tray index ams_id * 4 + slot_id is Kalico's slot index. The external
    spool holder is not a CFS slot and is left out.
    """
    physical = [s for s in slots or [] if not s.get("external")
                and isinstance(s.get("index"), int) and s["index"] >= 0]
    by_index = {s["index"]: s for s in physical}
    unit_ids = set()
    for box in boxes or []:
        if box.get("online", True) and isinstance(box.get("address"), int):
            unit_ids.add(box["address"] - 1)
    if not unit_ids:
        unit_ids = {index // SLOTS_PER_BOX for index in by_index}
    units, ams_bits, tray_bits = [], 0, 0
    for ams_id in sorted(unit_ids):
        ams_bits |= 1 << ams_id
        trays = []
        for slot_id in range(SLOTS_PER_BOX):
            index = ams_id * SLOTS_PER_BOX + slot_id
            slot = by_index.get(index) or {}
            tray = {"id": str(slot_id), "tag_uid": "0000000000000000"}
            material = str(slot.get("material") or "").strip()
            if slot.get("present") and material:
                tray_bits |= 1 << index
                tray.update({
                    "tray_info_idx": tray_info_idx(slot),
                    "tray_type": material,
                    "tray_color": normalize_color(slot.get("color")),
                    "tray_sub_brands": str(slot.get("name") or material),
                })
                temp = slot.get("target_temp")
                if isinstance(temp, (int, float)) and temp > 0:
                    tray["nozzle_temp_min"] = str(int(temp))
                    tray["nozzle_temp_max"] = str(int(temp))
            else:
                tray.update({"tray_info_idx": "", "tray_type": "",
                             "tray_color": "00000000",
                             "tray_slot_placeholder": "1"})
            trays.append(tray)
        units.append({"id": str(ams_id), "info": "0002", "tray": trays})
    return {"ams": units, "ams_exist_bits": "%X" % ams_bits,
            "tray_exist_bits": "%X" % tray_bits}


def moonraker_state(state):
    return {"printing": "RUNNING", "paused": "PAUSE", "complete": "FINISH",
            "cancelled": "FINISH", "error": "FAILED"}.get(state or "", "IDLE")


def build_status(status, model_id="", ams=None):
    """A push_status message from a Moonraker objects query."""
    stats = status.get("print_stats") or {}
    state = stats.get("state")
    print_ = {
        "command": "push_status", "msg": 0, "support_mqtt_alive": True,
        "gcode_state": moonraker_state(state),
        "mc_print_stage": {"printing": 1, "paused": 2, "complete": 3,
                           "error": 4}.get(state, 0),
        "mc_print_error_code": 0, "print_error": 0,
        "nozzle_temp_range": [100, 370], "bed_temp_range": [0, 120],
        "support_send_to_sd": True, "support_bed_leveling": 1,
        "sdcard": True,
    }
    if model_id:
        print_["printer_type"] = model_id
    homed = str((status.get("toolhead") or {}).get("homed_axes") or "").upper()
    print_["home_flag"] = (("X" in homed) * 1) | (("Y" in homed) * 2) | (("Z" in homed) * 4)
    for key, name in (("extruder", "nozzle"), ("heater_bed", "bed")):
        heater = status.get(key) or {}
        if isinstance(heater.get("temperature"), (int, float)):
            print_[name + "_temper"] = float(heater["temperature"])
        if isinstance(heater.get("target"), (int, float)):
            print_[name + "_target_temper"] = float(heater["target"])
    fan = status.get("fan") or {}
    if isinstance(fan.get("speed"), (int, float)):
        print_["fan_gear"] = max(0, min(255, int(fan["speed"] * 255 + 0.5)))
    if stats.get("filename"):
        print_["subtask_name"] = print_["gcode_file"] = stats["filename"]
    progress = (status.get("virtual_sdcard") or {}).get("progress")
    if isinstance(progress, (int, float)) and progress >= 0:
        print_["mc_percent"] = max(0, min(100, int(progress * 100 + 0.5)))
    total, elapsed = stats.get("total_duration"), stats.get("print_duration")
    if isinstance(total, (int, float)) and isinstance(elapsed, (int, float)) and total > 0:
        print_["mc_remaining_time"] = max(0, int((total - elapsed) / 60))
    if ams is not None:
        print_["ams"] = ams
    return {"print": print_, "t_utc": int(time.time() * 1000)}


def parse_slot_map(ams_mapping, ams_mapping2="", physical_slots=()):
    """{Orca filament (G-code tool) -> Kalico slot} from the print dialog.

    ams_mapping lists one tray per project filament: ams_id * 4 + slot_id,
    or -1 for a filament the plate does not use; ams_mapping2 has the same
    as {"ams_id", "slot_id"} pairs. Trays that are not CFS slots (external
    spool 254/255) are dropped.
    """
    valid = set(physical_slots)

    def accept(tool, slot, out):
        if isinstance(slot, int) and slot >= 0 and (not valid or slot in valid):
            out[tool] = slot

    mapping = {}
    try:
        values = json.loads(ams_mapping) if ams_mapping else []
    except (TypeError, ValueError):
        values = []
    if isinstance(values, list):
        for tool, value in enumerate(values):
            try:
                accept(tool, int(value), mapping)
            except (TypeError, ValueError):
                continue
    if mapping:
        return mapping
    try:
        pairs = json.loads(ams_mapping2) if ams_mapping2 else []
    except (TypeError, ValueError):
        pairs = []
    if isinstance(pairs, list):
        for tool, pair in enumerate(pairs):
            if not isinstance(pair, dict):
                continue
            try:
                ams_id, slot_id = int(pair.get("ams_id")), int(pair.get("slot_id"))
            except (TypeError, ValueError):
                continue
            if 0 <= ams_id < 64 and 0 <= slot_id < SLOTS_PER_BOX:
                accept(tool, ams_id * SLOTS_PER_BOX + slot_id, mapping)
    return mapping


def print_start_script(filename, mapping, used_tools):
    """The G-code that starts the print, and an error when the map is short.

    Kalico refuses a map that does not cover exactly the tools the file uses,
    so the map is cut to those tools; a used tool without a slot is an error.
    """
    if not used_tools:
        return "SDCARD_PRINT_FILE FILENAME=\"%s\"" % filename, None
    missing = sorted(set(used_tools) - set(mapping))
    if missing:
        return None, ("OrcaSlicer did not map %s to a CFS slot"
                      % ", ".join("T%d" % tool for tool in missing))
    pairs = ",".join("%d:%d" % (tool, mapping[tool]) for tool in sorted(used_tools))
    return "BOX_PRINT_START FILENAME=\"%s\" MAP=\"%s\"" % (filename, pairs), None


def safe_filename(name):
    base = os.path.basename(str(name or "").replace("\\", "/")) or "orca_print.gcode"
    base = "".join(c if c.isalnum() or c in " ._-()+@" else "_" for c in base).strip()
    if not base.lower().endswith(".gcode"):
        base += ".gcode"
    return base


# ----------------------------------------------------------------------------
# Moonraker client
# ----------------------------------------------------------------------------

class Moonraker:
    def __init__(self, host, port="", api_key="", use_ssl=False):
        self.host = host
        self.port = int(port) if str(port or "").isdigit() else (443 if use_ssl else 80)
        self.api_key = "" if api_key in PLACEHOLDER_KEYS else api_key
        self.use_ssl = use_ssl

    def _connection(self, timeout):
        if self.use_ssl:
            return http.client.HTTPSConnection(
                self.host, self.port, timeout=timeout,
                context=ssl.create_default_context())
        return http.client.HTTPConnection(self.host, self.port, timeout=timeout)

    def _headers(self, extra=None):
        headers = dict(extra or {})
        if self.api_key:
            headers["X-Api-Key"] = self.api_key
        return headers

    def request(self, method, path, body=None, timeout=10.0):
        conn = self._connection(timeout)
        try:
            data = None if body is None else json.dumps(body).encode()
            headers = self._headers(
                {"Content-Type": "application/json"} if data is not None else None)
            conn.request(method, path, body=data, headers=headers)
            resp = conn.getresponse()
            raw = resp.read()
        finally:
            conn.close()
        try:
            payload = json.loads(raw.decode("utf-8", "replace")) if raw else {}
        except ValueError:
            payload = {}
        if resp.status != 200:
            error = payload.get("error") if isinstance(payload, dict) else None
            message = (error or {}).get("message") if isinstance(error, dict) else None
            raise RuntimeError(message or "HTTP %d" % resp.status)
        return payload.get("result", payload) if isinstance(payload, dict) else payload

    def server_info(self):
        return self.request("GET", "/server/info", timeout=5.0)

    def query(self, objects):
        query = "&".join(
            name if fields is None else "%s=%s" % (name, fields)
            for name, fields in objects)
        return self.request("GET", "/printer/objects/query?" + query,
                            timeout=5.0).get("status", {})

    def gcode(self, script, timeout=60.0):
        return self.request("POST", "/printer/gcode/script",
                            {"script": script}, timeout=timeout)

    def upload(self, path, filename, progress=None, cancelled=None):
        boundary = "----k2oh" + uuid.uuid4().hex
        head = ("--%s\r\nContent-Disposition: form-data; name=\"root\"\r\n\r\ngcodes\r\n"
                "--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"%s\"\r\n"
                "Content-Type: application/octet-stream\r\n\r\n"
                % (boundary, boundary, filename)).encode()
        tail = ("\r\n--%s--\r\n" % boundary).encode()
        size = os.path.getsize(path)
        conn = self._connection(300.0)
        try:
            conn.putrequest("POST", "/server/files/upload")
            for key, value in self._headers({
                    "Content-Type": "multipart/form-data; boundary=" + boundary,
                    "Content-Length": str(len(head) + size + len(tail))}).items():
                conn.putheader(key, value)
            conn.endheaders()
            conn.send(head)
            sent = 0
            with open(path, "rb") as handle:
                while True:
                    if cancelled is not None and cancelled():
                        return False
                    chunk = handle.read(256 * 1024)
                    if not chunk:
                        break
                    conn.send(chunk)
                    sent += len(chunk)
                    if progress is not None and size:
                        progress(int(sent * 100 / size))
            conn.send(tail)
            resp = conn.getresponse()
            resp.read()
            if resp.status not in (200, 201):
                raise RuntimeError("upload HTTP %d" % resp.status)
            return True
        finally:
            conn.close()


# ----------------------------------------------------------------------------
# OrcaSlicer printer agent
# ----------------------------------------------------------------------------

_AgentBase = orca.printer_agent.PrinterAgentBase if orca is not None else object


def _call(fn, *args):
    if fn is None:
        return None
    try:
        return fn(*args)
    except Exception as exc:  # a callback must never kill the agent thread
        log("callback failed: %s", exc)
        return None


class K2OpenHostCfsAgent(_AgentBase):
    def __init__(self):
        super().__init__()
        self._lock = threading.RLock()
        self._client = None
        self._dev_id = ""
        self._dev_name = ""
        self._version = ""
        self._selected = ""
        self._model_id = ""
        self._generation = 0
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._thread = None
        self._callbacks = {}
        self._last_ams = None
        self._last_full = 0.0
        self._slots = []

    # -- plugin metadata ----------------------------------------------------
    def get_name(self):
        return AGENT_NAME

    def get_default_config(self):
        return dict(DEFAULTS)

    def _config(self):
        config = dict(DEFAULTS)
        try:
            config.update(json.loads(self.get_config()))
        except Exception:
            pass
        return config

    def get_agent_info(self):
        return orca.printer_agent.AgentInfo(
            AGENT_ID, AGENT_NAME, AGENT_VERSION,
            "Creality K2 with K2-OpenHost (Kalico + Moonraker): CFS slot sync "
            "by filament id and mapped print start")

    def get_filament_sync_mode(self):
        return orca.printer_agent.FilamentSyncMode.Subscription

    def get_camera_stream_mode(self):
        return orca.printer_agent.CameraStreamMode.None_

    # -- callbacks ---------------------------------------------------------
    def _set_callback(self, name, fn):
        with self._lock:
            self._callbacks[name] = fn
        return SUCCESS

    def set_server_callback(self, fn):
        return self._set_callback("server_err", fn)

    def set_on_ssdp_msg_fn(self, fn):
        return self._set_callback("ssdp", fn)

    def set_on_printer_connected_fn(self, fn):
        return self._set_callback("connected", fn)

    def set_on_subscribe_failure_fn(self, fn):
        return self._set_callback("subscribe_failure", fn)

    def set_on_message_fn(self, fn):
        return self._set_callback("message", fn)

    def set_on_user_message_fn(self, fn):
        return self._set_callback("user_message", fn)

    def set_on_local_connect_fn(self, fn):
        return self._set_callback("local_connect", fn)

    def set_on_local_message_fn(self, fn):
        return self._set_callback("local_message", fn)

    def set_queue_on_main_fn(self, fn):
        return self._set_callback("queue_on_main", fn)

    def _dispatch(self, payload):
        with self._lock:
            dev_id = self._dev_id
            fn = self._callbacks.get("local_message") or self._callbacks.get("message")
        if dev_id:
            _call(fn, dev_id, json.dumps(payload))

    # -- connection --------------------------------------------------------
    def _resolve_model_id(self):
        configured = str(self._config().get("model_id") or "").strip()
        if configured:
            return configured
        try:
            preset = orca.host.preset_bundle().current_printer_preset()
            model = str(preset.config_value("printer_model") or "").strip().strip('"')
            return model.replace(" ", "_")
        except Exception:
            return ""

    def connect_printer(self, params):
        if not params.dev_id or not params.host:
            return ERR_INVALID_HANDLE
        self.disconnect_printer()
        with self._lock:
            self._generation += 1
            generation = self._generation
            self._dev_id = params.dev_id
            self._dev_name = params.dev_id
            self._client = Moonraker(params.host, params.port, params.password,
                                     bool(params.use_ssl))
            self._model_id = self._resolve_model_id()
            self._last_ams = None
            self._stop = threading.Event()
            self._wake = threading.Event()
            self._thread = threading.Thread(
                target=self._run, args=(generation, self._stop), daemon=True,
                name="k2oh-cfs-agent")
            self._thread.start()
        return SUCCESS

    def disconnect_printer(self):
        with self._lock:
            self._generation += 1
            self._stop.set()
            self._wake.set()
        return SUCCESS

    def _current(self, generation):
        with self._lock:
            return generation == self._generation

    def _announce_connected(self, client):
        """Report the connection once Moonraker answers; False until then.

        The first attempt can be refused: OrcaSlicer asks the user before a
        plugin opens its first network connection, and denies the attempt
        that triggered the question. So this is retried by the poll loop.
        """
        try:
            info = client.server_info()
        except Exception as exc:
            log("Moonraker not reachable yet: %s", exc)
            return False
        with self._lock:
            self._dev_name = info.get("machine_name") or info.get("hostname") or self._dev_id
            self._version = info.get("moonraker_version", "")
            local_fn = self._callbacks.get("local_connect")
            connected_fn = self._callbacks.get("connected")
            dev_id = self._dev_id
        _call(local_fn, CONNECT_OK, dev_id, "0")
        _call(connected_fn, dev_id)
        self._send_version_info()
        return True

    def _run(self, generation, stop):
        client = self._client
        connected = False
        while not stop.is_set() and self._current(generation):
            if not connected:
                connected = self._announce_connected(client)
            if connected:
                self._poll(force_ams=False)
            interval = max(0.5, float(self._config().get("poll_interval_s") or 2.0))
            self._wake.wait(interval)
            self._wake.clear()

    def _poll(self, force_ams):
        client = self._client
        if client is None:
            return
        try:
            status = client.query([(name, None) for name in STATUS_OBJECTS]
                                  + [("box", BOX_FIELDS)])
        except Exception as exc:
            log("status query failed: %s", exc)
            return
        box = status.get("box") or {}
        slots = box.get("slots") or []
        ams = build_ams(slots, box.get("boxes"))
        now = time.monotonic()
        with self._lock:
            self._slots = slots
            send_ams = (force_ams or ams != self._last_ams
                        or now - self._last_full >= FULL_PUSH_EVERY_S)
            if send_ams:
                self._last_ams = ams
                self._last_full = now
            model_id = self._model_id
        self._dispatch(build_status(status, model_id, ams if send_ams else None))

    def _send_version_info(self):
        self._dispatch({"info": {"command": "get_version", "result": "success",
                                 "module": [{"name": "ota", "sw_ver": self._version or "1.0.0",
                                             "product_name": "K2-OpenHost"}]}})

    # -- discovery and binding --------------------------------------------
    def start_discovery(self, start, sending):
        if not start:
            return True
        with self._lock:
            fn, dev_id, client = self._callbacks.get("ssdp"), self._dev_id, self._client
            name, model = self._dev_name, self._model_id
        if fn is not None and dev_id and client is not None:
            _call(fn, json.dumps({
                "dev_name": name or dev_id, "dev_id": dev_id, "dev_ip": dev_id,
                "dev_type": model or name or dev_id, "dev_signal": "0",
                "connect_type": "lan", "bind_state": "free",
                "sec_link": "secure", "ssdp_version": "v1"}))
            with self._lock:
                self._selected = self._selected or dev_id
        return True

    def bind_detect(self, dev_ip, sec_link, detect):
        with self._lock:
            detect.dev_id = self._dev_id or dev_ip
            detect.dev_name = self._dev_name or dev_ip
            detect.model_id = self._model_id
            detect.version = self._version
        detect.connect_type = "lan"
        detect.bind_state = "free"
        return SUCCESS

    def get_user_selected_machine(self):
        with self._lock:
            return self._selected

    def set_user_selected_machine(self, dev_id):
        with self._lock:
            self._selected = dev_id
        return SUCCESS

    # -- commands from the Device tab -------------------------------------
    def send_message(self, dev_id, json_str, qos, flag):
        return self._handle(json_str)

    def send_message_to_printer(self, dev_id, json_str, qos, flag):
        return self._handle(json_str)

    def _gcode_async(self, script, reply=None):
        def run():
            ok = True
            try:
                self._client.gcode(script)
            except Exception as exc:
                ok = False
                log("G-code %r failed: %s", script, exc)
            if reply is not None:
                reply["print"]["result"] = "success" if ok else "failed"
                self._dispatch(reply)
        threading.Thread(target=run, daemon=True).start()

    def _handle(self, json_str):
        try:
            request = json.loads(json_str)
        except ValueError:
            return ERR_INVALID_HANDLE
        if (request.get("info") or {}).get("command") == "get_version":
            self._send_version_info()
            return SUCCESS
        if (request.get("system") or {}).get("command") == "get_access_code":
            client = self._client
            self._dispatch({"system": {"command": "get_access_code",
                                       "access_code": client.api_key if client else ""}})
            return SUCCESS
        print_ = request.get("print") or {}
        command = print_.get("command")
        if self._client is None or not isinstance(command, str):
            return SUCCESS
        if command in ("pushall", "push_all"):
            with self._lock:
                self._last_ams = None
            self._wake.set()
        elif command == "gcode_line" and isinstance(print_.get("param"), str):
            reply = {"print": {"command": "gcode_line", "param": print_["param"]}}
            if isinstance(print_.get("sequence_id"), str):
                reply["print"]["sequence_id"] = print_["sequence_id"]
            self._gcode_async(print_["param"], reply)
        elif command in ("pause", "resume", "stop"):
            self._gcode_async({"pause": "PAUSE", "resume": "RESUME",
                               "stop": "CANCEL_PRINT"}[command])
        elif command == "set_bed_temp" and isinstance(print_.get("temp"), (int, float)):
            self._gcode_async("SET_HEATER_TEMPERATURE HEATER=heater_bed TARGET=%d"
                              % int(print_["temp"]))
        elif command == "set_nozzle_temp" and isinstance(print_.get("target_temp"), (int, float)):
            self._gcode_async("SET_HEATER_TEMPERATURE HEATER=extruder TARGET=%d"
                              % int(print_["target_temp"]))
        elif command == "home":
            self._gcode_async("G28")
        return SUCCESS

    # -- filament sync ------------------------------------------------------
    def fetch_filament_info(self, dev_id, sync_mode):
        self._poll(force_ams=True)
        return True

    # -- printing ------------------------------------------------------------
    def _gcode_path(self, params):
        path = params.dst_file or params.filename
        return path if path and os.path.isfile(path) else ""

    def _upload(self, params, update_fn, cancel_fn):
        path = self._gcode_path(params)
        if not path:
            log("G-code file not found: %r / %r", params.dst_file, params.filename)
            return None, ERR_FILE_NOT_EXIST
        name = safe_filename(path if path.lower().endswith(".gcode")
                             else (params.task_name or path))
        _call(update_fn, STAGE_UPLOAD, 0, "Uploading G-code...")
        try:
            done = self._client.upload(
                path, name,
                progress=lambda pct: _call(update_fn, STAGE_UPLOAD, pct, "Uploading G-code..."),
                cancelled=cancel_fn)
        except Exception as exc:
            log("upload failed: %s", exc)
            _call(update_fn, STAGE_ERROR, 0, "Upload failed: %s" % exc)
            return None, ERR_UPLOAD_FAILED
        if not done:
            return None, ERR_CANCELED
        return name, SUCCESS

    def _used_tools(self, filename):
        """Tools the file uses, from Kalico's BOX_PRINT_INFO."""
        self._client.gcode('BOX_PRINT_INFO FILENAME="%s"' % filename)
        info = (self._client.query([("box", "print_info")]).get("box") or {}).get("print_info") or {}
        if info.get("filename") not in (None, filename):
            return []
        return sorted({int(t["tool"]) for t in info.get("tools") or []
                       if isinstance(t, dict) and isinstance(t.get("tool"), int)})

    def start_local_print(self, params, update_fn, cancel_fn):
        if self._client is None:
            return ERR_INVALID_HANDLE
        _call(update_fn, STAGE_CREATE, 0, "Preparing...")
        name, code = self._upload(params, update_fn, cancel_fn)
        if code != SUCCESS:
            return code
        if cancel_fn is not None and _call(cancel_fn):
            return ERR_CANCELED
        _call(update_fn, STAGE_SENDING, 0, "Starting print...")
        with self._lock:
            physical = [s["index"] for s in self._slots
                        if not s.get("external") and isinstance(s.get("index"), int)]
        mapping = {}
        if params.task_use_ams and self._config().get("use_slot_map", True):
            mapping = parse_slot_map(params.ams_mapping, params.ams_mapping2, physical)
        try:
            if mapping:
                script, error = print_start_script(name, mapping, self._used_tools(name))
                if error:
                    log(error)
                    _call(update_fn, STAGE_ERROR, 0, error)
                    return ERR_START_FAILED
                log("starting %s with %s", name, script)
                self._client.gcode(script, timeout=120.0)
            else:
                log("starting %s without a slot map (Kalico maps it)", name)
                self._client.request("POST", "/printer/print/start", {"filename": name})
        except Exception as exc:
            log("print start failed: %s", exc)
            _call(update_fn, STAGE_ERROR, 0, "Print start failed: %s" % exc)
            return ERR_START_FAILED
        _call(update_fn, STAGE_FINISHED, 100, "Print started")
        return SUCCESS

    def start_local_print_with_record(self, params, update_fn, cancel_fn, wait_fn):
        return self.start_local_print(params, update_fn, cancel_fn)

    def start_print(self, params, update_fn, cancel_fn, wait_fn):
        return self.start_local_print(params, update_fn, cancel_fn)

    def start_sdcard_print(self, params, update_fn, cancel_fn):
        return self.start_local_print(params, update_fn, cancel_fn)

    def start_send_gcode_to_sdcard(self, params, update_fn, cancel_fn, wait_fn):
        if self._client is None:
            return ERR_INVALID_HANDLE
        _call(update_fn, STAGE_CREATE, 0, "Preparing...")
        name, code = self._upload(params, update_fn, cancel_fn)
        if code == SUCCESS:
            _call(update_fn, STAGE_FINISHED, 100, "File uploaded: %s" % name)
        return code


# ----------------------------------------------------------------------------
# CFS slot panel and G-code map: the slot choice without OrcaSlicer's global
# "Use printer agents" switch. The panel stores a filament -> slot map; the
# post-processing step writes it at the top of the G-code as
# "; K2OH_TOOL_MAP = tool:slot,..." and Kalico's box_print_mapping uses it
# when the print starts (upload and print, or a later start from Mainsail).
# ----------------------------------------------------------------------------

TOOL_MAP_KEY = "K2OH_TOOL_MAP"
FOOTER_BYTES = 1024 * 1024
_map_lock = threading.Lock()
# {"printer": preset name, "filaments": [preset names], "map": {tool: slot}}
_slot_map = {}


def config_list(value):
    """A serialized OrcaSlicer list option ('"A";"B"' or '#FF0000;#00FF00')."""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value]
    return [part.strip().strip('"') for part in str(value).split(";")]


def config_text(value):
    if isinstance(value, (list, tuple)):
        value = value[0] if value else ""
    return str(value or "").strip().strip('"')


def parse_host(print_host, port=""):
    """(host, port, use_ssl) from a print host field such as http://h:7125."""
    text = config_text(print_host)
    use_ssl = text.lower().startswith("https://")
    for prefix in ("http://", "https://"):
        if text.lower().startswith(prefix):
            text = text[len(prefix):]
    text = text.split("/", 1)[0]
    host, sep, inline_port = text.rpartition(":")
    if not sep or not inline_port.isdigit():
        host, inline_port = text, ""
    return host, inline_port or config_text(port), use_ssl


def _rgb(color):
    text = str(color or "").lstrip("#")
    try:
        return tuple(int(text[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return None


def color_distance(a, b):
    ra, rb = _rgb(a), _rgb(b)
    if ra is None or rb is None:
        return 3 * 255 ** 2
    return sum((x - y) ** 2 for x, y in zip(ra, rb))


def propose_map(filaments, slots):
    """{tool: slot}: same material, then the closest colour; else nothing."""
    loaded = [s for s in slots if s.get("present") and not s.get("external")
              and str(s.get("material") or "").strip()]
    mapping = {}
    for tool, filament in enumerate(filaments):
        material = str(filament.get("type") or "").strip().upper()
        same = [s for s in loaded
                if str(s["material"]).strip().upper() == material]
        if same:
            best = min(same, key=lambda s: (color_distance(filament.get("color"), s.get("color")),
                                            s["index"]))
            mapping[tool] = best["index"]
    return mapping


def used_tools_from_footer(path):
    """Tools with filament used > 0, from the file's OrcaSlicer footer."""
    with open(path, "rb") as handle:
        size = os.fstat(handle.fileno()).st_size
        handle.seek(max(0, size - FOOTER_BYTES))
        tail = handle.read().decode("utf-8", "replace")
    for line in tail.splitlines():
        stripped = line.lstrip("; \t")
        if stripped.startswith("filament used [mm]"):
            values = stripped.split("=", 1)[1].split(",") if "=" in stripped else []
            used = []
            for tool, value in enumerate(values):
                try:
                    if float(value) > 0:
                        used.append(tool)
                except ValueError:
                    return []
            return used
    return []


def map_line(mapping, used_tools):
    """The K2OH_TOOL_MAP line, or (None, missing tools)."""
    missing = [tool for tool in used_tools if tool not in mapping]
    if missing or not used_tools:
        return None, missing
    pairs = ",".join("%d:%d" % (tool, mapping[tool]) for tool in used_tools)
    return "; %s = %s\n" % (TOOL_MAP_KEY, pairs), []


def insert_after_first_line(path, line):
    """Insert line after the first line of path, streaming (files can be large).

    No-op when a K2OH_TOOL_MAP line is already there: the post-processing
    step can run more than once on the same export.
    """
    marker = TOOL_MAP_KEY.encode()
    tmp = path + ".k2oh-tmp"
    with open(path, "rb") as src:
        first = src.readline()
        second = src.readline()
        if marker in second:
            return False
        with open(tmp, "wb") as dst:
            dst.write(first)
            dst.write(line.encode("utf-8"))
            dst.write(second)
            while True:
                chunk = src.read(1024 * 1024)
                if not chunk:
                    break
                dst.write(chunk)
    os.replace(tmp, path)
    return True


def store_slot_map(printer, filaments, mapping):
    with _map_lock:
        _slot_map.clear()
        _slot_map.update({"printer": printer, "filaments": list(filaments),
                          "map": {int(t): int(s) for t, s in mapping.items()}})


def stored_slot_map():
    with _map_lock:
        return {"printer": _slot_map.get("printer"),
                "filaments": list(_slot_map.get("filaments") or []),
                "map": dict(_slot_map.get("map") or {})}


def write_tool_map(gcode_path, printer, filament_names):
    """Post-processing: write the panel's map into gcode_path.

    Returns a short message. The map is written only for the printer and
    filament list it was chosen for, and only when every tool the file uses
    has a slot; otherwise Kalico maps the print automatically.
    """
    state = stored_slot_map()
    if not state["map"]:
        return "no slot map chosen"
    if state["printer"] != printer:
        return "slot map chosen for %r, not %r" % (state["printer"], printer)
    if state["filaments"] != list(filament_names):
        return "the filaments changed after the slot map was chosen: refresh the CFS panel"
    line, missing = map_line(state["map"], used_tools_from_footer(gcode_path))
    if line is None:
        return ("no slot for %s: Kalico maps the print automatically"
                % ", ".join("T%d" % t for t in missing) if missing else "no tools used")
    insert_after_first_line(gcode_path, line)
    return "wrote " + line.strip()


TEXT = {
    "en": {"title": "CFS slots", "auto": "Kalico decides", "refresh": "Refresh",
           "propose": "Propose", "note": "Choose a CFS slot for each filament, then slice and send. "
           "Filaments without a slot: Kalico maps the whole print automatically.",
           "pick": "Click a filament, then the spool it should print from.",
           "empty": "empty",
           "runout": "Runout order", "swap": "Switch to an identical spool when one runs out",
           "no_groups": "No group: runout needs at least two identical spools (same material and colour).",
           "manual": "manual order", "lowest": "lowest remaining first", "slot_order": "slot order",
           "auto_order": "Automatic order",
           "no_host": "Set the Moonraker address in the printer preset (print host).",
           "printer": "Printer"},
    "it": {"title": "Slot CFS", "auto": "Decide Kalico", "refresh": "Aggiorna",
           "propose": "Proponi", "note": "Scegli uno slot CFS per ogni filamento, poi fai slicing e invia. "
           "Se un filamento usato resta senza slot, Kalico abbina tutta la stampa da solo.",
           "pick": "Clicca un filamento, poi la bobina da cui deve stampare.",
           "empty": "vuoto",
           "runout": "Ordine di runout", "swap": "Passa a una bobina uguale quando una finisce",
           "no_groups": "Nessun gruppo: il runout richiede almeno due bobine uguali (stesso materiale e colore).",
           "manual": "ordine manuale", "lowest": "prima la bobina con meno residuo", "slot_order": "ordine degli slot",
           "auto_order": "Ordine automatico",
           "no_host": "Imposta l'indirizzo di Moonraker nel preset stampante (host di stampa).",
           "printer": "Stampante"},
}


def _language():
    try:
        info = orca.host.app_info()
        lang = info.get("language") if isinstance(info, dict) else getattr(info, "language", "")
        return "it" if str(lang or "").lower().startswith("it") else "en"
    except Exception:
        return "en"


PANEL_PAGE = """
<style>
  body { margin: 0; padding: 10px; font-size: 13px; }
  h3 { margin: 0 0 4px; font-size: 14px; }
  .note { margin: 0 0 8px; color: var(--orca-muted); font-size: 12px; }
  .actions { display: flex; gap: 6px; margin-bottom: 10px; }
  .cfs { border: 1px solid var(--orca-border); border-radius: 12px; padding: 8px 8px 10px;
         margin-bottom: 10px; background: rgba(127,127,127,0.08); }
  .cfs-head { display: flex; justify-content: space-between; font-weight: 600; margin-bottom: 6px; }
  .cfs-head span.env { font-weight: 400; color: var(--orca-muted); font-size: 12px; }
  .bays { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 6px; }
  .bay { border: 2px solid transparent; border-radius: 10px; padding: 4px 2px 6px; text-align: center;
         cursor: pointer; background: rgba(0,0,0,0.12); position: relative; min-width: 0; }
  .bay.empty { cursor: default; opacity: 0.55; }
  .bay.target { border-color: var(--orca-accent, #00ae42); }
  .bay svg { width: 100%; max-width: 64px; height: auto; display: block; margin: 0 auto; }
  .num { font-weight: 700; font-size: 12px; }
  .mat { font-size: 11px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .nm { font-size: 10px; color: var(--orca-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .bar { height: 4px; border-radius: 2px; background: rgba(127,127,127,0.3); margin: 3px 6px 0; overflow: hidden; }
  .bar i { display: block; height: 100%; background: var(--orca-accent, #00ae42); }
  .tags { position: absolute; top: 2px; left: 2px; right: 2px; display: flex; flex-wrap: wrap; gap: 2px; }
  .tag { font-size: 10px; font-weight: 700; padding: 0 4px; border-radius: 6px; border: 1px solid rgba(0,0,0,0.4); }
  .fil { display: flex; align-items: center; gap: 6px; padding: 5px 6px; margin: 4px 0; border-radius: 8px;
         border: 2px solid var(--orca-border); cursor: pointer; }
  .fil.sel { border-color: var(--orca-accent, #00ae42); }
  .sw { width: 16px; height: 16px; border-radius: 50%; border: 1px solid rgba(0,0,0,0.4); flex: none; }
  .fname { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .dest { font-weight: 600; white-space: nowrap; }
  .clr { border: none; background: transparent; color: var(--orca-muted); cursor: pointer; padding: 0 4px; }
  #status { margin-top: 8px; color: var(--orca-muted); font-size: 12px; }
  h4 { margin: 14px 0 6px; font-size: 13px; }
  .swap { display: flex; gap: 6px; align-items: center; margin-bottom: 8px; }
  .grp { border: 1px solid var(--orca-border); border-radius: 10px; padding: 6px 8px; margin-bottom: 8px; }
  .grp-head { display: flex; align-items: center; gap: 6px; font-weight: 600; margin-bottom: 4px; }
  .grp-head small { font-weight: 400; color: var(--orca-muted); }
  .ro { display: flex; align-items: center; gap: 6px; margin: 3px 0; }
  .ro .pos { width: 16px; text-align: right; font-weight: 700; }
  .ro .lbl { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .ro button, .grp .auto { padding: 0 6px; }
</style>
<h3 id="title"></h3>
<p class="note" id="note"></p>
<div class="actions">
  <button type="button" id="refresh"></button>
  <button type="button" id="propose"></button>
</div>
<div id="units"></div>
<div id="fils"></div>
<p id="status"></p>
<div id="runout"></div>
<script>
(function () {
  var m = null, sel = null;
  function esc(v) { var s = document.createElement("span"); s.textContent = v == null ? "" : v; return s.innerHTML; }
  function lum(hex) {
    var h = String(hex || "").replace("#", "");
    if (h.length < 6) return 0.5;
    var r = parseInt(h.substr(0, 2), 16), g = parseInt(h.substr(2, 2), 16), b = parseInt(h.substr(4, 2), 16);
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  }
  function spool(color, empty) {
    if (empty) {
      return '<svg viewBox="0 0 64 64"><circle cx="32" cy="32" r="27" fill="none" stroke="currentColor" ' +
             'stroke-opacity="0.5" stroke-width="2" stroke-dasharray="5 4"/><circle cx="32" cy="32" r="8" ' +
             'fill="none" stroke="currentColor" stroke-opacity="0.5" stroke-width="2"/></svg>';
    }
    var c = esc(color || "#888888");
    return '<svg viewBox="0 0 64 64">' +
      '<circle cx="32" cy="32" r="30" fill="#2b2b2b" stroke="#555" stroke-width="1.5"/>' +
      '<circle cx="32" cy="32" r="26" fill="' + c + '"/>' +
      '<circle cx="32" cy="32" r="26" fill="none" stroke="rgba(0,0,0,0.18)" stroke-width="1" stroke-dasharray="2 3"/>' +
      '<circle cx="32" cy="32" r="13" fill="#3a3a3a" stroke="#666" stroke-width="1.5"/>' +
      '<circle cx="32" cy="32" r="5" fill="#1e1e1e"/></svg>';
  }
  function slotName(index) { return "CFS" + (Math.floor(index / 4) + 1) + "·" + (index % 4 + 1); }
  function render() {
    var t = m.text;
    document.getElementById("title").textContent = t.title;
    document.getElementById("note").textContent = t.note;
    document.getElementById("refresh").textContent = t.refresh;
    document.getElementById("propose").textContent = t.propose;
    var units = document.getElementById("units"), fils = document.getElementById("fils");
    if (m.error) { units.innerHTML = ""; fils.innerHTML = ""; document.getElementById("status").textContent = m.error; return; }
    var byFil = {};
    m.filaments.forEach(function (f) { byFil[f.index] = f; });
    units.innerHTML = m.units.map(function (u) {
      var env = [];
      if (u.temp_c != null) env.push(u.temp_c + "°C");
      if (u.humidity_pct != null) env.push(u.humidity_pct + "%RH");
      return '<div class="cfs"><div class="cfs-head"><span>CFS ' + u.address + '</span><span class="env">' +
        esc(env.join(" · ")) + '</span></div><div class="bays">' + u.slots.map(function (s) {
          var loaded = s.present && s.material;
          var tags = Object.keys(m.map).filter(function (k) { return m.map[k] === s.index; }).map(function (k) {
            var f = byFil[k] || {}; var fg = lum(f.color) > 0.6 ? "#000" : "#fff";
            return '<span class="tag" style="background:' + esc(f.color) + ';color:' + fg + '">T' + (Number(k) + 1) + '</span>';
          }).join("");
          var bar = (loaded && s.percent != null) ? '<div class="bar" title="' + Math.round(s.percent) + '%"><i style="width:' +
            Math.max(0, Math.min(100, s.percent)) + '%"></i></div>' : "";
          return '<div class="bay' + (loaded ? "" : " empty") + (loaded && sel !== null ? " target" : "") +
            '" data-slot="' + s.index + '" title="' + esc(s.name || "") + '"><div class="tags">' + tags + '</div>' +
            spool(s.color, !loaded) + '<div class="num">' + s.local + '</div>' +
            '<div class="mat">' + esc(loaded ? s.material : t.empty) + '</div>' +
            '<div class="nm">' + esc(loaded ? (s.name || "") : "") + '</div>' +
            (loaded && s.percent != null ? '<div class="nm">' + Math.round(s.percent) + '%</div>' : "") + bar + '</div>';
        }).join("") + '</div></div>';
    }).join("");
    fils.innerHTML = '<p class="note">' + esc(t.pick) + '</p>' + m.filaments.map(function (f) {
      var slot = m.map[f.index];
      var dest = slot == null ? t.auto : slotName(slot);
      return '<div class="fil' + (sel === f.index ? " sel" : "") + '" data-tool="' + f.index + '">' +
        '<span class="sw" style="background:' + esc(f.color) + '"></span>' +
        '<span class="fname" title="' + esc(f.name) + '"><b>T' + (f.index + 1) + '</b> ' + esc(f.name) +
        ' <small>(' + esc(f.type) + ')</small></span><span class="dest">→ ' + esc(dest) + '</span>' +
        (slot == null ? "" : '<button class="clr" data-clear="' + f.index + '" title="' + esc(t.auto) + '">✕</button>') + '</div>';
    }).join("");
    Array.prototype.forEach.call(fils.querySelectorAll(".fil"), function (el) {
      el.addEventListener("click", function (ev) {
        var clear = ev.target.getAttribute("data-clear");
        if (clear !== null) { delete m.map[clear]; send(); render(); ev.stopPropagation(); return; }
        var tool = parseInt(el.getAttribute("data-tool"), 10);
        sel = (sel === tool) ? null : tool; render();
      });
    });
    Array.prototype.forEach.call(units.querySelectorAll(".bay"), function (el) {
      el.addEventListener("click", function () {
        if (sel === null || el.classList.contains("empty")) return;
        m.map[sel] = parseInt(el.getAttribute("data-slot"), 10);
        var next = m.filaments.filter(function (f) { return m.map[f.index] == null; })[0];
        sel = next ? next.index : null;
        send(); render();
      });
    });
    renderRunout();
    var done = m.filaments.filter(function (f) { return m.map[f.index] != null; }).length;
    document.getElementById("status").textContent = t.printer + ": " + m.printer + " · " + done + "/" + m.filaments.length;
  }
  function send() { orca.postMessage({ command: "set", map: m.map }); }
  function renderRunout() {
    var t = m.text, r = m.runout || { groups: [] }, box = document.getElementById("runout");
    var bays = {};
    (m.units || []).forEach(function (u) { u.slots.forEach(function (s) { bays[s.index] = s; }); });
    var label = { manual_order: t.manual, lowest_remaining_first: t.lowest, slot_order: t.slot_order };
    var html = '<h4>' + esc(t.runout) + '</h4><label class="swap"><input type="checkbox" id="swap"' +
      (r.swap ? " checked" : "") + '> ' + esc(t.swap) + '</label>';
    if (!r.groups.length) html += '<p class="note">' + esc(t.no_groups) + '</p>';
    html += r.groups.map(function (g, gi) {
      return '<div class="grp"><div class="grp-head"><span class="sw" style="background:' + esc(g.color) + '"></span>' +
        esc(g.material) + ' <small>' + esc(label[g.strategy] || g.strategy) + '</small></div>' +
        g.slots.map(function (slot, i) {
          var b = bays[slot] || {};
          var pct = b.percent != null ? " · " + Math.round(b.percent) + "%" : "";
          return '<div class="ro"><span class="pos">' + (i + 1) + '.</span><span class="sw" style="background:' +
            esc(b.color) + '"></span><span class="lbl">' + slotName(slot) + " " + esc(b.name || "") + pct + '</span>' +
            '<button data-g="' + gi + '" data-i="' + i + '" data-d="-1"' + (i === 0 ? " disabled" : "") + '>▲</button>' +
            '<button data-g="' + gi + '" data-i="' + i + '" data-d="1"' + (i === g.slots.length - 1 ? " disabled" : "") + '>▼</button></div>';
        }).join("") + (g.strategy === "manual_order" ? '<button class="auto" data-auto="' + gi + '">' + esc(t.auto_order) + '</button>' : "") +
        '</div>';
    }).join("");
    box.innerHTML = html;
    document.getElementById("swap").addEventListener("change", function (ev) {
      orca.postMessage({ command: "runout_swap", enable: ev.target.checked });
    });
    Array.prototype.forEach.call(box.querySelectorAll("button[data-d]"), function (el) {
      el.addEventListener("click", function () {
        var g = r.groups[+el.getAttribute("data-g")], i = +el.getAttribute("data-i"), j = i + (+el.getAttribute("data-d"));
        var order = g.slots.slice(); var x = order[i]; order[i] = order[j]; order[j] = x;
        orca.postMessage({ command: "runout_order", slots: order, manual: true });
      });
    });
    Array.prototype.forEach.call(box.querySelectorAll("button[data-auto]"), function (el) {
      el.addEventListener("click", function () {
        orca.postMessage({ command: "runout_order", slots: r.groups[+el.getAttribute("data-auto")].slots, manual: false });
      });
    });
  }
  orca.onMessage(function (msg) {
    if (msg && msg.command === "state") {
      m = msg; var fixed = {};
      Object.keys(m.map || {}).forEach(function (k) { fixed[k] = m.map[k]; });
      m.map = fixed; sel = null; render();
    }
  });
  document.getElementById("refresh").addEventListener("click", function () { orca.postMessage({ command: "refresh" }); });
  document.getElementById("propose").addEventListener("click", function () { orca.postMessage({ command: "propose" }); });
  orca.postMessage({ command: "refresh" });
})();
</script>
"""


def merged_runout_order(current, group_slots, manual=True):
    """Kalico's global runout order after changing one group of identical spools.

    Kalico ranks slots only against the other slots of their group, so the
    group's slots are taken out of the saved order and, for a manual order,
    appended in the new sequence. Without manual, the group goes back to
    Kalico's automatic order (lowest RFID remaining first).
    """
    group = [int(slot) for slot in group_slots]
    order = [int(slot) for slot in current or [] if int(slot) not in group]
    return order + group if manual else order


def runout_order_script(order):
    return "_BOX_SET_RUNOUT_ORDER ORDER=%s" % (
        ",".join(str(slot) for slot in order) if order else "AUTO")


def cfs_units(slots, boxes=()):
    """CFS units to draw: [{address, temp_c, humidity_pct, slots: [...]}]."""
    env = {b.get("address"): b for b in boxes or [] if isinstance(b.get("address"), int)}
    units = {}
    for slot in slots:
        index = slot["index"]
        address = index // SLOTS_PER_BOX + 1
        units.setdefault(address, {}).setdefault(index, slot)
    result = []
    for address in sorted(units):
        box = env.get(address) or {}
        bays = []
        for local in range(SLOTS_PER_BOX):
            index = (address - 1) * SLOTS_PER_BOX + local
            slot = units[address].get(index) or {}
            percent = slot.get("rfid_percent")
            bays.append({
                "index": index, "local": local + 1,
                "present": bool(slot.get("present")),
                "material": str(slot.get("material") or ""),
                "color": str(slot.get("color") or ""),
                "name": str(slot.get("name") or ""),
                "percent": float(percent) if isinstance(percent, (int, float)) else None,
            })
        result.append({"address": address, "temp_c": box.get("temp_c"),
                       "humidity_pct": box.get("humidity_pct"), "slots": bays})
    return result


def _slot_label(slot):
    index = int(slot["index"])
    name = str(slot.get("name") or "").strip()
    material = str(slot.get("material") or "").strip()
    return "CFS%d-%d  %s%s" % (index // SLOTS_PER_BOX + 1, index % SLOTS_PER_BOX + 1, material,
                               (" - " + name) if name and name != material else "")


_ScriptBase = orca.script.ScriptPluginCapabilityBase if orca is not None else object
_SlicingBase = orca.slicing.SlicingPipelineCapabilityBase if orca is not None else object


# Events after which the panel follows the selected printer and project, all
# fired on the GUI thread. SlicingJobComplete comes from the plater's
# "slicing finished" handler; the other slicing events run on the worker
# thread and are left out.
PANEL_EVENTS = ("PresetSelected", "PresetSaved", "ProjectOpened", "NewProject")
SLICED_EVENT = "SlicingJobComplete"


def is_k2oh_printer(printer):
    """The selected printer preset uses this plugin's agent."""
    try:
        return config_text(printer.config_value("printer_agent")) == AGENT_ID
    except Exception:
        return False


class K2OpenHostCfsPanel(_ScriptBase):
    """Opens the "CFS slots" panel beside the 3D view.

    It also opens by itself (option auto_open) after every successful slice
    for a printer using the K2-OpenHost CFS agent, the moment to check the
    slots before sending. When the printer preset, a preset save or the
    project changes, an open panel refreshes, and it hides for other
    printers.
    """

    panel = None
    _boxes = ()
    _runout = None

    def get_default_config(self):
        return {"auto_open": True}

    def _auto_open(self):
        try:
            return bool(json.loads(self.get_config()).get("auto_open", True))
        except Exception:
            return True

    def on_lifecycle_event(self, event, ctx):
        name = getattr(event, "name", str(event)).split(".")[-1]
        if name not in PANEL_EVENTS and name != SLICED_EVENT:
            return
        if name == SLICED_EVENT:
            code = getattr(getattr(ctx, "code", None), "name", "Ok")
            if code != "Ok":  # cancelled or failed slice
                return
        # UI calls only from the GUI thread, where these events come from.
        if threading.current_thread() is not threading.main_thread():
            return
        try:
            printer = orca.host.preset_bundle().current_printer_preset()
        except Exception:
            return
        is_open = self.panel is not None and self.panel.is_open()
        if not is_k2oh_printer(printer):
            if is_open:
                self.panel.hide()
            return
        if name == SLICED_EVENT and self._auto_open():
            if is_open:
                self.panel.show()
                self._post_state()
            else:
                log("opening the CFS panel after slicing")
                self.execute()
        elif is_open:
            self.panel.show()
            self._post_state()

    def _client(self, printer):
        host, port, use_ssl = parse_host(printer.config_value("print_host"),
                                         printer.config_value("printhost_port"))
        if not host:
            return None
        return Moonraker(host, port, config_text(printer.config_value("printhost_apikey")),
                         use_ssl)

    def get_name(self):
        return "K2-OpenHost CFS slots"

    def execute(self):
        if self.panel is not None and self.panel.is_open():
            self.panel.show()
            return orca.ExecutionResult.success("CFS slots panel already open")
        self.panel = orca.host.ui.create_dock_panel(
            html=PANEL_PAGE, title="CFS", width=340, height=420,
            on_message=self.on_message, on_close=self.on_close, dock="right")
        return orca.ExecutionResult.success("CFS slots panel opened")

    def on_close(self):
        self.panel = None

    def _project(self):
        bundle = orca.host.preset_bundle()
        printer = bundle.current_printer_preset()
        names = [str(n) for n in bundle.current_filament_preset_names()]
        colors = config_list(bundle.full_config_value("filament_colour"))
        types = config_list(bundle.full_config_value("filament_type"))
        filaments = [{"index": i, "name": name,
                      "color": colors[i] if i < len(colors) else "",
                      "type": types[i] if i < len(types) else ""}
                     for i, name in enumerate(names)]
        return printer, filaments

    def _slots(self, printer):
        client = self._client(printer)
        if client is None:
            return None
        box = client.query([("box", "slots,boxes,runout_order,runout_groups,"
                                       "runout_swap_enabled")]).get("box") or {}
        self._boxes = box.get("boxes") or []
        self._runout = {"swap": bool(box.get("runout_swap_enabled")),
                        "order": list(box.get("runout_order") or []),
                        "groups": [{"material": g.get("material"), "color": g.get("color"),
                                    "slots": list(g.get("slots") or []),
                                    "strategy": g.get("strategy")}
                                   for g in box.get("runout_groups") or []]}
        return [s for s in box.get("slots") or []
                if not s.get("external") and isinstance(s.get("index"), int)]

    def _post_state(self, propose=False):
        text = TEXT[_language()]
        message = {"command": "state", "text": text, "filaments": [], "slots": [],
                   "units": [], "map": {}, "printer": "", "summary": ""}
        try:
            printer, filaments = self._project()
            message["printer"] = printer.name
            message["filaments"] = filaments
            slots = self._slots(printer)
            if slots is None:
                message["error"] = text["no_host"]
            else:
                loaded = [s for s in slots if s.get("present") and s.get("material")]
                message["slots"] = [{"index": s["index"], "label": _slot_label(s)} for s in loaded]
                message["units"] = cfs_units(slots, self._boxes)
                message["runout"] = self._runout or {"swap": False, "order": [], "groups": []}
                state = stored_slot_map()
                names = [f["name"] for f in filaments]
                valid = {s["index"] for s in loaded}
                if propose or state["printer"] != printer.name or state["filaments"] != names:
                    mapping = propose_map(filaments, loaded)
                else:
                    mapping = {t: s for t, s in state["map"].items() if s in valid}
                store_slot_map(printer.name, names, mapping)
                message["map"] = {str(t): s for t, s in mapping.items()}
                message["summary"] = "%d/%d" % (len(mapping), len(filaments))
        except Exception as exc:
            log("CFS panel: %s", exc)
            message["error"] = str(exc)
        if self.panel is not None:
            self.panel.post(message)

    def on_message(self, message):
        command = (message or {}).get("command")
        if command == "refresh":
            self._post_state()
        elif command == "propose":
            self._post_state(propose=True)
        elif command in ("runout_order", "runout_swap"):
            try:
                printer, _filaments = self._project()
                client = self._client(printer)
                if client is None:
                    return
                if command == "runout_swap":
                    script = "_BOX_SET_RUNOUT_SWAP ENABLE=%d" % (1 if message.get("enable") else 0)
                else:
                    current = (self._runout or {}).get("order") or []
                    script = runout_order_script(merged_runout_order(
                        current, message.get("slots") or [], bool(message.get("manual"))))
                log("runout: %s", script)
                client.gcode(script, timeout=10.0)
            except Exception as exc:
                log("CFS panel: %s", exc)
            self._post_state()
        elif command == "set":
            try:
                printer, filaments = self._project()
                mapping = {int(t): int(s) for t, s in (message.get("map") or {}).items()}
                store_slot_map(printer.name, [f["name"] for f in filaments], mapping)
                log("slot map set: %s", mapping)
            except Exception as exc:
                log("CFS panel: %s", exc)


class K2OpenHostCfsGcodeMap(_SlicingBase):
    """Writes the panel's slot map into the exported G-code."""

    def get_name(self):
        return "K2-OpenHost CFS G-code map"

    def execute(self, ctx):
        if ctx.step != orca.slicing.Step.psGCodePostProcess or not ctx.gcode_path:
            return orca.ExecutionResult.success()
        try:
            result = write_tool_map(
                ctx.gcode_path, config_text(ctx.config_value("printer_settings_id")),
                config_list(ctx.config_value("filament_settings_id")))
        except Exception as exc:  # never break an export
            result = "not written: %s" % exc
        log("G-code map (%s): %s", ctx.host or "?", result)
        return orca.ExecutionResult.success("K2-OpenHost CFS: " + result)


if orca is not None:
    @orca.plugin
    class K2OpenHostCfsPackage(orca.base):
        def register_capabilities(self):
            orca.register_capability(K2OpenHostCfsAgent)
            orca.register_capability(K2OpenHostCfsPanel)
            orca.register_capability(K2OpenHostCfsGcodeMap)
