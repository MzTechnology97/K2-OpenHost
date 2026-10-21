# /// script
# requires-python = ">=3.12"
#
# [tool.orcaslicer.plugin]
# name = "K2-OpenHost CFS"
# description = "Printer agent for a Creality K2 driven by K2-OpenHost (Kalico + Moonraker): CFS slots with their exact filament, and the filament -> slot map of the print dialog sent to the CFS."
# author = "K2-OpenHost"
# version = "0.1.0"
# type = "printer-connection"
# ///
"""K2-OpenHost CFS printer agent for OrcaSlicer 2.5 or later.

OrcaSlicer's built-in Moonraker agent matches a CFS slot to a preset by
material only ("Generic PLA" for every PLA) and starts every print with
SDCARD_PRINT_FILE, ignoring the filament -> slot map of its print dialog.
This agent talks to the same Moonraker, but:

- it publishes each CFS slot with the OrcaSlicer filament_id Kalico keeps per
  filament (box.slots[].orca_filament_id), so Sync selects the slot's own
  preset (a system preset, or one of your custom root presets);
- it starts a mapped print with Kalico's BOX_PRINT_START MAP=tool:slot, the
  same request the Mainsail mapping dialog sends. Without a map (or with
  "Use AMS" off) the print starts normally and Kalico maps it by material and
  colour as before.

Select it in the printer preset (printer agent "K2-OpenHost CFS") and keep
the Moonraker address in the print host field.
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
AGENT_VERSION = "0.1.0"

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


def log(msg, *args):
    print("[k2oh-cfs] " + (msg % args if args else msg), file=sys.stderr, flush=True)


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

    def _run(self, generation, stop):
        client = self._client
        try:
            info = client.server_info()
        except Exception as exc:
            log("Moonraker %s:%s not reachable: %s", client.host, client.port, exc)
            info = None
        if info is not None and self._current(generation):
            with self._lock:
                self._dev_name = info.get("machine_name") or info.get("hostname") or self._dev_id
                self._version = info.get("moonraker_version", "")
                local_fn = self._callbacks.get("local_connect")
                connected_fn = self._callbacks.get("connected")
                dev_id = self._dev_id
            _call(local_fn, CONNECT_OK, dev_id, "0")
            _call(connected_fn, dev_id)
            self._send_version_info()
        while not stop.is_set() and self._current(generation):
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


if orca is not None:
    @orca.plugin
    class K2OpenHostCfsPackage(orca.base):
        def register_capabilities(self):
            orca.register_capability(K2OpenHostCfsAgent)
