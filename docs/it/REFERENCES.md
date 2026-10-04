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
- **Jacob10383/k2-plus-custom-firmware** — sorgente degli extra K2 Jacobean usati come baseline per CFS, motor control e altri componenti. L'implementazione Box corrente è anche il riferimento per la mappatura CFS tra tool logici e slot fisici e per il parsing dei metadata G-code Orca.
- **Jacob10383/fluidd** — fork Fluidd di Jacob e workflow Filament Box, usati come riferimento comportamentale/UI per la presentazione degli slot CFS e la mappatura filamenti prima della stampa.
- **Cartographer3D/cartographer3d-plugin** — il plugin Cartographer ufficiale usato da K2-OpenHost. Il precedente port K2 di Jacob10383 (adapter/reconnect/touch) è stato integrato a monte; anche il suo firmware usa il plugin ufficiale.
- **luketot/kalico-for-K2-Pro** — adattamento pubblico dei `.cfg` per K2 Pro usato come baseline di riferimento per geometria/pin; i valori macchina successivi vengono validati sulla K2 Pro reale del progetto.

## CFS / protocollo

- extra pubblici Creality K2/Hi, inclusi auto-address e material system;
- **gitstonelabs/creality-cfs-klipper** — reverse engineering CFS pubblico, soprattutto Hi/CFS-v1; riferimento, non prova automatica del comportamento K2 Pro;
- **grant0013/k2-reverse-engineering** e altri contributor pubblici;
- **HimAndRobot/creality-cfs-mainsail-integration** — riferimento visuale/interazione per card CFS, colori bobina e stati delle azioni in Mainsail/Fluidd. K2-OpenHost non usa il suo trasporto diretto tramite `web-server` Creality / porta `9999`: il frontend OpenHost consuma invece l'oggetto Klipper `box` nativo attraverso Moonraker.

## Probing, risonanza e UI

- **Cartographer3D/cartographer3d-plugin** e contributor Cartographer — plugin upstream e architettura probe/scan corrente;
- **Klippain / ShakeTune** e contributor — tooling per misure/analisi risonanza; un test reale OpenHost è stato completato con successo con questo stack;
- **mainsail-crew/mainsail** e contributor — UI web usata durante lo sviluppo OpenHost;
- **Moonraker / Arksine** e contributor — API/update-manager tra Kalico e Mainsail;
- **prestonbrown/helixscreen** — HelixScreen, candidato per la UI sul T113.

## Repository K2-OpenHost

- `MzTechnology97/K2-OpenHost` — documentazione e validazione canonica;
- `MzTechnology97/k2-pro-custom-firmware` — fork extra Jacobean e history patch K2 Pro/OpenHost (archiviato il 4 ottobre 2026);
- `MzTechnology97/k2-openhost-t113-bootstrap` — bootstrap dello slot B del T113;
- `MzTechnology97/kalico-k2pro` — fork Kalico con runtime K2 Pro ed extra validati;
- `MzTechnology97/cartographer3d-plugin-k2openhost` — vecchio fork Cartographer, dismesso il 4 ottobre 2026 a favore del plugin ufficiale;
- `MzTechnology97/k2-improvements` — fork di riferimento nella linea upstream k2-improvements;
- `MzTechnology97/mainsail-k2openhost` — fork Mainsail riservato ai lavori UI OpenHost mantenendo l'attribuzione upstream.
- `MzTechnology97/k2-openhost-firmware-tools` — strumenti in sola lettura per inventario, confronto e probing live dei firmware periferici K2 da OpenHost.

## Regola di attribuzione risultati

Ogni risultato deve essere distinguibile come:

- **verificato su hardware K2 Pro**;
- **derivato da sorgente/configurazione pubblica**;
- **dedotto / non ancora testato**.

La distinzione è essenziale perché K2 Plus, K2 Pro e altre varianti condividono molto codice ma possono differire in meccanica, pin mapping e comportamento protocollo.
