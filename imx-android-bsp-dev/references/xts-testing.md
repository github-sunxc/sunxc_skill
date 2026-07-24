# xTS Testing Reference (CTS / VTS / GTS / STS)

## Quick Reference

| Task | Command |
|------|---------|
| Run full CTS | `run cts --shard-count 6` |
| Run full VTS | `run vts --shard-count 4` |
| Run full GTS | `run gts --shard-count 4` |
| Run full STS | `run sts-dynamic-develop --shard-count 4` |
| Run single module | `run cts -m CtsNetTestCases` |
| Run single test | `run cts -m CtsNetTestCases -t android.net.cts.ConnectivityManagerTest#testRequestNetwork` |
| Retry failures (Android 9+) | `run retry --retry <session_id>` |
| Retry failures (Android 8.1-) | `run cts --retry <session_id>` |
| Non-interactive run | `./cts-tradefed run commandAndExit cts -m CtsNetTestCases` |
| List results | `list results` |
| List devices | `list devices` |
| Quick module debug | `run cts -m <module> --skip-preconditions -l DEBUG --logcat-on-failure` |

---

## Suite Overview

All xTS suites are built on **Trade Federation (Tradefed / TF)** — a Java host application communicating with devices via ADB. Most parameters are shared; only launch script and plan name differ.

| Suite | Purpose | Launch Script | Default Plan | Package Dir |
|-------|---------|---------------|--------------|-------------|
| CTS | Android platform compatibility | `cts-tradefed` | `run cts` | `android-cts/tools/` |
| VTS | HAL and kernel vendor compliance (Treble) | `vts-tradefed` | `run vts` | `android-vts/tools/` |
| GTS | Google Mobile Services compliance | `gts-tradefed` | `run gts` | `android-gts/tools/` |
| STS | Security patch verification (CVE) | `sts-tradefed` | `run sts-dynamic-develop` | `android-sts/tools/` |

---

## Environment Prerequisites

### Host Requirements

- **Java**: 8 / 9 / 11+ (`java -version`)
- **ADB**: Available and device authorized (`adb devices`)

### Device Preparation

- Factory reset recommended for certification runs
- Wi-Fi connected (many tests require network)
- Developer Options → Stay Awake enabled
- For CTS certification: use `user` build mode (not `userdebug`)

### Obtain Test Package

```bash
# Download pre-built package
unzip android-cts-<version>.zip

# Or build from AOSP source
make cts -j$(nproc)
```

### Build a Single CTS Test Module (for patching / debugging a test)

When you only need to rebuild one CTS module (e.g. after editing its test
source), build just that module instead of the whole `cts` target:

```bash
source build/envsetup.sh
lunch <any-target-from-the-board-list>     # see android-build.md Lunch Targets
m CtsAppFunctionTestCases                  # replace with your module name
```

**Lunch choice for building CTS modules does NOT need to match the DUT.** A CTS
test APK is portable, so for compiling a single test module you may `lunch` ANY
target from the board list (e.g. `evk_95-nxp_stable-userdebug`) — pick whichever
is convenient. The important thing is to use a real `nxp_stable` (release)
target, NOT a bare `lunch <product>` (which defaults to an `eng`/dev-codename
platform and produces an APK that fails to install on release devices with
`Requires development platform <codename> but this is a release platform`).

Built APK output:
```
out/host/linux-x86/cts/android-cts/testcases/<Module>/<abi>/<Module>.apk
```

To deploy into an existing xTS package, back up and replace the APK under
`android-cts/testcases/<Module>/<abi>/`, then rerun with a precise
`--include-filter`.

---

## Running Tests

### Execution Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| Interactive | Launch console, enter commands, stays open | Manual testing / debugging |
| commandAndExit | Single execution, exits when done | Automation scripts |

### Interactive Mode

```bash
# Start CTS console
./android-cts/tools/cts-tradefed

# At the prompt, run tests
cts-tf > run cts
```

### Non-Interactive Mode (commandAndExit)

```bash
# Run a module and exit
./cts-tradefed run commandAndExit cts -m CtsMediaTestCases

# VTS with debug flags
./android-vts/tools/vts-tradefed run commandAndExit vts \
  -m VtsHalCameraProviderV2_4TargetTest \
  --skip-all-system-status-check --primary-abi-only --skip-preconditions -l INFO
```

