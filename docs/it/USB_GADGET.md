# Indagine USB Gadget e Micro-USB

> Ambito: unità di test Creality K2 Pro. Questo documento separa le osservazioni verificate direttamente dalle ipotesi ancora da validare.

## 1. Scoperta iniziale

La K2 Pro espone un USB Device Controller Allwinner:

```text
/sys/class/udc/4100000.udc-controller
```

La configurazione kernel dell'unità testata include:

```text
CONFIG_USB_GADGET=y
CONFIG_USB_LIBCOMPOSITE=y
CONFIG_USB_F_SERIAL=y
CONFIG_USB_CONFIGFS=y
CONFIG_USB_CONFIGFS_UEVENT=y
CONFIG_USB_CONFIGFS_SERIAL=y
CONFIG_USB_CONFIGFS_F_FS=y
```

CDC ACM non risulta abilitato nel kernel testato, ma Generic Serial è integrato e utilizzabile.

## 2. Ruolo normale di USB0

In modalità stock USB0 opera come host per la camera interna. I controller host sono:

```text
4101000.ehci0-controller
4101400.ohci0-controller
```

Il passaggio di USB0 in device mode disconnette correttamente la camera e rimuove i controller host.

## 3. Commutazione USB0 in device mode

Il driver OTG vendor espone i controlli runtime sotto:

```text
/sys/devices/platform/soc@3000000/soc@3000000:usbc0@0
```

La lettura di `usb_device` commuta USB0 in device mode. Sull'unità testata ha restituito:

```text
device_chose finished!
```

L'operazione è runtime-only; un reboot ripristina il normale comportamento USB host stock.

## 4. Generic Serial gadget vendor

Il tool stock:

```text
/bin/setusbconfig
```

supporta `gser`. Eseguendo:

```sh
/bin/setusbconfig gser
```

viene creata la prima funzione:

```text
functions/gser.usb0
/dev/ttyGS0
```

con:

```text
VID:     0x0525
PID:     0xa4a6
Product: Gadget Serial
UDC:     4100000.udc-controller
```

## 5. Collegamento fisico Micro-USB

Con un host Linux esterno collegato alla porta Micro-USB service/recovery della K2 Pro, il gadget viene enumerato correttamente a USB 2.0 High-Speed:

```text
480M
```

Lato host viene usato il driver Linux `usbserial_generic`. Dopo il binding di VID:PID `0525:a4a6` vengono esposti i device `/dev/ttyUSB*`.

Il trasferimento bidirezionale tra `/dev/ttyUSB0` e `/dev/ttyGS0` è stato verificato.

## 6. Tre funzioni Generic Serial simultanee

ConfigFS è stato esteso a runtime con altre due funzioni seriali:

```text
gser.usb0  port_num=0  -> /dev/ttyGS0
gser.usb1  port_num=1  -> /dev/ttyGS1
gser.usb2  port_num=2  -> /dev/ttyGS2
```

Le tre funzioni sono state collegate alla stessa configurazione e ribindate allo stesso UDC.

L'host Linux esterno ha quindi enumerato un singolo device USB con tre interfacce vendor-specific:

```text
If 0 -> usbserial_generic -> /dev/ttyUSB0
If 1 -> usbserial_generic -> /dev/ttyUSB1
If 2 -> usbserial_generic -> /dev/ttyUSB2
```

Il collegamento è rimasto negoziato a 480M.

Questo verifica direttamente che kernel e ConfigFS stock della K2 Pro possono esporre almeno tre canali Generic Serial simultanei attraverso la singola Micro-USB fisica.

## 7. Mappatura UART verificata attraverso il gadget

Sul T113 sono stati usati bridge runtime byte-transparent:

```text
/dev/ttyGS0 <-> /dev/ttyS2   Main MCU
/dev/ttyGS1 <-> /dev/ttyS3   Nozzle MCU
/dev/ttyGS2 <-> /dev/ttyS5   bus RS-485
```

Tutte e tre le UART sono usate a 230400 baud nella configurazione stock testata.

