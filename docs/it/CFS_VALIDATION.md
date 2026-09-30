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

Le seguenti operazioni protocollo CFS sono state verificate end-to-end dall'host esterno:

| Operazione | Codice | Stato | Risultato |
|---|---:|---:|---|
| Discovery Material Box | `A1` | ✅ | Material Box rilevato in application mode |
| Assegnazione indirizzo | `A0` | ✅ | Indirizzo `0x01` accettato |
| Online check | `A2` | ✅ | Risposta valida dall'indirizzo `0x01` |
| Query address table | `A3` | ✅ | Risposta valida dall'indirizzo `0x01` |

L'UniID CFS a 12 byte non viene pubblicato intenzionalmente.

## Comandi operativi read-only

| Operazione | Codice | Stato | Risultato hardware |
|---|---:|---:|---|
| Stato box | `0x0A` | ✅ | Verificati stato steady e eventi asincroni slot |
| Versione / seriale | `0x14` | ✅ | Risposta ASCII valida a 22 byte; identificativo non pubblicato |
| Hardware status | `0x08` | ✅ | Osservato flag stabile |
| Buffer state | `0x05` | ✅ | Osservato `0x02` con buffer fisicamente vuoto |
| Record RFID/materiale | `0x02` | ✅ | Distinti correttamente slot vuoti, non-RFID e RFID |
| Remaining | `0x03` | ✅ | Valori posizionali A-D coerenti con lo stato fisico |

## Correlazione stato slot

È stato eseguito un test fisico controllato con:

- slot A vuoto;
- slot B con bobina RFID;
- slot C e D con filamento senza RFID.

Stato protocollo osservato:

```text
READ_MATERIAL:
A:none;B:<record RFID a 40 caratteri>;C:unknown;D:unknown;

READ_REMAIN:
A=0, B=13, C=100, D=100
```

Questo verifica sulla K2 Pro di test che:

- `none` rappresenta uno slot selezionato vuoto;
- `unknown` rappresenta filamento presente senza record RFID identificato;
- una bobina RFID valida produce il record atteso a 40 caratteri;
- `READ_REMAIN` riporta `0` per lo slot svuotato e un valore non-zero per gli slot occupati.

Il record RFID grezzo viene intenzionalmente omesso dalla documentazione pubblica.

## Evento asincrono slot

Subito dopo la modifica della configurazione degli slot, `CMD_BOX_STATE (0x0A)` ha restituito:

```text
STATUS = 0x30
DATA   = 02 03 00 00
```

Il reverse engineering pubblico dello stack CFS di Jacob10383 identifica `0x30` come `SLOT_EVENT`, con i quattro byte dati usati come fasi evento per gli slot. La fase `0x03` indica inserimento completato. Nel test il secondo byte corrisponde allo slot B e coincide con la nuova bobina RFID inserita.

## Extra Kalico Jacob10383

K2-OpenHost non reimplementerà il protocollo CFS. L'integrazione target è lo stack GPLv3 esistente di Jacob10383:

- `serial_485.py`
- `box.py`
- `box_addr.py`
- `box_catalog.py`
- `box_change.py`
- `box_protocol.py`

Gli extra K2/CFS non sono necessariamente presenti nel repository Kalico stesso: il firmware Jacobean li distribuisce separatamente. Sul clone Kalico volatile usato da OpenHost mancavano inizialmente questi file, quindi il primo bootstrap transport-only non poteva caricare `serial_485`/`motor_control`. Gli extra della release firmware Jacobean 6.18 sono stati quindi scaricati dal relativo store content-addressed e verificati tramite SHA-256, senza eseguire l'installer firmware e senza modificare il sistema persistente.

Il lavoro specifico OpenHost consiste soprattutto nella sostituzione del trasporto:

```text
Stack Jacob serial_485 / box
        -> /dev/ttyUSB2 sul CM5
        -> bridge USB/seriale K2 OpenHost
        -> T113 /dev/ttyS5
        -> bus RS-485 CFS
```

`serial_485.py` accetta già un device seriale configurabile e usa 230400 8N1, quindi sul CM5 la configurazione prevista è semplicemente `serial: /dev/ttyUSB2`.

## Transport nativo Jacob verificato

Il `Serial_485_Wrapper` originale di Jacob10383 è stato caricato direttamente dal clone Kalico volatile e collegato a `/dev/ttyUSB2` senza patch. Il wrapper ha aperto correttamente la porta a 230400 baud e una query nativa A2 verso il CFS assegnato a `0x01` ha prodotto una risposta valida:

```text
connected: true
port: /dev/ttyUSB2
baud: 230400
A2 response: valid
CRC: valid
tx_frames: 1
rx_frames: 1
crc_errors: 0
timeouts: 0
unmatched: 0
send_errors: 0
reader_errors: 0
```

Il payload identificativo della risposta A2 è intenzionalmente redatto. Questo valida il trasporto nativo Jacob end-to-end attraverso K2-OpenHost senza alcuna modifica al driver `serial_485.py`.

## Prossimo step di validazione

Usare `box_protocol.AutoAddressClient` e `box_addr.AutoAddressManager` originali di Jacob sul transport appena validato. Con un solo box già online a `0x01`, il test iniziale sarà read-only: A2 deve riconoscere il box prima che il manager abbia necessità di eseguire discovery o assegnazione. Successivamente verrà istanziato `BoxDriver` per confrontare slot mask, buffer, box state, record RFID e remaining con i risultati raw già verificati.
