# Tutorial 1: Twin Your First Repository

*Time: 10 minutes. No prior experience with PLATO or twin-maker required.*

---

## What You'll Learn

- Install and run the twin-maker
- Create a PLATO-twin of a public GitHub repo
- Query the twin in PLATO
- Understand what a tile looks like

---

## Prerequisites

- Python 3.10 or later
- A running PLATO room server (we'll use the local default)
- Internet access (for cloning a public repo)

---

## Step 1: Install the Twin-Maker

```bash
pip install git+https://github.com/SuperInstance/plato-twin-maker
```

Verify it installed:

```bash
python -m plato_twin_maker.plat_twin_maker --help
```

You should see the usage message. If you get an error, check [TROUBLESHOOTING](#troubleshooting) below.

---

## Step 2: Verify PLATO is Running

```bash
curl http://localhost:8847/status
```

You should see `{"status":"active", ...}`. If not, start PLATO:

```bash
# If PLATO is not running, start it:
cd /tmp && python3 -m plato_room_server &
```

---

## Step 3: Choose a Repo to Twin

Start with something small and well-documented. Good candidates:
- A Python library with a few modules
- A CLI tool with clear function structure
- Any repo you personally use and know well

For this tutorial, we'll use `SuperInstance/plato-twin-maker` itself (it's already there and you're reading its docs).

---

## Step 4: Run the Twin-Maker

```bash
python -m plato_twin_maker.plat_twin_maker \
  --repo https://github.com/SuperInstance/plato-twin-maker \
  --plato http://localhost:8847
```

Expected output:
```
[ptwin] Starting twin creation for https://github.com/SuperInstance/plato-twin-maker
[ptwin] Cloning https://github.com/SuperInstance/plato-twin-maker
[ptwin] Twin created: 8 modules, 9 tiles
[ptwin] Room: twin-python
[ptwin] Manifest saved to /tmp/twin-manifest-abc123.json
```

This took about 30 seconds (clone + extract + submit).

---

## Step 5: Check Your Tiles in PLATO

```bash
curl http://localhost:8847/room/twin-python | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(f'Total tiles: {d[\"tile_count\"]}')
print()
for t in d['tiles'][:5]:
    print(f'Q: {t[\"question\"][:80]}')
    print(f'A: {t[\"answer\"][:100]}...')
    print(f'tags: {t.get(\"tags\",\"\")}')
    print()
"
```

You should see tiles for each module in the repo — functions, classes, and a root tile describing the whole repo.

---

## Step 6: Ask Your Twin a Question

Imagine you want to understand how the `PlatoTwinMaker` class works. Instead of reading the source file, you can now ask PLATO:

```bash
curl -s -X POST http://localhost:8847/submit \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "twin-python",
    "question": "How does PlatoTwinMaker.make() work?",
    "answer": "The make() method clones the repo, runs RepoAnalyzer, creates tiles via TileCreator, and submits to PLATO. It self-glues missing pieces automatically.",
    "tags": "python,PlatoTwinMaker,making",
    "confidence": 0.9
  }' | python3 -c "import json,sys; print(json.dumps(json.load(sys.stdin), indent=2))"
```

Now query the room for tiles about `make`:

```bash
curl http://localhost:8847/room/twin-python | python3 -c "
import json, sys
d = json.load(sys.stdin)
for t in d['tiles']:
    if 'make' in t['question'].lower() and 'PlatoTwinMaker' in t['question']:
        print(f'Q: {t[\"question\"]}')
        print(f'A: {t[\"answer\"][:200]}')
        print()
"
```

---

## What You Just Created

```
Original repo (GitHub)
      │
      ▼
plato-twin-maker (clone + extract + submit)
      │
      ▼
PLATO room: twin-python
      │
      ├── Tile: RepoAnalyzer (function)
      ├── Tile: TileCreator (class)
      ├── Tile: PlatoTwinMaker (class)
      │     └── Tile: make() (method)
      ├── Tile: ModuleInfo (dataclass)
      └── Tile: __root__ (repo overview)
```

Every function and class is now a tile. You can query them in PLATO without reading the source.

---

## Step 7: Clean Up (Optional)

If you want to remove the twin from your local PLATO, edit the room server directly (PLATO doesn't have a delete API — tiles age out through compaction).

To remove the cloned repo:
```bash
rm -rf /tmp/ptwin-*
```

---

## Troubleshooting

**`pip install` fails with "not found"`**
→ Make sure you have Python 3.10+. Run `python3 --version`.

**`curl http://localhost:8847/status` returns error`**
→ PLATO isn't running. Start it with `python3 -m plato_room_server` or check your PLATO installation.

**`HTTP Error 403: Forbidden` on submit`**
→ Your answer is too short. PLATO requires answers of at least 20 characters. The twin-maker should auto-handle this, but if it persists, check the PLATO gate settings.

**`Repository not found`**
→ The repo is private or doesn't exist. Double-check the URL.

**Clone takes too long**
→ The maker uses `git clone --depth 1` (shallow clone). If it's still slow, the repo is large or GitHub rate-limiting is in effect. Wait a few minutes and retry.

---

## Next Steps

| Continue learning | Link |
|-------------------|------|
| Understand tiles in depth | [User Guide](../USER_GUIDE.md) |
| Integrate with your code | [Developer Guide](../DEVELOPER_GUIDE.md) |
| More examples | [examples/](../examples/) |
| Build a knowledge system | [Tutorial 2](./TUTORIAL_2.md) |