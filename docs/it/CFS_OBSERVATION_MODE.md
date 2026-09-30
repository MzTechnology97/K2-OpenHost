# CFS observation mode

Questo documento descrive la modalità di osservazione protetta usata per validare lo stack CFS di Jacob10383 attraverso K2-OpenHost senza consentire comandi mutanti sul Material Box.

## Obiettivo

La modalità di osservazione esegue discovery, validazione dell'indirizzo esistente e polling dello stato CFS usando lo stack nativo Jacob, impedendo fisicamente che funzioni mutanti raggiungano il bus.

```text
Jacob box/box_protocol
  -> /dev/ttyUSB2 sul CM5
  -> gadget USB K2 / ttyGS2
  -> bridge byte-transparent
  -> T113 /dev/ttyS5 @ 230400 8N1
  -> CFS
```

La protezione è applicata solo allo stack CFS e non globalmente a `serial_485.py`, perché lo stesso bus è condiviso con i controller closed-loop.

## Guard read-only verificato

Il proxy CFS ammette soltanto le funzioni read-only necessarie a discovery e polling e blocca le altre prima del transport seriale sottostante.

Il self-test ha tentato una scrittura RFID `FUNC=0x0D`:

```text
blocked: addr=0x01 func=0x0D
tx_frames before: 2
tx_frames after:  2
```

Il contatore TX invariato dimostra che il frame mutante non è stato trasmesso.

## `box.py` Jacob reale verificato

La copia volatile di Jacobean 6.18 è stata estesa con `observation_mode` e il vero oggetto `Box()` è stato eseguito attraverso K2-OpenHost.

Bootstrap verificato:

```text
observation_mode: True
state_path: /dev/shm/k2-openhost-filament_box.json
registered gcode: ['SERIAL_STATUS']
operational Box G-code: NONE

drivers: [1]
address_errors: []
rfid_presence: {1: '0x0E'}
serial_proxy: _ReadOnlyCFSProxy
```

`SERIAL_STATUS` appartiene al transport `serial_485`; nessun comando operativo `BOX_LOAD`, `BOX_UNLOAD`, `BOX_CUT`, `Tn` o equivalente è stato registrato da `box.py` in observation mode.

Il bootstrap protetto inoltre:

- usa `box_count=1`;
- usa uno `state_path` volatile sotto `/dev/shm`;
- non registra il cut sensor `nozzle_mcu:PB9`;
- non invia la policy RFID `0x0D` durante `_initialize_rfid()`;
- non registra i comandi `Tn`;
- non installa l'handler automatico di runout;
- mantiene attivi enumeration, snapshot e polling read-only.

## Polling nativo `Box.read_live_state()`

Sono stati eseguiti 10 cicli consecutivi tramite il vero `Box.read_live_state()` Jacob.

Ogni ciclo ha restituito:

```text
data_ready: True
loaded_slot: -1
loaded_mask: 0x0
slot_mask: 0x0E
tracking: False
buffer_state: 2
box_status: 0x00
substatus: 0
load_flag: 0
firmware_base: 0x1E22
```

`loaded_slot=-1` è intenzionale e conservativo: il formato steady K2 Pro a 4 byte non contiene il `downstream_mask` del modello Jacobean a 6 byte, quindi OpenHost non inventa ancora un loaded path.

Il test standalone mostrava `sensor_error_present=True` perché il Fake Klippy environment non istanziava il vero `filament_switch_sensor`; non è un errore CFS.

Anche un ciclo reale di `Box._poll()` ha aggiornato correttamente lo snapshot con `slot_mask=0x0E` e `buffer_state=2`.

## Statistiche finali del test `Box()`

```text
allowed requests: 35
blocked requests: 1
blocked funcs: [addr=0x01 func=0x0D]

tx_frames: 35
rx_frames: 35
crc_errors: 0
invalid_len: 0
unmatched: 0
stale_dropped: 0
timeouts: 0
send_errors: 0
reader_errors: 0
```

Questo valida end-to-end il polling nativo di `box.py` dietro la barriera CFS read-only.

## Fork e patchset riproducibile

Le modifiche validate sono state trasferite nel fork pubblico:

```text
MzTechnology97/k2-pro-custom-firmware
branch: k2-openhost
```

`main` rimane sulla base Jacob, mentre `k2-openhost` contiene direttamente:

- `extras/box_protocol.py`: compatibilità `BOX_STATE` K2 Pro a 4 byte;
- `extras/box.py`: `observation_mode` protetta.

Il fork conserva inoltre:

```text
patches/k2-openhost/0001-k2-pro-box-state-4byte.patch
patches/k2-openhost/0002-cfs-observation-mode.patch
patches/k2-openhost/apply.py
patches/k2-openhost/apply.sh
```

Il patcher è SHA-gated contro i file Jacobean 6.18 originali. GitHub Actions verifica anche che i due unified diff possano essere applicati a una worktree pulita di `origin/main` e che il risultato superi `py_compile`.

Commit sorgente principali:

```text
58438be54af474138c4f85eb6084edd8c0bc1096
k2-openhost: support K2 Pro 4-byte CFS BOX_STATE

7132f263c1706ad6810d8ec22c7a848e909b438a
k2-openhost: apply validated K2 Pro compatibility patches
```

## Stato

**Il vero `box.py` Jacob è verificato in observation mode attraverso K2-OpenHost.**

Il prossimo milestone è avviare una vera istanza Klippy/Kalico sul CM5 con `[serial_485 serial485]` su `/dev/ttyUSB2` e `[box] observation_mode: True`, mantenendo load/unload disabilitati finché il loaded-path K2 Pro non sarà correlato in modo affidabile.
