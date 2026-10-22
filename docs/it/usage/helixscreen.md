# HelixScreen (schermo della stampante)

Nello slot B lo schermo touch della stampante esegue **[HelixScreen](https://github.com/prestonbrown/helixscreen)**, collegato a Moonraker sull'host. Il bootstrap T113 lo installa al primo avvio dello slot B, già puntato all'host.

## Cosa funziona

- Stato della stampante, temperature, movimenti, file, avvio/pausa/annullamento della stampa.
- Il CFS: HelixScreen legge la struttura `box` stock della K2 che K2-OpenHost pubblica accanto alla propria, e invia i comandi stock della K2 (`BOX_MODIFY_TN`, `CR_BOX_*`, ...), che K2-OpenHost accetta ed esegue con il suo motore di cambio.
- Gli elenchi dei filamenti mostrano **solo la libreria filamenti dell'host** (vedi sotto).

## Elenco filamenti dall'host

HelixScreen include un catalogo di circa 360 preset. Nello slot B il servizio `k2oh-helix-filaments` lo sostituisce con la libreria usata da Mainsail e Kalico: i filamenti di sistema del CFS e i tuoi personalizzati da `cfs_filaments.json`.

- **Host → schermo**: ogni 30 s il servizio legge la libreria da Moonraker e, se è cambiata, riscrive il catalogo di HelixScreen. L'originale viene conservato come `filaments.json.helix-orig`.
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

## Risoluzione problemi

| Sintomo | Soluzione |
| --- | --- |
| Lo schermo resta sul logo di avvio | `k2oh-setup status`, `cat /mnt/UDISK/.k2openhost/setup.log`, poi di nuovo `k2oh-setup`. |
| HelixScreen non raggiunge Moonraker | IP dell'host sbagliato (menu 29), oppure la stampante non raggiunge l'host sulla porta 7125. |
| Un filamento nuovo non compare | Attendi 30 s; il servizio sincronizza mentre la stampante è ferma. `logread -e k2oh-helix`. |
