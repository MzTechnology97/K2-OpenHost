# Esclusione di responsabilità e limiti hardware

Aggiornato: **3 ottobre 2026**. [English](../en/DISCLAIMER.md)

## Esclusione di responsabilità

K2-OpenHost e tutti i repository pubblicati con esso (kalico-k2pro, k2-pro-custom-firmware, mainsail-k2openhost, k2-openhost-installer-helper, k2-openhost-firmware-tools e i fork collegati) sono strumenti **sperimentali** condivisi con la comunità e pensati **solo per un pubblico esperto**.

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
| **Fotocamera dell'ugello** | Non può essere gestita dal T113. | Ricablare il percorso originale del cavo e collegare la fotocamera **direttamente a una porta USB dell'host Linux esterno**; lo streaming si fa dall'host (per esempio con Crowsnest). |
| **Fotocamera della camera** | Non può essere gestita dal T113. | Come per la fotocamera dell'ugello: ricablarla e collegarla **direttamente all'host esterno**. |
| **Porta USB esterna** della stampante (chiavetta) | **Non può essere usata per stampare** da chiavetta e **smette completamente di funzionare** mentre il T113 è in modalità gadget. | Carica e stampa i file tramite Mainsail/Moonraker sull'host esterno. |
| **Cartographer3D** (opzionale) | Non passa dai canali gadget del T113. | Collegalo direttamente all'host esterno (vedi [Trasporto USB gadget](USB_GADGET.md)). |

Il ricablaggio all'interno della stampante è a tuo rischio: scollega prima l'alimentazione di rete e tieni i cavi lontani da parti in movimento e zone calde.

Questi limiti derivano dal cambio di ruolo di USB0 descritto in [Trasporto USB gadget](USB_GADGET.md#nota-sul-cambio-ruolo-usb). Sono previsti anche nell'architettura finale.
