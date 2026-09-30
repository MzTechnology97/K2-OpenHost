# Stato dei test

Questo documento tiene traccia dello stato di validazione di K2-OpenHost.

Legenda:

- ✅ Verificato su hardware
- 🟡 Verificato parzialmente / risultato intermedio
- ⏳ Pianificato / non ancora testato
- ❌ Fallito / smentito

## Identificazione piattaforma

| Voce | Stato | Note |
|---|---:|---|
| Tina Linux 5.0 / OpenWrt 21.02-SNAPSHOT confermato | ✅ | Verificato sulla K2 Pro di test |
| Kernel Linux 5.4.61 confermato | ✅ | Verificato sulla K2 Pro di test |
| Infrastruttura Allwinner USB0 dual-role presente | ✅ | UDC e OTG manager visibili in sysfs |

## Percorso USB0 / camera

| Test | Stato | Risultato |
|---|---:|---|
| Identificazione controller USB0 host | ✅ | `4101000.ehci0-controller` |
| Identificazione controller USB0 OHCI | ✅ | `4101400.ohci0-controller` |
| Identificazione camera interna su USB0 | ✅ | `1d6c:0103 CREALITY CAM` su Bus 003 |
| Disconnessione camera durante role switch | ✅ | Disconnessione pulita osservata in dmesg |
| Rimozione controller host | ✅ | EHCI0 e OHCI0 rimossi |

## Supporto USB gadget

| Test | Stato | Risultato |
|---|---:|---|
| Presenza UDC | ✅ | `4100000.udc-controller` |
| `CONFIG_USB_GADGET=y` | ✅ | Presente |
| `CONFIG_USB_CONFIGFS=y` | ✅ | Presente |
| `CONFIG_USB_F_SERIAL=y` | ✅ | Presente |
| `CONFIG_USB_CONFIGFS_SERIAL=y` | ✅ | Presente |
| `CONFIG_USB_CONFIGFS_F_FS=y` | ✅ | Presente |
| Passaggio USB0 a device mode | ✅ | `cat .../usb_device` ha restituito `device_chose finished!` |
| Creazione gadget ConfigFS tramite tool vendor | ✅ | `/bin/setusbconfig gser` exit 0 |
| Creazione `/dev/ttyGS0` | ✅ | Character device creato |
| Creazione funzione `gser.usb0` | ✅ | Verificata in ConfigFS |
| Binding gadget all'UDC | ✅ | `4100000.udc-controller` |
| VID/PID verificati | ✅ | `0525:a4a6` |
| Product string verificata | ✅ | `Gadget Serial` |

## Collegamento fisico Micro-USB

| Test | Stato | Risultato |
|---|---:|---|
| Conferma Micro-USB come connettore runtime USB0 device | ✅ | Il CM5 ha enumerato il gadget K2 attraverso il connettore Micro-USB service/recovery |
| Enumerazione `0525:a4a6` su host Linux | ✅ | Rilevato come `Netchip Technology, Inc. Linux-USB Serial Gadget` |
| Creazione `/dev/ttyUSB0` lato host | ✅ | Binding eseguito con `usbserial_generic` tramite `new_id` |
| Trasferimento host -> K2 | ✅ | `K2_OPENHOST_CM5_TO_K2_001` ricevuto su `/dev/ttyGS0` |
| Trasferimento K2 -> host | ✅ | `K2_OPENHOST_K2_TO_CM5_001` ricevuto su `/dev/ttyUSB0` |
| Negoziazione high-speed | ✅ | Albero USB a 480M; UDC K2 con `current_speed: high-speed` |
| UDC K2 in stato configured | ✅ | `state: configured`, `function: g1` |
| Recovery dopo disconnessione/riconnessione | ⏳ | Da eseguire |
| Stabilità con role switch ripetuti | ⏳ | Da eseguire |

## Mappatura MCU

| Test | Stato | Risultato |
|---|---:|---|
| Identificazione seriale MCU principale K2 Pro | ⏳ | Da eseguire |
| Identificazione seriale MCU nozzle K2 Pro | ⏳ | Da eseguire |
| Conferma baud rate | ⏳ | Da eseguire |
| Arresto Klipper stock senza disturbare i servizi hardware | ⏳ | Da eseguire |
| Apertura UART MCU da processo di test | ⏳ | Da eseguire |
| Bridge trasparente `ttyGSx <-> ttySx` | ⏳ | Da eseguire |
| Handshake Kalico con MCU principale originale | ⏳ | Da eseguire |
| Handshake Kalico con MCU nozzle originale | ⏳ | Da eseguire |

## Trasporto multi-canale

| Test | Stato | Risultato |
|---|---:|---|
| Creazione `gser.usb1` / seconda seriale gadget | ⏳ | Da eseguire |
| Esposizione di due seriali all'host Linux | ⏳ | Da eseguire |
| Link main + nozzle MCU simultanei | ⏳ | Da eseguire |
| Stress test di entrambi i canali durante stampa | ⏳ | Da eseguire |

## Display / UI

| Test | Stato | Risultato |
|---|---:|---|
| Mantenimento display fisico originale K2 | 🟡 | Scelta progettuale confermata; deployment finale OpenHost da validare |
| HelixScreen sul display originale K2 Pro | ⏳ | Pianificato |
| HelixScreen collegato a Moonraker remoto | ⏳ | Pianificato |
| Eliminazione dipendenza dallo stack UI Creality | ⏳ | Pianificato |

## Cartographer

| Test | Stato | Risultato |
|---|---:|---|
| Cartographer visibile sul percorso USB1 | ✅ | `1d50:614e Cartographer stm32g431xx` tramite hub interno |
| USB0 role switch separato dal bus Cartographer | ✅ | Cartographer non si trova su USB0 |
| Collegamento Cartographer diretto all'host esterno | ⏳ | Pianificato |

## Motori closed-loop / CFS

| Test | Stato | Risultato |
|---|---:|---|
| Riutilizzo riferimenti pubblici di reverse engineering | 🟡 | Documentazione pubblica identificata |
| Determinazione trasporto richiesto per closed-loop | ⏳ | Da eseguire |
| Validazione controllo motori dall'host Kalico esterno | ⏳ | Da eseguire |
| Validazione CFS dall'host esterno | ⏳ | Da eseguire |

## Affidabilità

| Test | Stato | Risultato |
|---|---:|---|
| Test breve serial gadget | ✅ | Traffico bidirezionale CM5 <-> K2 verificato |
| Test idle 1 ora | ⏳ | Da eseguire |
| Stampa lunga | ⏳ | Da eseguire |
| Recovery dopo reboot | 🟡 | Il comportamento stock USB host ritorna dopo reboot; automazione OpenHost non implementata |
| Watchdog / fail-safe | ⏳ | Da eseguire |

## Milestone attuale

È stato completato il secondo importante milestone di piattaforma:

> **Il connettore Micro-USB service/recovery della K2 Pro è stato verificato come percorso USB device funzionante a runtime. Un Raspberry Pi CM5 enumera correttamente il Generic Serial gadget ConfigFS del T113 stock come `0525:a4a6`, lo associa a `/dev/ttyUSB0`, negozia USB 2.0 High-Speed (480M) e scambia dati bidirezionalmente con `/dev/ttyGS0` lato K2.**

Il prossimo milestone è identificare le UART degli MCU Main e Nozzle della K2 Pro e validare un bridge byte-transparent `ttyGSx <-> ttySx` senza modificare il firmware originale degli MCU.
