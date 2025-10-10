# Trend Analysis System - Optimized Version

This is an optimized version of the trend analysis system for research paper data. The original notebook has been refactored into a modular, maintainable, and well-tested codebase.

##  What's New

###  **Major Improvements**

1. **Modular Design**: Core functions extracted into separate Python modules
2. **Clean Interface**: Simple, focused examples with clear documentation
3. **Better Error Handling**: Robust error handling and validation functions
4. **Configuration Management**: Centralized settings and parameters
5. **Example Scripts**: Reusable example scripts for common use cases
6. **Type Hints**: Better code documentation and IDE support
7. **Logging**: Proper logging for debugging and monitoring
8. **Unit Tests**: Comprehensive test coverage for core functions

###  **New File Structure**

```
analyser/
├── __init__.py
├── trend_analysis.py      # Core trend analysis functions
├── csv_processor.py       # CSV data processing
├── config.py             # Configuration settings
├── validation.py         # Validation and error handling
└── base_analyser.py      # (existing)

examples/
├── basic_trend_analysis.py
├── csv_integration_example.py
└── comparative_analysis_example.py

tests/
├── __init__.py
├── test_validation.py
├── test_trend_analysis.py
└── test_csv_processor.py

sample_analysis_optimized.ipynb  # Clean, focused notebook
run_tests.py                     # Test runner script
```

##  **Quick Start**

### 1. Basic Trend Analysis

```python
from analyser.trend_analysis import TrendAnalyzer
from analyser.config import get_config

# Initialize analyzer
config = get_config()
analyzer = TrendAnalyzer(na_values=config['na_values'])

# Analyze parameters field trends
params_df = analyzer.visualize_field_trends(
    field_name='parameters',
    run_id_start=None,
    run_id_end=None,
    figsize=(14, 10),
    show_numeric_trend=True,
    log_scale=True  # Perfect for parameter counts
)
```

### 2. CSV Integration

```python
from analyser.csv_processor import CSVProcessor

# Initialize CSV processor
csv_processor = CSVProcessor(na_values=config['na_values'])

# Process CSV and match with database
csv_data = csv_processor.process_csv_with_arxiv_lookup(
    csv_file_path="Epoch Database - Notable Models.csv",
    link_column='Link',
    parameters_column='Parameters'
)
```

### 3. Run Example Scripts

```bash
# Basic trend analysis
python examples/basic_trend_analysis.py

# CSV integration
python examples/csv_integration_example.py

# Comparative analysis
python examples/comparative_analysis_example.py
```

##  **Core Modules**

### `TrendAnalyzer` Class

The main class for trend analysis operations:

```python
analyzer = TrendAnalyzer(na_values=['n/a', 'N/A', 'unknown'])

# Analyze field trends
df = analyzer.visualize_field_trends(
    field_name='parameters',
    run_id_start=1,
    run_id_end=100,
    figsize=(12, 8),
    show_numeric_trend=True,
    log_scale=True
)
```

**Key Features:**
- Automatic numeric value extraction from text
- Logarithmic scale support for wide value ranges
- Custom N/A value handling
- Trend line computation
- Model provider color coding
- Confidence tracking

### `CSVProcessor` Class

Handles external CSV data integration:

```python
processor = CSVProcessor(na_values=config['na_values'])

# Process CSV file
csv_data = processor.process_csv_with_arxiv_lookup(
    csv_file_path="data.csv",
    link_column='Link',
    parameters_column='Parameters'
)

# Explore CSV structure
structure = processor.explore_csv_structure("data.csv")

# Preview ArXiv ID extraction
arxiv_ids = processor.extract_arxiv_ids_preview("data.csv")
```

**Key Features:**
- Automatic ArXiv ID extraction from various link formats
- Database integration for publication dates
- Data validation and error handling
- CSV structure exploration
- Duplicate removal

### Configuration System

Centralized configuration management:

```python
from analyser.config import get_config, validate_config

# Get configuration
config = get_config()

# Validate configuration
is_valid = validate_config(config)

# Access specific settings
na_values = config['na_values']
plot_settings = config['plot_settings']
color_schemes = config['colors']
```

### Validation System

Comprehensive validation and error handling:

```python
from analyser.validation import (
    validate_field_name, validate_run_id_range,
    validate_figsize, validate_csv_file,
    ValidationError, DataValidationError
)

# Validate parameters
validate_field_name('parameters')
validate_run_id_range(1, 100)
validate_figsize((12, 8))
validate_csv_file('data.csv')
```

##  **Testing**

### Run All Tests

```bash
python run_tests.py
```

### Run Specific Test Modules

```bash
# Test validation functions
python -m unittest tests.test_validation

# Test trend analysis
python -m unittest tests.test_trend_analysis

# Test CSV processor
python -m unittest tests.test_csv_processor
```

### Test Coverage

The test suite covers:
-  Input validation and error handling
-  Data processing and transformation
-  Database integration
-  CSV processing and ArXiv ID extraction
-  Configuration management
-  Edge cases and error conditions

##  **Usage Examples**

### Example 1: Basic Parameter Trend Analysis

