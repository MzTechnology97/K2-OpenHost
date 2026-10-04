# Roadmap K2-OpenHost

La roadmap è guidata dalla validazione: una fase successiva parte solo quando quella precedente è dimostrata sulla K2 Pro.

Aggiornata al **2 ottobre 2026**.

## Fondamenta completate

- identificazione UDC e supporto gadget del T113;
- Micro-USB di servizio validata come device path runtime;
- tre Generic Serial simultanee;
- bridge Main MCU, Nozzle MCU e RS-485;
- sessioni MCU Kalico simultanee;
- ricompilazione nativa AArch64 del C helper Kalico;
- comunicazione closed-loop X/Y e recovery startup motor-control;
- movimenti CoreXY normali;
- homing sensorless/stall X/Y e direzione Z corretta;
- homing completo con PRTouch stock;
- heater bed/nozzle/chamber e PID tuning;
- emergency shutdown con rimozione del carico heater;
- test risonanza Klippain-ShakeTune completato;
- discovery/address/read CFS;
- BoxDriver Jacobean sul trasporto OpenHost;
- decoder Box state 4-byte K2 Pro;
- guardia CFS observation;
- vera `Box()` in observation mode;
- stack Box in modalità operativa nel servizio Kalico completo, inclusi stato load-path, letture RFID per slot e rilettura forzata;
- inventario filamenti persistente, risoluzione database materiali K2-RFID e tracciamento percentuale residua;
- `BOX_PRINT_INFO` e auto-mapping backend contro l'inventario reale degli slot;
- patch versionate in `k2-pro-custom-firmware:k2-openhost`;
- assemblaggio `kalico-k2pro:k2-pro-openhost` con baseline K2 Pro ed extra K2;
- ~~creazione `cartographer3d-plugin-k2openhost`~~ superato: il plugin Cartographer ufficiale copre K2/Kalico e `register_as_probe` (fork dismesso il 4 ottobre 2026); la guida USB diretta è in [CARTOGRAPHER.md](CARTOGRAPHER.md);
- trasporto reale di dati MCU Cartographer attraverso un MUX/DEMUX T113 sperimentale, poi abbandonato come percorso finale a favore della USB diretta per la complessità di reset/re-enumeration.
- mappa GPIO di servizio T113 stock recuperata: MCU power, nozzle camera, buzzer, USB hub reset e UDISK power; polarità verificate dagli script Creality;


## Linea parallela — control plane GPIO T113

- mantenere `ttyGS0..2` dedicati e byte-transparent;
- non usare il quarto `gser.usb3` come requisito: il bind UDC non è stato validato;
- usare nomi logici invece dei numeri GPIO raw;
- validare sul T113 `tools/t113-gpio-control.sh` prima solo con `status`/buzzer, poi con segnali disruptive;
- scegliere un trasporto CM5 -> T113 che non interferisca con Main/Nozzle/RS-485;
- integrare preflight Moonraker (idle + heater target zero) prima di `mcu-power cycle`;
- usare il power-cycle hardware come possibile gate per i futuri probe loader Main/Nozzle/motori/CFS.

## Fase 1 — Cartographer USB diretto sul CM5

- collegare Cartographer direttamente alla USB host del CM5;
- configurare un path persistente `/dev/serial/by-id/...`;
- validare cold boot, automated reset e reconnect;
- validare Cartographer standalone con `register_as_probe: true`;
- validare probe/touch/scan controllati prima di qualunque movimento Z non supervisionato;
- validare una bed mesh reale da host esterno.

I tre canali gadget T113 restano dedicati a Main MCU, Nozzle MCU e RS-485/CFS.

## Fase 2 — mixed mode PRTouch + Cartographer opzionale

Solo dopo la stabilità Cartographer standalone:

- impostare `register_as_probe: false`;
- mantenere PRTouch come `probe` canonico e riferimento fisico nozzle-to-bed Z;
- mantenere Cartographer disponibile per scan/mesh con namespace endstop separato;
- verificare che i comandi probe standard restino di PRTouch;
- validare homing e mesh separatamente prima di combinarli nelle automazioni start-print.

Il mixed mode è opzionale e non è necessario per il primo profilo OpenHost production-capable.

## Fase 3 — prima validazione print path completo

- verificare estrusore e protezioni temperatura;
- validare pressure advance/retraction migrati dalla configurazione macchina nota funzionante;
- eseguire homing + heating + mesh/probing + estrusione nello stesso workflow controllato;
- eseguire la prima stampa supervisionata dallo stack OpenHost sul CM5;
- verificare pause/resume, cancel ed emergency stop durante una stampa reale;
- verificare recovery da restart e persistenza configurazione.

## Fase 4 — mutazioni CFS controllate

Stato Box in modalità operativa, letture RFID e auto-mapping sono già validati (vedi fondamenta completate). Resta da fare:

- validare le transizioni loaded-path durante load/unload reali;
- validare un `BOX_PRINT_START` controllato con singolo tool, poi un cambio materiale mappato multimateriale;
- abilitare una funzione mutante alla volta;
- testare load/unload con supervisione meccanica;
- validare cutter, buffer e runout recovery;
- mantenere visibili contatori transport/error e procedure di rollback.

## Fase 5 — UI

- mantenere Moonraker e planner principale sul CM5;
- valutare HelixScreen o altra UI leggera sul T113 con LCD/touch originali;
- ridurre le responsabilità del T113 a UI e bridge hardware.

Implementato offline nel [bootstrap del T113](T113_BOOTSTRAP.md): lo slot B esegue solo gadget, bridge, Wi-Fi e HelixScreen collegato al Moonraker dell'host esterno. In attesa di validazione su hardware.

## Fase 6 — deployment persistente

Solo dopo la validazione completa di runtime e print stack:

- startup persistente dei bridge — [bootstrap del T113](T113_BOOTSTRAP.md), costruito offline;
- boot/recovery — avvio di prova dello slot B, spegnendo e riaccendendo si torna allo slot A;
- conservazione slot stock funzionante — lo slot A non viene mai scritto;
- aggiornamento firmware delle periferiche con gli strumenti Creality — `k2oh-mcu-fw`, CFS compreso, costruito offline;
- procedura di update/rebase rispetto a Jacob/Kalico/Jacobean/Cartographer;
- procedura riproducibile di installazione su una seconda K2 Pro.

## Non-obiettivi attuali

- reflashing degli MCU Creality originali senza necessità dimostrata;
- sostituzione inutile dell'elettronica funzionante;
- pubblicazione UID/RFID privati;
- assumere che il comportamento K2 Plus valga automaticamente per K2 Pro;
- considerare il percorso Cartographer MUX/DEMUX sperimentale come trasporto production.