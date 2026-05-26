#!/usr/bin/env python3
"""
Quick test of file generation system.
"""

import sys
import json
from core.file_utils import is_safe_filename, ensure_extension, validate_and_prepare_filename

def test_filename_safety():
    print("[TEST] Filename safety validation")

    test_cases = [
        ("systemdown.py", True),
        ("system down.py", True),
        ("data@2024.json", True),
        ("config.yaml", True),
        ("../etc/passwd", False),
        ("file\x00.py", False),
        ("CON.txt", False),
        ("", False),
    ]

    for filename, expected in test_cases:
        result = is_safe_filename(filename)
        status = "OK" if result == expected else "FAIL"
        print(f"  [{status}] {repr(filename)} -> {result} (expected {expected})")

def test_extension():
    print("\n[TEST] Extension handling")

    test_cases = [
        ("systemdown", "py", "systemdown.py"),
        ("systemdown.py", "py", "systemdown.py"),
        ("config", "json", "config.json"),
        ("config.yaml", "json", "config.json"),
        ("README", "md", "README.md"),
    ]

    for filename, format, expected in test_cases:
        result = ensure_extension(filename, format)
        status = "OK" if result == expected else "FAIL"
        print(f"  [{status}] {repr(filename)} + {format} -> {repr(result)} (expected {repr(expected)})")

def test_validation():
    print("\n[TEST] Full validation")

    test_cases = [
        ("systemdown.py", "py", True),
        ("config.json", "json", True),
        ("../bad", "txt", False),
        ("CON", "txt", False),
    ]

    for filename, format, expected_valid in test_cases:
        is_valid, prepared, error = validate_and_prepare_filename(filename, format)
        status = "OK" if is_valid == expected_valid else "FAIL"
        print(f"  [{status}] {repr(filename)} + {format}")
        if is_valid:
            print(f"        -> Prepared: {repr(prepared)}")
        else:
            print(f"        -> Error: {error}")

if __name__ == "__main__":
    test_filename_safety()
    test_extension()
    test_validation()
    print("\n[DONE] All tests complete")
