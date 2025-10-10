#!/usr/bin/env python3
"""
Test script for the enhanced get_organization_analysis method.

This script demonstrates the new functionality:
1) count_type='models' - Count of models only
2) count_type='papers' - Count of papers only  
3) count_type='both' - Side-by-side comparison with orange and blue bars
"""

import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analyser.domain_analysis import DomainAnalyzer

def test_enhanced_organization_analysis():
    """Test the enhanced organization analysis functionality."""
    print(" Testing Enhanced Organization Analysis")
    print("=" * 60)
    
    # Initialize the analyzer
    analyzer = DomainAnalyzer()
    
    # Test cases
    test_cases = [
        {
            'name': 'Models Only',
            'params': {
                'count_type': 'models',
                'top_k': 10,
                'figsize': (12, 8)
            }
        },
        {
            'name': 'Papers Only', 
            'params': {
                'count_type': 'papers',
                'top_k': 10,
                'figsize': (12, 8)
            }
        },
        {
            'name': 'Both (sorted by models)',
            'params': {
                'count_type': 'both',
                'sort_by': 'models',
                'top_k': 10,
                'figsize': (14, 8)
            }
        },
        {
            'name': 'Both (sorted by papers)',
            'params': {
                'count_type': 'both', 
                'sort_by': 'papers',
                'top_k': 10,
                'figsize': (14, 8)
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n Test {i}: {test_case['name']}")
        print("-" * 40)
        
        try:
            result_df = analyzer.get_organization_analysis(**test_case['params'])
            
            if not result_df.empty:
                print(f" Success! Returned DataFrame with {len(result_df)} organizations")
                print(f" Columns: {list(result_df.columns)}")
                
                # Show first few rows
                print("\n Top 3 organizations:")
                for idx, (_, row) in enumerate(result_df.head(3).iterrows(), 1):
                    if 'models_count' in result_df.columns and 'papers_count' in result_df.columns:
                        print(f"  {idx}. {row['organization']}: {row['models_count']} models, {row['papers_count']} papers")
                    elif 'models_count' in result_df.columns:
                        print(f"  {idx}. {row['organization']}: {row['models_count']} models")
                    elif 'papers_count' in result_df.columns:
                        print(f"  {idx}. {row['organization']}: {row['papers_count']} papers")
            else:
                print(" Test failed - empty DataFrame returned")
                
        except Exception as e:
            print(f" Test failed with error: {e}")
    
    print("\n Testing completed!")

if __name__ == "__main__":
    test_enhanced_organization_analysis()




