#!/usr/bin/env python3
"""
Basic Trend Analysis Example

This script demonstrates how to perform basic trend analysis on extracted fields
from research papers using the refactored trend analysis modules.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from analyser.trend_analysis import TrendAnalyzer, explore_available_fields, get_run_id_ranges
from analyser.config import get_config


def main():
    """Main function demonstrating basic trend analysis."""
    print(" Basic Trend Analysis Example")
    print("=" * 50)
    
    # Initialize the trend analyzer
    config = get_config()
    analyzer = TrendAnalyzer(na_values=config['na_values'])
    
    # Step 1: Explore available data
    print("\n Step 1: Exploring available data...")
    run_info = get_run_id_ranges()
    field_info = explore_available_fields()
    
    # Step 2: Analyze parameters field trends
    print("\n Step 2: Analyzing Parameters field trends...")
    params_df = analyzer.visualize_field_trends(
        field_name='parameters',
        run_id_start=None,  # Use all data
        run_id_end=None,
        figsize=(14, 10),
        show_numeric_trend=True,
        log_scale=True  # Use log scale for parameter counts
    )
    
    if params_df is not None:
        print(f" Successfully analyzed {len(params_df)} parameter extractions")
    
    # Step 3: Analyze architecture field trends
    print("\n️ Step 3: Analyzing Architecture field trends...")
    arch_df = analyzer.visualize_field_trends(
        field_name='architecture',
        run_id_start=None,
        run_id_end=None,
        figsize=(14, 10),
        show_numeric_trend=False,  # Architecture is categorical
        log_scale=False
    )
    
    if arch_df is not None:
        print(f" Successfully analyzed {len(arch_df)} architecture extractions")
    
    # Step 4: Analyze with specific run ID range
    print("\n Step 4: Analyzing specific run ID range...")
    if run_info['total_runs'] > 0:
        # Analyze the most recent 20% of runs
        recent_start = int(run_info['max_run_id'] * 0.8)
        recent_df = analyzer.visualize_field_trends(
            field_name='parameters',
            run_id_start=recent_start,
            run_id_end=run_info['max_run_id'],
            figsize=(12, 8),
            show_numeric_trend=True,
            log_scale=True
        )
        
        if recent_df is not None:
            print(f" Analyzed {len(recent_df)} recent parameter extractions")
    
    print("\n Basic trend analysis completed!")
    print(" You can modify the field names, run ID ranges, and visualization options as needed.")


if __name__ == "__main__":
    main()
