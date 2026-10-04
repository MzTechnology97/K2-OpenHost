# GPIO di servizio T113 della K2 Pro

Stato: **mappa stock verificata staticamente; alimentazione delle MCU e buzzer comandati dal CM5 tramite `k2oh-ctl`, provati dal vivo il 4 ottobre 2026**.

Questi segnali appartengono all'Allwinner T113 originale della K2 Pro. I numeri `140/162/164/165/209/210` sono la numerazione GPIO Linux del T113 e **non** corrispondono ai GPIO del Raspberry Pi CM5.

## Mappa verificata dal firmware Creality stock

| GPIO Linux | Pin T113 | Nome stock | Funzione | Livello attivo |
|---:|---|---|---|---|
| 140 | PE12 | `MCU_PWR_EN` | alimentazione rail MCU/periferiche; usato da `mcu_reset.sh` | **0 = ON**, 1 = OFF |
| 161 | PF1 | `USB_P_EN4` | camera reserved, percorso K1 Max | **0 = ON**, 1 = OFF |
| 162 | PF2 | `USB_P_EN3` | alimentazione nozzle camera | **0 = ON**, 1 = OFF |
| 164 | PF4 | buzzer | buzzer motherboard | **1 = ON**, 0 = OFF |
| 165 | PF5 | `USB_HUB_RST` | reset hub USB | **1 = reset**, 0 = normale |
| 209 | PG17 | `USB_P_EN2` | CMS reserved, percorso K1 Max | **0 = ON**, 1 = OFF |
| 210 | PG18 | `USB_P_EN1` | alimentazione UDISK / USB storage | **0 = ON**, 1 = OFF |

La conversione usa la numerazione Allwinner standard a banchi da 32 GPIO: `PE12 = 4*32+12 = 140`, `PF2 = 162`, `PF4 = 164`, `PF5 = 165`, `PG17 = 209`, `PG18 = 210`.

## Evidenza stock

### MCU power/reset

`/usr/bin/mcu_reset.sh` dichiara:

```text
MCU_PWR_EN=140
0 = power on
1 = power off
```

Il power-cycle stock è:

```text
GPIO140 = 1
sleep 2 s
GPIO140 = 0
```

Questa è una vera interruzione della rail controllata dal T113, non un semplice reset logico Klipper.

### Nozzle camera e USB

`/usr/bin/usb_host_5v.sh` definisce:

```text
USB_HUB_RST=165
USB_P_EN1=210   # udisk
USB_P_EN2=209   # CMS, reserved
USB_P_EN3=162   # nozzle cam
USB_P_EN4=161   # cam, reserved
```

Per la K2 Pro vengono normalmente esportati 165, 210 e 162. I GPIO 209 e 161 vengono attivati dal codice solo nel ramo `CR-K1 Max`.

`/usr/bin/nozzle_cam_power.sh` conferma:

```text
GPIO162 = 0 -> nozzle camera ON
GPIO162 = 1 -> nozzle camera OFF
```

In OpenHost la service USB del T113 è usata come gadget; la topologia USB host stock cambia e le camere sono previste sul CM5 diretto. La mappa rimane comunque utile per inventario hardware e recovery.

### Buzzer

`/usr/bin/beep.sh` usa direttamente:

```text
GPIO164 = 1 -> buzzer ON
GPIO164 = 0 -> buzzer OFF
```

Lo script limita la durata massima a 30 secondi. Contiene anche una vecchia implementazione PWM6 commentata (4 kHz, duty 50%), ma la K2 stock usa il semplice GPIO PF4.

Il binario `audio-server` richiama esplicitamente `/usr/bin/beep.sh %f`, quindi il comando audio/beep dell'interfaccia Creality termina sul GPIO164.

### Chamber camera

`chamber_cam_power.sh` non usa uno di questi GPIO: sui modelli F012/F021 il restart passa dall'attributo kernel USB-host del controller T113. Non va quindi confuso con il GPIO162 della nozzle camera.

## Rapporto con il CM5

Il CM5 espone i propri controller `/dev/gpiochip*`, ma non sono stati trovati net nominati `MCU_PWR_EN`, `USB_P_EN3`, `BUZZER`, `USB_HUB_RST` o `USB_P_EN1` collegati direttamente al CM5.

```text
CM5
 |
 | USB gadget
 v
T113
 |-- GPIO140 -> MCU_PWR_EN
 |-- GPIO162 -> nozzle camera power
 |-- GPIO164 -> buzzer
 |-- GPIO165 -> USB hub reset
 `-- GPIO210 -> UDISK power
