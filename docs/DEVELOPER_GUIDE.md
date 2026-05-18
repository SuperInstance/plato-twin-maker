# Plato-Twin-Maker — Developer Guide

*How to extend, integrate, and customize the twin-maker for your system.*

---

## Architecture Overview

```
plato_twin_maker/
├── plat_twin_maker.py    # Core classes
│   ├── RepoAnalyzer      # Parses any repo into ModuleInfo[]
│   ├── TileCreator       # Converts modules → TileContent[]
│   ├── PlatoTwinMaker    # Orchestrates the full pipeline
│   ├── RepoAnalysis      # Dataclass: full repo analysis result
│   ├── PlatoTwin         # Dataclass: complete twin manifest
│   └── TileContent       # Dataclass: a single PLATO tile
└── cli.py                # CLI entry point
```

The design is intentional: **each class is independently testable and replaceable**. Swap `RepoAnalyzer` for your own parser. Replace `TileCreator` with a custom tile format. The `PlatoTwinMaker` just orchestrates.

---

## The Core Classes

### RepoAnalyzer

Takes a path, returns a `RepoAnalysis`:

```python
from plato_twin_maker import RepoAnalyzer

analyzer = RepoAnalyzer("/path/to/repo")
analysis = analyzer.analyze()

print(analysis.language)       # 'python', 'rust', 'go', etc.
print(analysis.build_system)    # 'cargo', 'npm', 'pip', etc.
print(analysis.entry_points)   # ['src/main.py', 'src/cli.py']
print(len(analysis.modules))    # number of modules extracted
print(analysis.dependencies)    # {'pytest': 'pytest>=7.0', ...}
```

**Key methods you can override:**
- `_extract_python()` — override to add your own Python parser
- `_extract_rust()` — override for Rust-specific extraction
- `_detect_build_system()` — override to add new build systems

### TileCreator

Takes a `RepoAnalysis`, returns `TileContent[]`:

```python
from plato_twin_maker import TileCreator, RepoAnalyzer

analysis = RepoAnalyzer("/path/to/repo").analyze()
creator = TileCreator(analysis, room_prefix="my-twin")
tiles = creator.create_tiles()

print(len(tiles))  # one tile per module + root tile
print(tiles[0].question)  # "What is the purpose of the repo?"
print(tiles[0].impl_hash)  # SHA-256 of the content
```

**Key methods you can override:**
- `_question_for(mod)` — customize question format
- `_module_as_code(mod)` — customize tile answer format
- `subroom_names()` — customize how sub-rooms are named

### PlatoTwinMaker

The main factory:

```python
from plato_twin_maker import PlatoTwinMaker

maker = PlatoTwinMaker(
    repo_url="https://github.com/user/repo",
    plato_url="http://localhost:8847",
    room_prefix="my-twin",
)

twin = maker.make()  # clone + analyze + submit
print(f"Created twin with {twin.modules} modules, {len(twin.tiles)} tiles")
```

---

## Custom Tile Format

If you want different fields in your tiles, subclass `TileCreator`:

```python
from plato_twin_maker import TileCreator, RepoAnalysis, TileContent
from dataclasses import replace

class MyTileCreator(TileCreator):
    def _question_for(self, mod):
        # Custom question format
        return f"[{mod.language.upper()}] {mod.name} :: {mod.kind}"

    def _module_as_code(self, mod):
        # Richer answer with complexity score
        return f"""
Source: {mod.file_path}:{mod.line_start}-{mod.line_end}
Kind: {mod.kind}
Language: {mod.language}
Complexity: {mod.complexity:.1f}

Code:
{mod.signature}

Docstring:
{mod.docstring or '(none)'}

Test hints:
{', '.join(mod.test_hints)}
""".strip()
```

---

## Custom Repo Analyzer

If your language isn't supported yet, add it:

```python
from plato_twin_maker import RepoAnalyzer, ModuleInfo

class MyLanguageAnalyzer(RepoAnalyzer):
    def _extract_mylang(self, f: Path, content: str):
        """Extract functions from MyLanguage source files."""
        import re
        for match in re.finditer(r'def\s+(\w+)\s*\(', content):
            name = match.group(1)
            line = content[:match.start()].count('\n') + 1
            self.modules.append(ModuleInfo(
                name=name,
                kind='function',
                language='mylang',
                file_path=str(f.relative_to(self.path)),
                line_start=line,
                line_end=line + 10,
                docstring='',
                signature=f'def {name}(...)',
            ))

# Register the extension
analyzer = MyLanguageAnalyzer("/path/to/mylang/project")
analysis = analyzer.analyze()
```

---

## Integrating with PLATO

### Manual Tile Submission

If you want to control submission yourself:

```python
import json, urllib.request
from plato_twin_maker import PlatoTwinMaker

maker = PlatoTwinMaker(repo_url="...", plato_url="...")
twin = maker.make()

# Manual submission with custom headers
for tile in twin.tiles:
    payload = json.dumps({
        "domain": twin.room_name,
        "question": tile.question,
        "answer": tile.answer,
        "tags": ",".join(tile.tags),
        "confidence": tile.confidence,
    }).encode()

    req = urllib.request.Request(
        "http://localhost:8847/submit",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        print(r.status, r.read()[:100])
```

