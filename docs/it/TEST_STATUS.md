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
| Identificazione camera interna su USB0 | ✅ | `1d6c:0103 CREALITY CAM` |
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
| Passaggio USB0 a device mode | ✅ | Switch runtime verificato |
| Creazione gadget iniziale tramite tool vendor | ✅ | `/bin/setusbconfig gser` funzionante |
| Creazione `gser.usb0` / `/dev/ttyGS0` | ✅ | Verificata |
| Aggiunta `gser.usb1` / `/dev/ttyGS1` | ✅ | Funzione ConfigFS e porta 1 verificate |
| Aggiunta `gser.usb2` / `/dev/ttyGS2` | ✅ | Funzione ConfigFS e porta 2 verificate |
| Binding di tre seriali nello stesso gadget | ✅ | Tutte collegate a `configs/c.1` |
| Binding gadget all'UDC | ✅ | `4100000.udc-controller` |
| VID/PID verificati | ✅ | `0525:a4a6` |
| Product string verificata | ✅ | `Gadget Serial` |

## Collegamento fisico Micro-USB

| Test | Stato | Risultato |
|---|---:|---|
| Conferma Micro-USB come connettore runtime USB0 device | ✅ | L'host Linux esterno enumera il gadget K2 dalla porta service/recovery |
| Negoziazione high-speed | ✅ | 480M |
| Esposizione di una seriale | ✅ | `/dev/ttyUSB0` |
| Esposizione di due seriali | ✅ | `/dev/ttyUSB0` + `/dev/ttyUSB1` |
| Esposizione di tre seriali | ✅ | `/dev/ttyUSB0` + `/dev/ttyUSB1` + `/dev/ttyUSB2` |
| Binding driver host | ✅ | Tutte e tre le interfacce usano `usbserial_generic` |
| Trasferimento bidirezionale byte | ✅ | Verificato |
| Recovery disconnessione/riconnessione | 🟡 | La re-enumerazione funziona; i bridge devono essere riavviati dopo unbind/rebind |
| Stabilità con role switch ripetuti | ⏳ | Endurance test da eseguire |

## Mappatura MCU

| Test | Stato | Risultato |
|---|---:|---|
| Seriale Main MCU | ✅ | `/dev/ttyS2` |
| Seriale Nozzle MCU | ✅ | `/dev/ttyS3` |
| Seriale RS-485 / CFS | ✅ | `/dev/ttyS5` |
| Baud rate | ✅ | Main, Nozzle e RS-485 a 230400 baud |
| Stop Klipper stock e rilascio UART | ✅ | Test runtime riuscito |
| Bridge raw `ttyGS0 <-> ttyS2` | ✅ | Main MCU |
| Bridge raw `ttyGS1 <-> ttyS3` | ✅ | Nozzle MCU |
| Bridge raw `ttyGS2 <-> ttyS5` | ✅ | Bus RS-485 |
| Handshake Kalico con Main MCU | ✅ | Dictionary e telemetria live decodificati |
| Handshake Kalico con Nozzle MCU | ✅ | Dictionary e telemetria live decodificati |
| Sessioni Main + Nozzle simultanee | ✅ | Due interfacce seriali host concorrenti verificate |

### Identità Main MCU verificata

- MCU: `gd32f303xe`
- Clock: `120000000`
- Baud seriale: `230400`
- Receive window: `192`
- Firmware build: `1.1.0.48-312-gcd5c2b81-dirty-20241227_092331-ubuntu`

### Identità Nozzle MCU verificata

- MCU: `gd32f303xb`
- Clock: `120000000`
- Baud seriale: `230400`
- Receive window: `192`
- Firmware build: `1.1.0.48-293-g493f9a0f-dirty-20241220_143931-ubuntu1804`

La `console.py` standalone di Kalico può mostrare `DangerOptions has not been loaded yet!`, ma le connessioni protocollo e la telemetria live continuano. Il problema è classificato come incompatibilità del tool console e non come errore di trasporto.

## Trasporto multi-canale

| Test | Stato | Risultato |
|---|---:|---|
| Creazione `gser.usb1` | ✅ | Porta 1 |
| Creazione `gser.usb2` | ✅ | Porta 2 |
| Esposizione di tre seriali host | ✅ | Interfacce 0/1/2 enumerate a 480M |
| Main + Nozzle simultanei | ✅ | Sessioni concorrenti verificate |
| RS-485 come terzo canale simultaneo | ✅ | `ttyUSB2 -> ttyGS2 -> ttyS5` verificato |
| Stress test di tutti i canali durante stampa | ⏳ | Da eseguire |

## Motori closed-loop / RS-485

