"""Tests of the K2-OpenHost CFS OrcaSlicer agent, without OrcaSlicer.

Run: python -m unittest tools/orcaslicer/test_k2_openhost_cfs.py
"""

import json
import os
import pathlib
import sys
import tempfile
import types
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import k2_openhost_cfs as agent_mod  # noqa: E402

SLOTS = [
    {"index": 0, "present": True, "material": "PETG-CF", "color": "#000000",
     "name": "IEMAI PETG-CF", "orca_filament_id": "OFoYSJKi", "target_temp": 250},
    {"index": 1, "present": True, "material": "PLA", "color": "#B1BEC6",
     "name": "Bambulab PLA Basic", "orca_filament_id": "OFoiVqVM", "target_temp": 215},
    {"index": 2, "present": False, "material": "", "color": ""},
    {"index": 3, "present": True, "material": "ASA", "color": "#FF0000",
     "name": "Mystery ASA", "orca_filament_id": ""},
    {"index": 4, "present": True, "external": True, "material": "PLA"},
]
BOXES = [{"address": 1, "online": True}]


class PureHelpers(unittest.TestCase):
    def test_ams_block_uses_kalico_filament_ids(self):
        ams = agent_mod.build_ams(SLOTS, BOXES)
        self.assertEqual(ams["ams_exist_bits"], "1")
        self.assertEqual(ams["tray_exist_bits"], "B")  # slots 0, 1, 3
        trays = ams["ams"][0]["tray"]
        self.assertEqual([t["tray_info_idx"] for t in trays],
                         ["OFoYSJKi", "OFoiVqVM", "", "K2OH_ASA"])
        self.assertEqual(trays[1]["tray_color"], "B1BEC6FF")
        self.assertEqual(trays[1]["tray_sub_brands"], "Bambulab PLA Basic")
        self.assertEqual(trays[1]["nozzle_temp_max"], "215")
        self.assertEqual(trays[2]["tray_slot_placeholder"], "1")

    def test_second_cfs_is_ams_unit_one(self):
        slots = [dict(SLOTS[1], index=5)]
        ams = agent_mod.build_ams(slots, [{"address": 2, "online": True}])
        self.assertEqual(ams["ams"][0]["id"], "1")
        self.assertEqual(ams["ams_exist_bits"], "2")
        self.assertEqual(ams["tray_exist_bits"], "20")
        self.assertEqual(ams["ams"][0]["tray"][1]["tray_info_idx"], "OFoiVqVM")

    def test_status_message(self):
        status = {"print_stats": {"state": "printing", "filename": "a.gcode",
                                  "total_duration": 600, "print_duration": 300},
                  "virtual_sdcard": {"progress": 0.5},
                  "extruder": {"temperature": 220.0, "target": 220.0},
                  "toolhead": {"homed_axes": "xyz"}}
        msg = agent_mod.build_status(status, "Creality_K2_Pro", {"ams": []})["print"]
        self.assertEqual(msg["gcode_state"], "RUNNING")
        self.assertEqual(msg["mc_percent"], 50)
        self.assertEqual(msg["mc_remaining_time"], 5)
        self.assertEqual(msg["home_flag"], 7)
        self.assertEqual(msg["printer_type"], "Creality_K2_Pro")
        self.assertTrue(msg["sdcard"])
        self.assertIn("ams", msg)
        self.assertNotIn("ams", agent_mod.build_status({}, "", None)["print"])

    def test_slot_map_from_print_dialog(self):
        self.assertEqual(agent_mod.parse_slot_map("[1,-1,3]", "", [0, 1, 2, 3]),
                         {0: 1, 2: 3})
        # External spool (254) and unknown slots are dropped.
        self.assertEqual(agent_mod.parse_slot_map("[254,9]", "", [0, 1, 2, 3]), {})
        pairs = json.dumps([{"ams_id": 0, "slot_id": 2}, {"ams_id": 255, "slot_id": 0}])
        self.assertEqual(agent_mod.parse_slot_map("", pairs, [0, 1, 2, 3]), {0: 2})
        self.assertEqual(agent_mod.parse_slot_map("garbage", "", [0]), {})

    def test_start_script(self):
        script, error = agent_mod.print_start_script("a.gcode", {0: 1, 1: 3, 2: 0}, [0, 1])
        self.assertIsNone(error)
        self.assertEqual(script, 'BOX_PRINT_START FILENAME="a.gcode" MAP="0:1,1:3"')
        script, error = agent_mod.print_start_script("a.gcode", {0: 1}, [0, 2])
        self.assertIsNone(script)
        self.assertIn("T2", error)
        script, error = agent_mod.print_start_script("a.gcode", {0: 1}, [])
        self.assertEqual(script, 'SDCARD_PRINT_FILE FILENAME="a.gcode"')

    def test_placeholder_key_is_not_sent(self):
        self.assertEqual(agent_mod.Moonraker("h", "7125", "88888888").api_key, "")
        self.assertEqual(agent_mod.Moonraker("h", "7125", "abc").api_key, "abc")
        self.assertEqual(agent_mod.Moonraker("h", "", "").port, 80)

    def test_safe_filename(self):
        self.assertEqual(agent_mod.safe_filename(r"C:\tmp\plate 1.gcode"), "plate 1.gcode")
        self.assertEqual(agent_mod.safe_filename("../x;y"), "x_y.gcode")


