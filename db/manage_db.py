#!/usr/bin/env python3
"""
CLI script to manage the database.
"""

import os
import json
import argparse

from .db_utils import create_schema, drop_schema
from .paper_dao import PaperDAO
from .model_dao import ModelDAO
from .extraction_dao import ExtractionDAO
from ..analyser.db_integration import store_paper_from_md_file, get_or_create_model
from ..arxiv_tools.arxiv_processor import process_paper_from_arxiv
from .migrate_add_model_instance import migrate_add_model_instance_id

def setup_database(args):
    """
    Set up the database schema
    """
    create_schema()
    print("Database schema created successfully")

def reset_database(args):
    """
    Reset the database schema (drop and recreate)
    """
    drop_schema()
    create_schema()
    print("Database schema reset successfully")

def add_paper(args):
    """
    Add a paper to the database
    """
    paper_id = store_paper_from_md_file(
        args.file_path, 
        args.arxiv_id, 
        args.title,
        not args.no_content
    )
    
    if paper_id:
        print(f"Paper added successfully with ID: {paper_id}")
        return paper_id
    else:
        print("Failed to add paper")
        return None

def add_model(args):
    """
    Add a model to the database
    """
    model_id = get_or_create_model(
        args.name,
        args.provider,
        args.context_size,
        args.version
    )
    
    if model_id:
        print(f"Model added successfully with ID: {model_id}")
        return model_id
    else:
        print("Failed to add model")
        return None

def list_papers(args):
    """
    List all papers in the database
    """
    papers = PaperDAO.get_all_papers()
    
    if not papers:
        print("No papers found in the database")
        return
    
    print(f"Found {len(papers)} papers:")
    
    for i, paper in enumerate(papers, 1):
        pub_date_str = ""
        if paper.get('published_date'):
            pub_date_str = f" (Published: {paper['published_date'].strftime('%Y-%m-%d')})"
        
        print(f"{i}. ID: {paper['id']}, ArXiv ID: {paper['arxiv_id']}, Title: {paper['title']}{pub_date_str}")
        
        if args.verbose:
            print(f"   MD Path: {paper['md_path']}")
            if paper['pdf_path']:
                print(f"   PDF Path: {paper['pdf_path']}")
            if paper.get('published_date'):
                print(f"   Published: {paper['published_date']}")
            print(f"   Created: {paper['created_at']}")
            
            # Get extraction runs for this paper
            runs = ExtractionDAO.get_extraction_runs_for_paper(paper['id'])
            if runs:
                print(f"   Extraction Runs: {len(runs)}")
                for run in runs:
                    print(f"      - {run['run_date']}: {run['model_provider']} {run['model_name']}")
            
            print()

def list_models(args):
    """
    List all models in the database
    """
    models = ModelDAO.get_all_models()
    
    if not models:
        print("No models found in the database")
        return
    
    print(f"Found {len(models)} models:")
    
    for i, model in enumerate(models, 1):
        print(f"{i}. ID: {model['id']}, Name: {model['name']}, Provider: {model['provider']}")
        
        if args.verbose:
            print(f"   Version: {model['version'] or 'N/A'}")
            print(f"   Context Size: {model['context_size'] or 'N/A'}")
            print(f"   Created: {model['created_at']}")
            print()

def process_arxiv_paper(args):
    """
    Process a paper from arXiv
    """
    arxiv_id = args.arxiv_id
    
    if not arxiv_id:
        print("arXiv ID is required")
        return
    
    print(f"Processing paper {arxiv_id} from arXiv...")
    
    paper_id = process_paper_from_arxiv(
        arxiv_id=arxiv_id,
        run_ocr=not args.skip_ocr,
        run_analysis=args.run_analysis,
        deepseek_runs=args.deepseek_runs,
        gemini_runs=args.gemini_runs,
        output_dir=args.output_dir
    )
    
    if paper_id:
        print(f"Paper processed successfully. Paper ID: {paper_id}")
    else:
        print("Failed to process paper completely")

def migrate_database(args):
    """
    Run database migrations
    """
    print("Running database migrations...")
    success = migrate_add_model_instance_id()
    if success:
        print("Migrations completed successfully")
    else:
        print("Migrations failed")

def migrate_publication_dates(args):
    """
    Run migration to add publication dates to papers table
    """
    try:
        from migrate_add_publication_date import add_published_date_column, fetch_publication_dates_from_arxiv
        
        if not args.fetch_dates_only:
            add_published_date_column()
        
        if not args.add_column_only:
            fetch_publication_dates_from_arxiv()
        
        print("\n Migration completed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n Migration failed: {e}")
        return 1

