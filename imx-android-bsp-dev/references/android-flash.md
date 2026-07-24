# Android Flash Workflows

Reference for flashing i.MX Android images via UUU, fastboot, and SD card.

## Quick Reference

| Task | Command |
|------|---------|
| Flash via UUU (eMMC) | `./uuu_imx_android_flash.sh -f <soc> -a -e -u trusty-dual` |
| Flash via UUU (SD) | `./uuu_imx_android_flash.sh -f <soc> -a -e -t sd -u dual` |
| Flash via fastboot | `./fastboot_imx_flashall.sh -f <soc> -a -e -u trusty-dual -D /path/` |
| SD card partition | `./imx-sdcard-partition.sh -f <soc> -D <dir> /dev/sdX` |
| Set USB boot mode (BCU) | `bcu reset usb -board=<board>` |
| Set eMMC boot mode (BCU) | `bcu reset emmc -board=<board>` |
| Load U-Boot to RAM only | `./uuu_imx_android_flash.sh -f <soc> -u trusty-dual -i` |

---

## End-to-End Flash Workflow

1. **Set board to USB download mode**
   - Via BCU: `bcu reset usb -board=<board>`
   - Manual: Set DIP switches to serial download mode (see [Board Switch Settings](#board-switch-settings))
2. **Connect USB cable** to the board's OTG/Type-C port
3. **Run UUU flash script** (see [UUU Flashing](#uuu-flashing))
4. **Power down**, switch back to eMMC/SD boot mode
   - Via BCU: `bcu reset emmc -board=<board>`
   - Manual: Restore DIP switches to eMMC/SD position
5. **Power on** — verify boot via serial console

> **sshfs note**: Images are typically built on a remote build server. The Ubuntu flash PC
> accesses them via sshfs mount (default `~/remote/sshfs/`). Detect the mount point:
> ```bash
> mount | grep fuse.sshfs
> ```
> Then pass the mounted image directory to `-D`.

---

## UUU Flashing

Tool: [UUU (Universal Update Utility)](https://github.com/nxp-imx/mfgtools/releases) — validated version 1.5.201.

Scripts: `uuu_imx_android_flash.sh` (Linux) / `uuu_imx_android_flash.bat` (Windows).

### Basic Command

```bash
./uuu_imx_android_flash.sh -f imx8mp -a -e -u trusty-dual
```

### Options

| Option | Description |
|--------|-------------|
| `-f soc_name` | **Required.** SoC name (see table below) |
| `-u uboot_feature` | U-Boot variant: `dual`, `trusty-dual`, `trusty-rbidx-blob-dual`, `trusty-secure-unlock-dual` |
| `-a` | Flash slot A only |
| `-b` | Flash slot B only (not recommended with virtual A/B) |
| `-e` | Erase user data |
| `-D directory` | Image directory (absolute path) |
| `-t target_dev` | Target device: `emmc` (default) or `sd` |
| `-c card_size` | Partition table for specific card size (e.g., `13` for 16GB) |
| `-m` | Flash MCU image |
| `-d dtb_feature` | DTBO/vbmeta variant |
| `-daemon` | Daemon mode for flashing multiple boards |
| `-i` | Load U-Boot to RAM only (development/debug) |

### Valid SoC Names for `-f`

| `-f` value | SoC |
|------------|-----|
| `imx8mm` | i.MX 8M Mini |
| `imx8mn` | i.MX 8M Nano |
| `imx8mp` | i.MX 8M Plus |
| `imx8mq` | i.MX 8M Quad |
| `imx8ulp` | i.MX 8ULP |
| `imx8qm` | i.MX 8QuadMax |
| `imx8qxp` | i.MX 8QuadXPlus |
| `imx95` | i.MX 95 |
| `imx952` | i.MX 952 |

### Constraints

- **Trusty + SD incompatible**: `-u trusty-*` cannot be used with `-t sd`
- **Slot B not recommended**: Virtual A/B is enabled; use `-a` for slot A
- **16GB SD cards**: Use `-c 13` for correct partition table
- **32GB SD/eMMC**: No `-c` option needed

---

## fastboot Flashing

Requires the board to be in fastboot mode with the device unlocked.

Host fastboot version must be **>= 30.0.4** (required for virtual A/B support).

> **No `sudo` needed.** USB device access is handled via udev rules (see [USB Permissions](#usb-permissions) below). Do NOT use `sudo` for `fastboot` or `uuu` commands. If the device is not detected, add the udev rules first.

### Basic Command

```bash
./fastboot_imx_flashall.sh -f imx8mp -a -e -u trusty-dual -D /path/to/images/
```

Options are the same as UUU (see [Options](#options) above). The `-D` flag is typically
required for fastboot since images may not be in the current directory.

---

## SD Card Partitioning

```bash
./imx-sdcard-partition.sh -f <soc_name> -D <image_directory> /dev/sdX
```

Supported SoC names: `imx8mm`, `imx8mn`, `imx8mp`, `imx8mq`, `imx8qm`, `imx8qxp`, `imx95`, `imx952`.

Requirements:
- SD card >= 16GB
- Unmount all SD card partitions before running
- Needs `simg2img` tool (install: `sudo apt install android-tools-fsutils`)

---

## U-Boot Image Variants

### i.MX 8M Mini EVK

| Config | Image | Description |
|--------|-------|-------------|
| `imx8mm_evk_android_defconfig` | `u-boot-imx8mm.imx` | Default (no Trusty) |
| `imx8mm_evk_android_dual_defconfig` | `spl-imx8mm-dual.bin` + `bootloader-imx8mm-dual.img` | Dual bootloader |
| `imx8mm_evk_android_trusty_dual_defconfig` | `spl-imx8mm-trusty-dual.bin` + `bootloader-imx8mm-trusty-dual.img` | Trusty + dual |
| `imx8mm_evk_android_trusty_rbidx_blob_dual_defconfig` | `spl-imx8mm-trusty-rbidx-blob-dual.bin` + `bootloader-imx8mm-trusty-rbidx-blob-dual.img` | Trusty + encrypted rollback index |
| `imx8mm_evk_android_trusty_secure_unlock_dual_defconfig` | `spl-imx8mm-trusty-secure-unlock-dual.bin` + `bootloader-imx8mm-trusty-secure-unlock-dual.img` | Trusty + secure unlock |
| `imx8mm_ddr4_evk_android_defconfig` | `u-boot-imx8mm-ddr4.imx` | DDR4 variant |
| `imx8mm_evk_android_uuu_defconfig` | `u-boot-imx8mm-evk-uuu.imx` | UUU flashing only |
| `imx8mm_ddr4_evk_android_uuu_defconfig` | `u-boot-imx8mm-ddr4-evk-uuu.imx` | UUU + DDR4 |

### i.MX 95 EVK

| Config | Image | Description |
|--------|-------|-------------|
| `imx95_19x19_evk_android_defconfig` | `u-boot-imx95.imx` | Default (no Trusty) |
| `imx95_19x19_evk_android_dual_defconfig` | `spl-imx95-dual.bin` + `bootloader-imx95-dual.img` | Dual bootloader |
| `imx95_19x19_evk_android_trusty_dual_defconfig` | `spl-imx95-trusty-dual.bin` + `bootloader-imx95-trusty-dual.img` | Trusty + dual |
| `imx95_19x19_evk_android_uuu_defconfig` | `u-boot-imx95-evk-uuu.imx` | UUU flashing only |

---

## Storage Partition Layout (Dual Bootloader)

| # | Partition | Start Offset | Size | Content |
|---|-----------|-------------|------|---------|
| — | bootloader0 | SoC-specific | 4MB | `spl.imx` / `u-boot.imx` |
| 1 | bootloader_a | 8M | 16MB | `bootloader.img` |
| 2 | bootloader_b | after bootloader_a | 16MB | `bootloader.img` |
| 3 | dtbo_a | after bootloader_b | 4MB | `dtbo.img` |
| 4 | dtbo_b | | 4MB | `dtbo.img` |
| 5 | boot_a | | 64MB | `boot.img` |
| 6 | boot_b | | 64MB | `boot.img` |
| 7 | init_boot_a | | 8MB | `init_boot.img` |
| 8 | init_boot_b | | 8MB | `init_boot.img` |
| 9 | vendor_boot_a | | 64MB | `vendor_boot.img` |
| 10 | vendor_boot_b | | 64MB | `vendor_boot.img` |
| 11 | misc | | 4MB | Recovery/bootloader message |
| 12 | metadata | | 64MB | OTA metadata (f2fs) |
| 13 | presistdata | | 1MB | Lock/unlock state |
| 14 | super | | 4096MB | system, system_dlkm, system_ext, vendor, vendor_dlkm, product |
| 15 | userdata | | Remaining | App data (f2fs) |
| 16 | fbmisc | | 1MB | Fastboot lock/unlock state |
| 17 | vbmeta_a | | 1MB | Verified boot metadata |
| 18 | vbmeta_b | | 1MB | Verified boot metadata |

### bootloader0 Offsets

| SoC | eMMC boot0 offset | SD card offset |
|-----|-------------------|----------------|
| i.MX 8M Mini | 33KB | 33KB |
| i.MX 8M Nano | 0 | 32KB |
| i.MX 8M Plus | 0 | 32KB |
| i.MX 8M Quad | 33KB | 33KB |
| i.MX 8ULP | 0 | 32KB |
| i.MX 8QM Rev.B | 0 | 32KB |
| i.MX 8QXP Rev.B | 32KB | 32KB |
| i.MX 8QXP Rev.C | 0 | 32KB |
| i.MX 95 | 0 | 32KB |
| i.MX 952 | 0 | 32KB |

---

## Board Switch Settings (Boot Mode)

### i.MX 8M Mini EVK (REV C)

| Mode | Switch | Setting |
|------|--------|---------|
| Serial download (USB) | SW1101 bits 1–4 | `1010` |
| SD boot | SW1101 (1–10) | `0110110010` |
| | SW1102 (1–10) | `0001101000` |
| eMMC boot | SW1101 (1–10) | `0110110001` |
| | SW1102 (1–10) | `0001010100` |

### i.MX 95 EVK

| Mode | Switch | Setting |
|------|--------|---------|
| Serial download (USB) | SW7 bits 1–4 | `1001` |
| eMMC boot | SW7 bits 1–4 | `1010` |
| SD boot | SW7 bits 1–4 | `1011` |

### FRDM i.MX 95

| Mode | Switch | Setting |
|------|--------|---------|
| Serial download (USB) | SW1 bits 1–2 | `01` |
| eMMC boot | SW1 bits 1–2 | `10` |
| SD boot | SW1 bits 1–2 | `11` |

---

## USB Permissions

Flash and debug commands (`fastboot`, `adb`, `uuu`) should run **without `sudo`**. USB device access is granted via udev rules.

### Common USB IDs

| Mode | Vendor:Product | Description |
|------|---------------|-------------|
| ADB (Android Debug) | `18d1:4ee7` | Google ADB interface |
| Fastboot | `1fc9:0152` | NXP i.MX fastboot |
| UUU (Serial Download) | `1fc9:013e` | NXP i.MX USB SDP (varies by SoC) |

### Adding udev Rules

Create `/etc/udev/rules.d/99-imx-android.rules`:

```
# ADB
SUBSYSTEM=="usb", ATTR{idVendor}=="18d1", ATTR{idProduct}=="4ee7", MODE="0666", GROUP="plugdev"
# Fastboot (NXP i.MX)
SUBSYSTEM=="usb", ATTR{idVendor}=="1fc9", ATTR{idProduct}=="0152", MODE="0666", GROUP="plugdev"
# UUU / Serial Download (NXP i.MX)
SUBSYSTEM=="usb", ATTR{idVendor}=="1fc9", MODE="0666", GROUP="plugdev"
```

Then reload:

```bash
sudo udevadm control --reload-rules && sudo udevadm trigger
```

Ensure your user is in the `plugdev` group: `sudo usermod -aG plugdev $USER` (re-login required).

### Troubleshooting: Device Not Found

If `fastboot devices` or `adb devices` returns empty:

1. **Check USB connection**: `lsusb | grep -i "1fc9\|18d1"` — device should appear
2. **Check udev rules**: `ls /etc/udev/rules.d/*imx* /etc/udev/rules.d/*android*` — rules file exists
3. **Check permissions**: `ls -la /dev/bus/usb/<bus>/<dev>` — should show `0666` or group-readable
4. **Add udev rules** if missing (see above), then unplug/replug the USB cable
5. **Last resort**: Use `sudo` if udev rules cannot be added (e.g., shared lab machine with no root)
