# Validazione CFS su K2 Pro

Questo documento riporta solo risultati verificati sulla K2 Pro del progetto o derivati esplicitamente dalle implementazioni pubbliche citate. Identificativi privati e payload RFID non vengono pubblicati.

## Baseline pubblica

Il lavoro CFS usa come riferimento soprattutto:

- extra Klipper pubblici Creality per serie K2;
- extra K2 custom firmware di Jacob10383/Jacobean;
- reverse engineering `gitstonelabs/creality-cfs-klipper`;
- altri lavori pubblici elencati in `REFERENCES.md`.

Il reverse engineering pubblico è una baseline di implementazione, non una prova che ogni comportamento sia identico sulla K2 Pro.

## Trasporto

Il CFS condivide il bus RS-485 stock su `/dev/ttyS5` a 230400 baud:

```text
CM5 /dev/ttyUSB2 <-> T113 /dev/ttyGS2 <-> /dev/ttyS5 <-> CFS/RS-485
```

## Addressing verificato

- frame head `0xF7`;
- broadcast MB/CFS `0xFE`;
- discovery A1 verificato ripetutamente con identificativo privato stabile;
- A0 verso indirizzo `0x01` verificato;
- A2 verificato;
- A3 verificato.

## Query read verificate

Sono stati letti correttamente:

- slot mask;
- buffer state;
- stato/record RFID;
- materiale residuo;
- Box state.

## Differenza BOX_STATE K2 Pro

Il decoder Jacobean originario attendeva payload steady a 6 byte. La K2 Pro testata risponde validamente con 4 byte.

K2-OpenHost mantiene i primi due byte opachi come `firmware_base`, poi espone `substatus` e `load_flag`. Il percorso 6-byte e gli eventi asincroni `STATUS=0x30` restano compatibili.

Valori opachi differenti osservati nel tempo confermano che non è corretto assegnare ai primi due byte una semantica non dimostrata.

## Test nativi Jacobean

### Serial_485_Wrapper

Funzionamento diretto su `/dev/ttyUSB2` verificato.

### AutoAddressManager + BoxDriver

Con un CFS collegato, enumeration read-only ha trovato l'indirizzo 1 senza errori e ha letto correttamente slot/buffer/RFID/residuo.

### BoxStateReply

La patch nativa a `box_protocol.py` decodifica sia lo steady state K2 Pro a 4 byte sia gli eventi slot esistenti.

## Guardia observation

Un proxy limitato al CFS consente discovery/query note e blocca gli altri function code prima di `_write_frame`.

Non viene applicato globalmente a `serial_485.py`, perché lo stesso bus trasporta anche dispositivi closed-loop.

Il self-test su `0x0D` ha dimostrato che il contatore TX del transport non aumenta quando la richiesta viene bloccata.

## Test vera classe Box()

La classe Jacobean `Box()` è stata eseguita con `observation_mode: True` sul vero `/dev/ttyUSB2`.

Risultato:

- enumeration indirizzo 1;
- inizializzazione RFID/slot solo tramite letture;
- 10 letture live consecutive stabili;
- `_poll()` interno completato;
- `0x0D` bloccato prima del TX;
- **35 TX / 35 RX**;
- tutti i contatori errore a zero.

È attualmente il milestone CFS end-to-end più forte del progetto.

## Prossimo passo

Ripetere la stessa observation mode all'interno di un processo Kalico/Klippy completo sul CM5. I comandi CFS mutanti resteranno disabilitati fino alla stabilità dell'integrazione host completa.