# Comandi G-code aggiunti da K2-OpenHost

Aggiornato: **5 ottobre 2026**. [English](../en/GCODE_COMMANDS.md)

Questa pagina elenca tutti i comandi G-code che K2-OpenHost aggiunge a Kalico, divisi per tipologia. Vengono da due posti:
- i moduli K2 di [kalico-k2pro](https://github.com/MzTechnology97/kalico-k2pro) (`klippy/extras`), ramo `k2-pro-openhost`;
- le macro del profilo K2 in `config/k2/macros/` (`print.cfg`, `kamp.cfg`, `fans.cfg`, `maintenance.cfg`, `openhost_controls.cfg`).

I comandi standard di Klipper e Kalico (`G28`, `PID_CALIBRATE`, `BED_MESH_CALIBRATE`, `SET_FAN_SPEED`…) non sono ripetuti qui: vedi il [riferimento G-code di Kalico](https://docs.kalico.gg/G-Codes.html).

**Come leggere le tabelle**
- I parametri tra `[parentesi]` sono facoltativi; il valore dopo `=` è quello predefinito.
- ⚠ = il comando muove la stampante, riscalda, taglia il filamento, scrive su una scheda o toglie alimentazione. Usalo solo a stampante ferma e piatto libero, salvo dove la descrizione dice altro.
- I comandi che iniziano con `_` li usano Mainsail, HelixScreen o le macro del profilo. Puoi scriverli a mano, ma di solito si usa il pannello che li invia.
- Gli slot sono numerati da 0: il box 1 ha gli slot 0–3 (T0–T3), il box 2 i 4–7, e così via. La bobina esterna è lo slot dopo l'ultimo slot del CFS (T4 con un box).

## Indice

1. [CFS: caricamento, scaricamento e cambio filamento](#1-cfs-caricamento-scaricamento-e-cambio-filamento)
2. [CFS: avvio stampa e abbinamento dei filamenti](#2-cfs-avvio-stampa-e-abbinamento-dei-filamenti)
3. [CFS: slot, libreria filamenti e RFID](#3-cfs-slot-libreria-filamenti-e-rfid)
4. [CFS: impostazioni](#4-cfs-impostazioni)
5. [CFS: compatibilità con HelixScreen e Creality](#5-cfs-compatibilità-con-helixscreen-e-creality)
6. [Calibrazioni](#6-calibrazioni)
7. [Motori closed-loop: stato e manutenzione](#7-motori-closed-loop-stato-e-manutenzione)
8. [Ripresa dopo un'interruzione di corrente](#8-ripresa-dopo-uninterruzione-di-corrente)
9. [Scheda T113 (cicalino, alimentazione MCU, bridge USB, schermo)](#9-scheda-t113-cicalino-alimentazione-mcu-bridge-usb-schermo)
10. [Diagnostica](#10-diagnostica)
11. [Ventole, camera, luci e limiti di movimento](#11-ventole-camera-luci-e-limiti-di-movimento)
12. [Macro di stampa del profilo K2](#12-macro-di-stampa-del-profilo-k2)

## 1. CFS: caricamento, scaricamento e cambio filamento

| Comando | Parametri | A cosa serve |
| --- | --- | --- |
| `T0`, `T1`, … ⚠ | `[FLUSH=1]` | Seleziona un utensile. Durante una stampa avviata con l'abbinamento dei filamenti va allo slot abbinato; altrimenti usa l'assegnazione utensile→slot salvata per HelixScreen. Se è caricato un altro filamento fa il cambio completo (taglio, scaricamento, caricamento, spurgo nel cestino; `FLUSH=0` salta lo spurgo). Se l'abbinamento della stampa non ha uno slot per quell'utensile, la stampa va in pausa per farti scegliere. |
| `BOX_SELECT_SLOT` ⚠ | `SLOT=<n>` `[FLUSH=1]` | Cambio completo verso uno slot fisico: taglia e scarica il filamento attuale, carica il nuovo e lo spurga nel cestino. `FLUSH=0` salta lo spurgo. |
| `BOX_LOAD` ⚠ | `[SLOT=0]` | Porta il filamento di uno slot fino alla testina e inizia a seguirlo. Non taglia e non spurga: si usa con l'ugello vuoto. Se lo slot è già caricato, riprende solo a seguirlo. |
| `BOX_UNLOAD` ⚠ | `[MANUAL=0]` | Scaricamento completo del filamento caricato: riscalda, fa l'homing se serve, taglia, va al cestino e riporta il filamento nel CFS, poi spegne il riscaldatore. Gestisce anche la bobina esterna. `MANUAL=1` riporta solo il filamento nel CFS, senza riscaldare né tagliare. |
| `BOX_CUT` ⚠ | `[FORCE=0]` | Va alla taglierina e taglia il filamento. Senza `FORCE=1` non taglia se il sensore non vede filamento. Richiede `cut_pos_x` in `[box]` (vedi `CALIBRATE_CUT_POS`). |
| `BOX_BUFFER_RETRACT` | — | Esegue solo la fase di ritiro del buffer del CFS che alimenta lo slot caricato. |
| `BOX_GO_TO_WASTEBIN` ⚠ | — | Porta la testina al cestino (scivolo di spurgo). |
| `NOZZLE_CLEAN` ⚠ | — | Va al cestino e pulisce l'ugello sul tampone, con velocità e accelerazione ridotte. Poi ripristina i limiti di movimento precedenti. |
| `BOX_NOZZLE_CLEAN` ⚠ | — | Uguale a `NOZZLE_CLEAN` (nome usato da HelixScreen). |

## 2. CFS: avvio stampa e abbinamento dei filamenti

| Comando | Parametri | A cosa serve |
| --- | --- | --- |
| `BOX_PRINT_INFO` | `[FILENAME=<file>]` | Legge i metadati dello slicer di un file e pubblica gli utensili usati (materiale, colore, quantità di filamento) nello stato `box`, dove li mostra la finestra di stampa CFS di Mainsail. Non avvia niente. |
| `BOX_PRINT_START` ⚠ | `MAP=<utensile:slot,…>` `[FILENAME=<file>]` | Avvia una stampa con un abbinamento utensile→slot esplicito, per esempio `MAP=0:2,1:0`. Ogni utensile usato dal file deve essere abbinato, e ogni slot deve essere online e contenere filamento. Lo invia la finestra di stampa CFS di Mainsail. |
| `PARSE_FLUSH_VOLUMES` | — | Legge dai metadati dello slicer del file caricato la matrice dei volumi di spurgo e le temperature di stampa. Lo chiama la sequenza di avvio stampa. |
| `BOX_RUNOUT_CHECK` ⚠ | — | Gestisce la fine del filamento nel CFS: passa a una bobina identica se lo scambio automatico è attivo, altrimenti mette in pausa. Lo chiama il sensore, non si usa a mano. |

## 3. CFS: slot, libreria filamenti e RFID

Questi comandi li invia il pannello CFS di Mainsail. I dati restano salvati sull'host anche dopo un riavvio.

| Comando | Parametri | A cosa serve |
| --- | --- | --- |
| `BOX_RFID_SCAN` | `[ADDR=<box>]` `[NUM=0x0F]` | Rilegge i tag RFID di tutti gli slot occupati (o di un solo box; `NUM` è una maschera degli slot, bit 0 = slot A). |
| `_BOX_RFID_READ_SLOT` | `SLOT=<n>` | Forza la rilettura RFID di uno slot. |
| `_BOX_RFID_SPOOL_NEW` | `SLOT=<n>` `[REMAINING=100]` | Dichiara nuova la bobina di uno slot e porta la stima del filamento rimasto a `REMAINING` per cento. Serve per i tag con numero di serie generico: altrimenti una bobina nuova erediterebbe la stima di una usata con stessa marca, materiale, colore e lunghezza. |
| `_BOX_SLOT_SET` | `SLOT=<n>` `MATERIAL=<tipo>` `COLOR=#RRGGBB` `[TARGET_TEMP]` `[BRAND]` `[NAME]` `[SPOOLMAN_ID]` | Salva a mano i dati del filamento di uno slot (per bobine senza RFID). |
| `_BOX_SLOT_CLEAR` | `SLOT=<n>` | Cancella i dati del filamento di uno slot. |
| `_BOX_SLOT_ASSIGN` | `SLOT=<n>` `FILAMENT_ID=<id>` `[COLOR=#RRGGBB]` | Assegna a uno slot un profilo della libreria filamenti, eventualmente con un altro colore. Rifiutato se lo slot è gestito da un tag RFID presente. |
| `_BOX_FILAMENT_SET` | `ID=<id>` `MATERIAL=<tipo>` `[COLOR]` `[TARGET_TEMP]` `[MIN_TEMP]` `[MAX_TEMP]` `[PRESSURE_ADVANCE]` `[BRAND]` `[NAME]` `[SPOOLMAN_ID]` | Crea o aggiorna un profilo filamento riutilizzabile nella libreria (`cfs_filaments.json`). |
| `_BOX_FILAMENT_DELETE` | `ID=<id>` | Cancella un profilo filamento personalizzato. |
| `_BOX_FILAMENT_RELOAD` | — | Ricarica dal disco il file della libreria filamenti e l'importazione K2-RFID, per esempio dopo aver modificato il file. |
| `_BOX_MATERIAL_SET` | `MATERIAL=<tipo>` `TARGET_TEMP=<170–350>` | Salva la temperatura di stampa predefinita di un tipo di materiale. |
| `_BOX_RFID_MAP_SET` | `CODE=<codice rfid>` `MATERIAL` `BRAND` `NAME` `[TARGET_TEMP]` | Insegna al sistema un codice RFID sconosciuto: da quel momento quel codice mostra questo materiale, marca e nome. |
| `_BOX_RFID_MAP_DELETE` | `CODE=<codice rfid>` | Elimina un codice RFID imparato. |
| `RFID_READER_READ` | — | Mostra l'ultimo dato letto dal lettore RFID separato della bobina esterna. |

## 4. CFS: impostazioni

Interruttori del pannello CFS. Restano salvati anche dopo un riavvio.

| Comando | Parametri | A cosa serve |
| --- | --- | --- |
| `_BOX_SET_RUNOUT_SWAP` | `[ENABLE=1]` | Quando una bobina finisce, continua da sola con una bobina identica in un altro slot. |
| `_BOX_SET_RUNOUT_ORDER` | `[ORDER=<slot>]` | Ordine in cui usare le bobine identiche per lo scambio automatico, per esempio `ORDER=2,1,0`. Vuoto = ordine automatico. |
| `_BOX_SET_UNLOAD_AFTER_PRINT` | `[ENABLE=0]` | Scarica il filamento in automatico a fine stampa. |
| `_BOX_SET_RFID_INSERT_READING` | `[ENABLE=0]` | Legge il tag RFID ogni volta che si inserisce una bobina. |
| `_BOX_SET_RFID_STARTUP_READING` | `[ENABLE=0]` | Legge tutti i tag RFID all'avvio di Klipper. |
| `_BOX_SET_CLOG_DETECTION` | `[ENABLE=1]` | Rilevamento intasamenti: pausa quando l'estrusore spinge `clog_extruder_length` (80 mm) mentre la CFS non ricarica. Lo salva la CFS; `clog_detection` in `box.cfg` è il valore predefinito. È anche lo switch **Clog detection** nel menu impostazioni della CFS in Mainsail. |

## 5. CFS: compatibilità con HelixScreen e Creality

HelixScreen e gli strumenti di Creality inviano i comandi originali della K2. K2-OpenHost li accetta, così lo schermo continua a funzionare con l'host esterno. Non serve scriverli a mano.

| Comando | Parametri | A cosa serve |
| --- | --- | --- |
| `BOX_INFO_REFRESH` | `[ADDR]` `[NUM]` | Uguale a `BOX_RFID_SCAN` (nome Creality). |
| `BOX_MODIFY_TN` | `T1A=T1B …` | Cambia l'assegnazione utensile→slot con i nomi Creality degli slot (numero del box + lettera A–D). |
| `BOX_MODIFY_TN_DATA` | `ADDR=<1–4>` `NUM=<A–D>` `PART=color_value` `DATA=<colore>` | Cambia dallo schermo il colore di uno slot. In questo modo si può cambiare solo il colore. |
| `BOX_ENABLE_AUTO_REFILL` | `[ENABLE=1]` | Uguale a `_BOX_SET_RUNOUT_SWAP` (nome Creality). |
| `CR_BOX_EXTRUDE` ⚠ | `TNN=<slot>` | Fase di caricamento di un cambio originale: esegue un cambio completo verso quello slot. |
| `CR_BOX_RETRUDE` ⚠ | — | Fase di scaricamento di un cambio originale: esegue `BOX_UNLOAD`. |
| `CR_BOX_PRE_OPT`, `CR_BOX_CUT`, `CR_BOX_WASTE`, `CR_BOX_FLUSH`, `CR_BOX_END_OPT`, `BOX_GO_TO_EXTRUDE_POS`, `BOX_MODE_WAIT`, `BOX_MOVE_TO_SAFE_POS`, `BOX_SAVE_FAN`, `BOX_RESTORE_FAN` | — | Accettati e ignorati di proposito: la sequenza di cambio di K2-OpenHost si occupa già di parcheggio, taglio, spurgo e ventole. |

## 6. Calibrazioni

| Comando | Parametri | A cosa serve |
| --- | --- | --- |
| `MOTOR_CALIBRATE` ⚠ | `AXIS=X`, `Y` o `XY` `[DETAIL=raw]` | Calibra i motori closed-loop di X e Y (encoder e offset elettrico). Alla prima chiamata chiede solo di mettere la testina al centro e il piatto in basso, e spegne i motori; alla seconda esegue la calibrazione. |
| `MOTOR_CALIBRATE AXIS=E` ⚠ | `STAGE=encoder\|offset\|1\|2` `[DETAIL=raw]` | Calibra il motore closed-loop dell'estrusore, una fase alla volta. |
| `MOTOR_ACCEPT_CALIBRATION` | `AXIS=X`, `Y` o `X,Y` | Permette l'homing con una calibrazione dei motori che il controllo all'avvio ha segnalato come sospetta, fino al prossimo avvio di Klipper. Usalo solo se sai che la calibrazione è buona; altrimenti esegui `MOTOR_CALIBRATE`. |
| `CALIBRATE_CUT_POS` ⚠ | — | Trova la posizione X della taglierina (fa l'homing di XY se serve) e la salva come `cut_pos_x`. Va eseguito dopo aver cambiato la taglierina o la testina. |
| `PRTOUCH_HOME` ⚠ | `[PRINT_TEMP]` `[SAMPLES]` `[TRAVEL_SPEED]` `[Z_HOP]` … | Homing di Z con più tocchi dell'ugello (sensore di pressione): più preciso di un solo `G28 Z`. Con `PRINT_TEMP` compensa la dilatazione termica dell'ugello a quella temperatura. |
| `PRTOUCH_SCRUB` ⚠ | — | Trova la linguetta flessibile sul retro del piatto e ci pulisce sopra l'ugello prima della misura. |
| `PRTOUCH_SCAN_CALIBRATE` ⚠ | `[MODEL=default]` `[SAMPLES]` … | Calibra il modello di scansione del Cartographer usando il tocco dell'ugello come Z=0. Richiede il Cartographer. |
| `PRTOUCH_AXIS_TWIST_COMPENSATION` ⚠ | `[SAMPLES]` `[LIFT_SPEED]` … | Misura la torsione dell'asse X confrontando le scansioni del Cartographer con i tocchi dell'ugello. Richiede il Cartographer. |
| `BEDPID` ⚠ (macro) | — | Taratura PID del piatto a 100 °C, poi `SAVE_CONFIG` (riavvia Klipper). |
| `NOZZLE_PID` ⚠ (macro) | — | Taratura PID dell'ugello a 230 °C con la ventola pezzo accesa, poi `SAVE_CONFIG`. |
| `NOZZLE_PID_HIGH` ⚠ (macro) | — | Uguale a 280 °C, per i filamenti ad alta temperatura. |

## 7. Motori closed-loop: stato e manutenzione

I motori X, Y ed E della K2 Pro sono closed-loop, con un proprio controller sul bus RS-485.

| Comando | Parametri | A cosa serve |
| --- | --- | --- |
| `MOTOR_STATUS` | `[VERBOSE=1]` `[REFRESH=1]` | Stato leggibile dei motori: avvio, prontezza, calibrazione, protezioni, temperature. `REFRESH=1` rilegge la calibrazione dai motori. |
| `MOTOR_EVENTS` | `[COUNT=n]` `[VERBOSE=1]` | Storico degli eventi di protezione (stallo, sovracorrente, guasti). `VERBOSE=1` dà un JSON da allegare a una segnalazione. |
| `MOTOR_QUERY_FAULTS` | — | Chiede subito a ogni motore i codici di errore, avviso e stato. |
| `MOTOR_CLEAR_ERROR` | — | Legge i guasti attivi dei motori, li cancella e riporta il risultato. |
| `MOTOR_RETRY_STARTUP` | — | Ripete la sequenza di avvio dei motori (per esempio dopo che il collegamento RS-485 è tornato). |
| `REQUIRE_EXTRUDER_CLEAR` | — | Interrompe la macro in corso (di solito `RESUME`) se il motore dell'estrusore ha un guasto di protezione bloccato. Prima prova a cancellarlo una volta. |
| `MOTOR_CFG_OVERRIDE_STATUS` | `[AXIS=XYE]` `[DETAIL=raw]` | Confronta i parametri dei motori impostati in `macros/motor_control.cfg` con i valori che i motori hanno adesso. |
| `MOTOR_READ_PARAM` | `PARAM=<nome>` | Legge un parametro di un motore, per esempio `PARAM=x_param_stall_cur_A`. |
| `MOTOR_FLASH_PARAM` ⚠ | `PARAM=<nome>` `[VALUE]` `[COMMIT=0]` | Scrive un parametro di un motore e lo verifica. Senza `COMMIT=1` il valore resta solo fino al riavvio del motore; con `COMMIT=1` viene salvato nella flash del motore. Solo per assistenza. |
| `MOTOR_READ_ALL_PIN_IO` | — | Legge le linee di step, direzione e stallo dei motori. |

## 8. Ripresa dopo un'interruzione di corrente

| Comando | Parametri | A cosa serve |
| --- | --- | --- |
| `PLR_STATUS` | — | Dice se una stampa si può riprendere dopo un'interruzione di corrente, e da dove. |
| `PLR_RECOVER` ⚠ | `CONFIRM=1` | Riprende la stampa interrotta dal punto salvato, ripristinando temperature, posizione e stato del CFS. Rifiuta senza `CONFIRM=1`, durante un'altra stampa o se non c'è un punto salvato. |
| `PLR_DISCARD` | — | Cancella il punto salvato: la stampa non si potrà più riprendere. |

## 9. Scheda T113 (cicalino, alimentazione MCU, bridge USB, schermo)

Comunicano con `k2oh-ctl` sulla scheda T113 della stampante (`[k2_t113]` in `macros/k2_t113.cfg`).

| Comando | Parametri | A cosa serve |
| --- | --- | --- |
| `BOARD_STATUS` | — | Mostra l'ultima telemetria del T113: slot, alimentazione degli MCU, temperatura del SoC, tempo di accensione, spazio libero sulla UDISK, stato del gadget USB e se ogni bridge è attivo. |
| `BUZZER` | `[MS=200]` `[COUNT=1]` oppure `PATTERN=on,off,…` oppure `SOUND=<nome>` | Fa suonare il cicalino della stampante. `SOUND` riproduce uno dei suoni configurati: `print_complete`, `pause`, `error`, `cancel`, `shutdown`, `rfid`. |
| `M300` | `[P=200]` | Beep standard per gli slicer (durata in ms; il cicalino ha un tono fisso). Solo se non esiste già un'altra macro `M300`. |
| `USB_BRIDGES_RESTART` ⚠ | `CONFIRM=1` | Riavvia i tre bridge USB sul T113. I collegamenti con gli MCU cadono per un attimo, quindi di solito Klipper va in shutdown: dopo serve `FIRMWARE_RESTART`. Solo a stampante ferma. |
| `MCU_POWER_CYCLE` ⚠ | `CONFIRM=1` | Toglie alimentazione agli MCU della stampante per 2 secondi, poi esegue `FIRMWARE_RESTART`. Funziona anche con Klipper in shutdown. Solo a stampante ferma. |
| `SCREEN_RESTART` | — | Riavvia HelixScreen sul display della stampante. |

## 10. Diagnostica

Solo lettura: mostrano informazioni e non cambiano niente.

| Comando | Parametri | A cosa serve |
| --- | --- | --- |
| `BOX_DEBUG` | `[RAW=0]` | Rapporto completo sul CFS: box online, stato attuale, sensori, motore di cambio, rilevamento intasamenti, registri di ogni box. `RAW=1` aggiunge le risposte grezze. |
| `BOX_ENV_DEBUG` | — | Versioni, hardware, temperatura e umidità del CFS, lette in quel momento. |
| `SERIAL_STATUS` | — | Stato e contatori del collegamento RS-485 (frame, timeout, errori CRC, collegamento perso/ok). |
| `LINK_MONITOR_REPORT` | — | Percentili dei tempi di andata e ritorno di ogni collegamento seriale (MCU e RS-485) dall'avvio di Klipper. Richiede `[link_monitor]`. |
| `FAN_FEEDBACK_STATUS` | — | Velocità delle ventole che hanno un tachimetro. |
| `EXTENDED_ZONE_TRANSFORM_STATUS` | — | Stato dell'instradamento nella zona estesa: l'area di Y oltre il limite normale del piatto (cestino e taglierina) si raggiunge solo dentro una finestra sicura di X. |

## 11. Ventole, camera, luci e limiti di movimento

| Comando | Parametri | A cosa serve |
| --- | --- | --- |
| `M106` (macro) | `[P=0]` `[S=255]` | Velocità delle ventole: `P0` ventola delle parti sulla testa, `P2` ventola delle parti laterale (`aux_fans`), `P3` ventole di estrazione/filtro della camera (come velocità minima). Mainsail le chiama **Toolhead Part Fan**, **Side Part Fan** e **Chamber Exhaust Fans**. |
| `M107` (macro) | `[P=0]` | Spegne la ventola scelta con `P` (stessi numeri di `M106`). |
| `M141` (macro) | `S=<°C>` | Temperatura della camera: sopra 40 °C usa il riscaldatore della camera, da 1 a 40 °C le ventole di estrazione tengono la camera sotto quel valore, 0 spegne entrambi. |
| `M191` (macro) | `S=<°C>` | Come `M141`, poi aspetta che la camera arrivi alla temperatura. |
| `SET_TEMPERATURE_FAN_MANUAL_SPEED` | `TEMPERATURE_FAN=<nome>` `SPEED=<0–1>` | Imposta una velocità minima per una ventola a controllo di temperatura (usato per il filtro della camera). Il controllo automatico può comunque farla girare più veloce. |
| `SET_FAN_SPEED FAN=chamber_exhaust_fans` | `SPEED=<0–1>` | Lo slider **Chamber Exhaust Fans** di Mainsail: imposta la stessa velocità minima (`generic_fan: True` in `[temperature_fan_manual_floor chamber_exhaust_fans]`); `M106 P3` sposta lo slider. |
| `LED_IDLE_MANAGER_ON` / `LED_IDLE_MANAGER_OFF` | — | Attiva o disattiva lo spegnimento automatico della luce per questa sessione di Klipper (la luce resta accesa durante la stampa e si spegne dopo un po' senza attività). |
| `SET_LED_IDLE_MANAGER` | `[ENABLE=1]` | Uguale, con un parametro. |
| `LED_IDLE_MANAGER_STATUS` | — | Mostra lo stato dello spegnimento automatico della luce. |
| `SAVE_MOTION_LIMITS` | `[NAME=default]` `[INCLUDE_GCODE=0]` | Salva con un nome i limiti attuali di velocità e accelerazione (`INCLUDE_GCODE=1` salva anche lo stato G-code). |
| `RESTORE_MOTION_LIMITS` | `[NAME=default]` `[INCLUDE_GCODE=0]` `[MOVE=0]` | Ripristina i limiti salvati con `SAVE_MOTION_LIMITS`. Con `INCLUDE_GCODE=1` ripristina anche lo stato G-code, e `MOVE=1` torna alla posizione salvata. |
| `M205` (macro) | `[X]` `[Y]` | Comando jerk degli slicer: imposta la square corner velocity di Kalico al valore di `X` (o di `Y`). |

## 12. Macro di stampa del profilo K2

| Comando | Parametri | A cosa serve |
| --- | --- | --- |
| `START_PRINT` ⚠ | `[BED_TEMP=60]` `[EXTRUDER_TEMP=220]` `[CHAMBER_TEMP=0]` `[MIN_CHAMBER_TEMP]` `[MATERIAL]` `[SOAK_TIME]` `[ATC]` | Inizio stampa, chiamato dal G-code iniziale dello slicer: riscalda piatto e camera, attesa di riscaldamento facoltativa, homing, pulizia dell'ugello a caldo sul cestino e di nuovo alla temperatura del tocco, mesh adattiva del piatto e compensazione della torsione dell'asse, homing di Z col tocco dell'ugello alla temperatura di stampa, poi riscalda l'ugello. |
| `END_PRINT` ⚠ | — | Fine stampa: ritrae se l'ugello è caldo, spegne riscaldatori e ventole, alza Z e parcheggia al cestino. |
| `PAUSE` ⚠ | `[SKIP_RETRACT_WIPE=0]` | Pausa: salva la temperatura da usare alla ripresa, abbassa l'ugello a 140 °C, ritrae e pulisce, alza Z, pulisce e parcheggia al cestino, spegne la ventola pezzo. |
| `RESUME` ⚠ | `[VELOCITY]` | Ripresa: completa le operazioni del CFS interrotte, riscalda e innesca al cestino, ripristina le ventole e torna alla stampa. |
| `CANCEL_PRINT` ⚠ | — | Annulla la stampa ed esegue `END_PRINT`. |
| `HOME_IF_NEEDED` ⚠ | `[AXIS=XYZ]` | Fa l'homing solo degli assi che non l'hanno ancora fatto. |
| `BED_MESH_CALIBRATE` ⚠ | come in Kalico | Il comando standard, eseguito con velocità e accelerazione ridotte; poi ripristina i limiti precedenti. |
| `LUBRICATE_RAILS` ⚠ | `[ITERATIONS=1]` `[SPEED=500]` | Muove la testina da un angolo all'altro su tutto il piatto per distribuire il lubrificante delle guide. |
| `LINE_PURGE` ⚠ | — | Linea di spurgo KAMP vicino agli oggetti stampati. |
| `STATUS_MSG` | `MSG=<testo>` `[TYPE]` `[PREFIX]` `[DISPLAY]` | Mostra un messaggio nella console e sul display. |
| `START_PRINT_ATC` | `[ENABLE=0\|1]` | Calibrazione della torsione dell'asse a inizio stampa accesa o spenta, salvata tra i riavvii (è anche lo switch **Axis Twist Compensation** in Mainsail); senza `ENABLE` mostra lo stato. Saltata quando la sonda è PRTouch. |
| `WARMUP` ⚠ | `[LOOPS=3]` `[X_ACCEL_MAX=10000]` `[Y_ACCEL_MAX=10000]` | Prova di stress del movimento: passate in X, Y e diagonale sull'area del piatto (Y fino a 301 mm), poi ripristina i limiti configurati. |
| `AUTO_WARMUP` ⚠ | `[CYCLES=3]` | Rodaggio lungo: `WARMUP` a tre accelerazioni con pause di 20 minuti, ripetuto `CYCLES` volte. |
| `TEST_SPEED` ⚠ | `[SPEED]` `[ACCEL]` `[ITERATIONS=5]` `[BOUND=25]` `[SMALLPATTERNSIZE=20]` | Prova dei passi persi: `GET_POSITION` dopo l'homing X/Y, figure veloci sul piatto, poi di nuovo homing e `GET_POSITION`. |
| `ACCELL_TEST_X` / `ACCELL_TEST_Y` ⚠ | `[STEPS=20]` `[ACCEL_START=10000]` `[ACCEL_STEP=1000]` `[VELOCITY=500]` `[VELOCITY_STEP=0]` | Un solo asse avanti e indietro (X a metà Y, Y a metà X); ogni passata alza accelerazione (e velocità) oltre i limiti configurati e viene scritta nel log; alla fine i limiti tornano quelli configurati. |

Macro interne, usate da quelle sopra: `_START_PRINT_VARS` (impostazioni dell'avvio stampa, in `macros/overrides.cfg`), `_NOZZLE_HOT_CLEAN`, `_MOTION_TEST_RESTORE`, `_PAUSE_CONTEXT`, `_PAUSE_Z_MOVE`, `_RETRACT_WIPE`, `_END_PRINT_Z_MOVE`, `_RESET_PRINT_STATE`, `_KAMP_Settings`, `_BOX_PAUSE_CAPTURE`, `_BOX_RESUME_PREPARE`, `_BOX_RESUME_COMMIT`.
