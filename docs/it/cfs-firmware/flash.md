# Flash e rollback

Il flash passa dal **menu 40 dell'helper (Experimental CFS firmware)**. L'helper non scarica né flasha mai da solo: tu metti l'immagine, lui la verifica, tu confermi con una frase, e il flash vero lo fanno **gli strumenti di Creality** sulla T113.

!!! warning "Prima di iniziare"
    - Stampante **ferma**, nessuna stampa in corso o in pausa, riscaldatori spenti.
    - **Slot B** della T113 in esecuzione, bootstrap 0.1.2 o successivo, controlli della T113 collegati (menu 32).
    - L'**immagine di recupero v3.22** (e CFG5T se passi a CFG6) scaricata accanto all'immagine che flashi.
    - In `box.cfg`, tieni `auto_apply: False` per il primo avvio con il nuovo firmware.

## 1. Scaricare l'immagine sull'host

Dalla cartella dell'helper sull'host:

```bash
cd ~/k2-openhost-installer-helper
F=cfs0_050_G32-cfs0_000_153-runtime-config-v3_25-K2OH-CFG6-EXPERIMENTAL.bin
curl -fL --retry 3 -o firmware/custom-cfs/$F \
  https://raw.githubusercontent.com/MzTechnology97/k2-cfs-rfid-tools/main/firmware/v3.25-cfg6-lab/$F
sha256sum firmware/custom-cfs/$F
```

L'hash deve essere `6579eb552210d6b2b84fbbbdf2749bc8d310b324ffb095cf9662e7cd0acc6cc6`. Scarica allo stesso modo l'immagine di recupero:

```bash
R=cfs0_050_G32-cfs0_000_153-runtime-config-v3_22-READONLY-DIAG-EXPERIMENTAL.bin
curl -fL --retry 3 -o firmware/custom-cfs/$R \
  https://raw.githubusercontent.com/MzTechnology97/k2-cfs-rfid-tools/main/firmware/v3.22-readonly-state-probes/$R
sha256sum firmware/custom-cfs/$R    # 40dbaad88de7b6f9435592fa03b081e9b96663a9e84896b1ad8021a8f13cf8c7
```

Mantieni i nomi originali esatti: il menu elenca solo le immagini che sono sia in `manifest.json` sia presenti con il nome e l'hash previsti.

## 2. Flashare dal menu 40

```bash
K2OH_NO_UPDATE_CHECK=1 ./helper.sh experimental-cfs
```

1. Scegli l'immagine (per esempio **CFG6 v3.25**). I numeri del menu possono cambiare da un host all'altro: controlla ogni volta il nome del file e lo SHA-256.
2. L'helper controlla lo SHA-256 e che il nome del file indichi esattamente l'hardware e l'applicazione del CFS, poi mostra la destinazione e i rischi.
3. Digita esattamente `FLASH EXPERIMENTAL CFS`. `--yes` non salta mai questo passo.
4. Parte il percorso protetto:
    1. SHA-256 verificato sull'host;
    2. il bootstrap installato deve supportare il percorso protetto per immagini personalizzate;
    3. caricamento sulla T113 e SHA-256 verificato di nuovo lì;
    4. controllo dello stato di stampa, Klipper fermato sull'host;
    5. `k2oh-mcu-fw apply --cfs --cfs-image ...` sulla T113, che flasha con `mcu_util_485` e controlla header dell'applicazione, CRC, dimensione, stack pointer e reset vector;
    6. la copia di trasferimento viene rimossa dalla T113.

La stessa operazione da riga di comando:

```bash
./helper.sh t113 mcu-fw apply --cfs \
  --cfs-image ./firmware/custom-cfs/cfs0_050_G32-cfs0_000_153-runtime-config-v3_25-K2OH-CFG6-EXPERIMENTAL.bin \
  --cfs-sha256 6579eb552210d6b2b84fbbbdf2749bc8d310b324ffb095cf9662e7cd0acc6cc6
```

