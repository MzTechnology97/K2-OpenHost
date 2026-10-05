# Bridge USB tra l'host e il T113: analisi e misure

Aggiornato: **5 ottobre 2026**. [English](../en/USB_BRIDGE.md)

L'host esterno raggiunge i tre bus della K2 Pro attraverso il T113. Questa pagina descrive:
- come funziona davvero il collegamento;
- cosa non andava;
- cosa è cambiato nel [bootstrap del T113](T113_BOOTSTRAP.md);
- le misure dietro ogni decisione.

Tutti i test sono stati fatti sulla K2 Pro di sviluppo: host CM5, slot A, bridge avviati a mano in RAM, piatto vuoto, riscaldatori spenti.

## Il percorso, com'è

```text
Klipper (CM5)
  serialqueue -> /dev/ttyUSB0/1/2   usbserial_generic, 0525:a4a6
  -> controller USB 2.0 dwc2 del CM5 -> hub a 4 porte -> cavo
T113 (2x Cortex-A7, kernel 5.4.61 PREEMPT)
  sunxi_usb_udc (high speed) -> gadget configfs g1: 3x gser (Generic Serial, non CDC ACM)
  -> /dev/ttyGS0/1/2 -> un processo bridge per canale (Python 3.9)
  -> /dev/ttyS2 / ttyS3 / ttyS5, 230400 8N1 -> MCU Main / MCU Nozzle / RS-485
```

| Elemento | Trovato |
| --- | --- |
| socat, PTY | **nessuno**. L'unico passaggio in user space è il bridge Python sul T113. |
| Funzione del gadget | `gser` (Generic Serial). Non si negoziano né line coding né linee di controllo, quindi il baud impostato dall'host non ha effetto sul lato USB. |
| Porte di Kalico | `serial: /dev/ttyUSB0/1/2` in `printer.cfg`: numeri decisi dall'ordine di enumerazione |
| Controller del CM5 | `dwc2` (IRQ 34, CPU0), circa **8 100 interrupt/s** anche a riposo (uno per microframe). Le porte `xhci` RP1 del CM5 non sono usate. |
| Interrupt del T113 | controller USB device (IRQ 55) e tutte e tre le UART su **CPU0**. L'IRQ 55 si può spostare su CPU1 (verificato con `effective_affinity_list`); gli interrupt delle UART non sono stati spostati. |
| Strumenti sul T113 | niente socat né chrt. C'è `taskset`, e `os.sched_setscheduler` / `sched_setaffinity` di Python funzionano. |

## Problemi trovati

1. **Scrittura bloccante nel bridge originale.** Il ciclo è `select`, `read(4096)`, poi una scrittura che riprova finché non ha scritto tutto. Quando un lato smette di accettare dati (Klipper fermo, FIFO della UART piena), anche l'altra direzione smette di essere letta.
   - La UART del nozzle `ttyS3` mostrava **2 239 272 buffer overrun** (`bo`) accumulati nei giorni precedenti.
   - In nessuna finestra di benchmark ne è comparso uno.
2. **Morto dopo una riconnessione USB.** Dopo un rebind del gadget (o una riconnessione USB) il vecchio descrittore di `ttyGS*` restituisce solo EOF, e le scritture falliscono con EIO.
   - Con EIO il bridge originale muore, e nessuno lo riavvia.
   - Con EOF torna subito a `select`: **il 104% di un core del T113**, per sempre, senza inoltrare più nulla (misurato, vedi i test di guasto).
   - Klipper che chiude le porte non lo provoca: `gser` non avvisa il gadget.
