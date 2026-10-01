# K2-OpenHost

> **Experimental / Work in Progress — Sperimentale / Lavori in corso**

K2-OpenHost is a hardware-validation and integration project for running the main **Kalico/Klipper + Moonraker** workload of a **Creality K2 Pro** on an external Linux host while keeping the original printer electronics and using the Allwinner T113 as the display/peripheral bridge.

K2-OpenHost è un progetto di validazione hardware e integrazione per eseguire il carico principale **Kalico/Klipper + Moonraker** di una **Creality K2 Pro** su un host Linux esterno, mantenendo l'elettronica originale e usando il sistema Allwinner T113 come bridge per display e periferiche.

The project is deliberately split into several repositories so upstream authorship stays visible and each layer can be updated independently.

## Repository ecosystem / Ecosistema repository

- **[MzTechnology97/K2-OpenHost](https://github.com/MzTechnology97/K2-OpenHost)** — canonical architecture, test results, validation notes and roadmap.
- **[MzTechnology97/kalico-k2pro](https://github.com/MzTechnology97/kalico-k2pro)** — fork of **Jacob10383/kalico**, itself based on the Kalico project. The active integration branch is `k2-pro-openhost`.
- **[MzTechnology97/k2-pro-custom-firmware](https://github.com/MzTechnology97/k2-pro-custom-firmware)** — fork of **Jacob10383/k2-plus-custom-firmware**. The `k2-openhost` branch remains the versioned source/history for Jacobean K2 extras plus the K2 Pro/OpenHost compatibility patches validated on hardware.
- **[MzTechnology97/cartographer3d-plugin-k2openhost](https://github.com/MzTechnology97/cartographer3d-plugin-k2openhost)** — Cartographer3D K2/OpenHost integration fork, based on the upstream Cartographer plugin and Jacob10383's K2 port.
- **[MzTechnology97/k2-improvements](https://github.com/MzTechnology97/k2-improvements)** — attributed reference fork in the `jamincollins -> Jacob10383` lineage.
- **[MzTechnology97/mainsail-k2openhost](https://github.com/MzTechnology97/mainsail-k2openhost)** — Mainsail fork retained for the OpenHost UI track; upstream Mainsail authorship remains unchanged.

Original author and upstream project references are intentionally preserved. K2-OpenHost does not claim authorship of code or discoveries originating in those projects.

## Current target architecture / Architettura attuale

```text
K2 stock LCD + touch
        |
        v
Allwinner T113 / Tina Linux
  - display/touch
  - future HelixScreen
  - USB ConfigFS gadget
  - byte-transparent bridges
        |
        | service Micro-USB / USB 2.0 High-Speed
        v
Raspberry Pi CM5 / external Linux host
  - kalico-k2pro:k2-pro-openhost
  - Moonraker
  - Mainsail / Fluidd
        |
        +-- ttyUSB0 -> T113 ttyGS0 -> ttyS2 -> Main MCU
        +-- ttyUSB1 -> T113 ttyGS1 -> ttyS3 -> Nozzle MCU
        +-- ttyUSB2 -> T113 ttyGS2 -> ttyS5 -> RS-485 / CFS / closed-loop devices
        `-- direct USB host -> Cartographer (preferred final topology)
```

The earlier Cartographer MUX/DEMUX experiment proved that Cartographer traffic could be carried through the T113 gadget path, but reset/re-enumeration and process-contention behaviour made that path unnecessarily fragile. The preferred architecture now keeps the three gadget serial channels dedicated to the original K2 buses and connects Cartographer directly to the CM5 USB host.

## Verified on the K2 Pro / Verificato sulla K2 Pro

As of **2026-10-01**:

- USB gadget mode on the service Micro-USB port is verified at **480M** with three simultaneous Generic Serial functions.
- Main MCU, Nozzle MCU and RS-485 communicate from external Kalico at **230400 baud** without reflashing the original Creality MCUs.
- The Kalico C helper builds and runs natively as **AArch64/ELF64** on the CM5.
- K2 Pro closed-loop motor control is integrated in `kalico-k2pro`; startup retries/delays were hardened for external-host boot timing.
- Closed-loop X/Y communication is live; CoreXY motion has been verified through normal G-code moves.
- X/Y sensorless/stall homing is verified on the real K2 Pro.
- Z direction is verified and a complete `G28` using the original **PRTouch** path completes correctly.
- Bed, nozzle and chamber heaters have been exercised successfully; PID tuning works on the external host.
- Klipper emergency shutdown was tested with all heaters active and correctly removed heater load, with printer consumption dropping back to near-idle.
- A resonance test using **Klippain-ShakeTune** completed successfully on the OpenHost stack.
- RS-485/CFS transport remains functional on `/dev/ttyUSB2`; the earlier duplicate-bridge/process-contention issue has been identified and removed.
- The real Jacobean CFS/Box stack remains validated in protected observation mode, including the K2 Pro 4-byte `BOX_STATE` path and mutation guard.
- Cartographer3D plugin import, Kalico adapter selection and live sensor streaming were demonstrated through the experimental bridge path. Final Cartographer validation is now being moved to **direct USB on the CM5**.
- `register_as_probe` support has been updated in the Cartographer fork so standalone Cartographer mode and a future PRTouch + Cartographer mixed mode can be maintained separately.

## Current project boundary / Stato attuale

The OpenHost stack has moved beyond passive transport validation: real homing, heaters, emergency shutdown and resonance testing now work on the external Kalico host. It is still **pre-production** because Cartographer direct-USB validation, full print-path validation and later CFS mutation/load-unload tests are not yet complete.

## Documentation / Documentazione

### English

- [Architecture](docs/en/ARCHITECTURE.md)
- [Test status](docs/en/TEST_STATUS.md)
- [CFS validation](docs/en/CFS_VALIDATION.md)
- [CFS observation mode](docs/en/CFS_OBSERVATION_MODE.md)
- [Roadmap](docs/en/ROADMAP.md)
- [Credits and references](docs/en/REFERENCES.md)

### Italiano

- [Architettura](docs/it/ARCHITECTURE.md)
- [Stato test](docs/it/TEST_STATUS.md)
- [Validazione CFS](docs/it/CFS_VALIDATION.md)
- [CFS observation mode](docs/it/CFS_OBSERVATION_MODE.md)
- [Roadmap](docs/it/ROADMAP.md)
- [Crediti e riferimenti](docs/it/REFERENCES.md)

## Safety / Sicurezza

All hardware experiments documented as runtime tests are intended to be reversible by reboot unless explicitly stated otherwise. Do not perform USB role switching or MCU bridge tests while printing. Keep a known-good stock boot slot/backup before persistent changes.

Tutti gli esperimenti hardware descritti come test runtime sono pensati per essere reversibili con un riavvio, salvo indicazione esplicita. Non effettuare commutazioni USB o bridge MCU durante una stampa e mantenere sempre uno slot/backup stock funzionante.

## Credits / Crediti

Core upstream projects and authors include, among others:

- **Klipper** — Klipper3d project and contributors
- **Kalico** — KalicoCrew and contributors
- **Jacob10383 / Jacobean** — Kalico K2 work, K2 custom firmware/extras, Cartographer K2 port and K2 improvements work
- **jamincollins** — original `k2-improvements` project lineage
- **CrealityOfficial** — public K2 Klipper sources
- **luketot** — public K2 Pro configuration adaptation used as a reference baseline
- **Cartographer3D** project and contributors
- **Klippain / ShakeTune** project and contributors
- **Mainsail** project and contributors
- **grant0013**, **gitstonelabs** and other public K2/CFS reverse-engineering contributors
- **HelixScreen** / prestonbrown

See the dedicated references documents for links and scope.