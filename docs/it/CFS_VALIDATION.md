# Protocollo della CFS sulla K2 Pro

Cosa fa la CFS della K2 Pro sul bus RS-485, verificato sulla stampante di riferimento. Lo stack della Box viene dal firmware K2 di Jacob10383; K2-OpenHost aggiunge le differenze della K2 Pro descritte qui. Identificativi privati e contenuti dei tag RFID non sono pubblicati.

## Trasporto

La CFS condivide il bus RS-485 con i motori X/Y a circuito chiuso, a 230400 baud. K2-OpenHost lo porta sul terzo canale del gadget:

```text
host /dev/serial/by-id/...-if02 <-> T113 /dev/ttyGS2 <-> /dev/ttyS5 <-> CFS e motori
```

## Indirizzi

- Intestazione del frame `0xF7`, indirizzo di broadcast `0xFE`.
- Il rilevamento A1 restituisce un identificativo stabile di 12 byte; A0 assegna l'indirizzo `0x01`; A2 controlla che l'unità sia in linea; A3 legge la tabella degli indirizzi.
- Dopo uno spegnimento la CFS risponde a `0xFE` finché non viene enumerata di nuovo, quindi Kalico interroga la sua configurazione runtime solo dopo `box:ready`.

## Stato della Box (comando `0x0A`)

La lunghezza della risposta dipende dal firmware della CFS:

| Firmware CFS | Risposta | Decodificata da |
| --- | --- | --- |
| 1.1.3 | 4 byte: temperatura (con segno, °C), umidità (%), evento, stato della box | `box_k2pro` |
| 1.5.3 (`cfs0_000_153`, con le schede 1.1.7.0) | 6 byte: temperatura, umidità, evento, stato della box, maschera degli slot | il percorso originale di `box_protocol.py` |

`box_k2pro` gestisce solo le risposte da 4 byte e lascia passare le altre lunghezze, quindi entrambe le versioni del firmware funzionano con la stessa configurazione. `boxes[].state_payload_bytes` riporta la lunghezza dell'ultima risposta per unità.

Risposte grezze da 1.5.3 (`BOX_DEBUG RAW=1`): ferma e vuota `1d 26 00 00 00 00` (29 °C, 38 %, stato IDLE, nessuno slot); slot 1 caricato fino all'ugello `1d 26 00 02 01 00` (stato PRINT, maschera degli slot `0x01`). Lo slot caricato viene quindi dalla CFS stessa; il sensore della testa serve solo quando nessuna unità ne riporta uno.

## Modalità osservazione

`observation_mode: True` in `[box]` fa girare il vero stack della CFS in sola lettura, per un primo test su una stampante nuova o dopo un cambio di firmware:

- un proxy lascia passare solo il rilevamento e le letture note, e blocca ogni altro codice funzione della CFS prima dell'invio (verificato: un `0x0D` bloccato non è mai arrivato al trasporto);
- nessun comando `BOX_*` né `T0`, `T1`..., nessun aggancio al sensore di taglio o al fine bobina, nessuna scrittura RFID all'avvio;
- lo stato resta in `/dev/shm`, se non indicato diversamente.

La protezione riguarda solo la CFS: i motori sullo stesso bus continuano a funzionare. Sulla stampante di riferimento ha enumerato l'indirizzo 1, letto slot e RFID e fatto dieci letture di stato con 35 frame inviati e 35 ricevuti, senza errori. Il funzionamento normale è `observation_mode: False`.

## Sorgenti

Il codice è in [kalico-k2pro](https://github.com/MzTechnology97/kalico-k2pro), ramo `k2-pro-openhost`. Il punto di partenza è stato il reverse engineering pubblico (le estensioni K2 di Creality, il firmware di Jacob10383, `gitstonelabs/creality-cfs-klipper`); la stampante ha confermato dove la K2 Pro è diversa. Cos'altro è verificato con la CFS è nello [stato dei test](TEST_STATUS.md).
