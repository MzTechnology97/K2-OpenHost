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

La prima patch di validazione manteneva i primi due byte opachi come `firmware_base` ed esponeva `substatus` / `load_flag`. L'analisi del firmware CFS 1.1.3 e le catture live hanno poi stabilito il layout, ora decodificato dall'adattatore `box_k2pro`: temperatura con segno in °C, umidità in %, byte evento e stato del box.

I valori registrati allora come basi opache (`0x1E22`, `0x1E23`, `0x1F23`) sono coerenti: 30–31 °C e 34–35 % di umidità. I campi opachi restano solo come ripiego in `box_protocol.py` quando `[box_k2pro]` non è caricato. Il percorso 6-byte e gli eventi asincroni `STATUS=0x30` restano compatibili.

### Firmware CFS 1.5.3: di nuovo 6 byte

Dopo l'aggiornamento delle schede a Creality 1.1.7.0 (applicazione CFS `cfs0_000_153`, riportata come 1.5.3), lo stesso CFS risponde al comando `0x0A` con il payload originale a 6 byte. Verificato il 2026-10-07 tramite `boxes[].state_payload_bytes` (kalico-k2pro PR #35), che riporta la lunghezza dell'ultima risposta per unità: `6`, con 29 °C e 38 % di umidità.

La risposta a 6 byte è decodificata dal percorso Jacobean originale in `box_protocol.py`: temperatura con segno, umidità, stato del box e maschera degli slot. `box_k2pro` gestisce solo le risposte a 4 byte e lascia passare le altre lunghezze, quindi entrambe le versioni del firmware funzionano con la stessa configurazione. Il percorso a 4 byte serve ancora per un CFS su 1.1.3, per esempio dopo un avvio dallo slot A, che scrive sulle schede i propri file firmware 1.1.0.94.

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

Questo milestone resta la baseline di sicurezza in sola lettura.

## Validazione in modalità operativa

Il processo Kalico completo sul CM5 esegue ora il Box stack con `observation_mode: false`. Sulla K2 Pro reale sono stati verificati:

- enumeration CFS e stato normalizzato con `driver_ready=true` / `data_ready=true`;
- temperatura e umidità del CFS tramite adattatore K2 Pro;
- inventario filamenti persistente e import del database materiali Creality/K2-RFID;
- risoluzione automatica degli ID materiale K2-RFID custom senza creare un nuovo profilo quando cambia soltanto il colore della bobina;
- rilettura RFID forzata per singolo slot;
- percentuale residua riportata dal CFS;
- stime residue indipendenti per bobine fisiche diverse anche quando i tag K2-RFID usano lo stesso seriale `000001`;
- ordinamento dei gruppi runout usando per primi gli slot compatibili con percentuale residua minore.

Un ID RFID custom Bambulab PLA Basic è stato risolto realmente su due bobine di colore diverso. Il CFS ha riportato rispettivamente 9% e 10%; OpenHost le mantiene indipendenti come circa 29,7 m e 33,0 m residui su una lunghezza taggata di 330 m.

Lo stimatore live sottrae inoltre i delta positivi di `print_stats.filament_used` dalla bobina RFID attiva e persiste la stima. La logica è implementata e verificata sul codice; resta da validarne l'andamento durante una stampa completa supervisionata.

## Prossimo passo

Il prossimo milestone CFS è un `BOX_PRINT_START` mappato e controllato, seguito da cambio materiale reale, test runout/recovery e stampa completa supervisionata.