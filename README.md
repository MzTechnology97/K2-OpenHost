# K2-OpenHost

> **Experimental / Work in Progress — Sperimentale / Lavori in corso**

K2-OpenHost is a hardware-validation and integration project for running the main **Kalico/Klipper + Moonraker** workload of a **Creality K2 Pro** on an external Linux host while keeping the original printer electronics and using the Allwinner T113 system as a display/peripheral bridge.

K2-OpenHost è un progetto di validazione hardware e integrazione per eseguire il carico principale **Kalico/Klipper + Moonraker** di una **Creality K2 Pro** su un host Linux esterno, mantenendo l'elettronica originale e usando il sistema Allwinner T113 come bridge per display e periferiche.

The project is deliberately split into several repositories so upstream authorship stays visible and each layer can be updated independently.

## Repository ecosystem / Ecosistema repository

- **[MzTechnology97/K2-OpenHost](https://github.com/MzTechnology97/K2-OpenHost)** — canonical architecture, test results, validation notes and roadmap.
- **[MzTechnology97/kalico-k2pro](https://github.com/MzTechnology97/kalico-k2pro)** — fork of **Jacob10383/kalico**, itself based on the Kalico project. The active integration branch is `k2-pro-openhost`. It contains the K2 Pro configuration baseline and the K2-specific extras required by the current OpenHost tests.
- **[MzTechnology97/k2-pro-custom-firmware](https://github.com/MzTechnology97/k2-pro-custom-firmware)** — fork of **Jacob10383/k2-plus-custom-firmware**. The `k2-openhost` branch is used as the versioned source for Jacobean K2 extras plus the K2 Pro/OpenHost compatibility patches validated on hardware.
- **[MzTechnology97/k2-improvements](https://github.com/MzTechnology97/k2-improvements)** — fork in the `jamincollins/k2-improvements -> Jacob10383/k2-improvements` lineage. It remains an important upstream reference for K2 modifications, Cartographer integration and printer-side improvements.

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
        +-- ttyUSB3 -> planned Cartographer bridge
```

## Verified on the K2 Pro / Verificato sulla K2 Pro

As of **2026-09-30**:

- USB gadget mode on the service Micro-USB port is verified at **480M**.
- Three simultaneous Generic Serial functions (`gser.usb0..2`) are verified.
- Main MCU and Nozzle MCU communicate simultaneously with external Kalico at **230400 baud** without reflashing either MCU.
- RS-485 traffic is bridged end-to-end through `/dev/ttyUSB2`.
- Closed-loop X (`0x81`) and Y (`0x82`) controllers answer valid read-only queries.
- CFS discovery/addressing and read-only queries are verified on the real K2 Pro.
- Jacobean `BoxDriver` works through the OpenHost transport.
- The real Jacobean `Box()` class works in the K2-OpenHost **observation mode**.
- The K2 Pro 4-byte `BOX_STATE` response is supported without breaking the existing 6-byte decoder path.
- The CFS observation guard blocks mutation function `0x0D` **before TX**.
- A complete observation-mode run completed **35 TX / 35 RX**, with **0 CRC errors, 0 invalid frames, 0 unmatched replies, 0 timeouts, 0 reader/send errors**.
- `MzTechnology97/kalico-k2pro:k2-pro-openhost` now contains the K2 Pro baseline configuration and the validated K2 extras.

The current work is still **pre-production**. Full CFS load/unload control, the Cartographer USB bridge and the final CM5 configuration migration are not yet declared production-ready.

## Documentation / Documentazione

### English

- [Architecture](docs/en/ARCHITECTURE.md)
- [USB gadget transport](docs/en/USB_GADGET.md)
- [Test status](docs/en/TEST_STATUS.md)
- [CFS validation](docs/en/CFS_VALIDATION.md)
- [CFS observation mode](docs/en/CFS_OBSERVATION_MODE.md)
- [Roadmap](docs/en/ROADMAP.md)
- [Credits and references](docs/en/REFERENCES.md)

### Italiano

- [Architettura](docs/it/ARCHITECTURE.md)
- [Trasporto USB Gadget](docs/it/USB_GADGET.md)
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
- **Jacob10383** — Kalico K2 work, K2 custom firmware/extras and K2 improvements work
- **jamincollins** — original `k2-improvements` project lineage
- **CrealityOfficial** — public K2 Klipper sources
- **luketot** — public K2 Pro configuration adaptation used as a reference baseline
- **grant0013**, **gitstonelabs** and other public K2/CFS reverse-engineering contributors
- **Cartographer3D** project and contributors
- **HelixScreen** / prestonbrown

See the dedicated references documents for links and scope.