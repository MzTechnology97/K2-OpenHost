# Back to stock

K2-OpenHost never writes the T113's slot A, so the printer's original system is always one command away.

## Go back to slot A

```bash
./helper.sh t113 boot-a     # menu 28
```

The printer reboots into slot A: Creality's own Klipper, screen and apps, exactly as before. At boot slot A flashes its own release's firmware back onto the boards if they differ.

Without the host, from an SSH session on the printer running slot B:

```sh
k2oh-slot boot-a && reboot
```

## Return to K2-OpenHost later

```bash
./helper.sh t113 boot-b     # trial boot, then
./helper.sh t113 commit     # keep slot B
```

## Remove K2-OpenHost from the printer

From slot A, after the steps above:

```sh
rm -rf /mnt/UDISK/.k2openhost
```

This removes slot B's writable layer, backups and downloaded firmware. Slot B's partitions stay as they are until a Creality OTA writes them.

## Cameras and USB

Put the chamber camera back on the T113, on its original cable path. In slot A the nozzle camera and the printer's external USB port work again.

## Experimental CFS firmware

If you flashed an experimental CFS image, flash the stock CFS firmware back with a Creality update from slot A (or `./helper.sh t113 mcu-fw apply --cfs` from slot B before going back). See [Flash and roll back](../cfs-firmware/flash.md#back-to-stock-cfs-firmware).
