# OrcaSlicer e il CFS

Aggiornato: **9 ottobre 2026**. [English](../en/ORCASLICER.md)

K2-OpenHost funziona con **OrcaSlicer ufficiale**: non serve una versione modificata. Due cose li collegano:

1. **Sincronizzazione dei filamenti** — la stampante pubblica gli slot del CFS nello spazio `lane_data` del database di Moonraker, la convenzione usata da AFC e Happy Hare. OrcaSlicer dalla 2.3.2 lo legge quando premi il pulsante **Sync** dei filamenti su una stampante Moonraker.
2. **Abbinamento automatico** — quando parte un G-code (da OrcaSlicer, Mainsail o API di Moonraker), il backend abbina ogni strumento dello slicer a uno slot del CFS per materiale e colore, con avvisi per le bobine che potrebbero finire. Vedi [Mappatura CFS delle stampe](CFS_PRINT_MAPPING.md) e la guida di Mainsail.

## Configurare la stampante in OrcaSlicer

1. Usa OrcaSlicer **2.4.0 o successivo** (tipo di host nativo "Moonraker (Klipper)"). Anche la 2.3.2 legge `lane_data`.
2. Seleziona o crea il profilo stampante K2 Pro, poi apri le impostazioni della **stampante fisica / connessione**.
3. **Tipo di host:** `Moonraker (Klipper)`. **Nome host, IP o URL:** l'host esterno, per esempio `k2host.local` o `192.168.1.50`.
4. Prova la connessione e salva.

**OrcaSlicer 2.4.2: la sincronizzazione non si collega.** Quella versione invia a Moonraker l'intestazione segnaposto `X-Api-Key: 88888888`, qualunque cosa scrivi nel campo della chiave API ([OrcaSlicer PR #15550](https://github.com/OrcaSlicer/OrcaSlicer/pull/15550), non ancora rilasciata). Moonraker accetta senza chiave un client fidato della rete locale, ma rifiuta una chiave sbagliata, quindi `moonraker.log` mostra:

```text
401 GET /server/database/item?namespace=lane_data (<il tuo PC>): Invalid API Key
```