### Automation Script Example

```bash
#!/bin/bash
# Automated CTS module run

CTS_DIR="/path/to/android-cts"
DEVICE_SERIAL="1a2b3c4d"

${CTS_DIR}/tools/cts-tradefed run commandAndExit cts \
  -m CtsNetTestCases \
  -s ${DEVICE_SERIAL} \
  --skip-preconditions \
  -l INFO

if [ $? -eq 0 ]; then
  echo "CTS module completed"
else
  echo "CTS module failed"
fi
```

> ⚠️ **MANDATORY**: After launching ANY test (interactive or commandAndExit), you MUST set up result monitoring per the main SKILL.md "Test Execution Monitoring" section. Never leave a test running without an active plan to detect and report results.

---

## Module and Test Selection

```bash
# Run single module
run cts -m CtsGestureTestCases
run cts --module CtsGestureTestCases

# Run multiple modules
run cts -m CtsGestureTestCases -m CtsNetTestCases

# Run specific test within a module
run cts -m CtsGestureTestCases -t android.gesture.cts.GestureTest#testGetStrokes
run cts -m CtsGestureTestCases --test android.gesture.cts.GestureTest#testGetStrokes

# Run a specific plan
run cts --plan cts-camera

# Run a subplan
run cts --subplan my_failures
```

### CTS Available Plans

| Plan | Description |
|------|-------------|
| `cts` | Full CTS (with precondition checks) |
| `cts-dev` | Development mode (skips preconditions, device info, single ABI only) |
| `cts-instant` | Instant App tests |
| `cts-sim` | Tests requiring SIM card |
| `cts-foldable` | Foldable device tests |
| `cts-multidevice` | Multi-device tests (Android 13+) |
| `cts-camera` | Camera-related tests |
| `cts-java` | Core Java tests |
| `cts-pdk` | PDK fusion build validation |
| `collect-tests-only` | Collect test list only, no execution |

### VTS Plans

| Plan | Description |
|------|-------------|
| `vts` | Full VTS |
| `vts-hal` | HAL (Hardware Abstraction Layer) tests |
| `vts-kernel` | Kernel tests (including LTP) |

### GTS Common Modules

`GtsPermissionTestCases`, `GtsAccountsHostTestCases`, `GtsGmscoreHostTestCases`, `GtsPlayStoreHostTestCases`, `GtsSetupWizardHostTestCases`

---

## Retry Workflows

### Check Previous Results

```bash
# View session history to get session ID
list results
```

### Android 9+ Retry (REQUIRED syntax)

```bash
# Retry all failed and not-executed tests
run retry --retry <session_id>

# Retry only not-executed tests
run retry --retry <session_id> --retry-type NOT_EXECUTED

# Retry only failed tests
run retry --retry <session_id> --retry-type FAILED

# Retry with sharding
run retry --retry <session_id> --shard-count 4

# Retry targeting specific device
run retry --retry <session_id> -s <device_serial>

# Retry filtering specific module (Android 12+)
run retry --retry <session_id> -m CtsNetTestCases
run retry --retry <session_id> --exclude-filter CtsDeqpTestCases
```

> **IMPORTANT**: Android 9+ does NOT allow `run cts --retry`. You MUST use `run retry --retry`.

### Android 8.1 and Earlier Retry

```bash
# Old syntax (only valid for Android 8.1 and below)
run cts --retry <session_id>
```

### Full Certification Retry Workflow

```bash
# 1. Factory reset device, complete initial setup
# 2. Start CTS and run with sharding
./android-cts/tools/cts-tradefed
run cts --shard-count 6

# 3. Deploy monitoring (see SKILL.md "Test Execution Monitoring")
# 4. Check results, then retry until stable
list results
run retry --retry 0 --shard-count 6
run retry --retry 1 --shard-count 6

# Results: android-cts/results/<timestamp>/test_result.xml
```

> Each `run` and `run retry` is a long-running operation. Re-deploy monitoring after EACH one.

---

## Sharding (Multi-Device Parallel)

