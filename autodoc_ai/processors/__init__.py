"""
Processors module for zenco.
Contains modular processors for different code enhancement features.
"""

from .dead_code_processor import DeadCodeProcessor
from .docstring_processor import DocstringProcessor
from .type_hint_processor import TypeHintProcessor
from .magic_number_processor import MagicNumberProcessor

__all__ = [
    'DeadCodeProcessor',
    'DocstringProcessor',
    'TypeHintProcessor',
    'MagicNumberProcessor',
]
