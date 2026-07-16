import sys
import types
import pytest
from unittest.mock import patch

# Stub utime so the module loads under CPython
_utime = types.ModuleType('utime')
_utime.ticks_ms = lambda: 0
sys.modules.setdefault('utime', _utime)

sys.path.insert(0, 'src')

from services.logging import log


def test_log_formats_timestamp_and_message(capsys):
    with patch('services.logging.ticks_ms', return_value=12345):
        log("hello world")
    assert capsys.readouterr().out == "[12345] hello world\n"


def test_log_converts_non_string_to_str(capsys):
    with patch('services.logging.ticks_ms', return_value=1):
        log(3.14)
    assert capsys.readouterr().out == "[1] 3.14\n"


def test_log_handles_zero_timestamp(capsys):
    with patch('services.logging.ticks_ms', return_value=0):
        log("boot")
    assert capsys.readouterr().out == "[0] boot\n"
