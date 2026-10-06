# Stato test K2-OpenHost

Aggiornato al **6 ottobre 2026**.

## Sintesi

K2-OpenHost ha superato la sola validazione del trasporto. La K2 Pro reale raggiunge ora una baseline OpenHost funzionante con Main MCU, Nozzle MCU, motor-control RS-485, homing PRTouch, heater e test risonanza gestiti dal CM5/host Kalico esterno. Lo stack CFS/Box Jacobean gira ora in modalità operativa (`observation_mode: false`) nel servizio Kalico completo.

La prima stampa lunga è andata il 5-6 ottobre (PLA, stima 18 h 44 min), con associazione automatica dello slot, caricamento dal CFS e cambio bobina automatico a metà stampa. Restano da provare sull'hardware: Cartographer in **USB diretta al CM5**, una stampa a più colori con cambi utensile, pausa e ripresa con cambio slot, e la ripresa dopo un'interruzione di corrente.

## Verificato

### Host esterno / runtime Kalico

- Kalico gira come servizio principale su host Linux AArch64 basato su CM5;
- il C helper Kalico è stato ricompilato nativamente come **ELF64/AArch64**;
- source tree attiva: `MzTechnology97/kalico-k2pro`, branch `k2-pro-openhost`;
- Moonraker/Mainsail attivi;
- lo startup host attende i transport K2 prima di avviare Klippy.

### USB gadget

- Micro-USB di servizio funzionante come percorso device runtime;
- gadget Generic Serial composito a USB 2.0 High-Speed;
- tre interfacce `gser` simultanee verificate;
- traffico bidirezionale verificato su tutti e tre i canali.

### Main MCU

- percorso `/dev/ttyUSB0 -> ttyGS0 -> ttyS2`;
- 230400 baud;
- firmware GD32 Creality originale mantenuto;
- protocollo e telemetria Kalico live verificati.

### Nozzle MCU

- percorso `/dev/ttyUSB1 -> ttyGS1 -> ttyS3`;
- 230400 baud;
- sessione Kalico live simultanea al Main MCU.

### RS-485 / motor-control

- percorso `/dev/ttyUSB2 -> ttyGS2 -> ttyS5`;
- 230400 8N1;
- topologia closed-loop K2 Pro X/Y/E, con controller cinematici X/Y agli indirizzi `0x81`/`0x82`;
- startup esterno reso più robusto con delay e retry, così i fallimenti transitori al primo tentativo vengono recuperati automaticamente;
- movimenti CoreXY normali via G-code verificati;
- homing sensorless/stall X e Y verificato sull'hardware reale;
- direzione Z verificata;
- query fault motori senza fault X/Y/E attivi nei run validati.

Durante l'esperimento Cartographer MUX è stata scoperta una condizione di doppio bridge/process contention su GS2. Tornando a una singola istanza bridge diretta RS-485, la comunicazione motor-control è tornata normale. La topologia finale mantiene quindi GS2 dedicato a RS-485/CFS.

### Allineamento Z sul sensore di fondo corsa (`[z_align]`)

Verificato il 3 ottobre 2026: il `G28` integrato porta il piatto sul fotoelettrico di fondo corsa della K2 Pro (`PA15`), risale di 255 mm ed esegue l'homing Z con PRTouch. Tre cicli consecutivi `G28` / `M84` si sono allineati tutti al primo tentativo MCU (delta 0 step). Sono stati necessari le unità di step MCU originali Creality (rapporto di riduzione ignorato), i 16 microstep Z originali (a 64 la routine gestita dal MCU perdeva passi e falliva con errori fotoelettrici) e una discesa più lenta (`quick_speed`/`slow_speed` 6, circa 1,9 mm/s).

Da allora ogni homing nei log si è allineato al primo tentativo con delta 0: 16 volte il 5 ottobre, compreso l'avvio della stampa lunga.

### Homing completo con PRTouch

È stato eseguito con successo un homing completo con **PRTouch** originale attivo e Cartographer disabilitato. Questo valida coordinate e homing macchina indipendentemente da Cartographer.

### Heater e shutdown di emergenza

