# CFS observation mode

Questo documento descrive la modalità di osservazione protetta usata per validare lo stack CFS di Jacob10383 attraverso K2-OpenHost senza consentire comandi mutanti sul Material Box.

## Obiettivo

La modalità di osservazione serve a eseguire discovery, addressing già esistente e polling dello stato CFS usando il transport nativo Jacob, impedendo fisicamente che funzioni di scrittura raggiungano il bus.

Il transport CFS usa:

```text
Jacob box/box_protocol
  -> /dev/ttyUSB2 sul CM5
  -> gadget USB K2 / ttyGS2
  -> bridge byte-transparent
  -> T113 /dev/ttyS5 @ 230400 8N1
  -> CFS
```

## Guard read-only verificato

È stato inserito un proxy davanti al transport CFS che accetta soltanto le funzioni read-only necessarie alla validazione e blocca le altre prima della chiamata a `_write_frame()`.

Durante il self-test, `set_rfid_insert_reading(False)` ha tentato `FUNC=0x0D`. Il guard lo ha bloccato correttamente:

```text
blocked: addr=0x01 func=0x0D
tx_frames before: 1
tx_frames after:  1
```

Il contatore TX invariato dimostra che il frame mutante non è stato trasmesso al CFS.

## Snapshot hardware verificato

Con slot A vuoto, B con bobina RFID e C/D con filamento non-RFID:

```text
online addresses: [1]
slot_mask: 0x0E
hub_mask:  0x00
buffer:    2
RFID:      A=none, B=RFID_RECORD, C=unknown, D=unknown
remaining: [0, 13, 100, 100]
```

L'identificativo CFS e il payload RFID grezzo non vengono pubblicati.

## Polling protetto

Sono stati eseguiti 10 cicli consecutivi di polling read-only. Tutti hanno restituito lo stesso stato steady:

```text
status=0x00
firmware_base=0x1E23
substatus=0x00
load_flag=0x00
slot_mask=0x0E
hub_mask=0x00
buffer=2
```

La `firmware_base` resta trattata come dato opaco e non viene usata per decisioni operative.

Statistiche finali:

```text
allowed requests: 46
blocked requests: 1
tx_frames: 46
rx_frames: 46
crc_errors: 0
invalid_len: 0
unmatched: 0
stale_dropped: 0
timeouts: 0
send_errors: 0
reader_errors: 0
```

Questo valida sia la stabilità del transport OpenHost sia l'efficacia del guard CFS read-only.

## Integrazione prevista in `box.py`

La protezione non deve essere applicata globalmente a `serial_485.py`, perché lo stesso bus è condiviso con i controller closed-loop. La modalità di osservazione verrà quindi implementata nel solo stack CFS.

Il bootstrap protetto dovrà:

- usare `box_count: 1`;
- usare uno `state_path` sotto `/dev/shm`;
- avvolgere il transport usato da `AutoAddressClient` e `BoxDriver` con un proxy read-only;
- non inviare `set_rfid_insert_reading()` durante `_initialize_rfid()`;
- non registrare i comandi `Tn` di cambio materiale;
- disabilitare load, unload, buffer retract, cut, runout recovery e altri comandi operativi;
- non installare l'handler automatico di runout durante la fase di osservazione;
- mantenere disponibili polling e diagnostica.

Il transport RS-485 condiviso resta invariato per gli altri dispositivi.

## Stato

**Guard read-only CFS: verificato su hardware.**

Il prossimo milestone è avviare il vero `box.py` Jacob in `observation_mode` e lasciare che sia il suo polling interno a mantenere lo snapshot CFS, sempre dietro la barriera read-only.