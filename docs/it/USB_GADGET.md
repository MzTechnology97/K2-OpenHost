# Trasporto USB Gadget sulla K2 Pro

Aggiornato al **1 ottobre 2026**.

## Dati verificati

Il T113 della K2 Pro espone l'USB Device Controller `4100000.udc-controller`. Il kernel include ConfigFS/libcomposite e supporto Generic Serial gadget.

Sono state verificate **tre funzioni seriali simultanee**:

- `gser.usb0` -> `/dev/ttyGS0`
- `gser.usb1` -> `/dev/ttyGS1`
- `gser.usb2` -> `/dev/ttyGS2`

Il CM5/host esterno vede il device composito come tre interfacce `usbserial_generic`, attualmente `/dev/ttyUSB0..2`. Enumerazione verificata a USB 2.0 High-Speed (**480M**).

## Mappatura verificata

```text
/dev/ttyUSB0 <-> ttyGS0 <-> ttyS2 <-> Main MCU
/dev/ttyUSB1 <-> ttyGS1 <-> ttyS3 <-> Nozzle MCU
/dev/ttyUSB2 <-> ttyGS2 <-> ttyS5 <-> RS-485 / CFS / closed-loop
```

Main, Nozzle e RS-485 operano a 230400 baud nella configurazione validata.

## Ruolo finale del gadget

Le tre funzioni seriali gadget restano volutamente dedicate ai tre percorsi hardware K2 originali.

È stato prototipato un quarto percorso Cartographer tramite MUX/DEMUX custom. L'esperimento ha dimostrato che dati MCU Cartographer reali possono attraversare T113 e gadget USB, ma reset/re-enumeration cambia la PTY lato T113 e introduce complessità di reconnect non necessaria.

Per questo il progetto **non prevede più `ttyGS3` / `/dev/ttyUSB3` come percorso finale Cartographer**. Cartographer va collegato direttamente alla USB host del CM5 usando un path persistente `/dev/serial/by-id/...`.

## Requisito di ownership dei processi

Ogni coppia UART/gadget deve avere esattamente un processo bridge. Durante l'esperimento di multiplexing Cartographer è stato trovato un bridge GS2 duplicato che apriva `ttyGS2`/`ttyS5` mentre era attivo anche un altro transport. Questo ha causato failure RS-485/motor-control.

Rimuovendo il duplicato e ripristinando un solo bridge diretto GS2, la comunicazione closed-loop è tornata normale.

Topologia stabile:

```text
un processo: ttyGS0 <-> ttyS2
un processo: ttyGS1 <-> ttyS3
un processo: ttyGS2 <-> ttyS5
```

Non eseguire il vecchio MUX Cartographer su GS2 contemporaneamente.

## Nota sul cambio ruolo USB

USB0 è dual-role. In modalità stock fa parte della topologia host USB interna, inclusa la camera. Il passaggio a device/gadget modifica quindi la topologia stock e può scollegare la camera. I test runtime sono progettati per essere reversibili con reboot.

Unbind/rebind del gadget ricrea i device `ttyGS*`; i processi bridge devono essere riavviati.

## Modello bridge

Il bridge stabile è byte-transparent. Il T113 non interpreta i protocolli Klipper/CFS; il CM5 resta planner/Python host mentre il T113 agisce da gateway hardware per i bus originali K2.

## Utilizzo downstream già validato

Con questi tre canali la K2 Pro reale ha già completato da host esterno:

- sessioni simultanee Main + Nozzle MCU;
- comunicazione closed-loop X/Y;
- movimenti CoreXY normali;
- homing stall X/Y;
- homing completo PRTouch;
- heater bed/nozzle/chamber;
- emergency heater shutdown;
- test risonanza Klippain-ShakeTune;
- traffico CFS observation protetto.

## Cosa non viene dichiarato

- La topologia USB fisica di ogni connettore non è completamente mappata per ogni variante K2.
- Il packaging di boot persistente è ancora in evoluzione.
- La validazione Cartographer direct-USB è un milestone separato e non passa attraverso i tre canali gadget.