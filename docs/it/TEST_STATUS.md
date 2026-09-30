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
| Identificazione seriale MCU principale K2 Pro | ✅ | `/dev/ttyS2` |
| Identificazione seriale MCU nozzle K2 Pro | ✅ | `/dev/ttyS3` |
| Identificazione seriale RS-485 / CFS | ✅ | `/dev/ttyS5` tramite `[serial_485 serial485]` in `box.cfg` |
| Conferma baud rate | ✅ | Main, nozzle e RS-485 configurati a 230400 baud |
| Arresto Klipper stock senza disturbare i servizi hardware | ✅ | `/etc/init.d/klipper stop`; `klipper_mcu -r` rimane attivo mentre le UART vengono liberate |
| Apertura UART Main MCU da processo di test | ✅ | `/dev/ttyS2` aperta correttamente dopo lo stop di Klippy stock |
| Bridge trasparente `ttyGS0 <-> ttyS2` | ✅ | Bridge Python volatile raw attivo a 230400 baud |
| Handshake Kalico con MCU principale originale | ✅ | La console Kalico sul CM5 si è connessa attraverso il bridge USB e ha decodificato traffico MCU reale |
| Handshake Kalico con MCU nozzle originale | ⏳ | Da eseguire |

### Identità Main MCU verificata

L'host esterno CM5 ha recuperato correttamente il protocol dictionary del Main MCU attraverso il percorso trasparente. I valori riportati includono:

- MCU: `gd32f303xe`
- Clock: `120000000`
- Baud seriale: `230400`
- Receive window: `192`
- Firmware build: `1.1.0.48-312-gcd5c2b81-dirty-20241227_092331-ubuntu`
- Toolchain: GNU Arm Embedded 9.2.1 / binutils 2.33.1

Dopo l'handshake, il CM5 ha ricevuto e decodificato messaggi live come `analog_in_state` e `stats`, confermando una reale comunicazione bidirezionale del protocollo Klipper con il Main MCU Creality originale.

Durante l'uso standalone di `console.py` è comparsa l'eccezione `DangerOptions has not been loaded yet!`, ma la connessione seriale è stata completata correttamente e la telemetria MCU ha continuato a essere decodificata. Il problema viene quindi classificato come incompatibilità del tool console standalone, non come errore di trasporto.

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
| Sessione live protocollo Main MCU | ✅ | La console Kalico è rimasta connessa e ha decodificato telemetria ricorrente |
| Test idle 1 ora | ⏳ | Da eseguire |
| Stampa lunga | ⏳ | Da eseguire |
| Recovery dopo reboot | 🟡 | Il comportamento stock USB host ritorna dopo reboot; automazione OpenHost non implementata |
| Watchdog / fail-safe | ⏳ | Da eseguire |

## Policy di sicurezza durante il reverse engineering

Tutti gli esperimenti attuali sullo slot stock funzionante sono esclusivamente runtime e devono essere completamente reversibili con un reboot. In questa fase non vengono modificati configurazione dello slot attivo, ambiente di boot, firmware MCU o stato persistente dei servizi.

## Milestone attuale

È stato completato il terzo importante milestone di piattaforma:

> **Un Raspberry Pi CM5 con Kalico ha stabilito con successo una sessione reale del protocollo Klipper con il Main MCU originale della K2 Pro passando attraverso l'Allwinner T113 stock, il connettore Micro-USB service, il Generic Serial gadget ConfigFS e un bridge byte-transparent `/dev/ttyGS0 <-> /dev/ttyS2`. L'host esterno ha recuperato il dictionary MCU e decodificato telemetria live senza riflashare o modificare il firmware del Main MCU.**

Il prossimo passo di validazione è ripetere lo stesso test sul Nozzle MCU originale collegato a `/dev/ttyS3`, quindi valutare una seconda funzione seriale gadget per far funzionare Main e Nozzle MCU contemporaneamente.
