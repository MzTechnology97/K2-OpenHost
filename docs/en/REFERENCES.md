# Credits and references

K2-OpenHost is an integration and hardware-validation project. It intentionally preserves upstream authorship and does not claim original ownership of code, protocol discoveries or reverse-engineering results that originate elsewhere.

## Core firmware projects

- **Klipper3d/klipper** — original Klipper firmware project and contributors.
- **KalicoCrew/kalico** — community Kalico fork and contributors.
- **Jacob10383/kalico** — Jacob's Kalico work used as the upstream base for the K2-oriented fork.
- **CrealityOfficial/K2_Series_Klipper** — public Creality K2 Klipper sources and proprietary-extension references.

## K2 projects and authors

- **jamincollins/k2-improvements** — original `k2-improvements` project lineage.
- **Jacob10383/k2-improvements** — Jacob's fork and K2 work used by the project as a public reference.
- **Jacob10383/k2-plus-custom-firmware** — source of the Jacobean K2 custom-firmware extras used as the implementation baseline for CFS, motor control and other K2 features. Its current Box implementation is also the source/reference for logical-tool CFS print mapping and Orca G-code metadata parsing.
- **Jacob10383/fluidd** — Jacob's Fluidd fork and Filament Box workflow, used as the behavioral/UI reference for CFS slot presentation and the pre-print filament-mapping flow.
- **Cartographer3D/cartographer3d-plugin** — the official Cartographer plugin used by K2-OpenHost. Jacob10383's earlier K2 port (adapter/reconnect/touch work) has been merged upstream; his firmware also uses the official plugin.
- **luketot/kalico-for-K2-Pro** — public K2 Pro `.cfg` adaptation used as a baseline reference for geometry/pin/config differences. Later machine values are validated against the real K2 Pro used by the project.

## CFS / protocol references

- Creality public K2/Hi Klipper extras, including auto-addressing and material-system wrappers.
- **gitstonelabs/creality-cfs-klipper** — public CFS reverse-engineering work, mainly Hi/CFS-v1 oriented; used as a reference, not assumed to prove all K2 Pro behavior.
- **grant0013/k2-reverse-engineering** and other public K2 reverse-engineering contributions.
- **HimAndRobot/creality-cfs-mainsail-integration** — visual/interaction reference for CFS slot cards, spool colors and action-state presentation in Mainsail/Fluidd. K2-OpenHost does not use its direct Creality `web-server` / port `9999` transport; the OpenHost frontend consumes the native Klipper `box` object through Moonraker instead.

## Probing, resonance and UI

- **Cartographer3D/cartographer3d-plugin** and Cartographer project contributors — upstream Cartographer plugin and current probe/scan architecture.
- **Klippain / ShakeTune** project and contributors — resonance-measurement/analysis tooling; a real OpenHost resonance test was completed successfully with this tooling.
- **mainsail-crew/mainsail** and contributors — web UI used during OpenHost development.
- **Moonraker / Arksine** and contributors — API/update-manager layer between Kalico and Mainsail.
- **prestonbrown/helixscreen** — HelixScreen UI project considered for the T113 display side.

## K2-OpenHost repositories

- `MzTechnology97/K2-OpenHost` — canonical documentation and validation.
- `MzTechnology97/k2-pro-custom-firmware` — forked Jacobean extras and K2 Pro/OpenHost patch history (archived 2026-10-04).
- `MzTechnology97/k2-openhost-t113-bootstrap` — T113 slot B bootstrap.
- `MzTechnology97/kalico-k2pro` — Kalico fork integrating the K2 Pro runtime and validated extras.
- `MzTechnology97/cartographer3d-plugin-k2openhost` — former Cartographer fork, retired on 2026-10-04 in favour of the official plugin.
- `MzTechnology97/k2-improvements` — preserved/reference fork in the upstream K2-improvements lineage.
- `MzTechnology97/mainsail-k2openhost` — Mainsail fork reserved for K2-OpenHost UI work while retaining upstream authorship.
- `MzTechnology97/k2-openhost-firmware-tools` — read-only peripheral firmware inventory, comparison and live probing tools for K2-OpenHost.

## Attribution rule

A result should be labelled as one of:

- **verified on K2 Pro hardware**;
- **derived from public source/configuration**;
- **inferred / not yet tested**.

This distinction is important because K2 Plus, K2 Pro and other Creality K2 variants can share substantial code while still differing in mechanics, pin mapping and protocol behavior.
