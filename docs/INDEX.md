# Plato-Twin-Maker — Documentation

```
docs/
├── QUICKSTART.md      ← Start here (5 min)
├── USER_GUIDE.md      ← How to use as a knowledge layer
├── DEVELOPER_GUIDE.md ← Extend, integrate, customize
└── INDEX.md           ← This file

tutorials/
├── TUTORIAL_1.md     ← Twin your first repo (10 min)
├── TUTORIAL_2.md     ← Build a fleet knowledge system (20 min)
└── TUTORIAL_3.md     ← Twin Forgemaster's constraint-theory-llvm

examples/
├── 01_simple_twin.py        ← Twin a repo, query the result
├── 02_api_usage.py          ← Custom TileCreator, programmatic query
└── 03_rust_fleet_integration.py ← Rust + constraint theory + fleet
```

## Reading Order

**New to plato-twin-maker:**
1. [QUICKSTART.md](./QUICKSTART.md) — get started in 5 minutes
2. [TUTORIAL_1.md](../tutorials/TUTORIAL_1.md) — twin your first repo
3. [USER_GUIDE.md](./USER_GUIDE.md) — understand the concepts

**Want to build with it:**
1. [DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md) — architecture and API
2. [examples/](../examples/) — runnable code for each integration pattern

**Want to go deeper:**
1. [TUTORIAL_2.md](../tutorials/TUTORIAL_2.md) — fleet knowledge system
2. [TUTORIAL_3.md](../tutorials/TUTORIAL_3.md) — Forgemaster's constraint-theory integration

## Quick Reference

```bash
# Install
pip install git+https://github.com/SuperInstance/plato-twin-maker

# Twin a repo (one-liner)
python -m plato_twin_maker.plat_twin_maker --repo https://github.com/user/repo

# Dry run (analyze only)
python -m plato_twin_maker.plat_twin_maker --repo /path/to/repo --dry-run --verbose

# Query PLATO
curl http://localhost:8847/room/twin-python | python3 -c "import json,sys; print(json.load(sys.stdin)['tile_count'], 'tiles')"
```