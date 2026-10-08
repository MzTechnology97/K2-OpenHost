#!/usr/bin/env python3
"""Check a K2-OpenHost release manifest (releases/*.json).

Offline: schema, fields and SHA format. With --online (GitHub API, GH_TOKEN
or GITHUB_TOKEN when set): every commit exists and is on its branch, and a
Mainsail tag points at its commit and carries mainsail.zip.

usage: check-release-manifest.py [--online] releases/stable.json [...]
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request

COMPONENTS = ("kalico", "mainsail", "helper", "t113_bootstrap")
SHA = re.compile(r"^[0-9a-f]{40}$")
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
VERSION = re.compile(r"^\d+\.\d+\.\d+$")


def check_offline(doc):
    errors = []
    if doc.get("schema") != 1:
        errors.append("schema must be 1")
    for key in ("name", "date", "summary"):
        if not isinstance(doc.get(key), str) or not doc[key]:
            errors.append("missing %s" % key)
    if isinstance(doc.get("date"), str) and not DATE.match(doc["date"]):
        errors.append("date must be YYYY-MM-DD")
    components = doc.get("components")
    if not isinstance(components, dict):
        return errors + ["missing components"]
    for name in COMPONENTS:
        item = components.get(name)
        if not isinstance(item, dict):
            errors.append("missing component %s" % name)
            continue
        if not REPO.match(str(item.get("repo", ""))):
            errors.append("%s: repo must be owner/name" % name)
        if not isinstance(item.get("branch"), str) or not item["branch"]:
            errors.append("%s: missing branch" % name)
        if not SHA.match(str(item.get("sha", ""))):
            errors.append("%s: sha must be a full 40-character commit" % name)
        if "version" in item and not VERSION.match(str(item["version"])):
            errors.append("%s: version must be X.Y.Z" % name)
    for name in set(components) - set(COMPONENTS):
        errors.append("unknown component %s" % name)
    if not str(components.get("mainsail", {}).get("tag", "")).startswith("v"):
        errors.append("mainsail: tag of the release with mainsail.zip is required")
    return errors


def github(path):
    request = urllib.request.Request("https://api.github.com/" + path)
    request.add_header("Accept", "application/vnd.github+json")
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise


def check_online(doc):
    errors = []
    for name in COMPONENTS:
        item = doc["components"][name]
        repo, branch, sha = item["repo"], item["branch"], item["sha"]
        if github("repos/%s/commits/%s" % (repo, sha)) is None:
            errors.append("%s: commit %s not found in %s" % (name, sha[:8], repo))
            continue
        compare = github("repos/%s/compare/%s...%s" % (repo, sha, branch))
        if compare is None:
            errors.append("%s: branch %s not found in %s" % (name, branch, repo))
        elif compare.get("status") not in ("ahead", "identical"):
            errors.append("%s: %s is not on %s (%s)"
                          % (name, sha[:8], branch, compare.get("status")))
    mainsail = doc["components"]["mainsail"]
    release = github("repos/%s/releases/tags/%s" % (mainsail["repo"], mainsail["tag"]))
    if release is None:
        errors.append("mainsail: release %s not found" % mainsail["tag"])
    else:
        if not any(a.get("name") == "mainsail.zip" for a in release.get("assets", [])):
            errors.append("mainsail: release %s has no mainsail.zip" % mainsail["tag"])
        ref = github("repos/%s/commits/%s" % (mainsail["repo"], mainsail["tag"]))
        if ref is None or ref.get("sha") != mainsail["sha"]:
            errors.append("mainsail: tag %s is not commit %s"
                          % (mainsail["tag"], mainsail["sha"][:8]))
    return errors


def main(argv):
    online = "--online" in argv
    paths = [arg for arg in argv if arg != "--online"]
    if not paths:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2
    failed = False
    for path in paths:
        try:
            with open(path, encoding="utf-8") as handle:
                doc = json.load(handle)
        except (OSError, ValueError) as exc:
            print("%s: %s" % (path, exc))
            failed = True
            continue
        errors = check_offline(doc)
        if not errors and online:
            errors = check_online(doc)
        for error in errors:
            print("%s: %s" % (path, error))
        if errors:
            failed = True
        else:
            print("%s: ok (%s)" % (path, doc["name"]))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