| Parameter | Description | Android Version |
|-----------|-------------|-----------------|
| `--shard-count <N>` | TF dynamic sharding (recommended) | Android 9+ |
| `--shards <N>` | CTS static sharding (legacy) | Android 8.1 and below |

```bash
# Dynamic sharding (Android 9+)
run cts --shard-count 6

# Static sharding (Android 8.1 and below)
run cts --shards 6
```

> Sharding requires at least 2 connected devices. Recommended: 6+ devices. All devices must run the same build.

### Split Large Modules

```bash
# Run CtsDeqpTestCases on one device group
run cts --max-log-size 100 --shard-count 6 -o -m CtsDeqpTestCases

# Run remaining CTS on another device group
run cts --max-log-size 100 --shard-count 6 -o --exclude-filter CtsDeqpTestCases
```

---

## Filters and Subplans

### Include/Exclude Filters

```bash
# Include specific module
run cts --include-filter CtsGestureTestCases

# Include module for specific ABI
run cts --include-filter "armeabi-v7a CtsGestureTestCases"

# Include specific test method
run cts --include-filter "CtsGestureTestCases android.gesture.cts.GestureTest#testGetStrokes"

# Exclude specific module
run cts --exclude-filter CtsDeqpTestCases

# Exclude specific test
run cts --exclude-filter "CtsCalendarcommon2TestCases android.calendarcommon2.cts.Calendarcommon2Test#testStaticLinking"
```

> `--exclude-filter` takes priority over `--include-filter`.

### Filter Format

```
[abi] <module_name> [test_class[#test_method]]

# Examples:
CtsGestureTestCases                                                    # Entire module
armeabi-v7a CtsGestureTestCases                                        # Module with specific ABI
CtsGestureTestCases android.gesture.cts.GestureTest                    # Class within module
CtsGestureTestCases android.gesture.cts.GestureTest#testGetStrokes     # Method within module
armeabi-v7a CtsGestureTestCases android.gesture.cts.GestureTest#testGetStrokes  # Fully qualified
```

### Subplans

```bash
# Create subplan from failed results
add subplan --name my_subplan --session <session_id> --result-type failed

# Create subplan from failed + not-executed
add subplan --name my_subplan --session <session_id> \
  --result-type failed --result-type not_executed

# Run a subplan
run cts --subplan my_subplan

# List all subplans
list subplans
```

---

## Tradefed Parameters Reference

Parameters below apply to all xTS suites (`run cts` / `run vts` / `run gts` / `run sts-*`).

### Module and Test Selection

| Parameter | Short | Description | Example |
|-----------|-------|-------------|---------|
| `--module` | `-m` | Run specific module | `run cts -m CtsNetTestCases` |
| `--test` | `-t` | Run specific test method | `-m Gesture -t ...GestureTest#testGetStrokes` |
| `--plan` | | Run specific plan | `--plan cts-camera` |
| `--subplan` | | Run specific subplan | `--subplan my_failures` |
| `--include-filter` | | Include module/test | `--include-filter CtsNetTestCases` |
| `--exclude-filter` | | Exclude module/test | `--exclude-filter CtsDeqpTestCases` |
| `--module-parameter` | | Parameterized module mode | `--module-parameter INSTANT_APP` |

### Device Selection

| Parameter | Short | Description | Example |
|-----------|-------|-------------|---------|
| `--serial` | `-s` | Target device serial | `-s 1a2b3c4d` |
| `--device-token` | | Device token (e.g., SIM) | `--device-token 1a2b3c4d:sim-card` |
| `--enable-token-sharding` | | Enable token-based sharding | |

### ABI Control

| Parameter | Short | Description | Example |
|-----------|-------|-------------|---------|
| `--abi` | `-a` | Force specific ABI | `--abi arm64-v8a` |
| `--force-abi` | | Force 32 or 64 bit (legacy) | `--force-abi 64` |
| `--primary-abi-only` | | Run primary ABI only | `run vts --primary-abi-only` |

### Skip/Optimization Options

