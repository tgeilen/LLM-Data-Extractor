"""
Unit tests for validation module.
"""

import unittest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Add the project root to the path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyser.validation import (
    validate_dataframe, validate_field_name, validate_run_id_range,
    validate_figsize, validate_na_values, validate_csv_file,
    validate_arxiv_id, validate_date_range, validate_numeric_data,
    validate_configuration, ValidationError, DataValidationError,
    ConfigurationError, is_valid_arxiv_id, is_valid_field_name,
    is_valid_csv_file, get_validation_summary
)


class TestValidation(unittest.TestCase):
    """Test cases for validation functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_df = pd.DataFrame({
            'value': ['175 billion', '11 billion', '70 billion'],
            'published_date': pd.to_datetime(['2020-01-15', '2021-03-20', '2022-07-10']),
            'arxiv_id': ['1234.5678', '1234.5679', '1234.5680']
        })
        
        # Create a temporary CSV file for testing
        self.temp_csv = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        self.temp_csv.write('Link,Parameters\n')
        self.temp_csv.write('https://arxiv.org/abs/1234.5678,175 billion\n')
        self.temp_csv.write('https://arxiv.org/abs/1234.5679,11 billion\n')
        self.temp_csv.close()
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_csv.name):
            os.unlink(self.temp_csv.name)
    
    def test_validate_dataframe_success(self):
        """Test successful DataFrame validation."""
        result = validate_dataframe(
            self.sample_df, 
            ['value', 'published_date', 'arxiv_id'], 
            min_rows=1
        )
        self.assertTrue(result)
    
    def test_validate_dataframe_none(self):
        """Test DataFrame validation with None input."""
        with self.assertRaises(DataValidationError):
            validate_dataframe(None, ['value'])
    
    def test_validate_dataframe_wrong_type(self):
        """Test DataFrame validation with wrong type."""
        with self.assertRaises(DataValidationError):
            validate_dataframe("not a dataframe", ['value'])
    
    def test_validate_dataframe_insufficient_rows(self):
        """Test DataFrame validation with insufficient rows."""
        empty_df = pd.DataFrame()
        with self.assertRaises(DataValidationError):
            validate_dataframe(empty_df, ['value'], min_rows=1)
    
    def test_validate_dataframe_missing_columns(self):
        """Test DataFrame validation with missing columns."""
        with self.assertRaises(DataValidationError):
            validate_dataframe(self.sample_df, ['missing_column'])
    
    def test_validate_field_name_success(self):
        """Test successful field name validation."""
        result = validate_field_name("parameters")
        self.assertTrue(result)
    
    def test_validate_field_name_empty(self):
        """Test field name validation with empty string."""
        with self.assertRaises(ValidationError):
            validate_field_name("")
    
    def test_validate_field_name_wrong_type(self):
        """Test field name validation with wrong type."""
        with self.assertRaises(ValidationError):
            validate_field_name(123)
    
    def test_validate_field_name_invalid_chars(self):
        """Test field name validation with invalid characters."""
        with self.assertRaises(ValidationError):
            validate_field_name("field<name>")
    
    def test_validate_field_name_too_long(self):
        """Test field name validation with too long name."""
        long_name = "a" * 101
        with self.assertRaises(ValidationError):
            validate_field_name(long_name)
    
    def test_validate_run_id_range_success(self):
        """Test successful run ID range validation."""
        result = validate_run_id_range(1, 100)
        self.assertTrue(result)
    
    def test_validate_run_id_range_none_values(self):
        """Test run ID range validation with None values."""
        result = validate_run_id_range(None, None)
        self.assertTrue(result)
    
    def test_validate_run_id_range_negative(self):
        """Test run ID range validation with negative values."""
        with self.assertRaises(ValidationError):
            validate_run_id_range(-1, 100)
        
        with self.assertRaises(ValidationError):
            validate_run_id_range(1, -100)
    
    def test_validate_run_id_range_wrong_type(self):
        """Test run ID range validation with wrong types."""
        with self.assertRaises(ValidationError):
            validate_run_id_range("1", 100)
        
        with self.assertRaises(ValidationError):
            validate_run_id_range(1, "100")
    
    def test_validate_run_id_range_invalid_range(self):
        """Test run ID range validation with invalid range."""
        with self.assertRaises(ValidationError):
            validate_run_id_range(100, 1)
    
    def test_validate_figsize_success(self):
        """Test successful figsize validation."""
        result = validate_figsize((12, 8))
        self.assertTrue(result)
    
    def test_validate_figsize_wrong_type(self):
        """Test figsize validation with wrong type."""
        with self.assertRaises(ValidationError):
            validate_figsize("not a tuple")
    
    def test_validate_figsize_wrong_length(self):
        """Test figsize validation with wrong length."""
        with self.assertRaises(ValidationError):
            validate_figsize((12, 8, 6))
    
    def test_validate_figsize_negative_values(self):
        """Test figsize validation with negative values."""
        with self.assertRaises(ValidationError):
            validate_figsize((-12, 8))
    
    def test_validate_figsize_too_large(self):
        """Test figsize validation with too large values."""
        with self.assertRaises(ValidationError):
            validate_figsize((100, 100))
    
    def test_validate_na_values_success(self):
        """Test successful N/A values validation."""
        result = validate_na_values(['n/a', 'N/A', 'unknown'])
        self.assertTrue(result)
    
    def test_validate_na_values_wrong_type(self):
        """Test N/A values validation with wrong type."""
        with self.assertRaises(ValidationError):
            validate_na_values("not a list")
    
    def test_validate_na_values_empty(self):
        """Test N/A values validation with empty list."""
        with self.assertRaises(ValidationError):
            validate_na_values([])
    
    def test_validate_na_values_non_string(self):
        """Test N/A values validation with non-string elements."""
        with self.assertRaises(ValidationError):
            validate_na_values(['n/a', 123])
    
    def test_validate_csv_file_success(self):
        """Test successful CSV file validation."""
        result = validate_csv_file(self.temp_csv.name)
        self.assertTrue(result)
    
    def test_validate_csv_file_nonexistent(self):
        """Test CSV file validation with nonexistent file."""
        with self.assertRaises(ValidationError):
            validate_csv_file("nonexistent.csv")
    
    def test_validate_csv_file_wrong_extension(self):
        """Test CSV file validation with wrong extension."""
        temp_txt = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        temp_txt.write("test")
        temp_txt.close()
        
        try:
            with self.assertRaises(ValidationError):
                validate_csv_file(temp_txt.name)
        finally:
            os.unlink(temp_txt.name)
    
    def test_validate_arxiv_id_success(self):
        """Test successful ArXiv ID validation."""
        result = validate_arxiv_id("1234.5678")
        self.assertTrue(result)
        
        result = validate_arxiv_id("1234.5678v1")
        self.assertTrue(result)
    
    def test_validate_arxiv_id_empty(self):
        """Test ArXiv ID validation with empty string."""
        with self.assertRaises(ValidationError):
            validate_arxiv_id("")
    
    def test_validate_arxiv_id_wrong_type(self):
        """Test ArXiv ID validation with wrong type."""
        with self.assertRaises(ValidationError):
            validate_arxiv_id(1234.5678)
    
    def test_validate_arxiv_id_invalid_format(self):
        """Test ArXiv ID validation with invalid format."""
        with self.assertRaises(ValidationError):
            validate_arxiv_id("invalid_id")
    
    def test_validate_date_range_success(self):
        """Test successful date range validation."""
        start_date = pd.Timestamp('2020-01-01')
        end_date = pd.Timestamp('2021-01-01')
        result = validate_date_range(start_date, end_date)
        self.assertTrue(result)
    
    def test_validate_date_range_none_values(self):
        """Test date range validation with None values."""
        result = validate_date_range(None, None)
        self.assertTrue(result)
    
    def test_validate_date_range_invalid_range(self):
        """Test date range validation with invalid range."""
        start_date = pd.Timestamp('2021-01-01')
        end_date = pd.Timestamp('2020-01-01')
        with self.assertRaises(ValidationError):
            validate_date_range(start_date, end_date)
    
    def test_validate_numeric_data_success(self):
        """Test successful numeric data validation."""
        data = pd.Series(['175', '11', '70', 'n/a'])
        result = validate_numeric_data(data, 'test_field')
        
        self.assertEqual(result['total_count'], 4)
        self.assertEqual(result['valid_count'], 3)
        self.assertEqual(result['invalid_count'], 1)
        self.assertAlmostEqual(result['valid_percentage'], 75.0)
    
    def test_validate_numeric_data_empty(self):
        """Test numeric data validation with empty data."""
        data = pd.Series([])
        with self.assertRaises(DataValidationError):
            validate_numeric_data(data, 'test_field')
    
    def test_validate_numeric_data_no_valid(self):
        """Test numeric data validation with no valid numeric values."""
        data = pd.Series(['n/a', 'unknown', 'not specified'])
        with self.assertRaises(DataValidationError):
            validate_numeric_data(data, 'test_field')
    
    def test_validate_configuration_success(self):
        """Test successful configuration validation."""
        config = {
            'na_values': ['n/a', 'N/A'],
            'common_fields': ['parameters', 'architecture'],
            'plot_settings': {'figsize': (12, 8)}
        }
        result = validate_configuration(config)
        self.assertTrue(result)
    
    def test_validate_configuration_missing_key(self):
        """Test configuration validation with missing key."""
        config = {
            'na_values': ['n/a', 'N/A']
            # Missing 'common_fields' and 'plot_settings'
        }
        with self.assertRaises(ConfigurationError):
            validate_configuration(config)
    
    def test_validate_configuration_invalid_na_values(self):
        """Test configuration validation with invalid N/A values."""
        config = {
            'na_values': [],  # Empty list
            'common_fields': ['parameters'],
            'plot_settings': {}
        }
        with self.assertRaises(ValidationError):
            validate_configuration(config)
    
    def test_is_valid_arxiv_id_success(self):
        """Test is_valid_arxiv_id with valid ID."""
        result = is_valid_arxiv_id("1234.5678")
        self.assertTrue(result)
    
    def test_is_valid_arxiv_id_invalid(self):
        """Test is_valid_arxiv_id with invalid ID."""
        result = is_valid_arxiv_id("invalid_id")
        self.assertFalse(result)
    
    def test_is_valid_field_name_success(self):
        """Test is_valid_field_name with valid name."""
        result = is_valid_field_name("parameters")
        self.assertTrue(result)
    
    def test_is_valid_field_name_invalid(self):
        """Test is_valid_field_name with invalid name."""
        result = is_valid_field_name("field<name>")
        self.assertFalse(result)
    
    def test_is_valid_csv_file_success(self):
        """Test is_valid_csv_file with valid file."""
        result = is_valid_csv_file(self.temp_csv.name)
        self.assertTrue(result)
    
    def test_is_valid_csv_file_invalid(self):
        """Test is_valid_csv_file with invalid file."""
        result = is_valid_csv_file("nonexistent.csv")
        self.assertFalse(result)
    
    def test_get_validation_summary_success(self):
        """Test get_validation_summary with valid data."""
        result = get_validation_summary(self.sample_df, 'test_field')
        
        self.assertEqual(result['field_name'], 'test_field')
        self.assertEqual(result['total_rows'], 3)
        self.assertTrue(result['is_valid'])
        self.assertEqual(len(result['errors']), 0)
    
    def test_get_validation_summary_invalid_data(self):
        """Test get_validation_summary with invalid data."""
        invalid_df = pd.DataFrame({'wrong_column': [1, 2, 3]})
        result = get_validation_summary(invalid_df, 'test_field')
        
        self.assertFalse(result['is_valid'])
        self.assertGreater(len(result['errors']), 0)


if __name__ == '__main__':
    unittest.main()
