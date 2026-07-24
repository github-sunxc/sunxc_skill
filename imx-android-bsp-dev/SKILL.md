---
name: imx-android-bsp-dev
description: >-
  Use when performing Android BSP development on NXP i.MX platforms — building
  Android images, flashing devices, running CTS/VTS/GTS/STS tests, debugging
  HAL/driver/kernel issues, or developing kernel/U-Boot. Trigger on: Android
  build, flash image, run CTS, adb debug, kernel menuconfig, device tree, boot
  mode, BCU, xTS test.
---

# i.MX Android BSP Development

## Overview

Orchestrator skill for Android BSP development on NXP i.MX platforms. Routes to specific reference files based on user task. Core architecture: AI agent on build server → SSH (mcp-ssh-tmux) → Ubuntu PC → USB/tty → i.MX board.

## When to Use

- Building Android images (full/incremental)
- Flashing images to i.MX boards via UUU
- Running CTS/VTS/GTS/STS test suites
- Debugging via adb (remount, logcat, push)
- Kernel or U-Boot development (menuconfig, device tree)
- Switching boot modes via BCU
- Finding debug/diagnostic commands

## Environment Architecture

```
Build Server (AI Agent)  ──SSH──>  Ubuntu PC (10.193.102.127)  ──USB/tty──>  i.MX Board
     ↑ skill runs here              ↑ mcp-ssh-tmux session          ↑ target device
     ↑ $MY_ANDROID source           ↑ sshfs mount to build server   ↑ adb/fastboot/console
```

## Required Inputs

| Input | How to Get | Default |
|-------|-----------|---------|
| Remote Server IP | User provides or default | 10.193.102.127 |
| SSH Username | User provides or default | maximus |
| Device Serial | User provides (adb serial) | — (MUST ask) |
| Console Device | User provides (ttyUSBx) | — (MUST ask) |
| xTS Location | User provides (path on remote) | — (MUST ask) |
| sshfs Mount Point | Auto-detect via `mount` cmd | ~/remote/sshfs/ |

**Dynamic sensing**: Scan user prompt for these values. Ask ONLY for missing ones required by the specific task. Confirm defaults before proceeding.
你可以使用"adb devices"和"fastboot devices"获取Device Serial。如果这两个命令只能找到一个Device Serial，那就用它。如果超过一个或者没有找到，再询问用户

## Connection Setup

### Prerequisites (one-time setup per machine pair)

The remote Ubuntu PC likely has a `.bashrc` that auto-attaches SSH sessions to a tmux session. This conflicts with mcp-ssh-tmux (which cannot execute tmux commands on the remote). To ensure session isolation, the following one-time setup is required:

**Build server `~/.ssh/config`** — add `SetEnv` for the remote host:
```
Host <remote-ip>
    SetEnv LC_OPENCODE=1
```

**Remote Ubuntu PC `~/.bashrc`** — detect and route opencode connections:
```bash
if [[ -n "$SSH_CONNECTION" && -z "$TMUX" && -z "$VSCODE_IPC_HOOK_CLI" ]]; then
    if [[ "$LC_OPENCODE" == "1" ]]; then
        exec tmux new-session -A -s opencode-remote
    else
        tmux ls | grep -q "0:" && tmux attach -t 0 || tmux new-session -s 0
    fi
fi
```

**Requirements:**
- Build server OpenSSH >= 7.8 (for `SetEnv` support) — verify: `ssh -V`
- Remote sshd must accept `LC_*` env vars — verify: `grep AcceptEnv /etc/ssh/sshd_config` shows `LC_*`

### Connection Steps

> ⚠️ **Steps 1-2 are NON-NEGOTIABLE.** You MUST complete BOTH before ANY other command. Skipping logging = skill violation.

1. **SSH session** (opens into isolated `opencode-remote` tmux session automatically):
   ```
   ssh_tmux_open_session(host="<remote-ip>", username="<user>")
   ```
   Verify isolation:
   ```
   ssh_tmux_send_command(session_id, "echo $TMUX | grep -o 'opencode-remote' || tmux display-message -p '#S'")
   ```
   Expected: session name contains `opencode-remote`.

2. **⚠️ Enable session logging (MANDATORY — IMMEDIATELY after step 1)**:
   ```
   ssh_tmux_send_command(session_id, "mkdir -p ~/remote-agent-logs && tmux pipe-pane -o 'cat >> ~/remote-agent-logs/$(date +%Y%m%d-%H%M%S)-opencode.log'")
   ```
   This captures ALL terminal I/O to a timestamped log file. **Do NOT proceed to any other command until this completes.**

3. **Serial console** (when needed):
   ```
   ssh_tmux_send_command(session_id, "socat STDIO,raw,echo=0,escape=0x1d UNIX-CONNECT:/tmp/<ttyUSBx>.sock")
   ```

