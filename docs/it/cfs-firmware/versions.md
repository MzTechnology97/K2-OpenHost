# Versioni

Tutte le immagini sono per la scheda CFS **`cfs0_050_G32`** con applicazione stock **`cfs0_000_153`**. Non flasharle mai su un altro hardware o applicazione CFS.

## Immagini attuali

| Immagine | Identità / feature | Parametri scrivibili | Stato | Usala per |
| --- | --- | --- | --- | --- |
| **CFG6 v3.25** | `K2OH` / `v323-cfg6` / `0xE3` | **23** (ID 1–3, 5–9, 11–24, 27) + residuo type-4 in tempo reale | Installata sul CFS di riferimento; 23/23 SET/GET verificati a riposo; movimento/RFID non qualificati | L'ultima, tutte le funzioni sbloccate |
| CFG5T v3.24 | `K2OH` / `v323-cfg5t` / `0xE5` | 8 (ID 1, 2, 3, 5, 7, 8, 20, 22) + residuo type-4 in tempo reale | Sperimentale | Rollback da CFG6 |
| CFG4 v3.23 | `K2OH` / `v323-cfg4` / `0xD7` | 6 (ID 1, 2, 3, 5, 7, 8) | Storica | — |
| v3.22 | `0xD7` | sonde in sola lettura | **Provata sul campo**: caricamento/scaricamento e stampe lunghe | **Immagine di recupero** |
| v3.13 | API v1 | le sei velocità di feeder/hub (vecchio sistema) | Vecchia | — |
| v3.12 | API7, caps `0xE8` | — | Interoperabilità RFID validata su hardware | RFID di terze parti con residuo Bambu |

SHA-256 delle immagini nel menu dell'helper:

| Immagine | File | SHA-256 |
| --- | --- | --- |
| CFG6 v3.25 | `cfs0_050_G32-cfs0_000_153-runtime-config-v3_25-K2OH-CFG6-EXPERIMENTAL.bin` | `6579eb552210d6b2b84fbbbdf2749bc8d310b324ffb095cf9662e7cd0acc6cc6` |
| CFG5T v3.24 | `cfs0_050_G32-cfs0_000_153-runtime-config-v3_24-K2OH-CFG5T-TYPE4-EXPERIMENTAL.bin` | `78c83416afaa4795de8a018533aea884f4def396f4829cc98c77fcce48155a55` |
| CFG4 v3.23 | `cfs0_050_G32-cfs0_000_153-runtime-config-v3_23-K2OH-CFG4-EXPERIMENTAL.bin` | `118f34118edeb1e3d4ac018445b3fb839f8762b9d762bbfc011e62861fe8f71b` |
| v3.22 | `cfs0_050_G32-cfs0_000_153-runtime-config-v3_22-READONLY-DIAG-EXPERIMENTAL.bin` | `40dbaad88de7b6f9435592fa03b081e9b96663a9e84896b1ad8021a8f13cf8c7` |
| v3.13 | `cfs0_050_G32-cfs0_000_153-runtime-config-v3_13.bin` | `9a68dd8205956dda58bc3108b265fdbc03756e70974ee9a8b1ee5afc3ce46aff` |
| v3.12 | `cfs0_050_G32-cfs0_000_153-rfid-remaining-v3_12.bin` | `fe436e33a3b86339673b559d345703593e1a8e9ec3237261027e9ae48d048198` |

Immagini, sorgenti, builder e test offline: [k2-cfs-rfid-tools/firmware](https://github.com/MzTechnology97/k2-cfs-rfid-tools/tree/main/firmware).

## Quale usare?

| Vuoi | Usa |
| --- | --- |
| Un CFS che funziona e basta | **Firmware stock** (nessun flash) |
| Tutti i parametri sbloccati e il residuo in tempo reale | **CFG6 v3.25**, tenendo v3.22 e CFG5T per il rollback |
| Recuperare un CFS dopo un esperimento fallito | **v3.22** |

## Storia

v3.19 (`0xF7`, banco di prova in RAM volatile), v3.20 (`0xB7`, agganci di temporizzazione), v3.21 (`0x97`, protezione busy incompleta) e le build RFID v3.3/v3.6–v3.11 restano nella storia del repository del firmware ma sono state tolte dal menu dell'helper.

## Problema noto aperto

[Issue #9 di k2-cfs-rfid-tools](https://github.com/MzTechnology97/k2-cfs-rfid-tools/issues/9): la MCU del CFS può segnalare `BOX_STATE=IDLE` mentre l'alimentazione del filamento è fisicamente attiva. Un blocco atomico "motori fermi" nella MCU non è ancora dimostrato. Per questo Kalico scrive i parametri solo all'avvio di Klipper a stampante ferma, e non esiste un comando di scrittura da console.