```

Quindi il CM5 potrà comandare questi segnali solo tramite un **control plane eseguito sul T113**.

## Vincolo USB gadget

I tre canali gadget validati restano dedicati a `ttyGS0` Main MCU, `ttyGS1` Nozzle MCU e `ttyGS2` RS-485/CFS/closed-loop.

Un quarto `gser.usb3` è stato sperimentato ma il bind del gadget al controller UDC non è riuscito; non viene quindi assunto come trasporto disponibile. Il vecchio MUX/DEMUX su GS2 è stato abbandonato come architettura production. Il GPIO control plane non deve reintrodurre contesa o framing nei tre stream MCU raw.

## API logica proposta

Il controllo remoto dovrà esporre **nomi logici**, non numeri GPIO:

```text
status
mcu-power on
mcu-power off
mcu-power cycle
nozzle-camera on
nozzle-camera off
buzzer <milliseconds>
usb-hub assert
usb-hub release
udisk-power on
udisk-power off
```

`mcu-power cycle` e `usb-hub assert` sono operazioni disruptive e devono richiedere stampante idle, target heater a zero, processi coinvolti fermati o compatibili, conferma esplicita e verifica post-operazione.

Per il firmware updater, `mcu-power cycle` è il controllo di maggiore interesse perché può permettere di osservare Main/Nozzle/motori/CFS nella loro finestra loader subito dopo il reset hardware.


## Helper locale T113

È stato aggiunto `tools/t113-gpio-control.sh` come endpoint locale, non come trasporto remoto. Supporta `--dry-run` e richiede `--confirm-disruptive` prima di togliere alimentazione alla rail MCU o asserire il reset USB hub.

Il helper è stato verificato con `sh -n`, dry-run e sysfs finto sul CM5. **Non è stato ancora installato o eseguito sul T113 reale.** Il timing di un eventuale impulso automatico `USB_HUB_RST` non viene inventato: sono esposti solo `assert` `release`, che corrispondono direttamente ai livelli stock verificati.

## Control plane: k2oh-ctl

Il control plane è `k2oh-ctl`, un piccolo servizio HTTP del [bootstrap del T113](T113_BOOTSTRAP.md) (slot B). Passa dalla rete locale, non dal gadget USB, quindi i tre flussi MCU restano intatti. Risponde solo all'indirizzo dell'host esterno, e solo con un token condiviso.

| Segnale | Esposto come | Note |
| --- | --- | --- |
| GPIO140 `MCU_PWR_EN` | stato/accensione/spegnimento (dispositivo Moonraker `K2_MCU_Power`), ciclo di alimentazione (`T113_MCU_POWER_CYCLE`), arresto di emergenza | spegnimento e ciclo richiedono uno stato di stampa inattivo noto dal Moonraker dell'host; il ciclo ferma i bridge, tiene la linea spenta 2 s come `mcu_reset.sh` e finisce sempre con la linea accesa |
| GPIO164 buzzer | `T113_BEEP`, `M300`, bip dell'RFID esterno | fino a 3 s e 5 bip |
| GPIO162, 165, 209, 210 | non esposti | le telecamere sono ricollegate all'host; alimentazione USB e reset dell'hub non servono a K2-OpenHost |

Vengono scritti solo i valori; le direzioni dei pin impostate all'avvio non vengono mai cambiate. Il lato host è `[k2_t113]` in kalico-k2pro, e l'installer helper collega le due parti (`./helper.sh t113 link`).

Lo script locale `tools/t113-gpio-control.sh` resta uno strumento manuale per lo slot A. Il servizio del bootstrap è la via supportata.

## Stato attuale

- mappa GPIO stock: **verificata**;
- buzzer GPIO164: **verificato**, comandato dal vivo tramite `k2oh-ctl` (4 ottobre 2026);
- ciclo di alimentazione e arresto di emergenza su GPIO140 tramite `k2oh-ctl`: **provati dal vivo** con la stampante inattiva. Dopo `FIRMWARE_RESTART`, pronto in 9 s, CFS in 16 s, motori in 21 s;
- polarità: **verificate dagli script stock**;
- accesso diretto CM5 ai net: **non presente / non provato**, quindi il control plane è necessario;
- cosa succede se si perde un collegamento seriale attraverso il T113: vedi [Perdita del collegamento seriale](SERIAL_LINK_LOSS.md).