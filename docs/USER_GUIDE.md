# Plato-Twin-Maker — User Guide

*How to use the twin-maker as a knowledge layer, not just a documentation tool.*

---

## The Core Concept

Every time you run the twin-maker on a repo, you create a **PLATO-twin**: a live overlay on the original code where every function and module is an explicit, queryable tile.

The original code is still the source of truth. The twin doesn't replace it — it **wraps** it. You can read a tile and understand what a function does without reading the source. You can query the tile room and get answers without calling the function.

**The twin produces the same output as the original code.** That's the test. If you can ask "what does `add(2,3)` return?" and get `5` from the tiles, the twin is faithful.

---

## Walking Through a Full Session

### Step 1: Choose a Repo

Start with something you know well. You'll be able to verify whether the twin is accurate.

```bash
# A simple, well-documented repo
python -m plato_twin_maker.plat_twin_maker \
  --repo https://github.com/SuperInstance/plato-twin-maker \
  --plato http://localhost:8847
```

### Step 2: Inspect the Manifest

After running, a manifest is saved to `/tmp/twin-manifest-{hash}.json`:

```bash
cat /tmp/twin-manifest-*.json | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(f'Repo: {d[\"repo_url\"]}')
print(f'Modules: {d[\"modules\"]}')
print(f'Tiles: {len(d[\"tiles\"])}')
print(f'Room: {d[\"room_name\"]}')
print()
print('Sub-rooms:', ', '.join(d['rooms'][:5]))
"
```

### Step 3: Query Your Twin in PLATO

Say you extracted a Python repo and want to find the `Calculator` class:

```python
import urllib.request

url = "http://localhost:8847/room/twin-python"
with urllib.request.urlopen(url) as r:
    data = json.load(r)

# Find tiles about the Calculator class
calc_tiles = [
    t for t in data['tiles']
    if 'Calculator' in t['question']
]

for t in calc_tiles:
    print(f"Q: {t['question']}")
    print(f"A: {t['answer'][:200]}")
    print(f"Confidence: {t.get('confidence', '?')}")
    print()
```

### Step 4: Use Tiles as a Knowledge Layer

The tiles aren't just documentation — they're queryable knowledge:

```python
def ask_twin(question: str, room: str = "twin-python"):
    """Ask the PLATO-twin a question."""
    url = f"http://localhost:8847/room/{room}"
    with urllib.request.urlopen(url) as r:
        tiles = json.load(r)['tiles']

    # Find best match by tag similarity
    best = None
    best_score = 0
    q_words = set(question.lower().split())

    for tile in tiles:
        tile_words = set(','.join(tile.get('tags', [])).split())
        score = len(q_words & tile_words)
        if score > best_score:
            best_score = score
            best = tile

    if best and best_score > 0:
        return best['answer']
    return None
```

---

## The Self-Glue Principle

If a required component doesn't exist, the maker creates it. This isn't error handling — it's **design**:

| Missing piece | Self-glue action |
|---------------|-----------------|
| No clone path | `git clone --depth 1` |
| PLATO server down | Cache to `/tmp/twin-manifest-{hash}.json` |
| No test framework | Generate `test_hints` (not actual tests) |
| No entry points | Scan for `main`, `__main__`, `app.py` |
| No sub-rooms | Mirror directory structure as room names |

The maker never fails because a piece is missing. It makes the piece.

---

## Tuning Confidence

When you submit tiles, you can set a `confidence` field per tile. The scale:

| Confidence | Meaning | Use case |
|------------|---------|----------|
| `0.95` | Rich docstring + signature | Well-documented code |
| `0.90` | Has docstring | Normal functions |
| `0.75` | No docstring | Generated from raw code |
| `< 0.7` | Unverified | New tiles awaiting verification |

PLATO's consensus snap only merges tiles with confidence `>= 0.7`. If you're submitting raw code without docs, keep confidence at `0.75` until a human verifies the tiles.

---

## Multi-Language Repos

The maker detects the dominant language in a repo, but can handle multiple:

```
# If a repo has Python + Rust + TypeScript:
# → Main room: twin-python
# → Sub-rooms: twin-src_bin, twin-src_cli, etc.
```

Each language gets its own room. All rooms are tagged with the language and file path, so cross-language queries work.

---

## Refreshing a Twin

When the original repo updates, refresh the twin:

```bash
# Remove old clone and re-twin
rm -rf /tmp/ptwin-{hash}
python -m plato_twin_maker.plat_twin_maker \
  --repo https://github.com/user/repo \
  --plato http://localhost:8847
```

Tiles from the old twin that match new tiles (same `impl_hash`) are deduplicated by PLATO's gate. New functions get new tiles.

---

## The Agentic Dial

Each PLATO room has an `agentic_weight ∈ [0, 1]`:

- **0.0** — Pure program. No model involved. Tile reads only. Use when the logic is fully explicit and there's no ambiguity.
- **0.5** — Hybrid. The model fills what the program can't specify. Default for twin-maker tiles.
- **1.0** — Pure model. No explicit logic. Model reasons from scratch.

For most twin rooms, `0.5` is correct: the tile has enough structure to be constraint-satisfiable, but enough flexibility for the model to adapt to the query context.

---

## Verifying Twin Faithfulness

A twin is faithful if it produces the same output as the original code. Test it:

```bash
# Run the original repo's tests
cd /path/to/cloned/repo
python -m pytest -q

# Compare with what the twin says
# If tests pass, and tile answers match function behavior, twin is faithful
```

The twin-maker automatically runs tests if a build system is detected (via `--dry-run` skip, it won't run tests).

---

## Use Cases

### As a Codebase搜索引擎
Replace "grep the source" with "query the twin": instead of opening a file and reading a function, ask the room and get the docstring + signature + test hints in one shot.

### As an Onboarding Tool
When a new developer joins, they can query the twin room instead of reading all the source files. Tiles show what each function does, how to call it, and what tests to write.

### As a Refactoring Safety Net
Before refactoring, create a twin. After refactoring, query the twin to verify behavior matches. If tiles and code diverge, the twin needs refresh.

### As a Fleet Knowledge Layer
When Forgemaster compiles a new library, run the twin-maker. All functions become queryable by any agent in the fleet. No need to read the source — just ask the room.

---

## FAQ

**Q: Does the twin replace the source code?**
No. The twin is a PLATO overlay. The source is still the authority.

**Q: What happens if the source code changes?**
The twin becomes stale. Refresh it by re-running the maker.

**Q: Can I submit tiles from multiple repos to the same room?**
Yes. Use `--room-prefix` to control the room name. By default each repo gets its own room (`twin-{language}`).

**Q: How do I delete a twin?**
PLATO doesn't delete tiles — it compacts them. Tiles age out when the room exceeds its compaction threshold. For hard deletion, you'd need to modify the PLATO room server directly.

**Q: Can I use the twin-maker on a private repo?**
Yes, but you need `GITHUB_TOKEN` in your environment: `export GITHUB_TOKEN=ghp_...`

**Q: What's the minimum viable repo?**
A single `.py` file with one function. No tests, no docs, no build system. The maker will extract the function, create a tile, and submit it.