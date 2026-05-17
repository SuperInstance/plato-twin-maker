"""
plato-twin-maker — The hermit crab factory.

Self-gluing: if a required component doesn't exist, the maker creates it.
The twin produces the same output as the original — but now every logic
chain is explicit, optimizable, and self-documenting in PLATO tiles.

The Agentic Dial:
    Each room has a dial [0..1] controlling how much agentic vs programmatic
    behavior it exhibits. 0 = pure program, no model needed. 1 = pure model,
    no explicit logic. Between them = hybrid.

    The model at each tile-making node can be big or small, traded/mixed/
    matched to distill favorite elements. This is why a room's tile-making
    can be experimented with — finding the best "sound" by models that could
    never make those musical licks algorithmically.
"""

from .plat_twin_maker import (
    PlatoTwinMaker,
    RepoAnalyzer,
    TileCreator,
    RepoAnalysis,
    PlatoTwin,
    TileContent,
    ModuleInfo,
    SUPPORTED_LANGUAGES,
    main as run_plato_twin_maker,
)

__all__ = [
    'PlatoTwinMaker',
    'RepoAnalyzer',
    'TileCreator',
    'RepoAnalysis',
    'PlatoTwin',
    'TileContent',
    'ModuleInfo',
    'SUPPORTED_LANGUAGES',
    'run_plato_twin_maker',
]

__version__ = '0.1.0'