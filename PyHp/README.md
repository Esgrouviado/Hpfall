# HP Disk Protection Python

A Python refactoring of the original C implementation for HP laptop disk protection. This daemon monitors for freefall events and protects the hard drive by parking the heads to prevent damage during drops.

## Features

- **Freefall Detection**: Monitors `/dev/freefall` for drop events
- **Head Parking**: Automatically parks hard drive heads during freefall
- **LED Control**: Controls the HP disk protection LED indicator
- **Power Management**: Adjusts protection duration based on AC/battery status
- **Daemon Mode**: Runs as a background daemon with high priority scheduling
- **Systemd Integration**: Includes service file for system integration

## Requirements

- Linux system with HP laptop hardware support
- Python 3.6 or later
- Root privileges (for hardware access and real-time scheduling)
- HP laptop with freefall sensor (`/dev/freefall` device)

## Installation

### Quick Install
```bash
sudo python3 setup.py install
sudo systemctl enable hp-disk-protection
sudo systemctl start hp-disk-protection
```

### Manual Installation
1. Copy `hp_disk_protection.py` to `/usr/local/bin/hp-disk-protection`
2. Make it executable: `chmod +x /usr/local/bin/hp-disk-protection`
3. Create systemd service (see setup.py for template)

## Usage

### Command Line
```bash
# Use default device (/dev/sda)
sudo ./hp_disk_protection.py

# Specify device
sudo ./hp_disk_protection.py /dev/sdb

# Run in foreground (for debugging)
sudo ./hp_disk_protection.py --no-daemon

# Show help
./hp_disk_protection.py --help
```

### As System Service
```bash
# Start the service
sudo systemctl start hp-disk-protection

# Enable on boot
sudo systemctl enable hp-disk-protection

# Check status
sudo systemctl status hp-disk-protection

# View logs
sudo journalctl -u hp-disk-protection -f
```

## How It Works

1. **Monitoring**: The daemon continuously reads from `/dev/freefall` device
2. **Detection**: When a freefall event is detected, the daemon:
   - Parks the hard drive heads by writing to `/sys/block/{device}/device/unload_heads`
   - Turns on the protection LED via `/sys/class/leds/hp::hddprotect/brightness`
   - Sets a timer to unpark the heads
3. **Recovery**: After the protection period, heads are unparked and LED turned off
4. **Adaptive Timing**: Protection duration varies based on power source and lid state

## Configuration

The daemon automatically detects:
- **AC Power**: Via `/sys/class/power_supply/AC0/online`
- **Lid State**: Via `/proc/acpi/button/lid/LID/state`

Protection timings:
- **AC Power or Lid Open**: 2 seconds protection
- **Battery with Lid Closed**: 20 seconds protection
- **Head Parking Duration**: 21 seconds

## Differences from Original C Implementation

### Improvements
- **Better Error Handling**: More robust error checking and reporting
- **Command Line Interface**: Proper argument parsing with help
- **Logging**: Better integration with system logging
- **Code Organization**: Object-oriented design for better maintainability
- **Documentation**: Comprehensive inline documentation

### Maintained Features
- **Same Core Functionality**: Identical freefall detection and head parking
- **Performance**: High-priority scheduling and memory locking
- **Hardware Compatibility**: Works with same HP laptop models

## Troubleshooting

### Common Issues

1. **Permission Denied**
   ```
   Error: This program should be run as root
   ```
   Solution: Run with `sudo`

2. **Device Not Found**
   ```
   Error accessing /sys/block/sda/device/unload_heads
   ```
   Solution: Check device name or verify HP laptop support

3. **Freefall Device Missing**
   ```
   Error opening /dev/freefall: No such file or directory
   ```
   Solution: Verify HP laptop with freefall sensor, check kernel modules

### Debugging
- Run with `--no-daemon` to see output in foreground
- Check system logs: `journalctl -u hp-disk-protection`
- Verify hardware support: `ls -la /dev/freefall /sys/block/*/device/unload_heads`

## Uninstallation

```bash
sudo python3 setup.py uninstall
```

## License

GPLv2 - Same as original implementation

## Credits
- J https://github.com/Esgrouviado
- Python refactoring: Maintains original functionality and design principles
- Fork from https://github.com/srijan/hpfall
- Original C implementation: Eric Piel (2008), Pavel Machek (2009)