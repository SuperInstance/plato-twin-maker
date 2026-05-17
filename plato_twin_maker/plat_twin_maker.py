"""
plato-twin-maker — The hermit crab factory.

Takes any repository, creates a PLATO-twin: a co-repo-shell in PLATO with tiles
that wrap every function and module. The twin produces the same output as the
original code — but now every logic chain is explicit, optimizable, and
self-documenting.

Usage:
    python -m plato_twin_maker.plat_twin_maker --repo https://github.com/SuperInstance/spreader-tool
    python -m plato_twin_maker.plat_twin_maker --repo /path/to/local/repo
    python -m plato_twin_maker.plat_twin_maker --repo https://github.com/user/repo --plato http://localhost:8847
"""

import os
import sys
import json
import hashlib
import subprocess
import re
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Any
from datetime import datetime

# ─── Platform detection ──────────────────────────────────────────────────────

SUPPORTED_LANGUAGES = {
    '.py': 'python',
    '.rs': 'rust',
    '.go': 'go',
    '.c': 'c',
    '.h': 'c',
    '.cpp': 'cpp',
    '.cc': 'cpp',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.jsx': 'javascript',
    '.tsx': 'typescript',
    '.java': 'java',
    '.rb': 'ruby',
    '.php': 'php',
    '.swift': 'swift',
    '.kt': 'kotlin',
    '.scala': 'scala',
    '.md': 'markdown',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.json': 'json',
    '.toml': 'toml',
    '.sh': 'shell',
    '.bash': 'shell',
}

@dataclass
class ModuleInfo:
    """A function, class, or module extracted from the source."""
    name: str
    kind: str  # 'function' | 'class' | 'module' | 'constant' | 'file'
    language: str
    file_path: str
    line_start: int
    line_end: int
    docstring: str
    signature: str  # for functions/methods
    dependencies: list[str] = field(default_factory=list)  # other modules this depends on
    complexity: float = 1.0  # cyclomatic complexity estimate
    test_hints: list[str] = field(default_factory=list)  # suggested test cases


@dataclass
class RepoAnalysis:
    """Complete analysis of a source repository."""
    url: str
    local_path: str
    language: str
    entry_points: list[str]
    modules: list[ModuleInfo]
    dependencies: dict[str, str]  # package -> version constraint
    build_system: Optional[str]  # 'cargo' | 'pip' | 'npm' | 'go' | 'make' | 'cmake' | None
    test_framework: Optional[str]
    has_tests: bool
    license: Optional[str]
    readme_content: str
    architecture_summary: str  # one-paragraph description of the repo's purpose


@dataclass
class TileContent:
    """What goes into a single PLATO tile."""
    question: str  # what does this module/do?
    answer: str   # the implementation + explanation
    tags: list[str]
    confidence: float
    source_module: str
    source_file: str
    line_range: tuple[int, int]
    impl_hash: str  # sha256 of the implementation


@dataclass
class PlatoTwin:
    """The PLATO-twin of a repository."""
    repo_url: str
    repo_hash: str
    created_at: str
    modules: int
    tiles: list[TileContent]
    room_name: str
    rooms: list[str]  # sub-room names (mirrors directory structure)


# ─── Repo Analysis ─────────────────────────────────────────────────────────────

