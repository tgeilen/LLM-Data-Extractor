#!/usr/bin/env python3
"""
Test runner script for the trend analysis modules.

This script runs all unit tests and provides a summary of the results.
"""

import unittest
import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def run_tests():
    """Run all unit tests and return the result."""
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = project_root / 'tests'
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    return result

def main():
    """Main function to run tests."""
    print(" Running Unit Tests for Trend Analysis Modules")
    print("=" * 60)
    
    try:
        result = run_tests()
        
        print("\n" + "=" * 60)
        print(" Test Results Summary:")
        print(f"  • Tests run: {result.testsRun}")
        print(f"  • Failures: {len(result.failures)}")
        print(f"  • Errors: {len(result.errors)}")
        print(f"  • Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
        
        if result.failures:
            print(f"\n Failures ({len(result.failures)}):")
            for test, traceback in result.failures:
                print(f"  • {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
        
        if result.errors:
            print(f"\n Errors ({len(result.errors)}):")
            for test, traceback in result.errors:
                print(f"  • {test}: {traceback.split('\\n')[-2]}")
        
        if result.wasSuccessful():
            print("\n All tests passed!")
            return 0
        else:
            print(f"\n {len(result.failures) + len(result.errors)} test(s) failed")
            return 1
            
    except Exception as e:
        print(f"\n Error running tests: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
