# Android Debug Workflows Reference

> **See also**: `debug-commands.md` for comprehensive debugging commands (GPU, thermal, network, input, etc.)

## Quick Reference

| Task | Command |
| :--- | :--- |
| Get root shell | `adb root` |
| Check build type | `adb shell getprop ro.build.type` |
| Check SoC type | `adb shell getprop ro.boot.soc_type` |
| Disable dm-verity | `adb root && adb disable-verity && adb reboot` |
| Remount partitions | `adb root && adb remount` |
| Push file to device | `adb push <local> <remote>` |
| Pull file from device | `adb pull <remote> <local>` |
| Stream Android logs | `adb logcat` |
| Filter logs by tag | `adb logcat -s MyTag:V` |
| Save logs to file | `adb logcat -d > logcat.txt` |
| Kernel logs | `adb shell dmesg` |
| Follow kernel log | `adb shell dmesg -w` |
| Bugreport | `adb bugreport > bugreport.zip` |
| List loaded modules | `adb shell lsmod` |
| Enter fastboot mode | `adb reboot bootloader` |
| Reboot device | `adb reboot` |

---

## ⚠️ CRITICAL WARNINGS

### 1. DO NOT Erase Userdata After `adb disable-verity`

When `adb disable-verity` runs, it allocates a scratch image at `/data/gsi/remount/scratch.img.0000` and stores its logical partition metadata in `/metadata/gsi/remount/lpmetadata`.

**If you erase userdata** (e.g., `fastboot erase userdata` or `fastboot -w`):
- The scratch image is destroyed
- The metadata in `/metadata` still references it
- **The system will crash on next boot — device becomes unbootable**

**Recovery:** Re-flash the entire device (all images). There is no partial fix.

### 2. adb vs Serial Console Have Different Mount Namespaces

`adb remount` only affects the adb daemon's mount namespace. The serial console has its own namespace.

If you need writable access from the serial console, run separately on the console:

```bash
su
remount
```

### 3. MEK Boards: Special Overlay Paths for /vendor/etc, /vendor/lib64, /vendor/firmware/tee

On **i.MX 8QuadMax MEK** and **i.MX 8QuadXPlus MEK**, init.rc pre-mounts overlayfs on these directories for SoC-specific configs. They remain **read-only even after `adb remount`**.

Push to the overlay upper directory instead:

```bash
# Determine SoC type first
adb shell getprop ro.boot.soc_type
# Returns: imx8qm  or  imx8qxp

# Push to overlay path
adb push my_config.json /vendor/vendor_overlay_soc/<soc_type>/vendor/etc/

# Create subdirectory if needed
adb shell su -c "umask 000 && mkdir -p /vendor/vendor_overlay_soc/imx8qm/vendor/etc/configs/audio/"
adb push cdnhdmi_config.json /vendor/vendor_overlay_soc/imx8qm/vendor/etc/configs/audio/
adb reboot
```

**MEK Limitations:**
- Cannot delete files from `/vendor/etc/` via adb — must rebuild and re-flash vendor image
- init.rc files under `/vendor/etc/` are parsed before overlayfs mounts — adb push has no effect; rebuild required

### 4. i.MX 8M Plus EVK: ISP Config Overlay Path

`/vendor/etc/configs/isp` is read-only even after remount. Push ISP configs to the sensor-specific overlay:

```bash
# For os08a20 camera:
adb push isp_config.json /vendor/vendor_overlay_sensor/os08a20/vendor/etc/configs/isp/

# For basler camera:
adb push isp_config.json /vendor/vendor_overlay_sensor/basler/vendor/etc/configs/isp/

adb reboot
```

---

## Prerequisites

- **Build type must be `userdebug` or `eng`** — `user` builds block `adb root` and `adb disable-verity`
- **USB cable connected** to the device's USB OTG/debug port
- `adb` available on host (from Android SDK platform-tools)

---

## First-Time Debug Setup (Full Sequence)

Run this once on a freshly flashed device to reach a debug-ready state.

