# Kernel & U-Boot Development Reference

## Quick Reference

| Task | Command / Path |
|------|----------------|
| Kernel source | `${MY_ANDROID}/vendor/nxp-opensource/kernel_imx/` |
| U-Boot source | `${MY_ANDROID}/vendor/nxp-opensource/uboot-imx/` |
| Build kernel only | `./imx-make.sh kernel -j$(nproc)` |
| Build U-Boot only | `./imx-make.sh bootloader -j$(nproc)` |
| Kernel output | `out/target/product/<product>/obj/KERNEL_OBJ/arch/arm64/boot/Image` |
| Device tree source | `vendor/nxp-opensource/kernel_imx/arch/arm64/boot/dts/freescale/` |
| U-Boot config | `device/nxp/<platform>/<product>/UbootKernelBoardConfig.mk` |
| Kernel defconfig | `vendor/nxp-opensource/kernel_imx/arch/arm64/configs/gki_defconfig` |
| Flash kernel | `fastboot flash boot out/target/product/<product>/boot.img` |
| Flash U-Boot | Via UUU or dd (see android-flash.md) |

> **Build setup**: See android-build.md for `source build/envsetup.sh`, lunch targets, `imx-make.sh`.

---

## Kernel Source Layout

Key directories under `${MY_ANDROID}/vendor/nxp-opensource/kernel_imx/`:

| Path | Content |
|------|---------|
| `arch/arm64/boot/dts/freescale/` | i.MX device tree sources (.dts/.dtsi) |
| `arch/arm64/configs/` | Kernel defconfig files |
| `drivers/gpu/drm/imx/` | GPU/display (Vivante/LCDIFv3/DCSS) |
| `drivers/media/platform/nxp/` | VPU (Hantro/Amphion) and ISP |
| `drivers/mxc/` | i.MX-specific peripheral drivers |
| `sound/soc/fsl/` | Audio (SAI/MICFIL/ASRC) drivers |

Build output paths (under `out/target/product/<product>/`):

| Artifact | Relative Path |
|----------|---------------|
| Kernel Image | `obj/KERNEL_OBJ/arch/arm64/boot/Image` |
| DTBs | `obj/KERNEL_OBJ/arch/arm64/boot/dts/freescale/*.dtb` |
| Modules | `obj/KERNEL_OBJ/modules/` |
| boot.img | `boot.img` |
| dtbo.img | `dtbo.img` |

---

## Kernel Configuration

### Find and Modify Defconfig

```bash
# Find which defconfig is used
grep KERNEL_DEFCONFIG ${MY_ANDROID}/device/nxp/imx8m/evk_8mp/UbootKernelBoardConfig.mk
# Result: TARGET_KERNEL_DEFCONFIG := gki_defconfig

# Run menuconfig
cd ${MY_ANDROID}/vendor/nxp-opensource/kernel_imx
export ARCH=arm64
export CROSS_COMPILE=${MY_ANDROID}/prebuilts/gcc/linux-x86/aarch64/aarch64-linux-android-4.9/bin/aarch64-linux-android-
make O=out gki_defconfig
make O=out menuconfig

# Save changes back
make O=out savedefconfig
cp out/defconfig arch/arm64/configs/gki_defconfig
```

### Common i.MX Config Options

| Config Option | Purpose |
|---------------|---------|
| `CONFIG_MXC_GPU_VIV` | Vivante GPU driver |
| `CONFIG_VIDEO_MXC_ISI_CORE` | ISI camera pipeline |
| `CONFIG_IMX_SDMA` | SDMA engine |
| `CONFIG_DRM_IMX_LCDIF` | LCDIFv3 display controller |
| `CONFIG_MXC_HANTRO` | Hantro VPU decoder |
| `CONFIG_TRUSTY` | Trusty TEE support |
| `CONFIG_IMX_ETHOSU` | Ethos-U NPU driver |
| `CONFIG_BRCMFMAC` | Broadcom/Cypress Wi-Fi |

### GKI Fragment-Based Configuration

Vendor fragments at `${MY_ANDROID}/device/nxp/common/kernel-config/nxp_defconfig_fragments/`:
- `android.config` — Android-specific options
- `imx8m.config` — i.MX 8M family options
- `trusty.config` — Trusty TEE options

---

## Kernel Build & Flash

```bash
# Build kernel (see android-build.md for full details)
cd ${MY_ANDROID}
source build/envsetup.sh && lunch evk_8mp-nxp_stable-userdebug
./imx-make.sh kernel -j$(nproc)

# Build boot.img and flash (fastest iteration)
./imx-make.sh bootimage -j$(nproc)
fastboot flash boot out/target/product/evk_8mp/boot.img
fastboot reboot

# Or flash kernel + dtbo separately
./imx-make.sh dtboimage -j$(nproc)
fastboot flash dtbo out/target/product/evk_8mp/dtbo.img
fastboot reboot
```

