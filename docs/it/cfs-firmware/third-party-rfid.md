# Tag RFID di terze parti

Il firmware CFS stock legge solo i tag RFID Creality. Con un firmware **API7** il CFS permette a Kalico di identificare le bobine **Bambu Lab** e altre **MIFARE Classic 1K** (QIDI, tag in stile OpenTag) **senza mai scrivere il tag**.

## Quale firmware ha API7

API7 (cattura con il task stock, caps `0xE8`) è stata validata con la v3.3 ed è presente nella v3.12. La v3.22 mantiene la cattura API7 della v3.12, e le immagini CFG4/CFG5T/CFG6 sono costruite dal builder della v3.22. Controlla il tuo CFS:

```text
BOX_RFID_DIAG_INFO
```

Atteso: `API=7`, `readers=2`, `slots/reader=2`, `caps=0xE8`. Su un firmware senza API7 il fallback automatico si spegne da solo fino al successivo avvio di Klipper: non si rompe nulla.

## Come funziona una lettura

1. Il CFS fa la sua normale lettura Creality. **Un tag Creality vince sempre.**
2. Solo se il record è vuoto o sconosciuto, Kalico guarda UID, ATQA e SAK che il CFS ha già catturato (nessuna lettura RF in più). Uno slot senza tag, o un tag che non è MIFARE Classic 1K, si ferma qui.
3. I decoder dei produttori girano per priorità (**Bambu**, poi **MIFARE**/QIDI). Ogni tentativo è una rilettura stock completa del CFS (circa 45 s, con il bus RS-485 occupato nel frattempo). Se il CFS sta ancora leggendo uno slot, la lettura Bambu aspetta fino a 15 s che il gestore RFID stock si liberi, poi fallisce con `CFS stock RFID manager is busy`; se resta occupato per minuti, spegni e riaccendi il CFS.
4. Materiale e colore decodificati selezionano un profilo filamento dalla libreria; l'UID viene memorizzato, così il prossimo inserimento di quella bobina non richiede rilettura.

Mai durante una stampa, una pausa, un'altra operazione del box, o con il filamento caricato verso la testina.

## Attivarlo

Gli extra richiedono API7, quindi il `printer.cfg` generico tiene commentati i loro include. Su un CFS con API7 togli il commento:

```ini
[include macros/box_rfid_diag.cfg]
[include macros/box_rfid_bambu.cfg]
[include macros/box_rfid_mifare.cfg]
```

e in `[box]` (entrambi predefiniti a `True`):

```ini
[box]
auto_bambu_rfid_fallback: True
auto_mifare_rfid_fallback: True
rfid_fallback_budget: 1          # riletture per inserimento di bobina (0 = solo cache)
rfid_fallback_manual_budget: 3   # riletture per slot su una rilettura manuale
```

`allow_active_rf: false` in `[box_rfid_diag]` è voluto: il percorso normale usa il task RFID di Creality, non i vecchi comandi RF diretti.

## Bobine validate

Tag Bambu Lab letti su hardware: PLA Matte, PETG HF, PETG Basic, ABS, ASA, ASA-CF, PAHT-CF, ABS-GF, PETG-CF, PC. QIDI: PET-CF.

## Associare un tag al tuo profilo

```text
_BOX_RFID_ASSOCIATE SLOT=<slot-globale> FILAMENT_ID=<id-libreria>
```

Le letture successive di quel tipo di tag (per esempio `BAMBU:PETG HF`) usano temperature, pressure advance e flusso massimo del tuo profilo, mantenendo il colore del tag.

## Filamento residuo

Il CFS stock restituisce `0xFF` (nessun valore) per i tag di terze parti, quindi la loro percentuale arriva dalla [stima di Kalico](remaining.md), oppure dal CFS stesso con CFG5T/CFG6 e il conteggio type-4 in tempo reale.

## Comandi

| Comando | Uso |
| --- | --- |
| `_BOX_RFID_READ_SLOT SLOT=<n>` | Rilegge uno slot (va diretto al decoder noto quando l'UID è in cache) |
| `BOX_RFID_BAMBU_READ SLOT=<n>` | Forza una lettura Bambu, con una riga di log dettagliata |
| `BOX_RFID_MIFARE_READ SLOT=<n>` | Forza una lettura MIFARE generica |
| `_BOX_RFID_FALLBACK_CACHE [CLEAR=1] [UID=<hex>]` | Mostra o svuota la cache degli UID |
| `BOX_RFID_DIAG_INFO`, `_RUNTIME`, `_STATE` | Diagnostica passiva |

Dettagli completi: [CFS_RFID_BAMBU.md](https://github.com/MzTechnology97/kalico-k2pro/blob/k2-pro-openhost/docs/CFS_RFID_BAMBU.md).
