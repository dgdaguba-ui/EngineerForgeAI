#!/usr/bin/env python3
"""Full pipeline: generate -> validate -> cost -> previews -> reports -> tests."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
steps = [["generate.py"], ["validate.py"], ["cost.py"], ["previews.py"], ["reports.py"]]
status = 0
for s in steps:
    print(f"\n=== {s[0]} ===", flush=True)
    r = subprocess.run([sys.executable, str(HERE / s[0]), *s[1:]])
    if r.returncode and s[0] == "validate.py":
        print("validate.py reported FAIL - continuing so reports reflect it")
        status = 1
    elif r.returncode:
        sys.exit(r.returncode)
print("\n=== pytest ===", flush=True)
r = subprocess.run([sys.executable, "-m", "pytest", "-q", str(HERE.parent / "tests")])
sys.exit(status or r.returncode)
