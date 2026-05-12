#!/usr/bin/env python3
# Usage: python build_flash.py [-v] [port]
import glob
import itertools
import subprocess
import sys
import time
from pathlib import Path

MPREMOTE = [sys.executable, "-m", "mpremote"]
VERBOSE  = '-v' in sys.argv or '--verbose' in sys.argv
_args    = [a for a in sys.argv[1:] if a not in ('-v', '--verbose')]


# --- output helpers ---

def _ok():
    sys.stdout.write(' \033[32m✓\033[0m\n')
    sys.stdout.flush()

def _fail(msg):
    sys.stdout.write(' \033[31m✗\033[0m\n')
    print(f"  ERROR: {msg}")
    sys.exit(1)

def _run(cmd, ignore_errors=False):
    if VERBOSE:
        print(f"  {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 and not ignore_errors:
        if VERBOSE:
            print(f"ERROR: {result.stderr.strip()}")
            sys.exit(1)
        _fail(result.stderr.strip())
    return result

def _spin(label, cmd, ignore_errors=False):
    """Run one command with a spinner; falls back to plain output in verbose mode."""
    if VERBOSE:
        print(label)
        return _run(cmd, ignore_errors)

    frames = itertools.cycle('|/-\\')
    sys.stdout.write(f"  {label} ")
    sys.stdout.flush()

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while proc.poll() is None:
        sys.stdout.write(f"\r  {label} {next(frames)}")
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write(f"\r  {label}  ")
    _, err = proc.communicate()

    if proc.returncode != 0 and not ignore_errors:
        _fail(err.decode().strip())
    _ok()


# --- device helpers ---

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
    src = Path("src_ref")
    all_files = list(src.rglob("*.py")) + list(src.rglob("*.csv")) + list(src.rglob("*.txt"))
    src_files = [f for f in all_files if "tools" not in f.parts]
    dirs = sorted({f.parent.relative_to(src).as_posix()
                   for f in src_files if f.parent != src})
    return sorted(src_files), dirs


def clean_device(tty, src_files, dirs):
    top_dirs  = sorted({Path(d).parts[0] for d in dirs})
    top_files = [f.relative_to(Path("src_ref")).as_posix()
                 for f in src_files if f.parent == Path("src_ref")]
    rmrf = (
        "import os\n"
        "def _rm(p):\n"
        "    try:\n"
        "        for e in os.listdir(p): _rm(p+'/'+e)\n"
        "        os.rmdir(p)\n"
        "    except OSError:\n"
        "        try: os.remove(p)\n"
        "        except: pass\n"
    )
    rmrf += "\n".join(f"_rm('{d}')" for d in top_dirs)
    rmrf += "\n" + "\n".join(f"_rm('{f}')" for f in top_files)
    _spin("Cleaning device...", MPREMOTE + ["connect", tty, "exec", rmrf])


def make_dirs(tty, dirs):
    if VERBOSE:
        print("Creating directories...")
    else:
        sys.stdout.write("  Creating directories...")
        sys.stdout.flush()
    for d in dirs:
        _run(MPREMOTE + ["connect", tty, "mkdir", f":{d}"], ignore_errors=True)
    if not VERBOSE:
        _ok()


def _exists_on_device(tty, path):
    """Return True if path exists on the device filesystem."""
    check = f"import os\ntry:\n    os.stat('{path}')\n    print('1')\nexcept OSError:\n    print('0')\n"
    result = subprocess.run(
        MPREMOTE + ["connect", tty, "exec", check],
        capture_output=True, text=True
    )
    return result.stdout.strip() == '1'


_SKIP_IF_EXISTS = {"config.txt", "data.txt"}


def upload_files(tty, src_files):
    total = len(src_files)
    if VERBOSE:
        print(f"Uploading {total} files...")
    bar_w = 24

    for i, f in enumerate(src_files, 1):
        dst = f.relative_to(Path("src_ref")).as_posix()
        if f.name in _SKIP_IF_EXISTS and _exists_on_device(tty, dst):
            if VERBOSE:
                print(f"  Skipping {dst} (already exists on device)")
            continue
        if VERBOSE:
            _run(MPREMOTE + ["connect", tty, "cp", str(f), f":{dst}"])
        else:
            filled = bar_w * i // total
            bar    = '█' * filled + '░' * (bar_w - filled)
            name   = f.name
            sys.stdout.write(f"\r  Uploading [{bar}] {i}/{total}  {name:<28}")
            sys.stdout.flush()
            result = subprocess.run(
                MPREMOTE + ["connect", tty, "cp", str(f), f":{dst}"],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                sys.stdout.write('\n')
                _fail(f"{dst}: {result.stderr.strip()}")

    if not VERBOSE:
        sys.stdout.write(f"\r  Uploading [{bar_w * '█'}] {total}/{total}  ")
        _ok()


# --- main ---

tty = _args[0] if _args else pick_tty()

src_files, dirs = find_files()
print(f"Flashing {len(src_files)} files → {tty}  (use -v for verbose)")

clean_device(tty, src_files, dirs)
make_dirs(tty, dirs)
upload_files(tty, src_files)
_spin("Resetting device...",  MPREMOTE + ["connect", tty, "reset"])
print("Done.")
