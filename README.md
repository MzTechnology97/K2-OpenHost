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
- **[MzTechnology97/k2-openhost-firmware-tools](https://github.com/MzTechnology97/k2-openhost-firmware-tools)** — read-only tooling to inventory, compare and probe K2 peripheral (MCU, motor, CFS) firmware from the OpenHost host; controlled flashing is a later phase.
- **[MzTechnology97/k2-openhost-installer-helper](https://github.com/MzTechnology97/k2-openhost-installer-helper)** — installer that prepares an external Linux host (Kalico K2-OpenHost, K2 Pro profile, Moonraker, Mainsail fork, udev names and start gate); experimental, pending a fresh-host test. A T113 bootstrap will follow after the hardware tests.

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
  - mainsail-k2openhost
        |
        +-- ttyUSB0 -> T113 ttyGS0 -> ttyS2 -> Main MCU
        +-- ttyUSB1 -> T113 ttyGS1 -> ttyS3 -> Nozzle MCU
        +-- ttyUSB2 -> T113 ttyGS2 -> ttyS5 -> RS-485 / CFS / closed-loop devices
        `-- direct USB host -> Cartographer (preferred final topology)
```

The earlier Cartographer MUX/DEMUX experiment proved that Cartographer traffic could be carried through the T113 gadget path, but reset/re-enumeration and process-contention behaviour made that path unnecessarily fragile. The preferred architecture now keeps the three gadget serial channels dedicated to the original K2 buses and connects Cartographer directly to the CM5 USB host.

## Verified on the K2 Pro / Verificato sulla K2 Pro

As of **2026-10-02**:

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
- The Jacobean CFS/Box stack is now running in operational mode on the real K2 Pro, including the K2 Pro 4-byte `BOX_STATE` compatibility path, load-path state and per-slot RFID reads.
- The normalized `box` object exposes persistent filament inventory, RFID material identity, hardware-reported remaining percentage and the OpenHost live remaining-filament estimate (the estimator is implemented and source-tested; its behaviour over a complete supervised print is still pending).
- K2-RFID/Creality material-database compatibility is validated with custom tags: five-digit database IDs and `1xxxxx` RFID material IDs resolve to one reusable material profile while per-spool color remains slot metadata.
- A per-slot forced RFID reread path is available for marginal/self-programmed tags; startup no longer blocks on a slow invalid RFID cache entry.
- Runout groups and auto-mapping can prefer the lowest known remaining compatible spool while preserving manual/current source selection.
- Cartographer3D plugin import, Kalico adapter selection and live sensor streaming were demonstrated through the experimental bridge path. Final Cartographer validation is now being moved to **direct USB on the CM5**.
- `register_as_probe` support has been updated in the Cartographer fork so standalone Cartographer mode and a future PRTouch + Cartographer mixed mode can be maintained separately.

## Newly implemented, pending hardware validation / Nuovo sviluppo da validare

The current Jacob/Jacobean CFS print-mapping model has now been integrated additively into the OpenHost branches:

- `BOX_PRINT_INFO` reads Orca tool/material metadata without mutating CFS state;
- `BOX_PRINT_START` accepts a logical-tool -> physical-slot map;
- `printer.objects.box` exposes `print_info` and `print_mapping` fields;
- `mainsail-k2openhost` now hooks the normal Print dialog and presents a CFS filament-mapping step;
- the compatibility layer translates purge-matrix and nozzle-temperature data from logical tools to the physical-slot indexing used by the currently validated OpenHost Box engine.

`BOX_PRINT_INFO`, real slot inventory and auto-mapping decisions are now hardware-validated in operational Box mode. The remaining milestone is a controlled `BOX_PRINT_START`/tool-change print and then a complete supervised print.

Il modello di mappatura CFS corrente di Jacob/Jacobean è stato integrato in modo additivo, inclusa la finestra di mapping in Mainsail. `BOX_PRINT_INFO`, inventario reale degli slot e auto-mapping sono ora verificati sulla K2 Pro in modalità Box operativa; restano da validare la stampa mappata con cambio materiale e una stampa completa supervisionata.

## Current project boundary / Stato attuale

The OpenHost stack has moved beyond passive transport validation: real homing, heaters, emergency shutdown and resonance testing now work on the external Kalico host. It is still **pre-production** because mapped CFS printing, Cartographer direct-USB validation and a complete print workflow are not yet validated end to end.

## Documentation / Documentazione

### English

- [Architecture](docs/en/ARCHITECTURE.md)
- [USB gadget transport](docs/en/USB_GADGET.md)
- [Test status](docs/en/TEST_STATUS.md)
- [Hardware test plan](docs/en/HARDWARE_TEST_PLAN.md)
- [CFS validation](docs/en/CFS_VALIDATION.md)
- [CFS observation mode](docs/en/CFS_OBSERVATION_MODE.md)
- [CFS print mapping](docs/en/CFS_PRINT_MAPPING.md)
- [Roadmap](docs/en/ROADMAP.md)
- [Credits and references](docs/en/REFERENCES.md)

### Italiano

- [Architettura](docs/it/ARCHITECTURE.md)
- [Trasporto USB gadget](docs/it/USB_GADGET.md)
- [Stato test](docs/it/TEST_STATUS.md)
- [Piano dei test hardware](docs/it/HARDWARE_TEST_PLAN.md)
- [Validazione CFS](docs/it/CFS_VALIDATION.md)
- [CFS observation mode](docs/it/CFS_OBSERVATION_MODE.md)
- [Mappatura CFS delle stampe](docs/it/CFS_PRINT_MAPPING.md)
- [Roadmap](docs/it/ROADMAP.md)
- [Crediti e riferimenti](docs/it/REFERENCES.md)

## Safety / Sicurezza

All hardware experiments documented as runtime tests are intended to be reversible by reboot unless explicitly stated otherwise. Do not perform USB role switching or MCU bridge tests while printing. Keep a known-good stock boot slot/backup before persistent changes.

Tutti gli esperimenti hardware descritti come test runtime sono pensati per essere reversibili con un riavvio, salvo indicazione esplicita. Non effettuare commutazioni USB o bridge MCU durante una stampa e mantenere sempre uno slot/backup stock funzionante.

## Credits / Crediti

Core upstream projects and authors include, among others:

- **Klipper** — Klipper3d project and contributors
- **Kalico** — KalicoCrew and contributors
- **Jacob10383 / Jacobean** — Kalico K2 work, K2 custom firmware/extras, Cartographer K2 port, Fluidd CFS workflow and K2 improvements work
- **jamincollins** — original `k2-improvements` project lineage
- **CrealityOfficial** — public K2 Klipper sources
- **luketot** — public K2 Pro configuration adaptation used as a reference baseline
- **Cartographer3D** project and contributors
- **Klippain / ShakeTune** project and contributors
- **Mainsail** project and contributors
- **HimAndRobot/creality-cfs-mainsail-integration** — CFS Mainsail/Fluidd UI reference
- **grant0013**, **gitstonelabs** and other public K2/CFS reverse-engineering contributors
- **HelixScreen** / prestonbrown

See the dedicated references documents for links and scope.
