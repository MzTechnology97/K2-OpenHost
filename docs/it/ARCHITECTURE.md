# Architettura K2-OpenHost

> Stato: progettazione in corso. Il trasporto principale verso host esterno è ora verificato su hardware; UI, automazione boot, CFS e validazione di lunga durata restano in corso.

## 1. Obiettivo del progetto

K2-OpenHost vuole mantenere l'elettronica originale della Creality K2 spostando il carico principale lato host Klipper/Kalico su un sistema Linux esterno.

La suddivisione preferita è:

```text
LCD + touch originali K2
        |
        v
Mainboard Allwinner T113
- Tina Linux
- driver framebuffer/touch
- futuro HelixScreen
- trasporto USB gadget
- servizi bridge UART byte-transparent
        |
        | USB 2.0 High-Speed
        v
Host Linux esterno
- Kalico / Klippy
- Moonraker
- Mainsail / Fluidd
- extras specifici K2
        |
        +-------------------+-------------------+
        |                   |                   |
        v                   v                   v
     Main MCU           Nozzle MCU          bus RS-485
                                            X/Y + CFS
```

Il T113 rimane parte integrante del sistema, ma passa dal ruolo di host principale a companion leggero rivolto all'hardware.

## 2. Perché mantenere la scheda T113

La mainboard originale fornisce già accesso diretto ad hardware che altrimenti richiederebbe ricablaggio o ulteriore reverse engineering:

- display LCD originale;
- touchscreen originale;
- Main MCU;
- Nozzle MCU;
- topologia USB interna;
- percorso RS-485 usato dall'infrastruttura closed-loop/CFS;
- I/O e percorsi di alimentazione specifici della stampante.

Mantenendo il T113, K2-OpenHost può preservare display e mainboard originali spostando altrove il carico host-side.

## 3. Strategia display

La strategia UI preferita resta:

```text
LCD/touch originali
      |
      v
T113 + HelixScreen
      |
      | rete
      v
Moonraker sull'host esterno
      |
      v
Kalico
```

Il display resta fisicamente collegato al T113. L'host Linux esterno non deve pilotare direttamente il pannello.

## 4. Strategia motion-control

L'host esterno dovrà eseguire:

- Kalico / Klippy;
- Moonraker;
- extras K2;
- motion planning e componenti Python di livello superiore;
- supporto host-side Cartographer.

Gli MCU originali K2 continueranno a svolgere il lavoro real-time.

## 5. Trasporto USB a tre canali verificato

Il T113 della K2 Pro può esporre tre funzioni ConfigFS Generic Serial simultanee attraverso la porta Micro-USB service/recovery:

```text
gser.usb0 -> /dev/ttyGS0
gser.usb1 -> /dev/ttyGS1
gser.usb2 -> /dev/ttyGS2
```

L'host Linux esterno enumera tre interfacce seriali indipendenti a USB 2.0 High-Speed (480M):

```text
/dev/ttyUSB0
/dev/ttyUSB1
/dev/ttyUSB2
```

Mappatura verificata:

```text
Host esterno                T113                       Hardware

/dev/ttyUSB0 <--------> /dev/ttyGS0 <--------> /dev/ttyS2 <--> Main MCU
/dev/ttyUSB1 <--------> /dev/ttyGS1 <--------> /dev/ttyS3 <--> Nozzle MCU
/dev/ttyUSB2 <--------> /dev/ttyGS2 <--------> /dev/ttyS5 <--> RS-485
```

Il bridge è attualmente un prototipo Python runtime byte-transparent. Per il deployment finale servirà un daemon/service dedicato.

## 6. Validazione Main e Nozzle MCU

Kalico sull'host esterno ha stabilito sessioni protocollo reali con entrambi gli MCU originali K2 Pro attraverso il bridge T113:

- Main MCU: `gd32f303xe` via `/dev/ttyS2`, 230400 baud;
- Nozzle MCU: `gd32f303xb` via `/dev/ttyS3`, 230400 baud.

Entrambi i canali sono stati usati contemporaneamente senza riflashare gli MCU.

## 7. Percorso RS-485 e closed-loop

Il terzo canale bridge espone `/dev/ttyS5` direttamente all'host esterno.

Sono state verificate end-to-end query read-only verso entrambi i controller closed-loop:

```text
X (0x81): risposta verificata
Y (0x82): risposta verificata
```

Per il traffico testato, `/dev/ttyS5` funziona come normale seriale 230400 8N1 senza configurazione Linux `TIOCSRS485` né toggle RTS esplicito in userspace.

