# 2. Preparare la stampante (slot B della T113)

Il **bootstrap T113** scrive un sistema K2-OpenHost nello **slot B** libero della T113: i bridge USB gadget, HelixScreen puntato al tuo host, il servizio di controllo e gli strumenti per il firmware. **Lo slot A, il sistema attuale della stampante, non viene mai scritto** e resta la tua via di ritorno.

!!! important "Versione del firmware"
    Preparato e provato sul firmware stock della K2 Pro **1.1.0.94**. Le release più recenti sono accettate con un avviso, ma su di esse il bootstrap e la modalità USB gadget (OTG) **non sono garantiti**.

## Prima di iniziare

- [ ] L'host è installato e riavviato ([passo 1](host.md)).
- [ ] L'SSH root è attivo sulla stampante e conosci il suo indirizzo IP.
- [ ] Il cavo **dati** collega una porta USB dell'host alla porta **Micro-USB di servizio** della scheda T113 (cerchio rosso qui sotto). Si consiglia una spina Micro-USB a 90°: entra accanto al telaio senza sforzare il connettore.
- [ ] La stampante è ferma, con circa 1,5 GB liberi nella UDISK.

<figure markdown="span">
  ![Porta Micro-USB di servizio della T113 sulla K2 Pro](../../images/hardware/t113-service-usb-marked.jpg){ width="480" }
  <figcaption>La porta Micro-USB di servizio della T113: qui va il cavo dell'host.</figcaption>
</figure>

## Controllare la stampante (menu 23)

```bash
cd ~/k2-openhost-installer-helper
./helper.sh t113 check
```

Sola lettura. Chiede l'IP della stampante, conferma l'IP dell'host, poi controlla via SSH che la stampante sia una K2 Pro (modello `F012`, scheda `CR0CN200400C10`), lo slot in esecuzione, lo spazio libero e il firmware dello slot A, e mostra la release Creality da cui verrebbe costruito lo slot B.

![Controllo T113](../../images/helper/cli-t113-check.png)

## Installare il bootstrap (menu 24)

```bash
./helper.sh t113 install
```

1. Conferma l'avviso, inserisci l'**IP della stampante** e l'**IP dell'host** come lo vede la stampante (Invio accetta la proposta).
2. Digita una volta la password root della stampante (`creality_2024` sullo stock).
3. L'helper ripete i controlli, poi propone la **release Creality** da cui costruire lo slot B: la release dello slot A se Creality la elenca ancora, altrimenti l'ultima.
4. Scarica l'OTA Creality (130–145 MB) dalla CDN di Creality, la verifica con l'elenco MD5 dell'immagine stessa e **costruisce lo slot B**. Il progetto non ridistribuisce nessun file Creality.
5. Rispondi **sì** per installare **HelixScreen** (consigliato).
6. I file vengono caricati sulla stampante e verificati con SHA-256; sulla stampante gira `install-slot-b.sh --check`.
7. **Conferma** per scrivere lo slot B. La stampante salva l'ambiente U-Boot e il vecchio slot B, scrive e rilegge `bootB` e `rootfsB`, e copia dallo slot A chiavi SSH, chiavi host e reti Wi-Fi.

A questo punto si avvia ancora lo slot A per impostazione predefinita.

## Avvio di prova (menu 26)

```bash
./helper.sh t113 boot-b
```

Lo slot B si avvia **una volta**. La prima cosa che fa il suo avvio è reimpostare il prossimo avvio sullo slot A, quindi **se qualcosa va storto, spegni e riaccendi la stampante e torna allo slot A**.

Dopo l'avvio di prova:

1. Al primo avvio HelixScreen si installa da solo (circa un minuto), già puntato al tuo host.
2. Klipper sull'host si collega da solo (lo start gate attende fino a 60 s i tre canali). Mainsail mostra la stampante pronta.
3. Se funzionano entrambi, conferma lo slot B.

## Confermare lo slot B (menu 27)

```bash
./helper.sh t113 commit
```

Lo slot B diventa quello predefinito. Il menu **28** (`t113 boot-a`) torna allo slot A in qualsiasi momento; il menu **25** (`t113 status`) mostra lo slot in esecuzione, il prossimo avvio e il flag di prova.

## Collegare i controlli della T113 (menu 32)

```bash
./helper.sh t113 link
```

Collega Kalico e Moonraker a `k2oh-ctl` sulla stampante: copia il token condiviso in `~/printer_data/config/k2oh_t113.token`, imposta `host` in `macros/k2_t113.cfg` e scrive il dispositivo di alimentazione Moonraker `K2_MCU_Power`. Ottieni:

- `BOARD_STATUS`: telemetria della T113 e stato di ogni bridge;
- `BUZZER`, `M300` e i suoni del cicalino (fine stampa, pausa, errore, ...);
- `USB_BRIDGES_RESTART CONFIRM=1`, `MCU_POWER_CYCLE CONFIRM=1`, `SCREEN_RESTART`;
- l'alimentazione delle MCU come dispositivo di alimentazione Moonraker, bloccato durante la stampa.

Dopo, riavvia Moonraker e Klipper (menu 22).

## Fuso orario

La T113 esce con l'ora della Cina. `./helper.sh t113 timezone` dà allo slot B il fuso orario dell'host, così i log coincidono; lo fanno anche `boot-b`, `commit` e `update`.

## Firmware delle schede (opzionale)

Lo slot B esegue `mcu_update` di Creality a ogni avvio, che mantiene le schede alla release firmware dello slot B. Per portare tutte le schede all'**ultima** release Creality usa il menu **31**; vedi [Aggiornamenti](updates.md#firmware-delle-schede-creality).

## Se qualcosa va storto

| Sintomo | Cosa fare |
| --- | --- |
| La stampante non torna dopo l'avvio di prova | Spegnila e riaccendila: torna allo slot A. Leggi `/mnt/UDISK/.k2openhost/setup.log` dallo slot A. |
| Klipper non si collega | `./helper.sh doctor`. Sulla stampante: `logread \| grep -E "k2oh\|bridge"`. Vedi [Risoluzione problemi](../reference/troubleshooting.md#host-non-vede-la-stampante). |
| Lo schermo resta sul logo di avvio | Sulla stampante: `k2oh-setup status`, `cat /mnt/UDISK/.k2openhost/setup.log`, poi esegui di nuovo `k2oh-setup`. |
| HelixScreen non raggiunge Moonraker | IP dell'host sbagliato: menu 29 oppure `k2oh-setup --host <IP>` sulla stampante. |
| Niente Wi-Fi nello slot B | Imposta il Wi-Fi da HelixScreen, oppure copia `/etc/wifi/wpa_supplicant/wpa_supplicant.conf` dallo slot A. |

La guida completa lato stampante è nel [repository del bootstrap](https://github.com/MzTechnology97/k2-openhost-t113-bootstrap#readme) e in [Bootstrap T113](../T113_BOOTSTRAP.md).
