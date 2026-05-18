# Tutorial 2: Build a Fleet Knowledge System

*Time: 20 minutes. You should have completed [Tutorial 1](./TUTORIAL_1.md) first.*

---

## What You'll Learn

- Run the twin-maker on multiple repos and aggregate tiles into one room
- Build a fleet-wide knowledge layer
- Query the aggregated knowledge system
- Connect tiles to Forgemaster's constraint theory

---

## The Scenario

You have three repos in your fleet:
- `mymath` — arithmetic library (Python)
- `shapes` — geometric primitives (Python)
- `geo` — geographic computations (Rust)

You want a single knowledge room (`fleet-knowledge`) where any agent can ask questions and get answers from any of the three repos — without knowing which repo the answer came from.

---

## Step 1: Create a Synthetic Fleet

Create three synthetic repos locally:

```bash
mkdir -p /tmp/my-fleet/{mymath,shapes,geo}

# mymath
cat > /tmp/my-fleet/mymath/math.py << 'EOF'
"""MyMath — arithmetic operations."""

def add(a, b): return a + b
def multiply(a, b): return a * b
def power(base, exp): return base ** exp
EOF

# shapes
cat > /tmp/my-fleet/shapes/shapes.py << 'EOF'
"""Shapes — geometric primitives."""

class Circle:
    def __init__(self, radius): self.radius = radius
    def area(self): return 3.14159 * self.radius ** 2

class Rectangle:
    def __init__(self, w, h): self.w, self.h = w, h
    def area(self): return self.w * self.h
EOF

# geo
mkdir -p /tmp/my-fleet/geo/src
cat > /tmp/my-fleet/geo/Cargo.toml << 'EOF'
[package]
name = "geo"
version = "0.1.0"
edition = "2021"
EOF

cat > /tmp/my-fleet/geo/src/lib.rs << 'EOF'
//! Geo — geographic computations.

pub fn haversine(lat1: f64, lon1: f64, lat2: f64, lon2: f64) -> f64 {
    // Great-circle distance between two points on Earth
    let r = 6371.0; // Earth radius in km
    let dlat = (lat2 - lat1).to_radians();
    let dlon = (lon2 - lon1).to_radians();
    let a = (dlat/2.0).sin().powi(2)
          + lat1.to_radians().cos() * lat2.to_radians().cos() * (dlon/2.0).sin().powi(2);
    let c = 2.0 * a.sqrt().asin();
    r * c
}
EOF
```

---

## Step 2: Twin Each Repo to the Same Room

Run the twin-maker on each repo, but use the same room (`fleet-knowledge`) for all three:

```bash
for repo in "mymath" "shapes"; do
    python -m plato_twin_maker.plat_twin_maker \
        --repo /tmp/my-fleet/$repo \
        --plato http://localhost:8847 \
        --room-prefix fleet-$repo \
        --dry-run
done

# Rust needs a different prefix since it's a different language
python -m plato_twin_maker.plat_twin_maker \
    --repo /tmp/my-fleet/geo \
    --plato http://localhost:8847 \
    --room-prefix fleet-geo
```

Wait for all three to complete.

---

## Step 3: Query the Fleet Knowledge

```python
import urllib.request, json

def query_fleet(question: str):
    """Query across all fleet rooms."""
    rooms = ['fleet-mymath', 'fleet-shapes', 'fleet-geo']
    all_tiles = []

    for room in rooms:
        try:
            with urllib.request.urlopen(f"http://localhost:8847/room/{room}") as r:
                data = json.load(r)
                all_tiles.extend([(room, t) for t in data.get('tiles', [])])
        except Exception:
            pass

    # Score tiles by tag overlap with question
    q_words = set(question.lower().split())
    scored = []
    for room, tile in all_tiles:
        tile_words = set(','.join(tile.get('tags', [])).split())
        score = len(q_words & tile_words)
        if score > 0:
            scored.append((score, room, tile))

    scored.sort(reverse=True)
    return scored[:5]

# Example queries
print("Query: 'area of circle'")
for score, room, tile in query_fleet("area of circle"):
    print(f"  [{score}] {room}: {tile['question']}")

print("\nQuery: 'distance'")
for score, room, tile in query_fleet("distance"):
    print(f"  [{score}] {room}: {tile['question']}")
```

---

## Step 4: Connect to Constraint Theory

Forgemaster's constraint theory reads tiles and compiles them. Here's how the fleet knowledge connects:

```
Fleet Knowledge Room
      │
      ├── Tile: add() [from mymath]
      │     → CT: addition is a constraint edge
      │
      ├── Tile: Circle.area() [from shapes]
      │     → CT: area computation as constraint
      │
      └── Tile: haversine() [from geo]
            → CT: geographic distance as constraint edge

H¹ Cohomology:
  V = number of distinct concepts (Point, Circle, distance, area...)
  E = number of relationships between concepts
  β₁ = V - E + 1

  If β₁ > 0 → emergent structure detected
  If β₁ = 0 → self-coordinating (stable fleet)
  If β₁ < 0 → over-constrained (conflicts)
```

---

## Step 5: Run the Full Pipeline End-to-End

```bash
#!/bin/bash
# twin-fleet.sh — twin all repos and aggregate knowledge

PLATO_URL="http://localhost:8847"
FLEET_DIR="/tmp/my-fleet"

for repo in mymath shapes geo; do
    echo "Twinning $repo..."
    python -m plato_twin_maker.plat_twin_maker \
        --repo $FLEET_DIR/$repo \
        --plato $PLATO_URL \
        --room-prefix fleet-$repo
    echo "Done: fleet-$repo"
done

echo ""
echo "Fleet twin complete!"
echo "Query with: curl http://localhost:8847/room/fleet-mymath"
```

---

## What You've Built

```
/tmp/my-fleet/
   ├── mymath/      ── twin-maker ──► fleet-mymath room
   │                                   └── Tiles: add, multiply, power
   ├── shapes/     ── twin-maker ──► fleet-shapes room
   │                                   └── Tiles: Circle, Rectangle
   └── geo/        ── twin-maker ──► fleet-geo room
                                       └── Tiles: haversine

Any agent can query all three rooms with one question:
  "What computes area?" → Circle.area(), Rectangle.area()
  "What computes distance?" → haversine()
```

---

## Troubleshooting

**Tiles from different repos look the same in the room**
→ Each repo gets its own room. Query multiple rooms or use the `tags` field to distinguish.

**Can't find a tile for a function**
→ The function might be nested or use non-standard syntax. Check the manifest at `/tmp/twin-manifest-{hash}.json` to see what was extracted.

**PLATO returns 403 on submit**
→ The answer is too short. The twin-maker auto-expands answers, but if it fails, increase the minimum answer length in your tile payload.

---

## Next Steps

| Goal | Link |
|------|------|
| Extend with custom language support | [Developer Guide](../DEVELOPER_GUIDE.md) |
| See Rust + fleet integration | [Example 3](../examples/03_rust_fleet_integration.py) |
| Build a twin of Forgemaster's constraint-theory-llvm | [Tutorial 3](./TUTORIAL_3.md) |