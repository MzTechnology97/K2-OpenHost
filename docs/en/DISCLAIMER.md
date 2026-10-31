# Disclaimer and hardware limitations

Updated: **2026-10-03**. [Italiano](../it/DISCLAIMER.md)

## Disclaimer

K2-OpenHost and every repository published with it (kalico-k2pro, k2-openhost-t113-bootstrap, mainsail-k2openhost, k2-openhost-installer-helper, k2-openhost-firmware-tools, the archived k2-pro-custom-firmware and the related forks) are **experimental** tools shared with the community **for experienced users only**.

By using them you accept that:

- **The manufacturer's warranty is void.** Running the printer from an external host, changing the T113 USB role and replacing the stock software are not supported by Creality.
- **The printer can be damaged beyond repair.** Wrong configuration values, motion or homing errors, or a lost connection can crash the toolhead or the bed, overheat parts or break mechanics and electronics.
- **The firmware can be bricked.** Changes to the T113 system or to peripheral firmware can leave the printer unable to start. Keep a known-good stock backup and a recovery method before any persistent change.
- **There is a risk of fire.** The heaters (nozzle, bed, chamber) are controlled by software running on the external host. A software, wiring, power or communication fault can leave a heater on. Never leave the printer unattended, keep working smoke detection near it, and keep a fire extinguisher at hand.
- **You use these tools entirely at your own risk.** They are provided "as is", without any warranty of any kind. **The authors and contributors accept no liability for any damage to property or persons**, injury, data loss or other consequence arising from their use, misuse or inability to use them.

If you are not comfortable diagnosing Linux, Klipper and 3D-printer electronics, or cannot accept these risks, do not use K2-OpenHost: keep the stock firmware.

The software licences of the individual repositories (GPL-3.0 and others) also exclude any warranty; this page adds the hardware and safety risks specific to this project.

## Hardware limitations in OpenHost mode

In K2-OpenHost the original T113 board stops being the printer's computer: its service USB port is switched to **USB gadget (device) mode** to carry the Main MCU, Nozzle MCU and RS-485/CFS channels to the external host. This changes the stock USB topology, with these consequences:

| Part | In OpenHost mode | What to do |
| --- | --- | --- |
| **Chamber camera** | Cannot be managed by the T113. | **Disconnect it from the T113** and rewire it **directly to a USB port of the external Linux host**; stream it from the host with Crowsnest (see [Chamber camera](CAMERA.md)). |
| **Nozzle camera** | **Cannot be used**: the T113 cannot run it in OpenHost mode. | None: the nozzle camera is not available in OpenHost mode. It works again when the printer boots the stock firmware (slot A). |
| **External USB port** of the printer (USB stick) | **Cannot be used to print** from a USB stick, and **stops working completely** while the T113 is in gadget mode. | Upload and print files through Mainsail/Moonraker on the external host. |
| **Cartographer3D** (optional) | Not carried through the T113 gadget channels. | Connect it directly to the external host (see [USB gadget transport](USB_GADGET.md)). |

Rewiring cables inside the printer is done at your own risk: disconnect mains power first, and route cables away from moving parts and heated areas.

These limits come from the USB0 role switch described in [USB gadget transport](USB_GADGET.md#role-switch-caveat). They are expected to remain in the final architecture.

## Operation

- **Mechanical damage.** Wrong configuration values, a homing or probing error, or a lost connection mid-move can crash the toolhead into the bed or the frame.
- **The USB cable is the printer's lifeline.** Unplugging or bumping the T113 cable, or a host reboot, stops the print at once: Klipper shuts down. Use a good data cable with a 90° plug and fix it in place.
- **The host's power is the printer's power.** If the host loses power, the print is lost even if the printer stays on. Use the host's official power supply; a UPS for both is a good idea.
- **No changes while printing.** Never restart Klipper, update, flash, edit the CFS runtime values or reboot the T113 during a print.
- **No Creality OTA from slot B.** An OTA in slot B would overwrite slot A, so it is disabled. From slot A an OTA replaces K2-OpenHost's slot B. Board firmware is updated from slot B with `k2oh-mcu-fw` (helper menu 31).
- **Supported model:** Creality K2 Pro only. The tools refuse other models and boards.
- **Experimental CFS firmware.** The [modified CFS firmware](cfs-firmware/index.md) is not production qualified: a bad image can stop the CFS until a recovery image is flashed, and an [open issue](https://github.com/MzTechnology97/k2-cfs-rfid-tools/issues/9) means the CFS can report idle while feeding. Flash only with the printer idle and keep the v3.22 recovery image. The stock CFS firmware works fine with K2-OpenHost.
- **Know your printer.** K2-OpenHost replaces the whole software stack, so you are your own support. Check the [test status](TEST_STATUS.md) before relying on a feature.
