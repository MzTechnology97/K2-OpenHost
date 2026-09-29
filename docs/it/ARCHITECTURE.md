# Architettura K2-OpenHost

> Stato: progettazione in corso. Alcuni livelli sono già verificati su hardware reale, altri sono ancora pianificati.

## 1. Obiettivo del progetto

K2-OpenHost vuole mantenere l'elettronica originale della Creality K2 spostando però il carico principale lato host Klipper/Kalico su un sistema Linux esterno.

La suddivisione attualmente preferita è:

```text
LCD + touch originali K2
        |
        v
Mainboard Allwinner T113
- Tina Linux
- driver framebuffer/touch
- HelixScreen
- trasporto USB gadget
- servizi bridge MCU/UART
        |
        | USB 2.0
        v
Host Linux esterno
- Raspberry Pi / CM / altro SBC
- Jacob10383 Kalico
- Moonraker
- Mainsail / Fluidd
- Cartographer
- extras specifici K2
        |
        v
MCU originali K2
```

Il T113 rimane quindi parte integrante del sistema, ma passa dal ruolo di host principale a quello di companion leggero rivolto all'hardware.

## 2. Perché mantenere la scheda T113

La mainboard originale fornisce già accesso diretto ad hardware che altrimenti richiederebbe ricablaggio o ulteriore reverse engineering:

- display LCD originale;
- touchscreen originale;
- MCU principale di motion control;
- MCU nozzle/toolhead;
- camera e topologia USB interna;
- infrastruttura motori closed-loop;
- I/O e percorsi di alimentazione specifici della stampante.

Mantenendo il T113, K2-OpenHost evita di sostituire sia la mainboard sia il display.

## 3. Strategia display

Il progetto prevede attualmente di usare **HelixScreen** sul display originale K2 invece di mantenere l'intero stack UI proprietario Creality.

Il display resta fisicamente collegato al T113. Il Raspberry Pi non deve pilotare direttamente l'LCD.

Percorso UI previsto:

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

In questo modo non è necessario emulare le interfacce di `display-server`, `app-server` e `master-server` Creality.

## 4. Strategia motion-control

L'host esterno dovrà eseguire il vero stack host-side:

- Kalico / Klippy;
- Moonraker;
- extras K2;
- integrazione Cartographer;
- motion planning e componenti Python di livello superiore.

Gli MCU originali continueranno invece a occuparsi del lavoro real-time, come nella normale architettura Klipper.

Il trasporto obiettivo è concettualmente:

```text
Kalico su Raspberry Pi
        |
        | trasporto seriale USB gadget
        v
T113 /dev/ttyGSx
        |
        | bridge byte-transparent
        v
UART T113 /dev/ttySx
        |
        v
MCU originale K2
```

## 5. Trasporto USB

La K2 Pro utilizzata per i test espone un USB Device Controller Allwinner come:

```text
/sys/class/udc/4100000.udc-controller
```

L'immagine Tina stock include il supporto generic serial gadget e `/bin/setusbconfig gser` crea correttamente:

```text
/dev/ttyGS0
```

L'obiettivo è esporre uno o più canali seriali logici dal T113 verso l'host esterno.

Possibile mappatura finale:

```text
Host esterno
/dev/ttyUSB0  <---->  /dev/ttyGS0  <---->  UART MCU principale
/dev/ttyUSB1  <---->  /dev/ttyGS1  <---->  UART MCU nozzle
```

Il trasporto multi-canale non è ancora stato verificato.

## 6. Conflitto USB0 con la camera interna

I test hardware hanno confermato che USB0 viene normalmente utilizzata in host mode per la `CREALITY CAM` interna.

Modalità normale:

```text
T113 USB0
  |
  +-- EHCI0 / OHCI0
          |
          +-- CREALITY CAM
```

Modalità device:

```text
T113 USB0
  |
  +-- UDC 4100000.udc-controller
          |
          +-- connettore Micro-USB service/recovery (percorso fisico atteso)
```

Quando USB0 passa in device mode, la camera interna viene disconnessa. L'architettura finale dovrà quindi adottare una delle seguenti soluzioni:

1. spostare la camera sull'host esterno;
2. usare un altro percorso USB per la camera;
3. accettare la perdita della camera stock;
4. verificare l'eventuale presenza di switching o routing hardware alternativo.

La decisione finale non è ancora stata presa.

## 7. Cartographer

Sulla K2 Pro testata, Cartographer compare su USB1 tramite l'hub interno, non su USB0.

Questo è utile perché la commutazione host/device di USB0 non coinvolge il bus su cui si trova Cartographer.

La soluzione finale preferita resta comunque il collegamento diretto di Cartographer all'host esterno, se praticabile.

## 8. Servizi previsti sul T113

Set minimo previsto:

- kernel e driver hardware;
- driver framebuffer/display;
- driver touchscreen;
- HelixScreen;
- configurazione USB gadget;
- daemon bridge UART/MCU;
- solo gli helper di alimentazione/reset realmente necessari.

## 9. Servizi previsti sull'host esterno

- Kalico / Klippy;
- Moonraker;
- Mainsail e/o Fluidd;
- supporto host-side Cartographer;
- extras K2 e diagnostica;
- logging e strumenti di sviluppo.

## 10. Questioni ancora aperte

Restano da risolvere:

- device UART esatto dell'MCU principale K2 Pro;
- device UART esatto dell'MCU nozzle;
- possibilità di esporre più canali seriali contemporaneamente tramite ConfigFS `gser`;
- comportamento di buffering e latenza con traffico Klipper reale;
- percorso richiesto per i motori closed-loop;
- requisiti di trasporto CFS;
- affidabilità di lungo periodo della modalità USB gadget;
- strategia definitiva per la camera;
- sequenza di boot e recovery automatica.

Vedi [TEST_STATUS.md](TEST_STATUS.md) e [ROADMAP.md](ROADMAP.md) per lo stato attuale.