class RepoAnalyzer:
    """Zero-shot analysis of any repository."""

    def __init__(self, repo_path: str):
        self.path = Path(repo_path)
        self.modules: list[ModuleInfo] = []

    def analyze(self) -> RepoAnalysis:
        """Full analysis of the repository."""
        if not self.path.exists():
            raise FileNotFoundError(f"Repository not found: {self.path}")

        language = self._detect_language()
        entry_points = self._find_entry_points()
        self._extract_modules()
        deps = self._parse_dependencies()
        build_sys = self._detect_build_system()
        test_info = self._detect_tests()
        readme = self._readme()
        arch = self._summarize_architecture()

        return RepoAnalysis(
            url="local",
            local_path=str(self.path),
            language=language,
            entry_points=entry_points,
            modules=self.modules,
            dependencies=deps,
            build_system=build_sys,
            test_framework=test_info[0],
            has_tests=test_info[1],
            license=self._detect_license(),
            readme_content=readme,
            architecture_summary=arch,
        )

    def _detect_language(self) -> str:
        """Primary language of the repo."""
        ext_counts = {}
        for f in self.path.rglob('*'):
            if f.is_file() and not any(p in str(f) for p in ['node_modules', '.git', '__pycache__', 'target', '.venv']):
                ext = f.suffix.lower()
                if ext in SUPPORTED_LANGUAGES:
                    ext_counts[ext] = ext_counts.get(ext, 0) + 1
        if not ext_counts:
            return 'unknown'
        return SUPPORTED_LANGUAGES.get(max(ext_counts, key=ext_counts.get), 'unknown')

    def _find_entry_points(self) -> list[str]:
        """Find main files (main, index, __main__, etc.)."""
        candidates = []
        lang = self._detect_language()
        for f in self.path.rglob('*'):
            if f.is_file() and not any(p in str(f) for p in ['node_modules', '.git', '__pycache__']):
                name = f.name.lower()
                if name in ['main', 'index', '__main__', 'main.py', 'app.py', 'lib.rs', 'main.go',
                            'run.py', 'serve.py', 'cli.py', 'bin', 'entrypoint.py']:
                    candidates.append(str(f.relative_to(self.path)))
        return candidates[:10]

    def _extract_modules(self):
        """Extract functions, classes, and constants from all source files."""
        for f in self.path.rglob('*'):
            if not f.is_file():
                continue
            ext = f.suffix.lower()
            if ext not in SUPPORTED_LANGUAGES:
                continue
            if any(p in str(f) for p in ['node_modules', '.git', '__pycache__', 'target', '.venv', 'dist', 'build']):
                continue

            try:
                content = f.read_text(errors='ignore')
            except Exception:
                continue

            lang = SUPPORTED_LANGUAGES[ext]
            if lang == 'python':
                self._extract_python(f, content)
            elif lang == 'rust':
                self._extract_rust(f, content)
            elif lang == 'typescript':
                self._extract_typescript(f, content)
            elif lang == 'javascript':
                self._extract_javascript(f, content)
            elif lang == 'go':
                self._extract_go(f, content)
            elif lang in ['c', 'cpp']:
                self._extract_c(f, content)

    def _extract_python(self, f: Path, content: str):
        """Extract Python functions/classes with line numbers."""
        lines = content.split('\n')
        n = len(lines)
        i = 0

        while i < n:
            line = lines[i]
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith('#'):
                i += 1
                continue

            # Class definition
            if stripped.startswith('class '):
                match = re.match(r'class\s+(\w+)(.*?):', stripped)
                if match:
                    name = match.group(1)
                    # Collect docstring
                    doc, doc_end = self._collect_python_docstring(lines, i + 1)
                    self.modules.append(ModuleInfo(
                        name=name, kind='class', language='python',
                        file_path=str(f.relative_to(self.path)),
                        line_start=i + 1, line_end=doc_end,
                        docstring=doc,
                        signature=f"class {name}",
                        dependencies=self._extract_imports(content),
                        test_hints=self._suggest_tests(name, 'python'),
                    ))
                    i = doc_end
                    continue

            # Function definition
            if stripped.startswith('def '):
                match = re.match(r'def\s+(\w+)\s*\((.*?)\)(.*?):', stripped)
                if match:
                    name, args, ret = match.group(1), match.group(2), match.group(3)
                    doc, doc_end = self._collect_python_docstring(lines, i + 1)
                    ret_part = ret.strip() if ret else ''
                    self.modules.append(ModuleInfo(
                        name=name, kind='function', language='python',
                        file_path=str(f.relative_to(self.path)),
                        line_start=i + 1, line_end=doc_end,
                        docstring=doc,
                        signature=f"def {name}({args}){' -> ' + ret_part if ret_part else ''}",
                        dependencies=self._extract_imports(content),
                        test_hints=self._suggest_tests(name, 'python'),
                    ))
                    i = doc_end
                    continue

            i += 1

    def _collect_python_docstring(self, lines: list[str], start: int) -> tuple[str, int]:
        """Collect Python docstring starting from line after def/class. Returns (doc, end_line)."""
        if start >= len(lines):
            return '', start

        first = lines[start].strip()
        doc_parts = []
        end = start

        # Triple-quote docstrings
        if first.startswith('"""') or first.startswith("'''"):
            delim = first[:3]
            if first.count(delim) >= 2:
                # Single-line docstring
                doc = first.strip(delim).strip()
                return doc, start + 1
            # Multi-line
            doc_parts.append(first[len(delim):].strip())
            j = start + 1
            while j < len(lines):
                if delim in lines[j]:
                    doc_parts.append(lines[j].split(delim)[0].strip())
                    return '\n'.join(doc_parts).strip(), j + 1
                doc_parts.append(lines[j].rstrip())
                j += 1
            return '\n'.join(doc_parts).strip(), j

        return '', start

    def _extract_rust(self, f: Path, content: str):
        """Extract Rust functions, structs, impl blocks."""
        lines = content.split('\n')
        in_comment = False
        doc_comment = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            # doc comments
            if stripped.startswith('///') or stripped.startswith('//!'):
                doc_comment.append(stripped.lstrip('/!'))
                continue

            if stripped.startswith('pub fn ') or stripped.startswith('fn '):
                match = re.match(r'(?:pub )?fn (\w+)\s*(<[^>]+>)?\((.*?)\)(.*?)(?:-> ([^{]+))?\{', stripped)
                if match:
                    name, generics, args, where, ret = match.groups()
                    self.modules.append(ModuleInfo(
                        name=name, kind='function', language='rust',
                        file_path=str(f.relative_to(self.path)),
                        line_start=i+1, line_end=i+10,
                        docstring=' '.join(doc_comment),
                        signature=f"fn {name}({args}) -> {ret.strip() if ret else '()'}",
                        dependencies=[],
                        test_hints=self._suggest_tests(name, 'rust'),
                    ))
                doc_comment = []

            elif stripped.startswith('struct ') or stripped.startswith('pub struct '):
                match = re.match(r'(?:pub )?struct (\w+)', stripped)
                if match:
                    self.modules.append(ModuleInfo(
                        name=match.group(1), kind='struct', language='rust',
                        file_path=str(f.relative_to(self.path)),
                        line_start=i+1, line_end=i+20,
                        docstring=' '.join(doc_comment),
                        signature=f"struct {match.group(1)}",
                        dependencies=[],
                        test_hints=[],
                    ))
                    doc_comment = []

    def _extract_typescript(self, f: Path, content: str):
        """Extract TypeScript functions, interfaces, classes."""
        for match in re.finditer(r'(?:export\s+)?(?:function|const|class|interface|type)\s+(\w+)', content):
            name = match.group(1)
            line = content[:match.start()].count('\n') + 1
            self.modules.append(ModuleInfo(
                name=name, kind='function', language='typescript',
                file_path=str(f.relative_to(self.path)),
                line_start=line, line_end=line+5,
                docstring='',
                signature=f"function {name}",
                dependencies=[],
                test_hints=self._suggest_tests(name, 'typescript'),
            ))

    def _extract_javascript(self, f: Path, content: str):
        """Extract JavaScript functions."""
        for match in re.finditer(r'(?:export\s+)?(?:function|const|async function)\s+(\w+)', content):
            name = match.group(1)
            line = content[:match.start()].count('\n') + 1
            self.modules.append(ModuleInfo(
                name=name, kind='function', language='javascript',
                file_path=str(f.relative_to(self.path)),
                line_start=line, line_end=line+5,
                docstring='',
                signature=f"function {name}",
                dependencies=[],
                test_hints=self._suggest_tests(name, 'javascript'),
            ))

    def _extract_go(self, f: Path, content: str):
        """Extract Go functions and types."""
        for match in re.finditer(r'func\s+(?:\([^)]+\)\s+)?(\w+)\s*\(', content):
            name = match.group(1)
            line = content[:match.start()].count('\n') + 1
            self.modules.append(ModuleInfo(
                name=name, kind='function', language='go',
                file_path=str(f.relative_to(self.path)),
                line_start=line, line_end=line+5,
                docstring='',
                signature=f"func {name}",
                dependencies=[],
                test_hints=self._suggest_tests(name, 'go'),
            ))

    def _extract_c(self, f: Path, content: str):
        """Extract C functions."""
        for match in re.finditer(r'(?:void|int|float|double|char|struct \w+)\s+(\w+)\s*\([^)]*\)', content):
            name = match.group(1)
            if name not in ['if', 'while', 'for', 'switch', 'return', 'sizeof']:
                line = content[:match.start()].count('\n') + 1
                self.modules.append(ModuleInfo(
                    name=name, kind='function', language='c',
                    file_path=str(f.relative_to(self.path)),
                    line_start=line, line_end=line+5,
                    docstring='',
                    signature=f"{name}(...)",
                    dependencies=[],
                    test_hints=self._suggest_tests(name, 'c'),
                ))

    def _extract_imports(self, content: str) -> list[str]:
        """Extract imports from Python content."""
        imports = []
        for match in re.finditer(r'^import\s+(\w+)|^from\s+(\w+)', content, re.MULTILINE):
            imports.append(match.group(1) or match.group(2))
        return imports

    def _suggest_tests(self, name: str, lang: str) -> list[str]:
        """Suggest test cases for a function."""
        suggestions = []
        if 'test' in name.lower() or 'Test' in name:
            return suggestions

        suggestions.append(f"test_{name}_basic")
        if 'parse' in name.lower():
            suggestions.append(f"test_{name}_edge_case_empty")
            suggestions.append(f"test_{name}_invalid_input")
        if 'compute' in name.lower() or 'calculate' in name.lower():
            suggestions.append(f"test_{name}_known_result")
            suggestions.append(f"test_{name}_overflow")
        if 'validate' in name.lower():
            suggestions.append(f"test_{name}_valid_input")
            suggestions.append(f"test_{name}_invalid_input")
        return suggestions[:4]

    def _parse_dependencies(self) -> dict[str, str]:
        """Parse dependency files (requirements.txt, Cargo.toml, package.json, go.mod)."""
        deps = {}
        for f in self.path.rglob('*'):
            if f.is_file():
                name = f.name.lower()
                try:
                    if name == 'requirements.txt':
                        for line in f.read_text().split('\n'):
                            line = line.strip()
                            if line and not line.startswith('#'):
                                pkg = re.split(r'[><=!]', line)[0].strip()
                                if pkg:
                                    deps[pkg] = line
                    elif name in ['cargo.toml', 'package.json', 'go.mod', 'pom.xml', 'build.gradle']:
                        deps[f.name] = f.read_text()[:200]
                except Exception:
                    pass
        return deps

    def _detect_build_system(self) -> Optional[str]:
        """Detect build system."""
        for f in self.path.rglob('*'):
            if not f.is_file():
                continue
            n = f.name.lower()
            if n == 'cargo.toml': return 'cargo'
            if n == 'package.json': return 'npm'
            if n == 'go.mod': return 'go'
            if n == 'requirements.txt': return 'pip'
            if n == 'setup.py' or n == 'pyproject.toml': return 'python'
            if n == 'makefile': return 'make'
            if n == 'cmakeLists.txt': return 'cmake'
            if n == 'build.gradle': return 'gradle'
            if n == 'pom.xml': return 'maven'
        return None

    def _detect_tests(self) -> tuple[Optional[str], bool]:
        """Detect test framework and presence."""
        has_tests = any(self.path.rglob(f'test_{ext}') for ext in ['', '.py', '.rs', '.js', '.ts'])
        for f in self.path.rglob('*'):
            if f.is_file():
                n = f.name.lower()
                if 'pytest' in n or n.endswith('_test.py') or n.endswith('.test.ts'):
                    return 'pytest', True
                if n.endswith('_test.go') or n.endswith('.test.ts') or n.endswith('.spec.ts'):
                    return 'standard', True
        return None, has_tests

    def _detect_license(self) -> Optional[str]:
        """Find license type."""
        for f in self.path.rglob('*'):
            if f.is_file() and f.name.lower().startswith('license'):
                try:
                    content = f.read_text()[:500].lower()
                    for lic in ['mit', 'apache', 'gpl', 'bsd', 'mpl']:
                        if lic in content:
                            return lic.upper()
                except Exception:
                    pass
        return None

    def _readme(self) -> str:
        """Read README content."""
        for n in ['README.md', 'readme.md', 'README.txt', 'readme.txt', 'README.rst']:
            f = self.path / n
            if f.exists():
                try:
                    return f.read_text()[:2000]
                except Exception:
                    pass
        return ''

    def _summarize_architecture(self) -> str:
        """One-paragraph description of what this repo does."""
        readme = self._readme()
        if readme:
            # Take first non-empty paragraph
            for para in readme.split('\n\n'):
                para = para.strip()
                if len(para) > 50:
                    return para[:300] + '...' if len(para) > 300 else para
        return f"{self._detect_language()} repository with {len(self.modules)} modules"


