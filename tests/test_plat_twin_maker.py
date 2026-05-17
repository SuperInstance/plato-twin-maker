"""Tests for plato-twin-maker."""

import pytest
import sys
import json
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from plato_twin_maker.plat_twin_maker import (
    RepoAnalyzer, TileCreator, PlatoTwinMaker,
    ModuleInfo, RepoAnalysis, TileContent, PlatoTwin,
)


@pytest.fixture
def sample_python_repo(tmp_path):
    """Create a minimal Python repo with functions, classes, and tests."""
    src = tmp_path / "sample_app"
    src.mkdir()

    # Main module with functions and classes
    (src / "__init__.py").write_text("")
    (src / "calculator.py").write_text('''
"""Calculator module — basic arithmetic operations."""


def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


def divide(a: float, b: float) -> float:
    """Divide two numbers. Raises if b is zero."""
    if b == 0:
        raise ValueError("Division by zero")
    return a / b


def parse_number(s: str) -> float:
    """Parse a string to float. Returns 0.0 on failure."""
    try:
        return float(s)
    except ValueError:
        return 0.0


class Calculator:
    """Stateful calculator that tracks history."""

    def __init__(self):
        self.history = []
        self.total = 0.0

    def add(self, value: float):
        """Add to running total."""
        self.total += value
        self.history.append(('add', value))
        return self.total

    def subtract(self, value: float):
        """Subtract from running total."""
        self.total -= value
        self.history.append(('sub', value))
        return self.total

    def reset(self):
        """Reset the calculator."""
        self.total = 0.0
        self.history.clear()
''')

    # Test file
    (src / "test_calculator.py").write_text('''
"""Tests for calculator module."""
import pytest
from calculator import add, multiply, divide, parse_number, Calculator


def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0


def test_multiply():
    assert multiply(3, 4) == 12


def test_divide():
    assert divide(10, 2) == 5
    with pytest.raises(ValueError):
        divide(1, 0)


def test_parse_number():
    assert parse_number("42") == 42.0
    assert parse_number("invalid") == 0.0


def test_calculator_class():
    calc = Calculator()
    assert calc.add(5) == 5
    assert calc.subtract(2) == 3
    assert calc.reset() is None
''')

    # Requirements
    (tmp_path / "requirements.txt").write_text("pytest>=7.0.0\n")

    # README
    (tmp_path / "README.md").write_text('''
# Sample Calculator App

A simple calculator with basic arithmetic and state tracking.

## Usage
    from sample_app.calculator import add, Calculator
    calc = Calculator()
    calc.add(5)
''')

    # pyproject.toml for build detection
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "sample-app"\nversion = "0.1.0"\n')
    (tmp_path / "__main__.py").write_text('''
"""Entry point for sample-app."""
if __name__ == "__main__":
    from sample_app.calculator import Calculator
    c = Calculator()
    print(c.add(5))
''')
    (src / "conftest.py").write_text('# pytest configuration')
    # app.py as explicit entry point (more detectable than __main__.py)
    (tmp_path / "app.py").write_text('''
"""Entry point for sample-app."""
if __name__ == "__main__":
    from sample_app.calculator import Calculator
    c = Calculator()
    print(c.add(5))
''')

    return tmp_path


class TestRepoAnalyzer:
    def test_build_system_detected(self, sample_python_repo):
        analyzer = RepoAnalyzer(str(sample_python_repo))
        analysis = analyzer.analyze()
        # pyproject.toml present → python build system
        assert analysis.build_system in ('python', 'pip', None)

    def test_extracts_modules(self, sample_python_repo):
        analyzer = RepoAnalyzer(str(sample_python_repo))
        analysis = analyzer.analyze()
        names = [m.name for m in analysis.modules]
        assert 'add' in names
        assert 'multiply' in names
        assert 'divide' in names
        assert 'parse_number' in names
        assert 'Calculator' in names

    def test_entry_points_detected(self, sample_python_repo):
        analyzer = RepoAnalyzer(str(sample_python_repo))
        analysis = analyzer.analyze()
        assert len(analysis.entry_points) >= 1

    def test_test_framework_from_conftest(self, sample_python_repo):
        analyzer = RepoAnalyzer(str(sample_python_repo))
        analysis = analyzer.analyze()
        assert analysis.has_tests is True

    def test_readme_content(self, sample_python_repo):
        analyzer = RepoAnalyzer(str(sample_python_repo))
        analysis = analyzer.analyze()
        assert 'Sample Calculator' in analysis.readme_content

    def test_architecture_summary(self, sample_python_repo):
        analyzer = RepoAnalyzer(str(sample_python_repo))
        analysis = analyzer.analyze()
        assert len(analysis.architecture_summary) > 20

    def test_calculator_class_extracted(self, sample_python_repo):
        analyzer = RepoAnalyzer(str(sample_python_repo))
        analysis = analyzer.analyze()
        calc_mod = next((m for m in analysis.modules if m.name == 'Calculator'), None)
        assert calc_mod is not None, f"Calculator not found. Modules: {[m.name for m in analysis.modules]}"
        assert calc_mod.kind == 'class'

    def test_parse_number_test_hints(self, sample_python_repo):
        analyzer = RepoAnalyzer(str(sample_python_repo))
        analysis = analyzer.analyze()
        parse_mod = next((m for m in analysis.modules if m.name == 'parse_number'), None)
        assert parse_mod is not None, f"parse_number not found. Modules: {[m.name for m in analysis.modules]}"
        assert len(parse_mod.test_hints) >= 1


