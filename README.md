# K2-OpenHost

> **Experimental / Work in Progress — Sperimentale / Lavori in corso**

**English:** K2-OpenHost is a research project that explores moving the main Klipper/Moonraker workload of the Creality K2 series to an external Linux host while retaining as much of the original printer electronics as possible.

**Italiano:** K2-OpenHost è un progetto di ricerca che esplora lo spostamento del carico principale Klipper/Moonraker della serie Creality K2 su un host Linux esterno, mantenendo il più possibile l'elettronica originale della stampante.

The first development target is the **Creality K2 Pro**.

Il primo target di sviluppo è la **Creality K2 Pro**.

---

## Documentation / Documentazione

### English

- [Project architecture](docs/en/ARCHITECTURE.md)
- [USB Gadget and Micro-USB investigation](docs/en/USB_GADGET.md)
- [Current test status](docs/en/TEST_STATUS.md)
- [Roadmap](docs/en/ROADMAP.md)
- [Credits and references](docs/en/REFERENCES.md)

### Italiano

- [Architettura del progetto](docs/it/ARCHITECTURE.md)
- [Indagine USB Gadget e Micro-USB](docs/it/USB_GADGET.md)
- [Stato attuale dei test](docs/it/TEST_STATUS.md)
- [Roadmap](docs/it/ROADMAP.md)
- [Crediti e riferimenti](docs/it/REFERENCES.md)

---

## Target architecture / Architettura prevista

```text
Original K2 display + touch / Display + touch originali K2
                         |
                         v
                  Allwinner T113
             Tina Linux + HelixScreen
          USB gadget + byte-transparent bridges
                         |
                         | USB 2.0 High-Speed
                         v
                 External Linux host
          Kalico + Moonraker + Mainsail/Fluidd
                         |
          +--------------+--------------+
          |              |              |
          v              v              v
       Main MCU      Nozzle MCU     RS-485 bus
                                   X/Y + CFS path
```

### Main objective / Obiettivo principale

**EN:** The objective is not to replace the original K2 mainboard. The current design keeps the Allwinner T113 board and uses it as a lightweight display controller and hardware bridge, while an external Linux host runs the heavier Klipper/Kalico side of the system.

**IT:** L'obiettivo non è sostituire la mainboard originale della K2. Il progetto mantiene la scheda con Allwinner T113 e la utilizza come controller leggero del display e bridge hardware, mentre un host Linux esterno esegue la parte più pesante di Klipper/Kalico.

---

## Verified so far / Verificato finora

The following has been verified directly on a **K2 Pro** running Tina 5.0 / OpenWrt 21.02-SNAPSHOT and Linux 5.4.61:

Quanto segue è stato verificato direttamente su una **K2 Pro** con Tina 5.0 / OpenWrt 21.02-SNAPSHOT e Linux 5.4.61:

- USB0 is dual-role / USB0 è dual-role.
- In stock operation USB0 is a host path for the internal chamber camera / In modalità stock USB0 gestisce la camera interna.
- The USB Device Controller is exposed as `4100000.udc-controller`.
- The kernel includes USB Gadget, ConfigFS, FunctionFS and Generic Serial support.
- The service/recovery Micro-USB connector has been verified as the runtime USB device path to an external Linux host.
- Generic Serial gadget enumeration is verified at USB 2.0 High-Speed (480M), using VID:PID `0525:a4a6`.
- Three simultaneous ConfigFS serial functions are verified: `gser.usb0`, `gser.usb1`, `gser.usb2`.
- The external host enumerates the three interfaces as independent `usbserial_generic` ports.
- Main MCU path verified: `ttyGS0 <-> ttyS2`, 230400 baud, original `gd32f303xe` firmware.
- Nozzle MCU path verified: `ttyGS1 <-> ttyS3`, 230400 baud, original `gd32f303xb` firmware.
- Main and Nozzle MCU protocol sessions have been run simultaneously from external Kalico without reflashing the MCUs.
- RS-485 path verified: `ttyGS2 <-> ttyS5`, 230400 baud.
- Closed-loop X (`0x81`) and Y (`0x82`) controllers have both replied correctly to read-only address queries sent from the external host through the complete USB gadget -> T113 -> RS-485 path.
- `/dev/ttyS5` does not require Linux `TIOCSRS485` mode for the tested traffic; direction handling is transparent to the userspace bridge.
- CFS protocol validation is still pending. Initial CFS probes were intentionally inconclusive because the CFS unit was physically disconnected during that test session.

