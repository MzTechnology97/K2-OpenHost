# Mainsail

K2-OpenHost usa **[Mainsail K2-OpenHost](https://github.com/MzTechnology97/mainsail-k2openhost)**, un fork di Mainsail che aggiunge due pannelli e un passaggio all'avvio della stampa per la K2. Il resto è Mainsail upstream. Aprilo su `http://k2host.local/` (o l'IP dell'host).

## Dashboard

| Pannello | Cos'è |
| --- | --- |
| **Status** | Mainsail upstream: avanzamento, file, velocità, layer, tempo stimato |
| **CFS** | Il CFS: percorso del filamento, riquadri degli slot, gruppi di runout, impostazioni ([sotto](#cfs-panel)) |
| **Motori** | Motori closed-loop X, Y ed E: prontezza, calibrazione, protezioni, temperature |
| **Temperature** | Piatto, estrusore, riscaldatore della camera, ventole di estrazione della camera, `cm5_fan` (ventola della CPU dell'host), temperature di MCU e motori |
| **Toolhead, Console, Macro, Webcam** | Mainsail upstream |

I pannelli si possono mostrare, nascondere e spostare in *Settings → Dashboard*.

## Pannello CFS { #cfs-panel }

![Pannello CFS](../../images/mainsail/cfs-panel-desktop.png){ width="480" }

Dall'alto in basso:

- **Indicatori di stato**: stato e modalità del box, lo slot caricato nella testina, rilevamento intasamenti/grovigli.
- **Avviso di recupero** quando un'operazione del CFS ha bloccato la stampa; `RESUME` riprova il passo.
- **Percorso del filamento** dal CFS al nozzle: slot → encoder → buffer → testina, con il tubo PTFE riempito del colore della bobina fin dove arrivano i sensori. Durante un caricamento o scaricamento un banner mostra il passo e la fase lampeggia.
- **Una sezione per ogni unità CFS** con temperatura e umidità, poi la **bobina esterna**.
- I gruppi di **runout swap**.

Pulsanti nell'intestazione: libreria filamenti, scansione RFID di tutti gli slot occupati, scaricamento, menu impostazioni. Le azioni manuali sono disattivate durante la stampa.

| A riposo | In caricamento |
| --- | --- |
| ![Percorso del filamento a riposo](../../images/mainsail/cfs-path-idle-wide.png) | ![Percorso del filamento in caricamento](../../images/mainsail/cfs-path-loading-wide.png) |

### Riquadri degli slot

![Parti di un'unità CFS](../../images/mainsail/cfs-tile-anatomy.png){ width="520" }

| Parte | Significato |
| --- | --- |
| Etichetta della fonte | `RFID`, `RFID ?` (tag sconosciuto), `Library`, `Spoolman` o `Manual` |
| Anello della bobina | Colore del filamento; per le bobine RFID il settore colorato è il filamento rimasto, con la percentuale al centro |
| ▶ Carica | Carica questo slot fisico nella testina (`BOX_SELECT_SLOT`) |
| ✎ Modifica | Editor dello slot per bobine senza RFID |
| ⟳ Rileggi | Rilegge il tag RFID di questo slot |
| RFID | Scheda in sola lettura con i dati del tag |

![Stati dei riquadri](../../images/mainsail/cfs-slot-states.png)

### Menu impostazioni

![Menu impostazioni del CFS](../../images/mainsail/cfs-settings-menu.png){ width="300" }

| Interruttore | Comando |
| --- | --- |
| Runout swap | `_BOX_SET_RUNOUT_SWAP` |
| Scarica a fine stampa | `_BOX_SET_UNLOAD_AFTER_PRINT` |
| Leggi RFID all'inserimento | `_BOX_SET_RFID_INSERT_READING` |
| Leggi RFID all'avvio | `_BOX_SET_RFID_STARTUP_READING` (spento per impostazione predefinita) |
| Rilevamento intasamenti | `_BOX_SET_CLOG_DETECTION` |

Tutte le impostazioni sono salvate sulla stampante e restano dopo i riavvii.

### Più unità CFS e telefoni

Il pannello segue la propria larghezza: quattro riquadri per riga su un pannello largo, riquadri compatti in una colonna stretta, una colonna sul telefono. Con più unità CFS ognuna ha la sua sezione.

| Telefono | Più CFS (simulato) |
| --- | --- |
| ![Layout su telefono](../../images/mainsail/cfs-panel-phone.png){ width="280" } | ![Più CFS](../../images/mainsail/cfs-panel-multi.png) |

La guida completa di ogni funzione del CFS è in [Usare il CFS](cfs.md) e nella [documentazione del fork di Mainsail](https://github.com/MzTechnology97/mainsail-k2openhost/blob/develop/docs/K2_CFS.md).

## Finestra di stampa con abbinamento CFS { #print-dialog-with-cfs-mapping }

Quando avvii una stampa da Mainsail, la normale finestra **Print** legge i metadati OrcaSlicer del file (`BOX_PRINT_INFO`) e mostra una riga per ogni tool dello slicer con lo slot CFS che lo alimenterà.

| Abbinamento | Fonte del filamento |
| --- | --- |
| ![Finestra di stampa](../../images/mainsail/cfs-print-dialog.png) | ![Fonte del filamento](../../images/mainsail/cfs-print-source.png) |

- **Auto map** usa l'abbinamento del backend: decidono materiale e colore; tra bobine uguali vince quella con filamento sufficiente, poi quella con il residuo più basso.
- **Filament source** cambia a mano qualsiasi tool.
- **Print** avvia il lavoro con `BOX_PRINT_START FILENAME=... MAP=tool:slot,...`.
- Gli avvisi (potrebbe finire, variante di materiale, CFS umido) non bloccano mai la stampa.

![Avviso filamento scarso](../../images/mainsail/cfs-print-warning-low.png){ width="420" }

## Pannello Motori

![Pannello Motori](../../images/mainsail/motors-healthy-desktop.png)

Diagnostica in sola lettura dei motori closed-loop X, Y ed E pubblicata da Kalico: avvio e prontezza, calibrazione, stato delle protezioni ed eventi recenti, temperature delle MCU dei motori, contatori RS-485. I comandi da console corrispondenti sono in [Comandi G-code](../GCODE_COMMANDS.md#7-motori-closed-loop-stato-e-manutenzione).

## Update manager

*Machine* → **Update Manager** aggiorna Kalico (`kalico-k2pro`), Moonraker, Mainsail K2-OpenHost, il plugin Cartographer e l'helper. Vedi [Aggiornamenti](../installation/updates.md).

## Suggerimenti utili per Mainsail

- **Console**: ogni messaggio di K2-OpenHost inizia con un prefisso come `[BOX]:`, `[k2_t113]` o `serial_485`; gli avvisi iniziano con `!!`.
- **Machine → files**: `cfs_filaments.json` (la tua libreria filamenti) e i file `.cfg` si modificano da lì; `filament_box.json` è fuori dalla cartella di configurazione di proposito.
- **Emergency stop**: con `estop_on_shutdown: m112` in `[k2_t113]` toglie anche l'alimentazione alle MCU.
