# Bridge USB tra l'host e la T113

[English](../en/USB_BRIDGE.md)

L'host raggiunge i tre bus della K2 Pro attraverso la T113. Questa pagina descrive il percorso, cosa fa il bridge dello slot B, come è stato misurato e come si comporta quando qualcosa si guasta.

## Il percorso

```text
Klipper (host)
  serialqueue -> /dev/serial/by-id/...-if00/01/02   usbserial_generic, 0525:a4a6
  -> controller USB dell'host -> cavo
T113 (2x Cortex-A7, kernel 5.4 PREEMPT)
  controller USB device -> gadget configfs: 3x gser (Generic Serial)
  -> /dev/ttyGS0/1/2 -> un processo k2oh-bridge per canale
  -> /dev/ttyS2 / ttyS3 / ttyS5, 230400 8N1 -> MCU principale / MCU ugello / RS-485
```

Non c'è socat e non ci sono PTY: l'unico passaggio in user space è il bridge sulla T113. `gser` non negozia la velocità di linea, quindi il baud impostato sull'host non ha effetto; la velocità delle UART è fissata sulla T113. In `printer.cfg` usa i nomi `by-id` (if00 principale, if01 ugello, if02 RS-485): non cambiano quando il gadget si ricollega, i numeri `ttyUSBn` invece sì.

## Cosa fa `k2oh-bridge`

Il bridge dello [slot B](T113_BOOTSTRAP.md) sostituisce quello originale di Creality, che aveva due difetti: una scrittura bloccante (se un lato si fermava, si fermava anche l'altra direzione) e nessun recupero dopo una riconnessione USB (moriva su EIO, oppure girava al 104 % di un core su un descrittore morto).

| Comportamento | Perché |
| --- | --- |
| Una coda di uscita non bloccante per direzione; oltre 64 KiB scarta i byte più vecchi e li conta | un lato fermo non blocca mai l'altro, e i buffer del kernel non traboccano |
| A un EOF dal gadget riapre la porta, aspettando da 50 ms fino a 1 s tra un tentativo e l'altro | dopo una riconnessione il vecchio descrittore è morto; nessun ciclo a vuoto |
| Esce su EIO/ENODEV e procd lo riavvia dopo 1 s | Klipper tollera circa 5 s senza la sua MCU, quindi il bridge torna prima |
| Aspetta le porte che mancano all'avvio | `ttyGS*` compaiono tardi; nessun ciclo di riavvii |
| Scrive i suoi contatori solo in un momento tranquillo (nessun dato per 20 ms) | scriverli subito dopo una richiesta ritardava la risposta della MCU |
| Legge 4096 byte alla volta | letture più piccole peggioravano la latenza di coda |
| `BRIDGE_OPTS` in `k2openhost.conf` (`--nice`, `--rr`, `--cpu`) | regolazioni senza modificare il servizio; spente di default |

## Misure

I tempi di andata e ritorno sono stati misurati con `[link_monitor]` di Kalico (10 richieste `get_uptime` in più al secondo per MCU), la T113 con `k2oh-linkstat`, 10 minuti per variante con movimenti X/Y, l'estrusore e letture RFID su tutti e tre i canali insieme.

Con l'host scarico il bridge dello slot B e quello originale sono uguali entro la variazione tra prove identiche:

| Canale | p50 | p99 | p99.9 |
| --- | --- | --- | --- |
| MCU principale | 0,97 ms | 2,45 ms | circa 8 ms |
| MCU ugello | 0,89 ms | 1,89 ms | circa 7 ms |
| RS-485 | 1,97 ms | | |

L'andata e ritorno dipende dalla UART (43 µs per byte a 230400 baud, in entrambe le direzioni) e dai microframe USB; le code vengono dallo scheduling sulla T113 e sull'host, non dal bridge. Il bridge usa circa l'1 % di un core sul canale principale, lo 0,7 % su quello dell'ugello e meno dello 0,1 % su RS-485, e non ha mai accodato. Nessun errore UART, scrittura parziale o byte perso in nessuna prova.

Durante la stampa da 18 h 44 min del 05/10/2026 (930 righe da un minuto per canale):

| Canale | p50 | p99 (mediana delle righe) | campione peggiore | Errori |
| --- | --- | --- | --- | --- |
| MCU principale | 1,17 ms | 5,25 ms | 18,8 ms | 0 byte ritrasmessi |
| MCU ugello | 1,04 ms | 3,01 ms | 16,4 ms | 0 byte ritrasmessi |
| RS-485 | 1,87 ms | 3,36 ms | 4,4 s (una lettura RFID) | 0 timeout, 0 errori CRC |

`nice`, lo scheduling in tempo reale e lo spostamento dell'interrupt USB sul secondo core non hanno dato differenze più grandi di quella variazione, quindi restano spenti.

## Test di guasto

| Test | Risultato con `k2oh-bridge` sotto procd |
| --- | --- |
| `kill -9` di un bridge, anche durante un movimento | torna in circa 1,5 s; Klipper resta `ready` e il movimento finisce |
| Klipper chiude le porte per 15 s | sulla T113 non cambia niente (`gser` non ha stato di linea) |
| Una porta mancante all'avvio | il bridge aspetta e scrive nel log ogni 30 s, con CPU circa a 0 % |
| Gadget scollegato per 10 s e poi ricollegato | i bridge si riaprono o si riavviano da soli; con i percorsi `by-id` `FIRMWARE_RESTART` recupera Klipper (il primo tentativo può dare "Failed automated reset", il secondo funziona) |
| Riavvio dell'host | i bridge si riaprono con gli stessi PID; l'host torna in circa 15 s con Klipper `ready`, RS-485, CFS e motori |

Se Klipper parte mentre il collegamento RS-485 è giù, kalico-k2pro #24 ritrova la CFS quando torna (coperto dai test, non ancora visto dal vivo).

## Scelte

- **gser invece di CDC ACM.** ACM darebbe nomi `ttyACM*` e la velocità di linea, che qui non usa niente. Stesso percorso bulk e stessa dimensione dei pacchetti, quindi nessun guadagno di latenza; cambiarlo toccherebbe il gadget, le regole udev e i percorsi di Kalico per niente.
- **Nessun bridge nativo in C.** Userebbe una frazione della CPU, ma il bridge non è il limite: il suo tempo di inoltro è molto sotto la variazione tra prove e le code non vengono da lui.
- **USB dell'host.** Se la scheda base lo permette, dai alla T113 un controller USB tutto suo; sulla CM5-IO-BASE-A di riferimento è da sola su un controller RP1 (vedi [Hardware dell'host](HOST.md#usb)). Non spostare mai il cavo durante una stampa.

## Misurare una stampa lunga

Sull'host, in `printer.cfg`:

```ini
[link_monitor]
interval: 60      # una riga CSV per canale al minuto
# probe_hz: 0     # andate e ritorni in più; 0 per le stampe (10 solo per i benchmark)
# raw_path:       # ogni campione su file; solo per i benchmark
```

`LINK_MONITOR_REPORT` stampa i percentili dall'avvio; le righe vanno in `~/printer_data/logs/link_monitor.csv`.

Sulla T113 (slot B), durante la stampa:

```sh
k2oh-linkstat --interval 10 --out /tmp/k2oh-linkstat.csv &
```

Legge solo `/proc` e `/sys`: CPU, interrupt, variazioni degli errori UART, stato del gadget e contatori dei bridge. Il file è in RAM, quindi copialo prima di riavviare.
