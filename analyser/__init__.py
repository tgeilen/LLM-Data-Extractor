"""
Scientific publication analyzer package.

This package provides tools for analyzing scientific publications 
using various LLM APIs to extract structured metadata.
"""

from analyser.base_analyser import BaseAnalyser

# Import analyzers with fallback
try:
    from analyser.deepseek_analyser import DeepSeekAnalyser
    _deepseek_available = True
except ImportError:
    _deepseek_available = False

try:
    from analyser.gemini_analyser import GeminiAnalyser
    _gemini_available = True
except ImportError:
    _gemini_available = False

# Build __all__ dynamically based on what's available
__all__ = ['BaseAnalyser']
if _deepseek_available:
    __all__.append('DeepSeekAnalyser')
if _gemini_available:
    __all__.append('GeminiAnalyser') 