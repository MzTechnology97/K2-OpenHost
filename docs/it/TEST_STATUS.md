# Stato test K2-OpenHost

Aggiornato al **2 ottobre 2026**.

## Sintesi

K2-OpenHost ha superato la sola validazione del trasporto. La K2 Pro reale raggiunge ora una baseline OpenHost funzionante con Main MCU, Nozzle MCU, motor-control RS-485, homing PRTouch, heater e test risonanza gestiti dal CM5/host Kalico esterno. Lo stack CFS/Box Jacobean gira ora in modalità operativa (`observation_mode: false`) nel servizio Kalico completo.

I principali elementi hardware ancora da chiudere sono Cartographer sulla topologia preferita **USB diretta al CM5**, un `BOX_PRINT_START` mappato e controllato con cambi materiale reali e la validazione completa del print path.

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
- `BOX_PRINT_INFO` su file Orca realmente sliciati e auto-mapping backend contro l'inventario reale degli slot.

Dettagli: [Validazione CFS](CFS_VALIDATION.md) e [Mappatura CFS delle stampe](CFS_PRINT_MAPPING.md).

### Plugin Cartographer / bridge sperimentale

Il plugin K2/OpenHost Cartographer è stato installato come pacchetto editable e il relativo adapter Kalico viene caricato correttamente. Durante l'esperimento MUX/DEMUX sul T113:

- è stata stabilita la comunicazione con MCU Cartographer V4;
- traffico live `cartographer_data` e ADC/temperatura è arrivato a Kalico esterno;
- configurazione plugin e caricamento `register_as_probe: true` sono stati validati.

Il bridge sperimentale **non** è il trasporto finale. Reset/re-enumeration Cartographer e lifecycle delle PTY rendono inutile la complessità quando è disponibile USB diretta sul CM5; inoltre un test è stato influenzato da un processo bridge GS2 duplicato. La topologia preferita è quindi Cartographer USB diretto al CM5.

Il fork Cartographer contiene anche supporto `register_as_probe: false` per il futuro mixed mode PRTouch + Cartographer. Il workflow Z automatico mixed non è ancora validato su hardware.

## Integrazione repository

`MzTechnology97/k2-pro-custom-firmware:k2-openhost` contiene la history versionata degli extra K2/Jacobean e delle patch OpenHost.

`MzTechnology97/kalico-k2pro:k2-pro-openhost` contiene il tree Kalico integrato per host esterno, incluso motor-control K2 e loader tracciati.

`MzTechnology97/cartographer3d-plugin-k2openhost` contiene plugin Cartographer K2/OpenHost, guida direct-USB, mixed mode e documentazione Moonraker update-manager.

## Da fare

- collegare Cartographer direttamente alla USB host del CM5 e validare il path persistente `/dev/serial/by-id/...`;
- validare reset/reconnect automatico Cartographer su USB diretta;
- validare probing/touch/scan Cartographer standalone sull'host esterno;
- eventualmente validare mixed mode PRTouch + Cartographer dopo la stabilità standalone;
- validare sensore filamento reale e transizioni loaded-path durante load/unload supervisionati;
- validare un `BOX_PRINT_START` controllato con singolo tool, poi un cambio materiale mappato multimateriale inclusi purge matrix e temperature;
- validare runout/recovery durante un job mappato e la stima residua RFID live su una stampa completa;
- adottare il flusso pausa/ripresa Box upstream insieme al relativo `box.py`; fino ad allora le macro K2 Pro mantengono il percorso `_BOX_RESUME_CHECK` esistente (le macro K2 Plus importate sono state annullate il 3 ottobre 2026 perché chiamavano comandi assenti nel Box engine attuale);
- implementare un power-loss recovery sicuro per K2 Pro; il `power_loss_recovery` upstream richiede `[z_align]`, presente solo sulla K2 Plus, ed è disattivato;
- completare la prima validazione del print path completo: homing, heating, mesh/probing, estrusione e fine stampa;
- proseguire con lo split UI e il futuro percorso display sul T113.

## Non ancora production-ready

Il milestone attuale dimostra molto più della sola fattibilità del transport: movimento reale, homing completo PRTouch, heater, emergency shutdown e analisi risonanza funzionano da host esterno. Il progetto resta pre-production fino alla validazione di Cartographer direct USB, della stampa CFS mappata e di un ciclo di stampa completo.