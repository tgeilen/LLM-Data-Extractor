#!/usr/bin/env python3
"""
Standalone ArXiv Discovery Script

This script discovers foundational robotics papers from arXiv and saves results to text files.
No database dependencies - just saves arXiv IDs and results to simple files.
"""

import os
import argparse
import json
from datetime import datetime
from typing import List, Dict

def main():
    """Run standalone discovery without database dependencies."""
    parser = argparse.ArgumentParser(description="Discover foundational robotics papers from arXiv")
    parser.add_argument("--search-terms", nargs="+", 
                       default=["foundation model AND robotics", "foundational model AND robotics"],
                       help="Search terms to use (simple AND/OR logic without complex grouping)")
    parser.add_argument("--search-mode", choices=["natural", "balanced", "exact", "title_focus", "comprehensive"], 
                       default="balanced",
                       help="Search strategy: balanced (RECOMMENDED - web-like behavior), natural (queries as-is), exact (exact phrase matching), title_focus (focus on titles), comprehensive (broad field search)")
    parser.add_argument("--categories", nargs="*", default=[],
                       help="arXiv categories to search (empty = search all categories)")
    parser.add_argument("--max-results", type=int, default=0,
                       help="Maximum results per search term (0 = get all available)")
    parser.add_argument("--months", type=int, default=0,
                       help="Date range in months (0 = search all dates)")
    parser.add_argument("--provider", choices=["deepseek", "gemini"], default="deepseek",
                       help="LLM provider for classification")
    parser.add_argument("--confidence", type=float, default=0.7,
                       help="Confidence threshold for positive classification")
    parser.add_argument("--output", help="Output filename for discovered arXiv IDs")
    
    args = parser.parse_args()
    
    print(" Standalone ArXiv Discovery")
    print("=" * 50)
    print(f"Search terms: {args.search_terms}")
    print(f"Search mode: {args.search_mode}")
    print(f"Categories: {args.categories}")
    print(f"Max results per term: {args.max_results if args.max_results > 0 else 'ALL'}")
    print(f"Provider: {args.provider}")
    print(f"Confidence threshold: {args.confidence}")
    
    # Ensure results directory exists
    os.makedirs("results", exist_ok=True)
    
    try:
        # Import discovery modules
        from .arxiv_discovery import ArXivDiscovery
        from .arxiv_filter import ArXivClassifier
        
        # Phase 1: Search arXiv
        print("\n Phase 1: Searching arXiv...")
        
        # Configure discovery
        config = {
            'search_terms': args.search_terms,
            'search_mode': args.search_mode,
            'categories': args.categories,
            'max_papers_per_search': args.max_results,
            'date_range_months': args.months,
            'sort_by': 'relevance',
            'classification_provider': args.provider,
            'confidence_threshold': args.confidence,
            'rate_limit_delay': 3.0  # Use recommended 3-second delay
        }
        
        discovery = ArXivDiscovery(config)
        papers = discovery.run_discovery()
        
        if not papers:
            print(" No papers found. Exiting.")
            return
            
        print(f" Found {len(papers)} papers")
        
        # Convert papers to classification format
        paper_data = []
        for paper in papers:
            paper_data.append({
                'arxiv_id': paper.get('arxiv_id'),
                'title': paper.get('title'),
                'abstract': paper.get('summary'),  # ArXivDiscovery uses 'summary' key
                'authors': paper.get('authors'),
                'published': paper.get('published'),
                'categories': paper.get('categories')
            })
        
        # Save search results
        search_file = f"results/search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(search_file, 'w', encoding='utf-8') as f:
            json.dump({
                'search_metadata': {
                    'search_terms': args.search_terms,
                    'categories': args.categories,
                    'total_papers': len(papers),
                    'timestamp': datetime.now().isoformat()
                },
                'papers': paper_data
            }, f, indent=2, ensure_ascii=False)
        print(f" Search results saved to: {search_file}")
        
        # Phase 2: LLM Classification
        print(f"\n Phase 2: LLM Classification...")
        classifier = ArXivClassifier(provider=args.provider)
        
        results = classifier.classify_papers(paper_data, confidence_threshold=args.confidence)
        
        # Save classification results
        classifier.save_classification_results(results)
        
        # Export arXiv IDs to text file
        output_file = args.output or f"discovered_foundational_robotics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        ids_file = classifier.export_positive_arxiv_ids(results, output_file)
        
        # Print summary
        summary = results['classification_summary']
        print(f"\n Discovery Summary:")
        print(f"   Total papers searched: {summary['total_papers']}")
        print(f"   Foundational models found: {summary['positive_classifications']}")
        print(f"   Success rate: {summary['success_rate']:.1%}")
        print(f"   Match rate: {summary['match_rate']:.1%}")
        print(f"   Results saved to: {ids_file}")
        
        # Print discovered papers
        positive_matches = results.get('positive_matches', [])
        if positive_matches:
            print(f"\n Discovered Foundational Robotics Models:")
            for match in positive_matches:
                print(f"   • {match['arxiv_id']}: {match['title'][:80]}...")
                print(f"     Confidence: {match['confidence']:.2f}")
                if match.get('model_name'):
                    print(f"     Model: {match['model_name']}")
                print()
        
    except ImportError as e:
        print(f" Import error: {e}")
        print("Please ensure arxiv_tools/arxiv_discovery.py and arxiv_tools/arxiv_filter.py are available")
    except Exception as e:
        print(f" Error during discovery: {e}")


if __name__ == "__main__":
    main()
