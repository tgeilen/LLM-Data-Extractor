#!/usr/bin/env python3
"""
Improved ArXiv Paper Discovery Module

This module provides functionality to search arXiv for papers matching specific criteria
with better alignment to the arXiv web interface behavior and proper API usage.

Key improvements:
1. Proper search query construction following arXiv API documentation
2. Better pagination handling 
3. Simplified search modes that actually match web interface behavior
4. Improved rate limiting and error handling
5. More accurate result filtering
"""

import os
import time
import json
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Iterator
import re

# Import existing arXiv functionality
import arxiv

# Load environment variables if .env file exists
if os.path.exists('.env'):
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # dotenv not installed, continue without it

class ArXivDiscovery:
    """
    Improved ArXiv discovery system that better matches web interface behavior.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the discovery module with configuration.
        
        Args:
            config: Configuration dictionary with search parameters
        """
        self.config = config or self._get_default_config()
        self.search_results = []
        
        # Configure arXiv client with proper rate limiting
        self.client = arxiv.Client(
            page_size=100,  # Match typical web interface page size
            delay_seconds=3.0,  # Recommended 3-second delay
            num_retries=3
        )
    
    def _get_default_config(self) -> Dict:
        """Get default configuration for paper discovery."""
        return {
            'search_terms': ['robotics AND "foundation model"', 'robotics AND "foundational model"'],
            'categories': [],  # Empty means search all categories
            'max_papers_per_search': 0,  # 0 means get all available
            'date_range_months': 0,  # 0 means search all dates
            'search_mode': 'balanced',  # New default mode
            'sort_by': 'relevance',  # Default sort like web interface
            'rate_limit_delay': 3.0,  # Respect arXiv guidelines
        }
    
    def build_search_query(self, search_term: str, categories: List[str] = None) -> str:
        """
        Build proper arXiv API search query following documentation guidelines.
        
        Args:
            search_term: The user's search term
            categories: Optional list of categories to filter by
            
        Returns:
            Properly formatted search query
        """
        # Clean up the search term
        query = search_term.strip()
        
        # Apply search mode transformations
        mode = self.config.get('search_mode', 'balanced')
        query = self._apply_search_mode(query, mode)
        
        # Add category constraints if specified
        if categories:
            category_query = ' OR '.join([f'cat:{cat}' for cat in categories])
            query = f"({query}) AND ({category_query})"
        
        # Add date constraints if specified
        date_range_months = self.config.get('date_range_months', 0)
        if date_range_months > 0:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=date_range_months * 30)
            date_constraint = f"submittedDate:[{start_date.strftime('%Y%m%d')}0000 TO {end_date.strftime('%Y%m%d')}2359]"
            query = f"({query}) AND {date_constraint}"
        
        return query
    
    def _apply_search_mode(self, query: str, mode: str) -> str:
        """
        Apply search mode transformation to match different search strategies.
        
        Args:
            query: Original search query
            mode: Search mode to apply
            
        Returns:
            Transformed query
        """
        if mode == 'exact':
            # Search for exact phrases in quotes
            return self._convert_to_exact_phrases(query)
        
        elif mode == 'title_focus':
            # Focus search on titles primarily
            return self._convert_to_title_search(query)
        
        elif mode == 'comprehensive':
            # Search across all fields broadly
            return self._convert_to_comprehensive_search(query)
        
        elif mode == 'balanced':
            # Balanced approach - similar to web interface default
            return self._convert_to_balanced_search(query)
        
        elif mode == 'web_exact':
            # Exact replication of web interface search behavior
            return self._convert_to_web_exact_search(query)
        
        else:  # 'natural' or default
            # Use the query as-is, let arXiv's natural language processing handle it
            return query
    
    def _convert_to_exact_phrases(self, query: str) -> str:
        """Convert query to use exact phrase matching."""
        # Handle AND/OR operators
        if ' AND ' in query:
            parts = [part.strip() for part in query.split(' AND ')]
            exact_parts = []
            for part in parts:
                if not (part.startswith('"') and part.endswith('"')):
                    exact_parts.append(f'"{part}"')
                else:
                    exact_parts.append(part)
            return ' AND '.join(exact_parts)
        
        elif ' OR ' in query:
            parts = [part.strip() for part in query.split(' OR ')]
            exact_parts = []
            for part in parts:
                if not (part.startswith('"') and part.endswith('"')):
                    exact_parts.append(f'"{part}"')
                else:
                    exact_parts.append(part)
            return ' OR '.join(exact_parts)
        
        else:
            # Single term - make it exact if not already quoted
            if not (query.startswith('"') and query.endswith('"')):
                return f'"{query}"'
            return query
    
    def _convert_to_title_search(self, query: str) -> str:
        """Convert query to focus on title searches."""
        if ' AND ' in query:
            parts = [part.strip() for part in query.split(' AND ')]
            title_parts = []
            for part in parts:
                if not part.startswith('ti:'):
                    if part.startswith('"') and part.endswith('"'):
                        title_parts.append(f'ti:{part}')
                    else:
                        title_parts.append(f'ti:"{part}"')
                else:
                    title_parts.append(part)
            return ' AND '.join(title_parts)
        
        elif ' OR ' in query:
            parts = [part.strip() for part in query.split(' OR ')]
            title_parts = []
            for part in parts:
                if not part.startswith('ti:'):
                    if part.startswith('"') and part.endswith('"'):
                        title_parts.append(f'ti:{part}')
                    else:
                        title_parts.append(f'ti:"{part}"')
                else:
                    title_parts.append(part)
            return ' OR '.join(title_parts)
        
        else:
            if not query.startswith('ti:'):
                if query.startswith('"') and query.endswith('"'):
                    return f'ti:{query}'
                else:
                    return f'ti:"{query}"'
            return query
    
    def _convert_to_comprehensive_search(self, query: str) -> str:
        """Convert query to search comprehensively across all fields."""
        if ' AND ' in query:
            parts = [part.strip() for part in query.split(' AND ')]
            comprehensive_parts = []
            for part in parts:
                if not any(part.startswith(f"{field}:") for field in ['all', 'ti', 'abs', 'au']):
                    comprehensive_parts.append(f'all:{part}')
                else:
                    comprehensive_parts.append(part)
            return ' AND '.join(comprehensive_parts)
        
        elif ' OR ' in query:
            parts = [part.strip() for part in query.split(' OR ')]
            comprehensive_parts = []
            for part in parts:
                if not any(part.startswith(f"{field}:") for field in ['all', 'ti', 'abs', 'au']):
                    comprehensive_parts.append(f'all:{part}')
                else:
                    comprehensive_parts.append(part)
            return ' OR '.join(comprehensive_parts)
        
        else:
            if not any(query.startswith(f"{field}:") for field in ['all', 'ti', 'abs', 'au']):
                return f'all:{query}'
            return query
    
    def _convert_to_balanced_search(self, query: str) -> str:
        """
        Convert query to balanced search - most similar to web interface.
        Uses a combination of approaches for best results.
        """
        # For complex queries with quoted phrases, preserve them
        if '"' in query:
            return query  # Keep quoted phrases as-is
        
        # For simple AND/OR queries, make them more targeted
        if ' AND ' in query:
            parts = [part.strip() for part in query.split(' AND ')]
            balanced_parts = []
            for part in parts:
                # For multi-word terms, use quotes; for single words, use all: prefix
                if ' ' in part and not part.startswith('"'):
                    balanced_parts.append(f'"{part}"')
                elif not any(part.startswith(f"{field}:") for field in ['all', 'ti', 'abs', 'au']):
                    balanced_parts.append(f'all:{part}')
                else:
                    balanced_parts.append(part)
            return ' AND '.join(balanced_parts)
        
        elif ' OR ' in query:
            parts = [part.strip() for part in query.split(' OR ')]
            balanced_parts = []
            for part in parts:
                # For multi-word terms, use quotes; for single words, use all: prefix
                if ' ' in part and not part.startswith('"'):
                    balanced_parts.append(f'"{part}"')
                elif not any(part.startswith(f"{field}:") for field in ['all', 'ti', 'abs', 'au']):
                    balanced_parts.append(f'all:{part}')
                else:
                    balanced_parts.append(part)
            return ' OR '.join(balanced_parts)
        
        else:
            # Single term
            if ' ' in query:
                return f'"{query}"'  # Multi-word: use quotes
            else:
                return f'all:{query}'  # Single word: use all: prefix
    
    def _convert_to_web_exact_search(self, query: str) -> str:
        """
        Convert query to match web interface search behavior exactly.
        
        Web interface uses a specific format that seems to work best with
        quoted phrases for exact terms combined with boolean operators.
        """
        # Handle common patterns based on web interface behavior
        if 'AND' in query.upper():
            parts = [part.strip() for part in query.split(' AND ')]
            # For web interface matching, use quoted phrases with AND
            quoted_parts = []
            for part in parts:
                part_clean = part.strip().strip('"')
                if ' ' in part_clean:
                    # Multi-word terms should be quoted
                    quoted_parts.append(f'"{part_clean}"')
                else:
                    # Single words can remain unquoted
                    quoted_parts.append(part_clean)
            return ' AND '.join(quoted_parts)
        
        elif 'OR' in query.upper():
            parts = [part.strip() for part in query.split(' OR ')]
            quoted_parts = []
            for part in parts:
                part_clean = part.strip().strip('"')
                if ' ' in part_clean:
                    quoted_parts.append(f'"{part_clean}"')
                else:
                    quoted_parts.append(part_clean)
            return ' OR '.join(quoted_parts)
        
        else:
            # Single term or phrase
            query_clean = query.strip().strip('"')
            if ' ' in query_clean:
                return f'"{query_clean}"'
            else:
                return query_clean
    
    def search_papers(self, search_term: str) -> List[Dict]:
        """
        Search for papers using improved methodology.
        
        Args:
            search_term: Search query string
            
        Returns:
            List of paper dictionaries
        """
        print(f" Searching arXiv for: '{search_term}'")
        
        # Build proper query
        categories = self.config.get('categories', [])
        query = self.build_search_query(search_term, categories)
        
        if query != search_term:
            print(f"   Transformed query: '{query}'")
        
        # Determine sort criteria
        sort_by = self.config.get('sort_by', 'relevance')
        if sort_by == 'relevance':
            sort_criterion = arxiv.SortCriterion.Relevance
        elif sort_by == 'date':
            sort_criterion = arxiv.SortCriterion.SubmittedDate
        else:
            sort_criterion = arxiv.SortCriterion.Relevance
        
        # Create search
        max_results = self.config.get('max_papers_per_search', 0)
        if max_results == 0:
            max_results = None  # Get all results
        
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=sort_criterion,
            sort_order=arxiv.SortOrder.Descending
        )
        
        papers = []
        try:
            print(f"   Fetching results...")
            
            count = 0
            for paper in self.client.results(search):
                # Normalize arXiv ID (remove version info if present for consistency)
                arxiv_id = paper.entry_id.split('/')[-1]
                if 'v' in arxiv_id:
                    arxiv_id = arxiv_id  # Keep version info for accuracy
                
                paper_data = {
                    'arxiv_id': arxiv_id,
                    'title': paper.title.strip(),
                    'summary': paper.summary.strip(),
                    'authors': [str(author) for author in paper.authors],
                    'published': paper.published.isoformat(),
                    'updated': paper.updated.isoformat(),
                    'categories': paper.categories,
                    'primary_category': paper.primary_category,
                    'pdf_url': paper.pdf_url,
                    'search_term': search_term,
                    'search_query': query
                }
                papers.append(paper_data)
                count += 1
                
                # Progress reporting
                if count % 100 == 0:
                    print(f"     Retrieved {count} papers...")
        
        except Exception as e:
            print(f" Error during search: {e}")
            return papers
        
        print(f"    Found {len(papers)} papers")
        return papers
    
    def run_discovery(self) -> List[Dict]:
        """
        Run the complete discovery process.
        
        Returns:
            List of all discovered papers
        """
        print(f" Starting improved arXiv paper discovery...")
        print(f"   Search terms: {self.config['search_terms']}")
        print(f"   Search mode: {self.config.get('search_mode', 'balanced')}")
        print(f"   Categories: {self.config.get('categories', 'all')}")
        print(f"   Sort by: {self.config.get('sort_by', 'relevance')}")
        
        if self.config.get('date_range_months', 0) > 0:
            print(f"   Date range: Last {self.config['date_range_months']} months")
        else:
            print(f"   Date range: All dates")
        
        all_papers = []
        seen_arxiv_ids = set()
        
        for i, search_term in enumerate(self.config['search_terms']):
            # Add rate limiting between searches
            if i > 0:
                print(f"   ⏸️  Rate limiting: waiting {self.config['rate_limit_delay']} seconds...")
                time.sleep(self.config['rate_limit_delay'])
            
            papers = self.search_papers(search_term)
            
            # Remove duplicates
            new_papers = 0
            for paper in papers:
                if paper['arxiv_id'] not in seen_arxiv_ids:
                    all_papers.append(paper)
                    seen_arxiv_ids.add(paper['arxiv_id'])
                    new_papers += 1
            
            print(f"    Added {new_papers} new papers from this search")
        
        print(f" Discovery complete: {len(all_papers)} unique papers found")
        self.search_results = all_papers
        return all_papers
    
    def save_results(self, filename: Optional[str] = None) -> str:
        """
        Save search results to a JSON file.
        
        Args:
            filename: Optional filename, defaults to timestamped file
            
        Returns:
            Path to saved file
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            mode = self.config.get('search_mode', 'balanced')
            filename = f"arxiv_discovery_{mode}_{timestamp}.json"
        
        # Ensure results directory exists
        os.makedirs("results", exist_ok=True)
        filepath = os.path.join("results", filename)
        
        # Prepare data for saving
        save_data = {
            'config': self.config,
            'timestamp': datetime.now().isoformat(),
            'total_papers': len(self.search_results),
            'search_summary': {
                'search_terms': self.config['search_terms'],
                'mode': self.config.get('search_mode', 'balanced'),
                'categories': self.config.get('categories', []),
                'papers_per_term': {}
            },
            'papers': self.search_results
        }
        
        # Add per-term statistics
        for term in self.config['search_terms']:
            term_papers = [p for p in self.search_results if p['search_term'] == term]
            save_data['search_summary']['papers_per_term'][term] = len(term_papers)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        
        print(f" Results saved to: {filepath}")
        return filepath
    
    def export_arxiv_ids(self, filename: Optional[str] = None) -> str:
        """
        Export just the arXiv IDs to a text file for use with other tools.
        
        Args:
            filename: Optional filename
            
        Returns:
            Path to saved file
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            mode = self.config.get('search_mode', 'balanced')
            filename = f"arxiv_ids_{mode}_{timestamp}.txt"
        
        # Ensure results directory exists
        os.makedirs("results", exist_ok=True)
        filepath = os.path.join("results", filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for paper in self.search_results:
                f.write(f"{paper['arxiv_id']}\n")
        
        print(f" ArXiv IDs exported to: {filepath}")
        return filepath


def main():
    """Main function for command-line usage with improved options."""
    parser = argparse.ArgumentParser(
        description="Improved arXiv paper discovery that better matches web interface behavior",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Search Modes:
  natural      - Use queries as-is (most similar to typing in web interface)
  balanced     - Balanced approach with smart field targeting (recommended)
  exact        - Exact phrase matching in quotes
  title_focus  - Focus search on paper titles
  comprehensive- Search broadly across all fields

Examples:
  %(prog)s --search-terms "robotics foundation model" --mode balanced
  %(prog)s --search-terms "machine learning" "deep learning" --categories cs.LG cs.AI
  %(prog)s --search-terms "transformer" --mode title_focus --months 12
        """
    )
    
    parser.add_argument("--search-terms", nargs="+", 
                        default=["robotics AND foundation model"],
                        help="Search terms to use")
    parser.add_argument("--categories", nargs="*", 
                        default=[],
                        help="arXiv categories to search (empty = all categories)")
    parser.add_argument("--max-results", type=int, default=0,
                        help="Maximum results per search term (0 = get all)")
    parser.add_argument("--months", type=int, default=0,
                        help="Date range in months (0 = all dates)")
    parser.add_argument("--mode", choices=["natural", "balanced", "exact", "title_focus", "comprehensive"], 
                        default="balanced",
                        help="Search mode to use (default: balanced)")
    parser.add_argument("--sort", choices=["relevance", "date"], 
                        default="relevance",
                        help="Sort results by relevance or date")
    parser.add_argument("--output", 
                        help="Output filename for results")
    parser.add_argument("--export-ids", action="store_true",
                        help="Also export just arXiv IDs to a text file")
    
    args = parser.parse_args()
    
    # Create configuration from arguments
    config = {
        'search_terms': args.search_terms,
        'categories': args.categories,
        'max_papers_per_search': args.max_results,
        'date_range_months': args.months,
        'search_mode': args.mode,
        'sort_by': args.sort,
        'rate_limit_delay': 3.0,
    }
    
    # Run discovery
    discovery = ArXivDiscovery(config)
    papers = discovery.run_discovery()
    
    if papers:
        # Save results
        results_file = discovery.save_results(args.output)
        
        # Export IDs if requested
        if args.export_ids:
            discovery.export_arxiv_ids()
        
        # Print summary
        print(f"\n Discovery Summary:")
        print(f"   Total papers found: {len(papers)}")
        print(f"   Search mode: {config['search_mode']}")
        print(f"   Sort order: {config['sort_by']}")
        
        if config['categories']:
            print(f"   Categories: {', '.join(config['categories'])}")
        else:
            print(f"   Categories: All")
        
        if config['date_range_months'] > 0:
            print(f"   Date range: Last {config['date_range_months']} months")
        else:
            print(f"   Date range: All dates")
        
        print(f"   Results saved to: {results_file}")
        
        # Show sample papers
        print(f"\n Sample papers:")
        for i, paper in enumerate(papers[:5], 1):
            print(f"   {i}. {paper['title'][:80]}...")
            print(f"      arXiv:{paper['arxiv_id']} | {paper['published'][:10]} | {paper['primary_category']}")
    else:
        print(" No papers found matching the search criteria.")


if __name__ == "__main__":
    main()