3. **Nomi delle porte legati all'ordine di enumerazione.** `ttyUSB0/1/2` mantengono il numero solo se nient'altro si enumera prima e i vecchi nodi sono chiusi. `/dev/serial/by-id/...-if00/01/02-port0` indica invece l'interfaccia.
4. **Controller USB del CM5.** Il traffico del bridge passa da `dwc2` e da un hub. In modalità host `dwc2` interrompe il CM5 circa 8 100 volte al secondo.
5. **Un bug di misura mio,** trovato e corretto durante questo lavoro. `link_monitor.get_status()` riordinava tutti i campioni dall'avvio a ogni interrogazione di Moonraker.
   - Dopo tre ore il thread principale di klippy usava circa il 55% di un core e il CM5 è arrivato a 85 °C (throttling termico).
   - Corretto in kalico-k2pro [#19](https://github.com/MzTechnology97/kalico-k2pro/pull/19): istogramma a costo costante, stato calcolato una volta per intervallo.

## Cosa è cambiato nel bootstrap (`k2oh-bridge`)

| Modifica | Perché |
| --- | --- |
| Code di uscita non bloccanti, una per direzione | un lato fermo non blocca mai l'altro. Una coda oltre 64 KiB scarta i byte più vecchi e li conta, così i buffer del kernel dietro di lei non vanno mai in overrun. |
| `poll` registrato una volta; le maschere cambiano solo quando una coda si riempie o si svuota | il passaggio normale è poll, read, write: niente liste, nessuna lettura dell'orologio |
| EOF dalla porta del gadget: la riapre, con attese da 50 ms che raddoppiano fino a 1 s | dopo una riconnessione il vecchio descrittore è morto; nessun ciclo a vuoto, al massimo una riapertura al secondo |
| Contatori scritti ogni 5 s **in un momento di silenzio** (nessun dato per 20 ms), ogni 30 s se non è cambiato nulla | scrivere il JSON costa circa 3,5 ms sul T113. Fatto subito dopo aver inoltrato una richiesta, ritardava la risposta dell'MCU: il p99 del nozzle passava da circa 2 a circa 4 ms (blocco B). |
| Ritardo misurato solo per i dati accodati | misurare ogni scrittura costava più CPU dell'inoltro |
| Attesa delle porte mancanti (log ogni 30 s, controllo ogni 0,5 s) | i ttyGS* compaiono tardi all'avvio e dopo un rebind del gadget; nessun ciclo di riavvii |
| Uscita con motivo su `EIO`/`ENODEV`; procd lo riavvia dopo 1 s (`respawn 60 1 0`) | Klipper tollera circa 5 s senza la sua MCU, quindi un bridge caduto torna prima. Al massimo un riavvio al secondo, mai un ciclo stretto. |
| `BRIDGE_OPTS` in `k2openhost.conf` (`--chunk`, `--nice`, `--rr`, `--cpu`) | regolazione senza modificare il servizio. Predefinito: nessuna opzione, vedi sotto. |
| `k2oh-linkstat` | campionatore per stampe lunghe, vedi sotto |

## Come è stato misurato

- **Round trip sull'host:** `[link_monitor]` di kalico-k2pro, in modalità benchmark con `probe_hz: 10` e `raw_path`.
  - Ogni MCU riceve 10 interrogazioni `get_uptime` in più al secondo, oltre alle risposte `clock` che clocksync chiede già.
  - Il tempo è `#receive_time - #sent_time` del livello seriale.
  - RS-485: il tempo dalla scrittura di una richiesta alla sua risposta.
  - `rpi` (la MCU host su socket locale) è il fondo del metodo: p50 0,04 ms.
- **T113:** `k2oh-linkstat` ogni 10 s.
  - CPU per core e cambi di contesto;
  - frequenza degli IRQ del controller USB e delle UART;
  - differenze degli errori UART (fe, oe, bo, brk);
  - stato del gadget;
  - CPU, cambi di contesto e RSS di ogni bridge, più i contatori dei bridge stessi.
- **CM5:** `/proc/stat` e il conteggio IRQ di `dwc2` all'inizio e alla fine di ogni finestra.
- **Carico**, 10 minuti per variante dopo 20 s di assestamento, tramite Moonraker:
  - **A**: solo XY. Archi e zig-zag a 300 mm/s, 19 blocchi per finestra.
  - **B, C, D**: tutti i canali insieme.
    - XY come in A.
    - L'estrusore che gira a freddo a ogni linea dello zig-zag. `M302 P1` per la durata della prova, senza filamento, nozzle freddo.
    - Letture RFID dei 4 slot del CFS e del lettore esterno via RS-485, inviate mentre il moto in coda è ancora in corso.
    - Le risposte RS-485 oltre 0,5 s sono letture RFID (il CFS prima fa girare lo slot). Sono tempo applicativo e vengono contate a parte.
- **Varianti del bridge:** il bridge originale (`orig`) contro `k2oh-bridge` (`new`), scambiati sul T113 tra una finestra e l'altra.
- **Variabilità tra corse:** ogni corsa ha circa 5 800 campioni per MCU, quindi il p99.9 poggia su circa 6 campioni. `orig` è stato ripetuto in ogni blocco per vedere la differenza tra corse identiche.

## Risultati

Round trip in ms, MCU Main (mcu) e MCU Nozzle (noz); CPU del bridge in % di un core del T113.

### A: solo XY

| Variante | mcu p50 | p95 | p99 | p99.9 | max | noz p99 | CPU bridge main/noz | cambi involontari/s T113 (main) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| orig | 1,014 | 1,862 | 3,612 | 7,737 | 12,3 | 1,949 | 1,83 / 0,74 | 7,0 |
| primo new, chunk 4096 | 1,070 | 2,196 | 4,229 | 8,663 | 16,2 | 3,525 | 3,09 / 1,44 | 22,4 |
| primo new, chunk 1024 | 1,078 | 2,367 | 4,559 | 7,978 | 17,8 | 3,804 | 3,05 / 1,43 | 21,7 |
| primo new, chunk 256 | 1,080 | 3,091 | 5,418 | 10,37 | 14,6 | 4,324 | 3,03 / 1,40 | 21,2 |
| primo new, chunk 64 | 1,075 | 3,270 | 5,464 | 9,047 | 14,3 | 4,775 | 3,07 / 1,37 | 20,6 |

- La prima riscrittura leggeva l'orologio e creava liste a ogni passaggio: doppia CPU e code peggiori. È stata riscritta (il ciclo descritto sopra).
- Letture più piccole peggiorano solo p95/p99: i messaggi si spezzano su più pacchetti USB e più passaggi. **Resta 4096 come predefinito.**

### B: tutti i canali, `new` con contatori scritti ogni secondo

| Variante | mcu p50 | p99 | p99.9 | max | noz p99 | p99.9 | rs485 p50/p95 | CPU bridge main/noz/485 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| orig | 1,021 | 3,053 | 8,444 | 15,6 | 2,248 | 5,799 | 1,94 / 2,85 | 1,15 / 0,68 / 0,04 |
| new | 1,020 | 3,797 | 6,740 | 16,5 | 4,073 | 7,032 | 1,95 / 3,18 | 1,21 / 0,77 / 0,35 |
| new `--nice -10` | 1,023 | 3,905 | 8,381 | 13,3 | 4,077 | 7,740 | 1,96 / 3,06 | 1,21 / 0,76 / 0,35 |
| new `--rr 10` | 1,014 | 3,492 | 5,663 | 8,7 | 4,052 | 6,763 | 1,93 / 2,92 | 1,28 / 0,78 / 0,35 |
| orig (ripetuto) | 1,035 | 2,524 | 6,940 | 8,9 | 2,091 | 7,304 | 1,97 / 3,23 | 1,14 / 0,68 / 0,04 |

- Il p99 del nozzle è circa 4,05 ms in tutte le varianti `new`, contro 2,1–2,25 ms di `orig`: una differenza reale, non rumore.
- La causa è la scrittura del JSON da 3,5 ms ogni secondo, fatta subito dopo aver inoltrato una richiesta. Il bridge RS-485 quasi inattivo mostra quel costo (0,35% di CPU con pochissimo traffico).

### C: tutti i canali, `new` con contatori scritti nei momenti di silenzio

| Variante | mcu p50 | p99 | p99.9 | max | noz p99 | p99.9 | CPU bridge main/noz/485 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| orig | 1,037 | 2,508 | 6,424 | 12,7 | 1,878 | 7,401 | 1,14 / 0,69 / 0,04 |
| new | 1,014 | 2,624 | 7,325 | 8,5 | 2,034 | 6,695 | 1,04 / 0,66 / 0,06 |
| new `--rr 10` | 1,019 | 2,502 | 8,369 | 14,4 | 1,791 | 7,613 | 1,12 / 0,68 / 0,06 |
| new, IRQ USB su CPU1 | 1,027 | 2,488 | 5,682 | 8,2 | 1,785 | 4,730 | 1,06 / 0,62 / 0,06 |
| orig (ripetuto) | 1,045 | 2,894 | 8,603 | 10,2 | 2,029 | 7,870 | 1,07 / 0,64 / 0,04 |

Il blocco C è girato mentre il bug di `link_monitor` caricava il CM5 sempre di più (CPU del CM5 dal 9,8% al 13,8%). Le varianti sono alternate, quindi il confronto regge, ma il blocco D lo ripete con Klipper appena riavviato.

### D: tutti i canali, host pulito (Klipper riavviato con la correzione)

| Variante | mcu p50 | p95 | p99 | p99.9 | max | noz p50 | p99 | p99.9 | rs485 p50/p95 | CPU bridge main/noz/485 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| orig | 0,993 | 1,464 | 2,426 | 8,043 | 14,6 | 0,909 | 1,909 | 6,735 | 1,94 / 3,01 | 1,27 / 0,76 / 0,04 |
| new | 0,970 | 1,411 | 2,359 | 7,904 | 15,5 | 0,884 | 1,881 | 7,353 | 1,96 / 2,94 | 1,18 / 0,74 / 0,05 |
| orig | 0,995 | 1,521 | 2,500 | 8,030 | 15,2 | 0,909 | 1,832 | 7,946 | 1,98 / 3,11 | 1,27 / 0,75 / 0,04 |
| new | 0,982 | 1,531 | 2,525 | 11,89 | 16,3 | 0,887 | 1,903 | 7,246 | 1,97 / 2,89 | 1,18 / 0,72 / 0,06 |
| **orig, 2 corse insieme** | 0,99 | — | 2,46 | 8,03 | 15,2 | 0,91 | 1,87 | 7,18 | 1,96 / — | 1,27 / 0,76 / 0,04 |
| **new, 2 corse insieme** | 0,97 | — | 2,45 | 8,87 | 16,3 | 0,89 | 1,89 | 7,25 | 1,97 / — | 1,18 / 0,73 / 0,06 |

- Da p50 a p99 i valori coincidono a pochi centesimi di millisecondo. p99.9 e massimo poggiano su pochi campioni e variano tra due corse `orig` quanto tra `orig` e `new`.
- Il nuovo bridge usa circa il 7% di CPU in meno.
- CM5: 0,7% di CPU (media su 4 core), contro il 5–14% dei blocchi B e C con il bug di `link_monitor`. Anche il p95 mcu è sceso da circa 1,85 a circa 1,5 ms: parte della coda era il carico dell'host stesso.

### In ogni finestra di ogni blocco

- Errori UART (fe, oe, bo, brk): **0**.
- Scritture parziali, EAGAIN, byte scartati: **0**. La coda del bridge non è mai stata usata (`maxq 0`).
- Klipper `ready` alla fine di ogni finestra.
- Interrupt `dwc2` del CM5: circa 8 075–8 130/s, qualunque sia il carico.

## Scheduling, affinità, interrupt

| Opzione | Misurato | Decisione |
| --- | --- | --- |
| `nice -10` | meno cambi involontari (0,6/s invece di 2,3/s), code non migliori | non predefinito |
| `SCHED_RR 10` | cambi involontari quasi 0. Una finestra con la coda mcu migliore (B), la successiva (C) non migliore di `orig`. Dentro la variabilità tra corse. | non predefinito, disponibile come `BRIDGE_OPTS="--rr 10"` |
| `SCHED_FIFO` | non provato | — |
| IRQ USB 55 su CPU1 | miglior p99.9 del blocco C (mcu 5,7, noz 4,7 ms), da una sola finestra | promettente, non predefinito: una finestra sta dentro la variabilità. La maschera non è persistente e il bootstrap non la imposta. |
| Affinità CPU dei bridge | non misurata a parte: con gli IRQ su CPU0 e due core, fissare i bridge non ha nulla da guadagnare senza spostare gli IRQ | — |

I bridge usano circa l'1% (Main) e lo 0,7% (Nozzle) di un core. Il T113 è occupato in tutto per circa il 13% per core; il resto sono altri processi, non analizzati qui.

## Gadget USB: gser o CDC ACM

- **gser** (attuale): nessuna richiesta di controllo, nessun line coding, pipe bulk grezze. È ciò a cui si lega `usbserial_generic` sull'host tramite VID/PID (`0525:a4a6`).
- **CDC ACM** porterebbe `cdc_acm` sull'host, nomi standard `ttyACM*` e un numero di serie in `by-id`. Le sue funzioni in più (line coding, DTR/RTS) qui non servono: la velocità delle UART è fissa sul T113 e nessuno usa le linee di controllo.
- Il percorso dei dati e la dimensione dei pacchetti sono gli stessi (bulk, 512 byte in high speed), quindi non c'è da aspettarsi differenze di latenza.
- Cambiarlo vorrebbe dire modificare lo script del gadget, le regole udev dell'host e i percorsi `serial:` di Kalico, senza un guadagno misurato. **Resta gser.**

## Test di guasto

procd è stato emulato con un servizio temporaneo creato via `ubus` (solo in RAM, sparisce al riavvio), con il `respawn 60 1 0` del bootstrap. Klipper a riposo salvo dove indicato; `k2oh-ctl` è stato fermato durante i test perché il suono di shutdown di Klipper non suonasse di notte.

| Test | Bridge originali (slot A oggi) | `k2oh-bridge` sotto procd |
| --- | --- | --- |
| `kill -9` di un bridge, ogni canale | il bridge resta fermo finché non lo riavvii a mano (nessun supervisore nello slot A) | di nuovo operativo in **1,5 s**; Klipper è rimasto `ready` su Main, Nozzle e RS-485 |
| `kill -9` del bridge Main **durante il moto** (zig-zag a 100 mm/s) | — | di nuovo attivo in circa 1,3 s, il moto è terminato, Klipper `ready` |
| L'host chiude le porte (Klipper fermo 15 s) | il gadget non viene avvisato (`gser` non ha stato di linea): non cambia nulla | non cambia nulla neppure qui: 0,4 / 0,1 / 0,0% di CPU, nessuna riapertura; Klipper `ready` dopo l'avvio |
| Porta mancante all'avvio (`ttyGS9`, `ttyS9`) | esce con un traceback (dal codice, non eseguito) | attende, log ogni 30 s, circa 0% di CPU |
| Gadget scollegato 10 s, poi ricollegato | Main e Nozzle **muoiono** per EIO e nessuno li riavvia; RS-485 **gira al 104% di CPU** su un descrittore morto e non inoltra più nulla. Klipper non si è ripreso finché i bridge non sono stati riavviati a mano. | Main e Nozzle escono per EIO e procd li riavvia; tutti e tre riaprono la porta all'EOF. L'RS-485 è tornato da solo. |
| Stesso test, lato CM5, con `serial: /dev/ttyUSBn` | le porte tornano come `ttyUSB2/3/4` perché Klipper tiene ancora le vecchie: `FIRMWARE_RESTART` fallisce (tre tentativi); per ripristinare serve fermare Klipper e far ri-enumerare il gadget | uguale |
| Stesso test, con `serial: /dev/serial/by-id/...` | — | **`FIRMWARE_RESTART` ripristina** (il primo tentativo incontra il noto "Failed automated reset", il secondo riesce); RS-485 ok, motori X/Y verificati |
| Riavvio del T113 o del CM5 | non eseguito: il riavvio richiede il tuo via libera | atteso come il test del gadget: un riavvio del CM5 toglie l'host USB (EOF sul gadget, i bridge riaprono); un riavvio del T113 toglie il device (le porte dell'host spariscono, Klipper va in shutdown, `FIRMWARE_RESTART` quando i bridge sono attivi) |

