# HP Disk Protection (Python)

Python daemon for HP laptops that detects freefall events and parks the hard drive heads to reduce damage risk.

Like HP 3D DriveGuard for Linux protects traditional Hard Disk Drives (HDDs) by using an integrated accelerometer to detect drops or severe jolts, 
temporarily "parking" the HDD's read/write heads and halting operations to prevent data corruption or damage to the drive.

## Key Features
- Monitors `/dev/freefall` for motion / drop events
- Parks drive heads via `/sys/block/<dev>/device/unload_heads`
- Controls HP HDD protection LED (`hp::hddprotect`)
- Adapts protection timing to AC vs battery & lid state
- Runs as a high‑priority background daemon (sched + mlock)
- Clean CLI, logging, and systemd service file

## Requirements
- HP laptop with freefall sensor (`/dev/freefall`)
- Linux + Python ≥ 3.6
- Root privileges

## Quick Install
```bash
sudo python3 setup.py install
sudo systemctl enable --now hp-disk-protection
```

## Manual Install
```bash
sudo cp hp_disk_protection.py /usr/local/bin/hp-disk-protection
sudo chmod +x /usr/local/bin/hp-disk-protection
# Create & enable systemd service (see setup.py template)
```

## Usage
CLI:
```bash
sudo hp-disk-protection              # default /dev/sda
sudo hp-disk-protection /dev/sdb     # specify device
sudo hp-disk-protection --no-daemon  # foreground / debug
hp-disk-protection --help
```

Service:
```bash
sudo systemctl start hp-disk-protection
sudo systemctl status hp-disk-protection
sudo journalctl -u hp-disk-protection -f
```

## How It Works (Lifecycle)
1. Read events from `/dev/freefall`
2. On trigger:
   - Write to `unload_heads` (parks heads)
   - Light LED (`hp::hddprotect`)
   - Start timer (duration depends on power / lid)
3. On expiry: unpark (by letting timeout elapse) & clear LED

## Adaptive Timings (Typical)
- AC power or lid open: ~2s active protection window
- Battery + lid closed: longer (up to ~20s)
- Internal head parking safety margin: ~21s

## Troubleshooting (Quick)
| Symptom | Hint |
|---------|------|
| Permission denied | Run with sudo |
| `/dev/freefall` missing | Check kernel modules / hardware support |
| Cannot access `unload_heads` | Verify device name (`ls /sys/block`) |
| No LED reaction | Confirm LED path exists |

Debug tips:
```bash
sudo hp-disk-protection --no-daemon
journalctl -u hp-disk-protection
ls -l /dev/freefall /sys/block/*/device/unload_heads
```

## Uninstall
```bash
sudo python3 setup.py uninstall
```

## Differences vs Original C
Improvements: structured OO design, argparse CLI, robust error handling, journald-friendly logging, cleaner systemd integration.  
Kept: core detection logic, performance focus, hardware behavior.

## License
GPLv3

## Credits
- Refactoring / Python version: https://github.com/Esgrouviado
- Based on fork: https://github.com/srijan/hpfall
- Original C contributors: Eric Piel (2008), Pavel Machek (2009)

---
Protect your disk: detect, park, recover—automatically.
