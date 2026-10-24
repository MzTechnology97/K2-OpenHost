# Flash and roll back

Flashing goes through the helper's **menu 40 (Experimental CFS firmware)**. The helper never downloads or flashes by itself: you place the image, it verifies it, you confirm with a phrase, and the actual flash is done by **Creality's own tools** on the T113.

!!! warning "Before you start"
    - Printer **idle**, no print running or paused, heaters off.
    - T113 **slot B** running, bootstrap 0.1.2 or later, T113 controls linked (menu 32).
    - The **v3.22 recovery image** (and CFG5T if you go to CFG6) downloaded next to the image you flash.
    - In `box.cfg`, keep `auto_apply: False` for the first start on the new firmware.

## 1. Download the image to the host

From the helper folder on the host:

```bash
cd ~/k2-openhost-installer-helper
F=cfs0_050_G32-cfs0_000_153-runtime-config-v3_25-K2OH-CFG6-EXPERIMENTAL.bin
curl -fL --retry 3 -o firmware/custom-cfs/$F \
  https://raw.githubusercontent.com/MzTechnology97/k2-cfs-rfid-tools/main/firmware/v3.25-cfg6-lab/$F
sha256sum firmware/custom-cfs/$F
```

The digest must be `6579eb552210d6b2b84fbbbdf2749bc8d310b324ffb095cf9662e7cd0acc6cc6`. Download the recovery image the same way:

```bash
R=cfs0_050_G32-cfs0_000_153-runtime-config-v3_22-READONLY-DIAG-EXPERIMENTAL.bin
curl -fL --retry 3 -o firmware/custom-cfs/$R \
  https://raw.githubusercontent.com/MzTechnology97/k2-cfs-rfid-tools/main/firmware/v3.22-readonly-state-probes/$R
sha256sum firmware/custom-cfs/$R    # 40dbaad88de7b6f9435592fa03b081e9b96663a9e84896b1ad8021a8f13cf8c7
```

Keep the exact original file names: the menu lists only images that are both in `manifest.json` and present with the expected name and digest.

## 2. Flash from menu 40

```bash
K2OH_NO_UPDATE_CHECK=1 ./helper.sh experimental-cfs
```

1. Choose the image (for example **CFG6 v3.25**). Menu numbers can differ between hosts: check the file name and SHA-256 every time.
2. The helper checks the SHA-256 and that the file name encodes the exact CFS hardware and application, then shows the target and the risks.
3. Type exactly `FLASH EXPERIMENTAL CFS`. `--yes` never bypasses this.
4. The guarded path runs:
    1. SHA-256 verified on the host;
    2. the installed bootstrap must support the guarded custom-image path;
    3. upload to the T113 and SHA-256 verified again there;
    4. print state checked, Klipper stopped on the host;
    5. `k2oh-mcu-fw apply --cfs --cfs-image ...` on the T113, which flashes with `mcu_util_485` and checks the app header, CRC, size, stack pointer and reset vector;
    6. the transfer copy is removed from the T113.

The same operation from the command line:

```bash
./helper.sh t113 mcu-fw apply --cfs \
  --cfs-image ./firmware/custom-cfs/cfs0_050_G32-cfs0_000_153-runtime-config-v3_25-K2OH-CFG6-EXPERIMENTAL.bin \
  --cfs-sha256 6579eb552210d6b2b84fbbbdf2749bc8d310b324ffb095cf9662e7cd0acc6cc6
```

## 3. First start on the new firmware

1. Start Klipper (the helper offers it, or `sudo systemctl start klipper`).
2. In the console:

    ```text
    BOX_CFS_CONFIG_INFO
    ```

    It must show the identity, e.g. `K2OH / v323-cfg6`, features `0xE3`, 28 parameters.

3. Check that the RS-485 link and the motors are fine: `SERIAL_STATUS`, `MOTOR_STATUS`, `BOX_DEBUG`.
4. Only then enable your values: see [Runtime parameters](parameters.md#enable-the-values).

## Roll back

Roll back **only while the printer is idle**, after confirming that the CFS loader responds and that the G32/APP153 image passes SHA-256 and compatibility checks. Prefer **the last image actually working on your CFS** (for example CFG6 v3.25); keep v3.22, CFG5T or stock as appropriate alternatives. **No firmware is guaranteed to recover every interrupted write**: if rollback also fails to receive ACKs, stop repeated attempts and diagnose the bus/loader.

## Back to stock CFS firmware

`apply --cfs` with Creality's own release flashes the stock CFS application listed in the release:

```bash
./helper.sh t113 mcu-fw apply --cfs
```

Run it from slot B with the printer idle. A CFS update from a stock Creality OTA in slot A does the same.

## If the flash fails half-way

**Do not automatically repeat the flash that just failed**, particularly for experimental firmware.

1. Keep power stable; **do not print, home, load or unload filament**. Preserve the T113 `/tmp/mcu_update.log` and record the image filename and SHA-256.
2. Distinguish `send fw data ... failed` (data transfer has not reached the final **DONE** response) from `START_APP NACK` (later startup failure). The former **does not prove the new application ever executed**.
3. With the printer idle, heater targets at zero and **exclusive ownership of the RS-485 bus**, check whether the CFS is discoverable in **loader** or **application** mode. `A1/A2` diagnostics and mode transitions are maintenance operations, not actions for an active print.
4. If the loader responds, choose a **known-good, SHA-256-verified image already tested on that CFS**, rather than blindly retrying the experimental candidate. Creality's updater starts a new transfer from offset zero; it does not guarantee resume. If CFS discovery fails or the rollback also times out, **stop further writes** and investigate hardware/transport.
5. After recovery, verify `A2` reports **`mode=application`**, CFS enumeration and normal application queries. An `F0/02` **ACK alone is not proof** of application startup. The documented `0B/01` fallback belongs in a supervised maintenance procedure. Verify RS-485 and X/Y motor readiness before returning to use.

**Documented incident — October 24, 2026:** the type-4 RFID fix candidate in [CFG6 PR #60](https://github.com/MzTechnology97/k2-cfs-rfid-tools/pull/60) remained in loader mode after `send fw data` timeouts; the prior CFG6 v3.25 was restored successfully. The log does not establish a crash of the candidate application. **Do not flash PR #60 again** until it is qualified; see the [transport forensics](https://github.com/MzTechnology97/k2-cfs-rfid-tools/blob/fix/cfg6-type4-runtime-accounting/firmware/v3.26-cfg6-type4-fix/FLASH_FAILURE_AUDIT_20261024_IT.md).
