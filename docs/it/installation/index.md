# Installazione

Tutta l'installazione si guida dall'host con il **[K2-OpenHost Helper](../helper/index.md)**. Prepara l'host e, via SSH, la scheda T113 della stampante. Segui i passi nell'ordine.

!!! tip "Prima di iniziare"
    - Leggi i [Requisiti](../getting-started/requirements.md) e l'[esclusione di responsabilità](../DISCLAIMER.md).
    - Annota l'indirizzo IP della stampante (schermo: impostazioni di rete) e attiva l'SSH root sulla stampante.
    - Usa una scheda SD o un'immagine eMMC di riserva per l'host, così la configurazione attuale resta intatta.

| Passo | Cosa fai | Pagina |
| --- | --- | --- |
| 1 | Scrivi Raspberry Pi OS, esegui l'**installazione completa** dell'helper, riavvia | [Preparare l'host](host.md) |
| 2 | Collega il cavo; menu **23** controllo, **24** installazione del bootstrap T113, **26** avvio di prova, **27** conferma dello slot B, **32** collegamento dei controlli T113 | [Preparare la stampante](printer.md) |
| 3 | `doctor`, Mainsail, homing, riscaldatori, calibrazione di motori e taglierina, CFS, prima stampa sorvegliata | [Primo avvio e controlli](first-start.md) |

In seguito:

- [Aggiornamenti e release](updates.md): l'update manager di Mainsail, `helper.sh update`, le release, i programmi della T113, il firmware delle schede Creality.
- [Backup e ripristino](backup.md): i backup locali dell'helper e un backup della configurazione su GitHub.
- [Tornare allo stock](uninstall.md): lo slot A, in qualsiasi momento.

## Avvio rapido (utenti esperti)

```bash
sudo apt update && sudo apt install -y git
git clone https://github.com/MzTechnology97/k2-openhost-installer-helper.git ~/k2-openhost-installer-helper
~/k2-openhost-installer-helper/helper.sh
```

Scegli **1) Full install**, riavvia, collega la K2, esegui i menu **23**, **24**, **26**, poi **27** e **32**, poi:

```bash
~/k2-openhost-installer-helper/helper.sh doctor
```

Apri `http://<nome-o-ip-dell-host>/`.
