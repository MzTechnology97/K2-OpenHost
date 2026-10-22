# Requisiti

## La stampante

| Voce | Requisito |
| --- | --- |
| Modello | Solo **Creality K2 Pro**. Gli strumenti controllano il modello Creality `F012` e la scheda `CR0CN200400C10` e rifiutano qualsiasi altra cosa. |
| Firmware stock | Preparato e provato sulla **1.1.0.94**. Le release più recenti (1.1.7.0 e successive) sono accettate con un avviso: il bootstrap della T113 e la modalità USB gadget (OTG) **non sono garantiti** su di esse. |
| SSH root | Attivato nelle impostazioni dello schermo. La password root stock è `creality_2024`. |
| Rete | Stampante e host nella stessa rete durante l'installazione. Dopo, HelixScreen usa la rete per raggiungere Moonraker. |
| Spazio libero | Circa 1,5 GB nella UDISK della stampante (immagini, HelixScreen, backup del vecchio slot B). |
| CFS | Opzionale. Da una a quattro unità. Sono supportati i firmware CFS 1.1.3 (stato a 4 byte) e 1.5.3 (stato a 6 byte). |

## L'host

| Voce | Requisito |
| --- | --- |
| Computer | Raspberry Pi 4, Pi 5 o **Compute Module 5** con almeno 2 GB di RAM. La macchina di riferimento è una CM5 (8 GB di RAM, 32 GB di eMMC) su una Waveshare CM5-IO-BASE-A, raffreddata dal Waveshare CM5-FAN-3007-B-5V (dissipatore all-in-one, ventola PWM a 4 pin). Va bene anche qualsiasi computer Debian/Ubuntu a 64 bit. |
| Sistema | **Raspberry Pi OS Lite (64-bit)**, Debian 12 bookworm. |
| Memoria | microSD o eMMC, 16 GB o più. |
| Alimentazione | L'alimentatore ufficiale della scheda. Una tensione insufficiente causa disconnessioni casuali. |
| USB | Una porta libera per il cavo della T113. Su una scheda base per CM5 la T113 dovrebbe essere da sola sul suo controller USB (vedi [Hardware host](../HOST.md#usb)). |
| Rete | Ethernet o Wi-Fi con accesso a internet durante l'installazione. |

### L'host di riferimento

Un Raspberry Pi **Compute Module 5** sulla scheda base Waveshare **CM5-IO-BASE-A**, con il dissipatore Waveshare **CM5-FAN-3007-B-5V** sul connettore ventola a 4 pin della scheda. Le porte USB 3.0 della CM5 danno alla T113 un controller USB tutto suo, e la ventola si comanda da Klipper (menu 36 dell'helper). Dettagli in [Hardware host](../HOST.md).

| CM5-IO-BASE-A | CM5-FAN-3007-B-5V |
| :---: | :---: |
| ![Scheda base Waveshare CM5-IO-BASE-A](../../images/hardware/cm5-io-base-a.jpg){ width="340" } | ![Dissipatore Waveshare CM5-FAN-3007-B-5V](../../images/hardware/cm5-fan-3007.jpg){ width="340" } |

## Cavi

| Cavo | Nota |
| --- | --- |
| USB dell'host verso la porta **Micro-USB di servizio** della K2 | Deve essere un cavo **dati**. I cavi di sola ricarica non funzionano. Si consiglia una spina **Micro-USB a 90° (ad angolo retto)** (vedi sotto). Non collegarlo né scollegarlo durante la stampa. |
| Telecamera della camera verso USB dell'host | In modalità OpenHost la telecamera della camera non può funzionare tramite la T113: **scollegala dalla T113** e ricablala a una porta USB dell'host. La **telecamera del nozzle non si può usare** in modalità OpenHost. |
| Cartographer3D verso USB dell'host | Opzionale, USB diretto all'host. |

### Dove si trova la porta Micro-USB di servizio

La porta di servizio è il connettore Micro-USB sulla **scheda T113** (cerchiato in rosso), accanto alla scheda madre nel vano dell'elettronica della stampante. È la porta che passa in modalità USB gadget: qui va il cavo dell'host.

<figure markdown="span">
  ![Porta Micro-USB di servizio della T113 sulla K2 Pro](../../images/hardware/t113-service-usb-marked.jpg){ width="520" }
  <figcaption>La porta Micro-USB di servizio della T113 (cerchio rosso) sulla K2 Pro di riferimento.</figcaption>
</figure>

!!! tip "Usa un cavo Micro-USB a 90°"
    La porta di servizio si trova sul bordo della scheda T113, vicino al telaio della stampante e agli altri cavi del vano elettronica. Una spina **Micro-USB ad angolo retto (90°)** lascia spazio al cavo, non sforza il connettore e mantiene stabile il collegamento. Scegli un cavo **dati**, abbastanza lungo da arrivare all'host senza tensione (2 m nell'esempio).

<figure markdown="span">
  ![Cavo dati Micro-USB a 90°](../../images/hardware/micro-usb-90-cable.jpg){ width="240" }
  <figcaption>Esempio di cavo dati Micro-USB a 90° verso USB-A (2 m, intrecciato).</figcaption>
</figure>

!!! warning "Ricablare dentro la stampante"
    Scollega prima la corrente di rete, e fai passare i cavi lontano da parti in movimento e zone calde. Il ricablaggio è a tuo rischio.

## Cosa smette di funzionare in modalità OpenHost

- La **porta USB esterna** della stampante: niente stampa da chiavetta USB, e la porta smette del tutto di funzionare. Invia i file da Mainsail o dallo slicer.
- **Telecamere tramite la T113**: la telecamera della camera passa all'host, quella del nozzle non è disponibile.
- **Cloud Creality e connessione diretta di Creality Print**: la T113 non esegue più i servizi di Creality. Usa la connessione Moonraker dello slicer.

## Un altro computer

Un computer Windows, macOS o Linux per scrivere la scheda dell'host (Raspberry Pi Imager) e collegarsi in SSH.

## Competenze

Dovresti saper:

- copiare comandi in un terminale SSH;
- leggere la console di Klipper e `klippy.log`;
- recuperare una stampante che non si avvia (spegnere e riaccendere, tornare allo slot A).

Altrimenti tieni il firmware stock. Vedi l'[esclusione di responsabilità](../DISCLAIMER.md).