```python
from analyser.trend_analysis import TrendAnalyzer

analyzer = TrendAnalyzer()

# Analyze parameter trends with log scale
df = analyzer.visualize_field_trends(
    field_name='parameters',
    log_scale=True,
    show_numeric_trend=True
)

print(f"Analyzed {len(df)} parameter extractions")
```

### Example 2: CSV Data Integration

```python
from analyser.csv_processor import CSVProcessor

processor = CSVProcessor()

# Process external CSV data
csv_data = processor.process_csv_with_arxiv_lookup(
    csv_file_path="Epoch Database - Notable Models.csv"
)

if csv_data is not None:
    print(f"Processed {len(csv_data)} papers from CSV")
    print(f"Date range: {csv_data['publication_date'].min()} to {csv_data['publication_date'].max()}")
```

### Example 3: Comparative Analysis

```python
# Compare early vs recent extractions
early_df = analyzer.visualize_field_trends(
    field_name='parameters',
    run_id_start=1,
    run_id_end=50,
    log_scale=True
)

recent_df = analyzer.visualize_field_trends(
    field_name='parameters',
    run_id_start=51,
    run_id_end=100,
    log_scale=True
)

# Calculate overlap
early_ids = set(early_df['arxiv_id'])
recent_ids = set(recent_df['arxiv_id'])
overlap = early_ids & recent_ids

print(f"Papers in both periods: {len(overlap)}")
```

## ️ **Configuration**

### Customizing Settings

Edit `analyser/config.py` to customize:

```python
# Default N/A values
DEFAULT_NA_VALUES = [
    'n/a', '', 'N/A', 'unknown', 'None', 'null',
    'not specified', 'not available', 'not reported'
]

# Plot settings
DEFAULT_PLOT_SETTINGS = {
    'figsize': (12, 10),
    'dpi': 100,
    'style': 'default',
    'palette': 'husl'
}

# Color schemes
COLOR_SCHEMES = {
    'database_range1': '#1f77b4',  # Blue
    'database_range2': '#ff7f0e',  # Orange
    'csv_data': '#2E8B57',         # Sea Green
}
```

### Environment Variables

You can also set configuration via environment variables:

```bash
export TREND_ANALYSIS_LOG_LEVEL=INFO
export TREND_ANALYSIS_MAX_FILE_SIZE=100MB
export TREND_ANALYSIS_DEFAULT_FIGSIZE="12,10"
```

##  **Advanced Usage**

### Custom Validation

```python
from analyser.validation import ValidationError, validate_analysis_parameters

try:
    validate_analysis_parameters(
        field_name='parameters',
        run_id_start=1,
        run_id_end=100,
        figsize=(12, 8),
        na_values=['n/a', 'N/A']
    )
    print("Parameters are valid")
except ValidationError as e:
    print(f"Validation error: {e}")
```

### Error Handling

```python
from analyser.validation import safe_execute

def risky_operation():
    # Some operation that might fail
    pass

result = safe_execute(risky_operation)
if result is None:
    print("Operation failed, but system continues")
```

### Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info("Starting trend analysis")
```

##  **API Reference**

### TrendAnalyzer Methods

- `visualize_field_trends()`: Main trend visualization method
- `_get_field_data()`: Retrieve data from database
- `_extract_numeric()`: Extract numeric values from text
- `_process_and_visualize_data()`: Process data and create plots

### CSVProcessor Methods

- `process_csv_with_arxiv_lookup()`: Process CSV and match with database
- `explore_csv_structure()`: Explore CSV file structure
- `extract_arxiv_ids_preview()`: Preview ArXiv ID extraction
- `_extract_arxiv_id_from_link()`: Extract ArXiv ID from single link

### Validation Functions

- `validate_field_name()`: Validate field name format
- `validate_run_id_range()`: Validate run ID range
- `validate_figsize()`: Validate figure size
- `validate_csv_file()`: Validate CSV file
- `validate_arxiv_id()`: Validate ArXiv ID format

##  **Troubleshooting**

### Common Issues

1. **Database Connection Error**
   ```
   ️ Database validation warning: Database connection failed
   ```
   - Check database configuration
   - Ensure database is running
   - Verify connection parameters

2. **CSV File Not Found**
   ```
    Validation error: CSV file does not exist
   ```
   - Check file path
   - Ensure file has .csv extension
   - Verify file permissions

3. **Invalid Field Name**
   ```
    Validation error: Field name contains invalid characters
   ```
   - Use alphanumeric characters and underscores only
   - Avoid special characters like <, >, ", ', etc.

4. **No Data Found**
   ```
    No data found for field 'parameters'
   ```
   - Check if field exists in database
   - Verify run ID range
   - Check date filters

### Debug Mode

Enable debug logging for detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

##  **Contributing**

### Adding New Features

1. Create feature branch
2. Add tests for new functionality
3. Update documentation
4. Run test suite
5. Submit pull request

### Code Style

- Follow PEP 8 guidelines
- Use type hints
- Add docstrings for all functions
- Write unit tests for new code

##  **License**

This project is part of the Master's Thesis research work.

##  **Acknowledgments**

- Original notebook implementation
- Database integration modules
- Matplotlib and Pandas libraries
- ArXiv API for paper metadata

---

**Note**: This optimized version maintains full compatibility with the original notebook while providing a much cleaner, more maintainable, and better-tested codebase.
