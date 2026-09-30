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

Nel funzionamento stock, USB0 viene utilizzata in host mode per la camera interna. La camera è stata osservata come:

```text
Bus 003 Device 002: ID 1d6c:0103 Creality 3D Technology CREALITY CAM
```

attraverso:

```text
4101000.ehci0-controller
```

con controller OHCI corrispondente:

```text
4101400.ohci0-controller
```

## 3. Commutazione USB0 in device mode

Il driver OTG vendor espone nodi sysfs tra cui:

```text
usb_host
usb_device
usb_null
otg_role
```

Sull'unità testata:

```sh
ROLE=/sys/devices/platform/soc@3000000/soc@3000000:usbc0@0
cat $ROLE/usb_device
```

ha restituito:

```text
device_chose finished!
```

Il kernel ha registrato:

```text
rmmod_host_driver
sunxi_usb_disable_ehci
4101000.ehci0-controller remove
usb 3-1: USB disconnect
sunxi_usb_disable_ohci
4101400.ohci0-controller remove
insmod_device_driver
```

Questo verifica direttamente che USB0 può passare dinamicamente da host mode a device mode con Tina Linux già avviato.

## 4. Tool USB gadget vendor

Nel filesystem stock è presente:

```text
/bin/setusbconfig
```

Il tool vendor espone una configurazione Generic Serial (`gser`). Eseguendo:

```sh
/bin/setusbconfig gser
```

vengono creati:

```text
/sys/kernel/config/usb_gadget/g1/functions/gser.usb0
/dev/ttyGS0
```

con:

```text
VID:     0x0525
PID:     0xa4a6
Product: Gadget Serial
UDC:     4100000.udc-controller
```

La configurazione attiva collega:

```text
configs/c.1/gser.usb0 -> .../functions/gser.usb0
```

## 5. Stato gadget verificato con host esterno collegato

Con un Raspberry Pi CM5 fisicamente collegato alla porta Micro-USB service/recovery della K2 Pro, l'UDC della K2 ha riportato:

```text
state:         configured
current_speed: high-speed
maximum_speed: high-speed
function:      g1
```

Il kernel ha inoltre registrato:

```text
android_work: sent uevent USB_STATE=CONNECTED
configfs-gadget gadget: high-speed config #1: c
android_work: sent uevent USB_STATE=CONFIGURED
```

Questo conferma l'enumerazione runtime corretta del gadget attraverso il connettore Micro-USB fisico.

## 6. Enumerazione lato Raspberry Pi CM5

L'host esterno utilizzato per il test è un Raspberry Pi CM5 con Debian Bookworm e kernel Linux 6.12.

`lsusb` ha rilevato:

```text
0525:a4a6 Netchip Technology, Inc. Linux-USB Serial Gadget
```

La topologia USB ha riportato il link a:

```text
480M
```

L'interfaccia non si è associata automaticamente a un driver seriale, quindi è stato collegato manualmente il driver Linux generico `usbserial`:

```sh
sudo modprobe usbserial
echo 0525 a4a6 | sudo tee /sys/bus/usb-serial/drivers/generic/new_id
```

Il kernel ha quindi riportato:

```text
usbserial_generic ... generic converter detected
usb ... generic converter now attached to ttyUSB0
```

ed è comparso:

```text
/dev/ttyUSB0
```

L'avviso di `usbserial_generic` relativo all'uso per test e prototipi è previsto in questa fase di sviluppo.

## 7. Trasferimento seriale bidirezionale verificato

### CM5 -> K2

K2:

```sh
cat /dev/ttyGS0
```

CM5:

```sh
printf 'K2_OPENHOST_CM5_TO_K2_001\n' | sudo tee /dev/ttyUSB0
```

La K2 ha ricevuto correttamente:

```text
K2_OPENHOST_CM5_TO_K2_001
```

### K2 -> CM5

CM5:

```sh
sudo cat /dev/ttyUSB0
```

K2:

```sh
printf 'K2_OPENHOST_K2_TO_CM5_001\n' > /dev/ttyGS0
```

Il CM5 ha ricevuto correttamente:

```text
K2_OPENHOST_K2_TO_CM5_001
```

Il seguente percorso è quindi verificato direttamente:

```text
Raspberry Pi CM5 /dev/ttyUSB0
        ^
        | seriale bidirezionale
        v
USB 2.0 High-Speed (480M)
        ^
        |
        v
Micro-USB service/recovery K2 Pro
        ^
        |
        v
UDC Allwinner T113 / gser.usb0
        ^
        |
        v
K2 Pro /dev/ttyGS0
```

## 8. Test USB ancora da eseguire

Il trasporto dati di base è verificato. Restano da validare:

- recovery dopo disconnessione/riconnessione;
- role switch host/device ripetuti;
- funzionamento idle prolungato;
- traffico seriale sostenuto;
- automazione al boot;
- configurazione gadget multi-funzione o multi-canale.

## 9. Ripristino della modalità host USB normale

Il test runtime non richiede modifiche persistenti.

Per sganciare il gadget e tornare in host mode:

```sh
ROLE=/sys/devices/platform/soc@3000000/soc@3000000:usbc0@0

echo "" > /sys/kernel/config/usb_gadget/g1/UDC 2>/dev/null
cat $ROLE/usb_host
```

Se necessario si può richiamare l'helper vendor della camera:

```sh
/usr/bin/chamber_cam_power.sh restart
```

Anche un reboot ripristina il normale comportamento stock USB host sull'unità testata.

## 10. Importanza per K2-OpenHost

Il test fisico Micro-USB è riuscito. La mainboard T113 originale può esporre un link seriale virtuale verso un host Linux esterno senza richiedere Arduino, RP2040, bridge USB-UART aggiuntivi o una mainboard sostitutiva.

Il prossimo obiettivo diventa:

```text
Host Kalico esterno /dev/ttyUSBx
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
MCU Main / Nozzle originali K2
```

La prossima fase hardware consiste nell'identificare le UART e i baud rate esatti degli MCU Main e Nozzle della K2 Pro e validare il bridge senza modificare il firmware originale degli MCU.
