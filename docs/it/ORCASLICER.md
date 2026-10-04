# OrcaSlicer e il CFS

Aggiornato: **4 ottobre 2026**. [English](../en/ORCASLICER.md)

K2-OpenHost funziona con **OrcaSlicer ufficiale**: non serve una versione modificata. Due cose li collegano:

1. **Sincronizzazione dei filamenti** — la stampante pubblica gli slot del CFS nello spazio `lane_data` del database di Moonraker, la convenzione usata da AFC e Happy Hare. OrcaSlicer dalla 2.3.2 lo legge quando premi il pulsante **Sync** dei filamenti su una stampante Moonraker.
2. **Abbinamento automatico** — quando parte un G-code (da OrcaSlicer, Mainsail o API di Moonraker), il backend abbina ogni strumento dello slicer a uno slot del CFS per materiale e colore, con avvisi per le bobine che potrebbero finire. Vedi [Mappatura CFS delle stampe](CFS_PRINT_MAPPING.md) e la guida di Mainsail.

## Configurare la stampante in OrcaSlicer

1. Usa OrcaSlicer **2.4.0 o successivo** (tipo di host nativo "Moonraker (Klipper)"). Anche la 2.3.2 legge `lane_data`.
2. Seleziona o crea il profilo stampante K2 Pro, poi apri le impostazioni della **stampante fisica / connessione**.
3. **Tipo di host:** `Moonraker (Klipper)`. **Nome host, IP o URL:** l'host esterno, per esempio `k2host.local` o `192.168.1.50`.
4. Prova la connessione e salva.

**OrcaSlicer 2.4.2: la sincronizzazione non si collega.** Quella versione invia sempre una chiave di accesso fissa, anche con il campo vuoto ([OrcaSlicer #13236](https://github.com/OrcaSlicer/OrcaSlicer/issues/13236)). Moonraker accetta senza chiave un client fidato della rete locale, ma rifiuta una chiave sbagliata, quindi `moonraker.log` mostra:

```text
401 GET /server/database/item?namespace=lane_data (<il tuo PC>): Invalid API Key
```

Soluzione: apri `http://<host>:7125/access/api_key` nel browser del PC, copia la chiave da `"result"` (tienila riservata), incollala nel campo **API Key / Password** della connessione di OrcaSlicer, salva e premi di nuovo Sync.

## Sincronizzare i filamenti

Premi **Sync** (il pulsante con le frecce in cima alla lista dei filamenti nella scheda Prepara). OrcaSlicer crea un filamento per ogni slot occupato del CFS, raggruppati a quattro come le unità CFS:

| CFS | OrcaSlicer |
| --- | --- |
| Box 1, slot 1 … slot 4 | filamenti 1–4 (strumenti T0–T3) |
| Box 2, slot 1 … slot 4 | filamenti 5–8 (strumenti T4–T7) |
| slot vuoto | segnaposto vuoto |

Ogni filamento sincronizzato prende **materiale** e **colore** dello slot. Fai lo slicing come sempre: T0 stampa dal Box 1 slot 1, T1 dallo slot 2 e così via, e all'avvio della stampa l'abbinamento automatico conferma la corrispondenza.

Rifai la sincronizzazione dopo aver cambiato bobine: la stampante aggiorna `lane_data` entro pochi secondi da ogni modifica di uno slot (lettura RFID, editor dello slot, Use in slot).

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
  "scan_time": ""
}
```

`lane` è il numero dello strumento (slot fisico, da 0). OrcaSlicer oggi legge `lane`, `material`, `color`, `nozzle_temp` e `bed_temp`; `name`, `vendor`, `filament_id` e `spool_id` servono per l'abbinamento ai preset di marca, che OrcaSlicer non fa ancora per le stampanti Moonraker ([#13006](https://github.com/OrcaSlicer/OrcaSlicer/issues/13006)).

Puoi verificare cosa pubblica la stampante con la stessa richiesta che fa OrcaSlicer:

```bash
curl -s "http://k2host.local:7125/server/database/item?namespace=lane_data"
```

## Limiti

- OrcaSlicer sceglie un **preset generico per materiale** ("Generic PLA" per uno slot PLA) con il colore dello slot, non il preset della marca. Se ti servono le sue impostazioni scegli dopo il tuo preset; l'abbinamento CFS funziona lo stesso.
- I profili filamento non hanno la temperatura del piano, quindi `bed_temp` è vuoto e OrcaSlicer usa quella del preset.
- La bobina esterna non fa parte della sincronizzazione; assegnala nella finestra di stampa di Mainsail quando serve.

## Disattivarla

In `box.cfg`:

```ini
[box]
publish_lane_data: false
```

Riavvia Klipper. Le voci già pubblicate restano nel database di Moonraker finché non vengono tolte; se serve, cancella lo spazio `lane_data` dalle impostazioni del database di Mainsail.
