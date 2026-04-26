#!/usr/bin/env python3
# Run this script from the directory where you extracted the firmware package.
import glob
import subprocess
import sys
from pathlib import Path

EXPECTED_FILE = Path("src") / "main.py"


def run(cmd, ignore_errors=False):
    print(f"  {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 and not ignore_errors:
        print(f"ERROR: {result.stderr.strip()}")
        sys.exit(1)


def pick_tty():
    if sys.platform == "darwin":
        patterns = ["/dev/tty.usbmodem*", "/dev/cu.usbmodem*"]
    elif sys.platform == "win32":
        patterns = []
    else:
        patterns = ["/dev/ttyACM*", "/dev/ttyUSB*"]
    candidates = sorted(p for pat in patterns for p in glob.glob(pat))
    if sys.platform == "win32":
        print("Windows: enter your COM port (e.g. COM3)")
    options = candidates + ["Enter manually"]
    print("Select a serial port:")
    for i, opt in enumerate(options):
        print(f"  [{i}] {opt}")
    while True:
        choice = input("Choice: ").strip()
        if not choice.isdigit() or int(choice) >= len(options):
            print("Invalid choice, try again.")
            continue
        idx = int(choice)
        if idx == len(options) - 1:
            return input("Enter port: ").strip()
        return options[idx]


def find_files():
    src = Path("src")
    all_files = list(src.rglob("*.py")) + list(src.rglob("*.csv"))
    src_files = [f for f in all_files if "tools" not in f.parts]
    dirs = sorted({f.parent.relative_to(src).as_posix() for f in src_files if f.parent != src})
    return sorted(src_files), dirs


if not EXPECTED_FILE.exists():
    print(f"Firmware files not found.")
    print(f"Make sure you extracted the full firmware package and are running this")
    print(f"script from the extracted folder. Expected to find: {EXPECTED_FILE}")
    sys.exit(1)

tty = sys.argv[1] if len(sys.argv) == 2 else pick_tty()

src_files, dirs = find_files()
print(f"Found {len(src_files)} files, flashing to {tty}...")

for d in dirs:
    run(["mpremote", "connect", tty, "mkdir", f":{d}"], ignore_errors=True)

for f in src_files:
    dst = f.relative_to(Path("src")).as_posix()
    run(["mpremote", "connect", tty, "cp", str(f), f":{dst}"])

run(["mpremote", "connect", tty, "reset"])
print("Done.")