class FakeClient:
    def __init__(self, used_tools=(0, 1)):
        self.api_key = ""
        self.scripts = []
        self.requests = []
        self.uploads = []
        self.used_tools = list(used_tools)

    def upload(self, path, filename, progress=None, cancelled=None):
        self.uploads.append(filename)
        if progress:
            progress(100)
        return True

    def gcode(self, script, timeout=60.0):
        self.scripts.append(script)
        return "ok"

    def query(self, objects):
        return {"box": {"print_info": {
            "filename": self.uploads[-1],
            "tools": [{"tool": t} for t in self.used_tools]}}}

    def request(self, method, path, body=None, timeout=10.0):
        self.requests.append((method, path, body))
        return "ok"


def make_agent(client):
    agent = agent_mod.K2OpenHostCfsAgent()
    agent._client = client
    agent._slots = SLOTS
    agent.get_config = lambda: json.dumps(agent_mod.DEFAULTS)
    return agent


def params(path, mapping="[1,3]", use_ams=True):
    return types.SimpleNamespace(
        dst_file="", filename=path, task_name="plate", task_use_ams=use_ams,
        ams_mapping=mapping, ams_mapping2="")


class PrintStart(unittest.TestCase):
    def setUp(self):
        handle, self.path = tempfile.mkstemp(suffix=".gcode")
        os.write(handle, b"G28\n")
        os.close(handle)
        self.stages = []

    def tearDown(self):
        os.unlink(self.path)

    def update(self, stage, code, msg):
        self.stages.append(stage)

    def test_mapped_start_uses_box_print_start(self):
        client = FakeClient()
        code = make_agent(client).start_local_print(params(self.path), self.update, None)
        self.assertEqual(code, agent_mod.SUCCESS)
        name = client.uploads[0]
        self.assertEqual(client.scripts, [
            'BOX_PRINT_INFO FILENAME="%s"' % name,
            'BOX_PRINT_START FILENAME="%s" MAP="0:1,1:3"' % name])
        self.assertEqual(self.stages[-1], agent_mod.STAGE_FINISHED)

    def test_without_ams_kalico_maps_the_print(self):
        client = FakeClient()
        code = make_agent(client).start_local_print(
            params(self.path, use_ams=False), self.update, None)
        self.assertEqual(code, agent_mod.SUCCESS)
        self.assertEqual(client.scripts, [])
        self.assertEqual(client.requests[0][1], "/printer/print/start")

    def test_unmapped_used_tool_is_not_started(self):
        client = FakeClient(used_tools=(0, 1, 2))
        code = make_agent(client).start_local_print(params(self.path), self.update, None)
        self.assertEqual(code, agent_mod.ERR_START_FAILED)
        self.assertFalse(any(s.startswith("BOX_PRINT_START") for s in client.scripts))
        self.assertEqual(self.stages[-1], agent_mod.STAGE_ERROR)

    def test_missing_file(self):
        client = FakeClient()
        code = make_agent(client).start_local_print(
            params(self.path + ".missing"), self.update, None)
        self.assertEqual(code, agent_mod.ERR_FILE_NOT_EXIST)

    def test_device_commands(self):
        client = FakeClient()
        agent = make_agent(client)
        sent = []
        agent._dev_id = "10.10.1.97:7125"
        agent.set_on_local_message_fn(lambda dev, msg: sent.append(json.loads(msg)))
        agent._handle(json.dumps({"info": {"command": "get_version"}}))
        self.assertEqual(sent[-1]["info"]["command"], "get_version")
        agent._gcode_async = lambda script, reply=None: client.scripts.append(script)
        agent._handle(json.dumps({"print": {"command": "set_bed_temp", "temp": 60}}))
        agent._handle(json.dumps({"print": {"command": "stop"}}))
        self.assertEqual(client.scripts[-2:], [
            "SET_HEATER_TEMPERATURE HEATER=heater_bed TARGET=60", "CANCEL_PRINT"])


if __name__ == "__main__":
    unittest.main()
