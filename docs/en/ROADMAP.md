# K2-OpenHost roadmap

Updated: 2026-10-31.

## Done

- Kalico, Moonraker and Mainsail on the external host, with the K2 Pro's three buses carried over the T113's USB gadget.
- Motion, closed-loop motors, PRTouch, heaters, resonance tests and the stock buzzer from the host.
- The CFS in full operation: RFID (Creality, Bambu and other MIFARE tags), filament library, remaining filament, automatic mapping, runout swap, external spool loading, notifications.
- Cartographer on direct USB in mixed mode with PRTouch.
- The T113 slot B system: boot without Creality's services, bridges, MCU firmware updates, a way back to slot A.
- HelixScreen on the printer screen through the K2-OpenHost fork, with its own interface for the CFS and the print.
- The helper script, the release manifest and the docs site.
- Daily production use on the reference printer since 2026-10-21.

## Next

- **HelixScreen 1.0.6-k2oh.8**: the filament list straight from Kalico, the CFS recovery card, Orca preset names; then the screen checks in the [test plan](HARDWARE_TEST_PLAN.md) (T6). The fork has its own [roadmap](https://github.com/MzTechnology97/helixscreen/blob/k2-openhost/docs/k2-openhost/ROADMAP.md) (Italian).
- **The remaining print tests**: a two-colour print, a pause with a slot change, power-loss recovery on a printer without a UPS, the Cartographer as the only probe.
- **CFS firmware**: R4 through a complete spool runout, then decide whether it replaces R3 as the reference.
- **A new slot B image and a full release**, so a fresh install gets the HelixScreen fork, `k2oh-setup helix-update` and the current programs without extra steps.
- **A second printer**: a complete install on a fresh host, following only the docs.

## Not planned

- Reflashing Creality's Main or Nozzle MCU without a real need.
- Replacing working K2 electronics.
- Publishing private CFS identifiers or RFID data.
- Assuming the K2 Plus behaves like the K2 Pro.
