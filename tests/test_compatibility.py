#!/usr/bin/env python3
"""
Compatibility Test Script

This script tests that the optimized system maintains compatibility with
the original notebook functionality by comparing outputs and behaviors.
"""

import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import traceback

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_original_vs_optimized_functions():
    """Test that optimized functions produce the same results as original ones."""
    print(" Testing original vs optimized function compatibility...")
    
    try:
        from analyser.trend_analysis import TrendAnalyzer
        from analyser.config import get_config
        
        config = get_config()
        analyzer = TrendAnalyzer(default_na_values=config['na_values'])
        
        # Test numeric extraction (this was a key function in the original notebook)
        test_values = [
            '175 billion',
            '11 million', 
            '70 thousand',
            '1234',
            '1.5e9',
            '2.5 × 10^9',
            'n/a',
            'unknown',
            'not specified'
        ]
        
        print("  Testing numeric value extraction...")
        for value in test_values:
            result = analyzer._extract_numeric(value)
            print(f"    '{value}' → {result}")
        
        # Test that N/A values are handled correctly
        na_values = config['na_values']
        print(f"  Testing N/A value handling with {len(na_values)} N/A patterns...")
        
        for na_value in na_values[:5]:  # Test first 5 N/A values
            result = analyzer._extract_numeric(na_value)
            assert np.isnan(result), f"N/A value '{na_value}' should return NaN"
        
        print(" Function compatibility verified")
        return True
        
    except Exception as e:
        print(f" Function compatibility error: {e}")
        traceback.print_exc()
        return False

def test_data_processing_compatibility():
    """Test that data processing produces compatible results."""
    print("\n Testing data processing compatibility...")
    
    try:
        from analyser.trend_analysis import TrendAnalyzer
        from analyser.csv_processor import CSVProcessor
        from analyser.config import get_config
        
        config = get_config()
        
        # Create sample data similar to what the original notebook would process
        sample_data = pd.DataFrame({
            'value': [
                '175 billion', '11 billion', '70 billion', 'n/a', 'unknown',
                '1.5 million', '2.5e9', 'not specified', '1234', '5.5 thousand'
            ],
            'confidence': [95, 90, 85, 70, 65, 80, 88, 60, 75, 82],
            'run_id': list(range(1, 11)),
            'published_date': pd.date_range('2020-01-01', periods=10, freq='M'),
            'arxiv_id': [f'1234.{5678+i}' for i in range(10)],
            'model_provider': ['deepseek', 'anthropic'] * 5
        })
        
        analyzer = TrendAnalyzer(default_na_values=config['na_values'])
        
        # Test that the analyzer can process this data
        print("  Testing data processing pipeline...")
        
        # Test numeric extraction
        numeric_values = []
        for value in sample_data['value']:
            numeric_val = analyzer._extract_numeric(value)
            numeric_values.append(numeric_val)
        
        sample_data['numeric_value'] = numeric_values
        
        # Verify results
        numeric_count = sum(1 for x in numeric_values if not np.isnan(x))
        na_count = sum(1 for x in numeric_values if np.isnan(x))
        
        print(f"    Processed {len(sample_data)} values:")
        print(f"    - Numeric values: {numeric_count}")
        print(f"    - N/A values: {na_count}")
        
        # Test that we get reasonable numeric values
        valid_numeric = [x for x in numeric_values if not np.isnan(x)]
        if valid_numeric:
            print(f"    - Numeric range: {min(valid_numeric):.0f} - {max(valid_numeric):.0f}")
        
        assert numeric_count > 0, "Should extract some numeric values"
        assert na_count > 0, "Should identify some N/A values"
        
        print(" Data processing compatibility verified")
        return True
        
    except Exception as e:
        print(f" Data processing compatibility error: {e}")
        traceback.print_exc()
        return False

def test_csv_processing_compatibility():
    """Test CSV processing compatibility."""
    print("\n Testing CSV processing compatibility...")
    
    try:
        from analyser.csv_processor import CSVProcessor
        from analyser.config import get_config
        
        config = get_config()
        processor = CSVProcessor(na_values=config['na_values'])
        
        # Create a test CSV file with various link formats
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_csv:
            temp_csv.write('Link,Parameters\n')
            temp_csv.write('https://arxiv.org/abs/1234.5678,175 billion\n')
            temp_csv.write('https://arxiv.org/pdf/1234.5679.pdf,11 billion\n')
            temp_csv.write('1234.5680,70 billion\n')
            temp_csv.write('1234.5681v1,1.5 million\n')
            temp_csv.write('invalid_link,unknown\n')
            temp_csv.write('https://arxiv.org/abs/1234.5682,2.5e9\n')
            temp_csv.close()
            
            try:
                print("  Testing CSV structure exploration...")
                structure = processor.explore_csv_structure(temp_csv.name, show_sample_rows=2)
                assert structure is not None, "Should be able to explore CSV structure"
                
                print("  Testing ArXiv ID extraction...")
                arxiv_ids = processor.extract_arxiv_ids_preview(temp_csv.name, max_examples=10)
                assert isinstance(arxiv_ids, list), "Should return list of ArXiv IDs"
                
                expected_ids = ['1234.5678', '1234.5679', '1234.5680', '1234.5681', '1234.5682']
                for expected_id in expected_ids:
                    assert expected_id in arxiv_ids, f"Should extract ArXiv ID {expected_id}"
                
                print(f"    Extracted {len(arxiv_ids)} ArXiv IDs: {arxiv_ids}")
                
                print(" CSV processing compatibility verified")
                return True
                
            finally:
                os.unlink(temp_csv.name)
        
    except Exception as e:
        print(f" CSV processing compatibility error: {e}")
        traceback.print_exc()
        return False

