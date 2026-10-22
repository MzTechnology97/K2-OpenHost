# Host hardware

Updated: **2026-10-14**. [Italiano](../it/HOST.md)

The external host of the reference K2 Pro, and how its CPU fan is driven from Klipper.

## Reference host

| | |
|---|---|
| Module | Raspberry Pi **Compute Module 5** (revision `d04180`): 8 GB RAM, 32 GB eMMC, Wi-Fi |
| Carrier | Waveshare **[CM5-IO-BASE-A](https://www.waveshare.com/wiki/CM5-IO-BASE-A)** |
| Cooling | Waveshare **CM5 Cooling Fan** `CM5-FAN-3007-B-5V`: dedicated all-in-one cooler, aluminium heatsink with a 30x07 mm 5 V PWM fan (8000 RPM ±10 %), 4-pin plug on the carrier's fan header |
| System | Raspberry Pi OS (Debian 12 bookworm), kernel `6.12.109+rpt-rpi-2712` |

| Carrier: Waveshare CM5-IO-BASE-A | Cooler: Waveshare CM5-FAN-3007-B-5V |
| :---: | :---: |
| ![Waveshare CM5-IO-BASE-A carrier board](../images/hardware/cm5-io-base-a.jpg){ width="340" } | ![Waveshare CM5-FAN-3007-B-5V cooler](../images/hardware/cm5-fan-3007.jpg){ width="340" } |

On 2026-10-05 the CM5 still sat on a Waveshare **CM4-IO-BASE-A**. That board's USB ports were all USB 2.0 behind one hub on `dwc2`, and its fan header was driven over I2C by an EMC2301 controller. [USB bridge](USB_BRIDGE.md#the-cm5s-usb-30-ports-and-the-carrier-board) describes that setup and why the board was changed.

## USB

As seen with `lsusb -t` on 2026-10-14:

| Bus | Controller | Device |
|---|---|---|
| 2 | RP1 `xhci` 0, USB 2.0 | T113 gadget (`0525:a4a6`), alone on the controller |
| 4 | RP1 `xhci` 1, USB 2.0 | hub `1a86:8091` (QinHeng), then hub `1a40:0101` (Terminus FE1.1S): Cartographer (`1d50:614e`) and the chamber camera (K2 Plus 1080p, `1d6c:0103`) |
| 3, 5 | RP1 `xhci` 0 and 1, USB 3.0 | none |
| 1 | `dwc2` (`dtoverlay=dwc2,dr_mode=host`) | none |

The T113 now has an RP1 `xhci` controller to itself, which was the goal of the carrier change. `dwc2` carries no traffic: about 8 100 interrupts a second on CPU0 with the CM4-IO-BASE-A, none now. The camera is described in [Chamber camera](CAMERA.md).

## CPU fan

**How the fan is wired.** On the CM5-IO-BASE-A the 4-pin fan header goes to the CM5's own `FAN_PWM` and `FAN_TACH` pins. There is no I2C fan controller.
- The kernel drives the fan with the Raspberry Pi 5's `pwm-fan` driver, on RP1 PWM channel 3 (`pwmchip0/pwm3`, inverted, ~24 kHz).
- The RPM comes from the RP1's tachometer counter.
- In sysfs it is hwmon `pwmfan`: `pwm1` (0-255) and `fan1_input` (RPM).

**What the kernel does by default.** It follows the trip points of the `cpu-thermal` zone:

| CPU temperature | PWM (of 255) |
|---|---|
| below 50 °C | 0 (off) |
| 50 °C | 75 |
| 60 °C | 125 |
| 67.5 °C | 175 |
| 75 °C | 250 |

The [Waveshare wiki](https://www.waveshare.com/wiki/CM5-IO-BASE-A) changes these steps with `dtparam=fan_temp0..3` in `config.txt`. On the reference printer the CM5 idles at 54-56 °C, so the fan runs at the first step: PWM 75, about 2600 RPM.

### Control from Klipper

Kalico's [`[host_fan]`](https://github.com/MzTechnology97/kalico-k2pro/blob/k2-pro-openhost/docs/K2_PRO_OPENHOST.md#host-fan-cm5) moves the fan into Klipper.

**What it does:**
- **Taking over:** while Klipper drives the fan, it sets the `mode` of the `cpu-thermal` zone to `disabled`, so the kernel stops changing it. It then writes `pwm1` and reads the RPM.
- **Default control:** `min_speed` 30 % up to `target_temp` 55 °C, rising linearly to `max_speed` at 70 °C. Above 75 °C the fan runs at full speed in every mode. These values are in `macros/host_fan.cfg`.
- **Mainsail:** the fan appears as the temperature fan `cm5_fan`, with temperature, target, speed and RPM, and its target can be set from the temperature panel.
- **Hand-back:** the fan goes back to the kernel when Klipper restarts, stops or shuts down. If the Klipper process crashes, the `klipper.service` drop-in does the same.
- **Stall check:** while Klipper drives the fan, 10 s without tachometer pulses print a `!!` warning in the console.
- **Throttling:** while the zone is disabled, its 110 °C critical trip is disabled too. The firmware still throttles the CPU at 85 °C, and the fan is at full speed from 75 °C.

Verified on the reference printer on 2026-10-15: target, manual and kernel modes, kick start, and the hand-back on a Klipper restart and after a killed Klipper process (see [TEST_STATUS](TEST_STATUS.md)).

**Setup:**
1. Update Kalico to a version with `host_fan` (kalico-k2pro #74).
2. Run `./helper.sh install host-fan` (menu 36 of the [installer helper](https://github.com/MzTechnology97/k2-openhost-installer-helper)). It installs:
   - a udev rule that gives Klipper's group write access to `pwm1` and to the zone's `mode`;
   - the `klipper.service` drop-in;
   - `macros/host_fan.cfg` with its include.
3. Restart Klipper when the printer is idle. Without the udev rule, `[host_fan]` only monitors the fan and says why in the console.

**Commands:**

| G-code | Effect |
|---|---|
| `SET_HOST_FAN TARGET=55` | speed follows the CPU temperature |
| `SET_HOST_FAN SPEED=0.6` | fixed speed |
| `SET_HOST_FAN MODE=kernel` | the kernel's automatic control, until the next `SET_HOST_FAN` or Klipper restart |
| `HOST_FAN_STATUS` | mode, temperature, speed, RPM |
