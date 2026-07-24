# Debug Command Reference for i.MX Android BSP

Comprehensive collection of diagnostic and debugging commands for i.MX Android platforms.
All commands run via `adb shell` unless noted otherwise.

> **See also**: `android-debug.md` for remount/push workflows, crash analysis, and first-time device setup.

## Quick Reference

| Task | Command |
|------|---------|
| Check SoC/board info | `getprop ro.boot.hardware` |
| Android version | `getprop ro.build.version.release` |
| CPU frequency | `cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq` |
| GPU status (Vivante) | `cat /sys/kernel/debug/gc/idle` |
| Clock tree | `cat /sys/kernel/debug/clk/clk_summary` |
| Regulator status | `cat /sys/class/regulator/*/name && cat /sys/class/regulator/*/state` |
| M-core state | `cat /sys/class/remoteproc/remoteproc0/state` |
| Display connectors | `cat /sys/kernel/debug/dri/0/state` |
| Thermal zones | `cat /sys/class/thermal/thermal_zone*/temp` |
| Memory info | `cat /proc/meminfo` |
| Disk usage | `df -h` |
| Running services | `dumpsys activity services` |
| SELinux mode | `getenforce` |
| Kernel log | `dmesg -T` |
| All logs | `logcat -b all` |
| Input devices | `getevent -l` |
| Network interfaces | `ip addr show` |
| Audio mixers | `tinymix` |
| Camera devices | `v4l2-ctl --list-devices` |
| Bug report | `bugreport` |

---

## 1. System Properties

```bash
# Build information
getprop ro.build.display.id          # Full build ID string
getprop ro.build.version.release     # Android version (e.g., 14)
getprop ro.build.version.sdk         # API level
getprop ro.build.type                # userdebug / eng / user
getprop ro.build.date                # Build date

# Hardware identification
getprop ro.boot.hardware             # SoC name (e.g., nxp)
getprop ro.hardware                  # Hardware variant
getprop ro.boot.soc_type             # SoC type (e.g., imx8mp)
getprop ro.boot.storage_type         # emmc / sd
getprop ro.boot.dtbo_idx             # Device tree overlay index
getprop ro.product.board             # Board name
getprop ro.product.device            # Device codename

# Runtime state
getprop sys.boot_completed           # 1 = boot finished
getprop init.svc.bootanim            # Boot animation state
getprop persist.sys.timezone         # Current timezone

# Set property (requires root)
setprop debug.hwui.renderer skiagl   # Force SkiaGL renderer
setprop persist.sys.usb.config mtp,adb  # USB config

# Dump all properties
getprop                              # List all properties
getprop | grep -i imx               # Filter i.MX-specific
```

## 2. Process and Service Management

```bash
# Process listing
ps -A                                # All processes
ps -A | grep surfaceflinger          # Find specific process
ps -eo pid,ppid,uid,cmd              # Extended format
top -n 1 -s cpu                      # CPU-sorted snapshot
top -n 1 -s rss                      # Memory-sorted snapshot

# Service management
dumpsys activity services            # All running services
dumpsys activity services <package>  # Services for specific app
service list                         # All registered system services
service check SurfaceFlinger         # Check if service exists

# Start/stop services
start                                # Start Android runtime
stop                                 # Stop Android runtime (keeps kernel)
setprop ctl.restart zygote           # Restart zygote (soft reboot)
setprop ctl.restart surfaceflinger   # Restart SurfaceFlinger

# System server dumps
dumpsys -l                           # List all dumpable services
dumpsys meminfo                      # Memory usage per process
dumpsys cpuinfo                      # CPU usage per process
dumpsys package <pkg>                # Package details
dumpsys window                       # Window manager state
dumpsys power                        # Power manager state
dumpsys alarm                        # Pending alarms

# Process signals
kill -3 <pid>                        # Dump Java stack trace (ANR trace)
kill -10 <pid>                       # SIGUSR1 (app-specific)
```

## 3. Hardware/Device (CPU/GPU/I2C/SPI/GPIO)

### CPU

```bash
# CPU frequency and governor
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_available_frequencies
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors
cat /sys/devices/system/cpu/online                    # Online CPUs
cat /sys/devices/system/cpu/possible                  # Possible CPUs

# Set CPU governor (requires root)
echo performance > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
echo 1 > /sys/devices/system/cpu/cpu2/online          # Bring CPU2 online
```

### GPU (Vivante / i.MX-specific)