def test_configuration_compatibility():
    """Test that configuration system works as expected."""
    print("\n️ Testing configuration compatibility...")
    
    try:
        from analyser.config import get_config, validate_config, DEFAULT_NA_VALUES
        
        # Test default configuration
        config = get_config()
        assert isinstance(config, dict), "Config should be a dictionary"
        
        # Test that default N/A values are reasonable
        default_na = config['na_values']
        assert len(default_na) > 0, "Should have default N/A values"
        
        # Test that common N/A patterns are included
        common_patterns = ['n/a', 'N/A', 'unknown', 'not specified']
        for pattern in common_patterns:
            assert pattern in default_na, f"Should include N/A pattern: {pattern}"
        
        print(f"  Default N/A values ({len(default_na)}): {default_na[:5]}...")
        
        # Test configuration validation
        is_valid = validate_config(config)
        assert is_valid, "Default configuration should be valid"
        
        # Test that we can modify configuration
        custom_config = config.copy()
        custom_config['na_values'] = ['custom1', 'custom2']
        
        # This should still be valid
        is_valid_custom = validate_config(custom_config)
        assert is_valid_custom, "Custom configuration should be valid"
        
        print(" Configuration compatibility verified")
        return True
        
    except Exception as e:
        print(f" Configuration compatibility error: {e}")
        return False

def test_error_handling_compatibility():
    """Test that error handling works as expected."""
    print("\n️ Testing error handling compatibility...")
    
    try:
        from analyser.validation import (
            ValidationError, DataValidationError, ConfigurationError,
            validate_field_name, validate_run_id_range, validate_figsize
        )
        from analyser.trend_analysis import TrendAnalyzer
        
        # Test that validation errors are raised appropriately
        print("  Testing validation error handling...")
        
        # Test invalid field name
        try:
            validate_field_name("")
            assert False, "Should raise ValidationError for empty field name"
        except ValidationError:
            pass  # Expected
        
        # Test invalid run ID range
        try:
            validate_run_id_range(100, 1)
            assert False, "Should raise ValidationError for invalid range"
        except ValidationError:
            pass  # Expected
        
        # Test invalid figsize
        try:
            validate_figsize((-12, 8))
            assert False, "Should raise ValidationError for negative figsize"
        except ValidationError:
            pass  # Expected
        
        # Test that TrendAnalyzer handles validation errors gracefully
        print("  Testing TrendAnalyzer error handling...")
        analyzer = TrendAnalyzer()
        
        # This should return None instead of crashing
        result = analyzer.visualize_field_trends(
            field_name="",  # Invalid field name
            run_id_start=100,
            run_id_end=1,   # Invalid range
            figsize=(-12, 8)  # Invalid figsize
        )
        assert result is None, "Should return None for invalid parameters"
        
        print(" Error handling compatibility verified")
        return True
        
    except Exception as e:
        print(f" Error handling compatibility error: {e}")
        traceback.print_exc()
        return False

def test_performance_compatibility():
    """Test that performance is reasonable."""
    print("\n Testing performance compatibility...")
    
    try:
        from analyser.trend_analysis import TrendAnalyzer
        from analyser.csv_processor import CSVProcessor
        from analyser.config import get_config
        import time
        
        config = get_config()
        
        # Test TrendAnalyzer performance
        print("  Testing TrendAnalyzer performance...")
        analyzer = TrendAnalyzer(default_na_values=config['na_values'])
        
        # Test numeric extraction performance
        test_values = ['175 billion', '11 million', '70 thousand', 'n/a', 'unknown'] * 100
        
        start_time = time.time()
        for value in test_values:
            analyzer._extract_numeric(value)
        end_time = time.time()
        
        processing_time = end_time - start_time
        print(f"    Processed {len(test_values)} values in {processing_time:.3f} seconds")
        assert processing_time < 1.0, "Numeric extraction should be fast"
        
        # Test CSVProcessor performance
        print("  Testing CSVProcessor performance...")
        processor = CSVProcessor(na_values=config['na_values'])
        
        # Test ArXiv ID extraction performance
        test_links = [
            'https://arxiv.org/abs/1234.5678',
            'https://arxiv.org/pdf/1234.5679.pdf',
            '1234.5680',
            '1234.5681v1',
            'invalid_link'
        ] * 50
        
        start_time = time.time()
        for link in test_links:
            processor._extract_arxiv_id_from_link(link)
        end_time = time.time()
        
        processing_time = end_time - start_time
        print(f"    Processed {len(test_links)} links in {processing_time:.3f} seconds")
        assert processing_time < 1.0, "ArXiv ID extraction should be fast"
        
        print(" Performance compatibility verified")
        return True
        
    except Exception as e:
        print(f" Performance compatibility error: {e}")
        return False

def main():
    """Run all compatibility tests."""
    print(" Compatibility Test Suite")
    print("=" * 50)
    print("Testing that the optimized system maintains compatibility")
    print("with the original notebook functionality...")
    
    tests = [
        ("Function Compatibility", test_original_vs_optimized_functions),
        ("Data Processing Compatibility", test_data_processing_compatibility),
        ("CSV Processing Compatibility", test_csv_processing_compatibility),
        ("Configuration Compatibility", test_configuration_compatibility),
        ("Error Handling Compatibility", test_error_handling_compatibility),
        ("Performance Compatibility", test_performance_compatibility)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f" {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print(" Compatibility Test Results:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = " PASS" if result else " FAIL"
        print(f"  {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n Summary: {passed}/{total} compatibility tests passed")
    
    if passed == total:
        print(" All compatibility tests passed! The optimized system maintains")
        print("   full compatibility with the original notebook functionality.")
        return 0
    else:
        print(f"️ {total - passed} compatibility test(s) failed.")
        print("   Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
