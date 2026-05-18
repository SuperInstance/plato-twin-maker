# Contributing to plato-twin-maker

Thank you for your interest in contributing! This project is the hermit crab factory — creates PLATO-twin of any repository.

## How to Add a New Language Extractor

The language detection system uses a `SUPPORTED_LANGUAGES` map in `plat_twin_maker.py` to map file extensions to language names. To add support for a new language:

### 1. Add the extension mapping

In `plat_twin_maker.py`, find the `SUPPORTED_LANGUAGES` dict (around line 28) and add your extension:

```python
SUPPORTED_LANGUAGES = {
    # ... existing entries ...
    '.your_ext': 'your_language',
}
```

### 2. Subclass RepoAnalyzer for custom extraction

If you need language-specific logic (e.g., custom AST parsing, function/class detection), subclass `RepoAnalyzer`:

```python
class YourLangAnalyzer(RepoAnalyzer):
    """Custom analyzer for YourLanguage."""
    
    def _find_modules(self) -> list[Module]:
        # Add your extraction logic here
        # Return list of Module objects with name, kind, language, file_path
        pass
    
    def _find_functions(self) -> list[Function]:
        # Add function detection specific to your language
        pass
```

### 3. Register your analyzer

In the `PLATO_TwinMaker` class `_create_analysis()` method, add your language to the language map:

```python
LANGUAGE_ANALYZERS = {
    'python': PythonAnalyzer,  # existing
    'rust': RustAnalyzer,     # existing
    'your_language': YourLangAnalyzer,  # add this
}
```

## How to Run Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=plato_twin_maker --cov-report=term-missing

# Run specific test file
python -m pytest tests/test_plat_twin_maker.py -v
```

## PR Process

1. **Fork** the repository and create a feature branch from `master`
2. **Write tests** for any new functionality
3. **Ensure tests pass**: `python -m pytest`
4. **Update docs** if adding new features
5. **Submit a PR** with a clear description of changes
6. **Respond to review** feedback promptly

## Code Style

- **Python**: Follow PEP 8; use type hints where possible
- **Naming**: Use `snake_case` for functions/variables, `PascalCase` for classes
- **Docstrings**: Use triple-quoted strings for public APIs
- **Types**: Add `# type: ignore` only when absolutely necessary
- **Line length**: Soft limit 100 characters
- **No dead code**: Remove commented-out blocks before submitting

## Getting Help

- Open an issue for bugs or feature requests
- Join the SuperInstance fleet discussions