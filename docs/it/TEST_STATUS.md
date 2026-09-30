# Stato test K2-OpenHost

Aggiornato al **30 settembre 2026**.

## Sintesi

Il progetto ha superato la sola validazione del trasporto seriale. Main MCU, Nozzle MCU, dispositivi closed-loop sul bus RS-485 e lo stack CFS reale sono stati testati attraverso il gadget USB del T113 da un host Kalico esterno.

## Verificato

### USB gadget

- Micro-USB di servizio come percorso device runtime;
- gadget Generic Serial composito a 480M;
- tre interfacce `gser` simultanee;
- traffico bidirezionale su tutti e tre i canali.

### Main MCU

- percorso `ttyUSB0 -> ttyGS0 -> ttyS2`;
- 230400 baud;
- firmware MCU Creality originale;
- protocollo e telemetria Kalico live verificati.

### Nozzle MCU

- percorso `ttyUSB1 -> ttyGS1 -> ttyS3`;
- 230400 baud;
- sessione live simultanea al Main MCU.

### RS-485 / closed-loop

- percorso `ttyUSB2 -> ttyGS2 -> ttyS5`;
- 230400 8N1;
- controller X `0x81` verificato;
- controller Y `0x82` verificato;
- nessuna modalità ioctl RS-485 Linux necessaria per il traffico testato.

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
- mantenimento del decoder eventi slot asincroni.

UID e payload RFID privati non vengono pubblicati.

### Extra Jacobean CFS

- `Serial_485_Wrapper` verificato su `/dev/ttyUSB2`;
- `AutoAddressManager` + `BoxDriver` read-only verificati;
- `box_protocol.py` nativo patchato per lo stato K2 Pro a 4 byte;
- guardia fisica read-only verificata;
- vera classe `Box()` verificata in `observation_mode`;
- nessun G-code Box operativo registrato (rimane `SERIAL_STATUS` del transport);
- funzione mutante `0x0D` bloccata prima del TX;
- 10 poll live consecutivi stabili;
- `_poll()` interno completato;
- risultato trasporto: **35 TX / 35 RX, tutti i contatori errore a zero**.

## Integrazione repository

`MzTechnology97/k2-pro-custom-firmware:k2-openhost` contiene gli extra K2 e le patch OpenHost versionate.

`MzTechnology97/kalico-k2pro:k2-pro-openhost` contiene ora baseline K2 Pro ed extra K2 validati sincronizzati in `klippy/extras/`.

In questa fase non è stato necessario modificare moduli core Kalico.

## Artefatti del solo harness

Nel test standalone `filament_sensor_error` è atteso perché il fake printer non crea il vero `filament_switch_sensor`.

`loaded_slot=-1` è volutamente conservativo finché non validiamo le semantiche loaded-path sulla macchina reale.

## Da fare

- avviare un'istanza Klippy/Kalico completa sul CM5 con CFS ancora in observation mode;
- adattare path host e `ttyUSB0..2` senza importare subito tutte le calibrazioni finali;
- validare Cartographer come quarto canale gadget;
- validare sensore filamento reale e loaded-path;
- solo dopo abilitare test CFS mutanti/load/unload controllati;
- migrare i `.cfg` già funzionanti dalla K2 Pro attuale;
- completare integrazione Moonraker/UI e successivamente HelixScreen sul T113.

## Non ancora production-ready

I risultati attuali dimostrano l'architettura e diversi livelli di protocollo, non ancora l'intero workflow di stampa.