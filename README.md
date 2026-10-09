# K2-OpenHost

> **Experimental / Work in Progress — Sperimentale / Lavori in corso**

> [!WARNING]
> **For experienced users only. Use at your own risk.** K2-OpenHost voids the manufacturer's warranty and can damage the printer beyond repair, brick its firmware or, in case of malfunction, cause a fire. The authors accept no liability for damage to property or persons. Read the [disclaimer and hardware limitations](docs/en/DISCLAIMER.md) before using any of these tools.
>
> **Solo per utenti esperti. Uso a proprio rischio.** K2-OpenHost invalida la garanzia del produttore e può danneggiare la stampante in modo irreparabile, mandare il firmware in brick o, in caso di malfunzionamento, causare un incendio. Gli autori non sono responsabili di danni a cose o a persone. Leggi l'[esclusione di responsabilità e i limiti hardware](docs/it/DISCLAIMER.md) prima di usare questi strumenti.

K2-OpenHost is a hardware-validation and integration project for running the main **Kalico/Klipper + Moonraker** workload of a **Creality K2 Pro** on an external Linux host while keeping the original printer electronics and using the Allwinner T113 as the display/peripheral bridge.

K2-OpenHost è un progetto di validazione hardware e integrazione per eseguire il carico principale **Kalico/Klipper + Moonraker** di una **Creality K2 Pro** su un host Linux esterno, mantenendo l'elettronica originale e usando il sistema Allwinner T113 come bridge per display e periferiche.

The project is deliberately split into several repositories so upstream authorship stays visible and each layer can be updated independently.

## Repository ecosystem / Ecosistema repository

