# Android Build Workflows Reference

## Quick Reference

| Task | Command |
|------|---------|
| Full build | `source build/envsetup.sh && lunch <target> && ./imx-make.sh -j$(nproc)` |
| Build kernel only | `./imx-make.sh kernel -j4` |
| Build U-Boot only | `./imx-make.sh bootloader -j4` |
| Build boot.img | `./imx-make.sh bootimage -j4` |
| Build dtbo.img | `./imx-make.sh dtboimage -j4` |
| Build OTA package | `make otapackage -j4` |
| Build bootloader + kernel | `./imx-make.sh bootloader kernel -j4` |
| Build fastboot tool | `make -j4 fastboot` |

---

## Host Setup

**OS**: Ubuntu 22.04 64-bit (Android 16), Ubuntu 18.04 64-bit (Android 14)

**Hardware requirements**:
- 450 GB free disk space
- 64 GB RAM recommended (16 GB minimum)
- With 16 GB RAM, reduce `-j` value to avoid segfaults

**Required packages** (in addition to [AOSP requirements](https://source.android.com/docs/setup/start/requirements)):

```bash
sudo apt-get install uuid uuid-dev zlib1g-dev liblz-dev liblzo2-2 liblzo2-dev \
    lzop git curl u-boot-tools mtd-utils android-sdk-libsparse-utils \
    device-tree-compiler gdisk m4 bison flex make libssl-dev gcc-multilib \
    libgnutls28-dev swig liblz4-tool libdw-dev dwarves bc cpio tar lz4 rsync \
    ninja-build clang build-essential libncurses5 xxd unzip efitools
```

**Git config** (required before repo sync):

```bash
git config --global user.name "First Last"
git config --global user.email "first.last@company.com"
```

---

## Source Code

### Install repo tool

```bash
mkdir ~/bin
curl https://storage.googleapis.com/git-repo-downloads/repo > ~/bin/repo
chmod a+x ~/bin/repo
export PATH=${PATH}:~/bin
```

### Unpack and sync

```bash
# Unpack release package
cd ~
tar xzvf imx-android-16.0.0_2.0.0.tar.gz

# Initialize repo
cd ${MY_ANDROID}
repo init -u http://androidsource.ap.freescale.net/project/p/platform/manifest.git -b ${RELEASE_BRANCH}
```

**Source components**:
- NXP i.MX public source: https://github.com/nxp-imx/imx-manifest
- AOSP source: https://android.googlesource.com/
- NXP proprietary package: from www.nxp.com

**SSL workaround** (if wireless-regdb sync fails):

```bash
git config --global http.sslVerify false
```

---

## Lunch Targets

**Pattern**: `lunch <product>-<release_variant>-<build_mode>`

### Android 16 (release variant: `nxp_stable`)

| Board | Lunch Command |
|-------|---------------|
| i.MX 8M Mini EVK | `lunch evk_8mm-nxp_stable-userdebug` |
| i.MX 8M Nano EVK | `lunch evk_8mn-nxp_stable-userdebug` |
| i.MX 8M Plus EVK | `lunch evk_8mp-nxp_stable-userdebug` |
| i.MX 8MQuad WEVK/EVK | `lunch evk_8mq-nxp_stable-userdebug` |
| i.MX 8ULP EVK | `lunch evk_8ulp-nxp_stable-userdebug` |
| i.MX 8QuadMax / 8QuadXPlus MEK | `lunch mek_8q-nxp_stable-userdebug` |
| i.MX 95 EVK | `lunch evk_95-nxp_stable-userdebug` |
| i.MX 952 EVK | `lunch evk_952-nxp_stable-userdebug` |

### Android 14 (release variant: `trunk_staging`)

| Board | Lunch Command |
|-------|---------------|
| i.MX 95 EVK | `lunch evk_95-trunk_staging-userdebug` |

> **Naming convention**: `evk_<soc>` for evaluation kits, `mek_<soc>` for multisensory kits.

---

## Build Modes

| Mode | ro.secure | ro.debuggable | adb | Use Case |
|------|-----------|---------------|-----|----------|
| `eng` | 0 | 1 | enabled | Development with extra debug tools |
| `userdebug` | default | 1 | enabled | Debugging with root access |
| `user` | 1 | 0 | disabled | Production / CTS testing |

**Key notes**:
- **CTS requires `user` mode** (not userdebug)
- `eng` installs `PRODUCT_PACKAGES_ENG` + `PRODUCT_PACKAGES_DEBUG`
- `userdebug` installs `PRODUCT_PACKAGES_DEBUG` only
- `PRODUCT_PACKAGES` modules are always installed in all modes

---

## Build Commands

All build commands assume environment is already set up:

```bash
cd ${MY_ANDROID}
source build/envsetup.sh
lunch <target>           # See Lunch Targets above
```

### Full Build (single command)

```bash
./imx-make.sh -j$(nproc)
```

### Full Build (step by step)

```bash
./imx-make.sh bootloader kernel -j4
make -j4
```

### Component Builds

| Component | Command | Output Path |
|-----------|---------|-------------|
| U-Boot | `./imx-make.sh bootloader -j4` | `${MY_ANDROID}/out/target/product/<product>/` |
| Kernel | `./imx-make.sh kernel -j4` | `out/target/product/<product>/obj/KERNEL_OBJ/arch/arm64/boot/Image` |
| boot.img | `./imx-make.sh bootimage -j4` | `${MY_ANDROID}/out/target/product/<product>/boot.img` |
| dtbo.img | `./imx-make.sh dtboimage -j4` | `${MY_ANDROID}/out/target/product/<product>/dtbo.img` |
| fastboot | `make -j4 fastboot` | `out/host/linux-x86/bin/fastboot` |

### U-Boot Special Variants

```bash
# Compress TEE images (if bootloader too large for bootloader0 partition)
USE_TEE_COMPRESS=true ./imx-make.sh bootloader -j4

# Encrypted boot (8MP/8MM/8MN/8MQ only, generates dummy dek_blob)
BUILD_ENCRYPTED_BOOT=true ./imx-make.sh bootloader -j4
```

### boot.img Alternative (step by step)

```bash
./imx-make.sh kernel -j4
TARGET_IMX_KERNEL=true make bootimage -j4
mv $OUT/boot.img $OUT/boot-imx.img
make bootimage -j4
```

### dtbo.img Alternative

```bash
./imx-make.sh kernel -j4
make dtboimage -j4
```

---

## OTA Packages

### Build Target Files (prerequisite)

```bash
cd ${MY_ANDROID}
source build/envsetup.sh
lunch evk_8mm-nxp_stable-userdebug
./imx-make.sh bootloader kernel -j4
make target-files-package -j4
```

Output: `out/target/product/<product>/obj/PACKAGING/target_files_intermediates/<product>-target_files-**.zip`

### Full OTA Package

```bash
cd ${MY_ANDROID}
source build/envsetup.sh
lunch evk_8mm-nxp_stable-userdebug
./imx-make.sh bootloader kernel -j4
make otapackage -j4
```

Output: `out/target/product/<product>/<product>-ota-**.zip`

### Incremental OTA Package

Requires two target-files zips: previous build and new build.

```bash
cd ${MY_ANDROID}
out/host/linux-x86/bin/ota_from_target_files \
    -i PREVIOUS-target_files.zip \
    NEW-target_files.zip \
    incremental-ota.zip
```

### OTA with Postinstall

Updates `bootloader0` partition via dd after OTA:

```bash
make otapackage -j4 IMX_OTA_POSTINSTALL=1
```

### OTA with Encrypted Boot

```bash
BUILD_ENCRYPTED_BOOT=true ./imx-make.sh bootloader -j24
# After encrypting images, copy to UBOOT_COLLECTION directory
./imx-make.sh kernel -j4
BUILD_ENCRYPTED_BOOT=true make otapackage -j24 IMX_OTA_POSTINSTALL=1
```

---

## Key Variables

| Variable / Path | Description |
|-----------------|-------------|
| `${MY_ANDROID}` | Android source root directory |
| `./imx-make.sh` | NXP build wrapper script (in source root) |
| `${MY_ANDROID}/device/nxp/` | NXP device configurations |
| `${MY_ANDROID}/device/nxp/{PLATFORM}/{PRODUCT}/UbootKernelBoardConfig.mk` | U-Boot and kernel build config per board |
| `${MY_ANDROID}/out/target/product/<product>/` | Build output directory |
| `${MY_ANDROID}/vendor/nxp-opensource/imx/` | NXP open-source HAL and tools |

### Environment Variables

| Variable | Effect |
|----------|--------|
| `USE_TEE_COMPRESS=true` | Compress TEE images for smaller bootloader |
| `BUILD_ENCRYPTED_BOOT=true` | Generate encrypted boot images (8MP/8MM/8MN/8MQ) |
| `IMX_OTA_POSTINSTALL=1` | Enable OTA postinstall for bootloader0 update |
| `TARGET_IMX_KERNEL=true` | Use i.MX kernel when building boot.img |

### Makefile Variables

| Variable | Effect |
|----------|--------|
| `PRODUCT_PACKAGES` | Modules installed in all build modes |
| `PRODUCT_PACKAGES_ENG` | Additional modules for `eng` builds only |
| `PRODUCT_PACKAGES_DEBUG` | Additional modules for `eng` and `userdebug` builds |

---

## MY_ANDROID Detection

Before running any build command, verify you are in a valid Android source tree:

```bash
# Check for build/envsetup.sh in current directory
if [ ! -f build/envsetup.sh ]; then
    echo "ERROR: Not in Android source root. Set MY_ANDROID and cd there first."
    exit 1
fi
```

**Agent guidance**: Always verify the working directory contains `build/envsetup.sh` before executing build commands. The `${MY_ANDROID}` variable should point to the root of the Android source tree where `imx-make.sh`, `build/envsetup.sh`, and `device/nxp/` all exist.

---

## Common Build Patterns

```bash
# Full build for i.MX 8M Plus (most common)
cd ${MY_ANDROID}
source build/envsetup.sh
lunch evk_8mp-nxp_stable-userdebug
./imx-make.sh -j$(nproc)

# Quick kernel iteration
source build/envsetup.sh
lunch evk_8mp-nxp_stable-userdebug
./imx-make.sh kernel -j4

# Rebuild bootloader after U-Boot config change
source build/envsetup.sh
lunch evk_8mp-nxp_stable-userdebug
./imx-make.sh bootloader -j4

# CTS-ready user build
source build/envsetup.sh
lunch evk_8mp-nxp_stable-user
./imx-make.sh -j$(nproc)
```

---

## Build Test Suites

| Suite | Command |
|-------|---------|
| CTS | `make cts -j$(nproc)` |
| VTS | `make vts -j$(nproc)` |
| GTS | Not built locally (Google proprietary) |

> Note: CTS certification requires `user` build variant (not `userdebug`).

### Building a single CTS/xTS test module

To rebuild just one test module (e.g. after patching a test), use `m <ModuleName>`
instead of building the whole suite:

```bash
source build/envsetup.sh
lunch evk_95-nxp_stable-userdebug    # ANY target from the list above is fine
m CtsAppFunctionTestCases
```

> **Lunch target does NOT need to match the device under test when building a
> CTS test module** — the test APK is portable, so pick any convenient
> `<product>-nxp_stable-userdebug` from the Lunch Targets table. Just avoid a
> bare `lunch <product>` (defaults to `eng`/dev-codename and yields an APK that
> won't install on release devices). See `xts-testing.md` for deploy/verify steps.
