#!/usr/bin/env python3
"""
Example 1: Twin a simple Python repo and query the result.
Run: python examples/01_simple_twin.py
"""

import json, urllib.request, subprocess, tempfile, shutil, os, sys

# ── Setup: create a synthetic Python repo to twin ──────────────────────────

temp_dir = tempfile.mkdtemp(prefix="ptwin_example1_")
repo_dir = os.path.join(temp_dir, "mymath")

os.makedirs(repo_dir)

# Write a simple Python module
with open(os.path.join(repo_dir, "mymath.py"), "w") as f:
    f.write('''
"""MyMath — simple arithmetic operations."""


def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


def subtract(a: float, b: float) -> float:
    """Subtract b from a."""
    return a - b


def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


def divide(a: float, b: float) -> float:
    """Divide a by b. Raises ValueError if b is zero."""
    if b == 0:
        raise ValueError("Division by zero")
    return a / b


def power(base: float, exponent: float) -> float:
    """Raise base to exponent power."""
    return base ** exponent
''')

with open(os.path.join(repo_dir, "README.md"), "w") as f:
    f.write("# MyMath\nSimple arithmetic library.\n")

with open(os.path.join(repo_dir, "pyproject.toml"), "w") as f:
    f.write('[project]\nname = "mymath"\nversion = "0.1.0"\n')

print(f"[example 1] Created test repo at {repo_dir}")

# ── Step 1: Run the twin-maker ──────────────────────────────────────────────

result = subprocess.run([
    sys.executable, "-m", "plato_twin_maker.plat_twin_maker",
    "--repo", repo_dir,
    "--plato", "http://localhost:8847",
    "--dry-run",  # don't actually submit to PLATO
], capture_output=True, text=True)

print(f"[example 1] Twin-maker output:\n{result.stdout}")
if result.stderr:
    print(f"[example 1] stderr:\n{result.stderr[:200]}")

# ── Step 2: Analyze the generated manifest ─────────────────────────────────

import glob
manifest_files = glob.glob("/tmp/twin-manifest-*.json")
manifest_files.sort(key=os.path.getmtime, reverse=True)
latest = manifest_files[0] if manifest_files else None

if latest:
    with open(latest) as f:
        twin = json.load(f)

    print(f"\n[example 1] Twin manifest:")
    print(f"  Repo: {twin['repo_url']}")
    print(f"  Modules: {twin['modules']}")
    print(f"  Tiles: {len(twin['tiles'])}")
    print(f"  Room: {twin['room_name']}")

    print(f"\n[example 1] All tile questions:")
    for tile in twin['tiles']:
        print(f"  - {tile['question']}")

    print(f"\n[example 1] 'divide' tile answer:")
    div_tile = next((t for t in twin['tiles'] if 'divide' in t['question'].lower()), None)
    if div_tile:
        print(f"  {div_tile['answer'][:200]}...")

# ── Step 3: Query PLATO (if available) ─────────────────────────────────────

try:
    response = urllib.request.urlopen(
        "http://localhost:8847/room/twin-python", timeout=2
    )
    data = json.loads(response.read())
    print(f"\n[example 1] PLATO room has {data['tile_count']} tiles")
except Exception as e:
    print(f"\n[example 1] PLATO not available: {e}")

# Cleanup
shutil.rmtree(temp_dir)
print("\n[example 1] Done — cleaned up temp repo")