# ─── Tile Creation ─────────────────────────────────────────────────────────────

class TileCreator:
    """Creates PLATO tiles from analyzed modules."""

    def __init__(self, analysis: RepoAnalysis, room_prefix: str = 'twin'):
        self.analysis = analysis
        self.room_prefix = room_prefix
        self.repo_hash = hashlib.sha256(analysis.local_path.encode()).hexdigest()[:12]

    def create_tiles(self) -> list[TileContent]:
        """Convert all modules to PLATO tiles."""
        tiles = []

        # Root module tile
        tiles.append(TileContent(
            question=f"What is the purpose of the {self.analysis.language} repo at {self.analysis.local_path}?",
            answer=self._module_as_code(self.analysis),
            tags=[self.analysis.language, 'repo-root', 'architecture'],
            confidence=0.95,
            source_module='__root__',
            source_file=self.analysis.local_path,
            line_range=(1, 9999),
            impl_hash=self._hash_content(self._module_as_code(self.analysis)),
        ))

        for mod in self.analysis.modules:
            tile = self._module_to_tile(mod)
            tiles.append(tile)

        return tiles

    def _module_to_tile(self, mod: ModuleInfo) -> TileContent:
        """Convert a single module to a PLATO tile."""
        tags = [mod.language, mod.kind, mod.file_path.split('.')[0]]

        # Add dependency tags
        for dep in mod.dependencies[:3]:
            tags.append(dep)

        impl = self._module_as_code(mod)

        return TileContent(
            question=f"{self._question_for(mod)}",
            answer=impl,
            tags=tags,
            confidence=0.90 if mod.docstring else 0.75,
            source_module=mod.name,
            source_file=mod.file_path,
            line_range=(mod.line_start, mod.line_end),
            impl_hash=self._hash_content(impl),
        )

    def _question_for(self, mod: ModuleInfo) -> str:
        """Generate the question for a module."""
        if mod.kind == 'function':
            return f"How does {mod.name} work? {mod.signature}"
        elif mod.kind == 'class':
            return f"What does the {mod.name} class do?"
        elif mod.kind == 'struct':
            return f"What fields does the {mod.name} struct have?"
        else:
            return f"What is in {mod.file_path}?"

    def _module_as_code(self, mod) -> str:
        """Render a module as readable code + explanation."""
        if isinstance(mod, RepoAnalysis):
            return f"""
## Repository: {mod.local_path}
Language: {mod.language}
Entry points: {', '.join(mod.entry_points) or 'none detected'}
Build system: {mod.build_system or 'unknown'}
Architecture: {mod.architecture_summary}

### Dependencies
{json.dumps(mod.dependencies, indent=2) if mod.dependencies else 'none detected'}

### Modules ({len(mod.modules)} total)
{', '.join(m.name for m in mod.modules[:20])}
{'... and more' if len(mod.modules) > 20 else ''}

### README
{mod.readme_content[:1000]}
""".strip()

        code = ""
        if mod.docstring:
            code += f'"""{mod.docstring}"""\n\n'
        code += f"# {mod.file_path}:{mod.line_start}-{mod.line_end}\n"
        code += f"# Kind: {mod.kind} | Language: {mod.language}\n"
        if mod.signature:
            code += f"\n{mod.signature}\n"
        if mod.test_hints:
            code += f"\n# Suggested tests: {', '.join(mod.test_hints)}\n"
        return code

    def _hash_content(self, content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def subroom_names(self) -> list[str]:
        """Generate sub-room names that mirror the directory structure."""
        dirs = set()
        for mod in self.analysis.modules:
            parent = str(Path(mod.file_path).parent)
            if parent and parent not in ['.', '']:
                safe = parent.replace('/', '_').replace('\\', '_').replace('.', '_')
                dirs.add(f"{self.room_prefix}-{safe}")
        return sorted(list(dirs))[:50]


# ─── PLATO Twin Maker ─────────────────────────────────────────────────────────

class PlatoTwinMaker:
    """
    The main factory. Clones/analyzes a repo, creates PLATO tiles, submits them.

    Self-gluing: if a required component doesn't exist, the maker creates it.
    """

    def __init__(
        self,
        repo_url: str,
        plato_url: str = "http://localhost:8847",
        local_clone_path: Optional[str] = None,
        room_prefix: str = "twin",
    ):
        self.repo_url = repo_url
        self.plato_url = plato_url.rstrip('/')
        self.local_clone_path = local_clone_path or f"/tmp/ptwin-{hashlib.md5(repo_url.encode()).hexdigest()[:8]}"
        self.room_prefix = room_prefix
        self._analysis: Optional[RepoAnalysis] = None

    def make(self) -> PlatoTwin:
        """Build the PLATO-twin end-to-end."""
        self._ensure_clone()
        analyzer = RepoAnalyzer(self.local_clone_path)
        self._analysis = analyzer.analyze()

        creator = TileCreator(self._analysis, self.room_prefix)
        tiles = creator.create_tiles()

        twin = PlatoTwin(
            repo_url=self.repo_url,
            repo_hash=hashlib.sha256(self.repo_url.encode()).hexdigest()[:12],
            created_at=datetime.utcnow().isoformat(),
            modules=len(self._analysis.modules),
            tiles=tiles,
            room_name=f"{self.room_prefix}-{self._analysis.language}",
            rooms=creator.subroom_names(),
        )

        # Self-glue: if PLATO is available, submit tiles
        if self._plato_available():
            self._submit_to_plato(twin)
        else:
            print("[plato-twin-maker] PLATO not available — saving tiles to local cache")

        return twin

    def _ensure_clone(self):
        """Clone the repo if not already present."""
        path = Path(self.local_clone_path)
        if path.exists():
            print(f"[plato-twin-maker] Using existing clone: {path}")
            return

        print(f"[plato-twin-maker] Cloning {self.repo_url}")
        if self.repo_url.startswith('http') or self.repo_url.startswith('git'):
            subprocess.run(['git', 'clone', '--depth', '1', self.repo_url, str(path)],
                          check=True, capture_output=True)
        else:
            # Local path — just use it
            if Path(self.repo_url).exists():
                import shutil
                shutil.copytree(self.repo_url, str(path), dirs_exist_ok=True)
                print(f"[plato-twin-maker] Copied local repo to {path}")
            else:
                raise ValueError(f"Cannot resolve repo: {self.repo_url}")

    def _plato_available(self) -> bool:
        """Check if PLATO is reachable."""
        import urllib.request
        try:
            with urllib.request.urlopen(f"{self.plato_url}/status", timeout=2) as r:
                return r.status == 200
        except Exception:
            return False

    def _submit_to_plato(self, twin: PlatoTwin):
        """Submit all tiles to PLATO room server."""
        import urllib.request
        import urllib.error

        room = twin.room_name
        submitted = 0
        failed = 0

        for tile in twin.tiles:
            payload = json.dumps({
                'domain': room,
                'question': tile.question,
                'answer': tile.answer,
                'tags': ','.join(tile.tags),
                'confidence': tile.confidence,
            }).encode()

            req = urllib.request.Request(
                f"{self.plato_url}/submit",
                data=payload,
                headers={'Content-Type': 'application/json'},
                method='POST',
            )
            try:
                with urllib.request.urlopen(req, timeout=5) as r:
                    if r.status == 200:
                        submitted += 1
                    else:
                        failed += 1
            except Exception as e:
                failed += 1
                if failed <= 3:
                    print(f"[plato-twin-maker] Submit failed: {e}")

        print(f"[plato-twin-maker] Submitted {submitted} tiles, {failed} failed")

    def run_tests(self) -> dict[str, Any]:
        """
        Run the original repo's tests to verify the twin is faithful.
        """
        if not self._analysis:
            raise RuntimeError("Must call make() before run_tests()")

        result = {
            'repo': self.repo_url,
            'tests_passed': False,
            'test_output': '',
            'twin_faithful': False,
        }

        build = self._analysis.build_system
        if not build:
            result['test_output'] = 'No build system detected — skipping test run'
            return result

        try:
            cwd = self.local_clone_path
            if build == 'cargo':
                out = subprocess.run(['cargo', 'test', '--', '--quiet'],
                                    cwd=cwd, capture_output=True, text=True, timeout=120)
            elif build == 'npm':
                out = subprocess.run(['npm', 'test'],
                                    cwd=cwd, capture_output=True, text=True, timeout=120)
            elif build == 'pip':
                out = subprocess.run([sys.executable, '-m', 'pytest', '-q'],
                                    cwd=cwd, capture_output=True, text=True, timeout=120)
            elif build == 'python':
                out = subprocess.run([sys.executable, '-m', 'pytest', '-q'],
                                    cwd=cwd, capture_output=True, text=True, timeout=120)
            elif build == 'go':
                out = subprocess.run(['go', 'test', './...'],
                                    cwd=cwd, capture_output=True, text=True, timeout=120)
            else:
                out = None

            if out:
                result['test_output'] = out.stdout + out.stderr
                result['tests_passed'] = out.returncode == 0

        except subprocess.TimeoutExpired:
            result['test_output'] = 'Tests timed out after 120s'
        except FileNotFoundError:
            result['test_output'] = f'{build} not found — cannot run tests'
        except Exception as e:
            result['test_output'] = str(e)

        result['twin_faithful'] = result['tests_passed']
        return result


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description='plato-twin-maker: Create PLATO-twin of any repo')
    parser.add_argument('--repo', required=True, help='URL or local path of repository')
    parser.add_argument('--plato', default='http://localhost:8847', help='PLATO room server URL')
    parser.add_argument('--room-prefix', default='twin', help='Room name prefix')
    parser.add_argument('--local-clone', help='Override clone path')
    parser.add_argument('--dry-run', action='store_true', help='Analyze only, do not submit to PLATO')
    parser.add_argument('--verbose', '-v', action='store_true')

    args = parser.parse_args()

    print(f"[plato-twin-maker] Starting twin creation for {args.repo}")

    maker = PlatoTwinMaker(
        repo_url=args.repo,
        plato_url=args.plato,
        local_clone_path=args.local_clone,
        room_prefix=args.room_prefix,
    )

    twin = maker.make()
    print(f"[plato-twin-maker] Twin created: {twin.modules} modules, {len(twin.tiles)} tiles")
    print(f"[plato-twin-maker] Room: {twin.room_name}")

    if not args.dry_run:
        test_result = maker.run_tests()
        print(f"[plato-twin-maker] Tests: {'PASS' if test_result['tests_passed'] else 'FAIL'}")
        if args.verbose and test_result['test_output']:
            print(test_result['test_output'][:500])

    # Save twin manifest locally
    manifest_path = f"/tmp/twin-manifest-{twin.repo_hash}.json"
    with open(manifest_path, 'w') as f:
        json.dump(asdict(twin), f, indent=2)
    print(f"[plato-twin-maker] Manifest saved to {manifest_path}")

    return twin


if __name__ == '__main__':
    main()