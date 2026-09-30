# Crediti e riferimenti

K2-OpenHost è un progetto di integrazione e validazione hardware. Mantiene volutamente visibile l'attribuzione upstream e non rivendica la paternità di codice, scoperte di protocollo o reverse engineering provenienti da altri progetti.

## Firmware principali

- **Klipper3d/klipper** — progetto Klipper originale e contributor.
- **KalicoCrew/kalico** — fork community Kalico e contributor.
- **Jacob10383/kalico** — lavoro Kalico di Jacob usato come base upstream per il fork K2.
- **CrealityOfficial/K2_Series_Klipper** — sorgenti pubblici Creality K2 e riferimenti alle estensioni proprietarie.

## Progetti/autori K2

- **jamincollins/k2-improvements** — origine della linea `k2-improvements`.
- **Jacob10383/k2-improvements** — fork/lavoro K2 di Jacob usato come riferimento pubblico.
- **Jacob10383/k2-plus-custom-firmware** — sorgente degli extra K2 Jacobean usati come baseline per CFS, motor control e altri componenti.
- **luketot/kalico-for-K2-Pro** — adattamento pubblico dei `.cfg` per K2 Pro usato come baseline di riferimento per geometria/pin; i valori macchina definitivi OpenHost verranno presi dalla K2 Pro reale già funzionante.

## CFS / protocollo

- extra pubblici Creality K2/Hi, inclusi auto-address e material system;
- **gitstonelabs/creality-cfs-klipper** — reverse engineering CFS pubblico, soprattutto Hi/CFS-v1; riferimento, non prova automatica del comportamento K2 Pro;
- **grant0013/k2-reverse-engineering** e altri contributor pubblici.

## UI e probing

- **Cartographer3D/cartographer3d-plugin** e contributor Cartographer;
- **prestonbrown/helixscreen** — HelixScreen, candidato per la UI sul T113.

## Repository K2-OpenHost

- `MzTechnology97/K2-OpenHost` — documentazione e validazione;
- `MzTechnology97/k2-pro-custom-firmware` — fork extra Jacobean e patch K2 Pro/OpenHost;
- `MzTechnology97/kalico-k2pro` — fork Kalico con baseline K2 Pro ed extra validati;
- `MzTechnology97/k2-improvements` — fork di riferimento nella linea upstream k2-improvements.

## Regola di attribuzione risultati

Ogni risultato deve essere distinguibile come:

- **verificato su hardware K2 Pro**;
- **derivato da sorgente/configurazione pubblica**;
- **dedotto / non ancora testato**.

La distinzione è essenziale perché K2 Plus, K2 Pro e altre varianti condividono molto codice ma possono differire in meccanica, pin mapping e comportamento protocollo.