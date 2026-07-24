# BCU (Board Control Utilities) Reference

BCU is a board-level remote control tool developed by NXP. It connects the PC to the development board via a debug cable (FTDI), supporting power on/off, reset, boot mode switching, GPIO control, and power measurement.

GitHub: https://github.com/nxp-imx/bcu

---

## Quick Reference

| Task | Command |
|------|---------|
| Reset to USB boot | `bcu reset usb -board=<board>` |
| Reset to eMMC boot | `bcu reset emmc -board=<board>` |
| Reset to SD boot | `bcu reset sd -board=<board>` |
| Set boot mode (no reset) | `bcu set_boot_mode <mode> -board=<board>` |
| List connected boards | `bcu lsftdi` |
| List supported boards | `bcu lsboard` |
| List boot modes | `bcu lsbootmode -board=<board>` |
| List GPIO | `bcu lsgpio -board=<board>` |
| Get current boot mode | `bcu get_boot_mode -board=<board>` |

---

## Command Format

```
bcu <command> [options]
```

---

## Boot Mode Switching

### Reset to USB Boot

```bash
bcu reset usb -board=<board>
```

### Reset to eMMC Boot

```bash
bcu reset emmc -board=<board>
```

### Reset to SD Boot

```bash
bcu reset sd -board=<board>
```

### Set Boot Mode Without Reset

To change boot mode without triggering a board reset:

```bash
bcu set_boot_mode usb -board=<board>
bcu set_boot_mode emmc -board=<board>
bcu set_boot_mode sd -board=<board>
```

### Persist Settings with `-keep`

By default, BCU de-asserts remote control on exit, which clears boot mode settings. Use `-keep` to persist:

```bash
bcu reset sd -board=<board> -keep
```

**Side effect:** After BCU exits with `-keep`, the FTDI second serial port is restored, which may change `ttyUSB` numbering.

### Custom Boot Pin Values

When the predefined boot mode names do not include the desired mode, specify boot pin values directly:

```bash
bcu reset -boothex=0x1A -board=<board>
bcu reset -bootbin=1001 -board=<board>
```

---

## Multi-Device Selection

When multiple boards are connected to the same PC, you must specify which board to target.

### List Connected Boards

```bash
bcu lsftdi
```

Example output:

```
number of boards connected through FTDI device found: 2
board[0] location_id=1-1
board[1] location_id=1-2
```

### Method 1: Use `-id=` with Location ID (Recommended)

```bash
bcu reset sd -board=imx8mpevkpwra0 -id=1-1
bcu reset emmc -board=imx93evk11 -id=1-2
```

### Method 2: Use `-board=` for Different Board Models

If the connected boards are different models, `-board=` alone is sufficient to distinguish them:

```bash
bcu reset sd -board=imx8mpevkpwra0
bcu reset emmc -board=imx93evk11
```

### Method 3: Use `-auto` for Automatic Detection

Requires EEPROM to have been programmed with board information:

```bash
bcu lsftdi -auto
bcu reset sd -auto
```

**Prerequisite:** The board EEPROM must be programmed via BCU or PMT first.

---

## Supported Boards (Partial)

| `-board=` Value | Board |
|-----------------|-------|
| `imx8mpevk` | i.MX8MP-EVK (CPU board) |
| `imx8mpevkpwra0` / `imx8mpevkpwra1` | i.MX8MP-EVK (PWR board) |
| `imx8dxlevk` | i.MX8DXL-EVK |
| `imx8ulpevk` / `imx8ulpevk9` | i.MX8ULP-EVK |
| `imx93evk11` / `imx93evk11b1` | i.MX93 11x11 EVK |
| `imx93qsb` | i.MX93 QSB |
| `imx93evk14` | i.MX93 14x14 EVK |
| `imx91evk11` | i.MX91 11x11 EVK |
| `imx91qsb` | i.MX91 QSB |
| `imx95evk19` / `imx95evk15` | i.MX95 EVK |
| `imx943evk19a0` / `imx943evk19b1` | i.MX943 EVK |

Run `bcu lsboard` for the complete list.

---

## Important Notes

1. **Settings reset on exit**: BCU de-asserts `remote_en` on exit by default, clearing boot mode settings. Use `-keep` to persist.
2. **`-keep` side effect**: After BCU exits with `-keep`, the FTDI second serial port is restored and `ttyUSB` numbers may change.
3. **EEPROM required for `-auto`**: New boards must be programmed first with `bcu eeprom -w -board=<board>`.
4. **`-auto` may affect other boards**: Using `-auto` can disconnect `ttyUSB` connections of other boards on the same host.
