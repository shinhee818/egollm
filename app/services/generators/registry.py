"""Simple registry for quiz generators.

Allows lookup of a generator implementation by quiz type string. This
keeps generator wiring in one place and makes `generate_multiple_quizzes`
implementation simple and extensible.
"""

from typing import Dict, Optional

# Generator classes are imported lazily to avoid circular imports at module
# import time in some contexts. The registry stores the generator class.
_REGISTRY: Dict[str, object] = {}


def register(quiz_type: str, generator_cls: object) -> None:
    """Register a generator class for a quiz_type (case-insensitive)."""
    _REGISTRY[quiz_type.lower()] = generator_cls


def get_generator(quiz_type: str) -> Optional[object]:
    """Return the generator class for quiz_type or None if not found."""
    if not quiz_type:
        return None
    return _REGISTRY.get(quiz_type.lower())


# Pre-register known generators
try:
    from app.services.generators.translate_generator import TranslateGenerator
    from app.services.generators.blank_generator import BlankGenerator
    from app.services.generators.sentence_arrange_generator import SentenceArrangeGenerator

    register("translate", TranslateGenerator)
    register("blank", BlankGenerator)
    register("sentencearrange", SentenceArrangeGenerator)
    register("sentence_arrange", SentenceArrangeGenerator)
    register("sentence-arrange", SentenceArrangeGenerator)
except Exception:
    # If imports fail during test-time discovery, registry can be filled later.
    pass
