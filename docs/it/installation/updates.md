# Aggiornamenti e release

!!! warning
    Aggiornamenti, riavvii di Klipper e flash dei firmware vengono rifiutati mentre una stampa è in corso o in pausa. Aggiorna con la stampante ferma.

## Software sull'host

=== "Da Mainsail"

    *Machine* → **Update Manager** aggiorna Kalico, Moonraker, Mainsail K2-OpenHost (canale pre-release), il plugin Cartographer e l'helper stesso.

=== "Dall'helper"

    ```bash
    ./helper.sh update        # menu 17
    ```

    Aggiorna Kalico, Moonraker e Mainsail.

A ogni avvio l'helper controlla anche i propri aggiornamenti, elenca i nuovi commit e chiede *Update the installer helper now?*. Non tocca mai le modifiche locali. `K2OH_NO_UPDATE_CHECK=1` salta il controllo.

## Release

I branch dei componenti si muovono a ogni merge. Una **release** è l'insieme di commit **validati insieme sulla stampante di riferimento**, elencati in [`releases/stable.json`](https://github.com/MzTechnology97/K2-OpenHost/blob/main/releases/stable.json) con il firmware con cui sono stati provati.

```bash
./helper.sh release status        # menu 34: ogni componente rispetto alla release, sola lettura
./helper.sh release apply         # menu 35: porta Kalico e Mainsail alla release
./helper.sh release apply --t113  # anche i programmi della T113
```

`release apply` fa solo avanzamenti fast-forward: un componente più nuovo della release, su un altro branch o con modifiche locali resta com'è. Klipper viene riavviato solo se confermi e solo con tutti i riscaldatori spenti.

## Programmi della T113 (slot B)

I programmi di K2-OpenHost sulla stampante (`k2oh-*`) si aggiornano sullo slot B in esecuzione, senza reinstallare dallo slot A:

```bash
./helper.sh t113 update           # menu 33: mostra prima --check, applica su conferma
./helper.sh t113 update --revert  # torna ai programmi dell'immagine
```

I programmi che girano solo all'avvio richiedono un riavvio della stampante, che l'helper propone. Solo una reinstallazione (menu 24) cambia il kernel o la base Creality.

## Firmware delle schede Creality { #firmware-delle-schede-creality }

Lo slot B esegue `mcu_update` di Creality a ogni avvio. Per portare Main MCU, Nozzle MCU, estrusore, motori X/Y e schede cinghia/RFID all'**ultima** release Creality:

```bash
./helper.sh t113 mcu-fw update    # menu 31
```

1. Scarica l'ultima release Creality e tiene solo i file del firmware.
2. Li prepara nello slot B e mostra quali schede cambierebbero.
3. Flasha **solo se rispondi sì**, con gli strumenti di Creality (`mcu_util`, `mcu_util_485`), dopo aver fermato Klipper sull'host.

Il CFS viene flashato solo con `--cfs`. Passo per passo: `./helper.sh t113 mcu-fw list|download|stage|apply`. Stato: menu **30**.

![k2oh-mcu-fw update](../../images/helper/cli-t113-mcu-fw-update.png)

!!! note
    Lo slot A riflasha sulle schede i file della propria release al suo avvio successivo. Tornare allo slot A riporta quindi anche le schede alle versioni dello slot A.

Il **firmware CFS sperimentale** ha un suo menu (40) e una sua procedura: vedi [Flash e rollback](../cfs-firmware/flash.md).

## Aggiornamenti del kernel sull'host

Dopo un `apt full-upgrade` con un nuovo kernel, il controllo di salute automatico avvisa quando è in attesa un riavvio e fallisce se il kernel più recente non ha il modulo `usbserial` (i canali della T113 non tornerebbero dopo il riavvio). Controlla prima di riavviare:

```bash
modinfo -k <versione-nuovo-kernel> usbserial
```
