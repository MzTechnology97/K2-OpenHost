# Disclaimer and hardware limitations

Updated: **2026-10-03**. [Italiano](../it/DISCLAIMER.md)

## Disclaimer

K2-OpenHost and every repository published with it (kalico-k2pro, k2-pro-custom-firmware, mainsail-k2openhost, cartographer3d-plugin-k2openhost, k2-openhost-installer-helper, k2-openhost-firmware-tools and the related forks) are **experimental** tools shared with the community **for experienced users only**.

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
| **Nozzle camera** | Cannot be managed by the T113. | Rewire the original camera cable path and connect the camera **directly to a USB port of the external Linux host**; stream it from the host (for example with Crowsnest). |
| **Chamber camera** | Cannot be managed by the T113. | Same as the nozzle camera: rewire it and connect it **directly to the external host**. |
| **External USB port** of the printer (USB stick) | **Cannot be used to print** from a USB stick, and **stops working completely** while the T113 is in gadget mode. | Upload and print files through Mainsail/Moonraker on the external host. |
| **Cartographer3D** (optional) | Not carried through the T113 gadget channels. | Connect it directly to the external host (see [USB gadget transport](USB_GADGET.md)). |

Rewiring cables inside the printer is done at your own risk: disconnect mains power first, and route cables away from moving parts and heated areas.

These limits come from the USB0 role switch described in [USB gadget transport](USB_GADGET.md#role-switch-caveat). They are expected to remain in the final architecture.
