# 1. Preparare l'host

Non serve esperienza con Linux: ogni comando si può copiare e incollare.

## Scrivere la scheda

1. Installa [Raspberry Pi Imager](https://www.raspberrypi.com/software/) sul tuo computer.
2. **Choose device:** la tua scheda (Raspberry Pi 5, CM5, ...).
3. **Choose OS:** *Raspberry Pi OS (other)* → **Raspberry Pi OS Lite (64-bit)**. La versione Lite non ha desktop e lascia più risorse a Klipper.
4. **Choose storage:** la microSD, oppure l'eMMC della CM5 tramite `rpiboot`.
5. **Next** → **Edit settings**:
    - **hostname:** `k2host` (Mainsail sarà su `http://k2host.local/`);
    - **username e password:** per esempio `pi` e una password che ricorderai;
    - **Wi-Fi** (se non usi Ethernet) e il tuo paese;
    - **Services:** **Enable SSH** con autenticazione a password.
6. **Save**, **Yes**, attendi la fine della scrittura.

## Primo avvio e SSH

1. Inserisci la scheda, collega l'Ethernet se la usi, accendi e attendi due minuti.
2. Trova l'host: `ping k2host.local`, oppure cerca `k2host` nell'elenco dei dispositivi del router.
3. Collegati da un terminale (Windows: tasto destro su Start → *Terminale*):

    ```bash
    ssh pi@k2host.local
    ```

    Rispondi `yes` alla domanda sull'impronta e digita la password (mentre scrivi non compare nulla).

4. Aggiorna il sistema e installa Git:

    ```bash
    sudo apt update && sudo apt full-upgrade -y
    sudo apt install -y git
    ```

## Scaricare ed eseguire l'helper

```bash
git clone https://github.com/MzTechnology97/k2-openhost-installer-helper.git ~/k2-openhost-installer-helper
~/k2-openhost-installer-helper/helper.sh
```

![Menu dell'helper](../../images/helper/cli-menu.png)

Digita `1` (**Full install**) e conferma. Durante l'installazione:

- ogni passo inizia con un titolo `==>` e ogni azione completata mostra un `✔` verde;
- le righe gialle con `!` sono informazioni;
- le domande accettano la risposta suggerita (lettera maiuscola) con Invio:

| Domanda | Significato | Consigliato |
| --- | --- | --- |
| Stop and disable ModemManager? | Interroga le porte seriali e disturba i canali della K2 | Sì |
| Remove brltty? | Servizio per display Braille che si prende i dispositivi seriali USB | Sì |
| Allow nginx to reach `/home/pi/mainsail`? | Permette al web server di leggere Mainsail nella tua cartella home | Sì |
| Move it aside and clone ...? | Esiste già una cartella con lo stesso nome; viene rinominata, mai cancellata | Sì |

L'installazione completa richiede 10–30 minuti e termina con un riepilogo che mostra l'indirizzo di Mainsail. Senza domande: `helper.sh --yes install full`.

## Cosa mette sull'host l'installazione completa

| Componente | Dettaglio |
| --- | --- |
| Preparazione dell'host | Strumenti di compilazione, gruppi `dialout`/`tty`, nomi udev `/dev/k2-main`, `/dev/k2-nozzle`, `/dev/k2-rs485`, `/dev/k2-cartographer`; ModemManager fermato, brltty rimosso; `~/printer_data` |
| Kalico K2-OpenHost | `~/klipper` (`kalico-k2pro`, branch `k2-pro-openhost`), `~/klippy-env`, `klipper.service` e lo start gate (attende fino a 60 s i tre canali) |
| Configurazione K2 Pro | Il profilo da `~/klipper/config/k2` in `~/printer_data/config`: `printer.cfg` e i file in `macros/` |
| Moonraker | Moonraker upstream con il suo installer, `moonraker.conf` per una rete domestica, voci dell'update manager |
| Mainsail K2-OpenHost | Ultima release precompilata servita da nginx sulla porta 80 |
| Extra dell'installazione completa | Moonraker timelapse e Klippain Shake&Tune |
| Controllo di salute automatico | Il doctor dopo ogni avvio e modifica apt, riportato nella console di Klipper |

Componenti opzionali dal menu: Cartographer3D, Crowsnest (con la correzione per la telecamera Creality), MCU host `[mcu rpi]`, Spoolman, Mobileraker, OctoEverywhere, la ventola della CM5 da Klipper (menu 36). Vedi il [riferimento del menu](../helper/menu.md).

## Riavviare una volta

```bash
sudo reboot
```

Serve ad applicare i gruppi delle porte seriali assegnati al tuo utente. Ricollegati con `ssh` dopo un minuto, poi continua con [2. Preparare la stampante](printer.md).

## La tua configurazione non viene mai sovrascritta

L'helper copia il profilo K2 Pro in `~/printer_data/config`. Un'esecuzione successiva mantiene i tuoi file: quando il profilo è cambiato e tu hai modificato la tua copia, la nuova versione del profilo viene salvata accanto come `<file>.k2oh-new`. `helper.sh config diff` (menu 18) mostra le differenze.

![Profilo installato](../../images/helper/cli-config.png)