> For full reflash via UUU, see android-flash.md.

---

## Device Tree Development

### DT Source Files by SoC

| SoC | Main DTS | Base DTSI |
|-----|----------|-----------|
| i.MX 8M Plus | `imx8mp-evk.dts` | `imx8mp.dtsi` |
| i.MX 8M Mini | `imx8mm-evk.dts` | `imx8mm.dtsi` |
| i.MX 8M Nano | `imx8mn-evk.dts` | `imx8mn.dtsi` |
| i.MX 8M Quad | `imx8mq-evk.dts` | `imx8mq.dtsi` |
| i.MX 95 | `imx95-19x19-evk.dts` | `imx95.dtsi` |
| i.MX 8ULP | `imx8ulp-evk.dts` | `imx8ulp.dtsi` |

All under: `vendor/nxp-opensource/kernel_imx/arch/arm64/boot/dts/freescale/`

### Common DT Modifications

**Enable/disable peripheral**:
```dts
&uart2 {
    status = "okay";     /* "okay" to enable, "disabled" to disable */
    pinctrl-names = "default";
    pinctrl-0 = <&pinctrl_uart2>;
};
```

**Add pin muxing**:
```dts
&iomuxc {
    pinctrl_uart2: uart2grp {
        fsl,pins = <
            MX8MP_IOMUXC_UART2_RXD__UART2_DCE_RX   0x140
            MX8MP_IOMUXC_UART2_TXD__UART2_DCE_TX   0x140
        >;
    };
};
```

**Add I2C device**:
```dts
&i2c1 {
    clock-frequency = <400000>;
    status = "okay";
    my_sensor: sensor@48 {
        compatible = "vendor,sensor-name";
        reg = <0x48>;
        interrupt-parent = <&gpio1>;
        interrupts = <5 IRQ_TYPE_EDGE_FALLING>;
    };
};
```

### DT Overlay (DTBO)

```dts
/dts-v1/;
/plugin/;

&i2c3 {
    status = "okay";
    /* Add or override nodes */
};
```

### Build and Validate DT

```bash
# Build DTBs (part of kernel build) + dtbo.img
./imx-make.sh kernel -j$(nproc)
./imx-make.sh dtboimage -j$(nproc)

# Validate on device
adb shell cat /proc/device-tree/model
adb shell cat /proc/device-tree/soc/i2c@30a20000/status

# Validate DTS syntax on host
cd ${MY_ANDROID}/vendor/nxp-opensource/kernel_imx
make ARCH=arm64 dtbs_check
```

---

## U-Boot Development

### Source and Config

Source: `${MY_ANDROID}/vendor/nxp-opensource/uboot-imx/`

Key subdirectories:
- `configs/` — defconfig files
- `board/freescale/<board>/` — board-specific init code
- `arch/arm/dts/` — U-Boot device trees
- `include/configs/<board>.h` — board config header

### Defconfig Naming Pattern

Format: `<soc>_<board>_android_[features_]defconfig`

| Suffix | Meaning |
|--------|---------|
| `_dual` | Dual bootloader (A/B slot) |
| `_trusty_dual` | Trusty TEE + dual bootloader |
| `_trusty_rbidx_blob_dual` | Trusty + encrypted rollback index |
| `_trusty_secure_unlock_dual` | Trusty + secure unlock |
| `_uuu` | UUU flashing variant (RAM-only) |

### Build and Flash U-Boot

```bash
# Build (see android-build.md for TEE compress / encrypted boot options)
cd ${MY_ANDROID}
source build/envsetup.sh && lunch evk_8mp-nxp_stable-userdebug
./imx-make.sh bootloader -j$(nproc)

# Flash via UUU (serial download mode)
sudo uuu -b emmc_all spl-imx8mp-trusty-dual.bin bootloader-imx8mp-trusty-dual.img

# Flash via dd (from running device)
adb shell dd if=/data/local/tmp/spl-imx8mp-trusty-dual.bin of=/dev/block/mmcblk2boot0 bs=1k seek=32
adb shell dd if=/data/local/tmp/bootloader-imx8mp-trusty-dual.img of=/dev/block/by-name/bootloader_a
```

---

## U-Boot Console

Access via serial (115200 8N1). Press any key during boot countdown.

```bash
# Connect via socat or minicom
socat - tcp:<serial-server-ip>:<port>
minicom -D /dev/ttyUSB0 -b 115200
```

### Essential Commands