def discover_papers(args):
    """
    Discover foundational robotics models from arXiv
    """
    try:
        # Import discovery modules here to avoid import issues if not available
        from ..arxiv_tools.discovery_pipeline import run_complete_discovery, get_default_config
        
        print(" Starting arXiv paper discovery...")
        
        # Build configuration from arguments
        config = get_default_config()
        
        # Override with command line arguments
        if args.search_terms:
            config['search_terms'] = args.search_terms
        config['categories'] = args.categories
        config['max_papers_per_search'] = args.max_results
        config['date_range_months'] = args.months
        config['classification_provider'] = args.provider
        config['confidence_threshold'] = args.confidence
        if args.output:
            config['output_file'] = args.output
        
        # Ensure results directory exists
        os.makedirs("results", exist_ok=True)
        
        # Run the discovery pipeline
        results = run_complete_discovery(config)
        
        if "error" not in results:
            print(f"\n Discovery completed successfully!")
            
            # Optionally ask if user wants to process discovered papers
            positive_count = results["classification_results"]["classification_summary"]["positive_classifications"]
            if positive_count > 0:
                print(f"\nFound {positive_count} potential foundational robotics models.")
                print("Use the output file to process these papers with the existing pipeline.")
        else:
            print(f"\n Discovery failed: {results['error']}")
            
    except ImportError as e:
        print(f" Discovery modules not available: {e}")
        print("Make sure arxiv_tools/arxiv_discovery.py and arxiv_tools/arxiv_filter.py are in the same directory.")
    except Exception as e:
        print(f" Discovery failed with error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Manage the LLM extraction database")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Setup database command
    setup_parser = subparsers.add_parser("setup", help="Set up the database schema")
    setup_parser.set_defaults(func=setup_database)
    
    # Reset database command
    reset_parser = subparsers.add_parser("reset", help="Reset the database (drop and recreate)")
    reset_parser.set_defaults(func=reset_database)
    
    # Migrate database command
    migrate_parser = subparsers.add_parser("migrate", help="Run database migrations")
    migrate_parser.set_defaults(func=migrate_database)
    
    # Add paper command
    add_paper_parser = subparsers.add_parser("add-paper", help="Add a paper to the database")
    add_paper_parser.add_argument("file_path", help="Path to the markdown file")
    add_paper_parser.add_argument("--arxiv-id", help="ArXiv ID of the paper")
    add_paper_parser.add_argument("--title", help="Title of the paper")
    add_paper_parser.add_argument("--no-content", action="store_true", help="Don't store the content in the database")
    add_paper_parser.set_defaults(func=add_paper)
    
    # Add model command
    add_model_parser = subparsers.add_parser("add-model", help="Add a model to the database")
    add_model_parser.add_argument("name", help="Name of the model")
    add_model_parser.add_argument("provider", help="Provider of the model")
    add_model_parser.add_argument("--context-size", type=int, help="Context size in tokens")
    add_model_parser.add_argument("--version", help="Version of the model")
    add_model_parser.set_defaults(func=add_model)
    
    # List papers command
    list_papers_parser = subparsers.add_parser("list-papers", help="List all papers in the database")
    list_papers_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed information")
    list_papers_parser.set_defaults(func=list_papers)
    
    # List models command
    list_models_parser = subparsers.add_parser("list-models", help="List all models in the database")
    list_models_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed information")
    list_models_parser.set_defaults(func=list_models)
    
    # Process arXiv paper command
    arxiv_parser = subparsers.add_parser("process-arxiv", help="Download and process a paper from arXiv")
    arxiv_parser.add_argument("arxiv_id", help="arXiv ID of the paper")
    arxiv_parser.add_argument("--skip-ocr", action="store_true", help="Skip OCR processing")
    arxiv_parser.add_argument("--run-analysis", action="store_true", help="Run analysis after OCR")
    arxiv_parser.add_argument("--deepseek-runs", type=int, default=0, help="Number of DeepSeek runs")
    arxiv_parser.add_argument("--gemini-runs", type=int, default=0, help="Number of Gemini runs")
    arxiv_parser.add_argument("--output-dir", help="Directory to save outputs to")
    arxiv_parser.set_defaults(func=process_arxiv_paper)
    
    # Migrate publication dates command
    migrate_pub_dates_parser = subparsers.add_parser("migrate-publication-dates", 
                                                     help="Add publication_date column and fetch dates from ArXiv")
    migrate_pub_dates_parser.add_argument("--add-column-only", action="store_true", 
                                         help="Only add the column, don't fetch publication dates")
    migrate_pub_dates_parser.add_argument("--fetch-dates-only", action="store_true", 
                                         help="Only fetch publication dates, assume column exists")
    migrate_pub_dates_parser.set_defaults(func=migrate_publication_dates)
    
    # Discover papers command
    discover_parser = subparsers.add_parser("discover-papers", help="Discover foundational robotics models from arXiv")
    discover_parser.add_argument("--search-terms", nargs="+", 
                                help="Search terms to use")
    discover_parser.add_argument("--categories", nargs="+", default=["cs.RO", "cs.AI", "cs.LG"],
                                help="arXiv categories to search")
    discover_parser.add_argument("--max-results", type=int, default=50,
                                help="Maximum results per search term")
    discover_parser.add_argument("--months", type=int, default=12,
                                help="Date range in months")
    discover_parser.add_argument("--provider", choices=["deepseek", "gemini"], default="deepseek",
                                help="LLM provider for classification")
    discover_parser.add_argument("--confidence", type=float, default=0.7,
                                help="Confidence threshold for positive classification")
    discover_parser.add_argument("--output", help="Output filename for discovered arXiv IDs")
    discover_parser.set_defaults(func=discover_papers)
    
    # Parse arguments and execute command
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    args.func(args)

if __name__ == "__main__":
    main()