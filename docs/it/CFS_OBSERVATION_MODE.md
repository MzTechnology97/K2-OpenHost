# CFS observation mode

`observation_mode` è un livello di sicurezza K2-OpenHost aggiunto all'integrazione Jacobean `box.py` per validare K2 Pro e OpenHost.

## Obiettivo

Eseguire lo stack CFS reale in Kalico impedendo, durante i primi test, movimenti filamento, write di policy RFID, cutter, toolchange o automazioni runout accidentali.

## Ambito

La protezione è volutamente limitata al layer **Box/CFS**. `serial_485.py` rimane disponibile per gli altri dispositivi sul bus RS-485 condiviso.

## Comportamento

In observation mode:

- il transport Box viene avvolto da un proxy read-only CFS;
- enumeration e query note restano disponibili;
- i function code non in whitelist vengono bloccati prima del TX;
- non vengono registrati i G-code `BOX_*` operativi;
- non vengono registrati `T0`, `T1`, ...;
- non vengono configurati hook operativi di cut sensor/button;
- non viene installato l'observer runout;
- non viene eseguita la normale write startup RFID `0x0D`;
- lo state file usa di default un percorso volatile `/dev/shm` se non diversamente configurato.

## Compatibilità protocollo K2 Pro

La modalità è associata alla patch `box_protocol.py` che accetta il `BOX_STATE` steady K2 Pro a 4 byte mantenendo i percorsi Jacobean a 6 byte e slot-event.

## Risultato validato

La vera classe Jacobean `Box()` ha completato:

- enumeration address 1;
- inizializzazione read-only RFID/slot;
- 10 letture live consecutive;
- una chiamata `_poll()` interna;
- test deliberato del blocco `0x0D`.

Il blocco non ha incrementato il contatore TX sottostante.

```text
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

## Note harness

`sensor_error_present=True` nel test standalone è atteso perché il fake printer non istanzia il vero sensore filamento.

`loaded_slot=-1` resta volutamente conservativo finché non validiamo il loaded-path reale.

## Sorgenti versionate

- `MzTechnology97/kalico-k2pro`, branch `k2-pro-openhost` (l'unica copia mantenuta);
- versionate per la prima volta in `MzTechnology97/k2-pro-custom-firmware`, branch `k2-openhost`, ora archiviato.

L'implementazione originaria rimane attribuita a Jacob10383/Jacobean; le modifiche K2-OpenHost sono limitate ai delta di compatibilità/sicurezza documentati qui.