4. **Detect sshfs mount**:
   ```
   ssh_tmux_send_command(session_id, "mount | grep fuse.sshfs")
   ```

5. **Detect $MY_ANDROID**: Current working directory — verify `build/envsetup.sh` exists.

### Troubleshooting: Session Not Isolated

If after connecting, `tmux display-message -p '#S'` shows session `0` instead of `opencode-remote`, the prerequisites are not configured. Diagnose:

1. **Check `LC_OPENCODE` reached remote:**
   ```
   ssh_tmux_send_command(session_id, "echo LC_OPENCODE=$LC_OPENCODE")
   ```
   - Empty → Build server `~/.ssh/config` missing `SetEnv LC_OPENCODE=1` for this host
   - Empty → Remote sshd doesn't `AcceptEnv LC_*` (check `/etc/ssh/sshd_config`)

2. **Check remote `.bashrc` has the routing logic:**
   ```
   ssh_tmux_send_command(session_id, "grep LC_OPENCODE ~/.bashrc")
   ```
   - No match → `.bashrc` hasn't been updated

3. **Fallback (if you cannot modify the remote):**
   Commands will execute in the user's existing tmux session. This works but is not isolated. Proceed with caution — avoid long-running or destructive operations that may interfere with the user's active work.

## Workflow Routing

| User wants to... | Load this reference | Key command preview |
|-----------------|---------------------|---------------------|
| Build Android image | `references/android-build.md` | `./imx-make.sh -j$(nproc)` |
| Flash image to device | `references/android-flash.md` | `uuu_imx_android_flash.sh` |
| Run CTS/VTS/GTS/STS | `references/xts-testing.md` | `cts-tradefed run cts` |
| Debug (remount/push/logs) | `references/android-debug.md` | `adb root && adb remount` |
| Switch boot mode | `references/bcu.md` | `bcu reset usb -board=...` |
| Kernel/U-Boot development | `references/kernel-uboot-dev.md` | `make menuconfig` |
| Find debug commands | `references/debug-commands.md` | (comprehensive reference) |

**IMPORTANT**: Load ONLY the reference file matching the user's task. NEVER load all references at once.

## Quick Reference

| Task | Command |
|------|---------|
| Full build | `source build/envsetup.sh && lunch <target> && ./imx-make.sh -j$(nproc)` |
| Flash via UUU | `./uuu_imx_android_flash.sh -f <soc> -a -e` |
| ADB remount | `adb root && adb disable-verity && adb reboot && adb remount` |
| Run CTS module | `run cts -m <ModuleName>` |
| BCU reset to USB | `bcu reset usb -board=<board>` |
| Kernel defconfig | `make imx_v8_defconfig && make menuconfig` |

## Test Execution Monitoring (MANDATORY)

> **NON-NEGOTIABLE.** After launching ANY test or long-running task (xTS suites, custom test scripts, build jobs, flash operations, or any other Android BSP test), you MUST arrange ongoing result monitoring. NEVER let all tasks end and wait for the human to manually check.

### The Rule

Whenever a test or task is launched and its result is not immediately available:

1. **Keep the SSH session open** — do NOT close it while work is running
2. **Set up some form of ongoing monitoring** — the exact method is your call (see below)
3. **Report back proactively** when results are ready, or when failure/hang is detected

### Choosing a Monitoring Approach

There is no single prescribed method. You are expected to reason about the test being run and choose the most appropriate strategy. Consider:

- **How long will this take?** A unit test script finishes in seconds; a full CTS suite runs for hours. Match your polling frequency to the expected duration.
- **What signals completion?** A result file appearing, a process exiting, a log line, a return code — use whichever signal is most reliable for this specific test.
- **What does failure look like?** Detect hangs, crashes, or error output — don't only watch for success.
- **Is the test interactive or headless?** Interactive tradefed sessions show progress in the console; background scripts may only emit exit codes.

Monitoring options you can combine as needed:
- Periodic `get_snapshot()` to observe terminal output
- A background polling script (`nohup ... &`) that watches for result files or process exit
- Tailing log files (`tail -f`) to stream output
- Watching for process completion (`wait <PID>`, `while kill -0 <PID>; do ...`)
- Parsing result artifacts (XML, logcat, dmesg) once the test ends

**You decide the interval, the signal, and the method.** The only requirement is that monitoring is active — the agent must not go silent until results are known.

### What Counts as "Monitoring Set Up"

- [ ] SSH session is still open (not closed)
- [ ] There is an active mechanism (script, polling plan, or background task) that will detect completion or failure
- [ ] The agent has committed to reporting results when they arrive

### Anti-Patterns (BLOCKING)

