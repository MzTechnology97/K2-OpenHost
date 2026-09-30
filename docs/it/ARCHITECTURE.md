# Architettura K2-OpenHost

Stato: **sperimentale, validato a fasi su hardware**. Stampante target: **Creality K2 Pro**.

## Obiettivo

Il progetto mantiene l'elettronica originale della K2 Pro e sposta il carico principale di pianificazione Kalico/Klipper su un host Linux esterno. Il T113 rimane come piattaforma fisica per display/touch e come bridge trasparente verso UART e bus RS-485 interni.

```text
LCD/touch K2
    |
Allwinner T113 (Tina Linux)
    |-- UI / futuro HelixScreen
    |-- USB ConfigFS gadget
    |-- ttyGS0 <-> ttyS2  Main MCU
    |-- ttyGS1 <-> ttyS3  Nozzle MCU
    `-- ttyGS2 <-> ttyS5  RS-485 / CFS / closed-loop
           |
           | Micro-USB di servizio
           v
Host Linux esterno / Raspberry Pi CM5
    |-- Kalico
    |-- Moonraker
    |-- Mainsail/Fluidd
    `-- extra specifici K2
```

È previsto un quarto canale Generic Serial per Cartographer dopo la validazione del relativo device USB seriale lato T113.

## Livelli repository

### K2-OpenHost

Architettura canonica, osservazioni hardware, risultati dei test e roadmap.

### kalico-k2pro

`MzTechnology97/kalico-k2pro` è un fork di `Jacob10383/kalico`. Il branch attivo `k2-pro-openhost` combina attualmente:

- core Kalico upstream;
- baseline di configurazione K2 Pro derivata dal lavoro pubblico `luketot/kalico-for-K2-Pro`;
- extra K2 Jacobean sincronizzati da `MzTechnology97/k2-pro-custom-firmware:k2-openhost`.

I `.cfg` macchina definitivi verranno migrati dalla K2 Pro già funzionante solo al termine dei test di trasporto/controllo.

### k2-pro-custom-firmware

Fork di `Jacob10383/k2-plus-custom-firmware`. Il branch `k2-openhost` è la sorgente versionata degli extra K2 e delle modifiche di compatibilità K2 Pro/OpenHost.

## Trasporto verificato

| Host esterno | Gadget T113 | UART T113 | Destinazione | Stato |
|---|---|---|---|---|
| `/dev/ttyUSB0` | `/dev/ttyGS0` | `/dev/ttyS2` | Main MCU | verificato |
| `/dev/ttyUSB1` | `/dev/ttyGS1` | `/dev/ttyS3` | Nozzle MCU | verificato |
| `/dev/ttyUSB2` | `/dev/ttyGS2` | `/dev/ttyS5` | RS-485/CFS | verificato |
| previsto `/dev/ttyUSB3` | previsto `ttyGS3` | USB seriale interno Cartographer | Cartographer | da testare |

I tre canali verificati viaggiano sullo stesso gadget USB composito a USB 2.0 High-Speed.

## Main e Nozzle MCU

La configurazione stock usa 230400 baud per entrambi. Kalico esterno ha aperto sessioni simultanee con gli MCU Creality originali senza reflashing.

## RS-485

`ttyS5` funziona con accesso seriale userspace ordinario a 230400 8N1 per i frame testati. Il bus è condiviso tra CFS e altri dispositivi K2, quindi le protezioni read-only devono essere applicate allo stack CFS e non globalmente al trasporto.

## Integrazione CFS

Gli extra K2 Jacobean sono la baseline di implementazione. K2-OpenHost aggiunge solo le differenze necessarie e validate:

1. supporto del `BOX_STATE` steady K2 Pro a 4 byte mantenendo il percorso legacy a 6 byte;
2. `observation_mode` in `box.py`;
3. proxy read-only limitato allo stack CFS;
4. disabilitazione di comandi Box operativi, T command, write RFID automatico e hook runout durante l'osservazione.

## UI

L'obiettivo è HelixScreen sul T113 collegato a Moonraker sul CM5. Il CM5 resta il planner/Python host; il T113 gestisce display e bridge hardware.

## Modello di sicurezza

Il progetto procede per livelli:

1. osservazione passiva;
2. query read-only;
3. integrazione runtime protetta;
4. solo dopo validazione, comandi mutanti strettamente controllati;
5. installazione persistente solo a stack runtime dimostrato.