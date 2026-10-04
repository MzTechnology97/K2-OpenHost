# Bootstrap del T113 (slot B)

Aggiornato: **4 ottobre 2026**. [English](../en/T113_BOOTSTRAP.md)

Stato: **costruito e provato offline; non ancora avviato su una stampante.** Leggi prima l'[esclusione di responsabilità](DISCLAIMER.md).

Il bootstrap del T113 prepara la scheda T113 della K2 Pro per K2-OpenHost. Si installa dall'host esterno con il [K2-OpenHost Installer Helper](https://github.com/MzTechnology97/k2-openhost-installer-helper) (voce 23 del menu, `./helper.sh t113 install`). La guida completa passo per passo è in quel repository: [guida al bootstrap del T113](https://github.com/MzTechnology97/k2-openhost-installer-helper/blob/main/t113/slot-b/README.it.md).

## Scelte di progetto

| Scelta | Perché |
| --- | --- |
| Usa lo **slot B** del T113 e non scrive mai lo **slot A** | Lo slot A, il sistema attuale della stampante, resta come riserva. Il cambio usa le stesse due variabili U-Boot dell'OTA Creality. |
| Lo slot B è **il sistema Creality 1.1.0.94 originale** con modifiche minime, costruito sull'host dall'OTA scaricato dal CDN Creality | Il kernel originale ha già i driver gadget USB validati sulla stampante di riferimento ([Trasporto USB gadget](USB_GADGET.md)). Nessun file Creality viene ridistribuito. |
| Livello scrivibile su UDISK (`/mnt/UDISK/.k2openhost/overlay`) | `rootfs_data` appartiene allo slot A. Lo slot B non la monta, non la controlla e non la formatta mai, e non formatta, non controlla e non cancella mai UDISK. |
| **Avvio di prova** | La prima cosa che fa l'avvio dello slot B è riportare il prossimo avvio sullo slot A. Spegnendo e riaccendendo si recupera da qualsiasi errore; `k2oh-slot commit` tiene lo slot B. |
| Controllo rigido del modello | L'installer sull'host, quello sulla stampante e lo strumento firmware richiedono tutti una K2 Pro: modello Creality `F012`, scheda `CR0CN200400C10`. |

## Cosa gira nello slot B

- **Gadget USB:** tre funzioni Generic Serial (`0525:a4a6`).
- **Bridge:** un bridge per bus (`ttyGS0↔ttyS2` Main MCU, `ttyGS1↔ttyS3` Nozzle MCU, `ttyGS2↔ttyS5` RS-485/CFS/motori), 230400 8N1. È il bridge validato sulla stampante di riferimento, riavviato da procd.
- **`mcu_update` originale:** avvia le applicazioni di Main e Nozzle MCU a ogni avvio.
- **Wi-Fi:** funziona senza il `wifi-server` Creality, con le reti copiate dallo slot A.
- **HelixScreen:** installato al primo avvio e collegato al Moonraker dell'host esterno.
- **`k2oh-mcu-fw`:** aggiornamento manuale del firmware di MCU, motori e CFS (sotto).

Disattivati:
- Klipper, klipper_mcu, Moonraker e nginx Creality;
- le app di interfaccia e cloud;
- ADB (prenderebbe il controller USB);
- la telecamera WebRTC;
- l'OTA da chiavetta (un OTA dallo slot B sovrascriverebbe lo slot A);
- il ripristino di fabbrica (`wipe_data`);
- il riavvio della telecamera della camera (sulla K2 Pro riporta la USB0 in modalità host).

## Aggiornamento del firmware delle periferiche

Gli aggiornamenti sono manuali apposta e usano **gli strumenti Creality** (`mcu_util`, `mcu_util_485`, `/etc/init.d/mcu_update`): la stessa sequenza di un OTA originale, con l'alimentazione delle MCU spenta e riaccesa da `mcu_reset.sh` (GPIO140 `MCU_PWR_EN`, vedi [GPIO di servizio T113](T113_GPIO.md)). Passi:

1. `k2oh-mcu-fw list` legge l'indice firmware pubblico di Creality.
2. `k2oh-mcu-fw download` scarica una versione dal CDN Creality, controlla il rootfs con l'elenco MD5 contenuto nell'immagine e tiene solo `fw/F012` e `fw/cfs`.
3. `k2oh-mcu-fw stage` li mette nello slot B.
4. `k2oh-mcu-fw apply` li scrive, solo con il Klipper dell'host fermo.

**CFS:** `apply --cfs` aggiunge un secondo passaggio tramite `/tmp/cfs_update.json`. Il formato è stato ricostruito da `mcu_util_485`:

```json
{"CFSs": [{"uuid": "<UniID a 12 byte, esadecimale minuscolo separato da spazi>", "fw": "<file>"}]}
```

- UniID e identità esatta del loader (`cfs0_050_G32-…`) arrivano dall'output dello strumento Creality (`/tmp/.485_mcu_version`) dopo il primo passaggio.
- Il file viene scelto in base alla variante hardware esatta: dalla 1.1.7.0 G30 e G32 sono diversi (150 e 153).

[K2-OpenHost Firmware Tools](https://github.com/MzTechnology97/k2-openhost-firmware-tools) documenta i protocolli. Le sue sonde in sola lettura sono il controllo indipendente.

**Perché gli strumenti Creality e non il `motor_updater.py` di Jacob10383:**
- sono gli strumenti validati per questo hardware e sono già nello slot B, alla versione dello slot A;
- corrispondono alla topologia della K2 Pro: due motori RS-485 più l'estrusore attraverso la scheda ugello, e le schede nastro e RFID;
- gestiscono il CFS come fa l'OTA Creality.

`motor_updater.py` è pensato per la disposizione di K2/K2 Plus e per il kernel di Jacob, e resta un ottimo riferimento.

Lo slot A riscrive i suoi file 1.1.0.94 al suo prossimo avvio: lo script originale riscrive a ogni differenza di versione.

## Stato

| Elemento | Stato |
| --- | --- |
| Build dello slot B (file per file rispetto all'originale), download/MD5 dell'OTA originale, script con BusyBox/Python 3.9 della stampante | verificati offline |
| Bridge con pseudo-terminali, estrazione firmware rispetto a `unsquashfs`, download della 1.1.7.0, piano CFS, installazione di HelixScreen (chroot) | verificati offline |
| Scrittura dello slot B, avvio di prova, gadget/bridge sullo slot B, HelixScreen sul pannello, `k2oh-mcu-fw apply` | **in attesa di validazione su hardware** |

Un control plane per gli altri GPIO di servizio del T113 ([GPIO di servizio T113](T113_GPIO.md)) potrà vivere nello slot B più avanti. Non fa parte di questa versione.
