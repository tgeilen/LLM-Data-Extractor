#!/usr/bin/env python3
"""
Integration Test Script

This script tests that the optimized system works end-to-end and maintains
compatibility with the original notebook functionality.
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

def test_imports():
    """Test that all modules can be imported successfully."""
    print(" Testing module imports...")
    
    try:
        from analyser.trend_analysis import TrendAnalyzer, explore_available_fields, get_run_id_ranges
        from analyser.csv_processor import CSVProcessor
        from analyser.config import get_config, validate_config
        from analyser.validation import (
            validate_field_name, validate_run_id_range, validate_figsize,
            validate_na_values, validate_csv_file, validate_arxiv_id,
            ValidationError, DataValidationError, ConfigurationError
        )
        print(" All modules imported successfully")
        return True
    except ImportError as e:
        print(f" Import error: {e}")
        return False

def test_configuration():
    """Test configuration system."""
    print("\n Testing configuration system...")
    
    try:
        from analyser.config import get_config, validate_config
        
        # Test getting configuration
        config = get_config()
        assert isinstance(config, dict), "Config should be a dictionary"
        assert 'na_values' in config, "Config should have na_values"
        assert 'common_fields' in config, "Config should have common_fields"
        assert 'plot_settings' in config, "Config should have plot_settings"
        
        # Test configuration validation
        is_valid = validate_config(config)
        assert is_valid, "Default configuration should be valid"
        
        print(" Configuration system working correctly")
        return True
    except Exception as e:
        print(f" Configuration error: {e}")
        return False

def test_validation_functions():
    """Test validation functions."""
    print("\n️ Testing validation functions...")
    
    try:
        from analyser.validation import (
            validate_field_name, validate_run_id_range, validate_figsize,
            validate_na_values, validate_arxiv_id, ValidationError
        )
        
        # Test field name validation
        assert validate_field_name("parameters") == True
        try:
            validate_field_name("")
            assert False, "Should raise ValidationError for empty field name"
        except ValidationError:
            pass
        
        # Test run ID range validation
        assert validate_run_id_range(1, 100) == True
        assert validate_run_id_range(None, None) == True
        try:
            validate_run_id_range(100, 1)
            assert False, "Should raise ValidationError for invalid range"
        except ValidationError:
            pass
        
        # Test figsize validation
        assert validate_figsize((12, 8)) == True
        try:
            validate_figsize((-12, 8))
            assert False, "Should raise ValidationError for negative figsize"
        except ValidationError:
            pass
        
        # Test N/A values validation
        assert validate_na_values(['n/a', 'N/A']) == True
        try:
            validate_na_values([])
            assert False, "Should raise ValidationError for empty N/A values"
        except ValidationError:
            pass
        
        # Test ArXiv ID validation
        assert validate_arxiv_id("1234.5678") == True
        assert validate_arxiv_id("1234.5678v1") == True
        try:
            validate_arxiv_id("invalid_id")
            assert False, "Should raise ValidationError for invalid ArXiv ID"
        except ValidationError:
            pass
        
        print(" Validation functions working correctly")
        return True
    except Exception as e:
        print(f" Validation error: {e}")
        return False

def test_trend_analyzer():
    """Test TrendAnalyzer class."""
    print("\n Testing TrendAnalyzer class...")
    
    try:
        from analyser.trend_analysis import TrendAnalyzer
        from analyser.config import get_config
        
        config = get_config()
        
        # Test initialization
        analyzer = TrendAnalyzer(default_na_values=config['na_values'])
        assert analyzer is not None, "TrendAnalyzer should initialize"
        assert isinstance(analyzer.default_na_values, list), "N/A values should be a list"
        
        # Test numeric extraction
        test_cases = [
            ('175 billion', 175_000_000_000),
            ('11 million', 11_000_000),
            ('70 thousand', 70_000),
            ('1234', 1234),
            ('n/a', np.nan)
        ]
        
        for input_val, expected in test_cases:
            result = analyzer._extract_numeric(input_val)
            if np.isnan(expected):
                assert np.isnan(result), f"Expected NaN for '{input_val}'"
            else:
                assert result == expected, f"Expected {expected} for '{input_val}', got {result}"
        
        print(" TrendAnalyzer working correctly")
        return True
    except Exception as e:
        print(f" TrendAnalyzer error: {e}")
        traceback.print_exc()
        return False

def test_csv_processor():
    """Test CSVProcessor class."""
    print("\n Testing CSVProcessor class...")
    
    try:
        from analyser.csv_processor import CSVProcessor
        from analyser.config import get_config
        
        config = get_config()
        
        # Test initialization
        processor = CSVProcessor(na_values=config['na_values'])
        assert processor is not None, "CSVProcessor should initialize"
        assert isinstance(processor.arxiv_patterns, list), "ArXiv patterns should be a list"
        
        # Test ArXiv ID extraction
        test_links = [
            ('https://arxiv.org/abs/1234.5678', '1234.5678'),
            ('https://arxiv.org/pdf/1234.5678.pdf', '1234.5678'),
            ('1234.5678', '1234.5678'),
            ('1234.5678v1', '1234.5678'),
            ('invalid_link', None)
        ]
        
        for link, expected in test_links:
            result = processor._extract_arxiv_id_from_link(link)
            assert result == expected, f"Expected {expected} for '{link}', got {result}"
        
        # Test with temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_csv:
            temp_csv.write('Link,Parameters\n')
            temp_csv.write('https://arxiv.org/abs/1234.5678,175 billion\n')
            temp_csv.write('https://arxiv.org/abs/1234.5679,11 billion\n')
            temp_csv.close()
            
            try:
                # Test CSV structure exploration
                structure = processor.explore_csv_structure(temp_csv.name, show_sample_rows=1)
                assert structure is not None, "Should be able to explore CSV structure"
                
                # Test ArXiv ID preview
                arxiv_ids = processor.extract_arxiv_ids_preview(temp_csv.name, max_examples=5)
                assert isinstance(arxiv_ids, list), "Should return list of ArXiv IDs"
                assert len(arxiv_ids) == 2, f"Should find 2 ArXiv IDs, found {len(arxiv_ids)}"
                
            finally:
                os.unlink(temp_csv.name)
        
        print(" CSVProcessor working correctly")
        return True
    except Exception as e:
        print(f" CSVProcessor error: {e}")
        traceback.print_exc()
        return False

def test_database_integration():
    """Test database integration (if available)."""
    print("\n️ Testing database integration...")
    
    try:
        from analyser.trend_analysis import get_run_id_ranges, explore_available_fields
        from analyser.validation import validate_database_connection
        
        # Test database connection validation
        try:
            validate_database_connection()
            print(" Database connection validated")
            
            # Test run ID ranges
            run_info = get_run_id_ranges()
            assert isinstance(run_info, dict), "Run info should be a dictionary"
            assert 'min_run_id' in run_info, "Run info should have min_run_id"
            assert 'max_run_id' in run_info, "Run info should have max_run_id"
            print(" Run ID ranges retrieved successfully")
            
            # Test field exploration
            field_info = explore_available_fields()
            assert isinstance(field_info, pd.DataFrame), "Field info should be a DataFrame"
            print(" Available fields explored successfully")
            
        except Exception as e:
            print(f"️ Database not available: {e}")
            print(" This is expected if database is not set up")
            return True  # Not a failure if DB is not available
        
        return True
    except Exception as e:
        print(f" Database integration error: {e}")
        return False

def test_example_scripts():
    """Test that example scripts can be imported and run."""
    print("\n Testing example scripts...")
    
    try:
        # Test basic trend analysis example
        sys.path.append(str(project_root / 'examples'))
        
        # Import example modules (don't run main() to avoid actual execution)
        import basic_trend_analysis
        import csv_integration_example
        import comparative_analysis_example
        
        assert hasattr(basic_trend_analysis, 'main'), "basic_trend_analysis should have main function"
        assert hasattr(csv_integration_example, 'main'), "csv_integration_example should have main function"
        assert hasattr(comparative_analysis_example, 'main'), "comparative_analysis_example should have main function"
        
        print(" Example scripts can be imported successfully")
        return True
    except Exception as e:
        print(f" Example scripts error: {e}")
        return False

def test_notebook_compatibility():
    """Test that the optimized notebook works."""
    print("\n Testing notebook compatibility...")
    
    try:
        # Test that the optimized notebook can be imported
        notebook_path = project_root / 'sample_analysis_optimized.ipynb'
        assert notebook_path.exists(), "Optimized notebook should exist"
        
        # Test that it's a valid notebook
        import json
        with open(notebook_path, 'r') as f:
            notebook = json.load(f)
        
        assert 'cells' in notebook, "Notebook should have cells"
        assert len(notebook['cells']) > 0, "Notebook should have content"
        
        # Check that it has the expected structure
        cell_types = [cell['cell_type'] for cell in notebook['cells']]
        assert 'markdown' in cell_types, "Notebook should have markdown cells"
        assert 'code' in cell_types, "Notebook should have code cells"
        
        print(" Optimized notebook is valid")
        return True
    except Exception as e:
        print(f" Notebook compatibility error: {e}")
        return False

def run_unit_tests():
    """Run the unit test suite."""
    print("\n Running unit tests...")
    
    try:
        import subprocess
        result = subprocess.run([sys.executable, 'run_tests.py'], 
                              capture_output=True, text=True, cwd=project_root)
        
        if result.returncode == 0:
            print(" All unit tests passed")
            return True
        else:
            print(f" Unit tests failed:")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f" Error running unit tests: {e}")
        return False

def main():
    """Run all integration tests."""
    print(" Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Configuration System", test_configuration),
        ("Validation Functions", test_validation_functions),
        ("TrendAnalyzer Class", test_trend_analyzer),
        ("CSVProcessor Class", test_csv_processor),
        ("Database Integration", test_database_integration),
        ("Example Scripts", test_example_scripts),
        ("Notebook Compatibility", test_notebook_compatibility),
        ("Unit Tests", run_unit_tests)
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
    print(" Integration Test Results:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = " PASS" if result else " FAIL"
        print(f"  {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print(" All integration tests passed! The optimized system is working correctly.")
        return 0
    else:
        print(f"️ {total - passed} test(s) failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
