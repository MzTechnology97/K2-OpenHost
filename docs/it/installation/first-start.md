# 3. Primo avvio e controlli

Esegui questi controlli nell'ordine, con la stampante sorvegliata, prima della prima stampa vera.

## 1. Doctor

```bash
~/k2-openhost-installer-helper/helper.sh doctor
```

Ogni riga dovrebbe essere verde. Le righe rosse `✘` dicono cosa non va e come correggerlo.

![Output del doctor](../../images/helper/cli-doctor.png)

Lo stesso controllo gira da solo dopo ogni avvio: nella console di Klipper compare `K2-OpenHost check after boot: OK.`. Vedi [Doctor e controllo di salute](../helper/doctor.md).

## 2. Mainsail

Apri `http://k2host.local/` (oppure `http://<ip>/`). La dashboard mostra lo stato della stampante, le temperature, il pannello **CFS** con il percorso del filamento e il pannello **Motori**. Nella console controlla:

```text
BOARD_STATUS        ; bridge della T113 attivi, alimentazione MCU accesa
SERIAL_STATUS       ; collegamento RS-485 ok
MOTOR_STATUS        ; motori X, Y, E pronti
BOX_DEBUG           ; CFS online
```

## 3. Movimento e homing

1. Libera il piatto. Tieni una mano vicino all'arresto di emergenza (**Emergency stop** di Mainsail, o l'interruttore).
2. `G28`. Con `[z_align]` il piatto scende prima fino al finecorsa in basso, poi X/Y fanno l'homing sensorless e Z l'homing con il nozzle (PRTouch).
3. Muovi ogni asse di qualche millimetro da Mainsail e controlla la direzione.

Se l'homing viene rifiutato perché una calibrazione dei motori è segnalata come sospetta: `MOTOR_STATUS`, poi `MOTOR_CALIBRATE AXIS=XY` (due chiamate: la prima ti chiede di centrare la testina e abbassare il piatto).

## 4. Riscaldatori

| Controllo | Comando |
| --- | --- |
| PID del piatto (100 °C) | `BEDPID` (salva e riavvia Klipper) |
| PID del nozzle (230 °C, ventola pezzo accesa) | `NOZZLE_PID` |
| PID del nozzle ad alta temperatura (280 °C) | `NOZZLE_PID_HIGH` |
| Camera | `M141 S45`, guarda la temperatura salire, poi `M141 S0` |

## 5. Taglierina del filamento

Il CFS taglia il filamento alla testina prima di ogni scaricamento. Trova la posizione della taglierina una volta:

```text
CALIBRATE_CUT_POS
```

Fa l'homing di X/Y se serve e salva `cut_pos_x`. Rieseguilo dopo aver cambiato la taglierina o la testina.

## 6. CFS

1. Inserisci una bobina: il CFS legge il suo tag RFID (tag Creality, o tag di terze parti con il firmware CFS API7). Bobine senza tag: imposta il filamento con il pulsante ✎ dello slot ([editor degli slot](../usage/cfs.md#spools-without-rfid)).
2. Carica uno slot dal pannello CFS (▶), poi scarica (**Unload**). Osserva il percorso del filamento.
3. Attiva **Runout swap** nel menu delle impostazioni CFS se hai bobine identiche.

## 7. Input shaper (opzionale)

Shake&Tune viene installato con l'installazione completa. Esegui il test di risonanza con il piatto libero; vedi la [documentazione di Klippain Shake&Tune](https://github.com/Frix-x/klippain-shaketune).

## 8. Slicer e prima stampa

1. Configura [OrcaSlicer](../ORCASLICER.md) con l'host Moonraker e il G-code di avvio `START_PRINT` ([Stampare](../usage/printing.md#slicer-start-and-end-g-code)).
2. Stampa un pezzo piccolo a un colore, sorvegliato.
3. Poi un pezzo a due colori, sempre sorvegliato.

La procedura completa di validazione, test per test, è il [piano di test hardware](../HARDWARE_TEST_PLAN.md).

!!! warning "Mai incustodita"
    Non lasciare mai la stampante incustodita mentre è comandata dall'host esterno. Tieni vicino un rilevatore di fumo e un estintore.
