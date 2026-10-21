# Risoluzione problemi

Trova il tuo sintomo, controlla la causa, applica la soluzione. Parti da `./helper.sh doctor` sull'host: controlla quasi tutto da solo. Per collegamenti persi e riavvii, la sequenza passo per passo è nella [procedura di recupero](../RECOVERY.md).

!!! warning "Non durante la stampa"
    Riavvii, riavvii dei bridge, spegnimento e riaccensione delle MCU, aggiornamenti e flash vengono rifiutati o non sono sicuri durante una stampa. Se una stampa è andata in pausa da sola, trova prima la causa, poi `RESUME`.

## L'host non vede la stampante { #host-non-vede-la-stampante }

| Cosa vedi | Causa | Soluzione |
| --- | --- | --- |
| `lsusb` non mostra `0525:a4a6` | Cavo nella porta sbagliata, cavo di sola ricarica, oppure la T113 non è sullo slot B | Cavo dati nella porta Micro-USB **di servizio** della T113 ([foto](../getting-started/requirements.md#dove-si-trova-la-porta-micro-usb-di-servizio)); `./helper.sh t113 status` deve mostrare lo slot B |
| `0525:a4a6` presente, nessun `/dev/k2-*` | Manca la regola udev | Menu 19 dell'helper (nomi seriali) |
| `0525:a4a6` presente, nemmeno `/dev/ttyUSB*` | `usbserial` non ha preso il gadget | `sudo sh ~/k2-openhost-t113-bootstrap/host/k2oh-host-usbserial install` |
| Il gadget compare e scompare | Cavo allentato o scadente, cavo in tensione | Usa un buon **cavo dati a 90°**, corto, e fissalo |
| Dopo un aggiornamento del kernel non funziona nulla | Kernel nuovo senza `usbserial` | `modinfo -k <versione> usbserial`; il controllo di salute lo segnala dopo apt |

## Errori di Klipper

| Messaggio | Causa | Soluzione |
| --- | --- | --- |
| `Lost communication with MCU 'mcu'` / `'nozzle_mcu'` | Bridge riavviato, cavo mosso, T113 riavviata | `FIRMWARE_RESTART` (due volte se la prima dice `Failed automated reset`), poi `BOARD_STATUS`; vedi la [procedura](../RECOVERY.md#lost-communication-with-mcu) |
| `Unable to open serial port` | Percorso `serial:` sbagliato o un altro programma tiene la porta | Usa `/dev/k2-*`; `sudo fuser -v /dev/k2-*` mostra chi la tiene |
| `RS-485 link lost` | Bridge RS-485 fermo, guasto sul bus CFS/motori | `BOARD_STATUS`, poi `USB_BRIDGES_RESTART CONFIRM=1`; si ripristina da solo quando il bus risponde |
| `Timer too close` | Host sovraccarico o in throttling | `vcgencmd get_throttled` (sottotensione), controlla la temperatura della CPU (`HOST_FAN_STATUS`), ferma i servizi pesanti |
| `MCU 'mcu' shutdown: ...` dopo un aggiornamento firmware | Firmware delle MCU non allineato | `./helper.sh t113 mcu-fw status`, aggiorna con il menu 31 a stampante ferma |
| L'opzione `xyz` non è valida | Configurazione di un profilo più nuovo/vecchio | `./helper.sh config diff` (menu 18) e confronta con il profilo distribuito |

## Movimento e tastatura

| Cosa vedi | Soluzione |
| --- | --- |
| Homing rifiutato, motori non pronti | `MOTOR_STATUS`; `SERIAL_STATUS` deve essere `ok`; `MOTOR_RETRY_STARTUP`; per un guasto `MOTOR_QUERY_FAULTS` → `MOTOR_CLEAR_ERROR` |
| "Calibrazione sospetta" all'avvio | `MOTOR_CALIBRATE AXIS=XY` (testina al centro, piatto in basso). `MOTOR_ACCEPT_CALIBRATION` solo se sai che è buona |
| Blocco / sovracorrente durante la stampa | `MOTOR_EVENTS VERBOSE=1`; controlla cinghie, guide e ostacoli; lubrifica (`LUBRICATE_RAILS`) |
| Primo layer troppo alto/basso | Z offset in `_START_PRINT_VARS` (`variable_offset_DEFAULT` o per materiale), nozzle pulito per PRTouch (`variable_prtouch_scrub`) |
| La taglierina non taglia | `CALIBRATE_CUT_POS` dopo aver cambiato la taglierina o la testina |

## CFS

| Cosa vedi | Causa | Soluzione |
| --- | --- | --- |
| CFS non trovato | Avviato mentre l'RS-485 era giù; alimentazione o cavo | Attende e riprova da solo; `SERIAL_STATUS` `ok` poi `RESTART`; controlla il cavo del CFS |
| Stampa rifiutata: tool non abbinato | Un tool dello slicer non ha una bobina corrispondente | Abbinalo nella finestra di stampa di Mainsail o con il plugin OrcaSlicer; oppure `auto_map_block_unresolved: false` |
| Il caricamento si ferma a metà, `cfs_error` | Attrito nel percorso, bobina posizionata male, buffer | Controlla il percorso PTFE e la bobina; `BOX_DEBUG`; `BOX_UNLOAD MANUAL=1` poi ricarica |
| Pausa per intasamento mentre stampa bene | `clog_extruder_length` troppo corto per il materiale | Aumentalo (minimo 30, predefinito 80) o disattiva con `_BOX_SET_CLOG_DETECTION ENABLE=0` |
| Il runout swap non è avvenuto | Swap spento, o nessuna bobina dello stesso filamento | `_BOX_SET_RUNOUT_SWAP ENABLE=1`; stesso materiale e colore in un altro slot; controlla l'ordine (`_BOX_SET_RUNOUT_ORDER`) |
| RFID sconosciuto | Tag di terze parti con firmware CFS stock | Assegna a mano un profilo della libreria; oppure [firmware API7](../cfs-firmware/third-party-rfid.md) |
| Tag di terze parti mai decodificato | Non è MIFARE Classic 1K, o è in cache come sconosciuto | `_BOX_RFID_FALLBACK_CACHE`, `CLEAR=1 UID=<hex>`, poi `_BOX_RFID_READ_SLOT SLOT=<n>` |
| "Another CFS RFID read is in progress" | Due letture insieme | Attendi circa 45 s e riprova |
| La percentuale del residuo sembra sbagliata | Lunghezza nominale sbagliata, bobina usata segnata come nuova | Imposta la lunghezza nominale del profilo oppure `_BOX_RFID_SPOOL_NEW SLOT=<n> TOTAL_M=<m> REMAINING=<%>` |
| Avviso di umidità all'avvio | Umidità del CFS oltre il limite del materiale | Asciuga la bobina o cambia `humidity_limits` |

## Firmware CFS sperimentale

| Cosa vedi | Soluzione |
| --- | --- |
| `BOX_CFS_CONFIG_INFO` non mostra un'identità | Firmware stock o precedente: non viene scritto nulla, è normale |
| All'avvio vengono elencate opzioni ignorate | Opzione non scrivibile su questo firmware (es. opzione CFG6 su CFG5T) o fuori intervallo: correggi `box.cfg` |
| Il CFS non risponde più dopo un flash | Flasha l'immagine di recupero **v3.22** ([Flash e rollback](../cfs-firmware/flash.md#roll-back)) |
| Flash interrotto | Riesegui lo stesso comando; log in `/tmp/mcu_update.log` sulla T113 |

## Mainsail, Moonraker, schermo

| Cosa vedi | Soluzione |
| --- | --- |
| Mainsail non mostra il pannello CFS | Mainsail K2-OpenHost non installato o versione vecchia in cache: `./helper.sh install mainsail`, poi ricarica la pagina (Ctrl+F5) |
| Errori dell'Update Manager | Mainsail → Machine → Update Manager → **Recover** su quel componente; `./helper.sh update` |
| HelixScreen mostra "disconnected" | IP dell'host cambiato: menu 29 dell'helper (cambia indirizzo dell'host); l'host deve avere un IP fisso |
| Elenco filamenti di HelixScreen vuoto | Servizio `k2oh-helix-filaments` sulla T113; vedi [HelixScreen](../usage/helixscreen.md) |
| Telecamera nera o fotogrammi neri a 30 fps | Crowsnest `max_fps: 25`, vedi [Fotocamera](../CAMERA.md) |

## OrcaSlicer

| Cosa vedi | Soluzione |
| --- | --- |
| Il Sync imposta filamenti "Generic" | I preset filamento devono essere preset **radice** con l'ID OrcaSlicer giusto; vedi [OrcaSlicer](../ORCASLICER.md) |
| Il plugin non si collega | L'host del dispositivo deve includere la porta (`host:7125`); consenti i permessi del plugin; vedi il [plugin](../usage/orca-plugin.md) |
| Altre stampanti si comportano male dopo aver attivato l'agent | Tieni **spenta** l'opzione globale *use printer agents* di OrcaSlicer; il plugin lavora tramite il suo pannello e la mappa nel G-code |

## Ancora bloccato

Raccogli quanto elencato in [Debug: cosa allegare](debug.md#what-to-attach-when-asking-for-help) e apri una issue su [K2-OpenHost](https://github.com/MzTechnology97/K2-OpenHost/issues).
