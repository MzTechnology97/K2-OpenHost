# FAQ

## Generale

??? question "K2-OpenHost funziona sulla K2 Plus o sulla K2 base?"
    No. È costruito e provato solo per la **Creality K2 Pro**, e gli strumenti controllano il modello (`F012`) e la scheda prima di cambiare qualsiasi cosa.

??? question "Perdo il firmware stock?"
    No. K2-OpenHost gira dallo **slot B** della T113; il sistema di Creality resta intatto nello **slot A**. `./helper.sh t113 boot-a` lo riavvia. Vedi [Tornare allo stock](../installation/uninstall.md).

??? question "È abbastanza stabile per l'uso quotidiano?"
    Sì: la K2 Pro di riferimento lo usa ogni giorno in una print farm, senza crash causati dall'host o da K2-OpenHost. Il [firmware CFS modificato](../cfs-firmware/index.md) e il plugin per OrcaSlicer 2.5 sono le parti ancora sperimentali.

??? question "Perché non far girare semplicemente Klipper sulla T113?"
    La T113 è un dual-core Cortex-A7 a 1,2 GHz con circa 512 MB di RAM, che sullo stock condivide con Moonraker, il web server, l'interfaccia, le app cloud di Creality e la telecamera. Un host esterno ha molte volte la CPU e la RAM, esegue Kalico e Mainsail aggiornati, e lascia alla T113 solo i bridge e lo schermo. Vedi [Perché un host esterno](../index.md#perché-un-host-esterno).

??? question "La stampante comunica ancora con Creality Cloud?"
    No. Nello slot B le app cloud e UI di Creality non vengono avviate. La stampante parla con il tuo host, nella tua rete.

## Hardware

??? question "Quale host devo comprare?"
    Un Raspberry Pi CM5 su una scheda base con porte USB 3.0 (il riferimento usa una Waveshare CM5-IO-BASE-A), oppure un Pi 5. Un Pi 4 funziona. Va bene anche qualsiasi computer Debian/Ubuntu a 64 bit. Vedi [Requisiti](../getting-started/requirements.md).

??? question "Che cavo serve?"
    Un cavo **dati** da Micro-USB a USB-A, possibilmente con **spina a 90°**, dall'host alla porta di servizio della T113. I cavi di sola ricarica non funzionano.

??? question "E le telecamere e la porta per la chiavetta USB?"
    La **telecamera della camera** si scollega dalla T113 e si ricabla all'host. La **telecamera del nozzle non si può usare** in modalità OpenHost. La porta USB della stampante smette di funzionare: carica i file tramite Mainsail.

??? question "Posso usare Cartographer3D?"
    Sì, collegato direttamente all'host. Vedi [Cartographer3D](../CARTOGRAPHER.md).

??? question "Cosa succede se l'host si blocca o perde corrente durante una stampa?"
    La stampa si ferma: le MCU vanno in shutdown e spengono da sole i riscaldatori. Usa l'alimentatore ufficiale dell'host; un UPS per host e stampante è una buona idea.

## CFS

??? question "Mi serve il firmware CFS modificato?"
    No. Il firmware CFS stock è pienamente supportato: caricamento, RFID delle bobine Creality, abbinamento, runout swap, stima del residuo. Il firmware modificato aggiunge parametri regolabili, residuo in tempo reale nel CFS e RFID di terze parti.

??? question "I tag RFID vengono mai scritti?"
    No. Né Kalico né il firmware del CFS scrivono i tag. Il residuo è tenuto sull'host (o calcolato in tempo reale nella RAM del CFS con CFG5T/CFG6).

??? question "Posso usare le bobine Bambu Lab con i loro tag?"
    Sì, con un firmware CFS API7 e l'include `box_rfid_bambu`. Vedi [RFID di terze parti](../cfs-firmware/third-party-rfid.md).

??? question "Quante unità CFS?"
    Fino a quattro (16 slot) più la bobina esterna. Imposta `box_count` in `overrides.cfg`.

## Slicer e app

??? question "Quale slicer?"
    OrcaSlicer, con il profilo stampante K2 Pro puntato al Moonraker dell'host. Il Sync legge i filamenti del CFS; il plugin per OrcaSlicer 2.5 aggiunge un pannello CFS e abbina gli slot prima dell'invio. Vedi [OrcaSlicer](../ORCASLICER.md).

??? question "Posso ancora usare Creality Print?"
    Creality Print si aspetta i servizi di Creality sulla stampante, che nello slot B non girano. Usa OrcaSlicer con Moonraker.

??? question "Home Assistant funziona?"
    Sì, con l'[integrazione K2-OpenHost CFS](../usage/home-assistant.md) e qualsiasi integrazione Moonraker.

## Aggiornamenti

??? question "Come aggiorno?"
    Mainsail → Machine → Update Manager per Kalico, Moonraker, Mainsail e l'helper, oppure `./helper.sh update`. `./helper.sh release status` / `release apply` portano tutto a una combinazione provata. Vedi [Aggiornamenti](../installation/updates.md).

??? question "Posso installare un OTA Creality?"
    Non dallo slot B: un OTA lì sovrascriverebbe lo slot A, quindi è disattivato. Dallo slot A (`./helper.sh t113 boot-a`) un OTA Creality scrive lo slot inattivo, cioè lo slot B di K2-OpenHost: K2-OpenHost viene sostituito e va reinstallato con l'helper. Raramente serve un OTA: il firmware di Main, Nozzle, motori e CFS si aggiorna dallo slot B con `k2oh-mcu-fw` (menu 31 dell'helper).
