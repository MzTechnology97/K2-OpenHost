# Validazione CFS

Questo documento tiene traccia della validazione hardware del Creality Filament System (CFS) attraverso il percorso di trasporto K2-OpenHost.

## Percorso di trasporto verificato

```text
Host Linux esterno / CM5
  -> /dev/ttyUSB2
  -> gadget USB K2 gser.usb2 / ttyGS2
  -> bridge userspace byte-transparent
  -> T113 /dev/ttyS5 @ 230400 8N1
  -> bus RS-485 condiviso
  -> CFS
```

Il percorso è stato verificato bidirezionalmente su hardware reale. Non è necessario riflashare gli MCU.

## Discovery e addressing

| Operazione | Codice | Stato | Risultato |
|---|---:|---:|---|
| Discovery Material Box | `A1` | ✅ | Material Box rilevato in application mode |
| Assegnazione indirizzo | `A0` | ✅ | Indirizzo `0x01` accettato |
| Online check | `A2` | ✅ | Risposta valida dall'indirizzo `0x01` |
| Query address table | `A3` | ✅ | Risposta valida dall'indirizzo `0x01` |

L'UniID CFS a 12 byte non viene pubblicato intenzionalmente.

## Comandi operativi read-only verificati

| Operazione | Codice | Stato | Risultato hardware |
|---|---:|---:|---|
| Stato box | `0x0A` | ✅ | Formato steady a 4 byte e slot-event `STATUS=0x30` verificati |
| Versione / seriale | `0x14` | ✅ | Risposta ASCII valida a 22 byte; identificativo non pubblicato |
| Slot / hardware mask | `0x08` | ✅ | `0x0F` con A-D presenti; `0x0E` con A vuoto e B-D presenti |
| Buffer state | `0x05` | ✅ | `0x02` con buffer fisicamente vuoto |
| Record RFID/materiale | `0x02` | ✅ | Distinti correttamente slot vuoto, non-RFID e RFID |
| Remaining | `0x03` | ✅ | Valori posizionali A-D coerenti con lo stato fisico |

## Correlazione stato slot

Test fisico controllato:

- slot A vuoto;
- slot B con bobina RFID;
- slot C e D con filamento senza RFID.

Risultato:

```text
READ_MATERIAL:
A:none;B:<record RFID a 40 caratteri>;C:unknown;D:unknown;

READ_REMAIN:
A=0, B=13, C=100, D=100

SLOT_MASK:
0x0E
```

Quindi, sulla K2 Pro di test:

- `none` = slot vuoto;
- `unknown` = filamento presente senza RFID riconosciuto;
- un tag valido produce il record RFID a 40 caratteri;
- `READ_REMAIN=0` segue lo slot svuotato;
- `CMD 0x08`, channel `0x00`, espone una bitmask di presenza slot.

Il record RFID grezzo non viene pubblicato.

## Evento asincrono slot

Dopo la modifica fisica degli slot, `CMD_BOX_STATE (0x0A)` ha restituito:

```text
STATUS = 0x30
DATA   = 02 03 00 00
```

Il reverse engineering pubblico identifica `0x30` come `SLOT_EVENT`; i quattro byte dati rappresentano le fasi per A/B/C/D e `0x03` indica inserimento completato. Nel test il secondo byte coincide con l'inserimento della bobina RFID nello slot B.

## Extra Kalico Jacob10383

K2-OpenHost riutilizza lo stack GPLv3 di Jacob10383 invece di reimplementare il protocollo:

- `serial_485.py`
- `box.py`
- `box_addr.py`
- `box_catalog.py`
- `box_change.py`
- `box_protocol.py`

Gli extra della release firmware Jacobean 6.18 sono stati scaricati dal relativo store content-addressed e verificati via SHA-256 nel clone volatile `/dev/shm/k2-openhost-kalico`. Non è stato eseguito l'installer firmware e non è stato modificato lo stato persistente della K2.

## Transport nativo Jacob verificato

`Serial_485_Wrapper` è stato collegato direttamente a `/dev/ttyUSB2` senza patch:

```text
connected: true
port: /dev/ttyUSB2
baud: 230400
A2 response: valid
CRC: valid
crc_errors: 0
timeouts: 0
unmatched: 0
send_errors: 0
reader_errors: 0
```

Questo valida il transport nativo Jacob end-to-end attraverso K2-OpenHost.

## AutoAddressManager e BoxDriver Jacob

`AutoAddressClient`, `AutoAddressManager` e `BoxDriver` Jacobean 6.18 sono stati eseguiti direttamente sul transport OpenHost.

```text
AutoAddressManager:
online addresses: [1]
known addresses: [1]
errors: []

query_slot_mask:
status: 0x00
value: 0x0E

query_hub_mask:
status: 0x00
value: 0x00

query_buffer:
status: 0x00
value: 2

query_rfid_records:
A: none
B: RFID_RECORD_40_CHARS
C: unknown
D: unknown

query_rfid_remaining:
[0, 13, 100, 100]
```

Il valore `hub_mask=0x00` è verificato soltanto nello stato corrente senza percorso CFS caricato; la semantica sotto carico resta da correlare.

L'intero test ha prodotto:

```text
tx_frames: 6
rx_frames: 6
crc_errors: 0
invalid_len: 0
unmatched: 0
stale_dropped: 0
timeouts: 0
send_errors: 0
reader_errors: 0
```

Quindi transport, addressing, decoder A2, slot mask, hub mask, buffer, RFID e remaining funzionano senza patch.

## Delta compatibilità BOX_STATE Jacobean 6.18 / K2 Pro

Il primo vero delta è `CMD_GET_BOX_STATE (0x0A)`.

Il CFS della K2 Pro restituisce in steady state:

```text
STATUS = 0x00
DATA   = 1f 23 00 00
```

Il reverse engineering wire-correct pubblico descrive questo formato come:

```text
[b0][b1][b2][b3]
 b0/b1 = base firmware opaca
 b2    = substatus
 b3    = load flag
         0x00 = feed/change
         0x02 = loaded/print-locked
```

`b0/b1` variano tra letture e non devono essere usati come stato.

`box_protocol.py` Jacobean 6.18, invece, accetta per lo steady state un payload a 6 byte e quindi genera:

```text
ProtocolError: box-state payload has the wrong shape
```

Il frame della K2 Pro è completo e CRC-valid: non è un errore di transport ma una incompatibilità del decoder.

## Strategia di compatibilità

La prima patch OpenHost sarà intenzionalmente conservativa:

1. accettare anche il formato steady `0x0A` a 4 byte;
2. mantenere `b0/b1` opachi;
3. esporre `substatus` e `load_flag` reali;
4. non inventare temperatura, umidità, `box_state` o `downstream_mask` mancanti;
5. mantenere invariato il parsing `STATUS=0x30` degli eventi slot;
6. testare la patch in `/dev/shm` prima di abilitarla nel `box.py` completo.

Per il monitoraggio questa compatibilità è sufficiente. Prima di abilitare load/unload automatici dovrà essere verificato come ricavare in modo affidabile lo slot/percorso caricato, probabilmente correlando il load flag con le query separate del bus invece di sintetizzare il modello a 6 byte.
