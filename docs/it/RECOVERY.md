# Procedura di ripristino

Aggiornato: **5 ottobre 2026**. [English](../en/RECOVERY.md)

Cosa fare quando l'host esterno perde la stampante, in un unico posto. Le cause e le misure dietro ogni passo sono in [Perdita del collegamento seriale](SERIAL_LINK_LOSS.md), [Bridge USB](USB_BRIDGE.md) e [Trasporto USB gadget](USB_GADGET.md).

## Prima di tutto

- **Non durante una stampa.** `USB_BRIDGES_RESTART`, `MCU_POWER_CYCLE`, gli aggiornamenti dell'helper e i riavvii di Klipper vengono rifiutati durante una stampa. Se la stampa è andata in pausa da sola, trova prima la causa, poi `RESUME`.
- **Leggi prima lo stato.** Sull'host, `./helper.sh doctor` (installer helper) controlla il cavo, i canali, altri lettori, Klipper, il CFS, i motori e il collegamento RS-485 senza modificare nulla. Nella console di Klipper:

| Comando | Mostra |
| --- | --- |
| `BOARD_STATUS` | T113: alimentazione delle MCU, stato del gadget USB, se ogni bridge è attivo |
| `SERIAL_STATUS` | collegamento RS-485 `ok` o `lost`, frame, timeout, errori CRC |
| `MOTOR_STATUS` | avvio dei motori a circuito chiuso, prontezza, calibrazione, guasti |
| `BOX_DEBUG` | unità CFS online e il loro stato |

Quando chiedi aiuto, allega l'output del doctor e `~/printer_data/logs/klippy.log`.

## Ordine dei passi

Passa al passo successivo solo se il precedente non è servito.

1. `FIRMWARE_RESTART`.
2. `FIRMWARE_RESTART` una seconda volta. Dopo la perdita di una MCU, la MCU può non aver mai ricevuto lo shutdown e il primo tentativo finisce con `Failed automated reset of MCU`. Il secondo ha sempre funzionato.
3. `USB_BRIDGES_RESTART CONFIRM=1`. Riavvia i tre bridge sul T113 in meno di 5 s. Di norma Klipper resta collegato; se va in shutdown, `FIRMWARE_RESTART`.
4. `MCU_POWER_CYCLE CONFIRM=1`. Toglie l'alimentazione alle MCU per 2 s, poi esegue `FIRMWARE_RESTART`. Funziona anche con Klipper in shutdown. Misurato: Klipper pronto in 9 s, CFS in 16 s, motori in 21 s.
5. `sudo systemctl restart klipper` sull'host.
6. Spegni e riaccendi la stampante. Senza `[k2_t113]` sostituisce il passo 4.

## Per sintomo

### Klipper non si collega mai dopo l'avvio dell'host

| Cosa si vede | Causa | Rimedio |
| --- | --- | --- |
| `lsusb` non elenca `0525:a4a6 Linux-USB Serial Gadget` | il gadget non è sul bus | Cavo dati nella porta Micro-USB **di servizio** della K2; bridge del T113 in esecuzione (`BOARD_STATUS` appena Klipper risponde, oppure SSH sul T113). |
| `lsusb` mostra `0525:a4a6`, ma non esistono `/dev/ttyUSB0..2` e Klipper resta in attesa all'avvio | il driver `usbserial` dell'host non ha preso il gadget | `sudo sh ~/k2-openhost-t113-bootstrap/host/k2oh-host-usbserial install`. Rende permanente il binding e collega il gadget già presente; gli altri dispositivi seriali non vengono toccati. |
| I canali esistono, Main e Nozzle si collegano, RS-485 resta `lost` | un altro processo legge il canale RS-485 insieme a Klipper (il 5 ottobre 2026 il demux Cartographer dismesso si prendeva 77 byte su 90) | Il doctor indica il processo. Per il vecchio demux: `scripts/system.sh retire-demux`, poi riavvia Klipper. |

Dopo un aggiornamento del kernel, controlla prima di riavviare che il nuovo kernel abbia ancora `usbserial`: `modinfo -k <versione> usbserial`.

### `Lost communication with MCU`

Klipper è in shutdown. I riscaldatori sono già spenti: le loro uscite hanno un `max_duration` di 3 s, quindi la MCU li spegne quando l'host smette di aggiornarli.

1. Passi 1 e 2 (`FIRMWARE_RESTART` due volte).
2. Se non basta: `BOARD_STATUS`. Un bridge `DOWN` → passo 3. Bridge attivi → passo 4.
3. `auto_power_cycle: True` in `[k2_t113]` esegue il passo 4 da solo, se non c'era una stampa in corso, al massimo una volta ogni 10 minuti. Disattivato di default.

