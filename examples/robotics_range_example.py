#!/usr/bin/env python3
"""
Example: Custom Robotics Range Analysis

This script demonstrates how to set custom run ID ranges specifically for robotics analysis.
"""

from analyser.domain_analysis import DomainAnalyzer
from analyser.trend_analysis import get_run_id_ranges

def main():
    # Initialize analyzer
    domain_analyzer = DomainAnalyzer()
    
    # Get available run ID information
    run_info = get_run_id_ranges()
    print(" Available Run ID Information:")
    print(f"  • Run ID range: {run_info['min_run_id']} - {run_info['max_run_id']}")
    print(f"  • Total runs: {run_info['total_runs']:,}")
    print("=" * 60)
    
    # Example 1: Analyze recent robotics data (last 500 runs)
    print("\n Example 1: Recent Robotics Data (Last 500 Runs)")
    print("-" * 50)
    
    recent_start = run_info['max_run_id'] - 500
    recent_end = run_info['max_run_id']
    
    robot_types_recent = domain_analyzer.get_robot_type_analysis(
        run_id_start=recent_start,
        run_id_end=recent_end,
        include_temporal=False,  # Skip temporal for quick demo
        figsize=(12, 6)
    )
    
    if not robot_types_recent.empty:
        print(f" Found {len(robot_types_recent)} robot types in recent data")
        print(f" Top robot type: {robot_types_recent.iloc[0]['robot_type']} ({robot_types_recent.iloc[0]['count']} models)")
    
    # Example 2: Analyze early robotics data (first 1000 runs)
    print("\n Example 2: Early Robotics Data (First 1000 Runs)")
    print("-" * 50)
    
    early_start = 1
    early_end = 1000
    
    robot_types_early = domain_analyzer.get_robot_type_analysis(
        run_id_start=early_start,
        run_id_end=early_end,
        include_temporal=False,
        figsize=(12, 6)
    )
    
    if not robot_types_early.empty:
        print(f" Found {len(robot_types_early)} robot types in early data")
        print(f" Top robot type: {robot_types_early.iloc[0]['robot_type']} ({robot_types_early.iloc[0]['count']} models)")
    
    # Example 3: Analyze specific robotics range (runs 8000-8500)
    print("\n Example 3: Specific Robotics Range (Runs 8000-8500)")
    print("-" * 50)
    
    specific_start = 8000
    specific_end = 8500
    
    robot_types_specific = domain_analyzer.get_robot_type_analysis(
        run_id_start=specific_start,
        run_id_end=specific_end,
        include_temporal=False,
        figsize=(12, 6)
    )
    
    if not robot_types_specific.empty:
        print(f" Found {len(robot_types_specific)} robot types in specific range")
        print(f" Top robot type: {robot_types_specific.iloc[0]['robot_type']} ({robot_types_specific.iloc[0]['count']} models)")
    
    # Example 4: Compare different robotics ranges
    print("\n Example 4: Compare Different Robotics Ranges")
    print("-" * 50)
    
    ranges = [
        (1, 2000, "Early period"),
        (2000, 5000, "Middle period"),
        (5000, 8000, "Recent period"),
        (8000, run_info['max_run_id'], "Latest period")
    ]
    
    for start, end, label in ranges:
        print(f"\n {label} (runs {start}-{end}):")
        
        # Robot type analysis
        robot_types = domain_analyzer.get_robot_type_analysis(
            run_id_start=start,
            run_id_end=end,
            include_temporal=False,
            figsize=(10, 5)
        )
        
        if not robot_types.empty:
            print(f"   Robot types: {len(robot_types)}")
            if len(robot_types) > 0:
                top_type = robot_types.iloc[0]['robot_type']
                top_count = robot_types.iloc[0]['count']
                print(f"   Top type: {top_type} ({top_count} models)")
        
        # Control type analysis
        control_types = domain_analyzer.get_control_type_analysis(
            run_id_start=start,
            run_id_end=end,
            figsize=(8, 5)
        )
        
        if not control_types.empty:
            print(f"   Control types: {len(control_types)}")
            if len(control_types) > 0:
                top_control = control_types.iloc[0]['control_type']
                top_count = control_types.iloc[0]['count']
                print(f"   Top control: {top_control} ({top_count} models)")
    
    # Example 5: Single run analysis
    print("\n Example 5: Single Run Analysis")
    print("-" * 50)
    
    single_run_id = 8000
    
    single_run_analysis = domain_analyzer.get_robot_type_analysis(
        run_id_start=single_run_id,
        run_id_end=single_run_id,
        include_temporal=False,
        figsize=(8, 4)
    )
    
    if not single_run_analysis.empty:
        print(f" Single run {single_run_id} analysis completed")
        print(f" Found {len(single_run_analysis)} robot types in this run")
    else:
        print(f"️ No robotics data found in run {single_run_id}")
    
    print("\n Robotics range analysis examples completed!")
    print("=" * 60)
    
    print("\n Key Points:")
    print("  • All robotics analysis methods support run_id_start and run_id_end parameters")
    print("  • You can analyze any range of runs, not just the default robotics range")
    print("  • Use get_run_id_ranges() to see available data ranges")
    print("  • Compare different time periods to see robotics evolution")
    print("  • Single run analysis helps debug specific extraction runs")

def demonstrate_robotics_modality_ranges():
    """Demonstrate robotics modality analysis with different ranges"""
    print("\n Robotics Modality Analysis with Different Ranges")
    print("=" * 60)
    
    domain_analyzer = DomainAnalyzer()
    
    # Analyze modalities in different ranges
    modality_ranges = [
        (1, 3000, "Early robotics"),
        (3000, 6000, "Middle robotics"),
        (6000, 9000, "Recent robotics")
    ]
    
    for start, end, label in modality_ranges:
        print(f"\n {label} (runs {start}-{end}):")
        
        # Robotics modality analysis
        modalities = domain_analyzer.get_robotics_modality_analysis(
            run_id_start=start,
            run_id_end=end,
            top_k=5,
            figsize=(12, 8)
        )
        
        if not modalities.empty:
            input_modalities = modalities[modalities['modality_type'] == 'input']
            sensor_modalities = modalities[modalities['modality_type'] == 'sensor']
            
            print(f"   Input modalities: {len(input_modalities['modality'].unique())}")
            print(f"   Sensor modalities: {len(sensor_modalities['modality'].unique())}")
            
            if not input_modalities.empty:
                top_input = input_modalities.groupby('modality')['count'].sum().nlargest(3)
                print(f"   Top input modalities:")
                for i, (modality, count) in enumerate(top_input.items(), 1):
                    print(f"    {i}. {modality}: {count} models")
            
            if not sensor_modalities.empty:
                top_sensor = sensor_modalities.groupby('modality')['count'].sum().nlargest(3)
                print(f"   Top sensor modalities:")
                for i, (modality, count) in enumerate(top_sensor.items(), 1):
                    print(f"    {i}. {modality}: {count} models")

if __name__ == "__main__":
    main()
    demonstrate_robotics_modality_ranges()
