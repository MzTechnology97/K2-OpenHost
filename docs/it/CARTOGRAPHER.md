# Cartographer3D su K2-OpenHost

Aggiornato: **4 ottobre 2026**. [English](../en/CARTOGRAPHER.md)

K2-OpenHost usa il [plugin Cartographer3D](https://github.com/Cartographer3D/cartographer3d-plugin) **ufficiale**, lo stesso del firmware K2 di Jacob10383. Il plugin ufficiale supporta direttamente Kalico e la K2: riconoscimento dell'ambiente Kalico e relativi adattatori, riconnessione dell'MCU "non critical", ultima API di homing di Kalico e `register_as_probe`.

Il vecchio fork `cartographer3d-plugin-k2openhost` (base ufficiale di marzo 2026 più il precedente port K2 di Jacob, pensato per k2-improvements) è stato dismesso e archiviato (sola lettura) il 4 ottobre 2026.

> Cartographer in USB diretta **non è ancora validato su hardware** con K2-OpenHost (test T5 del [piano dei test hardware](HARDWARE_TEST_PLAN.md)). La sonda validata è il **PRTouch** originale. Leggi prima l'[esclusione di responsabilità](DISCLAIMER.md).

## Topologia

I tre canali USB gadget del T113 restano dedicati ai bus della K2. Cartographer si collega **direttamente a una porta USB dell'host esterno**:

```text
T113 ttyS2 -> ttyGS0 -> host /dev/ttyUSB0  (Main MCU)
T113 ttyS3 -> ttyGS1 -> host /dev/ttyUSB1  (Nozzle MCU)
T113 ttyS5 -> ttyGS2 -> host /dev/ttyUSB2  (RS-485 / CFS / closed loop)
Cartographer USB ----------------------> host USB  (/dev/k2-cartographer)
```

Cartographer è un MCU Klipper che trasmette di continuo e si ri-enumera quando si resetta. Un esperimento precedente lo faceva passare dal T113 con un multiplexer PTY sul terzo canale gadget: i dati arrivavano, ma i reset e un bridge GS2 duplicato lo rendevano fragile. La USB diretta evita quello strato e lascia GS2 solo all'RS-485.

## Installazione

- **K2-OpenHost Installer Helper:** menu **8) Cartographer3D**, oppure `./helper.sh install cartographer`. Esegue lo script ufficiale (pacchetto pip in `~/klippy-env` e un loader di una riga in `~/klipper/klippy/plugins/cartographer.py`, ignorato da Git), aggiunge l'aggiornamento in Moonraker e migra un host che ha ancora il vecchio fork.
- **A mano:** clona il repository ufficiale e lancia `scripts/install.sh -k ~/klipper -e ~/klippy-env`.

Moonraker lo aggiorna come pacchetto Python:

```ini
[update_manager cartographer]
type: python
channel: stable
virtualenv: ~/klippy-env
project_name: cartographer3d-plugin
is_system_service: False
managed_services: klipper
info_tags:
    desc=Cartographer3D Plugin
```

`./helper.sh doctor` verifica che sia installato il plugin ufficiale e che esista un solo loader (Kalico non parte se il loader è sia in `klippy/extras` sia in `klippy/plugins`).

## Configurazione

Il profilo K2 Pro contiene `cartographer.cfg`, non incluso di default. La regola udev dell'installer chiama il dispositivo `/dev/k2-cartographer`; va bene anche `/dev/serial/by-id/...`. Non copiare mai l'identificativo seriale di un'altra stampante.

```ini
[mcu cartographer]
serial: /dev/k2-cartographer
restart_method: command
is_non_critical: True
reconnect_interval: 2.0

[cartographer]
mcu: cartographer
x_offset: 0
y_offset: -15            # da misurare sulla tua stampante
register_as_probe: true  # oppure false per il mixed mode, vedi sotto
```

Abilitalo con `[include cartographer.cfg]` in `printer.cfg` solo per la sessione di validazione.

## Ruoli della sonda

| `register_as_probe` | Cartographer | PRTouch |
| --- | --- | --- |
| `true` | gestisce `probe`, `probe:z_virtual_endstop`, `PROBE`, `PROBE_ACCURACY`, `QUERY_PROBE`, `Z_OFFSET_APPLY_PROBE` | non deve registrare un oggetto `probe` |
| `false` (mixed mode) | mantiene i suoi comandi e la mesh; il suo endstop è `cartographer_probe:z_virtual_endstop` | mantiene `probe` e `probe:z_virtual_endstop` per l'homing Z e il riferimento dell'ugello |

In mixed mode `[stepper_z]` resta sull'endstop del PRTouch; non puntarlo a `cartographer_probe:z_virtual_endstop` a meno di voler fare l'homing Z con Cartographer. Un flusso tipico: homing X/Y, Z con il PRTouch, spostamento all'altezza di scansione, mesh con Cartographer. Modifica le macro di avvio stampa solo dopo aver validato le due sonde separatamente.

## Sequenza di validazione (T5)

1. Conserva la configurazione validata solo PRTouch come base di ripristino.
2. Verifica che `/dev/ttyUSB0..2` restino stabili, poi collega Cartographer all'host.
3. Controlla il dispositivo (`lsusb`, `ls -l /dev/k2-cartographer /dev/serial/by-id/`).
4. Includi `cartographer.cfg`, riavvia Klipper e verifica che Cartographer si identifichi senza cicli di riconnessione:

   ```bash
   grep -Ei 'cartographer|identify_response|Timeout on connect|Unable to connect' ~/printer_data/logs/klippy.log | tail -50
   ```

5. Controlli senza movimento: `CARTOGRAPHER_QUERY` (e `QUERY_PROBE` quando gestisce la sonda).
6. Verifica che le letture cambino con la distanza.
7. Prova un riavvio automatico e la riconnessione.
8. Solo allora operazioni controllate di probe, touch e scan; il mixed mode per ultimo.
