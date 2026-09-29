# Roadmap

K2-OpenHost viene sviluppato in modo incrementale. Ogni fase deve essere validata prima di rendere persistenti modifiche più invasive o critiche per la sicurezza.

## Fase 0 — Preservare la possibilità di recovery

- Conservare un'immagine o slot stock noto e funzionante.
- Evitare modifiche persistenti finché i test a runtime non sono ripetibili.
- Documentare ogni modifica sysfs e ogni procedura di ripristino.

Stato: **in corso / parzialmente soddisfatto**.

## Fase 1 — Validare il collegamento Micro-USB a runtime

Obiettivo: dimostrare che il connettore Micro-USB service/recovery può trasportare un normale USB gadget Linux durante il runtime.

Attività:

1. Passare USB0 da host a device mode.
2. Eseguire `/bin/setusbconfig gser`.
3. Collegare la Micro-USB a un host Linux esterno.
4. Verificare l'enumerazione `0525:a4a6 Gadget Serial`.
5. Associare il driver generic usbserial se necessario.
6. Verificare `/dev/ttyUSB0` sull'host esterno.
7. Eseguire test di trasferimento bidirezionale.
8. Verificare disconnessione e riconnessione.

Stato: **prossimo test**.

## Fase 2 — Mappare i link MCU della K2 Pro

Obiettivo: identificare esattamente come Klipper stock raggiunge gli MCU della stampante.

Attività:

- identificare UART MCU principale;
- identificare UART MCU nozzle/toolhead;
- confermare baud rate e flow control;
- identificare i processi che mantengono aperte le porte;
- documentare reset line e comportamento al restart;
- determinare se altri bus o MCU richiedono accesso lato host.

Stato: **da eseguire**.

## Fase 3 — Creare un bridge seriale trasparente

Obiettivo: inoltrare byte del protocollo Klipper senza interpretarli.

Primo prototipo:

```text
/dev/ttyGS0 <-> processo bridge <-> /dev/ttySx
```

Requisiti:

- raw mode;
- nessuna trasformazione della line discipline;
- buffering minimo;
- gestione robusta della riconnessione;
- statistiche e logging disattivabili in produzione;
- startup/shutdown deterministici.

Si valuterà un piccolo daemon nativo o un tool di forwarding seriale opportunamente configurato. Latenza e buffering dovranno essere misurati prima della scelta definitiva.

Stato: **da eseguire**.

## Fase 4 — Handshake MCU con Kalico esterno

Obiettivo: eseguire Kalico sul Raspberry Pi / host Linux esterno mantenendo il firmware MCU originale K2.

Attività:

- installare `Jacob10383/kalico` sull'host esterno;
- creare una configurazione K2 minima;
- collegare inizialmente solo l'MCU principale;
- verificare identify/configure sequence;
- provare prima comandi non-motion;
- validare heater/fan/sensori solo dopo revisione pin/config;
- aggiungere MCU nozzle quando il link principale è stabile.

Stato: **da eseguire**.

## Fase 5 — Trasporto multi-MCU

Obiettivo: esporre simultaneamente tutti i link MCU necessari.

Target possibile:

```text
/dev/ttyUSB0 -> MCU principale
/dev/ttyUSB1 -> MCU nozzle
```

Attività:

- testare più funzioni `gser`;
- verificare nomi di enumerazione stabili;
- creare regole udev sull'host esterno;
- testare traffico concorrente e reconnect.

Stato: **da eseguire**.

## Fase 6 — HelixScreen sul display originale

Obiettivo: eliminare la dipendenza dalla UI Creality mantenendo display e touch originali.

Attività:

- installare/testare HelixScreen sul T113;
- verificare output framebuffer e input touch;
- collegare HelixScreen a Moonraker remoto;
- validare comandi base, stato stampa, temperature e selezione file;
- determinare quali servizi T113 restano necessari dopo la disattivazione della UI Creality.

Stato: **da eseguire**.

## Fase 7 — Integrazione Cartographer sull'host esterno

Obiettivo: collegare Cartographer direttamente al Raspberry Pi o altro host esterno.

Attività:

- spostare il collegamento USB se necessario;
- validare enumerazione MCU;
- validare probe/homing/mesh con Jacob10383 Kalico;
- rimuovere dipendenze T113 non necessarie.

Stato: **da eseguire**.

## Fase 8 — Motori closed-loop ed extras K2

Obiettivo: conservare le funzioni closed-loop e le altre caratteristiche hardware proprietarie K2.

Attività:

- mappare il percorso comandi realmente usato dagli extras motor-control;
- verificare se può essere riutilizzato il transparent forwarding esistente dell'MCU;
- validare comunicazione controller X/Y;
- validare tuning e telemetria;
- testare comportamento in caso di fault;
- documentare parametri e dipendenze.

Stato: **da eseguire**.

## Fase 9 — CFS

Obiettivo: mantenere o ripristinare il supporto CFS senza dipendere dall'intero stack host Creality.

Attività:

- identificare bus e componenti userspace richiesti;
- riutilizzare correttamente il reverse engineering pubblico esistente;
- validare reporting stato e operazioni filamento;
- integrare con Moonraker/HelixScreen.

Stato: **da eseguire**.

## Fase 10 — Strategia camera

Poiché USB0 viene usata dalla camera interna in host mode stock, OpenHost necessita di una soluzione definitiva per la camera.

Opzioni da valutare:

- collegare la camera originale direttamente all'host esterno;
- instradarla su un altro percorso USB host;
- modificare solo il collegamento della camera mantenendo il modulo originale;
- lasciare la camera disabilitata.

Stato: **decisione progettuale aperta**.

## Fase 11 — Automazione boot e fail-safe recovery

Solo dopo aver validato l'architettura a runtime:

- automatizzare USB role switching;
- avviare automaticamente le funzioni gadget;
- avviare i daemon bridge;
- avviare HelixScreen;
- implementare health check;
- definire il comportamento se il Raspberry è assente;
- mantenere una procedura semplice per tornare al funzionamento stock.

Stato: **futuro**.

## Fase 12 — Validazione di lunga durata

Necessaria prima di considerare il progetto utilizzabile:

- endurance link in idle;
- USB reconnect ripetuti;
- reboot ripetuti della stampante;
- cold boot;
- stampe multi-ora;
- G-code con altissimo numero di segmenti;
- workload ad alta accelerazione/frequenza comandi;
- test di sicurezza termica;
- gestione restart MCU;
- crash/reboot dell'host esterno.

Stato: **futuro**.
