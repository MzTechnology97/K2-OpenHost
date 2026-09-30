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
| Mappatura porta USB-A esterna rispetto a camera/Micro-USB | ⏳ | Da verificare se la porta USB-A esposta condivide lo stesso hub/controller della `CREALITY CAM` e/o della Micro-USB service/recovery usata dall'host esterno |

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
| Probe minimale del canale transparent | 🟡 | L'MCU accetta `config_transparent`, ma il frame di test restituisce payload vuoto; il controller a valle non era preparato su quel path |
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
| Collegamento CFS a OpenHost già attivo | ✅ | Il CFS collegato a caldo ha risposto senza riavviare la stampante |
| Discovery CFS `A1` dall'host esterno | ✅ | Tre richieste broadcast consecutive hanno restituito frame validi e identici |
| Tipo dispositivo CFS | ✅ | `0x01` = Material Box |
| Modalità application/loader CFS | ✅ | `0x00` = application mode |
| CRC risposta CFS | ✅ | CRC del frame discovery acquisito verificato |
| Unique ID CFS | ✅ | Ricevuto UniID a 12 byte; identificatore esatto intenzionalmente non pubblicato |
| Assegnazione indirizzo CFS (`A0`) | ⏳ | Non ancora eseguita |
| Online-check CFS dopo assegnazione (`A2`) | ⏳ | Da verificare dopo assegnazione controllata |
| Stato/operazioni filamento CFS | ⏳ | Da eseguire; nessun comando di movimento filamento inviato |

Percorso discovery verificato:

```text
Host esterno /dev/ttyUSB2
        -> T113 gser.usb2 / ttyGS2
        -> bridge byte-transparent
        -> /dev/ttyS5 @ 230400
        -> CFS
        -> risposta discovery A1 valida
```

Il box collegato ha risposto come Material Box non ancora indirizzato in application mode. La risposta contiene un UniID hardware valido a 12 byte e CRC valido. L'UniID viene deliberatamente omesso dalla documentazione pubblica.

Un precedente probe `A2` aveva prodotto quattro byte zero invece di un frame protocollo valido con header `F7`; non viene quindi classificato come risposta CFS. Subito dopo, tre discovery `A1` consecutive hanno prodotto frame puliti, identici e validi.

## Display / UI

| Test | Stato | Risultato |
|---|---:|---|
| Mantenimento display fisico originale K2 | 🟡 | Scelta progettuale confermata; deployment finale da validare |
| HelixScreen sul display originale K2 Pro | ⏳ | Pianificato |
| HelixScreen collegato a Moonraker remoto | ⏳ | Pianificato |
| Eliminazione dipendenza dallo stack UI Creality | ⏳ | Pianificato |

## Cartographer e connettore camera nozzle

L'unità K2 Pro usata per i test differisce intenzionalmente dal cablaggio stock.

| Test / scelta | Stato | Risultato |
|---|---:|---|
| Cartographer installato su percorso USB interno | ✅ | Funzionante sull'unità di test |
| Cartographer collegato tramite connettore camera della Nozzle MCU | ✅ | Il collegamento USB originariamente destinato alla camera nozzle è stato riutilizzato per Cartographer |
| Camera nozzle stock mantenuta | ❌ | Rimossa/non utilizzata intenzionalmente sull'unità di test |
| Necessità di un ulteriore cavo USB esterno per Cartographer | ✅ | No; il percorso USB interno della camera nozzle evita un cavo esterno aggiuntivo |
| Porta USB esterna della stampante lasciata libera | ✅ | Il cablaggio attuale evita di occupare l'unica porta USB esposta per Cartographer |

La camera nozzle stock è destinata al workflow Creality di calibrazione automatica legato a flusso/pressure. Questa funzione non è richiesta sull'unità di test attuale, quindi il relativo collegamento è stato deliberatamente riassegnato a Cartographer. Si tratta di una **scelta di cablaggio della macchina di test**, non di un requisito generale di K2-OpenHost.

Resta da verificare la relazione topologica esatta tra porta USB esterna, `CREALITY CAM` interna e percorso Micro-USB service/recovery.

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

> **Un singolo collegamento Micro-USB espone tre interfacce Generic Serial indipendenti dal T113 della K2 Pro verso un host Linux esterno. Main MCU, Nozzle MCU e RS-485 sono raggiungibili contemporaneamente; le query closed-loop X/Y funzionano end-to-end e un CFS fisicamente collegato restituisce ora frame discovery validi dall'host esterno attraverso lo stesso bridge RS-485. Non è stato necessario riflashare alcun MCU.**

Le prossime priorità sono assegnazione controllata indirizzo/online-check CFS, mappatura topologia USB, test reconnect/endurance, automazione boot, validazione forwarding Cartographer e successiva integrazione HelixScreen/Moonraker.
