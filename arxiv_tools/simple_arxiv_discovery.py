#!/usr/bin/env python3
"""
Simple ArXiv Paper Discovery

A straightforward implementation that just works without unnecessary complexity.
"""

import os
import time
import json
import argparse
from datetime import datetime
from typing import List, Dict, Optional

import arxiv

class SimpleArXivDiscovery:
    """Simple arXiv paper discovery that just works."""
    
    def __init__(self, search_terms: List[str], categories: List[str] = None, max_results: int = 0):
        """
        Initialize with basic parameters.
        
        Args:
            search_terms: List of search terms
            categories: Optional list of categories to filter by
            max_results: Maximum results per search (0 = get all)
        """
        self.search_terms = search_terms
        self.categories = categories or []
        self.max_results = max_results
        self.papers = []
        
        # Simple client with basic rate limiting
        self.client = arxiv.Client(
            page_size=100,
            delay_seconds=3.0,
            num_retries=3
        )
    
    def search_papers(self) -> List[Dict]:
        """Search for papers and return results."""
        print(f" Searching arXiv...")
        print(f"   Search terms: {self.search_terms}")
        if self.categories:
            print(f"   Categories: {self.categories}")
        
        all_papers = []
        seen_ids = set()
        
        for i, search_term in enumerate(self.search_terms):
            if i > 0:
                print(f"   ⏸️  Waiting 3 seconds...")
                time.sleep(3.0)
            
            print(f"\n Searching for: '{search_term}'")
            
            # Build query
            query = search_term
            if self.categories:
                category_filter = ' OR '.join([f'cat:{cat}' for cat in self.categories])
                query = f"({search_term}) AND ({category_filter})"
            
            print(f"   Query: {query}")
            
            # Create search
            search = arxiv.Search(
                query=query,
                max_results=self.max_results if self.max_results > 0 else None,
                sort_by=arxiv.SortCriterion.Relevance,
                sort_order=arxiv.SortOrder.Descending
            )
            
            # Get results
            count = 0
            try:
                for paper in self.client.results(search):
                    arxiv_id = paper.entry_id.split('/')[-1]
                    
                    if arxiv_id not in seen_ids:
                        paper_data = {
                            'arxiv_id': arxiv_id,
                            'title': paper.title.strip(),
                            'abstract': paper.summary.strip(),
                            'authors': [str(author) for author in paper.authors],
                            'published': paper.published.isoformat(),
                            'categories': paper.categories,
                            'primary_category': paper.primary_category,
                            'pdf_url': paper.pdf_url,
                            'search_term': search_term
                        }
                        all_papers.append(paper_data)
                        seen_ids.add(arxiv_id)
                        count += 1
                        
                        if count % 100 == 0:
                            print(f"     Found {count} papers...")
                
                print(f"    Found {count} papers for this search term")
                
            except Exception as e:
                print(f"    Error: {e}")
        
        self.papers = all_papers
        print(f"\n Total unique papers found: {len(all_papers)}")
        return all_papers
    
    def save_results(self, filename: Optional[str] = None) -> str:
        """Save results to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"simple_arxiv_results_{timestamp}.json"
        
        os.makedirs("results", exist_ok=True)
        filepath = os.path.join("results", filename)
        
        data = {
            'search_terms': self.search_terms,
            'categories': self.categories,
            'total_papers': len(self.papers),
            'timestamp': datetime.now().isoformat(),
            'papers': self.papers
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f" Results saved to: {filepath}")
        return filepath
    
    def export_ids(self, filename: Optional[str] = None) -> str:
        """Export arXiv IDs to text file."""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"arxiv_ids_{timestamp}.txt"
        
        os.makedirs("results", exist_ok=True)
        filepath = os.path.join("results", filename)
        
        with open(filepath, 'w') as f:
            for paper in self.papers:
                f.write(f"{paper['arxiv_id']}\n")
        
        print(f" ArXiv IDs exported to: {filepath}")
        return filepath


def main():
    """Simple command-line interface."""
    parser = argparse.ArgumentParser(description="Simple arXiv paper discovery")
    parser.add_argument("--search-terms", nargs="+", 
                        default=["foundational model AND robotics"],
                        help="Search terms to use")
    parser.add_argument("--categories", nargs="*", 
                        default=[],
                        help="arXiv categories to filter by")
    parser.add_argument("--max-results", type=int, default=0,
                        help="Maximum results per search (0 = get all)")
    parser.add_argument("--output", 
                        help="Output filename")
    parser.add_argument("--export-ids", action="store_true",
                        help="Also export arXiv IDs to text file")
    
    args = parser.parse_args()
    
    # Run discovery
    discovery = SimpleArXivDiscovery(
        search_terms=args.search_terms,
        categories=args.categories,
        max_results=args.max_results
    )
    
    papers = discovery.search_papers()
    
    if papers:
        # Save results
        discovery.save_results(args.output)
        
        if args.export_ids:
            discovery.export_ids()
        
        # Show summary
        print(f"\n Summary:")
        print(f"   Total papers: {len(papers)}")
        print(f"   Search terms: {args.search_terms}")
        
        if args.categories:
            print(f"   Categories: {args.categories}")
        
        # Show first few papers
        print(f"\n First 5 papers:")
        for i, paper in enumerate(papers[:5], 1):
            print(f"   {i}. {paper['title'][:70]}...")
            print(f"      {paper['arxiv_id']} | {paper['published'][:10]}")
    else:
        print(" No papers found")


if __name__ == "__main__":
    main()
