# Architettura K2-OpenHost

Stato: **sperimentale, validato a fasi su hardware**. Stampante target: **Creality K2 Pro**.

Ultimo aggiornamento architetturale: **1 ottobre 2026**.

## Obiettivo

Il progetto mantiene l'elettronica originale della K2 Pro e sposta il carico principale di pianificazione Kalico/Klipper su un host Linux esterno. Il T113 rimane come piattaforma fisica per display/touch e come bridge trasparente verso Main MCU, Nozzle MCU e bus RS-485 originali.

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
    |-- Kalico (kalico-k2pro:k2-pro-openhost)
    |-- Moonraker
    |-- Mainsail/Fluidd
    |-- extra specifici K2
    `-- USB host diretto <-> Cartographer
```

## Perché Cartographer passa direttamente al CM5

È stato prototipato un percorso Cartographer attraverso T113, MUX/DEMUX e gadget USB. Il test ha trasportato realmente i dati MCU Cartographer, ma ha anche evidenziato due problemi non necessari nell'architettura finale:

1. il reset/re-enumeration di Cartographer può cambiare la PTY lato T113 e richiede logica di riapertura/reconnect robusta;
2. condividere il canale gadget non porta vantaggi quando Cartographer può collegarsi nativamente alla USB host del CM5.

Per questo i tre canali gadget restano dedicati ai bus originali K2 e **Cartographer diretto USB sul CM5** diventa la topologia preferita. Sul CM5 va usato un path persistente `/dev/serial/by-id/...`.

## Livelli repository

### K2-OpenHost

Architettura canonica, osservazioni hardware, risultati dei test e roadmap.

### kalico-k2pro

`MzTechnology97/kalico-k2pro`, branch attivo `k2-pro-openhost`, è il target Kalico integrato per host esterno. Combina:

- lineage Jacob/Kalico;
- baseline e integrazione K2 Pro;
- extra K2/Jacobean richiesti dalla macchina;
- hardening dello startup motor-control per l'avvio da host esterno;
- loader Cartographer tracciato usato dal plugin Cartographer separato.

### k2-pro-custom-firmware

Fork di `Jacob10383/k2-plus-custom-firmware`. Il branch `k2-openhost` rimane sorgente/history versionata degli extra K2 Jacobean e delle patch di compatibilità K2 Pro/OpenHost.

### cartographer3d-plugin-k2openhost

Fork derivato dal plugin Cartographer3D e dal port K2 di Jacob10383. Mantiene il lavoro K2 specifico e aggiunge compatibilità Kalico/OpenHost, installazione editable, documentazione Moonraker update-manager e comportamento aggiornato `register_as_probe`.

## Trasporto verificato

| Host esterno | Gadget T113 | UART T113 | Destinazione | Stato |
|---|---|---|---|---|
| `/dev/ttyUSB0` | `/dev/ttyGS0` | `/dev/ttyS2` | Main MCU | verificato |
| `/dev/ttyUSB1` | `/dev/ttyGS1` | `/dev/ttyS3` | Nozzle MCU | verificato |
| `/dev/ttyUSB2` | `/dev/ttyGS2` | `/dev/ttyS5` | RS-485/CFS/closed-loop | verificato |
| `/dev/serial/by-id/...` | n/a | n/a | Cartographer via USB CM5 | topologia target; validazione hardware finale pendente |

I tre canali T113 verificati viaggiano sullo stesso gadget USB composito a USB 2.0 High-Speed.

## Runtime host esterno

Il target validato è un host Linux AArch64 basato su CM5. Il C helper di Kalico viene ricompilato nativamente come ELF64/AArch64, senza riutilizzare binari della piattaforma T113 a 32 bit.

Il servizio Kalico attende la disponibilità dei trasporti K2 prima dell'avvio. Anche il motor-control usa startup delay e retry per tollerare il caso in cui il CM5 si avvii più velocemente dei controller periferici K2.

## Movimento e homing

I controller closed-loop X/Y della K2 Pro sono gestiti sul bus RS-485 condiviso. Sono stati verificati movimenti CoreXY normali via G-code, homing sensorless/stall su X/Y e direzione Z corretta.

È stato eseguito con successo un homing completo usando il **PRTouch** originale come probe Z attivo. Questo costituisce la baseline nota funzionante prima di reintrodurre Cartographer via USB diretta.

## Termica e sicurezza

Bed, nozzle e chamber heater sono stati testati da Kalico esterno, inclusi i PID tuning. È stato inoltre eseguito un emergency shutdown con gli heater attivi: il carico termico è stato rimosso e il consumo della stampante è tornato quasi al livello idle.

## Test risonanza

Un test reale della risonanza con **Klippain-ShakeTune** è stato completato con successo sullo stack OpenHost, confermando il percorso dell'accelerometro nozzle e l'analisi lato host esterno.

## RS-485 e CFS

`ttyS5` funziona con accesso seriale userspace a 230400 8N1 per i frame testati. Il bus trasporta sia CFS sia motor-control, quindi le protezioni restano limitate allo stack CFS.

Il layer CFS usa gli extra K2 Jacobean come baseline, con supporto `BOX_STATE` steady K2 Pro a 4 byte e `observation_mode` protetto.

## Modalità Cartographer

Il fork Cartographer supporta due ruoli:

- `register_as_probe: true` — Cartographer possiede l'oggetto `probe` canonico e `probe:z_virtual_endstop`;
- `register_as_probe: false` — base per mixed mode, dove PRTouch resta il probe principale per il riferimento Z e Cartographer rimane disponibile per scan/mesh con namespace endstop separato.

Il mixed mode è implementato nel plugin ma non è ancora validato sull'intero workflow Z automatico OpenHost.

## UI

L'obiettivo resta HelixScreen o altra UI leggera sul T113 collegata a Moonraker sul CM5. Il CM5 resta autorevole per planning/controllo; il T113 gestisce display/touch e bridge hardware.

## Modello di sicurezza

Il progetto procede per livelli:

1. osservazione passiva;
2. query read-only;
3. integrazione runtime protetta;
4. test controllati movimento/termica;
5. homing completo e test risonanza;
6. solo dopo validazione, funzioni CFS mutanti strettamente controllate;
7. deployment persistente e stampa non supervisionata solo dopo validazione completa del print path.

Non è stato necessario riflashare Main MCU o Nozzle MCU per i test OpenHost validati.