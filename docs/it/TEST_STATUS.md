# Stato dei test

Ultimo aggiornamento: 31/10/2026.

La K2 Pro di riferimento (host CM5, una CFS) stampa ogni giorno con K2-OpenHost. Questa pagina elenca cosa è verificato su quella stampante e cosa resta aperto. Sono ancora sperimentali solo il firmware CFS modificato e il plugin di OrcaSlicer. Le procedure dei test aperti sono nel [piano dei test hardware](HARDWARE_TEST_PLAN.md).

## Verificato

| Area | Cosa funziona | Prima verifica |
| --- | --- | --- |
| Host | Kalico, Moonraker e Mainsail sul CM5 (AArch64); all'avvio Klipper aspetta i canali seriali della K2; dopo un riavvio del CM5 torna tutto da solo in circa 15 s | 03/10/2026 |
| Collegamento USB con il T113 | Tre canali seriali a USB 2.0 High-Speed (MCU principale, MCU ugello, RS-485). Su stampe lunghe: nessun byte perso nei bridge del T113, nessun errore CRC, circa un timeout RS-485 ogni 100.000 richieste, sempre recuperato. Misure in [Bridge USB](USB_BRIDGE.md) | 05/10/2026 |
| Movimento e homing | Movimenti CoreXY, homing X/Y sensorless, Z con PRTouch, motori X/Y/E a circuito chiuso senza errori | 03/10/2026 |
| Allineamento Z sul finecorsa inferiore (`z_align`) | Al primo tentativo ogni volta, delta 0, a 16 micropassi su Z. La stampante di riferimento ora lavora senza, perché è sotto UPS (vedi [Configurazione](reference/configuration.md)) | 03/10/2026 |
| Riscaldatori e sicurezza | Ugello, piatto e camera, taratura PID, arresto di emergenza con tutti i riscaldatori accesi | 03/10/2026 |
| Risonanze | Klippain ShakeTune con l'accelerometro dell'ugello | 04/10/2026 |
| CFS di base | Rilevamento e indirizzi, stato di slot e buffer, temperatura e umidità, carico e scarico (anche con gli assi non azzerati), notifiche su Mobileraker e Telegram | 05/10/2026 |
| RFID della CFS | Tag Creality e Bambu; un tag già noto viene riapplicato dalla cache degli UID senza rilettura; i tag sconosciuti vengono segnalati con il loro codice | 08/10/2026 |
| Filamento residuo | Stima di Kalico, conteggio dal vivo della CFS, geometria della bobina per produttore (firmware R3); il conteggio in millimetri di R4 avanza durante la stampa | 08/10/2026 |
| Mappatura automatica | I file di OrcaSlicer vengono mappati sugli slot caricati all'avvio della stampa; con bobine identiche parte da quella caricata o dalla prima nell'ordine di esaurimento | 05/10/2026 |
| Cambio automatico a fine bobina | La stampa passa da sola alla bobina identica successiva: 06/10, 15/10 e 16/10 (circa 45 s ciascuno), e più volte da allora | 06/10/2026 |
| Bobina esterna | Caricata a mano nel sensore della testa: Kalico la aggancia, chiede il profilo, scalda e spurga | 29/10/2026 |
| Stampe lunghe | 18 h 44 min (05/10), due da 30 h 12 min (15/10 e 17/10) e stampe quotidiane da allora | 05/10/2026 |
| Cartographer | Modalità mista: PRTouch fa l'homing di Z, il Cartographer scansiona la mesh via USB diretto. Dettagli in [Cartographer3D](CARTOGRAPHER.md) | 26/10/2026 |
| Slot B del T113 | Avvio senza i servizi Creality, schede avviate da `k2oh-mcu`, aggiornamento firmware delle MCU a Creality 1.1.7.0 dallo slot B | 06/10/2026 |
| HelixScreen | Il fork K2-OpenHost sullo schermo della stampante: pagina CFS e vista di stampa, colori dopo il reinserimento, filamento residuo, cambio bobina visto dal vivo, controllo aggiornamenti dal fork | 29/10/2026 |
| Ventola dell'host e telecamera | Ventola del CM5 gestita da Klipper; Creality CAM a 25 fps sul CM5 | 15/10/2026 |
| Watchdog RS-485 | Una perdita di 30 s a stampante ferma è stata segnalata e recuperata da sola | 05/10/2026 |

## Aperto

- **Stampa a due colori** avviata dalla finestra di mappatura di Mainsail: cambio utensile con la matrice di spurgo del file e temperature per utensile (T2).
- **Pausa con cambio di slot**, poi ripresa alla temperatura del nuovo filamento (seconda metà di T1).
- **Ripresa dopo un'interruzione di corrente** con `PLR_RECOVER`, a un colore e a due colori (T4). La stampante di riferimento è sotto UPS con la ripresa disattivata, quindi serve un'altra stampante o una prova sorvegliata.
- **Cartographer come unica sonda** (`register_as_probe: True`, T5).
- **Watchdog RS-485 durante una stampa**: finora è capitato solo a stampante ferma.
- **Rilevamento della CFS con RS-485 assente all'avvio di Klipper** (kalico-k2pro #24): coperto dai test, non visto dal vivo.
- **Firmware della CFS**: R4 fino all'esaurimento completo di una bobina; letture Bambu con CFG6 e tempi RFID originali.
- **HelixScreen 1.0.6-k2oh.8** sullo schermo: elenco dei filamenti da Kalico e salvataggio di un filamento nuovo, scheda touch con la configurazione fissa, fase di carico e scarico nella pagina CFS, scheda della bobina esterna, esclusione di un oggetto dalla mappa del piatto, scheda di recupero, aggiornamento dall'app e `k2oh-setup helix-restore` (T6).
- **Mappatura dal fork di OrcaSlicer di Jacob10383**: i suoi campi corrispondono allo stato della Box, non provato in stampa.
- **Pressure advance dalla cella di carico dell'ugello** (kalico-k2pro #29): archiviato, il modulo è spento.
