# Versions

All images target the CFS board **`cfs0_050_G32`** with stock application **`cfs0_000_153`**. Never flash them on another CFS hardware or application.

## Current images

| Image | Identity / features | Writable parameters | Status | Use it for |
| --- | --- | --- | --- | --- |
| CFG6 SGF1/RH1 R4-PRECISION1 (candidate) | `K2OH` / `v323-cfg6` / `0xE3`, plus SGF1 and the SGP1 millimetre read | 23, as CFG6 | On the reference CFS: valid Bambu read and `used_mm` advancing while printing; physical accuracy and a full runout not validated ([PR #65](https://github.com/MzTechnology97/k2-cfs-rfid-tools/pull/65)). | [Remaining in millimetres](remaining.md#remaining-in-millimetres-r4-precision1), with the paired Kalico |
| CFG6 SGF1/RH1 R3 (candidate) | `K2OH` / `v323-cfg6` / `0xE3`, plus the SGF1 geometry extension | 23, as CFG6 | Tested on the reference CFS on 2026-10-29: Bambu read in one cycle, valid measures, geometry bound; print consumption not validated ([PR #64](https://github.com/MzTechnology97/k2-cfs-rfid-tools/pull/64)) | [Spool geometry per vendor](spool-geometry.md), with the paired Kalico |
| CFG6 RDG2 | `K2OH` / `v323-cfg6` / `0xE3` | 23, as CFG6 | Working on the reference CFS (2026-10-28): RFID and MCU remaining verified; other tag formats and unload/reread still to validate | Maintained CFG6 image in the helper's menu |
| **CFG6 v3.25** | `K2OH` / `v323-cfg6` / `0xE3` | **23** (IDs 1–3, 5–9, 11–24, 27); type-4 remaining path **experimental** | 23/23 idle SET/GET verified; live type-4 **not hardware-qualified** ([#59](https://github.com/MzTechnology97/k2-cfs-rfid-tools/issues/59)) | Latest published CFG6; supervised experiments only |
| CFG5T v3.24 | `K2OH` / `v323-cfg5t` / `0xE5` | 8 (IDs 1, 2, 3, 5, 7, 8, 20, 22) + type-4 live remaining | Experimental | Rollback from CFG6 |
| CFG4 v3.23 | `K2OH` / `v323-cfg4` / `0xD7` | 6 (IDs 1, 2, 3, 5, 7, 8) | Historical | — |
| v3.22 | `0xD7` | read-only probes | **Field-tested**: load/unload and long prints | **Recovery image** |
| v3.13 | API v1 | the six feeder/hub speeds (legacy) | Legacy | — |
| v3.12 | API7, caps `0xE8` | — | Hardware-validated RFID interoperability | Third-party RFID with Bambu remaining |

SHA-256 of the images in the helper's menu:

| Image | File | SHA-256 |
| --- | --- | --- |
| SGF1/RH1 R3 | `cfs0_050_G32-cfs0_000_153-K2OH-CFG6-SGF1-RH1-R3-CANDIDATE.bin` | `a6dec25c74e7d259eec0387193548a0c3cc78ec9fc4ddc35824f0fe0965385b8` |
| RDG2 | `cfs0_050_G32-cfs0_000_153-K2OH-CFG6-RDG2.bin` | `7d611c5845d3c248cf55f57972fdc7fab1761d0e281bcbf70030ac97e458023f` |
| CFG6 v3.25 | `cfs0_050_G32-cfs0_000_153-runtime-config-v3_25-K2OH-CFG6-EXPERIMENTAL.bin` | `6579eb552210d6b2b84fbbbdf2749bc8d310b324ffb095cf9662e7cd0acc6cc6` |
| CFG5T v3.24 | `cfs0_050_G32-cfs0_000_153-runtime-config-v3_24-K2OH-CFG5T-TYPE4-EXPERIMENTAL.bin` | `78c83416afaa4795de8a018533aea884f4def396f4829cc98c77fcce48155a55` |
| CFG4 v3.23 | `cfs0_050_G32-cfs0_000_153-runtime-config-v3_23-K2OH-CFG4-EXPERIMENTAL.bin` | `118f34118edeb1e3d4ac018445b3fb839f8762b9d762bbfc011e62861fe8f71b` |
| v3.22 | `cfs0_050_G32-cfs0_000_153-runtime-config-v3_22-READONLY-DIAG-EXPERIMENTAL.bin` | `40dbaad88de7b6f9435592fa03b081e9b96663a9e84896b1ad8021a8f13cf8c7` |
| v3.13 | `cfs0_050_G32-cfs0_000_153-runtime-config-v3_13.bin` | `9a68dd8205956dda58bc3108b265fdbc03756e70974ee9a8b1ee5afc3ce46aff` |
| v3.12 | `cfs0_050_G32-cfs0_000_153-rfid-remaining-v3_12.bin` | `fe436e33a3b86339673b559d345703593e1a8e9ec3237261027e9ae48d048198` |

R4-PRECISION1 image: `cfs0_050_G32-cfs0_000_153-K2OH-CFG6-SGF1-RH1-R4-PRECISION1-CANDIDATE.bin`, SHA-256 `cc22f30adb5bf0ee471b73d21acb8789f9f8374b1cfe21c4bd405a8103d27099`.

Images, sources, builders and offline tests: [k2-cfs-rfid-tools/firmware](https://github.com/MzTechnology97/k2-cfs-rfid-tools/tree/main/firmware).

## Which one should I use?

| You want | Use |
| --- | --- |
| A CFS that just works | **Stock firmware** (no flash) |
| Test all 23 CFG6 writable IDs in a controlled environment | **CFG6 v3.25**, with a working rollback image and v3.22; type-4 live remaining is not qualified |
| To recover a CFS after a failed experiment | **v3.22** |
| Remaining in millimetres instead of whole percent | **R4-PRECISION1 candidate** with the paired Kalico, supervised; R3 stays the reference |
| Correct remaining % on Bambu spools (spool geometry) | **SGF1/RH1 R3 candidate** with the paired Kalico, supervised; keep RDG2 as rollback |

## History

v3.19 (`0xF7`, volatile RAM bench), v3.20 (`0xB7`, timing hooks), v3.21 (`0x97`, incomplete busy guard) and the v3.3/v3.6–v3.11 RFID builds are kept in the firmware repository's history but removed from the helper's menu.

## Type-4 RFID fix candidate: DO NOT FLASH

The experimental **CFG6 type-4 rescan fix** in [PR #60](https://github.com/MzTechnology97/k2-cfs-rfid-tools/pull/60) is **not a hardware-qualified release**. Its October 24, 2026 transfer failed at `send fw data` and the CFS was recovered using the working CFG6 v3.25. It deliberately retains the **same internal `v323-cfg6 / 0xE3` identity**, so an application version string cannot prove which image was flashed successfully. See the [PR #60 incident report](https://github.com/MzTechnology97/k2-cfs-rfid-tools/pull/60); **do not retry this candidate** pending a verified transport diagnosis.

## Known open issue

[k2-cfs-rfid-tools issue #9](https://github.com/MzTechnology97/k2-cfs-rfid-tools/issues/9): the CFS MCU can report `BOX_STATE=IDLE` while feeding is physically active. An atomic MCU motor-idle interlock is not proven yet. This is why Kalico writes parameters only at Klipper start with the printer idle, and why there is no console write command.
