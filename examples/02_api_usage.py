#!/usr/bin/env python3
"""
Example 2: Use the Python API programmatically — custom tile format
and programmatic query of the PLATO-twin.

Run: python examples/02_api_usage.py
"""

import json, sys, os, tempfile

# Add the package to the path (for development)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plato_twin_maker import (
    RepoAnalyzer, TileCreator, PlatoTwinMaker,
    RepoAnalysis, TileContent, ModuleInfo,
)


# ── Step 1: Create a synthetic repo ────────────────────────────────────────

temp_dir = tempfile.mkdtemp(prefix="ptwin_example2_")
repo_dir = os.path.join(temp_dir, "shapes")

os.makedirs(repo_dir)

with open(os.path.join(repo_dir, "shapes.py"), "w") as f:
    f.write('''
"""Shapes — geometric primitives."""


class Point:
    """A point in 2D space."""

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def distance_to(self, other: "Point") -> float:
        """Euclidean distance to another point."""
        dx = self.x - other.x
        dy = self.y - other.y
        return (dx * dx + dy * dy) ** 0.5

    def __repr__(self):
        return f"Point({self.x}, {self.y})"


class Circle:
    """A circle with center and radius."""

    def __init__(self, center: Point, radius: float):
        self.center = center
        self.radius = radius

    def area(self) -> float:
        """Area of the circle (πr²)."""
        return 3.14159 * self.radius * self.radius

    def circumference(self) -> float:
        """Circumference (2πr)."""
        return 2 * 3.14159 * self.radius

    def contains_point(self, point: Point) -> bool:
        """Check if a point is inside the circle."""
        return self.center.distance_to(point) <= self.radius


class Rectangle:
    """An axis-aligned rectangle."""

    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height

    def area(self) -> float:
        """Area of the rectangle."""
        return self.width * self.height

    def perimeter(self) -> float:
        """Perimeter of the rectangle."""
        return 2 * (self.width + self.height)
''')

with open(os.path.join(repo_dir, "pyproject.toml"), "w") as f:
    f.write('[project]\nname = "shapes"\nversion = "0.1.0"\n')

print(f"[example 2] Created shapes repo at {repo_dir}")

# ── Step 2: Use RepoAnalyzer directly ─────────────────────────────────────

analyzer = RepoAnalyzer(repo_dir)
analysis = analyzer.analyze()

print(f"\n[example 2] Analysis:")
print(f"  Language: {analysis.language}")
print(f"  Build system: {analysis.build_system}")
print(f"  Entry points: {analysis.entry_points}")
print(f"  Modules ({len(analysis.modules)}):")
for m in analysis.modules:
    print(f"    {m.kind}: {m.name} — {m.file_path}:{m.line_start}")
print(f"  Has tests: {analysis.has_tests}")
print(f"  Architecture: {analysis.architecture_summary[:80]}")

# ── Step 3: Customize TileCreator for richer format ─────────────────────────

class RichTileCreator(TileCreator):
    """Custom tile creator with richer metadata."""

    def _question_for(self, mod):
        if mod.kind == 'class':
            return f"What does the {mod.name} class do? What attributes does it have?"
        elif mod.kind == 'function':
            return f"How does the {mod.name} function work? What is its signature?"
        else:
            return f"What is in {mod.name}?"

    def _module_as_code(self, mod):
        # Handle both RepoAnalysis (root tile) and ModuleInfo (module tiles)
        if hasattr(mod, 'file_path'):
            # It's a ModuleInfo
            lines = [
                f"// File: {mod.file_path}:{mod.line_start}-{mod.line_end}",
                f"// Kind: {mod.kind}",
                f"// Language: {mod.language}",
                f"// Complexity: {mod.complexity:.1f}",
                "",
                f"Signature: {mod.signature}" if mod.signature else "",
                "",
            ]
            if mod.docstring:
                lines.append(f"Docstring: {mod.docstring}")
                lines.append("")
            if mod.dependencies:
                lines.append(f"Dependencies: {', '.join(mod.dependencies)}")
                lines.append("")
            if mod.test_hints:
                lines.append("Suggested tests:")
                for hint in mod.test_hints:
                    lines.append(f"  - {hint}")
        else:
            # It's a RepoAnalysis (root tile)
            lines = [
                f"// Repository: {mod.local_path}",
                f"// Language: {mod.language}",
                f"// Build: {mod.build_system or 'unknown'}",
                f"// Modules: {len(mod.modules)}",
                "",
                f"Architecture: {mod.architecture_summary[:200]}",
                "",
                f"Entry points: {', '.join(mod.entry_points) or 'none detected'}",
            ]
        return '\n'.join(lines).strip()

creator = RichTileCreator(analysis, room_prefix="shapes")
tiles = creator.create_tiles()

print(f"\n[example 2] Created {len(tiles)} tiles with RichTileCreator")
for tile in tiles:
    print(f"  Q: {tile.question[:60]}...")
    print(f"    tags: {tile.tags}")
    print(f"    confidence: {tile.confidence}")
    print(f"    hash: {tile.impl_hash}")
    print()

# ── Step 4: Submit to PLATO ──────────────────────────────────────────────────

maker = PlatoTwinMaker(
    repo_url=repo_dir,
    plato_url="http://localhost:8847",
    room_prefix="shapes",
)

try:
    twin = maker.make()
    print(f"[example 2] Twin created: {twin.modules} modules, {len(twin.tiles)} tiles")
    print(f"[example 2] Room: {twin.room_name}")
except Exception as e:
    print(f"[example 2] PLATO submission skipped: {e}")

# ── Step 5: Query the twin programmatically ──────────────────────────────────

def find_tiles(query: str, analysis: RepoAnalysis):
    """Find modules matching a query string."""
    q_words = set(query.lower().split())
    matches = []
    for mod in analysis.modules:
        score = len(q_words & set(mod.name.lower().split()))
        if score > 0:
            matches.append((score, mod.name, mod))
    return [m for _, _, m in sorted(matches, key=lambda x: x[0], reverse=True)]

print("\n[example 2] Query: 'Circle area'")
matches = find_tiles("Circle area", analysis)
for m in matches:
    print(f"  {m.name} ({m.kind})")

print("\n[example 2] Query: 'distance'")
matches = find_tiles("distance", analysis)
for m in matches:
    print(f"  {m.name} ({m.kind}): {m.signature}")

# Cleanup
import shutil
shutil.rmtree(temp_dir)
print("\n[example 2] Done — cleaned up temp repo")