Sono stati testati con successo da Kalico esterno:

- nozzle heater;
- bed heater;
- chamber heater;
- relativo workflow PID tuning.

È stato inoltre provocato volontariamente un emergency shutdown con tutti gli heater attivi. Il consumo misurato della stampante è tornato quasi al livello idle, confermando lo spegnimento corretto dei carichi heater testati tramite il percorso di emergenza Klipper.

### Risonanza / accelerometro

Un test reale della risonanza con **Klippain-ShakeTune** è stato completato con successo sullo stack OpenHost, validando il percorso dati dell'accelerometro nozzle e l'analisi lato host.

### CFS

Verificati sulla K2 Pro reale:

- discovery A1;
- assegnazione indirizzo A0 a `0x01`;
- online check A2;
- address table A3;
- slot mask;
- buffer;
- percorsi RFID/materiale residuo;
- `BOX_STATE` K2 Pro steady a 4 byte;
- decoder eventi slot asincroni preservato.

UID e payload RFID privati non vengono pubblicati.

### Extra Jacobean CFS

- `Serial_485_Wrapper` verificato su `/dev/ttyUSB2`;
- `AutoAddressManager` + `BoxDriver` read-only verificati;
- `box_protocol.py` nativo patchato per lo stato K2 Pro a 4 byte;
- guardia fisica read-only verificata;
- vera classe `Box()` verificata in `observation_mode`;
- nessun G-code Box operativo durante l'osservazione;
- funzione mutante `0x0D` bloccata prima del TX;
- 10 poll live consecutivi stabili;
- `_poll()` interno completato;
- run di riferimento: **35 TX / 35 RX, tutti i contatori transport error a zero**.

Questo run in observation resta la baseline di sicurezza in sola lettura.

### CFS in modalità operativa

Il servizio Kalico completo sul CM5 esegue ora lo stack Box con `observation_mode: false`. Verificati sulla K2 Pro reale:

- enumeration CFS e stato normalizzato con `driver_ready=true` / `data_ready=true`;
- percorso di compatibilità `BOX_STATE` K2 Pro a 4 byte e stato load-path nel servizio attivo;
- temperatura e umidità del CFS;
- inventario filamenti persistente e import del database materiali Creality/K2-RFID;
- letture RFID per slot e rilettura RFID forzata per singolo slot;
- percentuale residua riportata dal CFS e stime residue indipendenti per bobina;
- ordinamento dei gruppi runout per minore percentuale residua compatibile nota;
- `BOX_PRINT_INFO` su file Orca realmente sliciati e auto-mapping backend contro l'inventario reale degli slot;
- la stima del residuo ha seguito la bobina RFID durante la stampa lunga (slot 2: 74 % stimato, mentre il tag segna ancora 95 %).

Dettagli: [Validazione CFS](CFS_VALIDATION.md) e [Mappatura CFS delle stampe](CFS_PRINT_MAPPING.md).

### Prima stampa lunga (5-6 ottobre 2026)

`Sodastream-Terra-Lever v5` in PLA, stima dello slicer 18 h 44 min, avviata normalmente da Mainsail il 5 ottobre alle 17:52. Nell'ordine:

- homing X/Y sensorless, `z_align` sul fotoelettrico di fondo (primo tentativo, delta 0), homing Z con PRTouch e compensazione termica;
- mesh adattiva 6×6 con PRTouch;
- associazione automatica di T0 a Box 1, slot 4 (`print_mapping.map = {"0": 3}`), caricamento dal CFS (1,48 m), spurgo di 100 mm nel cestino, T0 pronto in 91 s;
- dopo circa 7 ore la bobina dello slot 4 è finita e la stampa è proseguita da sola con lo slot 2 (sezione successiva).

All'89 %, dopo 15 ore, nessun errore. Il risultato finale lo aggiungo a stampa finita.

Collegamenti durante la stampa, da `link_monitor.csv` (930 righe da un minuto per canale):

