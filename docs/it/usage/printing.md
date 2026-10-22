# Stampare

## G-code di avvio e fine nello slicer { #slicer-start-and-end-g-code }

Il profilo K2 esegue tutta la sequenza di avvio in `START_PRINT`. Nelle impostazioni stampante dello slicer usa:

=== "G-code di avvio (OrcaSlicer)"

    ```text
    START_PRINT EXTRUDER_TEMP=[nozzle_temperature_initial_layer] BED_TEMP=[bed_temperature_initial_layer_single] MATERIAL={filament_type[initial_tool]} CHAMBER_TEMP=[overall_chamber_temperature] MIN_CHAMBER_TEMP=[chamber_minimal_temperature]
    T[initial_no_support_extruder]
    ```

    La stampante di riferimento aggiunge una linea di spurgo dopo il comando `T`; `LINE_PURGE` (KAMP) è un'alternativa.

=== "G-code di fine"

    ```text
    END_PRINT
    ```

=== "G-code di pausa"

    ```text
    PAUSE
    ```

Lascia vuoto *Change filament G-code*: i comandi `T<n>` dello slicer vanno al CFS attraverso la mappa dei tool della stampa. Imposta il G-code flavour su **Klipper**.

## Cosa fa `START_PRINT`

1. Scalda piatto e camera (`BED_TEMP`, `CHAMBER_TEMP`; `MIN_CHAMBER_TEMP` attende un minimo), heat soak del piatto opzionale.
2. Fa l'homing degli assi non ancora referenziati (`[z_align]` porta prima il piatto al finecorsa in basso).
3. Pulisce il nozzle caldo sopra il cestino (temperatura di stampa − 10 °C), raffredda fino alla temperatura di tastatura (140 °C) con la ventola pezzo, pulisce di nuovo.
4. Bed mesh adattiva e, se attiva, compensazione della torsione dell'asse.
5. Homing Z con il tocco del nozzle (PRTouch) alla temperatura di stampa.
6. Scalda il nozzle a `EXTRUDER_TEMP`.

Impostazioni in `macros/overrides.cfg` (`_START_PRINT_VARS`):

| Variabile | Predefinito | Significato |
| --- | --- | --- |
| `variable_heat_soak` | 0 | Tempo di heat soak del piatto, minuti |
| `variable_offset_<MATERIALE>` | 0 | Z offset per materiale, es. `variable_offset_ASA` |
| `variable_offset_DEFAULT` | 0.00 | Z offset di riserva |
| `variable_hot_clean` | 1 | Pulisce il nozzle caldo prima di raffreddarlo alla temperatura di tastatura |
| `variable_hot_clean_offset` | 10 | Temperatura di pulizia a caldo = temperatura di stampa − questo valore |
| `variable_prtouch_scrub` | 0 | Strofina il nozzle sulla linguetta del piatto |
| `variable_adaptive_axis_twist_comp` | 0 | Valore predefinito dell'interruttore axis twist (`START_PRINT_ATC`) |

L'interruttore **Axis Twist Compensation** in Mainsail (o `START_PRINT_ATC ENABLE=0|1`) attiva o disattiva la calibrazione all'avvio della stampa; viene saltata quando la sonda è PRTouch.

## Avviare una stampa

| Da | Cosa succede |
| --- | --- |
| Mainsail → G-code files → **Print** | La [finestra di stampa](mainsail.md#print-dialog-with-cfs-mapping) abbina ogni tool a uno slot CFS |
| OrcaSlicer → **Upload and print** | Kalico abbina i tool automaticamente, oppure usa gli slot scelti nel [pannello del plugin](orca-plugin.md) |
| OrcaSlicer → solo **Upload** | Il file aspetta in Mainsail; avvialo dalla finestra di stampa |
| HelixScreen | Avvia il file; si applica l'abbinamento automatico |

La porta USB esterna della stampante non funziona in modalità OpenHost: invia i file in rete.

## Durante la stampa

- **Cambi tool**: `T<n>` taglia, scarica, carica lo slot abbinato e spurga nel cestino (volumi di spurgo dalla matrice dello slicer).
- **Fine filamento**: con il runout swap attivo, il box continua su una bobina identica; altrimenti la stampa va in pausa e suona il cicalino.
- **Rilevamento intasamenti**: pausa se l'estrusore spinge mentre il CFS non ricarica.
- **Collegamento RS-485 perso** (CFS e motori X/Y muti per 10 s): la stampa va in pausa (`link_lost_action: pause`).
- **Controllo del filamento in tempo reale**: ogni minuto, il filamento che serve ancora a ogni tool confrontato con quanto resta sulla sua bobina.

## Pausa, ripresa, annullamento

| Comando | Cosa fa |
| --- | --- |
| `PAUSE` | Salva la temperatura, abbassa il nozzle a 140 °C, ritrae e pulisce, alza Z, pulisce e parcheggia sul cestino, spegne il raffreddamento del pezzo |
| `RESUME` | Completa le operazioni CFS interrotte, scalda e innesca sul cestino, ripristina le ventole, torna alla stampa |
| `CANCEL_PRINT` | Annulla ed esegue `END_PRINT` |
| `END_PRINT` | Ritrae se caldo, spegne riscaldatori e ventole, alza Z, parcheggia sul cestino |

Se un'operazione CFS ha bloccato la stampa, il pannello CFS mostra un avviso di recupero con il motivo; risolvi la causa, poi `RESUME`.

## Ripresa dopo un'interruzione di corrente

Il profilo attiva `[power_loss_recovery]`, che salva dei checkpoint durante la stampa e ritrova Z sul finecorsa in basso (`[z_align]`).

| Comando | Cosa fa |
| --- | --- |
| `PLR_STATUS` | Se una stampa si può riprendere e da dove |
| `PLR_RECOVER CONFIRM=1` | Riprende dal checkpoint: porta il piatto al finecorsa, fa l'homing di X/Y, ripristina riscaldatori, CFS, mesh e posizione |
| `PLR_DISCARD` | Cancella il checkpoint |

!!! note
    `PLR_RECOVER` non è ancora stato validato con una vera interruzione di corrente sorvegliata. Con un UPS puoi disattivare `[power_loss_recovery]` e `[z_align]`; senza di essi, Z può lavorare a 64 microstep (lo `z_align` comandato dalla MCU perde passi a 64). Senza UPS tienili entrambi, con Z a 16 microstep.

## Comandi di calibrazione

| Comando | Quando |
| --- | --- |
| `CALIBRATE_CUT_POS` | Dopo aver cambiato la taglierina o la testina |
| `MOTOR_CALIBRATE AXIS=XY` | Quando `MOTOR_STATUS` segnala una calibrazione dei motori, o dopo lavori meccanici su X/Y |
| `BEDPID`, `NOZZLE_PID`, `NOZZLE_PID_HIGH` | Dopo aver cambiato un riscaldatore o un termistore |
| `PRTOUCH_HOME` | Homing Z con più tocchi, più preciso di un singolo `G28 Z` |
| `LUBRICATE_RAILS` | Distribuisce il lubrificante delle guide |
| `TEST_SPEED`, `ACCELL_TEST_X/Y`, `WARMUP` | Test di passi persi e di stress del movimento |

Tutti i comandi: [riferimento G-code](../GCODE_COMMANDS.md).
