"""
Unit tests for trend analysis module.
"""

import unittest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyser.trend_analysis import TrendAnalyzer, explore_available_fields, get_run_id_ranges
from analyser.validation import ValidationError, DataValidationError


class TestTrendAnalyzer(unittest.TestCase):
    """Test cases for TrendAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_data = pd.DataFrame({
            'value': ['175 billion', '11 billion', '70 billion', 'n/a'],
            'confidence': [95, 90, 85, 70],
            'run_id': [1, 2, 3, 4],
            'published_date': pd.to_datetime(['2020-01-15', '2021-03-20', '2022-07-10', '2023-01-01']),
            'arxiv_id': ['1234.5678', '1234.5679', '1234.5680', '1234.5681'],
            'model_provider': ['deepseek', 'anthropic', 'deepseek', 'anthropic']
        })
    
    @patch('analyser.trend_analysis.validate_database_connection')
    def test_init_success(self, mock_validate):
        """Test successful TrendAnalyzer initialization."""
        mock_validate.return_value = True
        
        analyzer = TrendAnalyzer()
        self.assertIsNotNone(analyzer)
        self.assertIsInstance(analyzer.default_na_values, list)
        self.assertGreater(len(analyzer.default_na_values), 0)
    
    @patch('analyser.trend_analysis.validate_database_connection')
    def test_init_with_custom_na_values(self, mock_validate):
        """Test TrendAnalyzer initialization with custom N/A values."""
        mock_validate.return_value = True
        
        custom_na = ['custom1', 'custom2']
        analyzer = TrendAnalyzer(default_na_values=custom_na)
        self.assertEqual(analyzer.default_na_values, custom_na)
    
    @patch('analyser.trend_analysis.validate_database_connection')
    def test_init_database_validation_warning(self, mock_validate):
        """Test TrendAnalyzer initialization with database validation warning."""
        mock_validate.side_effect = ValidationError("Database connection failed")
        
        # Should not raise exception, just print warning
        analyzer = TrendAnalyzer()
        self.assertIsNotNone(analyzer)
    
    @patch('analyser.trend_analysis.validate_analysis_parameters')
    @patch('analyser.trend_analysis.TrendAnalyzer._get_field_data')
    @patch('analyser.trend_analysis.validate_dataframe')
    @patch('analyser.trend_analysis.TrendAnalyzer._process_and_visualize_data')
    def test_visualize_field_trends_success(self, mock_process, mock_validate_df, 
                                          mock_get_data, mock_validate_params):
        """Test successful field trends visualization."""
        mock_validate_params.return_value = True
        mock_get_data.return_value = self.sample_data
        mock_validate_df.return_value = True
        mock_process.return_value = None
        
        analyzer = TrendAnalyzer()
        result = analyzer.visualize_field_trends('parameters')
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 4)
        mock_validate_params.assert_called_once()
        mock_get_data.assert_called_once()
        mock_validate_df.assert_called_once()
        mock_process.assert_called_once()
    
    @patch('analyser.trend_analysis.validate_analysis_parameters')
    def test_visualize_field_trends_validation_error(self, mock_validate):
        """Test field trends visualization with validation error."""
        mock_validate.side_effect = ValidationError("Invalid parameters")
        
        analyzer = TrendAnalyzer()
        result = analyzer.visualize_field_trends('invalid_field')
        
        self.assertIsNone(result)
    
    @patch('analyser.trend_analysis.validate_analysis_parameters')
    @patch('analyser.trend_analysis.TrendAnalyzer._get_field_data')
    def test_visualize_field_trends_no_data(self, mock_get_data, mock_validate):
        """Test field trends visualization with no data."""
        mock_validate.return_value = True
        mock_get_data.return_value = None
        
        analyzer = TrendAnalyzer()
        result = analyzer.visualize_field_trends('parameters')
        
        self.assertIsNone(result)
    
    @patch('analyser.trend_analysis.validate_analysis_parameters')
    @patch('analyser.trend_analysis.TrendAnalyzer._get_field_data')
    @patch('analyser.trend_analysis.validate_dataframe')
    def test_visualize_field_trends_data_validation_error(self, mock_validate_df, 
                                                        mock_get_data, mock_validate):
        """Test field trends visualization with data validation error."""
        mock_validate.return_value = True
        mock_get_data.return_value = self.sample_data
        mock_validate_df.side_effect = DataValidationError("Invalid data")
        
        analyzer = TrendAnalyzer()
        result = analyzer.visualize_field_trends('parameters')
        
        self.assertIsNone(result)
    
    def test_extract_numeric_success(self):
        """Test successful numeric value extraction."""
        analyzer = TrendAnalyzer()
        
        # Test various formats
        test_cases = [
            ('175 billion', 175_000_000_000),
            ('11 million', 11_000_000),
            ('70 thousand', 70_000),
            ('1234', 1234),
            ('1.5 billion', 1_500_000_000),
            ('2.5e9', 2_500_000_000),
            ('n/a', np.nan),
            ('unknown', np.nan)
        ]
        
        for input_val, expected in test_cases:
            result = analyzer._extract_numeric(input_val)
            if np.isnan(expected):
                self.assertTrue(np.isnan(result))
            else:
                self.assertEqual(result, expected)
    
    def test_extract_numeric_edge_cases(self):
        """Test numeric extraction with edge cases."""
        analyzer = TrendAnalyzer()
        
        # Test None input
        result = analyzer._extract_numeric(None)
        self.assertTrue(np.isnan(result))
        
        # Test empty string
        result = analyzer._extract_numeric('')
        self.assertTrue(np.isnan(result))
        
        # Test non-numeric string
        result = analyzer._extract_numeric('not a number')
        self.assertTrue(np.isnan(result))


class TestUtilityFunctions(unittest.TestCase):
    """Test cases for utility functions."""
    
    @patch('analyser.trend_analysis.get_connection')
    def test_explore_available_fields_success(self, mock_get_connection):
        """Test successful exploration of available fields."""
        # Mock database connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock query results
        mock_results = [
            ('parameters', 100, 1, 50),
            ('architecture', 80, 1, 40),
            ('dataset', 60, 1, 30)
        ]
        mock_cursor.fetchall.return_value = mock_results
        
        result = explore_available_fields()
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 3)
        self.assertEqual(list(result.columns), ['field_name', 'count', 'min_run_id', 'max_run_id'])
        
        mock_conn.close.assert_called_once()
    
    @patch('analyser.trend_analysis.get_connection')
    def test_explore_available_fields_with_filters(self, mock_get_connection):
        """Test exploration of available fields with run ID filters."""
        # Mock database connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock query results
        mock_results = [('parameters', 50, 10, 30)]
        mock_cursor.fetchall.return_value = mock_results
        
        result = explore_available_fields(run_id_start=10, run_id_end=30)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)
        
        # Verify the query was called with parameters
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        self.assertIn('WHERE', call_args[0][0])
        self.assertIn('ef.run_id >= %s', call_args[0][0])
        self.assertIn('ef.run_id <= %s', call_args[0][0])
    
    @patch('analyser.trend_analysis.get_connection')
    def test_get_run_id_ranges_success(self, mock_get_connection):
        """Test successful retrieval of run ID ranges."""
        # Mock database connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock query result
        mock_result = (1, 100, 50, 25, '2020-01-01', '2023-12-31')
        mock_cursor.fetchone.return_value = mock_result
        
        result = get_run_id_ranges()
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['min_run_id'], 1)
        self.assertEqual(result['max_run_id'], 100)
        self.assertEqual(result['total_runs'], 50)
        self.assertEqual(result['unique_papers'], 25)
        
        mock_conn.close.assert_called_once()
    
    @patch('analyser.trend_analysis.get_connection')
    def test_get_run_id_ranges_no_data(self, mock_get_connection):
        """Test run ID ranges retrieval with no data."""
        # Mock database connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock empty result
        mock_cursor.fetchone.return_value = None
        
        result = get_run_id_ranges()
        
        self.assertIsInstance(result, dict)
        # Should handle None result gracefully
        mock_conn.close.assert_called_once()


class TestTrendAnalyzerIntegration(unittest.TestCase):
    """Integration tests for TrendAnalyzer."""
    
    @patch('analyser.trend_analysis.get_connection')
    def test_get_field_data_success(self, mock_get_connection):
        """Test successful field data retrieval."""
        # Mock database connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock query results
        mock_results = [
            ('175 billion', 95, 1, '2020-01-15', '1234.5678', 'deepseek'),
            ('11 billion', 90, 2, '2021-03-20', '1234.5679', 'anthropic')
        ]
        mock_cursor.fetchall.return_value = mock_results
        
        analyzer = TrendAnalyzer()
        result = analyzer._get_field_data('parameters')
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        self.assertEqual(list(result.columns), [
            'value', 'confidence', 'run_id', 'published_date', 'arxiv_id', 'model_provider'
        ])
        
        mock_conn.close.assert_called_once()
    
    @patch('analyser.trend_analysis.get_connection')
    def test_get_field_data_no_results(self, mock_get_connection):
        """Test field data retrieval with no results."""
        # Mock database connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock empty results
        mock_cursor.fetchall.return_value = []
        
        analyzer = TrendAnalyzer()
        result = analyzer._get_field_data('nonexistent_field')
        
        self.assertIsNone(result)
        mock_conn.close.assert_called_once()
    
    @patch('analyser.trend_analysis.get_connection')
    def test_get_field_data_with_run_id_filters(self, mock_get_connection):
        """Test field data retrieval with run ID filters."""
        # Mock database connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock query results
        mock_results = [('175 billion', 95, 1, '2020-01-15', '1234.5678', 'deepseek')]
        mock_cursor.fetchall.return_value = mock_results
        
        analyzer = TrendAnalyzer()
        result = analyzer._get_field_data('parameters', run_id_start=1, run_id_end=10)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)
        
        # Verify the query was called with parameters
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        self.assertIn('ef.run_id >= %s', call_args[0][0])
        self.assertIn('ef.run_id <= %s', call_args[0][0])
        self.assertEqual(call_args[0][1], ['parameters', 1, 10])


if __name__ == '__main__':
    unittest.main()
