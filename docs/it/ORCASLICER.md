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

OrcaSlicer rilasciato (2.4.2) non legge ancora l'ID: la sincronizzazione sceglie ancora il preset generico per materiale. La [PR #16208 di OrcaSlicer](https://github.com/OrcaSlicer/OrcaSlicer/pull/16208) legge il `filament_id` di una lane; gli ID che assegna Kalico seguono i profili attuali di OrcaSlicer (`OF…`), che hanno sostituito quelli della 2.4.2 (Bambu PLA Basic: `OGFA00` nella 2.4.2, `OFoiVqVM` ora).

## Abbinamento degli slot all'invio

OrcaSlicer ufficiale mostra la finestra filamento → slot all'invio solo per il tipo di host **CrealityPrint** (firmware originale). Il [fork di OrcaSlicer di Jacob10383](https://github.com/Jacob10383/OrcaSlicer) la aggiunge per le stampanti Moonraker che pubblicano `box.print_mapping_version: 1`, come fa K2-OpenHost: ogni filamento del progetto ha una scelta **Load from: Box 1, slot n**, e la stampa parte con `BOX_PRINT_START` e quell'abbinamento, come la finestra di stampa di Mainsail. La sua sincronizzazione legge direttamente l'oggetto `box` e sceglie i preset per nome. Le build sono nella sua release `Nightly-Rolling` (lo zip portable per Windows gira accanto a un OrcaSlicer installato). I campi sono stati verificati sulla stampante di riferimento; non è ancora stato usato per una stampa.

Senza il fork, fai slicing e caricamento come sempre: l'abbinamento automatico assegna gli strumenti agli slot all'avvio della stampa.

## accel_to_decel

Kalico non ha `ACCEL_TO_DECEL`: il suo `SET_VELOCITY_LIMIT` scarta il parametro senza errori e usa `minimum_cruise_ratio` di `printer.cfg` (0.5 nel profilo K2, il vecchio 50 %). Con l'opzione **accel_to_decel** di OrcaSlicer attiva, ogni cambio di accelerazione aggiunge un `ACCEL_TO_DECEL=` che non fa nulla. Disattiva l'opzione nei preset di processo della stampante Kalico; per cambiare il rapporto imposta `minimum_cruise_ratio` in `printer.cfg` o aggiungi `SET_VELOCITY_LIMIT MINIMUM_CRUISE_RATIO=<0..0.99>` al G-code iniziale.

## Limiti

- OrcaSlicer sceglie un **preset generico per materiale** ("Generic PLA" per uno slot PLA) con il colore dello slot, non il preset della marca, finché non legge l'ID del preset descritto sopra. Se ti servono le sue impostazioni scegli dopo il tuo preset; l'abbinamento CFS funziona lo stesso.
- I profili filamento non hanno la temperatura del piano, quindi `bed_temp` è vuoto e OrcaSlicer usa quella del preset.
- La bobina esterna non fa parte della sincronizzazione; assegnala nella finestra di stampa di Mainsail quando serve.

## Disattivarla

In `macros/box.cfg`:

```ini
[box]
publish_lane_data: false
```

Riavvia Klipper. Le voci già pubblicate restano nel database di Moonraker finché non vengono tolte; se serve, cancella lo spazio `lane_data` dalle impostazioni del database di Mainsail.