| Canale | p50 | p99 (mediana delle righe) | caso peggiore | Ritrasmissioni / errori |
| --- | --- | --- | --- | --- |
| Main MCU | 1,17 ms | 5,25 ms | 18,8 ms | 0 byte |
| Nozzle MCU | 1,04 ms | 3,01 ms | 16,4 ms | 0 byte |
| RS-485 | 1,87 ms | 3,36 ms | 4,4 s (una lettura RFID) | 0 timeout, 0 errori CRC |

Sul T113 i tre bridge hanno perso 0 byte, con 0 errori di scrittura e senza mai accodare. Il CM5 è rimasto a 73–76 °C. `vcgencmd get_throttled` dà `0xe0000`: dall'avvio (13:37, prima della stampa) la CPU ha toccato il limite termico morbido ed è stata limitata almeno una volta; al momento della lettura non lo era.

### Cambio bobina automatico durante la stampa (6 ottobre 2026)

- Il CFS ha segnalato la fine della bobina nello slot 4. Circa 14 minuti e mezzo dopo è scattato il sensore della testa, dopo aver stampato il filamento rimasto nel tubo.
- Il cambio ha aspettato il primo tratto di riempimento (`gap infill`). Poi: Box 1, slot 4 → Box 1, slot 2 (stesso PLA, con tag RFID), 33 mm per liberare gli ingranaggi, caricamento dal CFS, 63 mm fino all'hotend, 20 mm di spurgo, ritorno al pezzo.
- `print_mapping.map` è diventata `{"0": 1}`. Lo slot di partenza ha tenuto il suo profilo finché il cambio non è stato deciso, poi lo slot vuoto è stato azzerato, come previsto.
- Nessun intervento.

### Watchdog del collegamento RS-485, dal vivo

Il 5 ottobre alle 17:40, a stampante ferma, nessun dispositivo RS-485 (CFS, motori X e Y) ha risposto per circa 30 s; poi sono arrivati 2 errori CRC e un gruppo di frame senza corrispondenza. Il watchdog ha segnalato `RS-485 link lost` e poi `RS-485 link restored` da solo, e Klipper è rimasto `ready`. I bridge del T113 non hanno perso niente e nessun altro processo aveva la porta aperta, né sul CM5 né sul T113. Probabilmente è successo mentre collegavo una webcam USB al CM5, sullo stesso hub del T113. Dettagli in [Perdita del collegamento seriale](SERIAL_LINK_LOSS.md).

### Riavvio del CM5

Il 5 ottobre il CM5 è stato riavviato da Moonraker. È tornato in circa 15 s con le porte seriali, Klipper `ready`, RS-485, CFS e motori; i bridge del T113 hanno riaperto le porte da soli (stessi PID). CPU a riposo: klippy 1,3 %, ogni bridge 0,1–0,5 %. Dettagli in [Bridge USB](USB_BRIDGE.md).

### Slot B del T113 (6 ottobre 2026)

Il [bootstrap del T113](T113_BOOTSTRAP.md) gira sulla stampante di riferimento: slot B 0.1.1 installato con l'installer helper e confermato come predefinito. Dopo uno spegnimento e una riaccensione completi la stampante è ripartita da sola: `k2oh-mcu` ha avviato le schede, poi i bridge, e Klipper sul CM5 era pronto senza `FIRMWARE_RESTART` (CFS OK, `[k2_t113]` connesso, HelixScreen sul pannello). La prima installazione (0.1.0) ha trovato sei problemi, tutti corretti; dettagli in [Bootstrap del T113](T113_BOOTSTRAP.md#stato).

### Aggiornamento firmware delle MCU dallo slot B (6 ottobre 2026)

`k2oh-mcu-fw update` ha portato le schede alla 1.1.7.0 di Creality: motori X/Y ed estrusore `mot2_…071` → `081`, RFID `009` → `010`, Main e Nozzle invariate. È stato aggiornato anche il CFS (113 → 153), anche se non era stato chiesto: `mcu_util_485` segue `fw/cfs/version.json` a ogni esecuzione. Un'immagine CFS personalizzata (diagnostica RFID v2.1) non è partita (`start_app NACK`) e il CFS è stato ripristinato con lo stock 153. Entrambi sono corretti nel bootstrap 0.1.2; dettagli in [Bootstrap del T113](T113_BOOTSTRAP.md#stato).