```bash
# Vivante GPU debug (i.MX 8M/8ULP)
cat /sys/kernel/debug/gc/idle                         # GPU idle status
cat /sys/kernel/debug/gc/info                         # GPU hardware info
cat /sys/kernel/debug/gc/meminfo                      # GPU memory usage
cat /sys/kernel/debug/gc/dump_trigger                 # Trigger GPU state dump
cat /sys/kernel/debug/gc/vidmem                       # Video memory stats
cat /sys/kernel/debug/gc/clients                      # GPU client processes

# GPU frequency
cat /sys/bus/platform/drivers/galcore/*/gpufreq       # Current GPU freq
```

### I2C

```bash
i2cdetect -l                         # List I2C buses
i2cdetect -y <bus>                   # Scan bus for devices
i2cdump -y <bus> <addr>              # Dump all registers
i2cget -y <bus> <addr> <reg>         # Read single register
i2cset -y <bus> <addr> <reg> <val>   # Write register
```

### SPI

```bash
ls /dev/spidev*                      # Available SPI devices
cat /sys/bus/spi/devices/*/modalias  # SPI device types
```

### GPIO

```bash
cat /sys/kernel/debug/gpio           # GPIO state summary
gpioinfo                             # List all GPIO lines (libgpiod)
gpioget <chip> <line>                # Read GPIO value
gpioset <chip> <line>=<val>          # Set GPIO value
cat /sys/class/gpio/export           # Legacy sysfs export
```

### Remoteproc (M4/M7 co-processor)

```bash
# i.MX remoteproc for Cortex-M core
cat /sys/class/remoteproc/remoteproc0/state           # running/offline
cat /sys/class/remoteproc/remoteproc0/firmware        # Loaded firmware name
echo start > /sys/class/remoteproc/remoteproc0/state  # Start M-core
echo stop > /sys/class/remoteproc/remoteproc0/state   # Stop M-core
ls /sys/class/remoteproc/                             # All remoteproc instances
```

## 4. Display and Graphics

```bash
# DRM/KMS debug (i.MX DPU/LCDIF/DCSS)
cat /sys/kernel/debug/dri/0/state            # Full DRM state (connectors, CRTCs, planes)
cat /sys/kernel/debug/dri/0/clients          # DRM client list
cat /sys/kernel/debug/dri/0/framebuffer      # Registered framebuffers
ls /sys/kernel/debug/dri/                    # Available DRI cards

# Connector info
cat /sys/class/drm/card0-HDMI-A-1/status     # HDMI connection status
cat /sys/class/drm/card0-HDMI-A-1/modes      # Supported display modes
cat /sys/class/drm/card0-HDMI-A-1/edid       # Raw EDID data (binary)

# SurfaceFlinger
dumpsys SurfaceFlinger                       # Full SF state
dumpsys SurfaceFlinger --latency             # Frame latency stats
dumpsys SurfaceFlinger --list                # List active layers
dumpsys SurfaceFlinger --static-screen       # Static screen detection

# Hardware Composer (HWC)
dumpsys hwservices                           # HAL services (includes HWC)
setprop vendor.hwc.debug 1                  # Enable HWC debug logging

# Display resolution and density
wm size                                      # Display resolution
wm density                                   # Display density (DPI)
wm size 1920x1080                           # Override resolution
wm density 240                              # Override density

# Screen capture
screencap /sdcard/screen.png                 # Capture screenshot
screenrecord /sdcard/video.mp4               # Record screen (max 3 min)
screenrecord --size 1280x720 /sdcard/v.mp4   # Record at lower res
```

## 5. Audio (TinyALSA)

```bash
# List audio hardware
cat /proc/asound/cards                       # ALSA sound cards
cat /proc/asound/pcm                         # PCM devices
cat /proc/asound/card0/pcm0p/sub0/status     # Playback stream status

# TinyALSA tools
tinymix                                      # List all mixer controls
tinymix -D 0                                 # Mixer controls for card 0
tinymix 'Speaker Volume' 80                  # Set mixer control value
tinyplay /sdcard/test.wav -D 0 -d 0          # Play WAV file
tinycap /sdcard/rec.wav -D 0 -d 0 -c 2 -r 48000 -b 16  # Record audio

# Audio service
dumpsys audio                                # Full audio state
dumpsys media.audio_flinger                  # AudioFlinger internals
dumpsys media.audio_policy                   # Audio policy state

# Audio HAL debug
setprop vendor.audio.hal.debug 1            # Enable HAL debug logs
logcat -s AudioFlinger AudioPolicyManager    # Filter audio logs

# HDMI audio
cat /sys/class/drm/card0-HDMI-A-1/audio/format  # Supported audio formats
```