### Reading Tiles from PLATO

```python
import urllib.request, json

def get_tiles(room: str) -> list[dict]:
    with urllib.request.urlopen(f"http://localhost:8847/room/{room}") as r:
        return json.load(r)['tiles']

tiles = get_tiles("twin-python")
by_tag = {}
for tile in tiles:
    for tag in tile.get('tags', []):
        by_tag.setdefault(tag, []).append(tile)
```

---

## The Self-Glue Extension API

The maker creates missing pieces automatically. To customize self-glue behavior:

```python
from plato_twin_maker import PlatoTwinMaker

class CustomTwinMaker(PlatoTwinMaker):
    def _glue_tests(self, analysis):
        """Override: if no test framework, create basic test scaffold."""
        if not analysis.has_tests:
            # Create test files
            test_dir = Path(analysis.local_path) / "tests"
            test_dir.mkdir(exist_ok=True)
            (test_dir / "test_generated.py").write_text("""
import pytest
# Auto-generated test scaffold
# Run with: pytest tests/
""")
        return analysis
```

---

## Event Hooks

The maker has three hook points:

```python
class HookedTwinMaker(PlatoTwinMaker):
    def on_clone(self, path: Path):
        """Called after repo is cloned."""
        print(f"Cloned to {path}")

    def on_module_extracted(self, mod):
        """Called after each module is extracted."""
        print(f"  Module: {mod.name} ({mod.kind})")

    def on_tile_submitted(self, tile, response: dict):
        """Called after each tile is submitted to PLATO."""
        if response.get('status') == 'accepted':
            print(f"  ✓ {tile.source_module}")
        else:
            print(f"  ✗ {tile.source_module}: {response.get('reason')}")
```

---

## Running Tests

```bash
# All tests
python -m pytest tests/ -v

# Single test
python -m pytest tests/test_plat_twin_maker.py::TestRepoAnalyzer -v

# With coverage
python -m pytest tests/ --cov=plato_twin_maker --cov-report=html

# Fast mode (no clone needed)
python -m pytest tests/ -m "not slow"
```

The test suite uses a `sample_python_repo` fixture that creates a synthetic repo in a temp directory. No internet required for most tests.

---

## Benchmarking

```python
import time
from plato_twin_maker import RepoAnalyzer

# Time extraction on a real repo
start = time.time()
analyzer = RepoAnalyzer("/path/to/large/repo")
analysis = analyzer.analyze()
elapsed = time.time() - start

print(f"Extracted {len(analysis.modules)} modules in {elapsed:.2f}s")
print(f"Rate: {len(analysis.modules) / elapsed:.1f} modules/sec")
```

---

## Publishing to PyPI

```bash
cd /path/to/plato-twin-maker

# Build
python3 -m build

# Upload (needs PyPI token in ~/.pypirc)
python3 -m twine upload dist/*
```

---

## Adding Documentation

Documentation lives in `docs/`:
- `QUICKSTART.md` — 5-minute getting started
- `USER_GUIDE.md` — conceptual deep dive
- `DEVELOPER_GUIDE.md` — extension and integration
- `examples/` — runnable examples
- `tutorials/` — step-by-step walkthroughs

Each guide should be independently readable. Don't reference internal implementation details in user-facing docs.

---

## API Reference

### `plato_twin_maker.PlatoTwinMaker`

| Method | Returns | Description |
|--------|---------|-------------|
| `make()` | `PlatoTwin` | Full pipeline: clone → analyze → submit |
| `run_tests()` | `dict` | Run the original repo's tests |
| `_ensure_clone()` | `Path` | Clone or use existing |
| `_plato_available()` | `bool` | Check PLATO connectivity |
| `_submit_to_plato(twin)` | `None` | Submit all tiles |

### `plato_twin_maker.RepoAnalyzer`

| Method | Returns | Description |
|--------|---------|-------------|
| `analyze()` | `RepoAnalysis` | Full analysis |
| `_detect_language()` | `str` | Primary language |
| `_find_entry_points()` | `list[str]` | Entry point files |
| `_extract_modules()` | `None` | Populates `self.modules` |

### `plato_twin_maker.TileCreator`

| Method | Returns | Description |
|--------|---------|-------------|
| `create_tiles()` | `list[TileContent]` | All tiles |
| `subroom_names()` | `list[str]` | Sub-room names |

### Dataclasses

**`RepoAnalysis`**: `url`, `local_path`, `language`, `entry_points`, `modules`, `dependencies`, `build_system`, `test_framework`, `has_tests`, `license`, `readme_content`, `architecture_summary`

**`PlatoTwin`**: `repo_url`, `repo_hash`, `created_at`, `modules`, `tiles`, `room_name`, `rooms`

**`TileContent`**: `question`, `answer`, `tags`, `confidence`, `source_module`, `source_file`, `line_range`, `impl_hash`

**`ModuleInfo`**: `name`, `kind`, `language`, `file_path`, `line_start`, `line_end`, `docstring`, `signature`, `dependencies`, `complexity`, `test_hints`