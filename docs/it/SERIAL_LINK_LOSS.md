# Perdita di un collegamento seriale dietro il T113

Aggiornato: **4 ottobre 2026**. [English](../en/SERIAL_LINK_LOSS.md)

L'host esterno raggiunge i tre bus della K2 Pro attraverso porte seriali USB gadget, che il T113 collega alle sue UART. Se un bridge, il cavo USB o il T113 si guastano, cosa fa l'host? Klipper si ferma, o continua a stampare senza accorgersene? Queste prove rispondono. Sono state fatte sulla K2 Pro di sviluppo, in standby con i riscaldatori spenti, fermando un bridge del T113 alla volta.

## Cosa è stato misurato

| Perso | Comportamento dell'host | Valutazione |
| --- | --- | --- |
| Bridge della Nozzle MCU (ttyGS1 ↔ ttyS3) | shutdown dopo **5,2 s**: `Lost communication with MCU 'nozzle_mcu'` | Sicuro. Il protocollo MCU di Klipper se ne accorge. Le uscite dei riscaldatori hanno un `max_duration` di 3 s, quindi una MCU che non riceve più aggiornamenti dall'host spegne da sola i riscaldatori. |
| Bridge della Main MCU | stesso meccanismo, visto anche nei log | Sicuro, come sopra. |
| Bridge RS-485 (ttyGS2 ↔ ttyS5: CFS, schede dei motori X/Y) | **nessuna reazione**: Klipper è rimasto `ready`, `motor_ready` è rimasto true, nel log solo timeout delle richieste | **Non rilevato.** Una stampa andrebbe avanti con il CFS (alimentazione, fine filamento) e la diagnostica dei motori muti. |
| Cavo USB o T113 bloccato | i dispositivi seriali dell'host spariscono e i collegamenti con le MCU si perdono | Sicuro: shutdown come sopra. |

Osservato inoltre:
- **Dopo la perdita del collegamento la MCU può non essere in shutdown,** perché non ha mai ricevuto il comando. Il primo `FIRMWARE_RESTART` può allora fallire con `Failed automated reset of MCU`. Qui il secondo ha funzionato. Un ciclo di alimentazione della linea MCU resetta sempre le MCU in modo pulito.
- **I guasti dei motori fermano comunque la stampante durante un'interruzione RS-485.** I pin di stallo di X/Y/E sono collegati a Main e Nozzle MCU, non all'RS-485. Uno stallo la cui lettura delle protezioni fallisce viene trattato come guasto non verificato, e X/Y vanno in shutdown.
- **Il bus RS-485 riprende da solo** quando il bridge torna, senza riavvii.
- **Riavviare i tre bridge richiede meno di 5 s,** quindi Klipper resta connesso. È un primo rimedio utile per un bridge bloccato.

## Cosa fa K2-OpenHost

1. **Watchdog del collegamento RS-485** in kalico-k2pro (`[serial_485 serial485]`):
   - il collegamento è perso quando nessun dispositivo risponde per `link_lost_timeout` (10 s) con 3 timeout di fila; un solo dispositivo assente non conta;
   - durante la stampa `link_lost_action` mette in pausa (predefinito), avvisa o va in shutdown; a stampante ferma avvisa;
   - il ritorno del collegamento viene segnalato.
2. **Comandi di ripristino tramite il T113** (`k2oh-ctl` + `[k2_t113]`):
   - `USB_BRIDGES_RESTART CONFIRM=1`;
   - `MCU_POWER_CYCLE CONFIRM=1`, che funziona anche con Klipper in shutdown e poi riavvia il firmware;
   - il dispositivo Moonraker `K2_MCU_Power`, bloccato durante la stampa.
3. **Arresto hardware opzionale:** `estop_on_shutdown: m112` toglie l'alimentazione alle MCU con l'arresto di emergenza, così riscaldatori e motori restano senza corrente anche se una MCU ha smesso di rispondere.
4. **Recupero automatico opzionale:** `auto_power_cycle: True` esegue un ciclo di alimentazione delle MCU e riavvia dopo la perdita del collegamento con una MCU mentre nessuna stampa era in corso, al massimo una volta ogni 10 minuti.

Entrambe le opzioni sono spente di default.

## Crash dei bridge e riconnessioni USB

Un bridge caduto e riavviato da procd entro 1,5 s ha lasciato Klipper `ready`, anche durante il moto. Per riprendersi con `FIRMWARE_RESTART` dopo una riconnessione USB, l'host deve usare `serial: /dev/serial/by-id/...`. Vedi i test di guasto in [Bridge USB](USB_BRIDGE.md#test-di-guasto).

## Ancora da provare

- La pausa del watchdog durante una stampa vera. Nelle prove in standby Klipper non stampa, quindi è stato eseguito solo il ramo dell'avviso.
- Le stesse prove con lo slot B al posto dei bridge avviati a mano sullo slot A.