- **[MzTechnology97/K2-OpenHost](https://github.com/MzTechnology97/K2-OpenHost)** — canonical architecture, test results, validation notes and roadmap.
- **[MzTechnology97/kalico-k2pro](https://github.com/MzTechnology97/kalico-k2pro)** — fork of **Jacob10383/kalico**, itself based on the Kalico project. The active integration branch is `k2-pro-openhost`, the repository's default branch. The K2 profile lives in `config/k2/`: a lean `printer.cfg` and the printer files in `macros/`.
- **[MzTechnology97/k2-pro-custom-firmware](https://github.com/MzTechnology97/k2-pro-custom-firmware)** — fork of **Jacob10383/k2-plus-custom-firmware**, **archived on 2026-10-04** (read-only history of the first K2 Pro/OpenHost patches to Jacobean's extras). The K2 extras are maintained in `kalico-k2pro`; upstream changes are reviewed directly against Jacob10383's repositories.
- **[MzTechnology97/k2-openhost-t113-bootstrap](https://github.com/MzTechnology97/k2-openhost-t113-bootstrap)** — the printer side: K2-OpenHost system for the T113 slot B (USB gadget bridges, HelixScreen, Creality MCU/motor/CFS firmware updates). Prepared and tested on stock firmware 1.1.0.94; not guaranteed on newer releases. See [T113 bootstrap](docs/en/T113_BOOTSTRAP.md) / [IT](docs/it/T113_BOOTSTRAP.md).
- **[Cartographer3D/cartographer3d-plugin](https://github.com/Cartographer3D/cartographer3d-plugin)** — the official Cartographer plugin, used unchanged (it supports Kalico and the K2 directly, as in Jacob10383's firmware). The former `cartographer3d-plugin-k2openhost` fork was archived on 2026-10-04. See [Cartographer](docs/en/CARTOGRAPHER.md) / [IT](docs/it/CARTOGRAPHER.md).
- **[MzTechnology97/k2-improvements](https://github.com/MzTechnology97/k2-improvements)** — attributed reference fork in the `jamincollins -> Jacob10383` lineage.
- **[MzTechnology97/mainsail-k2openhost](https://github.com/MzTechnology97/mainsail-k2openhost)** — Mainsail fork for the OpenHost UI (branch `develop`): CFS panel with filament mapping, runout order and settings (runout swap, unload after print, RFID reads, clog detection), filament warnings, motor and RS-485 counters, part fan labels; upstream Mainsail authorship remains unchanged.
- **[pedrolamas/klipper-virtual-pins](https://github.com/pedrolamas/klipper-virtual-pins)** — third-party Klipper module, installed unchanged on the host, used for the Mainsail **Axis Twist Compensation** switch (`config/k2/macros/openhost_controls.cfg`).
- **[MzTechnology97/k2-openhost-firmware-tools](https://github.com/MzTechnology97/k2-openhost-firmware-tools)** — read-only tooling to inventory, compare and probe K2 peripheral (MCU, motor, CFS) firmware from the OpenHost host; controlled flashing is a later phase.
- **[MzTechnology97/k2-openhost-installer-helper](https://github.com/MzTechnology97/k2-openhost-installer-helper)** — installer that prepares an external Linux host (Kalico K2-OpenHost, K2 Pro profile, Moonraker, Mainsail fork, udev names and start gate); experimental, pending a fresh-host test. A T113 bootstrap will follow after the hardware tests.

Original author and upstream project references are intentionally preserved. K2-OpenHost does not claim authorship of code or discoveries originating in those projects.

## Releases / Release

The component branches move with every merge. [`releases/stable.json`](releases/stable.json) lists the commits **validated together on the reference printer** (Kalico, Mainsail build, installer helper, T113 bootstrap) and the firmware they were tested with. On the host, `./helper.sh release status` compares the installation with it and `./helper.sh release apply` brings Kalico and Mainsail to it (fast-forward only, never during a print, Klipper restarted only when confirmed with the heaters off). See [releases/README.md](releases/README.md).

I branch dei componenti avanzano a ogni merge. [`releases/stable.json`](releases/stable.json) elenca i commit **validati insieme sulla stampante di riferimento** (Kalico, build di Mainsail, installer helper, bootstrap T113) e il firmware con cui sono stati provati. Sull'host, `./helper.sh release status` confronta l'installazione con il manifest e `./helper.sh release apply` porta Kalico e Mainsail a quei commit (solo fast-forward, mai durante una stampa, riavvio di Klipper solo se confermato e con i riscaldatori spenti).

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
  - kalico-k2pro:k2-pro-openhost (+ klipper-virtual-pins)
  - Moonraker
  - mainsail-k2openhost
  - crowsnest: chamber and nozzle cameras (USB, rewired to the host)
        |
        +-- /dev/k2-main   -> T113 ttyGS0 -> ttyS2 -> Main MCU
        +-- /dev/k2-nozzle -> T113 ttyGS1 -> ttyS3 -> Nozzle MCU
        +-- /dev/k2-rs485  -> T113 ttyGS2 -> ttyS5 -> RS-485 / CFS / closed-loop devices
        `-- direct USB host -> /dev/k2-cartographer (preferred final topology)
```

The earlier Cartographer MUX/DEMUX experiment proved that Cartographer traffic could be carried through the T113 gadget path, but reset/re-enumeration and process-contention behaviour made that path unnecessarily fragile. The preferred architecture now keeps the three gadget serial channels dedicated to the original K2 buses and connects Cartographer directly to the CM5 USB host.

## Verified on the K2 Pro / Verificato sulla K2 Pro

Since then (details in [test status](docs/en/TEST_STATUS.md) / [stato dei test](docs/it/TEST_STATUS.md)): long CFS prints and a live runout swap with the T113 on slot B, Creality 1.1.7.0 board firmware flashed from slot B, the CFS six-byte state on firmware 1.5.3, unload and slot change from unhomed axes with the heat-up over the wastebin, native fan tachometers, the clog detection switch, a faster bottom-switch Z drop and the printer config reorganised under `macros/` (2026-10-07); third-party RFID spools (Bambu, QIDI) recognised and tracked like Creality ones, and the CFS slots shown right after a spool swap (2026-10-08).

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
- The stock T113 service GPIO map is recovered, including MCU power (`GPIO140`), nozzle-camera power (`162`), buzzer (`164`), USB-hub reset (`165`) and UDISK power (`210`); no CM5-direct wiring for these nets has been proven.
- The Jacobean CFS/Box stack is now running in operational mode on the real K2 Pro, including the K2 Pro 4-byte `BOX_STATE` compatibility path (CFS firmware 1.1.3; 1.5.3 answers with the original 6 bytes), load-path state and per-slot RFID reads.
- The normalized `box` object exposes persistent filament inventory, RFID material identity, hardware-reported remaining percentage and the OpenHost live remaining-filament estimate (the estimator is implemented and source-tested; its behaviour over a complete supervised print is still pending).
- K2-RFID/Creality material-database compatibility is validated with custom tags: five-digit database IDs and `1xxxxx` RFID material IDs resolve to one reusable material profile while per-spool color remains slot metadata.
- A per-slot forced RFID reread path is available for marginal/self-programmed tags; startup no longer blocks on a slow invalid RFID cache entry.
- Runout groups and auto-mapping can prefer the lowest known remaining compatible spool while preserving manual/current source selection.
- Cartographer3D plugin import, Kalico adapter selection and live sensor streaming were demonstrated through the experimental bridge path. Final Cartographer validation is now being moved to **direct USB on the CM5**.
- The official Cartographer plugin provides `register_as_probe`, so standalone Cartographer mode and a future PRTouch + Cartographer mixed mode can be maintained separately.

## Newly implemented, pending hardware validation / Nuovo sviluppo da validare

The current Jacob/Jacobean CFS print-mapping model has now been integrated additively into the OpenHost branches:

- `BOX_PRINT_INFO` reads Orca tool/material metadata without mutating CFS state;
- `BOX_PRINT_START` accepts a logical-tool -> physical-slot map;
- `printer.objects.box` exposes `print_info` and `print_mapping` fields;
- `mainsail-k2openhost` now hooks the normal Print dialog and presents a CFS filament-mapping step;
- the compatibility layer translates purge-matrix and nozzle-temperature data from logical tools to the physical-slot indexing used by the currently validated OpenHost Box engine.

`BOX_PRINT_INFO`, real slot inventory, automatic mapping on a normal start, CFS loading and the automatic runout swap have now run on the K2 Pro, during an 18-hour print. Still to validate: an explicit `BOX_PRINT_START` with a multi-colour tool change, and pause/resume with a slot change.

Il modello di mappatura CFS corrente di Jacob/Jacobean è stato integrato in modo additivo, inclusa la finestra di mapping in Mainsail. `BOX_PRINT_INFO`, inventario reale degli slot, associazione automatica all'avvio, caricamento dal CFS e cambio bobina automatico sono andati sulla K2 Pro durante una stampa di 18 ore. Restano da provare un `BOX_PRINT_START` esplicito con cambio colore e la pausa con cambio slot.

Latest on the reference printer (2026-10-09): CFS notifications reach the phone (Mobileraker, Telegram); every CFS filament carries its OrcaSlicer preset ID, published for the slicer and editable in Mainsail; with CFS firmware v3.13+ the CFS runtime speeds are set from `box.cfg` (`box_cfs_runtime`). Details in [TEST_STATUS](docs/en/TEST_STATUS.md) and [OrcaSlicer](docs/en/ORCASLICER.md).

Ultime novità sulla stampante di riferimento (9 ottobre 2026): le notifiche CFS arrivano al telefono (Mobileraker, Telegram); ogni filamento CFS ha l'ID del suo preset OrcaSlicer, pubblicato per lo slicer e modificabile in Mainsail; con il firmware CFS v3.13+ le velocità runtime della CFS si impostano da `box.cfg` (`box_cfs_runtime`). Dettagli in [TEST_STATUS](docs/it/TEST_STATUS.md) e [OrcaSlicer](docs/it/ORCASLICER.md).

## Current project boundary / Stato attuale

The OpenHost stack has moved beyond passive transport validation: real homing, heaters, emergency shutdown and resonance testing now work on the external Kalico host. An 18-hour print with automatic CFS mapping and a runout swap also ran without errors. It is still **pre-production**: multi-colour CFS printing, pause/resume, power-loss recovery and Cartographer on direct USB are not validated yet.

## Hardware limitations / Limiti hardware

With the T113 service USB port in gadget mode (required by OpenHost):

- the **nozzle camera** and the **chamber camera** cannot be managed by the T113: rewire their original cable path and connect them **directly to the external Linux host**;
- the printer's **external USB port** cannot be used to print from a USB stick and **stops working completely** in gadget mode; send files through Mainsail/Moonraker instead.

Con la porta USB di servizio del T113 in modalità gadget (necessaria per OpenHost):

- la **fotocamera dell'ugello** e la **fotocamera della camera** non possono essere gestite dal T113: occorre ricablare il percorso originale e collegarle **direttamente all'host Linux esterno**;
- la **porta USB esterna** della stampante non può essere usata per stampare da chiavetta e in modalità gadget **smette completamente di funzionare**; i file si inviano da Mainsail/Moonraker.

Details / Dettagli: [EN](docs/en/DISCLAIMER.md#hardware-limitations-in-openhost-mode) · [IT](docs/it/DISCLAIMER.md#limiti-hardware-in-modalità-openhost).

## Documentation / Documentazione

### English

- [Disclaimer and hardware limitations](docs/en/DISCLAIMER.md)
- [Cartographer3D](docs/en/CARTOGRAPHER.md)
- [Architecture](docs/en/ARCHITECTURE.md)
- [G-code commands added by K2-OpenHost](docs/en/GCODE_COMMANDS.md)
- [USB gadget transport](docs/en/USB_GADGET.md)
- [T113 service GPIO map](docs/en/T113_GPIO.md)
- [Recovery runbook](docs/en/RECOVERY.md)
- [Serial link loss behind the T113](docs/en/SERIAL_LINK_LOSS.md)
- [USB bridge between the host and the T113: analysis and measurements](docs/en/USB_BRIDGE.md)
- [T113 bootstrap (slot B)](docs/en/T113_BOOTSTRAP.md)
- [Test status](docs/en/TEST_STATUS.md)
- [Hardware test plan](docs/en/HARDWARE_TEST_PLAN.md)
- [CFS validation](docs/en/CFS_VALIDATION.md)
- [CFS observation mode](docs/en/CFS_OBSERVATION_MODE.md)
- [CFS print mapping](docs/en/CFS_PRINT_MAPPING.md)
- [OrcaSlicer and the CFS](docs/en/ORCASLICER.md)
- [Roadmap](docs/en/ROADMAP.md)
- [Credits and references](docs/en/REFERENCES.md)

### Italiano

- [Esclusione di responsabilità e limiti hardware](docs/it/DISCLAIMER.md)
- [Cartographer3D](docs/it/CARTOGRAPHER.md)
- [Architettura](docs/it/ARCHITECTURE.md)
- [Comandi G-code aggiunti da K2-OpenHost](docs/it/GCODE_COMMANDS.md)
- [Trasporto USB gadget](docs/it/USB_GADGET.md)
- [GPIO di servizio T113](docs/it/T113_GPIO.md)
- [Procedura di ripristino](docs/it/RECOVERY.md)
- [Perdita del collegamento seriale dietro il T113](docs/it/SERIAL_LINK_LOSS.md)
- [Bridge USB tra l'host e il T113: analisi e misure](docs/it/USB_BRIDGE.md)
- [Bootstrap del T113 (slot B)](docs/it/T113_BOOTSTRAP.md)
- [Stato test](docs/it/TEST_STATUS.md)
- [Piano dei test hardware](docs/it/HARDWARE_TEST_PLAN.md)
- [Validazione CFS](docs/it/CFS_VALIDATION.md)
- [CFS observation mode](docs/it/CFS_OBSERVATION_MODE.md)
- [Mappatura CFS delle stampe](docs/it/CFS_PRINT_MAPPING.md)
- [OrcaSlicer e il CFS](docs/it/ORCASLICER.md)
- [Roadmap](docs/it/ROADMAP.md)
- [Crediti e riferimenti](docs/it/REFERENCES.md)

## Safety / Sicurezza

All hardware experiments documented as runtime tests are intended to be reversible by reboot unless explicitly stated otherwise. Do not perform USB role switching or MCU bridge tests while printing. Keep a known-good stock boot slot/backup before persistent changes. Never leave the printer unattended while it is controlled by the external host. See the [disclaimer](docs/en/DISCLAIMER.md).

Tutti gli esperimenti hardware descritti come test runtime sono pensati per essere reversibili con un riavvio, salvo indicazione esplicita. Non effettuare commutazioni USB o bridge MCU durante una stampa e mantenere sempre uno slot/backup stock funzionante. Non lasciare mai la stampante senza sorveglianza mentre è comandata dall'host esterno. Vedi l'[esclusione di responsabilità](docs/it/DISCLAIMER.md).

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