# Come funziona

## La K2 Pro stock

Su una K2 Pro stock la scheda **T113** esegue il sistema Linux di Creality: Klipper, Moonraker, l'interfaccia touch e le app cloud. Klipper parla con i microcontrollori della stampante su tre UART:

| UART T113 | Dispositivo |
| --- | --- |
| `ttyS2` | Main MCU (piatto, camera, ventole, Z, sensori) |
| `ttyS3` | Nozzle MCU (hotend, ventola pezzo, motore dell'estrusore tramite la scheda nozzle) |
| `ttyS5` | Bus RS-485: le unità CFS e i controller dei motori X/Y closed-loop |

## K2-OpenHost

K2-OpenHost mantiene le stesse schede e lo stesso firmware, ma sposta Klipper su un **host esterno**:

```text
Schermo touch stock della K2
        |
Allwinner T113 (slot B: sistema K2-OpenHost)
  - HelixScreen sullo schermo stock
  - USB gadget: tre funzioni Generic Serial
  - bridge trasparenti byte per byte:
      ttyGS0 <-> ttyS2  Main MCU
      ttyGS1 <-> ttyS3  Nozzle MCU
      ttyGS2 <-> ttyS5  RS-485 (CFS, motori X/Y)
        |
        | Micro-USB di servizio, USB 2.0 High-Speed
        v
Host Linux esterno (Raspberry Pi CM5)
  - Kalico (kalico-k2pro, k2-pro-openhost)
  - Moonraker, Mainsail K2-OpenHost, Crowsnest
  - /dev/k2-main, /dev/k2-nozzle, /dev/k2-rs485
  - USB diretto: telecamera della camera, Cartographer3D (opzionale)
```

- **Nessuna MCU viene riflashata** per il trasporto: il firmware Creality originale delle MCU resta al suo posto e comunica a 230400 baud attraverso i bridge.
- **La T113 non è più un computer**, solo uno schermo e un bridge. La sua porta di servizio passa in modalità USB device, ed è per questo che le telecamere e la porta USB esterna smettono di funzionare tramite lei: la telecamera della camera si ricabla all'host, quella del nozzle non si usa (vedi i [limiti](../DISCLAIMER.md#limiti-hardware-in-modalità-openhost)).
- **Lo slot A non viene mai scritto.** Il sistema K2-OpenHost vive nello slot B libero della T113, costruito dal firmware di Creality stesso. Uno spegnimento durante un avvio di prova torna allo slot A, e puoi tornare indietro in qualsiasi momento.

## Cosa gira sull'host

| Componente | Ruolo |
| --- | --- |
| **Kalico** `k2-pro-openhost` | Pianificazione dei movimenti, riscaldatori, le aggiunte K2: controllo dei motori closed-loop, PRTouch, `[z_align]`, lo stack CFS (`box`), ripresa dopo un'interruzione di corrente, KAMP, watchdog dei collegamenti |
| **Moonraker** | API per Mainsail, OrcaSlicer, HelixScreen, Home Assistant, Mobileraker |
| **Mainsail K2-OpenHost** | Interfaccia web con i pannelli CFS e motori |
| **Crowsnest** | Stream della telecamera collegata all'host |
| **Start gate** | `klipper.service` attende fino a 60 s i tre canali del gadget prima di avviare Klipper |
| **Controllo di salute** | Esegue il doctor dell'helper dopo ogni avvio e aggiornamento apt, e riporta nella console di Klipper |

## Cosa gira sulla T113 (slot B)

| Servizio | Ruolo |
| --- | --- |
| `k2oh-gadget` | Crea il gadget USB con tre funzioni seriali |
| `k2oh-bridge` | Un processo bridge per bus, riavviato entro 1 s se si blocca |
| `k2oh-mcu` | All'avvio: spegne e riaccende l'alimentazione delle MCU, esegue `mcu_update` di Creality, poi avvia i bridge |
| `k2oh-ctl` | Servizio di controllo per l'host: telemetria, cicalino, alimentazione MCU, riavvio dei bridge, riavvio di HelixScreen |
| HelixScreen | Interfaccia touch sullo schermo stock, collegata a Moonraker sull'host |
| `k2oh-helix-filaments` | Elenco filamenti per le build di HelixScreen precedenti alla 1.0.6-k2oh.8; spento con k2oh.8 o successive |
| `k2oh-mcu-fw` | Aggiornamenti manuali del firmware di MCU, motori e CFS con gli strumenti di Creality |

Klipper, Moonraker, nginx, app cloud, ADB e OTA da chiavetta USB di Creality sono disattivati nello slot B.

## Il CFS con K2-OpenHost

Il CFS è gestito dal modulo `box` di Kalico attraverso il canale RS-485. Kalico mantiene un inventario persistente degli slot e una libreria filamenti, legge i tag RFID (Creality, e Bambu/QIDI/MIFARE con il firmware CFS API7), stima il filamento residuo, abbina i tool dello slicer agli slot fisici all'avvio della stampa e passa a una bobina identica quando una finisce. Tutto è pubblicato come `printer.objects.box`, che Mainsail, HelixScreen, OrcaSlicer e Home Assistant leggono. Vedi [Usare il CFS](../usage/cfs.md).

## Livelli di sicurezza

- Le uscite dei riscaldatori hanno un `max_duration` di 3 s: se l'host smette di aggiornare una MCU, la MCU spegne da sola i suoi riscaldatori.
- Un collegamento perso con Main o Nozzle MCU manda Klipper in shutdown entro circa 5 s.
- Il bus RS-485 ha il suo watchdog (`[serial_485]`): un collegamento CFS/motori perso mette in pausa la stampa.
- `[k2_t113]` può togliere l'alimentazione alle MCU in caso di arresto di emergenza (`estop_on_shutdown: m112`).
- Aggiornamenti, riavvii e flash dei firmware vengono rifiutati durante la stampa.

Dettagli in [Perdita del collegamento seriale](../SERIAL_LINK_LOSS.md) e [Architettura](../ARCHITECTURE.md).
