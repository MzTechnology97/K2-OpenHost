# Bootstrap del T113 (slot B)

Aggiornato: **6 ottobre 2026**. [English](../en/T113_BOOTSTRAP.md)

Stato: **in uso sulla stampante di riferimento dal 6 ottobre 2026** (bootstrap 0.1.1, base 1.1.0.94): lo slot B è confermato come predefinito e provato con uno spegnimento completo. Le schede sono state aggiornate alla 1.1.7.0 di Creality con `k2oh-mcu-fw update`; le correzioni emerse sono nel bootstrap 0.1.2 (vedi [Stato](#stato)). Leggi prima l'[esclusione di responsabilità](DISCLAIMER.md).

> [!IMPORTANT]
> Questo lavoro è stato preparato e provato sul firmware originale della K2 Pro **1.1.0.94**, la versione della stampante di riferimento. Le versioni Creality più recenti sono accettate con un avviso, ma **su firmware diversi dalla 1.1.0.94 il corretto funzionamento del bootstrap e della modalità USB gadget (OTG) del T113 non è garantito.** La build dello slot B rifiuta una versione in cui gli script di avvio che modifica sono diversi da quelli verificati; nella 1.1.7.0 sono identici.

Il bootstrap del T113 prepara la scheda T113 della K2 Pro per K2-OpenHost. È sviluppato in un repository dedicato, **[k2-openhost-t113-bootstrap](https://github.com/MzTechnology97/k2-openhost-t113-bootstrap)**, che contiene la guida completa passo per passo. Si installa dall'host esterno con il [K2-OpenHost Installer Helper](https://github.com/MzTechnology97/k2-openhost-installer-helper): la voce 23 del menu (`./helper.sh t113 check`) controlla la stampante in sola lettura, e la voce 24 (`./helper.sh t113 install`) clona il repository del bootstrap ed esegue tutto via SSH.

## Scelte di progetto

| Scelta | Perché |
| --- | --- |
| Usa lo **slot B** del T113 e non scrive mai lo **slot A** | Lo slot A, il sistema attuale della stampante, resta come riserva. Il cambio usa le stesse due variabili U-Boot dell'OTA Creality. |
| Lo slot B è un **sistema Creality originale** (di default la versione dello slot A, o una più recente) con modifiche minime, costruito sull'host dall'OTA scaricato dal CDN Creality | Il kernel originale ha già i driver gadget USB validati sulla stampante di riferimento ([Trasporto USB gadget](USB_GADGET.md)). Nessun file Creality viene ridistribuito. |
| Livello scrivibile su UDISK (`/mnt/UDISK/.k2openhost/overlay`) | `rootfs_data` appartiene allo slot A. Lo slot B non la monta, non la controlla e non la formatta mai, e non formatta, non controlla e non cancella mai UDISK. |
| **Avvio di prova** | La prima cosa che fa l'avvio dello slot B è riportare il prossimo avvio sullo slot A. Spegnendo e riaccendendo si recupera da qualsiasi errore; `k2oh-slot commit` tiene lo slot B. |
| Controllo rigido del modello | L'installer sull'host, quello sulla stampante e lo strumento firmware richiedono tutti una K2 Pro: modello Creality `F012`, scheda `CR0CN200400C10`. |

## Cosa gira nello slot B

- **Gadget USB:** tre funzioni Generic Serial (`0525:a4a6`).
- **Bridge:** un bridge per bus (`ttyGS0↔ttyS2` Main MCU, `ttyGS1↔ttyS3` Nozzle MCU, `ttyGS2↔ttyS5` RS-485/CFS/motori), 230400 8N1. È il bridge validato sulla stampante di riferimento, riavviato da procd.
- **`k2oh-mcu`:** a ogni avvio spegne e riaccende l'alimentazione delle MCU, esegue `mcu_update` originale di Creality (avvia le applicazioni di Main e Nozzle MCU e riscrive ogni scheda con una versione diversa) e solo dopo avvia i bridge. Al primo avvio `mcu_update` girava insieme ai bridge, che gli prendevano le risposte: le schede restavano nel loader Creality.
- **Nomi seriali sull'host:** il gadget dello slot B ha nomi `/dev/serial/by-id` diversi da quelli del gadget originale dello slot A. L'host usa `/dev/k2-main`, `/dev/k2-nozzle` e `/dev/k2-rs485` (udev, per interfaccia), uguali nei due slot; li imposta l'installer helper.
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

La via breve è `k2oh-mcu-fw update` (voce 31 dell'installer): scarica l'**ultima** versione Creality, la prepara, mostra cosa cambia e aggiorna solo se confermi. Passo per passo:

1. `k2oh-mcu-fw list` legge l'indice firmware pubblico di Creality.
2. `k2oh-mcu-fw download` scarica una versione dal CDN Creality, controlla il rootfs con l'elenco MD5 contenuto nell'immagine e tiene solo `fw/F012` e `fw/cfs`.
3. `k2oh-mcu-fw stage` li mette nello slot B.
4. `k2oh-mcu-fw apply` li scrive, solo con il Klipper dell'host fermo.

**CFS:** `mcu_util_485` aggiorna un CFS a ogni esecuzione quando `fw/cfs/version.json` indica un'altra versione per quell'unità, con o senza il passaggio CFS. Dal bootstrap 0.1.2 lo slot B tiene quella lista vuota (quella vera resta in `version.json.k2oh`), quindi solo `apply --cfs` tocca il CFS. `apply --cfs` usa la lista vera e aggiunge un secondo passaggio tramite `/tmp/cfs_update.json`. Il formato è stato ricostruito da `mcu_util_485`:

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

Lo slot A riscrive i file della sua versione al suo prossimo avvio: lo script originale riscrive a ogni differenza di versione.

## Stato

| Elemento | Stato |
| --- | --- |
| Build dello slot B (file per file rispetto all'originale), download/MD5 dell'OTA originale, script con BusyBox/Python 3.9 della stampante | verificati offline sulla 1.1.0.94 |
| Versione più recente 1.1.7.0 | stessi script di avvio, servizi e kernel con gadget; lo slot B si costruisce con l'avviso "non provata"; non avviato |
| Bridge con pseudo-terminali, estrazione firmware rispetto a `unsquashfs`, download della 1.1.7.0, piano CFS, installazione di HelixScreen (chroot) | verificati offline |
| Prima installazione e avvio di prova, 0.1.0 (6 ottobre 2026) | slot B scritto e riletto, avvio di prova e ritorno allo slot A riusciti; gadget, bridge, `k2oh-ctl` e HelixScreen funzionanti. Sei problemi trovati: schede non avviate, chiave host SSH diversa, nomi by-id diversi, HelixScreen vedeva 0 MB liberi, attesa di 120 s di HelixScreen; nell'helper, `boot-b` non riavviava mai. Corretti nel bootstrap 0.1.1 e nell'helper ([bootstrap#8](https://github.com/MzTechnology97/k2-openhost-t113-bootstrap/pull/8), [helper#12](https://github.com/MzTechnology97/k2-openhost-installer-helper/pull/12)) |
| 0.1.1 sulla stampante di riferimento (6 ottobre 2026) | installazione, avvio di prova e `boot-a` con l'helper; schede avviate da `k2oh-mcu` all'avvio; slot B confermato; **spegnimento e riaccensione completi**: lo slot B è partito da solo e Klipper sul CM5 era pronto senza `FIRMWARE_RESTART`, CFS OK, `[k2_t113]` connesso, HelixScreen sul pannello |
| `k2oh-mcu-fw update` alla 1.1.7.0 (6 ottobre 2026) | motori ed estrusore `mot2_…071` → `081`, RFID `009` → `010`, Main e Nozzle invariate, tutte avviate; dopo, Klipper, CFS e motori a posto. È stato aggiornato anche il CFS (113 → 153) senza `--cfs`: corretto nella 0.1.2 |
| Immagine CFS personalizzata (`--cfs-image`, 6 ottobre 2026) | scritta, ma il loader del CFS ha rifiutato di avviarla (`start_app NACK`): la 0.1.1 chiamava la copia con il suo SHA-256, che `mcu_util_485` ha scritto come versione. Ripristinato con lo stock 153. Corretto nella 0.1.2; l'immagine è in revisione |
| Ancora da provare sull'hardware | un `apply --cfs` originale con la lista CFS messa da parte della 0.1.2; un'immagine CFS personalizzata rivista; l'installazione dell'immagine 0.1.2 (i suoi due strumenti corretti sono stati copiati a mano nello slot B in uso) |

Un control plane per gli altri GPIO di servizio del T113 ([GPIO di servizio T113](T113_GPIO.md)) potrà vivere nello slot B più avanti. Non fa parte di questa versione.
