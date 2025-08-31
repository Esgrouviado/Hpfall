# Makefile for HP Disk Protection Python

.PHONY: help install uninstall test clean check format

# Default target
help:
	@echo "HP Disk Protection Python - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  install     - Install the daemon system-wide (requires root)"
	@echo "  uninstall   - Remove the daemon from system (requires root)"
	@echo "  test        - Run basic functionality tests"
	@echo "  check       - Check code quality with pylint/flake8"
	@echo "  format      - Format code with black"
	@echo "  clean       - Clean up temporary files"
	@echo "  run         - Run the daemon in foreground mode (requires root)"
	@echo "  status      - Show systemd service status"
	@echo ""

# Installation targets
install:
	@if [ "$$(id -u)" != "0" ]; then \
		echo "Error: Installation requires root privileges"; \
		echo "Please run: sudo make install"; \
		exit 1; \
	fi
	python3 setup.py install

uninstall:
	@if [ "$$(id -u)" != "0" ]; then \
		echo "Error: Uninstallation requires root privileges"; \
		echo "Please run: sudo make uninstall"; \
		exit 1; \
	fi
	python3 setup.py uninstall

# Testing and development
test:
	python3 test_hp_protection.py

check:
	@echo "Checking code quality..."
	@if command -v pylint >/dev/null 2>&1; then \
		pylint hp_disk_protection.py || true; \
	else \
		echo "pylint not found, skipping..."; \
	fi
	@if command -v flake8 >/dev/null 2>&1; then \
		flake8 hp_disk_protection.py --max-line-length=100 || true; \
	else \
		echo "flake8 not found, skipping..."; \
	fi

format:
	@if command -v black >/dev/null 2>&1; then \
		black hp_disk_protection.py test_hp_protection.py setup.py; \
	else \
		echo "black not found, please install: pip install black"; \
	fi

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyo" -delete

# Runtime targets
run:
	@if [ "$$(id -u)" != "0" ]; then \
		echo "Warning: This program should be run as root for optimal performance"; \
	fi
	python3 hp_disk_protection.py --no-daemon

status:
	systemctl status hp-disk-protection || echo "Service not installed or not running"

# Development helpers
dev-install:
	chmod +x hp_disk_protection.py
	chmod +x test_hp_protection.py
	chmod +x setup.py

# Create a distribution package
dist: clean
	mkdir -p dist
	tar czf dist/hp-disk-protection-python.tar.gz \
		hp_disk_protection.py \
		setup.py \
		test_hp_protection.py \
		requirements.txt \
		README.md \
		Makefile
