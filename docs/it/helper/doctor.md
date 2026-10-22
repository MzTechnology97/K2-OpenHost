# Doctor e controllo di salute

## Doctor

```bash
./helper.sh doctor     # menu 16
```

Sola lettura: controlla l'host senza cambiare nulla.

![Output del doctor](../../images/helper/cli-doctor.png)

| Sezione | Cosa controlla |
| --- | --- |
| Host | Sistema operativo, gruppi seriali del tuo utente, ModemManager |
| USB gadget della T113 | Il gadget (`0525:a4a6`) è collegato; ogni canale (Main MCU, Nozzle MCU, RS-485/CFS) corrisponde al dispositivo usato in `printer.cfg`; nessun altro processo usa i canali; il binding `usbserial` resta dopo i riavvii |
| Servizi | Klipper, Moonraker, nginx e i servizi opzionali in esecuzione; lo start gate di Klipper installato |
| Software | Repository, branch e commit di Kalico; versione di Mainsail |
| Cartographer | Il plugin ufficiale installato (non il vecchio fork) e un solo loader |
| Klipper e il CFS | Stato di Klipper, driver e modalità del CFS, unità CFS online, motori closed-loop pronti, file della libreria filamenti, collegamento RS-485 |

Le righe rosse `✘` dicono cosa non va e come correggerlo. Le più comuni:

| Il doctor dice | Soluzione |
| --- | --- |
| `not in group dialout` / `tty` | Riavvia l'host, oppure esci e rientra. |
| `ModemManager is running` | `sudo systemctl stop ModemManager`, oppure di nuovo il menu 3. |
| `the K2 gadget (0525:a4a6) is not connected` | Cavo dati nella porta Micro-USB **di servizio** della K2; bridge della T113 attivi (slot B avviato); `lsusb` deve elencare *Linux-USB Serial Gadget*. |
| `interface .. is /dev/ttyUSBx but printer.cfg uses ...` | Menu 19 (nomi seriali stabili), poi riavvia Klipper. |
| `process … also uses /dev/ttyUSBx` | Un secondo lettore prende byte destinati a Klipper: ferma quel processo. Per il vecchio demux di Cartographer: `scripts/system.sh retire-demux`. |
| `RS-485 link LOST` | Nessuna risposta sull'RS-485: altri lettori, bridge RS-485 della T113, alimentazione del CFS. |

Quando chiedi aiuto, allega l'output del doctor e `~/printer_data/logs/klippy.log`.

## Controllo di salute automatico { #automatic-health-check }

Il menu 3 installa un controllo che gira da solo:

- **a ogni avvio** (`k2oh-health@boot.service`): attende fino a 4 minuti Klipper e l'avvio dei motori, poi esegue il doctor;
- **dopo ogni modifica apt/dpkg** (`k2oh-health@apt.service`, senza bloccare apt). Dice anche quando è in attesa un riavvio, e fallisce se il kernel più recente installato non ha il modulo `usbserial`.

Il risultato:

- compare nella **console di Klipper** in Mainsail (`K2-OpenHost check after boot: OK.`, oppure i problemi in rosso);
- è conservato in `~/printer_data/logs/k2oh-health.log`;
- può essere inviato a un tuo comando (Telegram, apprise, mail): imposta `K2OH_HEALTH_NOTIFY_CMD="..."` in `~/printer_data/systemd/k2oh-health.env`; riceve il riepilogo come argomento.

Eseguilo a mano con `./helper.sh health`; `scripts/system.sh health-remove` lo rimuove.
