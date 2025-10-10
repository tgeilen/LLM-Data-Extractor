#!/usr/bin/env python3
"""
Demo script showing how to use the papers vs models analysis.
"""

import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyser.domain_analysis import DomainAnalyzer

def main():
    """
    Demonstrate the papers vs models analysis.
    """
    print(" Papers vs Models Analysis Demo")
    print("=" * 50)
    
    # Initialize the analyzer
    analyzer = DomainAnalyzer()
    
    # Run the analysis for all data
    print("\n Analyzing papers vs models by year (all data)...")
    df_all = analyzer.get_papers_vs_models_by_year()
    
    if not df_all.empty:
        print(f"\n Analysis completed successfully!")
        print(f"Data shape: {df_all.shape}")
        print("\nFirst few years:")
        print(df_all.head())
    
    # Example with run ID filtering (adjust ranges as needed)
    print("\n" + "="*50)
    print(" Analyzing papers vs models for specific run ID range...")
    
    # You can adjust these run ID ranges based on your data
    # For example, if you want to analyze only robotics data:
    df_filtered = analyzer.get_papers_vs_models_by_year(
        run_id_start=7866,  # Example start for robotics data
        run_id_end=8087     # Example end for robotics data
    )
    
    if not df_filtered.empty:
        print(f"\n Filtered analysis completed!")
        print(f"Data shape: {df_filtered.shape}")
        print("\nFiltered results:")
        print(df_filtered.head())

if __name__ == "__main__":
    main()
