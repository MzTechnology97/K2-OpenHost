# Roadmap di K2-OpenHost

Aggiornata il 31/10/2026.

## Fatto

- Kalico, Moonraker e Mainsail sull'host esterno, con i tre bus della K2 Pro portati attraverso il gadget USB della T113.
- Movimento, motori a circuito chiuso, PRTouch, riscaldatori, test delle risonanze e il cicalino originale dall'host.
- La CFS in pieno funzionamento: RFID (tag Creality, Bambu e altri MIFARE), libreria filamenti, filamento residuo, mappatura automatica, cambio a fine bobina, caricamento della bobina esterna, notifiche.
- Cartographer via USB diretto in modalità mista con il PRTouch.
- Il sistema dello slot B della T113: avvio senza i servizi di Creality, bridge, aggiornamento del firmware delle MCU, ritorno allo slot A.
- HelixScreen sullo schermo della stampante con il fork K2-OpenHost, con un'interfaccia sua per la CFS e la stampa.
- Lo script helper, il manifest delle release e il sito della documentazione.
- Uso quotidiano in produzione sulla stampante di riferimento dal 21/10/2026.

## Prossimi passi

- **HelixScreen 1.0.6-k2oh.8**: l'elenco dei filamenti preso direttamente da Kalico, la scheda di recupero della CFS, i nomi dei preset di Orca; poi le verifiche sullo schermo del [piano dei test](HARDWARE_TEST_PLAN.md) (T6). Il fork ha una sua [roadmap](https://github.com/MzTechnology97/helixscreen/blob/k2-openhost/docs/k2-openhost/ROADMAP.md).
- **Le prove di stampa che mancano**: una stampa a due colori, una pausa con cambio di slot, la ripresa dopo un'interruzione di corrente su una stampante senza UPS, il Cartographer come unica sonda.
- **Firmware della CFS**: R4 fino all'esaurimento completo di una bobina, poi decidere se sostituisce R3 come riferimento.
- **Una nuova immagine dello slot B e una release completa**, così un'installazione nuova ha subito il fork di HelixScreen, `k2oh-setup helix-update` e i programmi aggiornati.
- **Una seconda stampante**: un'installazione completa su un host nuovo, seguendo solo la documentazione.

## Non previsto

- Riprogrammare la MCU principale o dell'ugello di Creality senza un vero motivo.
- Sostituire elettronica della K2 che funziona.
- Pubblicare identificativi privati della CFS o dati RFID.
- Dare per scontato che la K2 Plus si comporti come la K2 Pro.
