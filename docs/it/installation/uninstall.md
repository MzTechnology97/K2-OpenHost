# Tornare allo stock

K2-OpenHost non scrive mai lo slot A della T113, quindi il sistema originale della stampante è sempre a un comando di distanza.

## Tornare allo slot A

```bash
./helper.sh t113 boot-a     # menu 28
```

La stampante si riavvia nello slot A: Klipper, schermo e app di Creality, esattamente come prima. All'avvio lo slot A riflasha sulle schede il firmware della propria release, se diverso.

Senza l'host, da una sessione SSH sulla stampante con lo slot B in esecuzione:

```sh
k2oh-slot boot-a && reboot
```

## Tornare a K2-OpenHost in seguito

```bash
./helper.sh t113 boot-b     # avvio di prova, poi
./helper.sh t113 commit     # conferma lo slot B
```

## Rimuovere K2-OpenHost dalla stampante

Dallo slot A, dopo i passi sopra:

```sh
rm -rf /mnt/UDISK/.k2openhost
```

Questo rimuove lo strato scrivibile dello slot B, i backup e il firmware scaricato. Le partizioni dello slot B restano come sono finché un OTA Creality non le scrive.

## Telecamere e USB

Rimetti la telecamera della camera sulla T113, sul suo percorso originale. Nello slot A tornano a funzionare la telecamera del nozzle e la porta USB esterna della stampante.

## Firmware CFS sperimentale

Se hai flashato un'immagine CFS sperimentale, riflasha il firmware CFS stock con un aggiornamento Creality dallo slot A (oppure `./helper.sh t113 mcu-fw apply --cfs` dallo slot B prima di tornare indietro). Vedi [Flash e rollback](../cfs-firmware/flash.md#back-to-stock-cfs-firmware).