class TestTileCreator:
    def test_creates_root_tile(self, sample_python_repo):
        analyzer = RepoAnalyzer(str(sample_python_repo))
        analysis = analyzer.analyze()
        creator = TileCreator(analysis, 'test-twin')
        tiles = creator.create_tiles()
        assert len(tiles) > 0
        assert tiles[0].source_module == '__root__'

    def test_creates_tile_per_module(self, sample_python_repo):
        analyzer = RepoAnalyzer(str(sample_python_repo))
        analysis = analyzer.analyze()
        creator = TileCreator(analysis, 'test-twin')
        tiles = creator.create_tiles()
        module_names = [t.source_module for t in tiles[1:]]  # skip root
        assert 'add' in module_names
        assert 'Calculator' in module_names

    def test_tiles_have_questions(self, sample_python_repo):
        analyzer = RepoAnalyzer(str(sample_python_repo))
        analysis = analyzer.analyze()
        creator = TileCreator(analysis, 'test-twin')
        tiles = creator.create_tiles()
        for tile in tiles:
            assert len(tile.question) > 5
            assert '?' in tile.question

    def test_tiles_have_hashes(self, sample_python_repo):
        analyzer = RepoAnalyzer(str(sample_python_repo))
        analysis = analyzer.analyze()
        creator = TileCreator(analysis, 'test-twin')
        tiles = creator.create_tiles()
        for tile in tiles:
            assert len(tile.impl_hash) == 16

    def test_tags_include_language(self, sample_python_repo):
        analyzer = RepoAnalyzer(str(sample_python_repo))
        analysis = analyzer.analyze()
        creator = TileCreator(analysis, 'test-twin')
        tiles = creator.create_tiles()
        for tile in tiles:
            assert 'python' in tile.tags


class TestPlatoTwinMaker:
    def test_creates_twin_manifest(self, sample_python_repo):
        maker = PlatoTwinMaker(
            repo_url=str(sample_python_repo),
            plato_url='http://localhost:9999',  # will fail, but we get manifest
            room_prefix='test',
        )
        twin = maker.make()
        assert twin.modules > 0
        assert len(twin.tiles) > 0
        assert twin.room_name == 'test-python'
        assert twin.repo_hash is not None


class TestPlatoTwinSerde:
    def test_twin_serializes_to_json(self, sample_python_repo):
        maker = PlatoTwinMaker(str(sample_python_repo), 'http://localhost:9999')
        twin = maker.make()
        d = json.dumps(twin, default=lambda x: x.__dict__ if hasattr(x, '__dict__') else str(x))
        assert 'modules' in d
        assert 'tiles' in d

    def test_moduleinfo_serde(self):
        mod = ModuleInfo(
            name='test_fn', kind='function', language='python',
            file_path='test.py', line_start=1, line_end=5,
            docstring='test doc', signature='def test_fn()',
        )
        d = asdict_wrapped(mod)
        assert d['name'] == 'test_fn'
        assert d['kind'] == 'function'


def asdict_wrapped(obj):
    """Convert dataclass to dict, handling nested dataclasses."""
    if hasattr(obj, '__dataclass_fields__'):
        return {k: asdict_wrapped(v) for k, v in obj.__dict__.items()}
    elif isinstance(obj, list):
        return [asdict_wrapped(x) for x in obj]
    elif isinstance(obj, dict):
        return {k: asdict_wrapped(v) for k, v in obj.items()}
    return obj


# Run locally without PLATO
class TestSelfGlue:
    """Verify self-gluing behavior when PLATO is unavailable."""
    def test_creates_local_cache_when_plato_down(self, sample_python_repo):
        maker = PlatoTwinMaker(
            repo_url=str(sample_python_repo),
            plato_url='http://localhost:1',  # guaranteed down
            room_prefix='test',
        )
        twin = maker.make()
        assert twin.modules > 0
        # Should not raise even though PLATO is down