### Porte seriali rinumerate (`/dev/ttyUSB3/4/5`)

Dopo una riconnessione USB le porte tornano con numeri nuovi, mentre Klipper tiene ancora aperte le vecchie.

- Con `serial: /dev/serial/by-id/usb-Allwinner_Technology_Inc._Gadget_Serial-if0N-port0` (if00 Main, if01 Nozzle, if02 RS-485), `FIRMWARE_RESTART` si ricollega (al secondo tentativo, come sopra).
- Con `serial: /dev/ttyUSBn`, `FIRMWARE_RESTART` continua a fallire. Ferma Klipper, scollega e ricollega il cavo di servizio, avvia Klipper. Poi passa definitivamente ai nomi `by-id`: menu 19 dell'installer, oppure `config/k2/printer.cfg` in kalico-k2pro.

### Collegamento RS-485 perso: il CFS e i motori non rispondono

Klipper non va in shutdown per questo, perché le MCU rispondono ancora. Il watchdog di `[serial_485]` segnala `RS-485 link lost` dopo 10 s senza nessuna risposta.

- **Durante una stampa** decide `link_lost_action`: `pause` (default), `warn` oppure `shutdown`. kalico-k2pro [#30](https://github.com/MzTechnology97/kalico-k2pro/pull/30) aggiunge `cancel`. A riposo segnala soltanto.
- Gli stalli dei motori vengono comunque rilevati: le linee di stallo X/Y/E vanno alle MCU, non passano dall'RS-485.

Rimedio:
1. Il doctor: c'è un altro lettore sul canale RS-485? (vedi sopra)
2. `BOARD_STATUS`: bridge RS-485 `DOWN` → `USB_BRIDGES_RESTART CONFIRM=1`.
3. CFS alimentato e collegato.
4. Il bus si riprende da solo quando il bridge torna; in console compare `RS-485 link restored`. Non serve riavviare.
5. Se la stampa è in pausa: verifica che `SERIAL_STATUS` sia `ok`, poi `RESUME`.

### CFS non trovato

| Situazione | Cosa succede |
| --- | --- |
| Klipper è partito con l'RS-485 giù | Da kalico-k2pro [#24](https://github.com/MzTechnology97/kalico-k2pro/pull/24) il Box ripete la ricerca quando il collegamento torna, poi con un intervallo crescente. In console compare `CFS found after the RS-485 link came back`. |
| Ancora non trovato con `SERIAL_STATUS` `ok` | `RESTART`. |
| Non trovato subito dopo l'avvio | La ricerca richiede qualche secondo. Controlla alimentazione e cavo del CFS. |

### Motori a circuito chiuso non pronti

`MOTOR_STATUS` indica che l'avvio è fallito, quindi l'homing viene rifiutato.

1. Prima `SERIAL_STATUS` deve essere `ok`: i motori X/Y sono sull'RS-485.
2. `MOTOR_RETRY_STARTUP`.
3. Un guasto memorizzato: `MOTOR_QUERY_FAULTS`, poi `MOTOR_CLEAR_ERROR`.
4. Una calibrazione segnalata come sospetta: `MOTOR_CALIBRATE`, oppure `MOTOR_ACCEPT_CALIBRATION` solo se sai che è buona.

kalico-k2pro [#31](https://github.com/MzTechnology97/kalico-k2pro/pull/31) rende automatico il passo 2 quando l'avvio è fallito perché l'RS-485 era giù: riprova quando il collegamento torna, altrimenti ogni 30 s, fino a 5 minuti di distanza, solo a riposo.

### Il T113 si è riavviato o bloccato

- **Riavvio:** le porte dell'host spariscono e Klipper va in shutdown. Attendi i bridge (`lsusb` mostra il gadget, `/dev/serial/by-id/` ha tre voci), poi `FIRMWARE_RESTART`.
- **Nessuna risposta** (né `BOARD_STATUS` né SSH): spegni e riaccendi la stampante. Sullo slot B un avvio di prova fallito torna allo slot A alla riaccensione successiva.

### Dopo un aggiornamento o un riavvio dell'host

L'installer helper [#9](https://github.com/MzTechnology97/k2-openhost-installer-helper/pull/9) esegue il doctor da solo a ogni avvio e dopo ogni modifica di apt. Il risultato va nella console di Klipper e in `printer_data/logs/k2oh-health.log`. Dopo apt segnala anche quando serve un riavvio, e quando il kernel più recente non ha `usbserial`. A mano: `./helper.sh health`.