### Plugin Cartographer / bridge sperimentale

Il plugin K2/OpenHost Cartographer è stato installato come pacchetto editable e il relativo adapter Kalico viene caricato correttamente. Durante l'esperimento MUX/DEMUX sul T113:

- è stata stabilita la comunicazione con MCU Cartographer V4;
- traffico live `cartographer_data` e ADC/temperatura è arrivato a Kalico esterno;
- configurazione plugin e caricamento `register_as_probe: true` sono stati validati.

Il bridge sperimentale **non** è il trasporto finale. Reset/re-enumeration Cartographer e lifecycle delle PTY rendono inutile la complessità quando è disponibile USB diretta sul CM5; inoltre un test è stato influenzato da un processo bridge GS2 duplicato. La topologia preferita è quindi Cartographer USB diretto al CM5.

Il plugin Cartographer ufficiale offre `register_as_probe: false` per il futuro mixed mode PRTouch + Cartographer. Il workflow Z automatico mixed non è ancora validato su hardware.

## Integrazione repository

`MzTechnology97/k2-pro-custom-firmware:k2-openhost` contiene la prima history versionata degli extra K2/Jacobean e delle patch OpenHost. È stato archiviato il 4 ottobre 2026; gli extra si mantengono in `kalico-k2pro:k2-pro-openhost`.

`MzTechnology97/kalico-k2pro:k2-pro-openhost` contiene il tree Kalico integrato per host esterno, incluso motor-control K2 e loader tracciati.

Cartographer usa il plugin ufficiale `Cartographer3D/cartographer3d-plugin` (1.9.0 installato sul CM5 di riferimento il 4 ottobre 2026; il fork K2-OpenHost è stato dismesso). Guida USB diretta e ruoli della sonda in [CARTOGRAPHER.md](CARTOGRAPHER.md).

## Da fare

Le procedure passo passo per le prove fisiche qui sotto sono nel [piano dei test hardware](HARDWARE_TEST_PLAN.md).

- Cartographer in USB diretta al CM5: `/dev/serial/by-id/...` persistente, reset e riconnessione automatici, probing/touch/scan da solo, poi eventualmente PRTouch + Cartographer insieme (T5);
- una stampa a più colori avviata con `BOX_PRINT_START` dalla finestra di Mainsail: cambio utensile con la matrice di spurgo del file e le temperature per utensile (T2);
- pausa e ripresa con cambio slot durante la pausa (seconda metà di T1), che prova anche il flusso di pausa di 071c813 (`_BOX_PAUSE_CAPTURE` / `_BOX_RESUME_PREPARE` / `_BOX_RESUME_COMMIT`);
- `PLR_RECOVER` dopo un'interruzione di corrente controllata, monocolore e a due colori (T4);
- il watchdog RS-485 che mette in pausa una stampa vera: finora è andato solo il caso a stampante ferma;
- il rilevamento del CFS quando l'RS-485 è giù all'avvio di Klipper (kalico-k2pro #24, unita, non ancora vista dal vivo);
- un `k2oh-mcu-fw apply --cfs` originale con la lista CFS messa da parte del bootstrap 0.1.2, e l'installazione dell'immagine 0.1.2;
- un'immagine CFS personalizzata rivista (l'immagine diagnostica RFID v2.1 non è partita, vedi sopra);
- il pressure advance con la cella di carico dell'ugello (kalico-k2pro #29, in bozza): archiviato il 6 ottobre 2026 come da sviluppare, il modulo è disattivato; i risultati sono in `docs/K2_Load_Cell_PA.md` di kalico-k2pro;
- proseguire con lo split UI e il futuro percorso display sul T113.

## Non ancora production-ready

Il milestone attuale dimostra molto più della sola fattibilità del transport: movimento reale, homing completo PRTouch, heater, emergency shutdown e analisi risonanza funzionano da host esterno. È andata anche una stampa di 18 ore con associazione automatica e cambio bobina. Il progetto resta pre-production finché non sono provati Cartographer in USB diretta, la stampa CFS a più colori, pausa e ripresa e la ripresa dopo un'interruzione di corrente.