The currently verified runtime transport is therefore:

```text
External host
  /dev/ttyUSB0 <-> gser.usb0 / ttyGS0 <-> ttyS2 <-> Main MCU
  /dev/ttyUSB1 <-> gser.usb1 / ttyGS1 <-> ttyS3 <-> Nozzle MCU
  /dev/ttyUSB2 <-> gser.usb2 / ttyGS2 <-> ttyS5 <-> RS-485 (X/Y verified, CFS pending)
```

---

## Planned software split / Suddivisione software prevista

### Original K2 T113 board

- Tina Linux
- original LCD and touchscreen drivers
- HelixScreen
- USB Gadget transport
- byte-transparent UART bridge services
- only the hardware-specific services that prove necessary

### External host

- Raspberry Pi / Compute Module / other Linux SBC
- [Jacob10383/kalico](https://github.com/Jacob10383/kalico)
- Moonraker
- Mainsail and/or Fluidd
- Cartographer directly connected where appropriate
- K2-specific extras

---

## Safety / Sicurezza

**EN:** This project is experimental. Do not perform USB role switching or MCU bridge experiments while a print is running. Keep a known-good stock system backup or boot slot before making persistent changes.

**IT:** Questo progetto è sperimentale. Non eseguire commutazioni del ruolo USB o test di bridge verso gli MCU durante una stampa. Conservare sempre un backup o uno slot di sistema stock funzionante prima di applicare modifiche persistenti.

The USB and bridge experiments documented so far are runtime-only. On the tested K2 Pro, a reboot restores the normal stock USB-host behavior. Unbinding/rebinding the gadget recreates the `/dev/ttyGS*` endpoints, so active bridge processes must be restarted afterwards.

Gli esperimenti USB e bridge documentati finora sono eseguiti solo a runtime. Sulla K2 Pro testata, un riavvio ripristina il normale comportamento USB-host stock. Unbind/rebind del gadget ricrea gli endpoint `/dev/ttyGS*`, quindi i processi bridge attivi devono essere riavviati.

---

## Credits / Crediti

K2-OpenHost builds on public work from the Creality, Klipper/Kalico and K2 reverse-engineering communities. The project does **not** claim authorship of discoveries originating elsewhere.

K2-OpenHost si basa sul lavoro pubblico delle community Creality, Klipper/Kalico e reverse engineering K2. Il progetto **non** rivendica come proprie le scoperte provenienti da altri progetti.

See / Vedi:

- [English credits and references](docs/en/REFERENCES.md)
- [Crediti e riferimenti in italiano](docs/it/REFERENCES.md)

Key projects include:

- [CrealityOfficial/K2_Series_Klipper](https://github.com/CrealityOfficial/K2_Series_Klipper)
- [grant0013/k2-reverse-engineering](https://github.com/grant0013/k2-reverse-engineering)
- [prestonbrown/helixscreen](https://github.com/prestonbrown/helixscreen)
- [KalicoCrew/kalico](https://github.com/KalicoCrew/kalico)
- [Jacob10383/kalico](https://github.com/Jacob10383/kalico)

---

## Contributions / Contributi

When contributing test results, please identify each result as one of the following:

Quando si contribuisce con risultati di test, indicare chiaramente se il risultato è:

- **Verified on hardware / Verificato su hardware**
- **Derived from public source or configuration / Derivato da sorgenti o configurazioni pubbliche**
- **Inferred, not yet tested / Dedotto, non ancora testato**

This distinction is important because the project is still in an active reverse-engineering and validation phase.
