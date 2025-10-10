#!/usr/bin/env python3
"""
Quick Insights Analysis

This script provides quick insights for the most important analyses
from the comprehensive analysis plan. Perfect for getting immediate
insights without running the full analysis suite.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from analyser.domain_analysis import DomainAnalyzer
from analyser.trend_analysis import TrendAnalyzer


def main():
    """Run quick insights analysis."""
    print(" Quick Insights Analysis")
    print("=" * 40)
    
    # Initialize analyzers
    domain_analyzer = DomainAnalyzer()
    trend_analyzer = TrendAnalyzer()
    
    print(" Analyzers initialized")
    
    # =============================================================================
    # QUICK INSIGHTS
    # =============================================================================
    
    # 1. Publication Trends (Quick Overview)
    print(f"\n 1. Publication Trends Overview")
    print("-" * 30)
    pub_trends = domain_analyzer.get_publication_trends(
        group_by='year',
        figsize=(12, 6)
    )
    
    # 2. Top Domains
    print(f"\n️ 2. Top Domains (Last 5 Years)")
    print("-" * 30)
    domain_trends = domain_analyzer.get_domain_trends(
        top_k=8,
        figsize=(14, 8)
    )
    
    # 3. Parameter Size Evolution
    print(f"\n 3. Parameter Size Evolution")
    print("-" * 30)
    param_trends = domain_analyzer.get_parameter_size_analysis(
        log_scale=True,
        figsize=(12, 6)
    )
    
    # 4. Robotics Focus
    print(f"\n 4. Robotics Research Trends")
    print("-" * 30)
    robotics_trends = domain_analyzer.get_robotics_trends(
        figsize=(12, 8)
    )
    
    # 5. Top Architectures
    print(f"\n️ 5. Top Architectures")
    print("-" * 30)
    arch_trends = domain_analyzer.get_architecture_trends(
        top_k=8,
        figsize=(14, 8)
    )
    
    # 6. Input Modalities
    print(f"\n 6. Input Modality Trends")
    print("-" * 30)
    input_modalities = domain_analyzer.get_modality_analysis(
        modality_type='input',
        figsize=(14, 8)
    )
    
    print(f"\n Quick insights analysis completed!")
    print(f"\n Key takeaways:")
    print(f"  • Check the visualizations for trends and patterns")
    print(f"  • Look for acceleration in publication rates")
    print(f"  • Identify dominant domains and architectures")
    print(f"  • Note parameter size evolution patterns")
    print(f"  • Observe robotics research development")


if __name__ == "__main__":
    main()
