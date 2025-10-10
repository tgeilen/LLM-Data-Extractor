"""
Validation and Error Handling Module

This module provides validation functions and error handling utilities for the trend analysis system.
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Union, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class DataValidationError(ValidationError):
    """Exception raised when data validation fails."""
    pass


class ConfigurationError(ValidationError):
    """Exception raised when configuration validation fails."""
    pass


def validate_dataframe(df: pd.DataFrame, required_columns: List[str], 
                      min_rows: int = 1) -> bool:
    """
    Validate a DataFrame for required columns and minimum rows.
    
    Args:
        df: DataFrame to validate
        required_columns: List of required column names
        min_rows: Minimum number of rows required
    
    Returns:
        True if validation passes
    
    Raises:
        DataValidationError: If validation fails
    """
    if df is None:
        raise DataValidationError("DataFrame is None")
    
    if not isinstance(df, pd.DataFrame):
        raise DataValidationError(f"Expected DataFrame, got {type(df)}")
    
    if len(df) < min_rows:
        raise DataValidationError(f"DataFrame has {len(df)} rows, minimum required is {min_rows}")
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise DataValidationError(f"Missing required columns: {missing_columns}")
    
    return True


def validate_field_name(field_name: str) -> bool:
    """
    Validate field name format and content.
    
    Args:
        field_name: Field name to validate
    
    Returns:
        True if validation passes
    
    Raises:
        ValidationError: If validation fails
    """
    if not field_name:
        raise ValidationError("Field name cannot be empty")
    
    if not isinstance(field_name, str):
        raise ValidationError(f"Field name must be a string, got {type(field_name)}")
    
    # Check for invalid characters
    invalid_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '[', ']', '{', '}']
    if any(char in field_name for char in invalid_chars):
        raise ValidationError(f"Field name contains invalid characters: {invalid_chars}")
    
    # Check length
    if len(field_name) > 100:
        raise ValidationError(f"Field name too long: {len(field_name)} characters (max 100)")
    
    return True


def validate_run_id_range(run_id_start: Optional[int], run_id_end: Optional[int]) -> bool:
    """
    Validate run ID range parameters.
    
    Args:
        run_id_start: Starting run ID
        run_id_end: Ending run ID
    
    Returns:
        True if validation passes
    
    Raises:
        ValidationError: If validation fails
    """
    if run_id_start is not None:
        if not isinstance(run_id_start, int):
            raise ValidationError(f"run_id_start must be an integer, got {type(run_id_start)}")
        if run_id_start < 0:
            raise ValidationError(f"run_id_start must be non-negative, got {run_id_start}")
    
    if run_id_end is not None:
        if not isinstance(run_id_end, int):
            raise ValidationError(f"run_id_end must be an integer, got {type(run_id_end)}")
        if run_id_end < 0:
            raise ValidationError(f"run_id_end must be non-negative, got {run_id_end}")
    
    if run_id_start is not None and run_id_end is not None:
        if run_id_start > run_id_end:
            raise ValidationError(f"run_id_start ({run_id_start}) cannot be greater than run_id_end ({run_id_end})")
    
    return True


def validate_figsize(figsize: Tuple[int, int]) -> bool:
    """
    Validate figure size tuple.
    
    Args:
        figsize: Figure size as (width, height) tuple
    
    Returns:
        True if validation passes
    
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(figsize, (tuple, list)):
        raise ValidationError(f"figsize must be a tuple or list, got {type(figsize)}")
    
    if len(figsize) != 2:
        raise ValidationError(f"figsize must have exactly 2 elements, got {len(figsize)}")
    
    width, height = figsize
    if not isinstance(width, (int, float)) or not isinstance(height, (int, float)):
        raise ValidationError("figsize elements must be numbers")
    
    if width <= 0 or height <= 0:
        raise ValidationError(f"figsize dimensions must be positive, got {figsize}")
    
    if width > 50 or height > 50:
        raise ValidationError(f"figsize dimensions too large: {figsize} (max 50x50)")
    
    return True


