# Plato-Twin-Maker — The Hermit Crab Factory

> *"The hermit crab finds a shell. The shell doesn't know it's a home. The crab makes it one."*

## What It Does

`plato-twin-maker` takes **any repository** — any language, any size, any structure — and creates a **PLATO-twin**: a co-repo-shell in PLATO where every function, class, and module is wrapped as an explicit tile. The twin produces the same functional output as the original code, but now every logic chain is:

- **Explicit** — no more "read the code and figure it out"
- **Optimizable** — each tile is a constraint point; swap the implementation without changing the question
- **Self-documenting** — tiles have questions, answers, tags, confidence scores, and test hints
- **PLATO-native** — tiles survive agent restarts, compactions, and crashes

## The Self-Gluing Principle

If a required component doesn't exist, the maker **creates it**:

- No clone path? → clones the repo
- PLATO server down? → caches tiles locally, syncs when up
- No test framework detected? → generates `test_hints` for manual tests
- Missing entry points? → finds `main`, `__main__`, `app.py`, `run.py`, `lib.rs`
- No sub-room structure? → mirrors directory layout as room names

## Quick Start

```bash
# Clone and run
git clone https://github.com/SuperInstance/plato-twin-maker
cd plato-twin-maker
pip install -e .

# Create a twin of any public repo
python -m plato_twin_maker.plat_twin_maker \
  --repo https://github.com/SuperInstance/spreader-tool

# Create a twin of a local repo
python -m plato_twin_maker.plat_twin_maker \
  --repo /path/to/your/project \
  --plato http://localhost:8847

# Dry run — analyze only, no PLATO submission
python -m plato_twin_maker.plat_twin_maker \
  --repo /path/to/project --dry-run --verbose
```

## Architecture

```
Repository (any language)
      │
      ▼
┌─────────────────┐
│  RepoAnalyzer   │  ← extracts functions, classes, modules, deps
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  TileCreator    │  ← converts each module to a TileContent
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ PlatoTwinMaker  │  ← self-glues missing pieces, submits to PLATO
└────────┬────────┘
         │
         ▼
    ┌────┴────┐
    │  PLATO  │  ← tiles posted to rooms named twin-{language}
    │  Tiles  │
    └─────────┘
```

## Output

For each module in the source repo, you get a tile with:

| Field | Description |
|-------|-------------|
| `question` | What does this module do? |
| `answer` | The implementation + explanation |
| `tags` | Language, kind, directory path |
| `confidence` | 0.75 (no docstring) to 0.95 (rich docs) |
| `impl_hash` | SHA-256 of the implementation |
| `test_hints` | Suggested test case names |

Plus a root tile that describes the repository architecture, entry points, dependencies, and build system.

## Supported Languages

Python, Rust, Go, TypeScript, JavaScript, C, C++, Java, Ruby, PHP, Swift, Kotlin, Scala, Shell, Markdown, YAML, JSON, TOML.

## The Agentic Dial

Each PLATO room has an `agentic_weight ∈ [0,1]` — the **synthesizer dial**:

- `0` = pure program: no model involvement, just tile reads
- `1` = pure model: no explicit logic, model reasons from scratch
- Between them: the model fills what the program can't specify; the program constrains what the model can do

The twin-maker generates tiles at `agentic_weight=0.5` by default — explicit enough to be constraint-satisfiable, flexible enough for the model to fill gaps. You can tune this per-room after creation.

## Self-Glue Events

When the maker encounters a missing piece, it creates one:

| Missing piece | Self-glue action |
|---------------|-----------------|
| Repository | Clones via `git clone --depth 1` |
| PLATO server | Caches tiles to `/tmp/twin-manifest-{hash}.json` |
| Test framework | Generates `test_hints` (not actual tests) |
| Entry points | Scans for `main`, `__main__`, `app.py`, `lib.rs`, etc. |
| Sub-room structure | Creates rooms named `twin-{dir}_{subdir}` |
| License | Scans for `LICENSE*`, `COPYING*` files |

## Forgemaster Integration

Forgemaster's constraint-theory work plugs directly into the twin-maker as the **optimization layer**:

- **Constraint-theory-llvm**: if the twin encounters LLVM bitcode, CT compiles it to the fastest available backend (AVX-512, CUDA, FPGA)
- **Holonomy-consensus**: tiles from twin-maker rooms feed into the ZHC consensus layer for fleet-wide coordination
- **CUDA consensus kernel**: for large fleets (>50 agents), twin tiles flow through the CUDA consensus kernel for sub-millisecond snap decisions
- **Edge memory**: for constrained hardware (Jetson, ESP32), the twin-maker can target the bump-allocated pool architecture

## Files

```
plato-twin-maker/
├── plato_twin_maker/
│   ├── __init__.py
│   └── plat_twin_maker.py   # Main factory (1000+ lines)
├── tests/
│   └── test_plat_twin_maker.py
└── README.md
```

## License

MIT