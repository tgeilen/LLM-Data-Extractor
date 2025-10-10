# Testing Guide for Optimized Trend Analysis System

This guide explains how to test that the optimized system works correctly and maintains compatibility with the original notebook.

##  Quick Start Testing

### 1. Quick Verification (30 seconds)
```bash
python test_quick.py
```
This runs a minimal test to verify the system is working.

### 2. Full Integration Test (2-3 minutes)
```bash
python test_integration.py
```
This runs comprehensive tests of all components.

### 3. Compatibility Test (1-2 minutes)
```bash
python test_compatibility.py
```
This verifies compatibility with the original notebook.

### 4. Unit Tests (1-2 minutes)
```bash
python run_tests.py
```
This runs the full unit test suite.

##  Test Categories

###  **Integration Tests** (`test_integration.py`)

Tests that all components work together:

-  **Module Imports**: All modules can be imported
-  **Configuration System**: Configuration loading and validation
-  **Validation Functions**: Input validation works correctly
-  **TrendAnalyzer Class**: Core trend analysis functionality
-  **CSVProcessor Class**: CSV processing and ArXiv ID extraction
-  **Database Integration**: Database connection and queries (if available)
-  **Example Scripts**: Example scripts can be imported
-  **Notebook Compatibility**: Optimized notebook is valid
-  **Unit Tests**: All unit tests pass

###  **Compatibility Tests** (`test_compatibility.py`)

Tests that the optimized system maintains compatibility:

-  **Function Compatibility**: Optimized functions produce same results
-  **Data Processing**: Data processing pipeline works correctly
-  **CSV Processing**: CSV handling maintains original behavior
-  **Configuration**: Configuration system works as expected
-  **Error Handling**: Error handling is robust and informative
-  **Performance**: Performance is reasonable and not degraded

###  **Unit Tests** (`run_tests.py`)

Tests individual components in isolation:

-  **Validation Tests**: All validation functions work correctly
-  **Trend Analysis Tests**: TrendAnalyzer class methods
-  **CSV Processor Tests**: CSVProcessor class methods
-  **Edge Cases**: Error conditions and boundary cases
-  **Mock Tests**: Tests with mocked dependencies

##  What Each Test Verifies

### Core Functionality
- **Numeric Value Extraction**: `'175 billion'` → `175000000000`
- **ArXiv ID Extraction**: `'https://arxiv.org/abs/1234.5678'` → `'1234.5678'`
- **N/A Value Handling**: `'n/a'`, `'unknown'` → `NaN`
- **Data Validation**: Input parameters are validated correctly
- **Error Handling**: Invalid inputs are handled gracefully

### Data Processing
- **DataFrame Processing**: Data is processed correctly
- **Date Handling**: Publication dates are parsed correctly
- **Model Provider Tracking**: Different providers are tracked
- **Confidence Scoring**: Confidence scores are maintained

### CSV Integration
- **Link Parsing**: Various ArXiv link formats are supported
- **Database Matching**: ArXiv IDs are matched with publication dates
- **Data Validation**: CSV data is validated before processing
- **Error Recovery**: Invalid data is handled gracefully

### Configuration
- **Default Settings**: Default configuration is valid
- **Custom Settings**: Custom configuration can be applied
- **Validation**: Configuration is validated before use
- **Environment Variables**: Environment variables are supported

##  Troubleshooting Test Failures

### Common Issues and Solutions

#### 1. Import Errors
```
 Import error: No module named 'analyser'
```
**Solution**: Make sure you're in the project root directory and all files are present.

#### 2. Database Connection Errors
```
️ Database not available: Database connection failed
```
**Solution**: This is expected if the database isn't set up. The tests will still pass.

#### 3. CSV File Errors
```
 Validation error: CSV file does not exist
```
**Solution**: The tests create temporary CSV files, so this shouldn't happen. Check file permissions.

#### 4. Validation Errors
```
 Validation error: Field name contains invalid characters
```
**Solution**: Check that test data uses valid field names (alphanumeric + underscores only).

