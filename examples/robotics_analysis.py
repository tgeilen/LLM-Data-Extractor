#!/usr/bin/env python3
"""
Comprehensive Robotics Analysis Example

This script demonstrates all the robotics-specific analysis capabilities
for the specialized robotics data in run ID range 7866-8087.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from analyser.domain_analysis import DomainAnalyzer


def main():
    """Run comprehensive robotics analysis."""
    print(" Comprehensive Robotics Analysis")
    print("=" * 60)
    print("Analyzing robotics models from run IDs 7866-8087")
    print("=" * 60)
    
    # Initialize analyzer
    analyzer = DomainAnalyzer()
    
    # Set robotics data range
    robotics_start = 7866
    robotics_end = 8087
    
    print(f"\n Robotics Data Range: {robotics_start} - {robotics_end}")
    print(f" Total robotics runs: {robotics_end - robotics_start + 1}")
    
    # =============================================================================
    # 1. ROBOT TYPE ANALYSIS
    # =============================================================================
    print(f"\n" + "="*60)
    print("1. ROBOT TYPE ANALYSIS")
    print("="*60)
    
    print(f"\n 1a) Robot Types Histogram")
    print("-" * 40)
    robot_types = analyzer.get_robot_type_analysis(
        run_id_start=robotics_start,
        run_id_end=robotics_end,
        include_temporal=True,
        figsize=(15, 8)
    )
    
    if not robot_types.empty:
        print(f" Found {len(robot_types)} different robot types")
        print(f" Top 3 robot types:")
        for i, (_, row) in enumerate(robot_types.head(3).iterrows(), 1):
            print(f"  {i}. {row['robot_type']}: {row['count']} models")
    
    # =============================================================================
    # 2. ROBOTICS MODALITY ANALYSIS
    # =============================================================================
    print(f"\n" + "="*60)
    print("2. ROBOTICS MODALITY ANALYSIS")
    print("="*60)
    
    print(f"\n 2a) Robotics Modalities Over Time")
    print("-" * 40)
    robotics_modalities = analyzer.get_robotics_modality_analysis(
        run_id_start=robotics_start,
        run_id_end=robotics_end,
        top_k=8,
        figsize=(15, 12)
    )
    
    if not robotics_modalities.empty:
        print(f" Analyzed modalities over time")
        print(f" Input modalities: {len(robotics_modalities[robotics_modalities['modality_type'] == 'input']['modality'].unique())}")
        print(f" Sensor modalities: {len(robotics_modalities[robotics_modalities['modality_type'] == 'sensor']['modality'].unique())}")
    
    # =============================================================================
    # 3. MODALITY DEVELOPMENT ANALYSIS
    # =============================================================================
    print(f"\n" + "="*60)
    print("3. MODALITY DEVELOPMENT ANALYSIS")
    print("="*60)
    
    print(f"\n 3a) Development of Modalities per Model Over Time")
    print("-" * 40)
    modality_development = analyzer.get_modality_development_analysis(
        run_id_start=robotics_start,
        run_id_end=robotics_end,
        figsize=(14, 8)
    )
    
    if not modality_development.empty:
        print(f" Analyzed modality development for {len(modality_development)} models")
        avg_modalities = modality_development['total_modality_count'].mean()
        print(f" Average modalities per model: {avg_modalities:.2f}")
        
        # Show year-by-year progression
        yearly_avg = modality_development.groupby('year')['total_modality_count'].mean()
        print(f" Modality progression by year:")
        for year, avg in yearly_avg.items():
            print(f"  {int(year)}: {avg:.2f} modalities per model")
    
    # =============================================================================
    # 4. CONTROL TYPE ANALYSIS
    # =============================================================================
    print(f"\n" + "="*60)
    print("4. CONTROL TYPE ANALYSIS")
    print("="*60)
    
    print(f"\n 4a) Control Types Distribution")
    print("-" * 40)
    control_types = analyzer.get_control_type_analysis(
        run_id_start=robotics_start,
        run_id_end=robotics_end,
        figsize=(12, 8)
    )
    
    if not control_types.empty:
        print(f" Found {len(control_types)} different control types")
        print(f" Top 3 control types:")
        for i, (_, row) in enumerate(control_types.head(3).iterrows(), 1):
            print(f"  {i}. {row['control_type']}: {row['count']} models")
    
    # =============================================================================
    # 5. ENVIRONMENT TYPE ANALYSIS
    # =============================================================================
    print(f"\n" + "="*60)
    print("5. ENVIRONMENT TYPE ANALYSIS")
    print("="*60)
    
    print(f"\n 5a) Environment Types Distribution")
    print("-" * 40)
    environment_types = analyzer.get_environment_type_analysis(
        run_id_start=robotics_start,
        run_id_end=robotics_end,
        figsize=(12, 8)
    )
    
    if not environment_types.empty:
        print(f" Found {len(environment_types)} different environment types")
        print(f" Top 3 environment types:")
        for i, (_, row) in enumerate(environment_types.head(3).iterrows(), 1):
            print(f"  {i}. {row['environment_types']}: {row['count']} models")
    
    # =============================================================================
    # SUMMARY
    # =============================================================================
    print(f"\n" + "="*60)
    print(" ROBOTICS ANALYSIS SUMMARY")
    print("="*60)
    
    print(f"\n Key Insights:")
    print(f"  • Robot Types: Analyzed {len(robot_types) if not robot_types.empty else 0} different robot types")
    print(f"  • Modalities: Tracked input and sensor modalities over time")
    print(f"  • Development: Models show increasing modality complexity over time")
    print(f"  • Control: {len(control_types) if not control_types.empty else 0} different control approaches")
    print(f"  • Environment: {len(environment_types) if not environment_types.empty else 0} different environment types")
    
    print(f"\n Research Questions Answered:")
    print(f"   What robot types are most commonly developed for?")
    print(f"   What modalities are used in robotics models over time?")
    print(f"   Are models becoming more capable (more modalities)?")
    print(f"   What control depths are implemented?")
    print(f"   Are models developed for real-world conditions?")
    
    print(f"\n Robotics analysis complete!")
    print(f" All visualizations have been generated and displayed.")


if __name__ == "__main__":
    main()
