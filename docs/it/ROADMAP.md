# Roadmap K2-OpenHost

La roadmap è guidata dalla validazione: una fase successiva parte solo quando quella precedente è dimostrata sulla K2 Pro.

Aggiornata al **1 ottobre 2026**.

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
- patch versionate in `k2-pro-custom-firmware:k2-openhost`;
- assemblaggio `kalico-k2pro:k2-pro-openhost` con baseline K2 Pro ed extra K2;
- creazione `cartographer3d-plugin-k2openhost` con compatibilità K2/Kalico, installazione editable, guida direct-USB e supporto `register_as_probe`;
- trasporto reale di dati MCU Cartographer attraverso un MUX/DEMUX T113 sperimentale, poi abbandonato come percorso finale a favore della USB diretta per la complessità di reset/re-enumeration.

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

Dopo la stabilità observation nel servizio completo:

- validare loaded-path;
- validare policy RFID;
- abilitare una funzione mutante alla volta;
- testare load/unload con supervisione meccanica;
- validare cutter, buffer e runout recovery;
- mantenere visibili contatori transport/error e procedure di rollback.

## Fase 5 — UI

- mantenere Moonraker e planner principale sul CM5;
- valutare HelixScreen o altra UI leggera sul T113 con LCD/touch originali;
- ridurre le responsabilità del T113 a UI e bridge hardware.

## Fase 6 — deployment persistente

Solo dopo la validazione completa di runtime e print stack:

- startup persistente dei bridge;
- boot/recovery;
- conservazione slot stock funzionante;
- procedura di update/rebase rispetto a Jacob/Kalico/Jacobean/Cartographer;
- procedura riproducibile di installazione su una seconda K2 Pro.

## Non-obiettivi attuali

- reflashing degli MCU Creality originali senza necessità dimostrata;
- sostituzione inutile dell'elettronica funzionante;
- pubblicazione UID/RFID privati;
- assumere che il comportamento K2 Plus valga automaticamente per K2 Pro;
- considerare il percorso Cartographer MUX/DEMUX sperimentale come trasporto production.