#!/usr/bin/env python3
"""
Quick Test Script

This script provides a quick way to test that the optimized system is working
without running the full test suite. Perfect for quick verification.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def quick_test():
    """Run a quick test to verify the system is working."""
    print(" Quick Test - Verifying Optimized System")
    print("=" * 40)
    
    try:
        # Test 1: Import all modules
        print("1. Testing imports...")
        from analyser.trend_analysis import TrendAnalyzer
        from analyser.csv_processor import CSVProcessor
        from analyser.config import get_config
        from analyser.validation import validate_field_name
        print("    All modules imported successfully")
        
        # Test 2: Initialize classes
        print("2. Testing initialization...")
        config = get_config()
        analyzer = TrendAnalyzer(default_na_values=config['na_values'])
        processor = CSVProcessor(na_values=config['na_values'])
        print("    Classes initialized successfully")
        
        # Test 3: Test core functionality
        print("3. Testing core functionality...")
        
        # Test numeric extraction
        result = analyzer._extract_numeric('175 billion')
        assert result == 175_000_000_000, f"Expected 175B, got {result}"
        
        # Test ArXiv ID extraction
        arxiv_id = processor._extract_arxiv_id_from_link('https://arxiv.org/abs/1234.5678')
        assert arxiv_id == '1234.5678', f"Expected 1234.5678, got {arxiv_id}"
        
        # Test validation
        validate_field_name('parameters')
        print("    Core functionality working")
        
        # Test 4: Test configuration
        print("4. Testing configuration...")
        assert 'na_values' in config, "Config should have na_values"
        assert 'common_fields' in config, "Config should have common_fields"
        assert len(config['na_values']) > 0, "Should have N/A values"
        print("    Configuration working")
        
        print("\n Quick test passed! The optimized system is working correctly.")
        print("\n To run more comprehensive tests:")
        print("   python test_integration.py    # Full integration tests")
        print("   python test_compatibility.py  # Compatibility tests")
        print("   python run_tests.py           # Unit tests")
        
        return True
        
    except Exception as e:
        print(f"\n Quick test failed: {e}")
        print("\n Troubleshooting:")
        print("   1. Make sure you're in the project root directory")
        print("   2. Check that all files are present")
        print("   3. Verify Python path is correct")
        print("   4. Run 'python test_integration.py' for detailed diagnostics")
        return False

if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)
