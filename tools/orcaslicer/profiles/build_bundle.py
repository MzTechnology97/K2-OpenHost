#!/usr/bin/env python3
"""Build the OrcaSlicer printer bundle (.orca_printer) from the presets here.

The archive has the layout of OrcaSlicer's own "Export preset bundle ->
Printer config bundle": bundle_structure.json, printer/<printer>.json and
process/<process>.json. OrcaSlicer imports it with File -> Import -> Import
Configs. Run it after changing a preset:

    python3 tools/orcaslicer/profiles/build_bundle.py

--check only verifies that the committed bundle holds the same files.
"""
import glob
import io
import json
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
# A fixed id: importing a newer bundle replaces the one imported before.
BUNDLE_ID = "K2-OpenHost_K2_Pro_Kalico"
# Fixed entry date, so the same presets always give the same archive.
ZIP_DATE = (2026, 1, 1, 0, 0, 0)


def presets(kind):
    return sorted(glob.glob(os.path.join(HERE, kind, "*.json")))


def build():
    machines = presets("machine")
    if len(machines) != 1:
        raise SystemExit("expected one printer preset in machine/, found %d" % len(machines))
    with open(machines[0], encoding="utf-8") as f:
        printer_name = json.load(f)["name"]
    entries = [("printer/" + os.path.basename(machines[0]), machines[0])]
    entries += [("process/" + os.path.basename(p), p) for p in presets("process")]
    structure = {
        "bundle_id": BUNDLE_ID,
        "bundle_type": "printer config bundle",
        "filament_config": [],
        "printer_config": [name for name, _ in entries if name.startswith("printer/")],
        "printer_preset_name": printer_name,
        "process_config": [name for name, _ in entries if name.startswith("process/")],
        "version": "",
    }
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, path in entries:
            with open(path, "rb") as f:
                # LF whatever the checkout does (git autocrlf on Windows).
                data = f.read().replace(b"\r\n", b"\n")
            archive.writestr(zipfile.ZipInfo(name, ZIP_DATE), data, zipfile.ZIP_DEFLATED)
        archive.writestr(zipfile.ZipInfo("bundle_structure.json", ZIP_DATE),
                         json.dumps(structure, indent=4) + "\n", zipfile.ZIP_DEFLATED)
    return printer_name, out.getvalue()


def entries_of(data):
    """(name, content) of every archive entry: deflate output differs between
    zlib builds, so the check compares what OrcaSlicer reads, not the bytes."""
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return [(name, archive.read(name)) for name in archive.namelist()]


def main():
    printer_name, data = build()
    target = os.path.join(HERE, printer_name + ".orca_printer")
    if "--check" in sys.argv[1:]:
        try:
            with open(target, "rb") as f:
                current = entries_of(f.read())
        except (FileNotFoundError, zipfile.BadZipFile):
            current = None
        if current != entries_of(data):
            raise SystemExit("%s is out of date: run build_bundle.py" % os.path.basename(target))
        print("bundle up to date")
        return
    with open(target, "wb") as f:
        f.write(data)
    print("wrote", os.path.relpath(target))


if __name__ == "__main__":
    main()
