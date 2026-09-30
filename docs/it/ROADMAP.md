# Roadmap K2-OpenHost

La roadmap è guidata dalla validazione: la fase successiva parte solo quando quella precedente è dimostrata sulla K2 Pro.

## Fondamenta completate

- identificazione UDC e supporto gadget del T113;
- Micro-USB di servizio validata come device path runtime;
- tre Generic Serial simultanee;
- bridge Main MCU, Nozzle MCU e RS-485;
- sessioni MCU Kalico simultanee;
- query closed-loop X/Y;
- discovery/address/read CFS;
- BoxDriver Jacobean sul trasporto OpenHost;
- decoder Box state 4-byte K2 Pro;
- guardia CFS observation;
- vera `Box()` in observation mode;
- patch versionate in `k2-pro-custom-firmware:k2-openhost`;
- assemblaggio `kalico-k2pro:k2-pro-openhost` con baseline K2 Pro ed extra K2.

## Fase 1 — vera istanza Kalico sul CM5 in observation mode

- eseguire `kalico-k2pro:k2-pro-openhost` come servizio reale;
- usare `ttyUSB0`, `ttyUSB1`, `ttyUSB2` per i bridge verificati;
- mantenere CFS in `observation_mode`;
- validare startup Klippy, telemetria, heater/sensori senza movimenti;
- validare sensore filamento reale e stato Box.

I `.cfg` macchina definitivi sono volutamente rimandati fino alla stabilità dello stack host/trasporto.

## Fase 2 — bridge Cartographer

- identificare il device seriale Cartographer lato T113;
- aggiungere una quarta funzione gadget;
- verificare comunicazione MCU Cartographer normale;
- verificare separatamente eventuali esigenze USB dirette per bootloader/update.

## Fase 3 — migrazione configurazione macchina

Importare i valori già funzionanti dalla K2 Pro attuale:

- configurazione Cartographer;
- `motor_control.cfg` già tunato;
- PID/termiche;
- estrusore/pressure advance;
- macro e altri `.cfg` validati.

Cambiare solo path/seriali dipendenti dal nuovo host quando necessario.

## Fase 4 — mutazioni CFS controllate

Dopo la stabilità observation:

- validare loaded-path;
- validare policy RFID;
- abilitare una funzione mutante alla volta;
- testare load/unload con supervisione meccanica;
- validare cutter, buffer e runout recovery.

## Fase 5 — UI

- Moonraker/planner sul CM5;
- HelixScreen sul T113 con LCD/touch originali;
- ridurre il T113 a UI e bridge hardware.

## Fase 6 — deployment persistente

Solo dopo la validazione completa runtime:

- startup persistente bridge;
- boot/recovery;
- conservazione slot stock funzionante;
- procedura di rebase/update rispetto agli upstream.

## Non-obiettivi attuali

- reflashing degli MCU Creality originali;
- sostituzione inutile dell'elettronica funzionante;
- pubblicazione UID/RFID privati;
- assumere che il comportamento K2 Plus valga automaticamente per K2 Pro.