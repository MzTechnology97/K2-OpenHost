# Hardware host

Aggiornato al **14 ottobre 2026**. [English](../en/HOST.md)

L'host esterno del K2 Pro di riferimento, e come Klipper comanda la sua ventola della CPU.

## Host di riferimento

| | |
|---|---|
| Modulo | Raspberry Pi **Compute Module 5** (revisione `d04180`): 8 GB di RAM, 32 GB di eMMC, Wi-Fi |
| Scheda base | Waveshare **[CM5-IO-BASE-A](https://www.waveshare.com/wiki/CM5-IO-BASE-A)** |
| Raffreddamento | Waveshare **CM5 Cooling Fan** `CM5-FAN-3007-B-5V`: dissipatore all-in-one dedicato in alluminio con ventola 30x07 mm 5 V PWM (8000 giri/min ±10 %), spina a 4 pin sul connettore ventola della scheda |
| Sistema | Raspberry Pi OS (Debian 12 bookworm), kernel `6.12.109+rpt-rpi-2712` |

| Scheda base: Waveshare CM5-IO-BASE-A | Dissipatore: Waveshare CM5-FAN-3007-B-5V |
| :---: | :---: |
| ![Scheda base Waveshare CM5-IO-BASE-A](../images/hardware/cm5-io-base-a.jpg){ width="340" } | ![Dissipatore Waveshare CM5-FAN-3007-B-5V](../images/hardware/cm5-fan-3007.jpg){ width="340" } |

Il 5 ottobre 2026 il CM5 era ancora montato su una Waveshare **CM4-IO-BASE-A**. Le porte USB di quella scheda erano tutte USB 2.0 dietro un unico hub su `dwc2`, e il suo connettore ventola era comandato via I2C da un controller EMC2301. La CM5-IO-BASE-A dà alla T113 un controller USB RP1 tutto suo e comanda la ventola dai pin del CM5.

## USB

Come risulta da `lsusb -t` il 14 ottobre 2026:

| Bus | Controller | Dispositivo |
|---|---|---|
| 2 | `xhci` 0 dell'RP1, USB 2.0 | gadget del T113 (`0525:a4a6`), da solo sul controller |
| 4 | `xhci` 1 dell'RP1, USB 2.0 | hub `1a86:8091` (QinHeng), poi hub `1a40:0101` (Terminus FE1.1S): Cartographer (`1d50:614e`) e la fotocamera della camera (1080p del K2 Plus, `1d6c:0103`) |
| 3, 5 | `xhci` 0 e 1 dell'RP1, USB 3.0 | nessuno |
| 1 | `dwc2` (`dtoverlay=dwc2,dr_mode=host`) | nessuno |

Il T113 ora ha un controller `xhci` dell'RP1 tutto per sé, che era lo scopo del cambio di scheda. `dwc2` non porta traffico: circa 8 100 interrupt al secondo su CPU0 con la CM4-IO-BASE-A, nessuno adesso. La fotocamera è descritta in [Fotocamera della camera](CAMERA.md).

## Ventola della CPU

**Come è collegata la ventola.** Sulla CM5-IO-BASE-A il connettore a 4 pin va ai pin `FAN_PWM` e `FAN_TACH` del CM5 stesso. Non c'è un controller ventola su I2C.
- Il kernel la comanda con il driver `pwm-fan` del Raspberry Pi 5, sul canale 3 del PWM dell'RP1 (`pwmchip0/pwm3`, invertito, ~24 kHz).
- I giri arrivano dal contatore del tachimetro dell'RP1.
- In sysfs è l'hwmon `pwmfan`: `pwm1` (0-255) e `fan1_input` (giri al minuto).

**Cosa fa il kernel di serie.** Segue le soglie della zona `cpu-thermal`:

| Temperatura CPU | PWM (su 255) |
|---|---|
| sotto 50 °C | 0 (spenta) |
| 50 °C | 75 |
| 60 °C | 125 |
| 67,5 °C | 175 |
| 75 °C | 250 |

La [wiki Waveshare](https://www.waveshare.com/wiki/CM5-IO-BASE-A) modifica questi gradini con `dtparam=fan_temp0..3` in `config.txt`. Sulla stampante di riferimento il CM5 a riposo sta a 54-56 °C, quindi la ventola gira al primo gradino: PWM 75, circa 2600 giri al minuto.

### Controllo da Klipper

Il [`[host_fan]`](https://github.com/MzTechnology97/kalico-k2pro/blob/k2-pro-openhost/docs/K2_PRO_OPENHOST.md#host-fan-cm5) di Kalico porta la ventola sotto il controllo di Klipper.

**Cosa fa:**
- **Presa del controllo:** mentre Klipper comanda la ventola, mette il `mode` della zona `cpu-thermal` a `disabled`, così il kernel smette di cambiarla. Poi scrive `pwm1` e legge i giri.
- **Controllo predefinito:** `min_speed` 30 % fino a `target_temp` 55 °C, poi sale in modo lineare fino a `max_speed` a 70 °C. Sopra 75 °C la ventola va al massimo in ogni modalità. Questi valori sono in `macros/host_fan.cfg`.
- **Mainsail:** la ventola compare come temperature fan `cm5_fan`, con temperatura, target, velocità e giri, e il target si imposta dal pannello delle temperature.
- **Restituzione al kernel:** la ventola torna al kernel quando Klipper si riavvia, si ferma o va in shutdown. Se il processo di Klipper va in crash, lo fa il drop-in di `klipper.service`.
- **Controllo di blocco:** mentre Klipper comanda la ventola, 10 s senza impulsi del tachimetro producono un avviso `!!` in console.
- **Throttling:** mentre la zona è disattivata, è disattivata anche la sua soglia critica a 110 °C. Il firmware continua a limitare la CPU a 85 °C, e la ventola è al massimo da 75 °C.

Verificato sulla stampante di riferimento il 15 ottobre 2026: modalità target, manuale e kernel, spunto alla partenza, e restituzione al kernel con un riavvio di Klipper e dopo un processo di Klipper terminato a forza (vedi [TEST_STATUS](TEST_STATUS.md)).

**Installazione:**
1. Aggiorna Kalico a una versione con `host_fan` (kalico-k2pro #74).
2. Esegui `./helper.sh install host-fan` (menu 36 dell'[installer helper](https://github.com/MzTechnology97/k2-openhost-installer-helper)). Installa:
   - una regola udev che dà al gruppo di Klipper la scrittura su `pwm1` e sul `mode` della zona;
   - il drop-in di `klipper.service`;
   - `macros/host_fan.cfg` con il suo include.
3. Riavvia Klipper a stampante ferma. Senza la regola udev, `[host_fan]` si limita a monitorare la ventola e spiega il motivo in console.

**Comandi:**

| G-code | Effetto |
|---|---|
| `SET_HOST_FAN TARGET=55` | la velocità segue la temperatura della CPU |
| `SET_HOST_FAN SPEED=0.6` | velocità fissa |
| `SET_HOST_FAN MODE=kernel` | il controllo automatico del kernel, fino al prossimo `SET_HOST_FAN` o riavvio di Klipper |
| `HOST_FAN_STATUS` | modalità, temperatura, velocità, giri |