## 6. Camera (V4L2)

```bash
# List video devices
v4l2-ctl --list-devices                      # All V4L2 devices
v4l2-ctl -d /dev/video0 --all               # Full device capabilities
v4l2-ctl -d /dev/video0 --list-formats-ext  # Supported pixel formats
v4l2-ctl -d /dev/video0 --list-ctrls        # Available controls

# Media controller (ISI/ISP pipeline)
media-ctl -p -d /dev/media0                 # Print media graph topology
media-ctl -d /dev/media0 --print-dot        # Output DOT graph format
media-ctl -d /dev/media0 -l "'imx8-isi.0':1->'imx8-isi.0.capture':0[1]"  # Configure link

# Capture test frame
v4l2-ctl -d /dev/video0 --set-fmt-video=width=1920,height=1080,pixelformat=YUYV \
  --stream-mmap --stream-count=1 --stream-to=/sdcard/frame.raw

# Camera service
dumpsys media.camera                         # Camera service state
dumpsys media.camera --unreachable           # Memory leak detection

# Camera provider HAL
logcat -s CameraProvider Camera2Client       # Camera HAL logs

# CSI/MIPI debug
cat /sys/kernel/debug/mxc_mipi_csi2/mipi_csi2_status  # MIPI CSI status
dmesg | grep -i "csi\|mipi\|imx219\|ov5640"          # Camera sensor init
```

## 7. Network (WiFi/IP)

```bash
# Interface status
ip addr show                                 # All interfaces with IPs
ip link show                                 # Interface link state
ip route show                                # Routing table
ip neigh show                                # ARP table

# WiFi
iw dev                                       # Wireless interfaces
iw dev wlan0 link                            # Current connection info
iw dev wlan0 scan                            # Scan for APs
wpa_cli -i wlan0 status                      # WPA supplicant status
wpa_cli -i wlan0 list_networks               # Known networks
wpa_cli -i wlan0 scan_results                # Last scan results

# WiFi debug
dumpsys wifi                                 # WiFi service state
dumpsys connectivity                         # Connectivity manager
logcat -s WifiNative WifiStateMachine        # WiFi logs

# Ethernet
ip link show eth0                            # Ethernet link status
ethtool eth0                                 # Ethernet PHY info (if available)

# DNS and connectivity
nslookup google.com                          # DNS resolution test
ping -c 3 8.8.8.8                            # Basic connectivity
cat /etc/resolv.conf                         # DNS config

# Firewall
iptables -L -n                               # IPv4 firewall rules
ip6tables -L -n                              # IPv6 firewall rules

# Network stats
cat /proc/net/dev                            # Interface packet counters
dumpsys netstats                             # Network usage stats
```

## 8. Storage and Filesystem

```bash
# Disk usage
df -h                                        # Filesystem usage (human-readable)
du -sh /data/*                               # Directory sizes in /data
cat /proc/partitions                         # Block device partitions
ls -la /dev/block/by-name/                   # Partition name symlinks

# Mount info
mount                                        # All mounted filesystems
cat /proc/mounts                             # Same, from procfs
cat /proc/filesystems                        # Supported filesystem types

# Block device info
blkid                                        # UUID/label of block devices
cat /sys/block/mmcblk0/size                  # eMMC total size (sectors)
cat /sys/block/mmcblk0/device/cid            # eMMC CID (manufacturer)
cat /sys/block/mmcblk0/device/csd            # eMMC CSD

# eMMC health (i.MX eMMC)
cat /sys/block/mmcblk0/device/life_time      # eMMC lifetime estimate
cat /sys/block/mmcblk0/device/pre_eol_info   # Pre-EOL status

# I/O stats
cat /proc/diskstats                          # Disk I/O statistics
iostat                                       # I/O summary (if available)

# File operations debug
ls -laZ /data/                               # List with SELinux context
stat /data/local/tmp/                        # File inode details
cat /proc/self/mountinfo                     # Detailed mount info with IDs
```

## 9. Performance and Profiling

