"""
Tokenizer package for handling different LLM tokenizers and document chunking.

This package provides a unified interface for tokenizing text and chunking
documents for different LLM providers to fit within their context limits.
"""

# Import the main tokenizer factory interface
from tokenizer.tokenizer_factory import (
    get_tokenizer,
    process_file,
    compare_tokenizers,
    factory
)

# Import the base tokenizer for extendability
from tokenizer.base_tokenizer import BaseTokenizer

# Import specific implementations
try:
    from tokenizer.deepseek_tokenizer_impl import DeepSeekTokenizer
except ImportError:
    pass

try:
    from tokenizer.gemini_tokenizer_impl import GeminiTokenizer
except ImportError:
    pass

__all__ = [
    'get_tokenizer',
    'process_file',
    'compare_tokenizers',
    'factory',
    'BaseTokenizer',
] 