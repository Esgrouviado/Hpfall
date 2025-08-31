#!/usr/bin/env python3
"""
Setup script for HP Disk Protection daemon.
"""

from pathlib import Path
import stat
import shutil
import sys
import os

def install_daemon():
    """Install the HP Disk Protection daemon."""
    script_dir = Path(__file__).parent
    source_file = script_dir / "hp_disk_protection.py"
    
    # Target installation paths
    target_bin = Path("/usr/local/bin/hp-disk-protection")
    target_service = Path("/etc/systemd/system/hp-disk-protection.service")
    
    # Check if running as root
    if os.geteuid() != 0:
        print("Error: Installation requires root privileges", file=sys.stderr)
        print("Please run: sudo python3 setup.py install", file=sys.stderr)
        return 1
    
    try:
        # Copy the main script
        print(f"Installing {source_file} to {target_bin}")
        shutil.copy2(source_file, target_bin)
        
        # Make it executable
        target_bin.chmod(target_bin.stat().st_mode | stat.S_IEXEC)
        
        # Create systemd service file
        service_content = f"""[Unit]
Description=HP Disk Protection Daemon
After=multi-user.target

[Service]
Type=forking
ExecStart={target_bin}
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
"""
        
        print(f"Creating systemd service file: {target_service}")
        with open(target_service, 'w') as f:
            f.write(service_content)
        
        # Reload systemd
        os.system("systemctl daemon-reload")
        
        print("Installation completed successfully!")
        print("To start the service:")
        print("  sudo systemctl start hp-disk-protection")
        print("To enable on boot:")
        print("  sudo systemctl enable hp-disk-protection")
        
        return 0
        
    except Exception as e:
        print(f"Installation failed: {e}", file=sys.stderr)
        return 1

def uninstall_daemon():
    """Uninstall the HP Disk Protection daemon."""
    target_bin = Path("/usr/local/bin/hp-disk-protection")
    target_service = Path("/etc/systemd/system/hp-disk-protection.service")
    
    # Check if running as root
    if os.geteuid() != 0:
        print("Error: Uninstallation requires root privileges", file=sys.stderr)
        print("Please run: sudo python3 setup.py uninstall", file=sys.stderr)
        return 1
    
    try:
        # Stop and disable service
        os.system("systemctl stop hp-disk-protection 2>/dev/null")
        os.system("systemctl disable hp-disk-protection 2>/dev/null")
        
        # Remove files
        if target_service.exists():
            print(f"Removing {target_service}")
            target_service.unlink()
        
        if target_bin.exists():
            print(f"Removing {target_bin}")
            target_bin.unlink()
        
        # Reload systemd
        os.system("systemctl daemon-reload")
        
        print("Uninstallation completed successfully!")
        return 0
        
    except Exception as e:
        print(f"Uninstallation failed: {e}", file=sys.stderr)
        return 1

def main():
    """Main setup function."""
    if len(sys.argv) != 2:
        print("Usage: python3 setup.py [install|uninstall]", file=sys.stderr)
        return 1
    
    command = sys.argv[1].lower()
    
    if command == "install":
        return install_daemon()
    elif command == "uninstall":
        return uninstall_daemon()
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print("Usage: python3 setup.py [install|uninstall]", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