```bash
# Step 1: Unlock (one-time setup)
#   On device UI: Settings → About Phone → tap "Build number" 7× → Developer Options
#   Settings → Developer Options → enable "OEM unlocking"
adb reboot bootloader
fastboot oem unlock
# Device reboots and wipes data automatically

# Step 2: Disable dm-verity (one-time; persists until re-flash of vbmeta)
adb root
adb disable-verity
adb reboot

# Step 3: Remount (required after every reboot)
adb root
adb remount

# Step 4: Push modified files
adb push my_modified_file /vendor/path/to/file

# Step 5: Reboot if needed (some changes require reboot)
adb reboot

# Step 6: Verify and collect logs
adb shell dmesg | grep my_driver
adb logcat -s MyTag:V
```

> **Note:** Steps 3–6 must be repeated after every reboot. dm-verity disable (Step 2) and unlock (Step 1) persist until re-flash.

---

## Common Debug Workflows

### Replace a Native Library or Binary

```bash
adb root
adb remount
adb push my_hal.so /vendor/lib64/hw/my_hal.so
adb shell chmod 644 /vendor/lib64/hw/my_hal.so
adb reboot   # or restart the relevant service
```

> **MEK boards:** `/vendor/lib64` is read-only. Push to `/vendor/vendor_overlay_soc/<soc_type>/vendor/lib64/hw/` instead.

### Replace a Kernel Module (.ko)

Kernel modules live under `/vendor/lib/modules/` (vendor_dlkm partition).

```bash
adb root
adb remount
adb push my_driver.ko /vendor/lib/modules/my_driver.ko
adb reboot

# Verify module loaded
adb shell lsmod | grep my_driver

# Check for symbol errors
adb shell dmesg | grep symbol
# "Unknown symbol XXX (err -2)"      → symbol not exported by kernel
# "Protected symbol: XXX (err -13)"  → GKI protected symbol, cannot override
```

### Push Firmware Files

```bash
adb root
adb remount
adb push firmware.bin /vendor/firmware/firmware.bin
adb reboot
```

> **MEK boards:** `/vendor/firmware/tee` is read-only. Push TEE firmware to `/vendor/vendor_overlay_soc/<soc_type>/vendor/firmware/tee/` instead.

### Replace a Configuration File

```bash
adb root
adb remount
adb push my_config.xml /vendor/etc/my_config.xml
adb reboot  # may be needed depending on when the config is parsed
```

> **MEK boards:** `/vendor/etc` is read-only. See Critical Warnings §3 for the overlay path.

---

## Collecting Logs

### Android Logcat

```bash
# Stream all logs
adb logcat

# Filter by tag (V = verbose, minimum level)
adb logcat -s MyTag:V

# Save snapshot to file
adb logcat -d > logcat.txt
```

### Kernel dmesg

```bash
# Dump current kernel ring buffer
adb shell dmesg > dmesg.txt

# Follow kernel log in real-time
adb shell dmesg -w
```

### Bugreport

```bash
adb bugreport > bugreport.zip
```

---

## Serial Console Access via socat

The serial console gives access to U-Boot, kernel boot messages, and an Android shell — independent of adb.

```bash
# On the Ubuntu host PC — start socat relay to the USB serial socket:
socat STDIO,raw,echo=0,escape=0x1d UNIX-CONNECT:/tmp/<ttyUSBx>.sock

# Press Ctrl+] to exit socat

# Inside the console — get root and remount (separate namespace from adb):
su
remount
```

> **Note:** The `/tmp/<ttyUSBx>.sock` socket must be set up before running socat. Use the mcp-ssh-tmux tool to run socat on the Ubuntu PC if accessing remotely.

---

## Restoring to Clean State

To undo all debug changes (re-enables dm-verity, clears overlayfs scratch):

```bash
# Re-flash all images using uuu:
uuu -b emmc_all imx-boot-<board>.bin <other images>

# Or use the fastboot flash script:
./fastboot_imx_flashall.sh -f <image_dir>
```

> After re-flashing, repeat the First-Time Debug Setup sequence to re-enable debug access.
