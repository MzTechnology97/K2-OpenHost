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
| Hardware status / slot mask | `0x08` | ✅ | `0x0F` con quattro slot occupati; `0x0E` dopo svuotamento slot A |
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

SLOT_MASK:
0x0E
```

Questo verifica sulla K2 Pro di test che:

- `none` rappresenta uno slot selezionato vuoto;
- `unknown` rappresenta filamento presente senza record RFID identificato;
- una bobina RFID valida produce il record atteso a 40 caratteri;
- `READ_REMAIN` riporta `0` per lo slot svuotato e un valore non-zero per gli slot occupati;
- `CMD 0x08`, channel `0x00`, espone una bitmask di presenza degli slot sul firmware testato (`0x0F` = A-D presenti, `0x0E` = B-D presenti).

Il record RFID grezzo viene intenzionalmente omesso dalla documentazione pubblica.

## Evento asincrono slot

Subito dopo la modifica della configurazione degli slot, `CMD_BOX_STATE (0x0A)` ha restituito:

```text
STATUS = 0x30
DATA   = 02 03 00 00
```

Il reverse engineering pubblico identifica `0x30` come `SLOT_EVENT`, con i quattro byte dati usati come fasi evento per gli slot. La fase `0x03` indica inserimento completato. Nel test il secondo byte corrisponde allo slot B e coincide con la nuova bobina RFID inserita.

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

## AutoAddressManager e BoxDriver Jacob

Il secondo test ha usato direttamente `AutoAddressClient`, `AutoAddressManager` e `BoxDriver` della release Jacobean 6.18. Risultati verificati:

```text
AutoAddressManager:
online addresses: [1]
errors: []

BoxDriver query_slot_mask:
status: 0x00
slot_mask: 0x0E

BoxDriver query_buffer:
status: 0x00
buffer_state: 2
```

Questo conferma che transport, addressing, decoder A2, slot-presence query e buffer query funzionano senza patch sul percorso OpenHost.

## Delta compatibilità BOX_STATE Jacobean 6.18 / K2 Pro

Il primo delta reale trovato è `CMD_GET_BOX_STATE (0x0A)`. Il CFS della K2 Pro di test restituisce in steady state il formato a 4 byte già osservato nelle catture raw:

```text
STATUS = 0x00
DATA   = 1f 23 00 00
```

I primi due byte sono trattati come base firmware opaca, il terzo è substatus e il quarto è il load flag. Il valore dei primi due byte è già variato tra letture e non viene usato come stato.

`box_protocol.py` della release Jacobean 6.18, invece, accetta per lo steady state un payload a 6 byte e quindi solleva:

```text
ProtocolError: box-state payload has the wrong shape
```

Questo non è un errore di trasporto: il frame ricevuto è completo e CRC-valid. È una incompatibilità di forma del decoder `BOX_STATE` rispetto al firmware CFS presente sulla K2 Pro di test. La variante a 4 byte è inoltre coerente con il reverse engineering wire-correct pubblico del CFS.

La compatibilità non verrà risolta inventando campi mancanti: prima di abilitare il `box.py` completo bisogna adattare il layer protocollo in modo esplicito, mantenendo separata la semantica del formato K2-Pro a 4 byte da quella a 6 byte attesa dallo stack Jacobean 6.18.

## Prossimo step di validazione

Proseguire con le query read-only `BoxDriver` che non dipendono da `decode_box_state`: hub mask, RFID records e remaining. In parallelo definire una compatibility shim per `0x0A` che accetti il formato K2-Pro a 4 byte senza falsificare temperatura, umidità, stato o downstream mask richiesti dal modello a 6 byte.
