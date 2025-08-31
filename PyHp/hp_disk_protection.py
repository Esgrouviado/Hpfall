#!/usr/bin/env python3
"""
Disk protection for HP machines.

Python refactoring of the original C implementation.
By J
GPL v3

Copyright 2008 Eric Piel
Copyright 2009 Pavel Machek <pavel@ucw.cz>

GPLv2.
"""

import os
import sys
import time
import errno
import signal
import argparse
from pathlib import Path
from typing import Optional


class HPDiskProtection:
    """HP Disk Protection daemon for parking hard drive heads during freefall."""
    
    def __init__(self, device: str = "/dev/sda"):
        self.device = device
        self.unload_heads_path = ""
        self.protection_active = False
        
        if not self._set_unload_heads_path(device):
            raise ValueError(f"Invalid device: {device}")
            
        if not self._valid_disk():
            raise RuntimeError(f"Cannot access disk protection for {device}")
    
    def _set_unload_heads_path(self, device: str) -> bool:
        """Set the path for unload_heads sysfs entry."""
        if len(device) <= 5 or not device.startswith("/dev/"):
            return False
            
        devname = device[5:]  # Remove "/dev/" prefix
        self.unload_heads_path = f"/sys/block/{devname}/device/unload_heads"
        return True
    
    def _valid_disk(self) -> bool:
        """Check if the disk supports head unloading."""
        try:
            with open(self.unload_heads_path, 'r') as f:
                return True
        except (OSError, IOError) as e:
            print(f"Error accessing {self.unload_heads_path}: {e}", file=sys.stderr)
            return False
    
    def _write_int(self, path: str, value: int) -> bool:
        """Write an integer value to a sysfs file."""
        try:
            with open(path, 'w') as f:
                f.write(str(value))
            return True
        except (OSError, IOError) as e:
            print(f"Error writing to {path}: {e}", file=sys.stderr)
            return False
    
    def set_led(self, on: bool) -> bool:
        """Control the HP disk protection LED."""
        led_path = "/sys/class/leds/hp::hddprotect/brightness"
        return self._write_int(led_path, 1 if on else 0)
    
    def protect(self, seconds: int) -> bool:
        """Protect the disk by parking heads for specified seconds."""
        return self._write_int(self.unload_heads_path, seconds * 1000)
    
    def on_ac(self) -> bool:
        """Check if system is running on AC power."""
        ac_path = "/sys/class/power_supply/AC0/online"
        try:
            with open(ac_path, 'r') as f:
                return f.read().strip() == "1"
        except (OSError, IOError):
            # If we can't determine AC status, assume we're on AC
            return True
    
    def lid_open(self) -> bool:
        """Check if laptop lid is open."""
        lid_path = "/proc/acpi/button/lid/LID/state"
        try:
            with open(lid_path, 'r') as f:
                state = f.read().strip()
                return "open" in state.lower()
        except (OSError, IOError):
            # If we can't determine lid state, assume it's open
            return True
    
    def _signal_handler(self, signum, frame):
        """Handle alarm signal to unpark heads."""
        self.protect(0)  # Unpark heads
        self.set_led(False)  # Turn off LED
        self.protection_active = False
    
    def daemonize(self):
        """Daemonize the process."""
        try:
            # First fork
            pid = os.fork()
            if pid > 0:
                sys.exit(0)  # Exit parent
        except OSError as e:
            print(f"Fork failed: {e}", file=sys.stderr)
            sys.exit(1)
        
        # Decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)
        
        # Second fork
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)  # Exit second parent
        except OSError as e:
            print(f"Fork failed: {e}", file=sys.stderr)
            sys.exit(1)
        
        # Redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        
        with open('/dev/null', 'r') as si:
            os.dup2(si.fileno(), sys.stdin.fileno())
        with open('/dev/null', 'w') as so:
            os.dup2(so.fileno(), sys.stdout.fileno())
        with open('/dev/null', 'w') as se:
            os.dup2(se.fileno(), sys.stderr.fileno())
    
    def run(self, daemon_mode: bool = True):
        """Main daemon loop."""
        freefall_device = "/dev/freefall"
        
        try:
            with open(freefall_device, 'rb') as freefall_fd:
                if daemon_mode:
                    self.daemonize()
                
                # Set high priority scheduling (requires root privileges)
                try:
                    os.sched_setscheduler(0, os.SCHED_FIFO, os.sched_param(99))
                except (OSError, AttributeError):
                    print("Warning: Could not set real-time scheduling priority", file=sys.stderr)
                
                # Lock memory pages (requires root privileges)
                try:
                    import ctypes
                    libc = ctypes.CDLL("libc.so.6")
                    MCL_CURRENT = 1
                    MCL_FUTURE = 2
                    result = libc.mlockall(MCL_CURRENT | MCL_FUTURE)
                    if result != 0:
                        raise OSError("mlockall failed")
                except (ImportError, OSError, AttributeError):
                    print("Warning: Could not lock memory pages", file=sys.stderr)
                
                # Set up signal handler for alarm
                signal.signal(signal.SIGALRM, self._signal_handler)
                
                print(f"HP Disk Protection daemon started for {self.device}")
                
                while True:
                    try:
                        # Read freefall event
                        data = freefall_fd.read(1)
                        signal.alarm(0)  # Cancel any pending alarm
                        
                        if not data:
                            continue
                        
                        count = data[0]
                        print(f"Freefall detected! Count: {count}")
                        
                        # Protect the disk
                        self.protect(21)  # Park heads for 21 seconds
                        self.set_led(True)  # Turn on protection LED
                        self.protection_active = True
                        
                        # Set alarm to unpark heads
                        if self.on_ac() or self.lid_open():
                            signal.alarm(2)  # Short protection on AC or lid open
                        else:
                            signal.alarm(20)  # Longer protection on battery with lid closed
                        
                    except KeyboardInterrupt:
                        print("Shutting down HP Disk Protection daemon")
                        break
                    except OSError as e:
                        if e.errno == errno.EINTR:
                            # Alarm expired, continue loop
                            continue
                        else:
                            print(f"Error reading freefall device: {e}", file=sys.stderr)
                            break
        
        except (OSError, IOError) as e:
            print(f"Error opening {freefall_device}: {e}", file=sys.stderr)
            return 1
        
        finally:
            # Cleanup: unpark heads and turn off LED
            self.protect(0)
            self.set_led(False)
        
        return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="HP Disk Protection daemon for parking hard drive heads during freefall",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Use default device /dev/sda
  %(prog)s /dev/sdb          # Use specific device
  %(prog)s --no-daemon       # Run in foreground (for debugging)
        """
    )
    
    parser.add_argument(
        'device',
        nargs='?',
        default='/dev/sda',
        help='Device to protect (default: /dev/sda)'
    )
    
    parser.add_argument(
        '--no-daemon',
        action='store_true',
        help='Run in foreground instead of daemonizing'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='HP Disk Protection Python 1.0'
    )
    
    args = parser.parse_args()
    
    try:
        # Check if running as root
        if os.geteuid() != 0:
            print("Warning: This program should be run as root for optimal performance", file=sys.stderr)
        
        # Create and run the protection daemon
        protection = HPDiskProtection(args.device)
        return protection.run(daemon_mode=not args.no_daemon)
        
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        parser.print_help()
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