def validate_na_values(na_values: List[str]) -> bool:
    """
    Validate N/A values list.
    
    Args:
        na_values: List of values to treat as N/A
    
    Returns:
        True if validation passes
    
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(na_values, list):
        raise ValidationError(f"na_values must be a list, got {type(na_values)}")
    
    if len(na_values) == 0:
        raise ValidationError("na_values list cannot be empty")
    
    for i, value in enumerate(na_values):
        if not isinstance(value, str):
            raise ValidationError(f"na_values[{i}] must be a string, got {type(value)}")
    
    return True


def validate_csv_file(csv_file_path: Union[str, Path]) -> bool:
    """
    Validate CSV file path and existence.
    
    Args:
        csv_file_path: Path to CSV file
    
    Returns:
        True if validation passes
    
    Raises:
        ValidationError: If validation fails
    """
    csv_path = Path(csv_file_path)
    
    if not csv_path.exists():
        raise ValidationError(f"CSV file does not exist: {csv_path}")
    
    if not csv_path.is_file():
        raise ValidationError(f"Path is not a file: {csv_path}")
    
    if csv_path.suffix.lower() != '.csv':
        raise ValidationError(f"File must have .csv extension, got {csv_path.suffix}")
    
    # Check file size (max 100MB)
    file_size = csv_path.stat().st_size
    max_size = 100 * 1024 * 1024  # 100MB
    if file_size > max_size:
        raise ValidationError(f"CSV file too large: {file_size / 1024 / 1024:.1f}MB (max 100MB)")
    
    return True


def validate_arxiv_id(arxiv_id: str) -> bool:
    """
    Validate ArXiv ID format.
    
    Args:
        arxiv_id: ArXiv ID to validate
    
    Returns:
        True if validation passes
    
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(arxiv_id, str):
        raise ValidationError(f"ArXiv ID must be a string, got {type(arxiv_id)}")
    
    if not arxiv_id:
        raise ValidationError("ArXiv ID cannot be empty")
    
    # ArXiv ID format: YYMM.NNNNN or YYMM.NNNNNvN
    import re
    pattern = r'^\d{4}\.\d{4,5}(?:v\d+)?$'
    if not re.match(pattern, arxiv_id):
        raise ValidationError(f"Invalid ArXiv ID format: {arxiv_id}")
    
    return True


def validate_date_range(start_date: Optional[pd.Timestamp], 
                       end_date: Optional[pd.Timestamp]) -> bool:
    """
    Validate date range parameters.
    
    Args:
        start_date: Start date
        end_date: End date
    
    Returns:
        True if validation passes
    
    Raises:
        ValidationError: If validation fails
    """
    if start_date is not None and not isinstance(start_date, pd.Timestamp):
        raise ValidationError(f"start_date must be a pandas Timestamp, got {type(start_date)}")
    
    if end_date is not None and not isinstance(end_date, pd.Timestamp):
        raise ValidationError(f"end_date must be a pandas Timestamp, got {type(end_date)}")
    
    if start_date is not None and end_date is not None:
        if start_date > end_date:
            raise ValidationError(f"start_date ({start_date}) cannot be after end_date ({end_date})")
    
    return True


def validate_numeric_data(data: pd.Series, field_name: str) -> Dict[str, Any]:
    """
    Validate and analyze numeric data.
    
    Args:
        data: Series containing numeric data
        field_name: Name of the field for error messages
    
    Returns:
        Dictionary with validation results and statistics
    
    Raises:
        DataValidationError: If validation fails
    """
    if data is None or len(data) == 0:
        raise DataValidationError(f"No data provided for {field_name}")
    
    # Convert to numeric, coercing errors to NaN
    numeric_data = pd.to_numeric(data, errors='coerce')
    
    # Count valid vs invalid values
    valid_count = numeric_data.notna().sum()
    invalid_count = numeric_data.isna().sum()
    total_count = len(data)
    
    if valid_count == 0:
        raise DataValidationError(f"No valid numeric values found in {field_name}")
    
    # Calculate statistics
    stats = {
        'total_count': total_count,
        'valid_count': valid_count,
        'invalid_count': invalid_count,
        'valid_percentage': (valid_count / total_count) * 100,
        'min_value': numeric_data.min(),
        'max_value': numeric_data.max(),
        'mean_value': numeric_data.mean(),
        'median_value': numeric_data.median(),
        'std_value': numeric_data.std()
    }
    
    # Check for outliers (values more than 3 standard deviations from mean)
    if valid_count > 1:
        z_scores = np.abs((numeric_data - numeric_data.mean()) / numeric_data.std())
        outliers = z_scores > 3
        stats['outlier_count'] = outliers.sum()
        stats['outlier_percentage'] = (outliers.sum() / valid_count) * 100
    
    return stats


def validate_configuration(config: Dict[str, Any]) -> bool:
    """
    Validate configuration dictionary.
    
    Args:
        config: Configuration dictionary to validate
    
    Returns:
        True if validation passes
    
    Raises:
        ConfigurationError: If validation fails
    """
    required_keys = ['na_values', 'common_fields', 'plot_settings']
    
    for key in required_keys:
        if key not in config:
            raise ConfigurationError(f"Missing required configuration key: {key}")
    
    # Validate N/A values
    validate_na_values(config['na_values'])
    
    # Validate common fields
    if not isinstance(config['common_fields'], list):
        raise ConfigurationError("common_fields must be a list")
    
    if len(config['common_fields']) == 0:
        raise ConfigurationError("common_fields list cannot be empty")
    
    for field in config['common_fields']:
        validate_field_name(field)
    
    # Validate plot settings
    plot_settings = config.get('plot_settings', {})
    if 'figsize' in plot_settings:
        validate_figsize(plot_settings['figsize'])
    
    return True


