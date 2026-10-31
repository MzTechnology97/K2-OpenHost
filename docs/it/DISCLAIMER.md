# Esclusione di responsabilità e limiti hardware

Aggiornato: **3 ottobre 2026**. [English](../en/DISCLAIMER.md)

## Esclusione di responsabilità

K2-OpenHost e tutti i repository pubblicati con esso (kalico-k2pro, k2-openhost-t113-bootstrap, mainsail-k2openhost, k2-openhost-installer-helper, k2-openhost-firmware-tools, l'archiviato k2-pro-custom-firmware e i fork collegati) sono strumenti **sperimentali** condivisi con la comunità e pensati **solo per un pubblico esperto**.

Usandoli accetti che:

- **La garanzia del produttore decade.** Far funzionare la stampante da un host esterno, cambiare il ruolo USB del T113 e sostituire il software originale non sono supportati da Creality.
- **La stampante può subire danni irreparabili.** Valori di configurazione errati, errori di movimento o di homing, o una connessione persa possono far urtare la testina o il piano, surriscaldare componenti o rompere parti meccaniche ed elettroniche.
- **Il firmware può andare in brick.** Modifiche al sistema del T113 o ai firmware delle periferiche possono lasciare la stampante incapace di avviarsi. Conserva un backup originale funzionante e un metodo di ripristino prima di qualsiasi modifica permanente.
- **C'è rischio di incendio.** I riscaldatori (ugello, piano, camera) sono comandati da software che gira sull'host esterno. Un guasto software, di cablaggio, di alimentazione o di comunicazione può lasciare un riscaldatore acceso. Non lasciare mai la stampante senza sorveglianza, tieni un rilevatore di fumo funzionante vicino e un estintore a portata di mano.
- **Usi questi strumenti interamente a tuo rischio.** Sono forniti "così come sono", senza alcuna garanzia. **Gli autori e i contributori non sono responsabili di alcun danno a cose o a persone**, lesioni, perdita di dati o altre conseguenze derivanti dall'uso, dall'uso improprio o dall'impossibilità di usarli.

Se non sei a tuo agio nella diagnosi di Linux, Klipper e dell'elettronica delle stampanti 3D, o non puoi accettare questi rischi, non usare K2-OpenHost: mantieni il firmware originale.

Anche le licenze software dei singoli repository (GPL-3.0 e altre) escludono ogni garanzia; questa pagina aggiunge i rischi hardware e di sicurezza specifici di questo progetto.

## Limiti hardware in modalità OpenHost

In K2-OpenHost la scheda T113 originale smette di essere il computer della stampante: la sua porta USB di servizio passa in **modalità USB gadget (device)** per portare all'host esterno i canali Main MCU, Nozzle MCU e RS-485/CFS. Questo cambia la topologia USB originale, con queste conseguenze:

| Componente | In modalità OpenHost | Cosa fare |
| --- | --- | --- |
| **Fotocamera della camera** | Non può essere gestita dal T113. | **Scollegarla dal T113** e ricablarla **direttamente a una porta USB dell'host Linux esterno**; lo streaming si fa dall'host con Crowsnest (vedi [Fotocamera della camera](CAMERA.md)). |
| **Fotocamera dell'ugello** | **Non utilizzabile**: in modalità OpenHost il T113 non può gestirla. | Nessuna: la fotocamera dell'ugello non è disponibile in modalità OpenHost. Torna a funzionare quando la stampante avvia il firmware stock (slot A). |
| **Porta USB esterna** della stampante (chiavetta) | **Non può essere usata per stampare** da chiavetta e **smette completamente di funzionare** mentre il T113 è in modalità gadget. | Carica e stampa i file tramite Mainsail/Moonraker sull'host esterno. |
| **Cartographer3D** (opzionale) | Non passa dai canali gadget del T113. | Collegalo direttamente all'host esterno (vedi [Trasporto USB gadget](USB_GADGET.md)). |

Il ricablaggio all'interno della stampante è a tuo rischio: scollega prima l'alimentazione di rete e tieni i cavi lontani da parti in movimento e zone calde.

Questi limiti derivano dal cambio di ruolo di USB0 descritto in [Trasporto USB gadget](USB_GADGET.md#nota-sul-cambio-ruolo-usb). Sono previsti anche nell'architettura finale.

## Uso

- **Danni meccanici.** Valori di configurazione sbagliati, un errore di homing o di tastatura, o un collegamento perso durante un movimento possono far urtare la testina contro il piatto o il telaio.
- **Il cavo USB è vitale per la stampa.** Staccare o urtare il cavo della T113, o riavviare l'host, ferma subito la stampa: Klipper va in shutdown. Usa un buon cavo dati con spina a 90° e fissalo.
- **L'alimentazione dell'host è quella della stampa.** Se l'host perde corrente, la stampa è persa anche se la stampante resta accesa. Usa l'alimentatore ufficiale dell'host; un UPS per entrambi è una buona idea.
- **Nessuna modifica durante la stampa.** Non riavviare Klipper, non aggiornare, non flashare, non modificare i valori runtime della CFS e non riavviare la T113 durante una stampa.
- **Niente OTA Creality dallo slot B.** Un OTA nello slot B sovrascriverebbe lo slot A, quindi è disattivato. Dallo slot A un OTA sostituisce lo slot B di K2-OpenHost. Il firmware delle schede si aggiorna dallo slot B con `k2oh-mcu-fw` (menu 31 dell'helper).
- **Modello supportato:** solo Creality K2 Pro. Gli strumenti rifiutano altri modelli e schede.
- **Firmware CFS sperimentale.** Il [firmware CFS modificato](cfs-firmware/index.md) non è qualificato per la produzione: un'immagine difettosa può fermare la CFS finché non si flasha un'immagine di recupero, e un [problema aperto](https://github.com/MzTechnology97/k2-cfs-rfid-tools/issues/9) fa sì che la CFS possa dichiararsi ferma mentre sta ancora alimentando. Flasha solo a stampante ferma e tieni l'immagine di recupero v3.22. Il firmware CFS originale funziona benissimo con K2-OpenHost.
- **Conosci la tua stampante.** K2-OpenHost sostituisce l'intero software, quindi il supporto sei tu. Controlla lo [stato dei test](TEST_STATUS.md) prima di affidarti a una funzione.
