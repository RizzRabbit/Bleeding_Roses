#!/usr/bin/env python3
"""Run Bleeding Roses mechanic tests. Exits non-zero when any check fails."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import test_mechanics


if __name__ == "__main__":
    failures = 0
    tests = [value for name, value in sorted(vars(test_mechanics).items()) if name.startswith("test_")]
    for test in tests:
        try:
            test()
            print(f"ok {test.__name__}")
        except Exception as exc:
            failures += 1
            print(f"FAIL {test.__name__}: {exc}")
            import traceback

            traceback.print_exc()
    if failures:
        print(f"{failures} test(s) failed")
        raise SystemExit(1)
    print(f"{len(tests)} tests passed")