Visto anche: se Klipper parte mentre il bridge RS-485 è fermo, il CFS non viene rilevato e resta così anche quando il collegamento torna; un `RESTART` di Klipper lo risolve.

## Bridge nativo in C: confronto (non implementato)

| | Python (`k2oh-bridge`) | C (poll/epoll, stesso schema) |
| --- | --- | --- |
| CPU (misurata / stimata) | 1,0–1,2% Main, 0,6–0,7% Nozzle, sotto lo 0,1% RS-485 | circa 5–10 volte meno: pochi decimi di punto |
| Tempo di inoltro per pacchetto | decine di µs di lavoro dell'interprete attorno a due syscall | pochi µs |
| Peso sul round trip | il p50 del round trip è circa 1 ms: tempo UART a 230400 baud (43 µs per byte, nei due sensi) più microframe USB più lavoro dell'MCU | il risparmio è sotto il 5% del p50 |
| Code (p99.9, max) | 5–9 ms, uguali con il bridge originale, `nice`, RR o un'altra CPU per l'IRQ | invariate: le code vengono dallo scheduling e dagli interrupt sulla CPU0 condivisa e dal lato CM5, non dall'interprete |
| Rischi | nessuno nuovo: stesso interprete del resto del bootstrap | cross-compilazione per il T113 (armhf, libc di Tina), un binario nell'immagine, un secondo codice da testare |

