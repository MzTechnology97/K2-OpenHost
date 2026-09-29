# Credits and References

K2-OpenHost is an independent experimental project. It builds on public documentation, source code, reverse-engineering work and community research produced by several projects and developers.

This repository does **not** claim authorship of findings that originated elsewhere. Whenever possible, K2-OpenHost distinguishes between:

- observations independently verified on the project's K2 Pro test hardware;
- information derived from public source code or documentation;
- design hypotheses that still require testing.

## Creality official K2 Klipper sources

### CrealityOfficial/K2_Series_Klipper

Repository:

https://github.com/CrealityOfficial/K2_Series_Klipper

Credit: **CrealityOfficial**

Used as a primary reference for:

- K2-series Klipper configuration structure;
- MCU declarations;
- serial-port assignments on known K2 variants;
- printer-specific extras and configuration names;
- hardware model/configuration differences.

This is an important reference when comparing the K2 Pro test unit against known K2-series configurations.

## K2 reverse engineering

### grant0013/k2-reverse-engineering

Repository:

https://github.com/grant0013/k2-reverse-engineering

Credit: **grant0013** and contributors

Important reference material includes work on:

- K2 system architecture;
- communication paths between host, MCU(s) and motor controllers;
- RS-485 protocol investigation;
- motor-controller parameter mapping;
- analysis of Creality userspace components and services;
- transparent communication mechanisms used by K2 motor-control infrastructure.

K2-OpenHost relies on this work as a major source when planning future MCU and closed-loop transport experiments.

### grant0013/K2-OpenKlipper

Repository:

https://github.com/grant0013/K2-OpenKlipper

Credit: **grant0013** and contributors

Relevant as a practical reference for replacing or reimplementing parts of the Creality K2 software stack and for understanding which K2 features can be supported without depending entirely on the stock host environment.

## HelixScreen and K2 platform research

### prestonbrown/helixscreen

Repository:

https://github.com/prestonbrown/helixscreen

Credit: **prestonbrown** and HelixScreen contributors

Used as a reference for:

- K2-series display support;
- framebuffer and touchscreen access;
- K2 platform research;
- using the original physical display without the stock Creality UI;
- remote Moonraker UI architecture.

K2-OpenHost currently plans to use HelixScreen on the original T113/display side of the system.

## Kalico

### KalicoCrew/kalico

Repository:

https://github.com/KalicoCrew/kalico

Credit: **KalicoCrew** and contributors

Kalico is the upstream community project from which the preferred external-host firmware stack is derived.

### Jacob10383/kalico

Repository:

https://github.com/Jacob10383/kalico

Credit: **Jacob10383** and upstream Kalico contributors

This fork is currently the preferred candidate for the K2-OpenHost external Linux host because of its relevance to K2 experimentation and the broader K2 community ecosystem.

K2-OpenHost does not redistribute or claim ownership of Kalico or Jacob10383's changes.

## Additional K2 community work

### night-gnida/k2-vanilla-public

Repository:

https://github.com/night-gnida/k2-vanilla-public

Credit: **night-gnida** and contributors

Useful as a reference for experiments that replace parts of the stock K2 Klipper environment while retaining original printer hardware and parts of the Creality software environment.

## Linux USB Gadget framework

### Linux kernel USB Gadget / ConfigFS documentation

Project:

https://www.kernel.org/

Relevant upstream documentation includes the Linux USB Gadget ConfigFS and gadget-testing documentation.

Credit: **Linux kernel developers and documentation contributors**

Used as a reference for:

- USB Device Controller concepts;
- ConfigFS gadget construction;
- generic serial gadget (`gser`);
- UDC binding;
- expected gadget states and host enumeration behavior.

The K2 Pro experiments documented in this repository use the vendor Tina kernel implementation, but the Linux Gadget framework provides the underlying model.

## Allwinner Tina Linux

Credit: **Allwinner Technology / Tina Linux developers**

The stock K2 Pro host runs Tina Linux based on OpenWrt. Public Tina Linux documentation and the software present on the printer itself are references for:

- USB0 OTG role switching;
- vendor sysfs nodes such as `usb_host` and `usb_device`;
- ConfigFS initialization;
- `/bin/setusbconfig` behavior;
- FunctionFS/ADB and gadget setup patterns.

The most important USB findings in K2-OpenHost were not assumed solely from documentation: role switching and Generic Serial gadget creation were independently verified on the project's K2 Pro hardware.

## Archworks K2 Plus reverse-engineering notes

Reference:

https://archworks.co/docs/k2-plus-reverse-engineering/

Credit: **Archworks authors**

Used as an additional independent source when comparing K2-series hardware and userspace observations.

## Project-specific hardware verification

The following results currently documented by K2-OpenHost were independently observed on the project's K2 Pro test machine:

- `CREALITY CAM` at USB ID `1d6c:0103` on USB0 host bus;
- USB0 EHCI controller at `4101000.ehci0-controller`;
- USB0 OHCI controller at `4101400.ohci0-controller`;
- UDC at `4100000.udc-controller`;
- successful runtime host-to-device role switch;
- clean camera disconnect during the role switch;
- presence of USB Gadget/ConfigFS/Generic Serial kernel options;
- stock Tina `/bin/setusbconfig` support for `gser`;
- creation of `/dev/ttyGS0`;
- creation and binding of `gser.usb0`;
- gadget VID `0x0525`, PID `0xa4a6`, product `Gadget Serial`.

These observations are documented to add hardware-specific validation, not to supersede or appropriate the reverse-engineering work listed above.

## Attribution policy for future contributions

When adding material from another project:

1. link the original project/document;
2. credit the original author or project where identifiable;
3. do not copy large sections of documentation verbatim;
4. describe what K2-OpenHost independently tested;
5. distinguish confirmed behavior from inference.

If an attribution is missing or inaccurate, please open an issue or pull request so it can be corrected.
