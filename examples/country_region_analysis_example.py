#!/usr/bin/env python3
"""
Example usage of the new country and region distribution analysis functions.

This example demonstrates how to use the DomainAnalyzer to analyze the
geographical distribution of research organizations over time.
"""

import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyser.domain_analysis import DomainAnalyzer

def main():
    """Run country and region distribution analysis examples."""
    
    print(" Country and Region Distribution Analysis Example")
    print("=" * 60)
    
    # Initialize the analyzer
    analyzer = DomainAnalyzer()
    
    # Example 1: Country Distribution Analysis
    print("\n Running Country Distribution Analysis...")
    print("This will show the top 10 countries by publication count over time")
    print("Each year's bar will total to 100%")
    
    country_df = analyzer.get_country_distribution_analysis(
        run_id_start=None,  # Use all available data
        run_id_end=None,    # Use all available data
        top_k=10,           # Show top 10 countries
        figsize=(15, 10)    # Large figure for better visibility
    )
    
    if not country_df.empty:
        print(f"\n Country analysis completed!")
        print(f"   • Analyzed {len(country_df)} years")
        print(f"   • Top countries: {list(country_df.columns)}")
        
        # Show some statistics
        print(f"\n Country Statistics:")
        for country in country_df.columns:
            avg_percentage = country_df[country].mean()
            print(f"   • {country}: {avg_percentage:.1f}% average")
    
    # Example 2: Region Distribution Analysis
    print("\n\n Running Region Distribution Analysis...")
    print("This will show all regions by publication count over time")
    print("Each year's bar will total to 100%")
    
    region_df = analyzer.get_region_distribution_analysis(
        run_id_start=None,  # Use all available data
        run_id_end=None,    # Use all available data
        figsize=(15, 10)    # Large figure for better visibility
    )
    
    if not region_df.empty:
        print(f"\n Region analysis completed!")
        print(f"   • Analyzed {len(region_df)} years")
        print(f"   • Regions: {list(region_df.columns)}")
        
        # Show some statistics
        print(f"\n Region Statistics:")
        for region in region_df.columns:
            avg_percentage = region_df[region].mean()
            print(f"   • {region}: {avg_percentage:.1f}% average")
    
    print("\n Analysis completed!")
    print("\n Tips:")
    print("   • Use run_id_start and run_id_end to analyze specific time periods")
    print("   • Adjust top_k parameter to show more/fewer countries")
    print("   • The CSV file 'ai_orgs.csv' contains the organization mappings")
    print("   • Organizations with 'n/a' mappings are automatically excluded")

if __name__ == "__main__":
    main()
