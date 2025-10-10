#!/usr/bin/env python3
"""
Comprehensive Domain Analysis Example

This script demonstrates how to perform all the domain-specific analyses
requested in the analysis plan, including publication trends, model size
analysis, modality analysis, and architecture trends.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from analyser.domain_analysis import DomainAnalyzer, create_domain_modality_matrix, create_domain_architecture_matrix
from analyser.trend_analysis import TrendAnalyzer
from analyser.config import get_config


def main():
    """Run comprehensive domain analysis."""
    print(" Comprehensive Domain Analysis")
    print("=" * 50)
    
    # Initialize analyzers
    domain_analyzer = DomainAnalyzer()
    trend_analyzer = TrendAnalyzer()
    
    print(" Analyzers initialized successfully")
    
    # Get configuration
    config = get_config()
    print(f" Using configuration with {len(config['na_values'])} N/A value patterns")
    
    # Define analysis parameters
    run_id_start = None  # Use all data
    run_id_end = None    # Use all data
    
    print(f"\n Analysis Parameters:")
    print(f"  • Run ID range: {run_id_start or 'All'} - {run_id_end or 'All'}")
    print(f"  • Date range: 2010-2025 (full dataset)")
    
    # =============================================================================
    # 1. PUBLICATION TRENDS ANALYSIS
    # =============================================================================
    print(f"\n" + "="*60)
    print(" 1. PUBLICATION TRENDS ANALYSIS")
    print("="*60)
    
    # 1a) Publication trends over time (Histogram)
    print(f"\n 1a) Publication Trends Over Time")
    print("-" * 40)
    pub_trends = domain_analyzer.get_publication_trends(
        run_id_start=run_id_start,
        run_id_end=run_id_end,
        group_by='year',
        figsize=(14, 8)
    )
    
    # 1b) Domain trends (Stacked column chart)
    print(f"\n 1b) Domain Trends Over Time (Top 10 Domains)")
    print("-" * 40)
    domain_trends = domain_analyzer.get_domain_trends(
        run_id_start=run_id_start,
        run_id_end=run_id_end,
        top_k=10,
        figsize=(16, 10)
    )
    
    # 1c) Robotics focus
    print(f"\n 1c) Robotics Research Trends")
    print("-" * 40)
    robotics_trends = domain_analyzer.get_robotics_trends(
        run_id_start=run_id_start,
        run_id_end=run_id_end,
        figsize=(14, 10)
    )
    
    # =============================================================================
    # 2. MODEL SIZE ANALYSIS
    # =============================================================================
    print(f"\n" + "="*60)
    print(" 2. MODEL SIZE ANALYSIS")
    print("="*60)
    
    # 2a) Parameter size over time (Scatter plot)
    print(f"\n 2a) Parameter Size Trends Over Time")
    print("-" * 40)
    param_trends = domain_analyzer.get_parameter_size_analysis(
        run_id_start=run_id_start,
        run_id_end=run_id_end,
        log_scale=True,
        figsize=(14, 8)
    )
    
    # 2b) Domain parameter comparison
    print(f"\n 2b) Parameter Size by Domain (Box Plot)")
    print("-" * 40)
    domain_param_comparison = domain_analyzer.get_domain_parameter_comparison(
        run_id_start=run_id_start,
        run_id_end=run_id_end,
        top_domains=10,
        figsize=(16, 10)
    )
    
    # 2c) Modality parameter analysis
    print(f"\n 2c) Parameter Size by Input Modality")
    print("-" * 40)
    input_modality_param = analyze_modality_parameters(
        trend_analyzer, 'input_modality', run_id_start, run_id_end
    )
    
    print(f"\n 2d) Parameter Size by Output Modality")
    print("-" * 40)
    output_modality_param = analyze_modality_parameters(
        trend_analyzer, 'output_modality', run_id_start, run_id_end
    )
    
    # 2e) Architecture parameter analysis
    print(f"\n 2e) Parameter Size by Architecture")
    print("-" * 40)
    arch_param = analyze_architecture_parameters(
        trend_analyzer, run_id_start, run_id_end
    )
    
    # =============================================================================
    # 3. MODALITY ANALYSIS
    # =============================================================================
    print(f"\n" + "="*60)
    print(" 3. MODALITY ANALYSIS")
    print("="*60)
    
    # 3a) Input modality trends
    print(f"\n 3a) Input Modality Trends Over Time")
    print("-" * 40)
    input_modality_trends = domain_analyzer.get_modality_analysis(
        run_id_start=run_id_start,
        run_id_end=run_id_end,
        modality_type='input',
        figsize=(16, 10)
    )
    
    # 3b) Output modality trends
    print(f"\n 3b) Output Modality Trends Over Time")
    print("-" * 40)
    output_modality_trends = domain_analyzer.get_modality_analysis(
        run_id_start=run_id_start,
        run_id_end=run_id_end,
        modality_type='output',
        figsize=(16, 10)
    )
    
    # 3c) Domain-Modality matrices
    print(f"\n 3c) Domain-Input Modality Matrix")
    print("-" * 40)
    domain_input_matrix = create_domain_modality_matrix(
        domain_analyzer, run_id_start, run_id_end, 'input', top_k_domains=8, top_k_modalities=8, figsize=(14, 10)
    )
    
    print(f"\n 3d) Domain-Output Modality Matrix")
    print("-" * 40)
    domain_output_matrix = create_domain_modality_matrix(
        domain_analyzer, run_id_start, run_id_end, 'output', top_k_domains=8, top_k_modalities=8, figsize=(14, 10)
    )
    
    # =============================================================================
    # 4. ARCHITECTURE ANALYSIS
    # =============================================================================
    print(f"\n" + "="*60)
    print("️ 4. ARCHITECTURE ANALYSIS")
    print("="*60)
    
    # 4a) Architecture trends over time
    print(f"\n 4a) Architecture Trends Over Time")
    print("-" * 40)
    architecture_trends = domain_analyzer.get_architecture_trends(
        run_id_start=run_id_start,
        run_id_end=run_id_end,
        top_k=10,
        figsize=(16, 10)
    )
    
    # 4b) Domain-Architecture matrix
    print(f"\n 4b) Domain-Architecture Matrix")
    print("-" * 40)
    domain_arch_matrix = create_domain_architecture_matrix(
        domain_analyzer, run_id_start, run_id_end, top_k_domains=8, top_k_architectures=8, figsize=(14, 10)
    )
    
    # =============================================================================
    # SUMMARY
    # =============================================================================
    print(f"\n" + "="*60)
    print(" ANALYSIS SUMMARY")
    print("="*60)
    
    print(f"\n Completed Analyses:")
    print(f"   Publication Trends: {len(pub_trends) if not pub_trends.empty else 0} time periods")
    print(f"  ️ Domain Trends: {len(domain_trends) if not domain_trends.empty else 0} domains analyzed")
    print(f"   Robotics Trends: {len(robotics_trends) if not robotics_trends.empty else 0} years")
    print(f"   Parameter Analysis: {len(param_trends) if param_trends is not None else 0} models")
    print(f"   Modality Analysis: Input & Output trends")
    print(f"  ️ Architecture Analysis: {len(architecture_trends) if not architecture_trends.empty else 0} architectures")
    
    print(f"\n Key Insights Generated:")
    print(f"  • Publication acceleration patterns")
    print(f"  • Domain focus shifts over time")
    print(f"  • Robotics research development timeline")
    print(f"  • Parameter size evolution trends")
    print(f"  • Modality adoption patterns")
    print(f"  • Architecture preference changes")
    
    print(f"\n Next Steps:")
    print(f"  • Review generated visualizations")
    print(f"  • Export data for further analysis")
    print(f"  • Create custom analysis scripts")
    print(f"  • Integrate with external datasets")
    
    print(f"\n Comprehensive domain analysis completed successfully!")


def analyze_modality_parameters(trend_analyzer, modality_field, run_id_start, run_id_end):
    """Analyze parameter sizes by modality."""
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    # Get parameter data with modality information
    param_df = trend_analyzer._get_field_data('parameters', run_id_start, run_id_end)
    if param_df is None or param_df.empty:
        print(f" No parameter data found for {modality_field}")
        return None
    
    # Get modality data
    modality_df = trend_analyzer._get_field_data(modality_field, run_id_start, run_id_end)
    if modality_df is None or modality_df.empty:
        print(f" No {modality_field} data found")
        return None
    
    # Merge data on run_id
    merged_df = param_df.merge(modality_df, on='run_id', suffixes=('_param', '_modality'))
    
    # Extract numeric values
    merged_df['numeric_value'] = merged_df['value_param'].apply(trend_analyzer._extract_numeric)
    merged_df = merged_df[merged_df['numeric_value'].notna()]
    
    if merged_df.empty:
        print(f" No numeric parameter values found for {modality_field}")
        return None
    
    # Get top modalities
    modality_counts = merged_df['value_modality'].value_counts()
    top_modalities = modality_counts.head(8).index.tolist()
    merged_top = merged_df[merged_df['value_modality'].isin(top_modalities)]
    
    # Create box plot
    fig, ax = plt.subplots(figsize=(14, 8))
    merged_top.boxplot(column='numeric_value', by='value_modality', ax=ax)
    ax.set_yscale('log')
    ax.set_xlabel(f'{modality_field.replace("_", " ").title()}')
    ax.set_ylabel('Parameter Count (log scale)')
    ax.set_title(f'Parameter Size Distribution by {modality_field.replace("_", " ").title()}')
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()
    
    # Print statistics
    modality_stats = merged_top.groupby('value_modality')['numeric_value'].agg([
        'count', 'mean', 'median', 'std'
    ]).round(0)
    
    print(f" {modality_field.replace('_', ' ').title()} Parameter Statistics:")
    print(modality_stats)
    
    return merged_top


def analyze_architecture_parameters(trend_analyzer, run_id_start, run_id_end):
    """Analyze parameter sizes by architecture."""
    import pandas as pd
    import matplotlib.pyplot as plt
    
    # Get parameter data with architecture information
    param_df = trend_analyzer._get_field_data('parameters', run_id_start, run_id_end)
    if param_df is None or param_df.empty:
        print(" No parameter data found")
        return None
    
    # Get architecture data
    arch_df = trend_analyzer._get_field_data('architecture', run_id_start, run_id_end)
    if arch_df is None or arch_df.empty:
        print(" No architecture data found")
        return None
    
    # Merge data on run_id
    merged_df = param_df.merge(arch_df, on='run_id', suffixes=('_param', '_arch'))
    
    # Extract numeric values
    merged_df['numeric_value'] = merged_df['value_param'].apply(trend_analyzer._extract_numeric)
    merged_df = merged_df[merged_df['numeric_value'].notna()]
    
    if merged_df.empty:
        print(" No numeric parameter values found")
        return None
    
    # Get top architectures
    arch_counts = merged_df['value_arch'].value_counts()
    top_architectures = arch_counts.head(8).index.tolist()
    merged_top = merged_df[merged_df['value_arch'].isin(top_architectures)]
    
    # Create box plot
    fig, ax = plt.subplots(figsize=(14, 8))
    merged_top.boxplot(column='numeric_value', by='value_arch', ax=ax)
    ax.set_yscale('log')
    ax.set_xlabel('Architecture')
    ax.set_ylabel('Parameter Count (log scale)')
    ax.set_title('Parameter Size Distribution by Architecture')
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()
    
    # Print statistics
    arch_stats = merged_top.groupby('value_arch')['numeric_value'].agg([
        'count', 'mean', 'median', 'std'
    ]).round(0)
    
    print(" Architecture Parameter Statistics:")
    print(arch_stats)
    
    return merged_top


if __name__ == "__main__":
    main()
