# K2-OpenHost releases

`stable.json` is the newest set of component commits validated together on the reference K2 Pro. The installer helper reads it from this repository's `main` branch:

- `./helper.sh release status`: each component against the release.
- `./helper.sh release apply [--t113]`: Kalico fast-forwarded to the release commit and the release's Mainsail build installed; with `--t113` also the T113 programs. Nothing newer than the release is downgraded, local changes are left alone, and nothing runs during a print.

## Fields

| Field | Meaning |
|---|---|
| `name`, `date`, `summary` | Release name (date-based), date and one-line content |
| `components.kalico` | `MzTechnology97/kalico-k2pro`, branch `k2-pro-openhost`, commit running on the reference printer |
| `components.mainsail` | `MzTechnology97/mainsail-k2openhost`, branch `develop`; `tag` is the pre-release that carries `mainsail.zip` for that commit |
| `components.helper` | `MzTechnology97/k2-openhost-installer-helper`, branch `main`, and its `VERSION` |
| `components.t113_bootstrap` | `MzTechnology97/k2-openhost-t113-bootstrap`, branch `main`, and its `VERSION` (programs installed with `t113 update`) |
| `tested_with` | Firmware on the reference printer: slot B base release, board firmware, CFS application; informational |

Every `sha` is a full commit on the listed branch. CI (`.github/workflows/release-manifest.yml`, `tools/check-release-manifest.py --online`) checks the fields, that each commit exists on its branch, and that the Mainsail tag points at its commit and carries `mainsail.zip`.

## Making a release

1. Deploy the candidate commits on the reference printer and run the checks of [TEST_STATUS](../docs/en/TEST_STATUS.md) that the changes touch.
2. Update `stable.json`: the commits that ran, the Mainsail tag built from that commit, the versions, `tested_with`, a new `name` and `date`.
3. Run `python3 tools/check-release-manifest.py --online releases/stable.json` and open a pull request.

Commits merged but not yet run on the printer stay out of the release, even when they only move code (for example the Kalico `box.py` split of 2026-10-08, kalico-k2pro #56-#58).
