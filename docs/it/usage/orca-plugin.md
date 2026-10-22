# Plugin per OrcaSlicer 2.5

OrcaSlicer 2.5 (alpha dal 16 ottobre 2026) carica plugin Python. Il plugin **K2-OpenHost CFS** porta il CFS dentro OrcaSlicer: Sync con il preset esatto, un pannello CFS per scegliere lo slot di ogni filamento, e l'ordine di runout.

!!! warning "Sperimentale"
    OrcaSlicer 2.5 e la sua API dei plugin sono in alpha. Il plugin è provato con il Moonraker della stampante di riferimento e dentro OrcaSlicer (Sync, pannello), ma una stampa avviata con la sua mappa degli slot non è ancora validata. Sorgente: [`tools/orcaslicer/k2_openhost_cfs.py`](https://github.com/MzTechnology97/K2-OpenHost/tree/main/tools/orcaslicer).

## Cosa fa

| Parte | Tipo | Cosa fa |
| --- | --- | --- |
| **K2-OpenHost CFS** | Printer agent | Pubblica ogni slot del CFS a OrcaSlicer con l'`orca_filament_id` che Kalico tiene per ogni filamento, così **Sync** seleziona quel preset (Bambu PLA Basic, non Generic PLA). Serve anche la scheda Device. |
| **K2-OpenHost CFS slots** | Script (pannello) | Un pannello accanto alla vista 3D che disegna ogni CFS con le sue bobine; clicca un filamento, poi una bobina, per scegliere da dove stampa. Anche l'ordine di runout. Si apre da solo dopo ogni slicing. |
| **K2-OpenHost CFS G-code map** | Slicing pipeline | Scrive la scelta del pannello dopo la prima riga del G-code, es. `; K2OH_TOOL_MAP = 0:1,2:0`. Kalico la usa all'avvio della stampa, al posto del suo abbinamento automatico. |

![Plugin in OrcaSlicer](../../images/orca/plugin-manager.webp)

## Installazione

1. Scarica [`k2_openhost_cfs.py`](https://github.com/MzTechnology97/K2-OpenHost/tree/main/tools/orcaslicer).
2. OrcaSlicer → **Plugins** → **Install local plugin** → scegli il file. OrcaSlicer lo copia in `%APPDATA%\OrcaSlicer\orca_plugins\`.
3. Preset stampante → **Printer settings → Basic information → Advanced → Printer Agent**: **K2-OpenHost CFS**.
4. **Print host**: l'indirizzo di Moonraker **con la porta**, per esempio `10.10.1.97:7125`.
   - **Device UI** (modalità avanzata): `http://10.10.1.97`, l'indirizzo semplice. La scheda Dispositivo apre questo campo quando è compilato, così continua a mostrare Mainsail mentre l'host di stampa ha la porta.
   - Salva il preset.
5. OrcaSlicer chiede il permesso perché il plugin crei un thread e si colleghi a quell'indirizzo: consenti entrambi. Il primo collegamento viene rifiutato mentre la domanda è aperta; il plugin riprova ogni 2 s.
6. **Preset di processo** → passa alla modalità **Avanzata** → **Altro** → **Slicing Pipeline Plugin**: aggiungi **K2-OpenHost CFS G-code map** e salva. Fallo in ogni preset di processo che usi con la K2.

!!! important "Senza il passo 6 la mappa non viene scritta"
    OrcaSlicer esegue una funzione slicing-pipeline sul G-code esportato solo se il preset di processo la elenca: installare e attivare il plugin non basta. Pannello e Sync funzionano comunque, e questo nasconde il problema. Finché il passo non è elencato, il pannello CFS mostra un avviso e nel log del plugin non compare nessuna riga `G-code map`.

!!! important "Usa l'indirizzo con la porta"
    OrcaSlicer lega ogni stampante salvata all'agent con cui è stata aggiunta. Una stampante salvata con l'indirizzo semplice (`10.10.1.97`) resta legata all'agent Moonraker integrato, e scegliendo il plugin non trova nessuna stampante ("target machine was not found"). L'indirizzo con la porta è una stampante nuova per OrcaSlicer, legata al plugin.

!!! warning "Lascia spento *Use printer agents instead of print hosts*"
    *Preferences → Developer → Use printer agents instead of print hosts* è un'opzione **globale** di OrcaSlicer 2.5-alpha: cambia il flusso di stampa e la scheda Device di **tutte** le stampanti non Bambu, e può guastare altre stampanti. Al plugin non serve: tieni il classico **Upload and print**.

## Sync

Premi **Sync** nell'elenco dei filamenti. Ogni slot del CFS arriva con l'ID del suo preset.

![Finestra Sync](../../images/orca/sync-dialog.png){ width="560" }

!!! info "Perché il tuo preset personalizzato non viene scelto"
    Il sync di OrcaSlicer abbina solo i **preset radice**: i preset di sistema, e i tuoi preset creati con **Create filament** (hanno un loro ID `P…`). Un preset salvato da un altro (mostra un genitore in *Dependencies*) non viene mai scelto, da nessun agent: OrcaSlicer prende il genitore. Per sincronizzare il tuo preset personalizzato, crealo con **Create filament**, copia dentro le tue impostazioni e dai il suo ID `P…` al filamento CFS in Mainsail (libreria filamenti → **OrcaSlicer preset…**). Il pannello degli slot qui sotto non ha questo limite.

    Il plugin **Filament ID Fixer** (catalogo plugin di OrcaSlicer) lo fa per te: filtra `@K2`, seleziona i tuoi preset, **Apply**, riavvia OrcaSlicer. Ogni preset viene staccato dal genitore e riceve un ID proprio `U…` (prima viene fatto un backup zip). Dai quell'ID al filamento CFS in Mainsail (libreria filamenti → **OrcaSlicer preset…**, oppure `_BOX_FILAMENT_ORCA_ID ID=<filamento> ORCA_ID=<U…>`). Un preset staccato non segue più le modifiche fatte al genitore.

## Pannello CFS

Dopo ogni slicing per la K2 il pannello si apre accanto alla vista 3D (o ricompare se l'avevi chiuso). Mostra ogni CFS con le sue quattro bobine (colore, materiale, nome, residuo, temperatura e umidità) e sotto i filamenti del progetto.

![Pannello CFS](../../images/orca/cfs-panel.jpg){ width="360" }

1. Il plugin propone uno slot per ogni filamento: stesso materiale, poi il colore più vicino.
2. Per cambiarlo: clicca il filamento, poi la bobina. La ✕ lascia quel filamento a Kalico.
3. **Upload and print**. Il plugin scrive la mappa nel G-code al momento del caricamento (o dell'esportazione), quindi va bene scegliere gli slot dopo lo slicing; Kalico la applica all'avvio della stampa. Nel log del plugin compare `G-code map (OctoPrint): wrote ; K2OH_TOOL_MAP = …`.

La mappa viene scritta solo per il preset stampante e l'elenco filamenti per cui è stata scelta, e solo quando **ogni filamento usato dal piatto** ha uno slot. Altrimenti non viene scritto nulla e Kalico abbina la stampa automaticamente. Kalico ignora anche, con un messaggio in console, una mappa con uno slot vuoto o non in linea.

**Refresh** ricarica filamenti e slot; **Propose** ricomincia da capo. Impostando `auto_open: false` (configurazione della capability) il pannello non si apre più dopo lo slicing; puoi sempre aprirlo dal gestore dei plugin (**K2-OpenHost CFS slots** ▶).

## Ordine di runout { #runout-order }

Sotto i filamenti, il pannello ha una sezione **Runout order**:

- l'interruttore **Switch to an identical spool when one runs out** (`_BOX_SET_RUNOUT_SWAP`);
- ogni gruppo di bobine identiche nell'ordine in cui Kalico le userà, con ▲▼ e **Automatic order**.

Le modifiche vengono salvate sulla stampante con `_BOX_SET_RUNOUT_ORDER`, come fa Mainsail, e valgono dal runout successivo.

## Impostazioni

| Capability | Impostazione | Predefinito | Significato |
| --- | --- | --- | --- |
| K2-OpenHost CFS | `poll_interval_s` | 2 | Aggiornamento dello stato |
| K2-OpenHost CFS | `model_id` | modello del preset con `_` (`Creality_K2_Pro`) | Modello di stampante inviato a OrcaSlicer |
| K2-OpenHost CFS | `use_slot_map` | true | Con l'opzione globale degli agent attiva: invia la mappa della finestra di stampa |
| K2-OpenHost CFS slots | `auto_open` | true | Apre il pannello dopo lo slicing |

Log: `k2oh_cfs.log` nella cartella del plugin, `%APPDATA%\OrcaSlicer\orca_plugins\k2_openhost_cfs.py\`.

## Requisiti sulla stampante

- Kalico con `orca_filament_id` per filamento (dal 9 ottobre 2026) per il Sync.
- Kalico con la mappa dello slicer in `box_print_mapping` (kalico-k2pro #87, 21 ottobre 2026) per la mappa del pannello.

Verificato sulla stampante di riferimento il 22 ottobre 2026: il file caricato inizia con `; K2OH_TOOL_MAP = 0:0` e Kalico lo legge come tool 0 → slot 0 (CFS1·1).