Le sessioni protocollo Main e Nozzle sono state verificate simultaneamente da Kalico esterno, senza riflashare gli MCU originali.

## 8. RS-485 sul terzo canale USB

`/dev/ttyS5` è stata testata prima localmente sul T113 e poi attraverso il percorso completo dall'host esterno.

Lo stato ioctl RS-485 Linux risulta disabilitato:

```text
SER_RS485_ENABLED = false
```

Nonostante ciò, la normale I/O seriale userspace 230400 8N1 funziona correttamente per il traffico testato. Non è stato necessario configurare `TIOCSRS485` né gestire RTS esplicitamente.

Una query read-only verso il controller closed-loop X inviata direttamente su `/dev/ttyS5` ha restituito:

```text
TX: f7 81 04 00 0e 02 80
RX: f7 81 04 00 0e 81 00
```

La stessa query ha poi funzionato dall'host esterno attraverso:

```text
/dev/ttyUSB2
  -> gser.usb2
  -> /dev/ttyGS2
  -> bridge byte-transparent
  -> /dev/ttyS5
  -> RS-485
  -> controller X
```

Anche il controller Y ha risposto correttamente:

```text
TX: f7 82 04 00 0e 02 80
RX: f7 82 04 00 0e 82 09
```

Questo conferma l'accesso end-to-end al bus RS-485 della K2 Pro dal terzo canale USB dell'host esterno.

## 9. Stato CFS

Lo stesso `/dev/ttyS5` viene usato dal percorso CFS nella configurazione stock.

I primi probe `A2` online-check e `A1` discovery non hanno ricevuto risposta, ma durante quei test l'unità CFS era fisicamente scollegata. I risultati quindi non vengono considerati fallimenti del trasporto.

La validazione CFS con hardware collegato resta da eseguire.

## 10. Comportamento durante unbind/rebind

L'unbind del gadget ConfigFS rimuove le interfacce host e invalida i file descriptor `/dev/ttyGS*` già aperti. Di conseguenza i processi bridge byte-transparent attivi terminano quando il gadget viene sganciato.

Dopo il rebind vengono ricreati `/dev/ttyGS0`, `/dev/ttyGS1` e `/dev/ttyGS2`, mentre l'host enumera nuovamente `/dev/ttyUSB0`, `/dev/ttyUSB1` e `/dev/ttyUSB2`. I processi bridge devono quindi essere riavviati.

Il futuro service manager OpenHost dovrà gestire automaticamente questo comportamento.

## 11. Trasporto attualmente verificato

```text
Host Linux esterno

/dev/ttyUSB0
    |
    v
T113 gser.usb0 / ttyGS0
    |
    v
/dev/ttyS2 -> Main MCU

/dev/ttyUSB1
    |
    v
T113 gser.usb1 / ttyGS1
    |
    v
/dev/ttyS3 -> Nozzle MCU

/dev/ttyUSB2
    |
    v
T113 gser.usb2 / ttyGS2
    |
    v
/dev/ttyS5 -> RS-485 -> X/Y verificati, CFS da validare
```

## 12. Lavoro USB ancora da eseguire

Il trasporto principale è ormai verificato. Restano:

- traffico multi-canale sostenuto;
- funzionamento idle prolungato;
- cicli ripetuti di disconnect/reconnect;
- role switch ripetuti;
- restart deterministico dei bridge dopo rebind USB;
- nomi host stabili/regole udev;
- automazione gadget e bridge al boot;
- recovery quando l'host esterno è assente o viene riavviato.

## 13. Ripristino della modalità USB host stock

La procedura attuale resta runtime-only. Per sganciare il gadget e tornare in host mode:

```sh
ROLE=/sys/devices/platform/soc@3000000/soc@3000000:usbc0@0

echo "" > /sys/kernel/config/usb_gadget/g1/UDC 2>/dev/null
cat $ROLE/usb_host
```

Se necessario:

```sh
/usr/bin/chamber_cam_power.sh restart
```

Durante lo sviluppo, il reboot resta il percorso di recovery autoritativo.
