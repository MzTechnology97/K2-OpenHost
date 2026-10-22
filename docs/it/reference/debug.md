# Debug e diagnostica

Ogni comando di questa pagina è **in sola lettura**: stampa informazioni e non cambia nulla, quindi puoi eseguirlo in qualsiasi momento, anche durante la stampa, salvo dove la tabella dice altro.

## Da dove partire

Sull'host:

```bash
cd ~/k2-openhost-installer-helper
./helper.sh doctor
```

Il [doctor](../helper/doctor.md) controlla il cavo, i tre canali, altri processi sulle porte seriali, Klipper, il CFS, i motori e il collegamento RS-485, e propone la soluzione per ogni problema.

Nella console di Klipper (Mainsail):

| Comando | Mostra |
| --- | --- |
| `BOARD_STATUS` | T113: slot, alimentazione MCU, temperatura del SoC, uptime, UDISK libera, stato del gadget USB, ogni bridge attivo o no |
| `SERIAL_STATUS` | Collegamento RS-485 `ok`/`lost`, frame, timeout, errori CRC |
| `MOTOR_STATUS [VERBOSE=1]` | Motori closed-loop: avvio, prontezza, calibrazione, protezioni, temperature |
| `BOX_DEBUG [RAW=1]` | Unità CFS online, stato attuale, sensori, motore di cambio, rilevamento intasamenti |

## Per area

### Collegamenti seriali e T113

| Comando | Uso |
| --- | --- |
| `BOARD_STATUS` | Bridge e stato del gadget sulla T113 |
| `SERIAL_STATUS` | Contatori RS-485 e stato del collegamento |
| `LINK_MONITOR_REPORT` | Percentili dei tempi di andata e ritorno di ogni collegamento dall'avvio (richiede `[link_monitor]`, vedi `printer.cfg`) |

### CFS

| Comando | Uso |
| --- | --- |
| `BOX_DEBUG [RAW=1]` | Resoconto completo del CFS; `RAW=1` aggiunge le risposte grezze |
| `BOX_ENV_DEBUG` | Versioni del CFS, hardware, temperatura e umidità |
| `BOX_PRINT_INFO [FILENAME=...]` | I tool che usa un file e come verrebbero abbinati, senza avviare nulla |
| `_BOX_RFID_REMAINING_DIAG SLOT=<n>` | Valore grezzo del residuo che il CFS restituisce per uno slot |
| `_BOX_RFID_FALLBACK_CACHE` | Decoder RFID di terze parti, budget e cache degli UID |
| `BOX_CFS_TRACE_START` → operazione → `BOX_CFS_TRACE_SHOW` | Cronologia di un caricamento/scaricamento dallo stato in cache di Kalico (richiede `[box_cfs_trace]`; nessun traffico in più sul bus) |

### Firmware CFS sperimentale

| Comando | Uso |
| --- | --- |
| `BOX_CFS_CONFIG_INFO` | Identità del firmware, esito dell'applicazione all'avvio, tutti i valori |
| `BOX_CFS_CONFIG_DIAG ALL=1` | GET dei 28 parametri con controllo dei limiti |
| `BOX_RFID_DIAG_INFO` | API RFID (API7 / `caps=0xE8`) |
| `BOX_RFID_DIAG_INTERNAL SLOT=<0-3>` | UID, ATQA, SAK del tag in uno slot |

### Motori

| Comando | Uso |
| --- | --- |
| `MOTOR_STATUS VERBOSE=1` | Stato completo |
| `MOTOR_EVENTS [COUNT=n] [VERBOSE=1]` | Eventi di protezione (blocco, sovracorrente); `VERBOSE=1` produce JSON per una segnalazione |
| `MOTOR_QUERY_FAULTS` | Codici di errore, avviso e stato, letti ora |
| `MOTOR_CFG_OVERRIDE_STATUS` | Parametri dei motori configurati rispetto a quelli effettivi |

### Host

| Comando | Uso |
| --- | --- |
| `HOST_FAN_STATUS` | Modalità, temperatura, velocità e giri della ventola della CM5 |
| `FAN_FEEDBACK_STATUS` | Ventole della stampante con tachimetro |

## Comandi da shell

Sull'**host**:

```bash
lsusb | grep 0525:a4a6                 # il gadget della T113 è sul bus
ls -l /dev/k2-*                        # i tre nomi stabili dei canali
ls /dev/serial/by-id/                  # i nomi grezzi del gadget
sudo fuser -v /dev/k2-*                # chi tiene aperti i canali (solo Klipper)
systemctl status klipper moonraker
journalctl -u klipper -b --no-pager | tail -50
vcgencmd get_throttled                 # 0x0 = nessuna sottotensione o throttling (Raspberry Pi)
```

Sulla **T113** (`ssh root@<ip-stampante>`):

```bash
logread | grep -E "k2oh|bridge"        # bridge e servizi K2-OpenHost
k2oh-mcu-fw status                     # versioni del firmware delle schede
fw_printenv -n boot_partition          # slot che avvia la T113 (bootA o bootB)
df -h /mnt/UDISK
```

## Log

| File | Contenuto |
| --- | --- |
| `~/printer_data/logs/klippy.log` | Kalico: tutto, compresi CFS, decoder RFID e motori |
| `~/printer_data/logs/moonraker.log` | Moonraker, update manager, API |
| `~/printer_data/logs/k2oh-health.log` | Controllo di salute automatico dopo avvio e apt |
| `~/printer_data/logs/crowsnest.log` | Telecamera |
| `~/printer_data/logs/link_monitor.csv` | Tempi di andata e ritorno dei collegamenti, con `[link_monitor]` |
| T113: `logread` | Bridge, `k2oh-ctl`, HelixScreen |
| T113: `/tmp/mcu_update.log` | Ultimo flash del firmware MCU/CFS |
| Plugin OrcaSlicer: `k2oh_cfs.log` | Nella cartella del plugin |

In Mainsail tutti i file di `printer_data/logs` sono in **Machine → logs**.

## Cosa allegare quando chiedi aiuto { #what-to-attach-when-asking-for-help }

1. L'output di `./helper.sh doctor`.
2. `klippy.log` (dopo il problema, possibilmente prima di riavviare di nuovo Klipper).
3. L'output dei comandi da console per l'area: `BOARD_STATUS`, `SERIAL_STATUS`, `BOX_DEBUG`, `MOTOR_STATUS VERBOSE=1`.
4. Le versioni: `./helper.sh release status` oppure Mainsail → Machine → Update Manager.
5. Cosa hai fatto, cosa ti aspettavi, cosa è successo, e se c'era una stampa in corso.

Non pubblicare mai il contenuto di `k2oh_t113.token`, `~/klipper-backup/.env` o le chiavi API di Moonraker.
