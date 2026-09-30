# Trasporto USB Gadget sulla K2 Pro

## Dati verificati

Il T113 della K2 Pro espone l'USB Device Controller `4100000.udc-controller`. Il kernel include ConfigFS/libcomposite e il supporto Generic Serial gadget.

Sono state verificate **tre funzioni seriali simultanee**:

- `gser.usb0` -> `/dev/ttyGS0`
- `gser.usb1` -> `/dev/ttyGS1`
- `gser.usb2` -> `/dev/ttyGS2`

Il CM5/host esterno vede il device composito come tre interfacce `usbserial_generic`, attualmente `/dev/ttyUSB0..2`. Enumerazione verificata a **480M**.

## Mappatura verificata

```text
/dev/ttyUSB0 <-> ttyGS0 <-> ttyS2 <-> Main MCU
/dev/ttyUSB1 <-> ttyGS1 <-> ttyS3 <-> Nozzle MCU
/dev/ttyUSB2 <-> ttyGS2 <-> ttyS5 <-> RS-485 / CFS
```

Main, Nozzle e RS-485 operano a 230400 baud nei test correnti.

## Nota sul cambio ruolo USB

USB0 è dual-role. In modalità stock fa parte della topologia host USB interna, inclusa la camera di camera. Il passaggio a device/gadget modifica quindi la topologia stock e può scollegare la camera. I test runtime sono progettati per essere reversibili con reboot.

Unbind/rebind del gadget ricrea i device `ttyGS*`; i processi bridge devono essere riavviati.

## Modello bridge

Il bridge corrente è byte-transparent. Il T113 non deve interpretare i protocolli Klipper/CFS salvo future necessità hardware specifiche.

## Quarto canale previsto

Sulla K2 Pro di test Cartographer usa internamente il percorso USB originariamente destinato alla camera toolhead/nozzle. Il prossimo obiettivo è esporre quel device seriale con `gser.usb3` verso un futuro `/dev/ttyUSB3` sul CM5.

Il traffico Cartographer normale dovrebbe essere compatibile con un bridge seriale, ma bootloader/firmware update potrebbero dipendere da semantiche USB/control-line non preservate automaticamente. Questa parte deve ancora essere verificata.