```bash
# Perfetto (modern tracing)
perfetto --out /data/misc/perfetto-traces/trace.perfetto-trace \
  --txt -c - <<EOF
buffers { size_kb: 65536 fill_policy: RING_BUFFER }
data_sources { config { name: "linux.ftrace" ftrace_config {
  ftrace_events: "sched/sched_switch"
  ftrace_events: "power/cpu_frequency"
  ftrace_events: "gpu_mem/gpu_mem_total"
}}}
duration_ms: 5000
EOF
# Pull trace: adb pull /data/misc/perfetto-traces/trace.perfetto-trace

# Simpleperf (CPU profiling)
simpleperf stat -a --duration 5              # System-wide CPU stats
simpleperf record -a --duration 5 -o /data/perf.data  # Record samples
simpleperf report -i /data/perf.data         # Report from recording

# Atrace / systrace categories
atrace --list_categories                     # Available trace categories
atrace -z -b 4096 -t 5 gfx view sched freq  # Capture trace

# Frame timing
dumpsys gfxinfo <package>                    # Frame render stats
dumpsys gfxinfo <package> reset              # Reset frame stats

# Memory profiling
procrank                                     # Process memory ranking (if available)
showmap <pid>                                # Detailed memory map
dumpsys meminfo <pid>                        # Per-process memory breakdown
cat /proc/<pid>/smaps                        # Detailed memory segments
cat /proc/<pid>/status                       # Process status summary

# Scheduler
cat /proc/sched_debug                        # Scheduler state
cat /proc/interrupts                         # IRQ counters
```

## 10. Thermal and Power

### Thermal

```bash
# Thermal zones
cat /sys/class/thermal/thermal_zone*/type    # Zone names (cpu/gpu/etc)
cat /sys/class/thermal/thermal_zone*/temp    # Temperatures (millidegrees)
cat /sys/class/thermal/thermal_zone0/trip_point_0_temp  # Trip point

# Cooling devices
cat /sys/class/thermal/cooling_device*/type  # Cooling device types
cat /sys/class/thermal/cooling_device*/cur_state  # Current cooling level
cat /sys/class/thermal/cooling_device*/max_state  # Max cooling level

# All thermal info
dumpsys thermalservice                       # Android thermal service state
for z in /sys/class/thermal/thermal_zone*; do
  echo "$(cat $z/type): $(cat $z/temp)";
done
```

### Power / Regulators

```bash
# Power supply
cat /sys/class/power_supply/*/type           # Battery/USB/AC
cat /sys/class/power_supply/*/status         # Charging/Discharging
cat /sys/class/power_supply/*/capacity       # Battery percentage
dumpsys battery                              # Battery service state

# Voltage regulators (i.MX PMIC)
cat /sys/class/regulator/*/name              # Regulator names
cat /sys/class/regulator/*/state             # enabled/disabled
cat /sys/class/regulator/*/microvolts        # Current voltage
cat /sys/kernel/debug/regulator/regulator_summary  # Full regulator tree

# Suspend/wake
cat /sys/power/state                         # Supported sleep states
cat /sys/power/wakeup_count                  # Wakeup event counter
cat /sys/kernel/debug/wakeup_sources         # Active wakeup sources
dumpsys power | grep -i "wake\|sleep"        # Power manager wake locks
```

## 11. SELinux

```bash
# Status
getenforce                                   # Enforcing / Permissive / Disabled
sestatus                                     # Detailed SELinux status

# Temporarily change mode (requires root)
setenforce 0                                 # Set Permissive (debug only!)
setenforce 1                                 # Set Enforcing

# Policy inspection
cat /sys/fs/selinux/enforce                  # 1=enforcing, 0=permissive
ls /sys/fs/selinux/                          # SELinux filesystem

# AVC denial analysis
logcat -b all | grep avc                     # Find AVC denials in logcat
dmesg | grep avc                             # Find AVC denials in kernel log
logcat -b events | grep "avc:"              # AVC in event buffer

# Common denial format:
# avc: denied { read } for pid=1234 comm="app" name="file"
#   scontext=u:r:untrusted_app:s0 tcontext=u:object_r:vendor_file:s0 tclass=file

# Generate allow rules (on host with audit2allow)
# adb shell "logcat -b all -d | grep avc" | audit2allow -p policy

# File contexts
ls -Z /vendor/bin/                           # Show SELinux labels on files
ls -Z /sys/class/thermal/                    # Labels on sysfs
restorecon -R /data/local/tmp/               # Restore default labels

# Process contexts
ps -eZ | grep surfaceflinger                 # Process SELinux domain
cat /proc/<pid>/attr/current                 # Current process context
```

## 12. Kernel Debugging