def safe_execute(func, *args, **kwargs):
    """
    Safely execute a function with error handling and logging.
    
    Args:
        func: Function to execute
        *args: Function arguments
        **kwargs: Function keyword arguments
    
    Returns:
        Function result or None if error occurred
    """
    try:
        return func(*args, **kwargs)
    except ValidationError as e:
        logger.error(f"Validation error in {func.__name__}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in {func.__name__}: {e}")
        return None


def validate_database_connection():
    """
    Validate database connection and basic schema.
    
    Returns:
        True if validation passes
    
    Raises:
        ValidationError: If validation fails
    """
    try:
        from db.db_utils import get_connection
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if required tables exist
        required_tables = ['papers', 'extraction_runs', 'extracted_fields', 'models']
        
        for table in required_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table} LIMIT 1")
            result = cursor.fetchone()
            if result is None:
                raise ValidationError(f"Table {table} does not exist or is not accessible")
        
        conn.close()
        return True
        
    except ImportError:
        raise ValidationError("Database module not available")
    except Exception as e:
        raise ValidationError(f"Database connection failed: {e}")


def validate_analysis_parameters(field_name: str, run_id_start: Optional[int], 
                                run_id_end: Optional[int], figsize: Tuple[int, int],
                                na_values: List[str]) -> bool:
    """
    Validate all parameters for trend analysis.
    
    Args:
        field_name: Field name to analyze
        run_id_start: Starting run ID
        run_id_end: Ending run ID
        figsize: Figure size
        na_values: N/A values list
    
    Returns:
        True if all validations pass
    
    Raises:
        ValidationError: If any validation fails
    """
    validate_field_name(field_name)
    validate_run_id_range(run_id_start, run_id_end)
    validate_figsize(figsize)
    validate_na_values(na_values)
    
    return True


# Utility functions for common validation patterns
def is_valid_arxiv_id(arxiv_id: str) -> bool:
    """Check if ArXiv ID is valid without raising exception."""
    try:
        validate_arxiv_id(arxiv_id)
        return True
    except ValidationError:
        return False


def is_valid_field_name(field_name: str) -> bool:
    """Check if field name is valid without raising exception."""
    try:
        validate_field_name(field_name)
        return True
    except ValidationError:
        return False


def is_valid_csv_file(csv_file_path: Union[str, Path]) -> bool:
    """Check if CSV file is valid without raising exception."""
    try:
        validate_csv_file(csv_file_path)
        return True
    except ValidationError:
        return False


def get_validation_summary(data: pd.DataFrame, field_name: str) -> Dict[str, Any]:
    """
    Get a comprehensive validation summary for a DataFrame and field.
    
    Args:
        data: DataFrame to validate
        field_name: Field name to analyze
    
    Returns:
        Dictionary with validation summary
    """
    summary = {
        'field_name': field_name,
        'total_rows': len(data) if data is not None else 0,
        'is_valid': False,
        'errors': [],
        'warnings': [],
        'statistics': {}
    }
    
    try:
        # Basic DataFrame validation
        if data is not None and len(data) > 0:
            summary['is_valid'] = True
            
            # Check for required columns
            required_columns = ['value', 'published_date', 'arxiv_id']
            missing_columns = [col for col in required_columns if col not in data.columns]
            if missing_columns:
                summary['errors'].append(f"Missing columns: {missing_columns}")
                summary['is_valid'] = False
            
            # Analyze the field data
            if 'value' in data.columns:
                try:
                    stats = validate_numeric_data(data['value'], field_name)
                    summary['statistics'] = stats
                except DataValidationError as e:
                    summary['warnings'].append(str(e))
            
            # Check for date validity
            if 'published_date' in data.columns:
                date_series = pd.to_datetime(data['published_date'], errors='coerce')
                invalid_dates = date_series.isna().sum()
                if invalid_dates > 0:
                    summary['warnings'].append(f"{invalid_dates} invalid dates found")
            
            # Check for ArXiv ID validity
            if 'arxiv_id' in data.columns:
                invalid_arxiv_ids = data['arxiv_id'].apply(
                    lambda x: not is_valid_arxiv_id(str(x)) if pd.notna(x) else False
                ).sum()
                if invalid_arxiv_ids > 0:
                    summary['warnings'].append(f"{invalid_arxiv_ids} invalid ArXiv IDs found")
        
        else:
            summary['errors'].append("No data provided")
    
    except Exception as e:
        summary['errors'].append(f"Validation error: {e}")
        summary['is_valid'] = False
    
    return summary
