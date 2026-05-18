#!/usr/bin/env python3
"""
Example 3: Twin a Rust repo and connect it to Forgemaster's constraint theory.

This shows how the twin-maker integrates with the rest of the fleet:
- Twin a Rust repo → tiles go to PLATO
- PLATO tiles feed into constraint-theory operations (H1 cohomology)
- The agent can reason about the code via tiles instead of reading source

Run: python examples/03_rust_fleet_integration.py
"""

import json, sys, os, tempfile, subprocess, shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plato_twin_maker import RepoAnalyzer, PlatoTwinMaker


# ── Step 1: Create a synthetic Rust repo ───────────────────────────────────

temp_dir = tempfile.mkdtemp(prefix="ptwin_example3_")
repo_dir = os.path.join(temp_dir, "geo")

os.makedirs(os.path.join(repo_dir, "src"))

with open(os.path.join(repo_dir, "Cargo.toml"), "w") as f:
    f.write('''
[package]
name = "geo"
version = "0.1.0"
edition = "2021"

[dependencies]
''')

with open(os.path.join(repo_dir, "src/lib.rs"), "w") as f:
    f.write('''
//! Geo — geometric computation library.

// ============================================================================
// Point
// ============================================================================

/// A 2D point with x,y coordinates.
#[derive(Debug, Clone, PartialEq)]
pub struct Point {
    pub x: f64,
    pub y: f64,
}

impl Point {
    /// Create a new point.
    pub fn new(x: f64, y: f64) -> Self {
        Point { x, y }
    }

    /// Euclidean distance to another point.
    pub fn distance_to(&self, other: &Point) -> f64 {
        let dx = self.x - other.x;
        let dy = self.y - other.y;
        (dx * dx + dy * dy).sqrt()
    }

    /// Midpoint between this point and another.
    pub fn midpoint(&self, other: &Point) -> Point {
        Point::new(
            (self.x + other.x) / 2.0,
            (self.y + other.y) / 2.0,
        )
    }

    /// Squared distance (avoids sqrt for comparisons).
    pub fn distance_sq(&self, other: &Point) -> f64 {
        let dx = self.x - other.x;
        let dy = self.y - other.y;
        dx * dx + dy * dy
    }
}

// ============================================================================
// Triangle
// ============================================================================

/// A triangle defined by three vertices.
#[derive(Debug, Clone)]
pub struct Triangle {
    pub a: Point,
    pub b: Point,
    pub c: Point,
}

impl Triangle {
    /// Create a new triangle from three points.
    pub fn new(a: Point, b: Point, c: Point) -> Self {
        Triangle { a, b, c }
    }

    /// Compute the area using the cross-product formula.
    pub fn area(&self) -> f64 {
        let ab_x = self.b.x - self.a.x;
        let ab_y = self.b.y - self.a.y;
        let ac_x = self.c.x - self.a.x;
        let ac_y = self.c.y - self.a.y;
        (ab_x * ac_y - ab_y * ac_x).abs() / 2.0
    }

    /// Perimeter of the triangle.
    pub fn perimeter(&self) -> f64 {
        self.a.distance_to(&self.b) + self.b.distance_to(&self.c) + self.c.distance_to(&self.a)
    }

    /// Centroid (average of vertices).
    pub fn centroid(&self) -> Point {
        Point::new(
            (self.a.x + self.b.x + self.c.x) / 3.0,
            (self.a.y + self.b.y + self.c.y) / 3.0,
        )
    }

    /// Check if a point is inside the triangle (barycentric method).
    pub fn contains_point(&self, p: &Point) -> bool {
        let v0_x = self.c.x - self.a.x;
        let v0_y = self.c.y - self.a.y;
        let v1_x = self.b.x - self.a.x;
        let v1_y = self.b.y - self.a.y;
        let v2_x = p.x - self.a.x;
        let v2_y = p.y - self.a.y;

        let dot00 = v0_x * v0_x + v0_y * v0_y;
        let dot01 = v0_x * v1_x + v0_y * v1_y;
        let dot02 = v0_x * v2_x + v0_y * v2_y;
        let dot11 = v1_x * v1_x + v1_y * v1_y;
        let dot12 = v1_x * v2_x + v1_y * v2_y;

        let inv_denom = 1.0 / (dot00 * dot11 - dot01 * dot01);
        let u = (dot11 * dot02 - dot01 * dot12) * inv_denom;
        let v = (dot00 * dot12 - dot01 * dot02) * inv_denom;

        u > 0.0 && v > 0.0 && (u + v) < 1.0
    }
}
''')

