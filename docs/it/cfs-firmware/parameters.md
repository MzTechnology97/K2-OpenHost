# Parametri runtime (CFG6)

Il firmware CFG6 v3.25 espone **28 parametri** dell'applicazione CFS stock. **23 sono scrivibili**; gli ID 0, 4, 10, 25 e 26 sono in sola lettura (solo GET). `[box_cfs_runtime]` di Kalico li scrive da `box.cfg` all'avvio di Klipper.

!!! info "Come leggere i valori"
    - Le velocità del motore dell'hub `1–255` sono **valori di comando grezzi**. Non esiste una conversione dimostrata in mm/s o giri: `220` non significa 220 mm/s. I feeder delle bobine sono solo ON/OFF.
    - I valori `_ms` sono millisecondi reali in `box.cfg`. L'ID 8 deve essere multiplo di 10, gli ID 20 e 22 multipli di 20 (il firmware conta a tick di 10/20 ms).
    - Un **timeout** sposta una scadenza di errore, un **delay** cambia un'attesa, un **count** cambia le ripetizioni di un ciclo. Nessuno di questi velocizza l'estrusore della testina.

## Tutti i 28 parametri

| ID | Opzione `box.cfg` | Stock | Intervallo | CM5 di riferimento | Scrivibile | Cosa fa |
|---:|---|---:|---|---:|:---:|---|
| 0 | `feeder_forward_speed` | 255 | 1–255 | — | No | Il feeder della bobina è ON/OFF: nessuna velocità da regolare |
| 1 | `hub_forward_speed` | 100 | 1–255 | 100 | Sì | Velocità dell'hub nella spinta iniziale in avanti |
| 2 | `hub_transition_speed` | 200 | 1–255 | 220 | Sì | Velocità dell'hub nel trasferimento verso buffer/testina: **la principale velocità di trasferimento** |
| 3 | `hub_insert_speed` | 155 | 1–255 | 100 | Sì | Velocità dell'hub nell'inserimento finale guidato dal sensore |
| 4 | `feeder_reverse_speed` | 255 | 1–255 | — | No | La retromarcia del feeder è ON/OFF |
| 5 | `hub_reverse_speed` | 80 | 1–255 | 150 | Sì | Velocità dell'hub mentre ritira il filamento allo scaricamento |
| 6 | `reverse_detooth_enable` | 1 | 0/1 | True | Sì | Attiva il passo di sgancio degli ingranaggi (de-tooth) durante la retromarcia |
| 7 | `hub_transition_wait_ms` | 3200 | 100–10000 | 3200 | Sì | Pausa dopo la spinta dell'hub, prima del percorso verso il buffer |
| 8 | `insert_sensor_timeout_ms` | 7000 | 1000–50000, passo 10 | 7000 | Sì | Finestra di attesa del sensore di inserimento |
| 9 | `hub_pullback_timeout_ms` | 5000 | 500–15000 | 5000 | Sì | Limite di tempo della fase di ritiro allo scaricamento |
| 10 | `unload_sensor_timeout_ms` | 1000 | — | — | No | Non modificato in CFG6 |
| 11 | `rfid_seek_speed` | 160 | 1–255 | 160 | Sì | Velocità dell'hub mentre cerca il tag RFID |
| 12 | `rfid_measure_speed` | 120 | 1–255 | 150 | Sì | Velocità dell'hub mentre la bobina si muove durante la lettura RFID |
| 13 | `rfid_reposition_speed` | 100 | 1–255 | 100 | Sì | Velocità dell'hub nel riposizionamento tra i passi RFID |
| 14 | `rfid_seek_move_ms` | 800 | 100–5000 | 800 | Sì | Durata del movimento di ricerca del tag |
| 15 | `rfid_seek_settle_ms` | 200 | 10–2000 | 200 | Sì | Pausa dopo il movimento di ricerca |
| 16 | `rfid_post_auth_wait_ms` | 1000 | 100–5000 | 1000 | Sì | Attesa dopo l'autenticazione del tag |
| 17 | `rfid_pre_measure_settle_ms` | 400 | 1–2000 | 400 | Sì | Pausa prima della lettura RFID |
| 18 | `rfid_neighbor_detect_delay_ms` | 400 | 50–2000 | 400 | Sì | Temporizzazione del movimento di rilevamento della bobina adiacente |
| 19 | `rfid_neighbor_settle_ms` | 100 | 10–1000 | 100 | Sì | Pausa di assestamento dopo il movimento della bobina adiacente |
| 20 | `feed_total_timeout_ms` | 25000 | 5000–60000, passo 20 | 25000 | Sì | Timeout complessivo dell'alimentazione verso la testina |
| 21 | `feed_recovery_timeout_ms` | 3000 | 500–10000 | 3000 | Sì | Tempo concesso a un recupero dell'alimentazione |
| 22 | `odometer_stall_timeout_ms` | 500 | 100–2000, passo 20 | 500 | Sì | Nessun avanzamento dell'odometro per questo tempo = blocco |
| 23 | `rfid_neighbor_retry_count` | 3 | 1–10 | 1 | Sì | Tentativi nella ricerca RFID della bobina adiacente |
| 24 | `reverse_detooth_timeout_ms` | 1000 | 100–10000 | 1000 | Sì | Soglia di tempo del passo de-tooth (lavora con l'ID 6) |
| 25 | `buffer_fill_timeout_ms` | 30000 | — | — | No | Non modificato in CFG6 |
| 26 | `transition_detect_timeout_ms` | 300 | — | — | No | Non modificato in CFG6 |
| 27 | `load_retry_count` | 3 | 1–10 | 1 | Sì | **Cicli di pretensionamento** avanti/indietro durante il caricamento (non tentativi generici) |

La colonna "CM5 di riferimento" è quello che usa la macchina di riferimento, verificato con la rilettura del 18 ottobre 2026: **non è una raccomandazione**. L'analisi completa parametro per parametro (indirizzi ARM degli agganci, rischi, prove) è in [CFS_RUNTIME_CFG6_PARAMETERS_IT.md](https://github.com/MzTechnology97/kalico-k2pro/blob/k2-pro-openhost/docs/CFS_RUNTIME_CFG6_PARAMETERS_IT.md).

!!! tip "Velocità del CFS e velocità della testina"
    Gli ID 1, 2, 3 e 5 muovono il **motore dell'hub del CFS**. L'estrusore della testina si imposta in `[box]`: `hotend_feed_speed` (mm³/s), `retract_velocity` ed `external_feed_velocity` (mm/min).

## Attivare i valori { #enable-the-values }

Il `box.cfg` distribuito tiene tutto commentato, così un'installazione nuova non scrive mai sul CFS. Su un CFS verificato come CFG6 (`BOX_CFS_CONFIG_INFO`):

```ini
[box_cfs_runtime]
auto_apply: True
hub_transition_speed: 220
hub_insert_speed: 100
hub_reverse_speed: 150
rfid_measure_speed: 150
rfid_neighbor_retry_count: 1
load_retry_count: 1
#reverse_detooth_enable: True
#hub_pullback_timeout_ms: 5000
```

1. Modifica `box.cfg` con la stampante ferma.
2. Riavvia **Klipper** (non un riavvio del firmware durante una stampa).
3. La console stampa `applied N value(s)`. Ogni opzione rifiutata viene elencata con il motivo.
4. Controlla con `BOX_CFS_CONFIG_DIAG ALL=1`: ogni valore configurato deve corrispondere alla rilettura del CFS.

Cambia **un parametro alla volta** e osserva qualche caricamento, scaricamento e lettura RFID prima del successivo.

## Regole imposte da Kalico

| Regola | Perché |
| --- | --- |
| Identità esatta `K2OH` / `v323-cfg6` / `0xE3`, API 2, 28 ID | Stock, CFG4, CFG5T e OpenCFS non ricevono mai scritture CFG6 |
| Scritture solo all'avvio di Klipper, stampante ferma | [Issue #9](https://github.com/MzTechnology97/k2-cfs-rfid-tools/issues/9): il CFS può dichiararsi IDLE mentre sta ancora alimentando |
| Nessun comando console `SET`/`RESET`/`APPLY` | I valori arrivano solo da `box.cfg` |
| Ogni SET seguito da un GET | Una discrepanza viene segnalata, mai tenuta in silenzio |
| Valori solo nella RAM del CFS | Spegnendo il CFS tornano i valori stock fino al successivo avvio di Klipper |

## Comandi

| Comando | Uso |
| --- | --- |
| `BOX_CFS_CONFIG_INFO [ADDRESS=1-4]` | Identità del firmware (`0x7A`), esito dell'applicazione all'avvio, tutti i valori per gruppo |
| `BOX_CFS_CONFIG_DIAG [ALL=1]` | GET in sola lettura con valore previsto, intervallo e `OK`/`INVALID`; senza `ALL=1` solo gli ID 0, 6, 7, 8, 11, 20, 27 |
| `BOX_CFS_CONFIG_SNAPSHOT` | Istantanea in sola lettura dello stato interno; solo su firmware `0xD7` (v3.22, CFG4) |

Vedi anche [Comandi G-code](../GCODE_COMMANDS.md) e [Debug](../reference/debug.md).