```bash
# Kernel log
dmesg                                        # Full kernel ring buffer
dmesg -T                                     # With human-readable timestamps
dmesg -w                                     # Follow (tail) kernel messages
dmesg -l err,warn                            # Only errors and warnings
dmesg -c                                     # Clear ring buffer after read

# Clock tree (i.MX-specific)
cat /sys/kernel/debug/clk/clk_summary        # Full clock hierarchy
cat /sys/kernel/debug/clk/clk_summary | grep -i gpu  # GPU clocks
cat /sys/kernel/debug/clk/clk_summary | grep -i uart # UART clocks

# Ftrace
cat /sys/kernel/debug/tracing/available_tracers      # Available tracers
echo function > /sys/kernel/debug/tracing/current_tracer
echo 1 > /sys/kernel/debug/tracing/tracing_on
cat /sys/kernel/debug/tracing/trace                  # Read trace
echo 0 > /sys/kernel/debug/tracing/tracing_on       # Stop tracing

# Function graph tracing
echo function_graph > /sys/kernel/debug/tracing/current_tracer
echo imx_clk_* > /sys/kernel/debug/tracing/set_ftrace_filter
echo 1 > /sys/kernel/debug/tracing/tracing_on

# Dynamic debug (pr_debug messages)
cat /sys/kernel/debug/dynamic_debug/control          # All debug points
echo 'module imx_sdma +p' > /sys/kernel/debug/dynamic_debug/control  # Enable
echo 'file drivers/gpu/drm/imx/* +p' > /sys/kernel/debug/dynamic_debug/control

# Platform devices (i.MX device tree nodes)
ls /sys/devices/platform/                    # All platform devices
ls /sys/firmware/devicetree/base/            # Device tree as filesystem
cat /sys/firmware/devicetree/base/model      # Board model from DT
cat /proc/device-tree/compatible             # Compatible strings

# Kernel config
zcat /proc/config.gz | grep CONFIG_IMX      # i.MX kernel config (if enabled)
cat /proc/version                            # Kernel version string
cat /proc/cmdline                            # Kernel command line
```

## 13. Logcat Advanced

```bash
# Buffer selection
logcat -b main                               # Main app buffer (default)
logcat -b system                             # System/framework messages
logcat -b crash                              # Crash/ANR traces
logcat -b events                             # Binary event log
logcat -b kernel                             # Kernel messages (if supported)
logcat -b all                                # All buffers combined

# Filtering by tag and priority
logcat -s ActivityManager:I                  # Only ActivityManager at Info+
logcat -s *:E                                # Only Error level from all tags
logcat -s SurfaceFlinger:V Camera:D          # Multiple tag filters
logcat ActivityManager:I *:S                 # AM Info+, silence everything else

# Time-based filtering
logcat -T '01-01 00:00:00.000'              # Show from timestamp
logcat -t 100                                # Last 100 lines
logcat -d                                    # Dump and exit (no follow)

# Output format
logcat -v time                               # Add timestamps
logcat -v threadtime                         # Timestamp + TID (default)
logcat -v long                               # Multiline verbose format
logcat -v color                              # Colorized output
logcat -v uid                                # Show UID of sender

# Log to file
logcat -f /data/local/tmp/log.txt            # Write to file
logcat -r 1024 -n 5 -f /data/log.txt        # Rotate: 1MB files, 5 backups

# Persistent logging (survives reboot)
logcat -L                                    # Last (previous boot) log
cat /data/misc/logd/logcat*                  # Persistent log files

# Clear logs
logcat -c                                    # Clear all buffers
logcat -b main -c                            # Clear specific buffer

# Common debug patterns
logcat | grep -i "fatal\|exception\|crash"   # Find crashes
logcat | grep -i "anr in"                    # Find ANRs
logcat -b crash -d                           # Dump crash buffer
```

## 14. Input Subsystem

```bash
# List input devices
getevent -l                                  # Monitor all input events (labeled)
getevent -p                                  # Print device capabilities
getevent -lp /dev/input/event0               # Capabilities of specific device
cat /proc/bus/input/devices                  # Kernel input device list

# Monitor specific device
getevent /dev/input/event2                   # Raw events from device
getevent -l /dev/input/event2                # Labeled events

# Inject input events
sendevent /dev/input/event0 1 330 1          # Touch down (EV_KEY BTN_TOUCH)
sendevent /dev/input/event0 1 330 0          # Touch up
input tap 500 500                            # Tap at coordinates
input swipe 100 500 900 500 300              # Swipe (x1 y1 x2 y2 duration_ms)
input keyevent 3                             # HOME key
input keyevent 26                            # POWER key
input text "hello"                           # Type text

# Dumpsys input
dumpsys input                                # Full input state
dumpsys input_method                         # IME state

# Touchscreen debug
cat /sys/class/input/input0/name             # Input device name
cat /sys/class/input/input0/capabilities/abs # Absolute axis capabilities
dmesg | grep -i "touch\|goodix\|ft5x"       # Touch controller init

# Key layout debugging
cat /system/usr/keylayout/*.kl               # Key layout files
cat /system/usr/idc/*.idc                    # Input device config
dumpsys input | grep -A5 "KeyboardType"      # Keyboard type per device
```

