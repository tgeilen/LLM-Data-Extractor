#!/usr/bin/env python3
"""
Complete ArXiv Discovery Pipeline

This script combines paper search and LLM classification to automatically discover
foundational robotics models from arXiv.
"""

import os
import argparse
from datetime import datetime
from typing import Dict, List

from .arxiv_discovery import ArXivDiscovery
from .arxiv_filter import ArXivClassifier


def run_complete_discovery(config: Dict) -> Dict:
    """
    Run the complete discovery pipeline: search + classification.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Complete results including search and classification
    """
    print(" Starting Complete ArXiv Discovery Pipeline")
    print("=" * 60)
    
    # Phase 1: Search arXiv
    print("\n Phase 1: Searching arXiv...")
    discovery = ArXivDiscovery(config)
    papers = discovery.run_discovery()
    
    if not papers:
        print(" No papers found. Exiting.")
        return {"error": "No papers found"}
    
    # Save search results
    search_file = discovery.save_results()
    
    # Phase 2: LLM Classification
    print(f"\n Phase 2: LLM Classification...")
    classifier = ArXivClassifier(
        provider=config.get('classification_provider', 'deepseek'),
        rate_limit_delay=config.get('rate_limit_delay', 1.0)
    )
    
    classification_results = classifier.classify_papers(
        papers, 
        confidence_threshold=config.get('confidence_threshold', 0.7)
    )
    
    # Save classification results
    classification_file = classifier.save_classification_results(classification_results)
    
    # Export discovered arXiv IDs
    arxiv_ids_file = classifier.export_positive_arxiv_ids(
        classification_results,
        config.get('output_file', None)
    )
    
    # Combine results
    complete_results = {
        "pipeline_config": config,
        "search_results": {
            "total_papers_found": len(papers),
            "search_file": search_file,
            "papers": papers
        },
        "classification_results": classification_results,
        "output_files": {
            "search_results": search_file,
            "classification_results": classification_file,
            "discovered_arxiv_ids": arxiv_ids_file
        },
        "pipeline_timestamp": datetime.now().isoformat()
    }
    
    # Print final summary
    print_pipeline_summary(complete_results)
    
    return complete_results


def print_pipeline_summary(results: Dict):
    """Print a summary of the discovery pipeline results."""
    search_summary = results["search_results"]
    class_summary = results["classification_results"]["classification_summary"]
    
    print(f"\n Discovery Pipeline Summary")
    print("=" * 60)
    print(f"Search Results:")
    print(f"   Total papers found: {search_summary['total_papers_found']}")
    
    print(f"\nClassification Results:")
    print(f"   Papers classified: {class_summary['total_papers']}")
    print(f"   Positive matches: {class_summary['positive_classifications']}")
    print(f"   Match rate: {class_summary['match_rate']:.1%}")
    print(f"   Success rate: {class_summary['success_rate']:.1%}")
    print(f"   Provider: {class_summary['provider'].upper()}")
    
    print(f"\nOutput Files:")
    for file_type, filepath in results["output_files"].items():
        print(f"   {file_type}: {filepath}")
    
    if class_summary['positive_classifications'] > 0:
        print(f"\n Found {class_summary['positive_classifications']} potential foundational robotics models!")
        print("   Check the output files for detailed results.")
    else:
        print(f"\n No foundational robotics models found matching the criteria.")
        print("   Consider adjusting search terms or confidence threshold.")


def get_default_config() -> Dict:
    """Get default configuration for the discovery pipeline."""
    return {
        'search_terms': [
            'robotics AND "foundation model"',
            'robot AND "large model"',
            'robotics AND transformer',
            'robot AND multimodal AND model'
        ],
        'categories': ['cs.RO', 'cs.AI', 'cs.LG', 'cs.CV'],
        'max_papers_per_search': 50,
        'date_range_months': 12,  # Last 12 months
        'search_mode': 'balanced',  # Use improved search modes
        'sort_by': 'relevance',
        'classification_provider': 'deepseek',
        'confidence_threshold': 0.7,
        'rate_limit_delay': 3.0,  # Use recommended 3-second delay
        'output_file': 'discovered_foundational_robotics_models.txt'
    }


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Discover foundational robotics models from arXiv",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic discovery with default settings
  python discovery_pipeline.py

  # Custom search terms and provider
  python discovery_pipeline.py --search-terms "robotics foundation model" "robot transformer" --provider gemini

  # Adjust parameters
  python discovery_pipeline.py --max-results 100 --months 6 --confidence 0.8
        """
    )
    
    parser.add_argument("--search-terms", nargs="+",
                        help="Search terms to use (default: robotics-focused terms)")
    parser.add_argument("--categories", nargs="+",
                        default=["cs.RO", "cs.AI", "cs.LG", "cs.CV"],
                        help="arXiv categories to search")
    parser.add_argument("--max-results", type=int, default=50,
                        help="Maximum results per search term (default: 50)")
    parser.add_argument("--months", type=int, default=12,
                        help="Date range in months (default: 12)")
    parser.add_argument("--search-mode", choices=["natural", "balanced", "exact", "title_focus", "comprehensive"], 
                        default="balanced",
                        help="Search mode to use (default: balanced)")
    parser.add_argument("--provider", choices=["deepseek", "gemini"], default="deepseek",
                        help="LLM provider for classification (default: deepseek)")
    parser.add_argument("--confidence", type=float, default=0.7,
                        help="Confidence threshold for positive classification (default: 0.7)")
    parser.add_argument("--output", 
                        help="Output filename for discovered arXiv IDs")
    parser.add_argument("--delay", type=float, default=3.0,
                        help="Rate limit delay between API calls (default: 3.0)")
    
    args = parser.parse_args()
    
    # Build configuration
    config = get_default_config()
    
    # Override with command line arguments
    if args.search_terms:
        config['search_terms'] = args.search_terms
    config['categories'] = args.categories
    config['max_papers_per_search'] = args.max_results
    config['date_range_months'] = args.months
    config['search_mode'] = args.search_mode
    config['classification_provider'] = args.provider
    config['confidence_threshold'] = args.confidence
    config['rate_limit_delay'] = args.delay
    if args.output:
        config['output_file'] = args.output
    
    # Ensure results directory exists
    os.makedirs("results", exist_ok=True)
    
    # Run the complete pipeline
    try:
        results = run_complete_discovery(config)
        
        if "error" not in results:
            print(f"\n Discovery pipeline completed successfully!")
            return 0
        else:
            print(f"\n Discovery pipeline failed: {results['error']}")
            return 1
            
    except KeyboardInterrupt:
        print(f"\n⏹️ Discovery pipeline interrupted by user")
        return 1
    except Exception as e:
        print(f"\n Discovery pipeline failed with error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
