# HelixScreen (schermo della stampante)

Nello slot B lo schermo touch della stampante esegue **HelixScreen**, collegato a Moonraker sull'host. Il bootstrap T113 lo installa al primo avvio dello slot B, già puntato all'host.

K2-OpenHost usa il suo fork, **[MzTechnology97/helixscreen](https://github.com/MzTechnology97/helixscreen)** (ramo `k2-openhost`), basato su [HelixScreen](https://github.com/prestonbrown/helixscreen) di prestonbrown. Le versioni del fork si chiamano come quella di base più il numero della nostra build: `1.0.6-k2oh.1` è la prima build sulla 1.0.6.

## Cosa funziona

- Stato della stampante, temperature, movimenti, file, avvio/pausa/annullamento della stampa.
- La CFS: HelixScreen legge il formato `slots[]` che Kalico pubblica in `box` (dialetto Fork, `api_version` 1) e invia i comandi della K2 (`BOX_MODIFY_TN`, `CR_BOX_*`, ...), che Kalico esegue con il suo motore di cambio.
- Gli elenchi dei filamenti mostrano **solo la libreria filamenti dell'host** (vedi sotto).

## Cosa cambia il fork

| | HelixScreen 1.0.6 | Fork K2-OpenHost |
| --- | --- | --- |
| Colore dopo aver reinserito una bobina | Spesso grigio, anche in OrcaSlicer: HelixScreen scriveva il suo `lane_data` prima della lettura RFID | Quello del tag: il `lane_data` lo scrive solo Kalico |
| Utensili T0–T3 sugli slot | Sempre T*n* = slot *n* | Durante la stampa, la mappatura della stampa (`print_mapping`); altrimenti quella della CFS (`box.map`). L'utensile attivo è quello che passa per lo slot caricato |
| Filamento residuo | Non mostrato | Metri residui e barra di riempimento, dalla CFS o dalla stima di Kalico (vedi [Residuo del filamento](../cfs-firmware/remaining.md)) |
| Attesa di Moonraker all'avvio | `127.0.0.1:7125`, da correggere a ogni aggiornamento | L'host Moonraker scritto nelle impostazioni di HelixScreen |
| Server della telecamera sul T113 (`ustreamer`) | Sempre installato | Saltato se il T113 non ha `/dev/video0`: in OpenHost le telecamere sono sull'host |
| Aggiornamenti dall'app | Dalle release di upstream | Solo dalle release del fork |

## Interfaccia K2-OpenHost

Dalla `1.0.6-k2oh.5` il fork ha un'interfaccia propria per la K2, con il tema `k2-openhost` (Impostazioni → Display). Compare quando HelixScreen è collegato alla CFS di Kalico; con altre stampanti resta l'interfaccia di HelixScreen.

- **Home**: lavoro in corso (anteprima, avanzamento, tempo restante e fine, Pausa/Regola/Stop) o, a stampante ferma, Stampa un file, coda, ristampa dell'ultimo lavoro e preriscaldamento; temperature, CFS, luce (tocco = accesa/spenta, trascinamento = luminosità) e ventole. La Home resta personalizzabile come in HelixScreen.
- **CFS nella Home**: le quattro bobine con colore e residuo. In stampa la bobina in uso dice **IN USO** e indica lo slot del cambio automatico (`9% » 2`).
- **Stato stampa**: anello di avanzamento con anteprima, tempi, bobina in uso con l'ordine di cambio, temperature, velocità, flusso e ventola. **Escludi oggetti** mostra il piatto a tutta larghezza: si tocca l'oggetto da escludere.
- **Pagina CFS**: le quattro bobine, il percorso del filamento (slot, buffer, encoder, anti-intasamento, sensore in testa, ugello), il cambio automatico e la **scheda della bobina esterna** con l'interruttore **Bypass** per attivare o disattivare la modalità bypass. Durante un carico o uno scarico l'intestazione dice la fase (`Caricamento 2 · verso la testa 3/5`).
- **Profilo della bobina** (Modifica → Cambia filamento): l'elenco si apre sul profilo attuale dello slot. Un profilo della libreria di Kalico viene assegnato intero con `_BOX_SLOT_ASSIGN` (temperatura, pressure advance, flusso massimo, ID Orca), anche alla bobina esterna. Gli slot con un tag RFID letto non si modificano a mano.
- **Touch e input** (Impostazioni): area di prova del touch. Il controller GT911 del K2 ha la configurazione fissa nel chip: sensibilità e filtro antirimbalzo non si possono cambiare, né dall'app né dal kernel. Dopo il primo tentativo rifiutato, la scheda lo dice e nasconde i preset.

L'elenco dei lavori previsti è nella [roadmap del fork](https://github.com/MzTechnology97/helixscreen/blob/k2-openhost/docs/k2-openhost/ROADMAP.md).

## Installare o aggiornare il fork

- **Installazione nuova:** l'helper scarica l'ultima release del fork (menu 24, risposta **sì** a HelixScreen).
- **Slot B con HelixScreen di upstream:** a stampante ferma, scarica la release sull'host, copiala sulla stampante e installala con `k2oh-setup helix-update`:

  ```sh
  # sull'host
  curl -fLO https://github.com/MzTechnology97/helixscreen/releases/download/v1.0.6-k2oh.5/helixscreen-k2-v1.0.6-k2oh.5.tar.gz
  scp -O helixscreen-k2-v1.0.6-k2oh.5.tar.gz root@<IP-stampante>:/mnt/UDISK/
  # sulla stampante (SSH)
  k2oh-setup helix-update /mnt/UDISK/helixscreen-k2-v1.0.6-k2oh.5.tar.gz
  ```

  `helix-update` rifiuta se la stampante sta stampando o se l'host non risponde. Salva HelixScreen (impostazioni comprese) e i suoi script di avvio in `/mnt/UDISK/.k2openhost/helix-backup/<data>`, esegue l'installer della release, poi rimette l'attesa sul Moonraker dell'host e spegne il server della telecamera. HelixScreen si riavvia due o tre volte in pochi secondi.
- **Aggiornamenti successivi:** dall'aggiornamento di HelixScreen sullo schermo, che ora legge solo le release del fork.
- **Tornare indietro:** `k2oh-setup helix-restore`, a stampante ferma. Rimette l'ultima versione salvata e sposta quella sostituita in `/mnt/UDISK/.k2openhost/trash/` (niente viene cancellato).

## Elenco filamenti dall'host

HelixScreen include un catalogo di circa 360 preset. Nello slot B il servizio `k2oh-helix-filaments` lo sostituisce con la libreria usata da Mainsail e Kalico: i filamenti di sistema del CFS e i tuoi personalizzati da `cfs_filaments.json`.

- **Host → schermo**: ogni 30 s il servizio legge la libreria da Moonraker e, se è cambiata, riscrive il catalogo di HelixScreen. L'originale viene conservato come `filaments.json.helix-orig`. Dopo un aggiornamento di HelixScreen il servizio riconosce il nuovo catalogo e lo sostituisce di nuovo.
- **Schermo → host**: un filamento creato in HelixScreen viene inviato a Kalico (`_BOX_FILAMENT_SET ID=HXnnnn …`) mentre la stampante è ferma.
- **Durante la stampa** il servizio legge soltanto.

Impostazioni in `/mnt/UDISK/.k2openhost/k2openhost.conf` sulla stampante: `HELIX_FILAMENTS=off` spegne il servizio; `RESTART_HELIX=never` disattiva il riavvio di HelixScreen dopo una modifica della libreria.

Tornare ai preset di HelixScreen:

```sh
/etc/init.d/k2oh-helix-filaments stop
/etc/init.d/k2oh-helix-filaments disable
k2oh-helix-filaments --restore
```

Log: `logread -e k2oh-helix`.

## Comandi utili

| Dove | Comando | Cosa fa |
| --- | --- | --- |
| Console di Klipper | `SCREEN_RESTART` | Riavvia HelixScreen (richiede `[k2_t113]` collegato) |
| Helper | `./helper.sh t113 host <IP>` (menu 29) | Punta HelixScreen a un altro indirizzo dell'host |
| SSH della stampante | `k2oh-setup --host <IP>` | Uguale, sulla stampante |
| SSH della stampante | `k2oh-setup status` | Stato della configurazione al primo avvio |
| SSH della stampante | `k2oh-setup helix-update <archivio>` | Installa un'altra release di HelixScreen, a stampante ferma, con backup |
| SSH della stampante | `k2oh-setup helix-restore` | Rimette l'ultima versione salvata |

## Risoluzione problemi

| Sintomo | Soluzione |
| --- | --- |
| Lo schermo resta sul logo di avvio | `k2oh-setup status`, `cat /mnt/UDISK/.k2openhost/setup.log`, poi di nuovo `k2oh-setup`. |
| HelixScreen non raggiunge Moonraker | IP dell'host sbagliato (menu 29), oppure la stampante non raggiunge l'host sulla porta 7125. |
| Un filamento nuovo non compare | Attendi 30 s; il servizio sincronizza mentre la stampante è ferma. `logread -e k2oh-helix`. |
| Una bobina reinserita resta grigia, anche in OrcaSlicer | HelixScreen di upstream: installa il fork. Per correggere subito lo slot, `_BOX_RFID_READ_SLOT SLOT=<n>` dalla console. |
| Gli utensili sugli slot non seguono la mappatura | HelixScreen di upstream: installa il fork. |
| `helix-update` risponde `printer state is printing` | Attendi la fine della stampa. Con `unreachable` la stampante non raggiunge Moonraker sull'host. |
| Dopo un aggiornamento qualcosa non va | `k2oh-setup helix-restore` e segnala il problema nel [fork](https://github.com/MzTechnology97/helixscreen/issues). |