| Command | Description |
|---------|-------------|
| `printenv` | Show all env variables |
| `printenv bootcmd` | Show specific variable |
| `setenv <var> <value>` | Set variable |
| `saveenv` | Persist env to storage |
| `env default -a` | Reset to defaults |
| `boot` / `run bootcmd` | Execute boot |
| `reset` | Reboot board |

### Key Environment Variables

| Variable | Example | Purpose |
|----------|---------|---------|
| `bootcmd` | `run distro_bootcmd` | Default boot command |
| `bootargs` | `console=ttymxc1,115200 ...` | Kernel cmdline |
| `fdt_file` | `imx8mp-evk.dtb` | Device tree filename |
| `bootdelay` | `2` | Auto-boot delay (seconds) |

### Network/USB Boot Examples

```bash
# TFTP boot
setenv serverip 192.168.1.100
setenv ipaddr 192.168.1.10
tftp 0x40480000 Image
tftp 0x43000000 imx8mp-evk.dtb
booti 0x40480000 - 0x43000000

# USB boot
usb start
load usb 0:1 0x40480000 Image
load usb 0:1 0x43000000 imx8mp-evk.dtb
booti 0x40480000 - 0x43000000

# Debug bootargs override
setenv bootargs 'console=ttymxc1,115200 earlycon loglevel=8'
boot
```

---

## Kernel Module Development

### Out-of-Tree Module Makefile

```makefile
obj-m := my_module.o
my_module-objs := main.o utils.o
KERNEL_SRC := ${MY_ANDROID}/out/target/product/evk_8mp/obj/KERNEL_OBJ

all:
	make -C $(KERNEL_SRC) M=$(PWD) ARCH=arm64 CROSS_COMPILE=aarch64-linux-android- modules
clean:
	make -C $(KERNEL_SRC) M=$(PWD) clean
```

### Load/Unload/Debug

```bash
adb push my_module.ko /data/local/tmp/
adb shell insmod /data/local/tmp/my_module.ko debug_level=3
adb shell lsmod | grep my_module
adb shell dmesg | grep my_module
adb shell rmmod my_module

# Runtime parameter change (if module_param has 0644 perms)
adb shell "echo 2 > /sys/module/my_module/parameters/debug_level"
```

---

## Git Workflows for Kernel

### Git Bisect for Regressions

```bash
cd ${MY_ANDROID}/vendor/nxp-opensource/kernel_imx
git bisect start
git bisect bad                          # Current HEAD is broken
git bisect good <known-good-commit>

# For each bisect step:
cd ${MY_ANDROID}
./imx-make.sh bootimage -j$(nproc)
fastboot flash boot out/target/product/evk_8mp/boot.img && fastboot reboot
# Test, then:
cd vendor/nxp-opensource/kernel_imx
git bisect good   # or: git bisect bad

# When done:
git bisect reset
```

### Cherry-Pick and Patch Management

```bash
cd ${MY_ANDROID}/vendor/nxp-opensource/kernel_imx

# Cherry-pick from upstream
git remote add upstream https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git
git fetch upstream master
git cherry-pick <commit-hash>

# Create/apply patch series
git format-patch -1 <commit> -o /tmp/patches/
git am /tmp/patches/*.patch
git am --abort    # if conflicts, start over
```

---

## Troubleshooting

### Kernel Panic

```bash
# Read pstore crash log
adb shell cat /sys/fs/pstore/console-ramoops-0

# Decode stack trace on host
cd ${MY_ANDROID}/vendor/nxp-opensource/kernel_imx
scripts/decode_stacktrace.sh vmlinux < /tmp/panic_log.txt

# Add verbose boot for next attempt (in U-Boot)
setenv bootargs '... loglevel=8 earlycon panic=5'
```

### Boot Hang Analysis

| Symptom | Likely Cause | Action |
|---------|-------------|--------|
| No serial output | SPL crash / wrong boot mode | Check DIP switches, reflash via UUU |
| U-Boot prompt, no kernel | Bad bootcmd / corrupt Image | `printenv bootcmd`, rebuild kernel |
| Kernel hangs early | DT error / driver probe fail | Add `earlycon loglevel=8` to bootargs |
| Kernel boots, no Android | init/SELinux/mount failure | Check serial console or `adb logcat` |
| Reboot loop | Panic + watchdog | Capture ramoops, disable watchdog |

### U-Boot Recovery

```bash
# Reset corrupted env (at U-Boot console)
env default -a
saveenv
reset

# Reflash broken U-Boot via UUU
sudo uuu -b emmc_all spl-imx8mp-trusty-dual.bin bootloader-imx8mp-trusty-dual.img
```