| Anti-Pattern | Correct Behavior |
|---|---|
| Launch test → close SSH → tell user "check results later" | Launch test → choose appropriate monitoring → keep session → report proactively |
| Launch test → end response → never follow up | Launch test → set up monitoring → report when done |
| "Tests are running, let me know when done" | "Tests are running. I'm monitoring via [method] and will report results." |
| Polling at fixed intervals regardless of test type | Calibrate frequency to expected duration and signal type |

---

## Debug Escalation Principles

When debugging on-device, follow the **least-invasive** approach first:

| Priority | Method | When to Use |
|----------|--------|-------------|
| 1 (preferred) | `adb remount` + push single lib/ELF | Can isolate issue to one binary |
| 2 | Flash single image partition (e.g. `fastboot flash system`) | Single lib replacement insufficient |
| 3 | Flash all images via `fastboot` | Multiple partitions affected |
| 4 (last resort) | UUU full flash | Board unresponsive, fastboot unavailable |

**Rule**: Always try higher-priority methods first. UUU is the nuclear option — use only when the board is bricked or fastboot mode is unreachable.

### Code Modification Priority

When fixing issues, follow this order — prefer downstream (NXP device) changes over upstream (AOSP) changes:

| Priority | Action | Confirmation Required |
|----------|--------|-----------------------|
| 1 (preferred) | Fix in NXP device/ vendor code (downstream) | No |
| 2 | Check if AOSP already has a fix (cherry-pick) | No |
| 3 (last resort) | Modify AOSP code directly | **Yes — ask user before proceeding** |

**Never modify AOSP source without explicit user approval.** AOSP changes are harder to maintain across upgrades and may conflict with future merges.

## Development Workflow Discipline

### Source Code Changes

- **Always create a new debug branch** before modifying source code (`git checkout -b debug/<topic>`)
- If modifying the Ubuntu PC build environment (env vars, toolchains, configs), **document every change** in a scratch note or commit message so it can be reverted

### Session Cleanup Reminder

**After all development work is complete**, remind the user:

> "Development tasks are done. Would you like me to help restore the environment (revert debug branches, undo env changes, unmount temp filesystems) to avoid impacting the next development session?"

Never skip this step — leftover debug state is the #1 cause of "works on my machine" confusion in shared build environments.

## Session Logging & Command Archival

> **THIS IS NOT OPTIONAL.** Logging is a hard requirement of this skill, not a nice-to-have. Every session without logging is a session that cannot be debugged, replayed, or audited. If you skip logging, you are violating this skill.

### Why This Exists

- **Reproducibility**: When a board bricks or a test fails, the log is the ONLY way to replay what happened
- **Environment restoration**: The command archive tells you exactly what was changed and needs reverting
- **Handoff**: Another engineer (or future you) can understand what was done without guessing

### tmux Session Logging (automatic capture)

**Already handled by Connection Step 2** (see above). The `tmux pipe-pane` command captures ALL terminal I/O automatically. No further action needed for raw logging.

Log location: `~/remote-agent-logs/<timestamp>-opencode.log` on the Ubuntu PC.

### Command Archival (structured record)

In addition to raw logs, maintain a **structured** command record. At session start, create:

```
ssh_tmux_send_command(session_id, "echo '# Session: $(date +%Y-%m-%d) <TOPIC>' > ~/remote-agent-logs/$(date +%Y%m%d)-commands.md")
```

Then **after every significant command**, append to this file:

```
ssh_tmux_send_command(session_id, "echo '- `<command>` — <purpose>' >> ~/remote-agent-logs/$(date +%Y%m%d)-commands.md")
```

#### What to Log

| Always Log | Skip |
|-----------|------|
| Any `adb` command | `ls`, `cd`, `pwd` (navigational) |
| Any `fastboot` / `uuu` command | `echo` used for testing |
| Any file push/pull/edit | Repeated retries of same command |
| Environment variable changes | Read-only inspection (`cat`, `grep`) |
| Service restarts / reboots | |
| Build commands | |

#### Example Command Archive

```markdown
# Session: 2025-05-29 Debug camera HAL

## Commands Executed
- `adb root && adb remount` — prepare for file push
- `adb push out/.../camera.so /vendor/lib64/` — deploy patched lib
- `adb shell setprop persist.vendor.camera.debug 1` — enable debug logs
- `adb reboot` — apply changes

## Environment Changes
- Modified `~/.bashrc`: added `export CAMERA_DEBUG=1`
- Symlinked `/opt/toolchain-v2` → `/opt/toolchain`
```

### Verification Checklist (before closing session)

Before `ssh_tmux_close_session()`, confirm:
- [ ] `ls ~/remote-agent-logs/*opencode.log` — raw log exists and has content
- [ ] `cat ~/remote-agent-logs/$(date +%Y%m%d)-commands.md` — structured log is populated
- [ ] If environment was modified — changes are documented in "Environment Changes" section
