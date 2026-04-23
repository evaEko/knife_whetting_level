#!/usr/bin/env python3
import glob
import os
import subprocess
import sys

def run(cmd):
    print(f"  {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr.strip()}")
        sys.exit(1)

def pick_tty():
    candidates = sorted(glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*"))
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
            return input("Enter tty path: ").strip()
        return options[idx]

def find_files():
    all_files = glob.glob("src/**/*.py", recursive=True)
    src_files = [f for f in all_files if not f.startswith("src/tools/")]
    dirs = sorted({os.path.dirname(f).replace("src/", "") for f in src_files if os.path.dirname(f) != "src"})
    return sorted(src_files), dirs

tty = sys.argv[1] if len(sys.argv) == 2 else pick_tty()

src_files, dirs = find_files()
print(f"Found {len(src_files)} files, flashing to {tty}...")

for d in dirs:
    run(["mpremote", "connect", tty, "mkdir", f":{d}"])

for src in src_files:
    dst = src.removeprefix("src/")
    run(["mpremote", "connect", tty, "cp", src, f":{dst}"])

run(["mpremote", "connect", tty, "reset"])
print("Done.")
