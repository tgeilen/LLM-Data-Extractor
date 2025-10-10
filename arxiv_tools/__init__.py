"""
ArXiv Module

This module contains all arXiv-related functionality including:
- Paper discovery and search
- LLM-based classification 
- PDF downloading
- Complete processing pipeline

Main classes:
- ArXivDiscovery: Primary paper discovery system
- ArXivClassifier: LLM-based paper classification
- Functions for downloading and processing papers
"""

# Import core functionality that doesn't require external dependencies
from .arxiv_discovery import ArXivDiscovery
from .arxiv_filter import ArXivClassifier
from .arxiv_downloader import download_arxiv_paper

# Don't import arxiv_processor by default since it has more dependencies
# Users can import it explicitly if needed: from arxiv_tools.arxiv_processor import process_paper_from_arxiv

__all__ = [
    'ArXivDiscovery',
    'ArXivClassifier', 
    'download_arxiv_paper'
]
