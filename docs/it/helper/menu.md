# Riferimento del menu

## Installazione dell'host

| # | Voce | Cosa fa |
| --- | --- | --- |
| 1 | **Full install** | Installazione base più Moonraker timelapse e Shake&Tune. Consigliata per un host nuovo. |
| 2 | Core install | Preparazione dell'host, Kalico, configurazione K2 Pro, Moonraker e Mainsail, poi avvia Klipper. |
| 3 | Preparazione dell'host | Pacchetti, gruppi seriali, nomi udev `/dev/k2-*`, ModemManager e brltty, il controllo di salute automatico. Si può rieseguire senza rischi. |
| 4 | Kalico K2-OpenHost | Installa o aggiorna `~/klipper` (`kalico-k2pro`, `k2-pro-openhost`), `~/klippy-env`, `klipper.service` e lo start gate. |
| 5 | Configurazione K2 Pro | Copia i file del profilo che non hai ancora; per i file cambiati salva la versione del profilo come `<file>.k2oh-new`. |
| 6 | Moonraker | Installa Moonraker e aggiunge le sezioni mancanti di `moonraker.conf`. |
| 7 | Mainsail K2-OpenHost | Installa o aggiorna l'interfaccia web e il sito nginx, compresa la regola che lascia passare la chiave API segnaposto di OrcaSlicer 2.4.2. |

## Componenti opzionali

| # | Voce | Cosa fa |
| --- | --- | --- |
| 8 | Cartographer3D | Il plugin ufficiale (pacchetto pip più loader), collegato via USB diretto. PRTouch resta la sonda validata. Vedi [Cartographer3D](../CARTOGRAPHER.md). |
| 9 | Shake&Tune | Strumenti di risonanza Klippain Shake&Tune. |
| 10 | Timelapse | Moonraker timelapse (il profilo K2 include le sue macro). |
| 11 | Crowsnest | Streaming della webcam. Con la Creality CAM 1080p della K2 Plus collegata imposta anche `max_fps: 25` e i controlli della telecamera (`install creality-cam` fa solo quel passo). Vedi [Fotocamera](../CAMERA.md). |
| 12 | MCU host | `[mcu rpi]`: GPIO, accelerometro e temperatura della scheda host. |
| 13 | Spoolman | Collegamento a un server Spoolman esistente. |
| 14 | Mobileraker | Mobileraker companion (notifiche sul telefono). |
| 15 | OctoEverywhere | Accesso remoto. |
| 36 | Ventola dell'host da Klipper | La ventola della CPU della CM5 comandata da `[host_fan]`: regola udev, drop-in di `klipper.service`, `macros/host_fan.cfg`. Vedi [Host e ventola della CPU](../HOST.md#ventola-della-cpu). |

## Manutenzione

| # | Voce | Cosa fa |
| --- | --- | --- |
| 16 | Doctor | Controllo di salute in sola lettura. Vedi [Doctor](doctor.md). |
| 17 | Update | Aggiorna Kalico, Moonraker e Mainsail. Rifiutato durante la stampa. |
| 18 | Confronta la configurazione | Differenze tra la tua configurazione e il profilo K2. |
| 19 | Nomi seriali | Porta `printer.cfg` e lo start gate sui nomi `/dev/k2-*`, indipendenti dall'ordine di enumerazione USB. |
| 20 / 21 | Backup / Ripristino | Configurazione, libreria filamenti del CFS, stato del CFS e database di Moonraker. Vedi [Backup](../installation/backup.md). |
| 22 | Riavvio | Riavvia Klipper e Moonraker. Rifiutato durante la stampa. |

## Stampante (T113)

| # | Voce | Cosa fa |
| --- | --- | --- |
| 23 | Controlla la stampante | Sola lettura: modello, slot in esecuzione, spazio libero, firmware dello slot A, la release Creality che userebbe lo slot B. |
| 24 | Installa il bootstrap T113 | Costruisce lo slot B dall'OTA Creality, aggiunge HelixScreen, scrive lo slot B (slot A intatto), propone l'avvio di prova. |
| 25 | Stato della T113 | Slot in esecuzione, prossimo avvio, flag di prova, configurazione al primo avvio, HelixScreen. |
| 26 | Avvio di prova dello slot B | Avvia lo slot B una volta; spegnendo e riaccendendo si torna allo slot A. |
| 27 | Conferma lo slot B | Rende lo slot B quello predefinito. |
| 28 | Avvia lo slot A | Torna al sistema originale della stampante. |
| 29 | Cambia l'indirizzo dell'host | Aggiorna l'host usato da HelixScreen e da `k2oh-mcu-fw`. |
| 30 | Stato del firmware delle MCU | Versioni delle schede e i file firmware che lo slot B flasherebbe. |
| 31 | Aggiorna il firmware delle MCU | Ultima release Creality: scarica, prepara, mostra le modifiche, flasha solo su conferma. |
| 32 | Collega i controlli della T113 | Token, host di `[k2_t113]`, dispositivo di alimentazione Moonraker `K2_MCU_Power`. |
| 33 | Aggiorna i programmi della T113 | Aggiorna i programmi di K2-OpenHost sullo slot B in esecuzione senza reinstallare; `--revert` torna indietro. |

## Release

| # | Voce | Cosa fa |
| --- | --- | --- |
| 34 | Stato della release | Ogni componente rispetto all'ultima release validata. Sola lettura. |
| 35 | Applica la release | Porta avanti Kalico e installa la build di Mainsail della release. Niente viene retrocesso. |

## Sperimentale

| # | Voce | Cosa fa |
| --- | --- | --- |
| 40 | Firmware CFS sperimentale | Elenca le immagini CFS approvate dal manifest presenti in `firmware/custom-cfs/`, verifica lo SHA-256 e l'hardware/applicazione di destinazione, mostra i rischi e flasha solo dopo che digiti `FLASH EXPERIMENTAL CFS`. Vedi [Flash e rollback](../cfs-firmware/flash.md). |
