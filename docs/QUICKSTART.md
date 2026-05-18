# Plato-Twin-Maker Quickstart

*5 minutes to your first PLATO-twin.*

---

## What You Need

- Python 3.10+
- Access to a PLATO room server (default: `http://localhost:8847`)
- A public GitHub repo (or a local directory)

```bash
pip install git+https://github.com/SuperInstance/plato-twin-maker
```

---

## 1. Twin a Public GitHub Repo (60 seconds)

```bash
python -m plato_twin_maker.plat_twin_maker \
  --repo https://github.com/user/repo \
  --plato http://localhost:8847
```

That's it. The maker will:
1. Clone the repo (`git clone --depth 1`)
2. Extract every function, class, and module
3. Create a PLATO tile for each one
4. Post all tiles to a room named `twin-{language}`
5. Print a summary

Example output:
```
[ptwin] Starting twin creation for https://github.com/user/mymath
[ptwin] Cloning https://github.com/user/mymath
[ptwin] Twin created: 12 modules, 13 tiles
[ptwin] Room: twin-python
[ptwin] Manifest saved to /tmp/twin-manifest-a3f2b1.json
```

---

## 2. Twin a Local Directory (30 seconds)

```bash
python -m plato_twin_maker.plat_twin_maker \
  --repo /path/to/your/project \
  --plato http://localhost:8847
```

No internet needed. Works with any local codebase.

---

## 3. Dry Run — Analyze Without Submitting (10 seconds)

```bash
python -m plato_twin_maker.plat_twin_maker \
  --repo https://github.com/user/repo \
  --dry-run --verbose
```

Shows you what would be extracted — modules, languages, entry points, dependencies — without touching PLATO.

---

## 4. Check Your Tiles in PLATO

After the twin is created, query the room:

```bash
curl http://localhost:8847/room/twin-python | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(f'Total tiles: {d[\"tile_count\"]}')
for t in d['tiles'][:3]:
    print(f'  Q: {t[\"question\"][:80]}')
    print(f'    A: {t[\"answer\"][:100]}...')
    print()
"
```

---

## 5. What's a Tile?

A tile is a question-answer pair with metadata:

| Field | Example |
|-------|---------|
| `question` | "How does `add` work?" |
| `answer` | The function's docstring + signature + test hints |
| `tags` | `python`, `function`, `calculator` |
| `confidence` | `0.95` (with docstring) or `0.75` (without) |
| `impl_hash` | `a3f2b1c9d8e7f012` — SHA-256 of the implementation |

When you ask a question in the same room, PLATO finds matching tiles first. Same answer. Zero tokens.

---

## 6. Next Steps

| Want to... | Read |
|------------|------|
| Understand how it works in depth | [USER_GUIDE.md](USER_GUIDE.md) |
| Extend or integrate it | [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) |
| See real examples | [examples/](examples/) |
| Follow step-by-step tutorials | [tutorials/](tutorials/) |

---

## Troubleshooting

**`HTTP Error 403: Forbidden`**
→ PLATO is rejecting tiles. Usually `answer` is too short (under 20 chars). The maker should auto-fix this, but if it persists, check your PLATO gate settings.

**`Repository not found`**
→ The repo is private. Twin-maker doesn't clone private repos without a GitHub token in your environment.

**`No build system detected`**
→ The repo has no `package.json`, `Cargo.toml`, `requirements.txt`, etc. That's fine — the maker will still extract modules, just without running tests afterward.

**PLATO server unavailable**
→ Tiles are cached to `/tmp/twin-manifest-{hash}.json`. Submit them later with the same `--plato` flag pointing to a live server.