**Giudizio: oggi non è giustificato.**
- In tutti i blocchi il bridge non è il limite. Usa circa l'1% di CPU, non accoda mai, e il suo tempo di inoltro è ben sotto la differenza tra corse identiche.
- Un bridge in C diventa utile solo se una misura futura mostra il contrario, per esempio la CPU del bridge che cresce con più traffico, o la comparsa di accodamenti.

## Raccomandazioni

1. **Usare il `k2oh-bridge` dello slot B** (questa modifica). Stessa latenza dell'originale entro la variabilità di misura, CPU leggermente più bassa, e niente blocchi tra le direzioni. Sopravvive a una riconnessione USB, si riavvia in 1,5 s e attende le porte mancanti.
2. **Usare `/dev/serial/by-id/usb-Allwinner_Technology_Inc._Gadget_Serial-if0N-port0`** invece di `/dev/ttyUSBn` in `printer.cfg` (if00 Main, if01 Nozzle, if02 RS-485). Il numero di interfaccia non cambia quando il gadget si riconnette, e allora `FIRMWARE_RESTART` ripristina.
   - Fatto in kalico-k2pro [#20](https://github.com/MzTechnology97/kalico-k2pro/pull/20).
   - Fatto sul CM5 di sviluppo, con un backup del vecchio `printer.cfg`.
3. **Spostare il cavo del T113 su una porta `xhci` non è possibile con la scheda base attuale.** Vedi [Le porte USB 3.0 del CM5 e la scheda base](#le-porte-usb-30-del-cm5-e-la-scheda-base). Bassa priorità: il guadagno atteso è piccolo.
4. **Raffreddamento del CM5.** A riposo il CM5 stava a 70–78 °C ed è andato in throttling a 85 °C con un bug che consumava CPU. Controllare `vcgencmd get_throttled` dopo le stampe lunghe.
5. **Lasciare `nice`, RR e affinità degli IRQ ai valori predefiniti** finché una misura più lunga non mostra una differenza maggiore della variabilità tra corse identiche.

## Le porte USB 3.0 del CM5 e la scheda base

Verificato il 5 ottobre 2026, in sola lettura sul CM5 di sviluppo durante una stampa.

**Su cosa è montato il CM5.** Il CM5 è su una Waveshare **CM4-IO-BASE-A**. Il suo hub FE1.1S compare come `1a40:0101 Terminus Technology Hub`.
- Tutte le sue porte USB sono USB 2.0, dietro quell'hub, sul controller `dwc2` del CM5: due porte Type-A, e due su un connettore FFC che richiedono un cavo adattatore.
- Le due porte Type-A ospitano il gadget del T113 e, per ora, una fotocamera di scorta (`364d:6366`, `uvcvideo`, MJPEG 1280×720 a 25 fps).
- La configurazione completa richiede tre dispositivi: il T113, la fotocamera della camera e Cartographer (la fotocamera dell'ugello è stata eliminata). Con un adattatore FFC per la terza porta, tutti e tre condividono un unico hub a 480M.
- `dwc2` ha ricevuto 267 milioni di interrupt, tutti sulla CPU0.
- I due controller `xhci` RP1 del CM5 (bus 2–5) non hanno nulla collegato.

**Perché le porte RP1 non sono raggiungibili.** Le due porte USB 3.0 del CM5 usano i pin delle porte CAM0 e DSI0 a 2 linee del CM4. Le coppie USB 2.0 di quelle porte sono i pin 134/136 e 163/165 ([Raspberry Pi, *Transitioning from CM4 to CM5*](https://pip-assets.raspberrypi.com/categories/1261-transitioning/documents/RP-008924-WP-1-Transitioning%20from%20Compute%20Module%204%20to%20Compute%20Module%205.pdf)).
- Una scheda per CM4 porta quei pin a connettori FPC per fotocamera o display.
- Sulla CM4-IO-BASE-A (due connettori CSI, uno DSI) un connettore CSI porta USB3-0, e il suo connettore DSI può portare USB3-1. Non hanno VBUS né un connettore USB, quindi non si possono usare come porte USB.

**L'adattatore CM4-to-Pi4.** Le sue quattro porte USB 3.0 vengono da un **VL805** su PCIe, come sul Pi 4, non dalle porte RP1 del CM5.
- Con un CM5 il VL805 sarebbe un terzo controller `xhci` sul PCIe x1 esterno. Quel PCIe è attivo su questo CM5 (`pcie@1000110000` okay) e ora non ha nulla collegato.
- Waveshare non documenta l'adattatore con il CM5, né da dove arrivi il firmware del VL805.
- Sostituisce l'intera scheda base e non ha uno slot M.2.
- Non consigliato per questo scopo.

**Modi per arrivare a una porta `xhci`, dal cambiamento minore al maggiore:**

| Opzione | Cosa dà | Costo e rischio |
| --- | --- | --- |
| Scheda controller USB 3.0 nello slot **M.2 M-key** della CM4-IO-BASE-A (vuoto: il CM5 parte dall'eMMC) | un controller `xhci` su PCIe per il T113 e Cartographer; la fotocamera resta sull'hub della scheda | una scheda, nessun cambio di scheda base. Scegline una con VL805, il controller già usato sul Pi 4. Non provato qui. |
| Una scheda base fatta per il CM5 con quattro porte USB, per esempio **Geekworm X1500** (2× USB 3.0, 2× USB 2.0, 2× M.2 NVMe, connettore per ventola PWM, zoccolo per la batteria dell'orologio) | T113 e Cartographer ciascuno da solo su un controller `xhci` RP1, la fotocamera su una porta USB 2.0 | l'intera scheda base. È più grande (circa 87 × 88 mm contro 85 × 56 mm) e vuole 5,1 V 5 A via USB-C PD. Che le sue porte USB 3.0 siano quelle RP1 è dedotto: la sua unica linea PCIe va agli slot NVMe, e Geekworm non lo dice. Da verificare con `lsusb -t` dopo il cambio. |
| Waveshare **CM5-IO-BASE-A** (stesso formato carta di credito, 2× USB 3.2 Gen1) o la CM5 IO Board ufficiale | le porte RP1 del CM5 | l'intera scheda base; verificare l'alimentazione a 5 V e il case. Che le sue porte USB 3.2 siano quelle RP1 è dedotto: il CM5 non ha altre sorgenti USB 3, e Waveshare non lo dice. |
| Adattatore CM4-to-Pi4 | VL805, come sopra | cambio di scheda base con supporto CM5 non documentato; nessun vantaggio rispetto alla scheda M.2 |

**Conviene?**
- Il guadagno sono i ~8 000 interrupt/s di `dwc2` sulla CPU0, e un T113 che non condivide più un hub con la fotocamera. Una fotocamera UVC riserva banda periodica in ogni microframe, e il traffico bulk come quello del T113 riceve solo quello che resta su quel bus.
- Le misure qui sopra hanno trovato il round trip limitato dal tempo UART, e le code dallo scheduling. Il CM5 usava lo 0,7% di CPU nel gruppo D.
- Con una sola fotocamera, un adattatore FFC sulla scheda attuale basta per il numero di porte: T113 e fotocamera sulle porte Type-A, Cartographer sulla porta FFC. Misurare il round trip con la fotocamera spenta e in streaming. Spostare il T113 su un controller `xhci` (scheda M.2 o X1500) solo se le code crescono.
- Il gadget va a 480M su qualsiasi porta, USB 3 o no.
- I nomi `by-id` in `printer.cfg` non dipendono dalla porta, quindi spostare il cavo non richiede modifiche alla configurazione.
- Non spostare mai il cavo durante una stampa.

## Modalità di misura per stampe lunghe

Sull'host, in `printer.cfg`:

```ini
[link_monitor]
interval: 60      # una riga CSV per canale al minuto
# probe_hz: 0     # round trip extra; 0 per le stampe (10 solo per i benchmark)
# raw_path:       # ogni campione su file; solo benchmark
```

`LINK_MONITOR_REPORT` stampa i percentili dall'avvio. Le righe vanno in `~/printer_data/logs/link_monitor.csv`.

Sul T113 (slot B), durante la stampa:

```sh
k2oh-linkstat --interval 10 --out /tmp/k2oh-linkstat.csv &
```

Legge solo `/proc` e `/sys`: CPU, interrupt, differenze degli errori UART, stato del gadget e contatori dei bridge. Il file è in RAM, quindi copialo prima di riavviare.