### Debug Mode

To get more detailed error information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

##  Expected Test Results

### Successful Test Run
```
 Integration Test Suite
==================================================
 Testing module imports...
 All modules imported successfully

 Testing configuration system...
 Configuration system working correctly

️ Testing validation functions...
 Validation functions working correctly

 Testing TrendAnalyzer class...
 TrendAnalyzer working correctly

 Testing CSVProcessor class...
 CSVProcessor working correctly

️ Testing database integration...
️ Database not available: Database connection failed
 This is expected if database is not set up

 Testing example scripts...
 Example scripts can be imported successfully

 Testing notebook compatibility...
 Optimized notebook is valid

 Running unit tests...
 All unit tests passed

==================================================
 Integration Test Results:
==================================================
   PASS Module Imports
   PASS Configuration System
   PASS Validation Functions
   PASS TrendAnalyzer Class
   PASS CSVProcessor Class
   PASS Database Integration
   PASS Example Scripts
   PASS Notebook Compatibility
   PASS Unit Tests

 Summary: 9/9 tests passed
 All integration tests passed! The optimized system is working correctly.
```

##  Manual Testing

### Test Individual Components

#### Test TrendAnalyzer
```python
from analyser.trend_analysis import TrendAnalyzer
from analyser.config import get_config

config = get_config()
analyzer = TrendAnalyzer(na_values=config['na_values'])

# Test numeric extraction
result = analyzer._extract_numeric('175 billion')
print(f"Result: {result}")  # Should print: 175000000000
```

#### Test CSVProcessor
```python
from analyser.csv_processor import CSVProcessor

processor = CSVProcessor()

# Test ArXiv ID extraction
arxiv_id = processor._extract_arxiv_id_from_link('https://arxiv.org/abs/1234.5678')
print(f"ArXiv ID: {arxiv_id}")  # Should print: 1234.5678
```

#### Test Configuration
```python
from analyser.config import get_config, validate_config

config = get_config()
is_valid = validate_config(config)
print(f"Config valid: {is_valid}")  # Should print: True
```

### Test with Real Data

If you have access to the database:

```python
from analyser.trend_analysis import TrendAnalyzer, explore_available_fields

# Explore available data
fields = explore_available_fields()
print(f"Available fields: {list(fields['field_name'])}")

# Test with real data
analyzer = TrendAnalyzer()
df = analyzer.visualize_field_trends('parameters', log_scale=True)
print(f"Analyzed {len(df)} records")
```

##  Performance Testing

### Benchmark Tests
```python
import time
from analyser.trend_analysis import TrendAnalyzer

analyzer = TrendAnalyzer()

# Test numeric extraction performance
test_values = ['175 billion', '11 million', 'n/a'] * 1000

start_time = time.time()
for value in test_values:
    analyzer._extract_numeric(value)
end_time = time.time()

print(f"Processed {len(test_values)} values in {end_time - start_time:.3f} seconds")
```

##  Success Criteria

The system is working correctly if:

1.  **All tests pass** (integration, compatibility, unit tests)
2.  **No import errors** when importing modules
3.  **Core functions work** (numeric extraction, ArXiv ID extraction)
4.  **Error handling works** (invalid inputs are handled gracefully)
5.  **Configuration loads** (default and custom configurations work)
6.  **Examples run** (example scripts can be executed)
7.  **Notebook is valid** (optimized notebook can be opened)

##  Next Steps

After successful testing:

1. **Use the optimized system** for your analysis
2. **Run example scripts** to see the system in action
3. **Customize configuration** for your specific needs
4. **Add new features** using the modular architecture
5. **Extend tests** for any new functionality you add

##  Getting Help

If tests fail or you encounter issues:

1. **Check the error messages** - they usually indicate the problem
2. **Run tests individually** to isolate the issue
3. **Check file permissions** and directory structure
4. **Verify Python environment** and dependencies
5. **Review the troubleshooting section** above

The optimized system is designed to be robust and well-tested, so most issues are related to environment setup rather than the code itself.