Questo dimostra che l'host esterno può raggiungere direttamente il bus controller X/Y attraverso il T113 senza necessità di un proxy RS-485 aggiuntivo.

I dictionary MCU originali espongono anche i comandi transparent serial di Creality. I log stock storici ne confermano l'uso, ma il bridge diretto del terzo canale verso `/dev/ttyS5` è il percorso esterno attualmente verificato per la comunicazione read-only X/Y.

## 8. Percorso CFS

La configurazione stock associa anche il CFS alla stessa UART RS-485 `/dev/ttyS5`.

L'host esterno dispone quindi già di un percorso di trasporto verificato verso il bus corretto. La validazione protocollo con CFS collegato resta da eseguire. I primi probe senza risposta sono stati effettuati mentre il CFS era fisicamente scollegato e non vengono considerati fallimenti.

## 9. Conflitto USB0 e topologia USB fisica ancora da verificare

USB0 viene normalmente usata come host per la `CREALITY CAM` interna. La commutazione in device mode disconnette la camera.

Resta aperta un'ulteriore verifica hardware: la relazione esatta tra la porta USB-A esposta esternamente, la `CREALITY CAM` interna e la porta Micro-USB service/recovery utilizzata per il collegamento OpenHost. Non è ancora confermato se la porta USB-A esterna condivida lo stesso hub/controller fisico o appartenga a un ramo USB distinto.

Questa topologia deve essere mappata prima di definire in modo definitivo la strategia camera/USB esterna.

## 10. Cablaggio Cartographer sull'unità di test attuale

La K2 Pro usata per i test riutilizza intenzionalmente il collegamento USB interno originariamente destinato alla camera nozzle sulla Nozzle MCU/toolhead.

Cablaggio attuale:

```text
Connettore USB interno camera nozzle su Nozzle MCU/toolhead
                     |
                     v
                Cartographer
```

La camera nozzle stock non è quindi installata/utilizzata su questa unità. La camera è associata al workflow Creality di calibrazione automatica legato a flusso/pressure, funzione non necessaria nella configurazione attuale della macchina.

Questa scelta offre due vantaggi pratici:

- Cartographer usa un percorso USB interno già disponibile, evitando un ulteriore cavo esterno;
- l'unica porta USB esposta esternamente sulla stampante resta libera per altri utilizzi.

Si tratta di una **scelta implementativa dell'unità di test**, non di un requisito generale di K2-OpenHost. Altre installazioni possono mantenere la camera nozzle e collegare Cartographer in modo differente.

Resta da verificare la relazione a monte tra questo percorso USB interno, la porta USB-A esterna e il collegamento Micro-USB OpenHost.

## 11. Servizi previsti sul T113

Set minimo previsto:

- kernel e driver hardware;
- driver framebuffer/display;
- driver touchscreen;
- HelixScreen;
- configurazione USB gadget;
- daemon bridge UART byte-transparent;
- solo gli helper hardware di alimentazione/reset/controllo realmente necessari.

## 12. Servizi previsti sull'host esterno

- Kalico / Klippy;
- Moonraker;
- Mainsail e/o Fluidd;
- supporto host-side Cartographer;
- extras K2 e diagnostica;
- logging e strumenti di sviluppo.

## 13. Comportamento reconnect

Un unbind/rebind del gadget ConfigFS ricrea gli endpoint `/dev/ttyGS*`. I processi bridge con file descriptor già aperti terminano quindi e devono essere riavviati dopo il rebind.

Il service manager OpenHost finale dovrà gestire:

- creazione gadget;
- enumerazione host;
- avvio bridge;
- restart bridge dopo reconnect USB;
- naming deterministico;
- fallback sicuro quando l'host esterno non è disponibile.

## 14. Questioni ancora aperte

Identificazione UART e trasporto multi-canale non sono più questioni aperte. Restano:

- validazione CFS con hardware collegato;
- mappatura della topologia USB fisica tra porta USB-A esterna, `CREALITY CAM`, percorso camera-nozzle/Cartographer e Micro-USB service/recovery;
- traffico multi-canale sostenuto e durante stampa;
- reconnect/re-enumeration robusti;
- implementazione production del bridge;
- sequenza di boot e recovery automatica;
- integrazione HelixScreen;
- validazione del percorso USB interno Cartographer durante funzionamento OpenHost completo;
- strategia camera definitiva;
- validazione operazioni di tuning/scrittura motori;
- test di sicurezza e affidabilità di lunga durata.

Vedi [TEST_STATUS.md](TEST_STATUS.md) e [ROADMAP.md](ROADMAP.md) per lo stato attuale.