## 15. ADB Advanced

```bash
# Port forwarding
adb forward tcp:8080 tcp:8080               # Forward local port to device
adb forward tcp:5555 localabstract:name     # Forward to abstract socket
adb forward --list                           # List active forwards
adb forward --remove-all                     # Remove all forwards

# Reverse forwarding (device to host)
adb reverse tcp:3000 tcp:3000               # Device connects to host:3000
adb reverse --list                           # List active reverses

# Multi-device management
adb devices -l                               # List with transport info
adb -s <serial> shell                        # Target specific device
export ANDROID_SERIAL=<serial>               # Set default device

# File transfer
adb pull /data/tombstones/ ./tombstones/     # Pull crash dumps
adb push local_file /data/local/tmp/         # Push file to device
adb sync                                     # Sync host to device

# Bugreport
adb bugreport                                # Full bug report (zip)
adb bugreport ./bugreport.zip                # Save to specific path

# Shell tricks
adb shell "cmd package list packages"        # List installed packages
adb shell "pm path <package>"                # APK path for package
adb shell "am start -n com.pkg/.Activity"    # Start activity
adb shell "am broadcast -a android.intent.action.BOOT_COMPLETED"
adb shell "settings get system screen_off_timeout"
adb shell "settings put system screen_off_timeout 600000"  # 10min

# Logcat from host
adb logcat -G 16M                            # Set logcat buffer size
adb logcat --pid=$(adb shell pidof <proc>)   # Logs for specific process

# Device state
adb get-state                                # device/offline/bootloader
adb get-serialno                             # Device serial number
adb shell getprop sys.usb.state              # USB configuration state

# Wireless ADB
adb tcpip 5555                               # Switch to TCP mode
adb connect <device-ip>:5555                 # Connect over WiFi
adb usb                                      # Switch back to USB mode

# Recovery/sideload
adb reboot bootloader                        # Reboot to bootloader
adb reboot recovery                          # Reboot to recovery
adb sideload update.zip                      # Sideload OTA (in recovery)
```

---

## One-Liner Cheat Sheet

```bash
# Quick system overview
getprop ro.boot.soc_type && cat /proc/version && free -m && df -h /data

# Thermal snapshot
for z in /sys/class/thermal/thermal_zone*; do echo "$(cat $z/type): $(($(cat $z/temp)/1000))C"; done

# GPU idle check (Vivante)
cat /sys/kernel/debug/gc/idle

# Clock tree for specific IP
cat /sys/kernel/debug/clk/clk_summary | grep -i "gpu\|disp\|vpu"

# All regulators state
paste <(cat /sys/class/regulator/*/name) <(cat /sys/class/regulator/*/state)

# M-core firmware status
echo "State: $(cat /sys/class/remoteproc/remoteproc0/state), FW: $(cat /sys/class/remoteproc/remoteproc0/firmware)"

# SELinux denials last 60 seconds
logcat -d -T "$(date -d '60 seconds ago' '+%m-%d %H:%M:%S.000')" | grep avc

# Top memory consumers
dumpsys meminfo | head -30

# Find crash tombstones
ls -lt /data/tombstones/ | head -5

# Active wakelocks blocking suspend
cat /sys/kernel/debug/wakeup_sources | awk '$3 > 0 {print $1, $3}'

# DRM display pipeline status
cat /sys/kernel/debug/dri/0/state | grep -A2 "connector\|crtc\|plane"

# Network quick check
ip addr show | grep "inet " | grep -v 127.0.0.1

# Audio playback test (1kHz sine, 2s)
tinyplay /dev/zero -D 0 -d 0 -c 2 -r 48000 -b 16 -p 5

# Kernel errors since boot
dmesg -l err,crit,alert,emerg

# Full system snapshot to file
(getprop; dumpsys cpuinfo; dumpsys meminfo; dmesg -T) > /data/local/tmp/snapshot.txt
```
