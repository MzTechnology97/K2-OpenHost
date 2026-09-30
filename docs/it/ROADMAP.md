# Roadmap

K2-OpenHost viene sviluppato in modo incrementale. Ogni fase deve essere validata prima di rendere persistenti modifiche più invasive o critiche per la sicurezza.

## Fase 0 — Preservare la possibilità di recovery

- Conservare un'immagine o slot stock noto e funzionante.
- Evitare modifiche persistenti finché i test a runtime non sono ripetibili.
- Documentare ogni modifica sysfs e ogni procedura di ripristino.

Stato: **in corso / parzialmente soddisfatto**.

## Fase 1 — Validare il collegamento Micro-USB a runtime

Obiettivo: dimostrare che la porta Micro-USB service/recovery può trasportare un normale USB gadget Linux durante il runtime.

Completato:

- switch USB0 host -> device;
- enumerazione `0525:a4a6 Gadget Serial`;
- binding Linux `usbserial_generic`;
- trasferimento byte bidirezionale;
- link USB 2.0 High-Speed a 480M.

Stato: **completato per il trasporto base**.

I test di affidabilità residui sono spostati alla Fase 12.

## Fase 2 — Mappare i link hardware K2 Pro

Mappatura completata:

```text
/dev/ttyS2 -> Main MCU @ 230400
/dev/ttyS3 -> Nozzle MCU @ 230400
/dev/ttyS5 -> percorso RS-485 / closed-loop / CFS @ 230400
```

Stato: **completato per l'identificazione delle UART necessarie**.

## Fase 3 — Creare un bridge seriale trasparente

Prototipo Python runtime verificato per:

```text
/dev/ttyGS0 <-> /dev/ttyS2
/dev/ttyGS1 <-> /dev/ttyS3
/dev/ttyGS2 <-> /dev/ttyS5
```

Stato: **prototipo completato**.

Resta da fare:

- sostituire il prototipo con service/daemon production;
- gestione deterministica reconnect;
- health check/statistiche;
- startup/shutdown puliti.

## Fase 4 — Handshake MCU con Kalico esterno

Completato:

- Kalico esterno connesso al Main MCU originale;
- dictionary e telemetria Main MCU decodificati;
- Kalico esterno connesso al Nozzle MCU originale;
- dictionary e telemetria Nozzle MCU decodificati;
- nessun reflashing MCU necessario.

Stato: **completato per la connettività protocollo**.

## Fase 5 — Trasporto multi-MCU / multi-bus

Mappatura verificata:

```text
/dev/ttyUSB0 -> gser.usb0 -> ttyGS0 -> ttyS2 -> Main MCU
/dev/ttyUSB1 -> gser.usb1 -> ttyGS1 -> ttyS3 -> Nozzle MCU
/dev/ttyUSB2 -> gser.usb2 -> ttyGS2 -> ttyS5 -> RS-485
```

Completato:

- tre funzioni ConfigFS `gser` simultanee;
- tre interfacce host `usbserial_generic`;
- sessioni Main + Nozzle simultanee;
- terzo canale RS-485 attivo contemporaneamente.

Stato: **completato per la validazione funzionale**.

Resta da fare:

- naming host stabile / regole udev;
- automazione reconnect;
- traffico concorrente sostenuto.

## Fase 6 — HelixScreen sul display originale

Obiettivo: eliminare la dipendenza dalla UI Creality mantenendo display e touch originali.

Attività:

- installare/testare HelixScreen sul T113;
- verificare framebuffer e touch;
- collegare HelixScreen a Moonraker remoto;
- validare comandi base, stato stampa, temperature e selezione file;
- determinare i servizi T113 realmente necessari.

Stato: **da eseguire**.

## Fase 7 — Integrazione Cartographer sull'host esterno

Obiettivo: collegare Cartographer direttamente all'host esterno.

Attività:

- spostare il collegamento USB se necessario;
- validare enumerazione MCU;
- validare probe/homing/mesh con Kalico;
- rimuovere dipendenze T113 ridondanti.

Stato: **da eseguire**.

## Fase 8 — Motori closed-loop ed extras K2

Completato:

- dictionary Main e Nozzle stock confermati con `config_transparent` / `transparent_send`;
- log stock confermati con traffico reale `transparent_response`;
- `/dev/ttyS5` aperta direttamente a 230400 8N1;
- nessuna modalità Linux `TIOCSRS485` necessaria per il traffico testato;
- query read-only controller X (`0x81`) verificata direttamente sul T113;
- query X verificata end-to-end dall'host esterno;
- query Y (`0x82`) verificata end-to-end dall'host esterno.

Stato: **trasporto e accesso read-only X/Y verificati**.

Resta da fare:

- mappare solo le operazioni di scrittura strettamente necessarie;
- validare tuning/telemetria;
- validare fault handling;
- evitare scritture persistenti finché il protocollo non è completamente compreso.

## Fase 9 — CFS

Obiettivo: mantenere il supporto CFS senza dipendere dall'intero stack host Creality.

Stato attuale:

- UART host identificata come `/dev/ttyS5`;
- trasporto dall'host esterno verso la UART già verificato;
- i primi probe A1/A2 sono stati eseguiti mentre il CFS era fisicamente scollegato e sono quindi inconclusivi.

Prossimi test:

- collegare il CFS;
- ripetere online-check/discovery;
- acquisire e documentare le risposte;
- validare reporting stato prima di qualsiasi comando che cambi indirizzo o muova il filamento;
- successivamente integrare con Moonraker/HelixScreen.

Stato: **prossima validazione hardware**.

## Fase 10 — Strategia camera

Poiché USB0 viene usata dalla camera interna in modalità host stock, OpenHost necessita di una soluzione definitiva.

Opzioni:

- collegare la camera originale direttamente all'host esterno;
- instradarla su un altro percorso USB host;
- modificare solo il collegamento camera;
- lasciare la camera disabilitata.

Stato: **decisione progettuale aperta**.

## Fase 11 — Automazione boot e fail-safe recovery

Solo dopo la validazione dell'architettura runtime:

- automatizzare USB role switching;
- creare automaticamente tutte e tre le funzioni gadget;
- avviare/riavviare i bridge;
- rilevare la presenza dell'host esterno;
- aggiungere health check;
- preservare un recovery stock semplice.

Stato: **futuro**.

## Fase 12 — Validazione di lunga durata

Necessaria prima di considerare il progetto utilizzabile:

- endurance idle;
- traffico sostenuto su tutti e tre i canali;
- reconnect USB ripetuti;
- unbind/rebind gadget ripetuti;
- reboot e cold boot ripetuti;
- stampe multi-ora;
- workload ad alta frequenza comandi;
- gestione restart MCU;
- crash/reboot dell'host esterno;
- validazione termica e fail-safe.

Stato: **futuro**.
