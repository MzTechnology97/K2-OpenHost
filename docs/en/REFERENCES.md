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
- **Jacob10383/k2-plus-custom-firmware** — source of the Jacobean K2 custom-firmware extras used as the implementation baseline for CFS, motor control and other K2 features.
- **luketot/kalico-for-K2-Pro** — public K2 Pro `.cfg` adaptation used as a baseline reference for geometry/pin/config differences; the final OpenHost machine configuration will instead use the proven settings from the actual test K2 Pro.

## CFS / protocol references

- Creality public K2/Hi Klipper extras, including auto-addressing and material-system wrappers.
- **gitstonelabs/creality-cfs-klipper** — public CFS reverse-engineering work, mainly Hi/CFS-v1 oriented; used as a reference, not assumed to prove all K2 Pro behavior.
- **grant0013/k2-reverse-engineering** and other public K2 reverse-engineering contributions.

## UI and probing

- **Cartographer3D/cartographer3d-plugin** and the Cartographer project contributors.
- **prestonbrown/helixscreen** — HelixScreen UI project considered for the T113 display side.

## K2-OpenHost repositories

- `MzTechnology97/K2-OpenHost` — documentation and validation.
- `MzTechnology97/k2-pro-custom-firmware` — forked Jacobean extras and K2 Pro/OpenHost patches.
- `MzTechnology97/kalico-k2pro` — Kalico fork integrating the K2 Pro baseline and validated extras.
- `MzTechnology97/k2-improvements` — preserved/reference fork in the upstream K2-improvements lineage.

## Attribution rule

A result should be labelled as one of:

- **verified on K2 Pro hardware**;
- **derived from public source/configuration**;
- **inferred / not yet tested**.

This distinction is important because K2 Plus, K2 Pro and other Creality K2 variants can share substantial code while still differing in mechanics, pin mapping and protocol behavior.