with open(os.path.join(repo_dir, "src/main.rs"), "w") as f:
    f.write('''
//! Geo CLI — command-line interface for the geo library.

fn main() {
    println!("Geo library — see lib.rs for API");
}
''')

print(f"[example 3] Created Rust geo repo at {repo_dir}")

# ── Step 2: Analyze the Rust repo ─────────────────────────────────────────

analyzer = RepoAnalyzer(repo_dir)
analysis = analyzer.analyze()

print(f"\n[example 3] Analysis:")
print(f"  Language: {analysis.language}")
print(f"  Build system: {analysis.build_system}")
print(f"  Modules ({len(analysis.modules)}):")
for m in analysis.modules:
    print(f"    {m.kind}: {m.name}")
    print(f"      signature: {m.signature}")
    print(f"      docstring: {m.docstring[:60] if m.docstring else '(none)'}")
    print(f"      lines: {m.line_start}-{m.line_end}")

# ── Step 3: Show how tiles map to constraint theory ────────────────────────

print("""
\n[example 3] How twin tiles feed into constraint theory:

  Tile: "What does Point.distance_to do?"
    ↓
  PLATO room: twin-rust
    ↓
  Forgemaster's constraint theory reads the tile:
    - Point is a node (constraint vertex)
    - distance_to is an edge (constraint)
    - The tile tells us: distance_to computes Euclidean distance
    ↓
  H1 cohomology can now reason about:
    - Point ↔ Point relationships as edges
    - Triangle ↔ Triangle relationships as 2-simplices
    - Emergence detection via H¹: β₁ = V - 2 when self-coordinating

  The tile is the explicit constraint. No need to read the Rust source.
""")

# ── Step 4: Submit to PLATO ───────────────────────────────────────────────

maker = PlatoTwinMaker(
    repo_url=repo_dir,
    plato_url="http://localhost:8847",
    room_prefix="geo",
)

try:
    twin = maker.make()
    print(f"[example 3] Twin created: {twin.modules} modules, {len(twin.tiles)} tiles")
    print(f"[example 3] Room: {twin.room_name}")

    # Show the rooms structure
    print(f"[example 3] Sub-rooms: {twin.rooms}")

    # Show what a tile looks like
    print(f"\n[example 3] Sample tile (Point.distance_to):")
    pt_tile = next((t for t in twin.tiles if 'distance_to' in t.question), None)
    if pt_tile:
        print(f"  Question: {pt_tile.question}")
        print(f"  Answer:\n{pt_tile.answer[:300]}")
        print(f"  Tags: {pt_tile.tags}")
        print(f"  Confidence: {pt_tile.confidence}")

except Exception as e:
    print(f"[example 3] PLATO submission: {e}")

# ── Step 5: Show fleet routing ─────────────────────────────────────────────

print("""
\n[example 3] Fleet routing for twin tiles:

  twin-geo room
      │
      ├── If agentic_weight = 0 (pure program):
      │     PLATO reads tile → returns answer → done. No model call.
      │
      ├── If agentic_weight = 0.5 (hybrid):
      │     PLATO reads tile → model fills context → response.
      │
      └── If agentic_weight = 1 (pure model):
            Tile is hint → model reasons from scratch.

  For constraint theory (Forgemaster):
    - agentic_weight = 0.3 (heavy on program, light on model)
    - The tile says "distance_to = Euclidean distance"
    - CT compiles this to the fastest available backend (AVX-512, CUDA...)
    - Fleet math tests verify correctness of the compilation
""")

# Cleanup
shutil.rmtree(temp_dir)
print("\n[example 3] Done — cleaned up temp repo")