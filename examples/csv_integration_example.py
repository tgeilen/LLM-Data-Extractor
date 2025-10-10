#!/usr/bin/env python3
"""
CSV Integration Example

This script demonstrates how to process external CSV data and compare it with
database extractions using the refactored modules.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from analyser.csv_processor import CSVProcessor
from analyser.trend_analysis import TrendAnalyzer
from analyser.config import get_config


def main():
    """Main function demonstrating CSV integration."""
    print(" CSV Integration Example")
    print("=" * 50)
    
    # Initialize processors
    config = get_config()
    csv_processor = CSVProcessor(na_values=config['na_values'])
    analyzer = TrendAnalyzer(na_values=config['na_values'])
    
    # Step 1: Explore CSV structure
    csv_file_path = "Epoch Database - Notable Models.csv"
    
    if not Path(csv_file_path).exists():
        print(f" CSV file not found: {csv_file_path}")
        print(" Please ensure the CSV file exists in the current directory")
        return
    
    print(f"\n Step 1: Exploring CSV structure...")
    csv_structure = csv_processor.explore_csv_structure(csv_file_path, show_sample_rows=3)
    
    if csv_structure is None:
        print(" Failed to load CSV file")
        return
    
    # Step 2: Preview ArXiv ID extraction
    print(f"\n Step 2: Previewing ArXiv ID extraction...")
    arxiv_ids = csv_processor.extract_arxiv_ids_preview(csv_file_path, max_examples=5)
    
    if not arxiv_ids:
        print(" No ArXiv IDs found in the CSV file")
        return
    
    # Step 3: Process CSV and match with database
    print(f"\n️ Step 3: Processing CSV and matching with database...")
    csv_data = csv_processor.process_csv_with_arxiv_lookup(
        csv_file_path=csv_file_path,
        link_column='Link',
        parameters_column='Parameters'
    )
    
    if csv_data is None or csv_data.empty:
        print(" No data was processed from CSV")
        return
    
    print(f" Successfully processed CSV data!")
    print(f" Final dataset shape: {csv_data.shape}")
    print(f" Date range: {csv_data['publication_date'].min()} to {csv_data['publication_date'].max()}")
    
    # Step 4: Compare with database extractions
    print(f"\n Step 4: Comparing with database extractions...")
    
    # Get recent database extractions for comparison
    db_data = analyzer._get_field_data('parameters', run_id_start=None, run_id_end=None)
    
    if db_data is not None and not db_data.empty:
        print(f" Database extractions: {len(db_data)} records")
        print(f" CSV data: {len(csv_data)} records")
        
        # Find overlapping papers
        csv_arxiv_ids = set(csv_data['arxiv_id'])
        db_arxiv_ids = set(db_data['arxiv_id'])
        overlap = csv_arxiv_ids & db_arxiv_ids
        
        print(f"\n Paper Overlap Analysis:")
        print(f"  • Papers in both datasets: {len(overlap)}")
        print(f"  • CSV-only papers: {len(csv_arxiv_ids - db_arxiv_ids)}")
        print(f"  • Database-only papers: {len(db_arxiv_ids - csv_arxiv_ids)}")
        
        # Show some statistics
        print(f"\n Quick Statistics:")
        print(f"  • CSV papers with parameters: {csv_data['parameters'].notna().sum()}")
        print(f"  • Database papers with parameters: {db_data['value'].notna().sum()}")
        
        # Show sample of overlapping papers
        if overlap:
            print(f"\n Sample overlapping papers:")
            overlap_sample = list(overlap)[:5]
            for arxiv_id in overlap_sample:
                csv_row = csv_data[csv_data['arxiv_id'] == arxiv_id].iloc[0]
                db_row = db_data[db_data['arxiv_id'] == arxiv_id].iloc[0]
                print(f"  • {arxiv_id}: CSV='{csv_row['parameters']}' | DB='{db_row['value']}'")
    else:
        print(" No database extractions found for comparison")
    
    print("\n CSV integration example completed!")
    print(" You can now use the processed data for further analysis and visualization.")


if __name__ == "__main__":
    main()