## 3. Primo avvio con il nuovo firmware

1. Avvia Klipper (l'helper lo propone, oppure `sudo systemctl start klipper`).
2. In console:

    ```text
    BOX_CFS_CONFIG_INFO
    ```

    Deve mostrare l'identità, es. `K2OH / v323-cfg6`, feature `0xE3`, 28 parametri.

3. Controlla che il collegamento RS-485 e i motori siano a posto: `SERIAL_STATUS`, `MOTOR_STATUS`, `BOX_DEBUG`.
4. Solo dopo attiva i tuoi valori: vedi [Parametri runtime](parameters.md#enable-the-values).

## Rollback { #roll-back }

Un rollback si esegue **solo a stampante ferma**, dopo aver confermato che il loader della CFS risponde e che l'immagine destinata all'hardware G32/APP153 è integra (SHA-256). Prediligi **l'ultima immagine effettivamente funzionante sulla tua CFS** (per esempio CFG6 v3.25); tieni anche v3.22, CFG5T o stock come alternative, secondo la compatibilità. **Nessun firmware garantisce il recupero di ogni scrittura interrotta**: se anche il rollback non ottiene ACK, interrompi i tentativi e diagnostica il bus/loader.

## Tornare al firmware CFS stock { #back-to-stock-cfs-firmware }

`apply --cfs` con la release di Creality flasha l'applicazione CFS stock elencata nella release:

```bash
./helper.sh t113 mcu-fw apply --cfs
```

Eseguilo dallo slot B con la stampante ferma. Un aggiornamento del CFS da un OTA Creality stock nello slot A fa lo stesso.

## Se il flash si interrompe a metà

**Non ripetere automaticamente il flash che ha appena fallito**, soprattutto se il BIN è sperimentale.

1. Mantieni l'alimentazione stabile e **non avviare stampa, homing o carico/scarico**. Raccogli subito il log T113 `/tmp/mcu_update.log` e annota l'immagine e il suo SHA-256.
2. Distingui `send fw data ... failed` (il trasferimento non è arrivato alla risposta finale **DONE**) da `START_APP NACK` (errore in una fase successiva). Nel primo caso **non è dimostrato che il nuovo firmware abbia eseguito codice**.
3. Con stampante ferma, riscaldatori spenti ed **esclusività del bus RS-485**, verifica se la CFS risponde ancora come **loader** o come **applicazione**. La diagnostica con `A1/A2` e le eventuali transizioni di modalità non vanno eseguite durante la stampa e possono richiedere la procedura protetta sul T113.
4. Se il bootloader è raggiungibile, preferisci l'immagine **già collaudata su quella CFS** e con checksum confermato, non un'altra prova dello stesso firmware sperimentale. L'updater Creality ricomincia da offset zero: non esiste un resume garantito. Se la CFS non è più visibile o il trasferimento fallisce ancora, **ferma i tentativi**; non è assicurato un recupero software.
5. Dopo il rollback, verifica la risposta `A2` con **`mode=application`**, l'enumerazione CFS e i comandi applicativi. Un semplice `ACK` a `F0/02` **non basta**; il fallback `0B/01` è documentato ma va gestito solo da una procedura di manutenzione controllata. Controlla anche RS-485 e motori X/Y prima dell'uso.

**Incidente documentato — 24 ottobre 2026:** la CFG6 candidata al fix RFID [PR #60](https://github.com/MzTechnology97/k2-cfs-rfid-tools/pull/60) è rimasta nel loader dopo timeout `send fw data`; la precedente CFG6 v3.25 è stata ripristinata. Il log non prova un crash dell'applicazione candidata. **Non usare la build della PR #60 per un altro flash** finché non sarà qualificata. Vedi l'[analisi del trasferimento](https://github.com/MzTechnology97/k2-cfs-rfid-tools/blob/fix/cfg6-type4-runtime-accounting/firmware/v3.26-cfg6-type4-fix/FLASH_FAILURE_AUDIT_20261024_IT.md).
