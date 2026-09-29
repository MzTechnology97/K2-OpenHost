# Indagine USB Gadget e Micro-USB

> Ambito: unità di test Creality K2 Pro. Questo documento separa le osservazioni verificate direttamente dalle ipotesi che richiedono ancora test.

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

CDC ACM non risulta abilitato nel kernel attuale, ma è disponibile il generic serial gadget.

## 2. Ruolo normale di USB0

L'OTG manager Allwinner espone:

```text
/sys/devices/platform/soc@3000000/soc@3000000:usbc0@0/otg_role
```

Prima del test riportava:

```text
usb_host
```

`lsusb` mostrava:

```text
Bus 003 Device 002: ID 1d6c:0103 Creality 3D Technology CREALITY CAM
```

La camera risultava collegata attraverso:

```text
4101000.ehci0-controller
```

con controller OHCI corrispondente:

```text
4101400.ohci0-controller
```

Questo conferma che USB0 viene normalmente utilizzata in host mode per la camera interna.

## 3. Commutazione USB0 in device mode

Il driver OTG vendor espone nodi sysfs tra cui:

```text
usb_host
usb_device
usb_null
otg_role
```

Sull'unità testata, eseguendo:

```sh
ROLE=/sys/devices/platform/soc@3000000/soc@3000000:usbc0@0
cat $ROLE/usb_device
```

si ottiene:

```text
device_chose finished!
```

Il kernel ha quindi registrato la sequenza prevista:

```text
rmmod_host_driver
sunxi_usb_disable_ehci
4101000.ehci0-controller remove
usb 3-1: USB disconnect
sunxi_usb_disable_ohci
4101400.ohci0-controller remove
insmod_device_driver
```

La `CREALITY CAM` interna si disconnette durante il passaggio.

Questo costituisce una verifica hardware diretta del fatto che USB0 può passare dinamicamente da host mode a device mode con Tina Linux già avviato.

## 4. Tool USB gadget vendor

Nel filesystem stock è presente:

```text
/bin/setusbconfig
```

L'analisi delle stringhe del tool mostra supporto integrato per varie funzioni USB gadget:

- ADB;
- MTP;
- mass storage;
- RNDIS;
- NCM;
- HID;
- loopback;
- printer gadget;
- generic serial (`gser`).

Per `gser`, l'implementazione vendor crea:

```text
/sys/kernel/config/usb_gadget/g1/functions/gser.usb0
```

utilizzando:

```text
VID: 0x0525
PID: 0xa4a6
Product: Gadget Serial
```

Il tool esegue inoltre automaticamente il binding al controller UDC disponibile.

## 5. Creazione verificata del generic serial gadget

Dopo aver commutato USB0 in device mode, il comando:

```sh
/bin/setusbconfig gser
```

è terminato correttamente con exit status `0`.

Sono stati verificati:

```text
/dev/ttyGS0
```

come character device, e:

```text
/sys/kernel/config/usb_gadget/g1/functions/gser.usb0
```

in ConfigFS.

La configurazione attiva contiene il link:

```text
configs/c.1/gser.usb0 -> .../functions/gser.usb0
```

Gli identificativi sono:

```text
idVendor  = 0x0525
idProduct = 0xa4a6
product   = Gadget Serial
```

Il binding UDC è:

```text
4100000.udc-controller
```

Il campo `function` dell'UDC riporta:

```text
g1
```

## 6. Stato endpoint attuale

Prima di collegare un host USB esterno, l'UDC riporta correttamente:

```text
state:         not attached
current_speed: UNKNOWN
maximum_speed: high-speed
function:      g1
```

È lo stato previsto: il gadget è configurato e bindato, ma non esiste ancora un host USB esterno collegato.

## 7. Connettore fisico Micro-USB

La mainboard K2 dispone di un connettore Micro-USB service/recovery utilizzato per procedure di full recovery/flash.

L'ipotesi di lavoro è che questo connettore sia fisicamente collegato allo stesso percorso USB0 device usato dall'UDC Allwinner.

### Stato importante

Questo percorso fisico a runtime **non è ancora stato confermato**.

Il prossimo test prevede di collegare la Micro-USB a un host Linux dopo aver abilitato `gser` e verificare l'enumerazione come:

```text
0525:a4a6 Gadget Serial
```

Se il driver `usbserial` generico non si associa automaticamente, sul sistema Linux host si potrà usare:

```sh
sudo modprobe usbserial
echo 0525 a4a6 | sudo tee /sys/bus/usb-serial/drivers/generic/new_id
```

Dovrebbe quindi comparire un device come:

```text
/dev/ttyUSB0
```

## 8. Test bidirezionale previsto

Lato K2:

```sh
cat /dev/ttyGS0
```

Lato host Linux:

```sh
echo "TEST_HOST_TO_K2" > /dev/ttyUSB0
```

Direzione opposta:

Host:

```sh
cat /dev/ttyUSB0
```

K2:

```sh
echo "TEST_K2_TO_HOST" > /dev/ttyGS0
```

Questo test è ancora da eseguire.

## 9. Ripristino della modalità host USB normale

Gli esperimenti eseguiti finora non richiedono modifiche persistenti.

Per sganciare il gadget e tornare in host mode:

```sh
ROLE=/sys/devices/platform/soc@3000000/soc@3000000:usbc0@0

echo "" > /sys/kernel/config/usb_gadget/g1/UDC 2>/dev/null
cat $ROLE/usb_host
```

Se necessario si può richiamare anche l'helper vendor della camera:

```sh
/usr/bin/chamber_cam_power.sh restart
```

Sull'unità testata, anche un reboot ripristina il normale comportamento stock USB host.

## 10. Importanza per K2-OpenHost

Se il test di enumerazione fisica della Micro-USB avrà successo, la mainboard T113 originale potrà esporre link seriali virtuali verso un host Linux esterno senza usare Arduino, RP2040 o bridge hardware aggiuntivi.

Il percorso obiettivo diventa:

```text
Host esterno /dev/ttyUSBx
        |
        v
Micro-USB -> UDC T113 -> /dev/ttyGSx
        |
        v
bridge userspace byte-transparent
        |
        v
T113 /dev/ttySx
        |
        v
MCU originale K2
```

Questo permetterebbe all'host Kalico esterno di comunicare con gli MCU originali mantenendo la mainboard K2.
