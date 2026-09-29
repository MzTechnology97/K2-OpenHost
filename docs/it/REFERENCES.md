# Crediti e riferimenti

K2-OpenHost è un progetto sperimentale indipendente. Si basa su documentazione pubblica, codice sorgente, reverse engineering e ricerca community prodotti da diversi sviluppatori e progetti.

Questo repository **non rivendica come proprie** le scoperte provenienti da altri lavori. Quando possibile, K2-OpenHost distingue chiaramente tra:

- osservazioni verificate direttamente sull'hardware K2 Pro utilizzato dal progetto;
- informazioni derivate da sorgenti o documentazione pubblica;
- ipotesi progettuali che devono ancora essere testate.

## Sorgenti ufficiali Creality K2 Klipper

### CrealityOfficial/K2_Series_Klipper

Repository:

https://github.com/CrealityOfficial/K2_Series_Klipper

Crediti: **CrealityOfficial**

Utilizzato come riferimento principale per:

- struttura della configurazione Klipper della serie K2;
- dichiarazioni MCU;
- assegnazioni delle porte seriali sulle varianti K2 note;
- extras e nomi di configurazione specifici della stampante;
- differenze hardware/configurazione tra modelli.

È un riferimento importante per confrontare la K2 Pro testata con le configurazioni note della serie K2.

## Reverse engineering K2

### grant0013/k2-reverse-engineering

Repository:

https://github.com/grant0013/k2-reverse-engineering

Crediti: **grant0013** e contributori

Materiale particolarmente importante relativo a:

- architettura del sistema K2;
- percorsi di comunicazione tra host, MCU e controller motore;
- reverse engineering del protocollo RS-485;
- mappatura dei parametri dei controller motore;
- analisi dei componenti e servizi userspace Creality;
- meccanismi di comunicazione trasparente utilizzati dall'infrastruttura motor-control K2.

K2-OpenHost utilizza questo lavoro come riferimento fondamentale per pianificare i futuri test MCU e closed-loop.

### grant0013/K2-OpenKlipper

Repository:

https://github.com/grant0013/K2-OpenKlipper

Crediti: **grant0013** e contributori

Riferimento pratico importante per la sostituzione o reimplementazione di parti dello stack software K2 e per capire quali funzioni possono essere mantenute senza dipendere completamente dall'ambiente host stock Creality.

## HelixScreen e ricerca piattaforma K2

### prestonbrown/helixscreen

Repository:

https://github.com/prestonbrown/helixscreen

Crediti: **prestonbrown** e contributori HelixScreen

Utilizzato come riferimento per:

- supporto display serie K2;
- accesso framebuffer e touchscreen;
- ricerca sulla piattaforma K2;
- utilizzo del display fisico originale senza UI Creality stock;
- architettura UI con Moonraker remoto.

K2-OpenHost prevede attualmente di utilizzare HelixScreen sul lato T113/display originale.

## Kalico

### KalicoCrew/kalico

Repository:

https://github.com/KalicoCrew/kalico

Crediti: **KalicoCrew** e contributori

Kalico è il progetto community upstream da cui deriva lo stack firmware preferito per l'host esterno.

### Jacob10383/kalico

Repository:

https://github.com/Jacob10383/kalico

Crediti: **Jacob10383** e contributori upstream Kalico

Questo fork è attualmente il candidato preferito per l'host Linux esterno di K2-OpenHost, per la sua rilevanza nell'ecosistema di sperimentazione K2.

K2-OpenHost non redistribuisce né rivendica la proprietà di Kalico o delle modifiche di Jacob10383.

## Altri lavori community K2

### night-gnida/k2-vanilla-public

Repository:

https://github.com/night-gnida/k2-vanilla-public

Crediti: **night-gnida** e contributori

Utile come riferimento per esperimenti di sostituzione di parti dell'ambiente Klipper stock K2 mantenendo l'hardware originale e parte dell'ambiente software Creality.

## Framework Linux USB Gadget

### Documentazione Linux kernel USB Gadget / ConfigFS

Progetto:

https://www.kernel.org/

La documentazione upstream rilevante comprende USB Gadget ConfigFS e gadget-testing.

Crediti: **sviluppatori Linux kernel e contributori della documentazione**

Utilizzato come riferimento per:

- concetti USB Device Controller;
- costruzione gadget tramite ConfigFS;
- generic serial gadget (`gser`);
- binding UDC;
- stati attesi del gadget ed enumerazione lato host.

Gli esperimenti K2 Pro documentati nel repository usano l'implementazione kernel vendor Tina, ma il modello sottostante è il framework Linux Gadget.

## Allwinner Tina Linux

Crediti: **Allwinner Technology / sviluppatori Tina Linux**

L'host stock K2 Pro esegue Tina Linux basato su OpenWrt. La documentazione Tina Linux pubblica e il software presente direttamente sulla stampante vengono utilizzati come riferimento per:

- role switching OTG USB0;
- nodi sysfs vendor come `usb_host` e `usb_device`;
- inizializzazione ConfigFS;
- comportamento di `/bin/setusbconfig`;
- pattern FunctionFS/ADB e configurazione gadget.

Le principali scoperte USB di K2-OpenHost non sono state semplicemente dedotte dalla documentazione: il role switching e la creazione del Generic Serial gadget sono stati verificati direttamente sulla K2 Pro di test.

## Note reverse engineering K2 Plus di Archworks

Riferimento:

https://archworks.co/docs/k2-plus-reverse-engineering/

Crediti: **autori Archworks**

Utilizzato come ulteriore fonte indipendente per confrontare osservazioni hardware e userspace della serie K2.

## Verifiche hardware specifiche K2-OpenHost

I seguenti risultati documentati in K2-OpenHost sono stati osservati direttamente sulla K2 Pro utilizzata per i test:

- `CREALITY CAM` con USB ID `1d6c:0103` sul bus USB0 host;
- controller USB0 EHCI `4101000.ehci0-controller`;
- controller USB0 OHCI `4101400.ohci0-controller`;
- UDC `4100000.udc-controller`;
- commutazione runtime host -> device riuscita;
- disconnessione pulita della camera durante la commutazione;
- presenza delle opzioni kernel USB Gadget/ConfigFS/Generic Serial;
- supporto `gser` nel tool Tina stock `/bin/setusbconfig`;
- creazione di `/dev/ttyGS0`;
- creazione e binding di `gser.usb0`;
- gadget VID `0x0525`, PID `0xa4a6`, product `Gadget Serial`.

Queste osservazioni servono ad aggiungere validazione hardware specifica e non a sostituire o appropriarsi del lavoro di reverse engineering elencato sopra.

## Politica di attribuzione per i futuri contributi

Quando si aggiunge materiale proveniente da un altro progetto:

1. inserire il link alla fonte originale;
2. attribuire il credito all'autore/progetto originale quando identificabile;
3. non copiare grandi sezioni di documentazione alla lettera;
4. descrivere chiaramente cosa è stato verificato indipendentemente da K2-OpenHost;
5. distinguere sempre comportamento confermato e semplice deduzione.

Se un'attribuzione risulta mancante o imprecisa, è possibile aprire una issue o pull request per correggerla.
