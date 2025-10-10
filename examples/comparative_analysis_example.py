#!/usr/bin/env python3
"""
Comparative Analysis Example

This script demonstrates how to compare trends between different run ID ranges
and external CSV data using the refactored modules.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from analyser.trend_analysis import TrendAnalyzer, get_run_id_ranges
from analyser.csv_processor import CSVProcessor
from analyser.config import get_config


def compare_two_ranges(
    analyzer: TrendAnalyzer,
    field_name: str,
    range1_start: int,
    range1_end: int,
    range1_label: str,
    range2_start: int,
    range2_end: int,
    range2_label: str,
    log_scale: bool = True
):
    """
    Compare trends between two run ID ranges.
    
    Args:
        analyzer: TrendAnalyzer instance
        field_name: Field to analyze
        range1_start/end: First range parameters
        range1_label: Label for first range
        range2_start/end: Second range parameters  
        range2_label: Label for second range
        log_scale: Whether to use logarithmic scale
    """
    print(f"\n Comparing {range1_label} vs {range2_label}")
    print("=" * 60)
    
    # Get data for both ranges
    range1_data = analyzer._get_field_data(field_name, range1_start, range1_end)
    range2_data = analyzer._get_field_data(field_name, range2_start, range2_end)
    
    if range1_data is None or range2_data is None:
        print(" Could not retrieve data for one or both ranges")
        return None, None
    
    print(f" {range1_label}: {len(range1_data)} records")
    print(f" {range2_label}: {len(range2_data)} records")
    
    # Analyze each range separately
    print(f"\n Analyzing {range1_label}...")
    analyzer.visualize_field_trends(
        field_name=field_name,
        run_id_start=range1_start,
        run_id_end=range1_end,
        figsize=(14, 10),
        show_numeric_trend=True,
        log_scale=log_scale
    )
    
    print(f"\n Analyzing {range2_label}...")
    analyzer.visualize_field_trends(
        field_name=field_name,
        run_id_start=range2_start,
        run_id_end=range2_end,
        figsize=(14, 10),
        show_numeric_trend=True,
        log_scale=log_scale
    )
    
    # Calculate overlap
    range1_arxiv_ids = set(range1_data['arxiv_id'])
    range2_arxiv_ids = set(range2_data['arxiv_id'])
    overlap = range1_arxiv_ids & range2_arxiv_ids
    
    print(f"\n Overlap Analysis:")
    print(f"  • Papers in both ranges: {len(overlap)}")
    print(f"  • {range1_label}-only: {len(range1_arxiv_ids - range2_arxiv_ids)}")
    print(f"  • {range2_label}-only: {len(range2_arxiv_ids - range1_arxiv_ids)}")
    
    return range1_data, range2_data


def main():
    """Main function demonstrating comparative analysis."""
    print(" Comparative Analysis Example")
    print("=" * 50)
    
    # Initialize processors
    config = get_config()
    analyzer = TrendAnalyzer(na_values=config['na_values'])
    csv_processor = CSVProcessor(na_values=config['na_values'])
    
    # Get run ID information
    run_info = get_run_id_ranges()
    
    if run_info['total_runs'] == 0:
        print(" No extraction runs found in database")
        return
    
    # Example 1: Compare early vs recent extractions
    print("\n Example 1: Early vs Recent Parameter Extractions")
    
    # Define ranges (adjust these based on your data)
    total_runs = run_info['max_run_id'] - run_info['min_run_id']
    early_end = run_info['min_run_id'] + int(total_runs * 0.3)
    recent_start = run_info['min_run_id'] + int(total_runs * 0.7)
    
    early_data, recent_data = compare_two_ranges(
        analyzer=analyzer,
        field_name='parameters',
        range1_start=run_info['min_run_id'],
        range1_end=early_end,
        range1_label="Early Extractions",
        range2_start=recent_start,
        range2_end=run_info['max_run_id'],
        range2_label="Recent Extractions",
        log_scale=True
    )
    
    # Example 2: Compare different extraction batches
    print("\n Example 2: Different Extraction Batches")
    
    # Define two different ranges (adjust based on your data)
    batch1_start = run_info['min_run_id']
    batch1_end = run_info['min_run_id'] + int(total_runs * 0.4)
    batch2_start = run_info['min_run_id'] + int(total_runs * 0.4)
    batch2_end = run_info['min_run_id'] + int(total_runs * 0.8)
    
    batch1_data, batch2_data = compare_two_ranges(
        analyzer=analyzer,
        field_name='architecture',
        range1_start=batch1_start,
        range1_end=batch1_end,
        range1_label="Batch 1",
        range2_start=batch2_start,
        range2_end=batch2_end,
        range2_label="Batch 2",
        log_scale=False  # Architecture is categorical
    )
    
    # Example 3: CSV integration comparison
    print("\n Example 3: CSV Integration Comparison")
    
    csv_file_path = "Epoch Database - Notable Models.csv"
    if Path(csv_file_path).exists():
        print(f" Processing CSV file: {csv_file_path}")
        
        csv_data = csv_processor.process_csv_with_arxiv_lookup(
            csv_file_path=csv_file_path,
            link_column='Link',
            parameters_column='Parameters'
        )
        
        if csv_data is not None and not csv_data.empty:
            print(f" CSV data processed: {len(csv_data)} papers")
            
            # Compare with recent database extractions
            recent_db_data = analyzer._get_field_data(
                'parameters',
                run_id_start=recent_start,
                run_id_end=run_info['max_run_id']
            )
            
            if recent_db_data is not None:
                print(f" Recent DB data: {len(recent_db_data)} papers")
                
                # Find overlap
                csv_arxiv_ids = set(csv_data['arxiv_id'])
                db_arxiv_ids = set(recent_db_data['arxiv_id'])
                overlap = csv_arxiv_ids & db_arxiv_ids
                
                print(f"\n CSV vs Database Overlap:")
                print(f"  • Papers in both: {len(overlap)}")
                print(f"  • CSV-only: {len(csv_arxiv_ids - db_arxiv_ids)}")
                print(f"  • Database-only: {len(db_arxiv_ids - csv_arxiv_ids)}")
                
                # Show some sample comparisons
                if overlap:
                    print(f"\n Sample Parameter Comparisons:")
                    overlap_sample = list(overlap)[:3]
                    for arxiv_id in overlap_sample:
                        csv_row = csv_data[csv_data['arxiv_id'] == arxiv_id].iloc[0]
                        db_row = recent_db_data[recent_db_data['arxiv_id'] == arxiv_id].iloc[0]
                        print(f"  • {arxiv_id}:")
                        print(f"    CSV: {csv_row['parameters']}")
                        print(f"    DB:  {db_row['value']}")
        else:
            print(" Failed to process CSV data")
    else:
        print(f"️ CSV file not found: {csv_file_path}")
        print(" Skipping CSV comparison example")
    
    print("\n Comparative analysis example completed!")
    print(" You can modify the run ID ranges and field names to analyze different aspects of your data.")


if __name__ == "__main__":
    main()
