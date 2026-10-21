# Versions

All images target the CFS board **`cfs0_050_G32`** with stock application **`cfs0_000_153`**. Never flash them on another CFS hardware or application.

## Current images

| Image | Identity / features | Writable parameters | Status | Use it for |
| --- | --- | --- | --- | --- |
| **CFG6 v3.25** | `K2OH` / `v323-cfg6` / `0xE3` | **23** (IDs 1–3, 5–9, 11–24, 27) + type-4 live remaining | Installed on the reference CFS; 23/23 SET/GET verified at idle; motion/RFID not qualified | Latest, all unlocked features |
| CFG5T v3.24 | `K2OH` / `v323-cfg5t` / `0xE5` | 8 (IDs 1, 2, 3, 5, 7, 8, 20, 22) + type-4 live remaining | Experimental | Rollback from CFG6 |
| CFG4 v3.23 | `K2OH` / `v323-cfg4` / `0xD7` | 6 (IDs 1, 2, 3, 5, 7, 8) | Historical | — |
| v3.22 | `0xD7` | read-only probes | **Field-tested**: load/unload and long prints | **Recovery image** |
| v3.13 | API v1 | the six feeder/hub speeds (legacy) | Legacy | — |
| v3.12 | API7, caps `0xE8` | — | Hardware-validated RFID interoperability | Third-party RFID with Bambu remaining |

SHA-256 of the images in the helper's menu:

| Image | File | SHA-256 |
| --- | --- | --- |
| CFG6 v3.25 | `cfs0_050_G32-cfs0_000_153-runtime-config-v3_25-K2OH-CFG6-EXPERIMENTAL.bin` | `6579eb552210d6b2b84fbbbdf2749bc8d310b324ffb095cf9662e7cd0acc6cc6` |
| CFG5T v3.24 | `cfs0_050_G32-cfs0_000_153-runtime-config-v3_24-K2OH-CFG5T-TYPE4-EXPERIMENTAL.bin` | `78c83416afaa4795de8a018533aea884f4def396f4829cc98c77fcce48155a55` |
| CFG4 v3.23 | `cfs0_050_G32-cfs0_000_153-runtime-config-v3_23-K2OH-CFG4-EXPERIMENTAL.bin` | `118f34118edeb1e3d4ac018445b3fb839f8762b9d762bbfc011e62861fe8f71b` |
| v3.22 | `cfs0_050_G32-cfs0_000_153-runtime-config-v3_22-READONLY-DIAG-EXPERIMENTAL.bin` | `40dbaad88de7b6f9435592fa03b081e9b96663a9e84896b1ad8021a8f13cf8c7` |
| v3.13 | `cfs0_050_G32-cfs0_000_153-runtime-config-v3_13.bin` | `9a68dd8205956dda58bc3108b265fdbc03756e70974ee9a8b1ee5afc3ce46aff` |
| v3.12 | `cfs0_050_G32-cfs0_000_153-rfid-remaining-v3_12.bin` | `fe436e33a3b86339673b559d345703593e1a8e9ec3237261027e9ae48d048198` |

Images, sources, builders and offline tests: [k2-cfs-rfid-tools/firmware](https://github.com/MzTechnology97/k2-cfs-rfid-tools/tree/main/firmware).

## Which one should I use?

| You want | Use |
| --- | --- |
| A CFS that just works | **Stock firmware** (no flash) |
| Every unlocked parameter and live remaining | **CFG6 v3.25**, keeping v3.22 and CFG5T for rollback |
| To recover a CFS after a failed experiment | **v3.22** |

## History

v3.19 (`0xF7`, volatile RAM bench), v3.20 (`0xB7`, timing hooks), v3.21 (`0x97`, incomplete busy guard) and the v3.3/v3.6–v3.11 RFID builds are kept in the firmware repository's history but removed from the helper's menu.

## Known open issue

[k2-cfs-rfid-tools issue #9](https://github.com/MzTechnology97/k2-cfs-rfid-tools/issues/9): the CFS MCU can report `BOX_STATE=IDLE` while feeding is physically active. An atomic MCU motor-idle interlock is not proven yet. This is why Kalico writes parameters only at Klipper start with the printer idle, and why there is no console write command.