Soluzione sulla stampante: far scartare a nginx solo quel segnaposto, così OrcaSlicer viene trattato come Mainsail e gli altri client fidati della rete locale; le chiavi vere passano invariate. Il [K2-OpenHost Installer Helper](https://github.com/MzTechnology97/k2-openhost-installer-helper) installa questa regola insieme a Mainsail (menu 7 per aggiungerla a un host esistente). A mano, crea `/etc/nginx/conf.d/k2openhost-orca-api-key.conf` con:

```nginx
map $http_x_api_key $k2oh_api_key {
    "88888888" "";
    default    $http_x_api_key;
}
```

poi aggiungi `proxy_set_header X-Api-Key $k2oh_api_key;` dopo le due righe `proxy_pass http://apiserver...` del sito Mainsail, controlla con `sudo nginx -t` e ricarica con `sudo systemctl reload nginx`. Verificato sulla macchina di riferimento con OrcaSlicer 2.4.2.

## Sincronizzare i filamenti

Premi **Sync** (il pulsante con le frecce in cima alla lista dei filamenti nella scheda Prepara). OrcaSlicer crea un filamento per ogni slot occupato del CFS, raggruppati a quattro come le unità CFS:

| CFS | OrcaSlicer |
| --- | --- |
| Box 1, slot 1 … slot 4 | filamenti 1–4 (strumenti T0–T3) |
| Box 2, slot 1 … slot 4 | filamenti 5–8 (strumenti T4–T7) |
| slot vuoto | segnaposto vuoto |

Ogni filamento sincronizzato prende **materiale** e **colore** dello slot. Fai lo slicing come sempre: T0 stampa dal Box 1 slot 1, T1 dallo slot 2 e così via, e all'avvio della stampa l'abbinamento automatico conferma la corrispondenza.

Rifai la sincronizzazione dopo aver cambiato bobine: la stampante aggiorna `lane_data` entro pochi secondi da ogni modifica di uno slot (lettura RFID, editor dello slot, Use in slot).

**HelixScreen** tiene i propri override degli slot nello stesso namespace `lane_data` e toglie una corsia quando ne azzera uno, per esempio dopo uno scambio di bobine. La stampante ripubblica lo slot alla sua modifica successiva, e una corsia già tolta da HelixScreen non è un errore. Se OrcaSlicer non vede uno slot subito dopo uno scambio, premi di nuovo **Sync** quando la nuova bobina è stata letta.

## Cosa viene pubblicato

Una voce per ogni slot occupato del CFS con un materiale (la bobina esterna non viene pubblicata):

```json
"lane2": {
  "lane": "1",
  "material": "PLA",
  "color": "#B1BEC6",
  "nozzle_temp": 215,
  "bed_temp": null,
  "spool_id": null,
  "name": "Bambulab PLA Basic",
  "vendor": "Bambulab",
  "filament_id": "05628",
  "orca_filament_id": "OFoiVqVM",
  "scan_time": ""
}
```

`lane` è il numero dello strumento (slot fisico, da 0). OrcaSlicer oggi legge `lane`, `material`, `color`, `nozzle_temp` e `bed_temp`. `filament_id` è l'ID del filamento CFS (libreria) e `orca_filament_id` l'ID del preset OrcaSlicer (sotto); con `name`, `vendor` e `spool_id` servono per l'abbinamento ai preset di marca, che OrcaSlicer non fa ancora per le stampanti Moonraker ([#13006](https://github.com/OrcaSlicer/OrcaSlicer/issues/13006)).

Puoi verificare cosa pubblica la stampante con la stessa richiesta che fa OrcaSlicer:

```bash
curl -s "http://k2host.local:7125/server/database/item?namespace=lane_data"
```

## Preset OrcaSlicer di ogni filamento

Ogni filamento della CFS ha il `filament_id` del suo preset OrcaSlicer, l'ID con cui OrcaSlicer abbina i preset. Non cambia mai l'ID, il nome, la marca o i codici RFID del filamento.

- **Predefinito** (Kalico, generato dai profili di OrcaSlicer): il preset K2 Pro di un filamento Creality o Generic del catalogo (`Hyper PLA` → "Hyper PLA @K2 Pro-all"), il prodotto della libreria filamenti di OrcaSlicer per un tag Bambu (`Bambulab PETG HF` → "Bambu PETG HF @System"), oppure un preset con lo stesso nome del profilo.
- **Scelto da te**: nella libreria filamenti di Mainsail, menu della scheda → **OrcaSlicer preset…** (anche per i profili di sistema), oppure la sezione OrcaSlicer del modulo di modifica; `_BOX_FILAMENT_ORCA_ID` dalla console.
- **Un tuo preset OrcaSlicer**: crealo da zero (Filamento → **+** → *Crea filamento*), poi copia `"filament_id"` (`P…`) da `%APPDATA%\OrcaSlicer\user\<account>\filament\base\<nome>.json`. Un preset salvato da un altro ("Salva come") non ha un ID suo: usa quello del genitore, e OrcaSlicer selezionerebbe il genitore.

OrcaSlicer 2.4.2 e l'agente Moonraker integrato della 2.5 non leggono l'ID: la loro sincronizzazione sceglie il preset generico per materiale. Il [plugin K2-OpenHost CFS](#orcaslicer-25-il-plugin-k2-openhost-cfs) per OrcaSlicer 2.5 lo invia. La [PR #16208 di OrcaSlicer](https://github.com/OrcaSlicer/OrcaSlicer/pull/16208) legge il `filament_id` di una lane; gli ID che assegna Kalico seguono i profili attuali di OrcaSlicer (`OF…`), che hanno sostituito quelli della 2.4.2 (Bambu PLA Basic: `OGFA00` nella 2.4.2, `OFoiVqVM` ora).

## OrcaSlicer 2.5: il plugin K2-OpenHost CFS

OrcaSlicer 2.5 (alpha dal 16/10/2026) carica plugin Python. [`tools/orcaslicer/k2_openhost_cfs.py`](../../tools/orcaslicer/k2_openhost_cfs.py) è un unico plugin con tre parti. Usa lo stesso Moonraker dell'agente Moonraker integrato:

- **Agente della stampante: sincronizzazione per ID del preset.** Ogni slot della CFS arriva a OrcaSlicer con l'`orca_filament_id` che Kalico tiene per ogni filamento (vedi sopra). Sync sceglie quindi quel preset, per esempio Bambu PLA Basic per una bobina Bambu PLA Basic, non Generic PLA. Uno slot senza ID ricade sul preset `Generic <materiale>` di OrcaSlicer. Tramite l'agente funziona anche la scheda Dispositivo (stato, temperature, avanzamento, pausa/ripresa/stop, riga G-code).
- **Pannello CFS: lo slot di ogni filamento.** Un pannello accanto alla vista 3D elenca i filamenti del progetto, ognuno con un menu degli slot CFS caricati. Il plugin propone uno slot per materiale e poi per colore più vicino; lo cambi lì prima di inviare.
- **Mappa nel G-code.** Quando OrcaSlicer esporta o carica il G-code, il plugin scrive quella scelta dopo la prima riga, per esempio `; K2OH_TOOL_MAP = 0:1,2:0`. All'avvio della stampa Kalico (`box_print_mapping`) la usa al posto dell'abbinamento automatico.
  - La mappa viene scritta solo per il preset stampante e l'elenco di filamenti per cui è stata scelta, e solo se ogni filamento usato dal piatto ha uno slot. Altrimenti non viene scritto nulla e Kalico abbina la stampa da solo.
  - Kalico ignora, con un messaggio in console, anche una mappa con uno slot vuoto o non in linea, e torna all'abbinamento automatico.

Funziona con il classico **Carica e stampa** dell'host di stampa Moonraker. L'opzione globale di OrcaSlicer *Use printer agents instead of print hosts* non serve. Nella 2.5-alpha quell'opzione cambia il flusso di stampa e la scheda Dispositivo di tutte le stampanti non Bambu, quindi tienila spenta se ne hai altre. Se la attivi, l'abbinamento lo fa la finestra di stampa di OrcaSlicer in stile Bambu, e il plugin avvia la stampa con `BOX_PRINT_START … MAP=`.

**Installazione** (OrcaSlicer 2.5 o successivo; Kalico con il supporto della mappa dello slicer in `box_print_mapping`):

1. Scarica `k2_openhost_cfs.py`.
2. In OrcaSlicer apri la gestione dei plugin e installalo come plugin locale. OrcaSlicer lo copia in `%APPDATA%\OrcaSlicer\orca_plugins\`.
3. Nel preset della stampante (**Impostazioni stampante → Informazioni di base → Avanzate**) imposta **Printer Agent** su **K2-OpenHost CFS**. Come host di stampa metti l'indirizzo di Moonraker **con la porta**, per esempio `10.10.1.97:7125`, poi salva il preset.
   - Una stampante che OrcaSlicer conosce già con l'indirizzo semplice resta legata all'agente Moonraker integrato.
   - Con il nuovo indirizzo OrcaSlicer la aggiunge sotto questo agente.
4. OrcaSlicer chiede di permettere al plugin di creare un thread e di collegarsi all'indirizzo di Moonraker: consenti entrambi. Il primo collegamento viene rifiutato finché la domanda è aperta; il plugin riprova ogni 2 s.
5. Premi **Sync** nell'elenco dei filamenti.
6. Nella gestione dei plugin esegui **K2-OpenHost CFS slots** per aprire il pannello CFS. Controlla gli slot, poi fai slicing e **Carica e stampa**.

Il pannello tiene la tua scelta finché i filamenti del progetto non cambiano. Quando cambiano, propone di nuovo: premi **Aggiorna** dopo aver cambiato i filamenti, e **Proponi** per ripartire da capo.

La sincronizzazione sceglie solo **preset radice**: quelli di sistema e i tuoi creati con **Crea filamento**, che hanno un ID proprio `P…`. Un preset salvato da un altro (in *Dipendenze* mostra un genitore) non viene mai scelto, con nessun agente: OrcaSlicer prende il genitore. Il pannello CFS non ha questo limite: abbina qualunque preset di filamento usi il progetto. Perché Sync scelga il tuo preset ottimizzato, crealo con **Crea filamento** (marca, tipo, basato sullo stesso preset di sistema), copia le tue impostazioni e assegna il suo ID `P…` al filamento della CFS in Mainsail.

L'agente ha tre impostazioni:
- `poll_interval_s`: aggiornamento dello stato, predefinito 2 s;
- `model_id`: il modello di stampante inviato a OrcaSlicer, per impostazione predefinita il modello del preset con `_`, qui `Creality_K2_Pro`;
- `use_slot_map`: con false le stampe avviate tramite l'agente non usano mai l'abbinamento della finestra.

Le sue righe di log (`[k2oh-cfs]`) sono in `%APPDATA%\OrcaSlicer\log\python_*.log`.

**Provato finora**
- Con il Python di OrcaSlicer (3.12), sul Moonraker della stampante di riferimento: i quattro slot con i loro ID, lo stato della stampante, l'elenco degli slot e la proposta del pannello.
- In OrcaSlicer: Sync tramite l'agente.

Il pannello dentro OrcaSlicer e una stampa avviata con la sua mappa non sono ancora provati. L'API dei plugin di OrcaSlicer è ancora alpha e può cambiare.

## Abbinamento degli slot all'invio

OrcaSlicer ufficiale mostra la finestra filamento → slot all'invio solo per il tipo di host **CrealityPrint** (firmware originale). Il [fork di OrcaSlicer di Jacob10383](https://github.com/Jacob10383/OrcaSlicer) la aggiunge per le stampanti Moonraker che pubblicano `box.print_mapping_version: 1`, come fa K2-OpenHost: ogni filamento del progetto ha una scelta **Load from: Box 1, slot n**, e la stampa parte con `BOX_PRINT_START` e quell'abbinamento, come la finestra di stampa di Mainsail. La sua sincronizzazione legge direttamente l'oggetto `box` e sceglie i preset per nome. Le build sono nella sua release `Nightly-Rolling` (lo zip portable per Windows gira accanto a un OrcaSlicer installato). I campi sono stati verificati sulla stampante di riferimento; non è ancora stato usato per una stampa.

Senza il fork o il plugin sopra, fai slicing e caricamento come sempre: l'abbinamento automatico assegna gli strumenti agli slot all'avvio della stampa.

## accel_to_decel

Kalico non ha `ACCEL_TO_DECEL`: il suo `SET_VELOCITY_LIMIT` scarta il parametro senza errori e usa `minimum_cruise_ratio` di `printer.cfg` (0.5 nel profilo K2, il vecchio 50 %). Con l'opzione **accel_to_decel** di OrcaSlicer attiva, ogni cambio di accelerazione aggiunge un `ACCEL_TO_DECEL=` che non fa nulla. Disattiva l'opzione nei preset di processo della stampante Kalico; per cambiare il rapporto imposta `minimum_cruise_ratio` in `printer.cfg` o aggiungi `SET_VELOCITY_LIMIT MINIMUM_CRUISE_RATIO=<0..0.99>` al G-code iniziale.

## Limiti

- OrcaSlicer sceglie un **preset generico per materiale** ("Generic PLA" per uno slot PLA) con il colore dello slot, non il preset della marca, a meno che non usi il plugin K2-OpenHost CFS di OrcaSlicer 2.5. Se ti servono le sue impostazioni scegli dopo il tuo preset; l'abbinamento CFS funziona lo stesso.
- I profili filamento non hanno la temperatura del piano, quindi `bed_temp` è vuoto e OrcaSlicer usa quella del preset.
- La bobina esterna non fa parte della sincronizzazione; assegnala nella finestra di stampa di Mainsail quando serve.

## Disattivarla

In `macros/box.cfg`:

```ini
[box]
publish_lane_data: false
```

Riavvia Klipper. Le voci già pubblicate restano nel database di Moonraker finché non vengono tolte; se serve, cancella lo spazio `lane_data` dalle impostazioni del database di Mainsail.