| Test | Stato | Risultato |
|---|---:|---|
| Comandi transparent presenti nei dictionary MCU stock | ✅ | Main e Nozzle espongono `config_transparent` e `transparent_send` |
| Uso stock di `transparent_send` nei log | ✅ | I log storici contengono `transparent_response` validi |
| Probe minimale del canale transparent | 🟡 | L'MCU accetta `config_transparent`, ma il frame di test restituisce payload vuoto; il percorso raggiunge l'MCU ma il motore non era ancora preparato su quel path |
| Apertura diretta `/dev/ttyS5` | ✅ | 230400 8N1 |
| Necessità ioctl RS-485 Linux | ✅ | Non richiesta per il traffico testato; flag `TIOCGRS485` disabilitati |
| Query diretta controller X dal T113 | ✅ | Indirizzo `0x81` risponde correttamente |
| Query X dall'host esterno via terzo canale USB | ✅ | Risposta end-to-end verificata |
| Query Y dall'host esterno via terzo canale USB | ✅ | Indirizzo `0x82` risponde correttamente |
| Trasporto pratico closed-loop dall'host esterno | ✅ | Il bridge raw verso `/dev/ttyS5` funziona per query read-only X/Y |
| Operazioni di scrittura/tuning | ⏳ | Non ancora eseguite; nessun parametro controller persistente modificato |

Risultati read-only verificati:

```text
X TX: f7 81 04 00 0e 02 80
X RX: f7 81 04 00 0e 81 00

Y TX: f7 82 04 00 0e 02 80
Y RX: f7 82 04 00 0e 82 09
```

## CFS

| Test | Stato | Risultato |
|---|---:|---|
| Identificazione UART host CFS/RS-485 | ✅ | `/dev/ttyS5` |
| Esposizione UART CFS/RS-485 all'host esterno | ✅ | Terza seriale gadget verificata |
| Probe CFS `A2` online-check | 🟡 | Nessuna risposta, ma il CFS era fisicamente scollegato |
| Probe CFS `A1` discovery | 🟡 | Nessuna risposta, ma il CFS era fisicamente scollegato |
| Validazione CFS collegato dall'host esterno | ⏳ | Prossimo test CFS con hardware collegato |

I test CFS senza risposta **non vengono classificati come fallimenti**, perché l'unità CFS era scollegata. Il trasporto è comunque validato indipendentemente dal traffico X/Y riuscito sullo stesso `/dev/ttyS5`.

## Display / UI

| Test | Stato | Risultato |
|---|---:|---|
| Mantenimento display fisico originale K2 | 🟡 | Scelta progettuale confermata; deployment finale da validare |
| HelixScreen sul display originale K2 Pro | ⏳ | Pianificato |
| HelixScreen collegato a Moonraker remoto | ⏳ | Pianificato |
| Eliminazione dipendenza dallo stack UI Creality | ⏳ | Pianificato |

## Cartographer

| Test | Stato | Risultato |
|---|---:|---|
| Cartographer su percorso USB interno separato | ✅ | Non coinvolto dal role switch USB0 |
| Cartographer diretto sull'host esterno | ⏳ | Pianificato |

## Affidabilità

| Test | Stato | Risultato |
|---|---:|---|
| Test breve serial gadget | ✅ | Traffico bidirezionale verificato |
| Sessione live Main MCU | ✅ | Verificata |
| Sessione live Nozzle MCU | ✅ | Verificata |
| Enumerazione tre interfacce | ✅ | Verificata |
| Unbind/rebind gadget | 🟡 | Le interfacce ricompaiono; i bridge aperti terminano e vanno riavviati |
| Test idle 1 ora | ⏳ | Da eseguire |
| Stampa lunga | ⏳ | Da eseguire |
| Recovery dopo reboot | 🟡 | Il comportamento USB host stock ritorna dopo reboot; automazione OpenHost non implementata |
| Watchdog / fail-safe | ⏳ | Da eseguire |

## Policy di sicurezza durante il reverse engineering

Tutti gli esperimenti attuali sullo slot stock funzionante sono esclusivamente runtime e reversibili con reboot. In questa fase non vengono modificati configurazione dello slot attivo, ambiente di boot, firmware MCU, stato persistente di enable dei servizi o parametri persistenti dei controller motore.

## Milestone attuale

Il milestone di trasporto attuale è verificato su hardware:

> **Un singolo collegamento Micro-USB espone tre interfacce Generic Serial indipendenti dal T113 della K2 Pro verso un host Linux esterno. I tre canali sono stati validati come Main MCU (`ttyS2`), Nozzle MCU (`ttyS3`) e RS-485 (`ttyS5`). Le sessioni protocollo Klipper Main e Nozzle possono funzionare contemporaneamente, mentre il terzo canale RS-485 ha interrogato con successo entrambi i controller closed-loop X e Y originali end-to-end dall'host esterno. Non è stato necessario riflashare alcun MCU.**

Le prossime priorità sono la validazione CFS con unità collegata, test di reconnect/endurance, automazione boot e successiva integrazione HelixScreen/Moonraker.
