# K2 Pro T113 service GPIOs

Status: **stock map statically verified; remote CM5 control not implemented yet**.

These signals belong to the original K2 Pro Allwinner T113. Linux GPIO numbers `140/162/164/165/209/210` are T113 numbering and **do not** map directly to Raspberry Pi CM5 GPIO numbers.

## Map verified from Creality stock firmware

| Linux GPIO | T113 pin | Stock name | Function | Active level |
|---:|---|---|---|---|
| 140 | PE12 | `MCU_PWR_EN` | MCU/peripheral power rail; used by `mcu_reset.sh` | **0 = ON**, 1 = OFF |
| 161 | PF1 | `USB_P_EN4` | reserved camera path, K1 Max branch | **0 = ON**, 1 = OFF |
| 162 | PF2 | `USB_P_EN3` | nozzle-camera power | **0 = ON**, 1 = OFF |
| 164 | PF4 | buzzer | motherboard buzzer | **1 = ON**, 0 = OFF |
| 165 | PF5 | `USB_HUB_RST` | USB hub reset | **1 = reset**, 0 = normal |
| 209 | PG17 | `USB_P_EN2` | CMS reserved, K1 Max branch | **0 = ON**, 1 = OFF |
| 210 | PG18 | `USB_P_EN1` | UDISK / USB-storage power | **0 = ON**, 1 = OFF |

The numbering follows the standard Allwinner 32-GPIO bank layout: `PE12 = 4*32+12 = 140`, `PF2 = 162`, `PF4 = 164`, `PF5 = 165`, `PG17 = 209`, `PG18 = 210`.

## Stock evidence

`/usr/bin/mcu_reset.sh` defines GPIO140 as active-low `MCU_PWR_EN` and performs the stock power cycle as `1 -> sleep 2 s -> 0`.

`/usr/bin/usb_host_5v.sh` defines GPIO165 as `USB_HUB_RST`, GPIO210 as UDISK power and GPIO162 as nozzle-camera power. GPIO209 and GPIO161 are reserved paths enabled only in the `CR-K1 Max` branch.

`/usr/bin/nozzle_cam_power.sh` confirms GPIO162 `0 = camera ON`, `1 = OFF`.

`/usr/bin/beep.sh` drives GPIO164 active-high. It contains an older commented PWM6 implementation (4 kHz, 50% duty), but stock K2 uses plain PF4 GPIO switching. The `audio-server` binary explicitly invokes `/usr/bin/beep.sh %f`.

`chamber_cam_power.sh` does not use one of these GPIOs; on F012/F021 its restart path uses the T113 USB-host controller kernel attribute.

## Relationship to the CM5

The CM5 exposes its own `/dev/gpiochip*` controllers, but no direct CM5 line named or proven to be wired to `MCU_PWR_EN`, `USB_P_EN3`, `BUZZER`, `USB_HUB_RST`, or `USB_P_EN1` was found.

```text
CM5
 |
 | USB gadget
 v
T113
 |-- GPIO140 -> MCU_PWR_EN
 |-- GPIO162 -> nozzle camera power
 |-- GPIO164 -> buzzer
 |-- GPIO165 -> USB hub reset
 `-- GPIO210 -> UDISK power
```

The CM5 therefore needs a **control plane running on the T113** to command these signals.

## USB gadget constraint

The three validated gadget channels remain dedicated to `ttyGS0` Main MCU, `ttyGS1` Nozzle MCU and `ttyGS2` RS-485/CFS/closed-loop.

A fourth `gser.usb3` was experimentally attempted but the gadget could not bind to the UDC, so it is not treated as an available transport. The old GS2 MUX/DEMUX experiment was abandoned as a production architecture. GPIO control must not reintroduce contention or framing into the three raw MCU streams.

## Proposed logical API

Remote control should use logical names rather than raw GPIO numbers:

```text
status
mcu-power on
mcu-power off
mcu-power cycle
nozzle-camera on
nozzle-camera off
buzzer <milliseconds>
usb-hub assert
usb-hub release
udisk-power on
udisk-power off
```

`mcu-power cycle` and `usb-hub assert` are disruptive and must require idle printer state, zero heater targets, compatible/stopped affected processes, explicit acknowledgement and post-operation verification.

For the firmware updater, `mcu-power cycle` is the key signal because it may allow Main/Nozzle/motors/CFS to be observed during their loader window immediately after hardware reset.


## Local T113 helper

`tools/t113-gpio-control.sh` has been added as a local endpoint, not as the remote transport. It supports `--dry-run` and requires `--confirm-disruptive` before removing MCU-rail power or asserting USB-hub reset.

The helper has been checked with `sh -n`, dry-run and a fake sysfs tree on the CM5. **It has not been installed or executed on the real T113 yet.** No automatic USB-hub reset pulse timing is invented: only `assert` and `release` are exposed because those levels are directly supported by stock evidence.

## Current state

- stock GPIO map: **verified**;
- GPIO164 buzzer: **verified**;
- polarities: **verified from stock scripts**;
- direct CM5 access to these nets: **not present / not proven**;
- CM5 -> T113 control plane: **pending**;
- no GPIO was toggled during this analysis.