| Parameter | Description |
|-----------|-------------|
| `--skip-preconditions` | Skip precondition checks (Wi-Fi, media push, etc.) |
| `--skip-device-info` | Skip device info collection (**do NOT use for certification**) |
| `--skip-all-system-status-check` | Skip all system status checks (VTS-specific) |
| `--collect-tests-only` | Collect test list only, no execution |
| `-o` | Skip already-passed modules (optimize retry) |

### Logging and Debugging

| Parameter | Short | Description |
|-----------|-------|-------------|
| `--log-level-display` | `-l` | Console log level: `VERBOSE` / `DEBUG` / `INFO` / `WARN` / `ERROR` |
| `--logcat-on-failure` | | Capture logcat on failure |
| `--bugreport-on-failure` | | Capture bugreport on failure |
| `--screenshoot-on-failure` | | Take screenshot on failure |
| `--max-log-size <MB>` | | Limit log file size |

### Module Argument Passing

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--module-arg` | Pass argument to specific module | `--module-arg CtsMediaTestCases:local-media-path:/tmp/media` |
| `--test-arg` | Pass argument to test runner type | `--test-arg com.android.tradefed.testtype.JarHosttest:collect-tests-only:true` |

### Other Execution Options

| Parameter | Description |
|-----------|-------------|
| `--loop` | Run in continuous loop |
| `--invocation-timeout <ms>` | Invocation timeout |
| `--dry-run` | Validate config only, no execution |
| `--dynamic-config-url <url>` | Specify dynamic config URL |

---

## Console Commands

| Command | Short | Description |
|---------|-------|-------------|
| `help` | | Show common command summary |
| `help all` | | Show all available commands |
| `version` | | Show version |
| `exit` | | Graceful exit (waits for current test) |
| `kill` | | Force terminate current run |
| `list modules` | | List all available test modules |
| `list plans` | `list configs` | List all available test plans |
| `list subplans` | | List all subplans |
| `list results` | `l r` | List stored results (with session IDs) |
| `list invocations` | `l i` | List currently running invocations |
| `list commands` | | List queued commands |
| `list devices` | `l d` | List connected devices and their status |
| `dump logs` | | Export tradefed logs from running invocations |

---

## Media and Instant App Tests (CTS-Specific)

```bash
# Local media files for CTS media modules
run cts -m CtsMediaTestCases \
  --module-arg CtsMediaTestCases:local-media-path:/tmp/android-cts-media-1.5 --shard-count 6

# Instant App tests
run cts --module-parameter INSTANT_APP
run cts-instant  # dedicated plan alternative
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Wrong java version` | Install Java 8/9/11+, verify with `java -version` |
| Device shows `Unavailable` | Check ADB authorization (`adb devices`), verify USB |
| Module Not Done (`done="false"`) | Do not use filter options in retry; use `run retry --retry <session_id>` directly |
| `run cts --retry` errors out | Android 9+: must use `run retry --retry <session_id>` |
| Shard device count mismatch | All devices must run the same build |
| Media tests fail | Verify media files pushed or `local-media-path` set correctly |
| GPS/Network tests intermittent | Ensure good signal; retry until stable |
| CtsNNAPITestCases failures | Known Linux param issue; run separately: `run cts -m CtsNNAPITestCases` |

### Common NXP i.MX Known Failures

- **CtsNNAPITestCases**: NNAPI accelerator delegates may fail on non-GPU models
- **CtsDeqpTestCases**: GPU (Vivante) deqp failures for unsupported extensions
- **CtsMediaTestCases**: Codec-specific failures when VPU firmware not loaded
- **VtsHalCamera**: ISP pipeline issues on boards without camera module

> These are platform-level known issues — retry or exclude-filter as needed.

### View Tradefed Help

```bash
run cts --help       # Important options
run cts --help-all   # All options
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `ANDROID_BUILD_TOP` | Android source root directory |
| `TF_GLOBAL_CONFIG` | Tradefed global config file path |
| `VTS_PYPI_PATH` | VTS Python package local cache directory |
| `ENABLE_XTS_DYNAMIC_DOWNLOADER` | Set to `false` to disable dynamic download |

### Results File Location

```
android-cts/results/<timestamp>/
  test_result.xml, test_result.html, test_result_failures.html, logs/
```

---
*Based on AOSP official documentation. Applicable to all xTS suites sharing the Tradefed framework.*
