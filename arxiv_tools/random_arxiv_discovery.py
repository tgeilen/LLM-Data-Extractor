#!/usr/bin/env python3
"""
Random ArXiv Paper Discovery Module

This module provides functionality to search arXiv for random papers from various domains,
specifically excluding foundation models and robotics papers.
"""

import os
import time
import json
import random
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Import existing arXiv functionality
import arxiv

class RandomArXivDiscovery:
    """
    Class for discovering random papers from various domains, excluding
    foundation models and robotics papers.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the discovery module with configuration.
        
        Args:
            config: Configuration dictionary with search parameters
        """
        self.config = config or self._get_default_config()
        self.search_results = []
        
        # Create arXiv client with proper rate limiting
        self.client = arxiv.Client(
            page_size=100,
            delay_seconds=3.0,
            num_retries=3
        )
    
    def _get_default_config(self) -> Dict:
        """Get default configuration for random paper discovery."""
        return {
            # Diverse search terms from different domains
            'search_terms': [
                'cat:math.CO',  # Combinatorics
                'cat:physics.optics',  # Optics
                'cat:q-bio.BM',  # Biomolecules
                'cat:cs.DB',  # Databases
                'cat:econ.EM',  # Econometrics
                'cat:stat.ML',  # Machine Learning (Statistics)
                'cat:cs.CG',  # Computational Geometry
                'cat:physics.chem-ph',  # Chemical Physics
                'cat:cs.IR',  # Information Retrieval
                'cat:math.NT',  # Number Theory
                'cat:physics.soc-ph',  # Physics and Society
                'cat:cs.CY',  # Computers and Society
                'cat:q-bio.QM',  # Quantitative Methods
                'cat:cs.SE',  # Software Engineering
                'cat:math.ST',  # Statistics Theory
            ],
            'exclude_terms': [
                'foundation model',
                'foundational model',
                'robotics',
                'robot',
                'robotic',
                'manipulation',
                'grasping',
                'navigation',
                'autonomous',
                'LLM',
                'large language model',
                'vision language model',
                'transformer',
                'BERT',
                'GPT',
                'multimodal'
            ],
            'max_papers_per_category': 50,  # Limit per category to ensure diversity
            'target_total': 500,
            'date_range_months': 24,  # Last 24 months for relatively recent papers
            'rate_limit_delay': 3.0,
            'randomize': True
        }
    
    def search_random_papers(self) -> List[Dict]:
        """
        Search for random papers from various domains, excluding foundation models and robotics.
        
        Returns:
            List of paper dictionaries
        """
        print(f" Starting random arXiv paper discovery...")
        print(f"   Target: {self.config['target_total']} papers")
        exclude_terms = self.config.get('exclude_terms', [])
        if exclude_terms:
            print(f"   Excluding: {', '.join(exclude_terms[:5])}...")
        print(f"   Date range: Last {self.config['date_range_months']} months")
        
        all_papers = []
        seen_arxiv_ids = set()
        
        # Calculate date range for filtering
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.config['date_range_months'] * 30)
        
        # Randomize search terms for more variety
        search_terms = self.config['search_terms'].copy()
        if self.config['randomize']:
            random.shuffle(search_terms)
        
        for i, search_term in enumerate(search_terms):
            if len(all_papers) >= self.config['target_total']:
                break
                
            if i > 0:
                print(f"   ⏸️  Waiting {self.config['rate_limit_delay']} seconds...")
                time.sleep(self.config['rate_limit_delay'])
            
            print(f"\n Searching category {i+1}/{len(search_terms)}: {search_term}")
            
            papers = self._search_category(search_term, start_date, end_date)
            
            # Filter out foundation model and robotics papers
            filtered_papers = self._filter_exclude_terms(papers)
            
            print(f"   Found {len(papers)} papers, {len(filtered_papers)} after filtering")
            
            # Add papers to results (avoid duplicates)
            added_count = 0
            for paper in filtered_papers:
                if paper['arxiv_id'] not in seen_arxiv_ids:
                    all_papers.append(paper)
                    seen_arxiv_ids.add(paper['arxiv_id'])
                    added_count += 1
                    
                    if len(all_papers) >= self.config['target_total']:
                        break
            
            print(f"   Added {added_count} new papers (total: {len(all_papers)})")
        
        # If we have more papers than needed, randomly sample
        if len(all_papers) > self.config['target_total']:
            print(f"\n Randomly sampling {self.config['target_total']} from {len(all_papers)} papers...")
            all_papers = random.sample(all_papers, self.config['target_total'])
        
        print(f"\n Random discovery complete: {len(all_papers)} papers found")
        self.search_results = all_papers
        return all_papers
    
    def _search_category(self, category_term: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        Search for papers in a specific category.
        
        Args:
            category_term: Category search term (e.g., 'cat:math.CO')
            start_date: Start date for filtering
            end_date: End date for filtering
            
        Returns:
            List of paper dictionaries
        """
        papers = []
        max_papers = self.config['max_papers_per_category']
        
        # Add date constraint to query
        date_constraint = f"submittedDate:[{start_date.strftime('%Y%m%d')} TO {end_date.strftime('%Y%m%d')}]"
        full_query = f"{category_term} AND {date_constraint}"
        
        try:
            # Use relevance sorting for more diverse results
            search = arxiv.Search(
                query=full_query,
                max_results=max_papers,
                sort_by=arxiv.SortCriterion.Relevance,
                sort_order=arxiv.SortOrder.Descending
            )
            
            for paper in self.client.results(search):
                if paper.published.date() >= start_date.date():
                    paper_data = {
                        'arxiv_id': paper.entry_id.split('/')[-1],
                        'title': paper.title.strip(),
                        'summary': paper.summary.strip(),
                        'authors': [str(author) for author in paper.authors],
                        'published': paper.published.isoformat(),
                        'categories': paper.categories,
                        'primary_category': paper.primary_category,
                        'pdf_url': paper.pdf_url,
                        'search_term': category_term
                    }
                    papers.append(paper_data)
                    
        except Exception as e:
            print(f"     Warning: Error searching {category_term}: {e}")
        
        return papers
    
    def _filter_exclude_terms(self, papers: List[Dict]) -> List[Dict]:
        """
        Filter out papers that mention excluded terms.
        
        Args:
            papers: List of paper dictionaries
            
        Returns:
            Filtered list of papers
        """
        filtered_papers = []
        exclude_terms = [term.lower() for term in self.config.get('exclude_terms', [])]
        
        for paper in papers:
            title_lower = paper['title'].lower()
            abstract_lower = paper['summary'].lower()
            
            # Check if any exclude term appears in title or abstract
            exclude_paper = False
            for term in exclude_terms:
                if term in title_lower or term in abstract_lower:
                    exclude_paper = True
                    break
            
            if not exclude_paper:
                filtered_papers.append(paper)
        
        return filtered_papers
    
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
            filename = f"random_arxiv_results_{timestamp}.json"
        
        filepath = os.path.join("results", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'search_config': self.config,
                'search_timestamp': datetime.now().isoformat(),
                'total_papers': len(self.search_results),
                'papers': self.search_results
            }, f, indent=2, ensure_ascii=False)
        
        print(f" Results saved to: {filepath}")
        return filepath
    
    def export_arxiv_ids(self, filename: Optional[str] = None) -> str:
        """
        Export just the arXiv IDs to a text file.
        
        Args:
            filename: Optional filename, defaults to timestamped file
            
        Returns:
            Path to saved file
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"random_arxiv_ids_{timestamp}.txt"
        
        filepath = os.path.join("results", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for paper in self.search_results:
                f.write(f"{paper['arxiv_id']}\n")
        
        print(f" ArXiv IDs exported to: {filepath}")
        return filepath
    
    def get_domain_statistics(self) -> Dict:
        """
        Get statistics about the domains/categories found.
        
        Returns:
            Dictionary with domain statistics
        """
        stats = {}
        
        for paper in self.search_results:
            primary_cat = paper.get('primary_category', 'unknown')
            if primary_cat not in stats:
                stats[primary_cat] = 0
            stats[primary_cat] += 1
        
        return stats
    
    def print_summary(self):
        """Print a summary of the discovered papers."""
        if not self.search_results:
            print("No papers found.")
            return
        
        print(f"\n Random ArXiv Discovery Summary:")
        print(f"   Total papers: {len(self.search_results)}")
        print(f"   Date range: {self.config['date_range_months']} months")
        
        # Domain statistics
        domain_stats = self.get_domain_statistics()
        print(f"\n Papers by domain:")
        for domain, count in sorted(domain_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"   {domain}: {count}")
        
        # Sample papers
        print(f"\n Sample papers:")
        sample_papers = random.sample(self.search_results, min(5, len(self.search_results)))
        for i, paper in enumerate(sample_papers, 1):
            print(f"   {i}. {paper['title'][:80]}...")
            print(f"      arXiv:{paper['arxiv_id']} | {paper['primary_category']} | {paper['published'][:10]}")


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description="Discover random papers from various arXiv domains")
    parser.add_argument("--target", type=int, default=500,
                        help="Target number of papers to collect")
    parser.add_argument("--months", type=int, default=24,
                        help="Date range in months (recent papers)")
    parser.add_argument("--max-per-category", type=int, default=50,
                        help="Maximum papers per category")
    parser.add_argument("--output", 
                        help="Output filename for results")
    parser.add_argument("--ids-only", action="store_true",
                        help="Export only arXiv IDs (not full results)")
    parser.add_argument("--categories", nargs="+",
                        help="Specific categories to search (overrides defaults)")
    
    args = parser.parse_args()
    
    # Create discovery instance with defaults first
    discovery = RandomArXivDiscovery()
    
    # Update configuration from arguments
    discovery.config.update({
        'target_total': args.target,
        'date_range_months': args.months,
        'max_papers_per_category': args.max_per_category,
        'rate_limit_delay': 3.0,
        'randomize': True
    })
    
    # Override categories if specified
    if args.categories:
        discovery.config['search_terms'] = [f'cat:{cat}' for cat in args.categories]
    
    # Run discovery
    papers = discovery.search_random_papers()
    
    if papers:
        # Save results
        if args.ids_only:
            output_file = discovery.export_arxiv_ids(args.output)
        else:
            output_file = discovery.save_results(args.output)
            discovery.export_arxiv_ids()  # Also save IDs
        
        # Print summary
        discovery.print_summary()
        print(f"\n Results saved to: {output_file}")
        
    else:
        print("No papers found matching the criteria.")


if __name__ == "__main__":
    main()
