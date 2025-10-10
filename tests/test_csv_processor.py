"""
Unit tests for CSV processor module.
"""

import unittest
import pandas as pd
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
import sys

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyser.csv_processor import CSVProcessor, compare_csv_with_extractions
from analyser.validation import ValidationError


class TestCSVProcessor(unittest.TestCase):
    """Test cases for CSVProcessor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary CSV file for testing
        self.temp_csv = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        self.temp_csv.write('Link,Parameters\n')
        self.temp_csv.write('https://arxiv.org/abs/1234.5678,175 billion\n')
        self.temp_csv.write('https://arxiv.org/abs/1234.5679,11 billion\n')
        self.temp_csv.write('https://arxiv.org/abs/1234.5680,70 billion\n')
        self.temp_csv.close()
        
        # Create a CSV with invalid data
        self.temp_csv_invalid = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        self.temp_csv_invalid.write('Link,Parameters\n')
        self.temp_csv_invalid.write('invalid_link,175 billion\n')
        self.temp_csv_invalid.write('https://arxiv.org/abs/invalid_id,11 billion\n')
        self.temp_csv_invalid.close()
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_csv.name):
            os.unlink(self.temp_csv.name)
        if os.path.exists(self.temp_csv_invalid.name):
            os.unlink(self.temp_csv_invalid.name)
    
    def test_init_success(self):
        """Test successful CSVProcessor initialization."""
        processor = CSVProcessor()
        self.assertIsNotNone(processor)
        self.assertIsInstance(processor.na_values, list)
        self.assertGreater(len(processor.na_values), 0)
        self.assertIsInstance(processor.arxiv_patterns, list)
    
    def test_init_with_custom_na_values(self):
        """Test CSVProcessor initialization with custom N/A values."""
        custom_na = ['custom1', 'custom2']
        processor = CSVProcessor(na_values=custom_na)
        self.assertEqual(processor.na_values, custom_na)
    
    @patch('analyser.csv_processor.validate_na_values')
    def test_init_validation_error(self, mock_validate):
        """Test CSVProcessor initialization with validation error."""
        mock_validate.side_effect = ValidationError("Invalid N/A values")
        
        # Should not raise exception, just use default values
        processor = CSVProcessor(na_values=['invalid'])
        self.assertNotEqual(processor.na_values, ['invalid'])
    
    @patch('analyser.csv_processor.validate_csv_file')
    @patch('analyser.csv_processor.pd.read_csv')
    def test_process_csv_with_arxiv_lookup_success(self, mock_read_csv, mock_validate):
        """Test successful CSV processing with ArXiv lookup."""
        mock_validate.return_value = True
        
        # Mock CSV data
        mock_df = pd.DataFrame({
            'Link': [
                'https://arxiv.org/abs/1234.5678',
                'https://arxiv.org/abs/1234.5679'
            ],
            'Parameters': ['175 billion', '11 billion']
        })
        mock_read_csv.return_value = mock_df
        
        # Mock database connection
        with patch('analyser.csv_processor.get_connection') as mock_get_connection:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_get_connection.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            
            # Mock database results
            mock_db_results = [
                ('1234.5678', '2020-01-15'),
                ('1234.5679', '2021-03-20')
            ]
            mock_cursor.fetchall.return_value = mock_db_results
            
            processor = CSVProcessor()
            result = processor.process_csv_with_arxiv_lookup(
                self.temp_csv.name,
                link_column='Link',
                parameters_column='Parameters'
            )
            
            self.assertIsInstance(result, pd.DataFrame)
            self.assertEqual(len(result), 2)
            self.assertEqual(list(result.columns), ['arxiv_id', 'publication_date', 'parameters'])
            
            mock_conn.close.assert_called_once()
    
    @patch('analyser.csv_processor.validate_csv_file')
    def test_process_csv_with_arxiv_lookup_validation_error(self, mock_validate):
        """Test CSV processing with validation error."""
        mock_validate.side_effect = ValidationError("Invalid CSV file")
        
        processor = CSVProcessor()
        result = processor.process_csv_with_arxiv_lookup(self.temp_csv.name)
        
        self.assertIsNone(result)
    
    @patch('analyser.csv_processor.validate_csv_file')
    @patch('analyser.csv_processor.pd.read_csv')
    def test_process_csv_with_arxiv_lookup_file_not_found(self, mock_read_csv, mock_validate):
        """Test CSV processing with file not found."""
        mock_validate.side_effect = FileNotFoundError("File not found")
        
        processor = CSVProcessor()
        result = processor.process_csv_with_arxiv_lookup("nonexistent.csv")
        
        self.assertIsNone(result)
    
    def test_validate_columns_success(self):
        """Test successful column validation."""
        df = pd.DataFrame({
            'Link': ['link1', 'link2'],
            'Parameters': ['param1', 'param2']
        })
        
        processor = CSVProcessor()
        result = processor._validate_columns(df, 'Link', 'Parameters')
        
        self.assertTrue(result)
    
    def test_validate_columns_missing_link_column(self):
        """Test column validation with missing link column."""
        df = pd.DataFrame({
            'Parameters': ['param1', 'param2']
        })
        
        processor = CSVProcessor()
        result = processor._validate_columns(df, 'Link', 'Parameters')
        
        self.assertFalse(result)
    
    def test_validate_columns_missing_parameters_column(self):
        """Test column validation with missing parameters column."""
        df = pd.DataFrame({
            'Link': ['link1', 'link2']
        })
        
        processor = CSVProcessor()
        result = processor._validate_columns(df, 'Link', 'Parameters')
        
        self.assertFalse(result)
    
    def test_extract_arxiv_id_from_link_success(self):
        """Test successful ArXiv ID extraction from various link formats."""
        processor = CSVProcessor()
        
        test_cases = [
            ('https://arxiv.org/abs/1234.5678', '1234.5678'),
            ('https://arxiv.org/pdf/1234.5678.pdf', '1234.5678'),
            ('1234.5678', '1234.5678'),
            ('1234.5678v1', '1234.5678'),
            ('invalid_link', None)
        ]
        
        for link, expected in test_cases:
            result = processor._extract_arxiv_id_from_link(link)
            self.assertEqual(result, expected)
    
    @patch('analyser.csv_processor.validate_arxiv_id')
    def test_extract_arxiv_id_from_link_validation_error(self, mock_validate):
        """Test ArXiv ID extraction with validation error."""
        mock_validate.side_effect = ValidationError("Invalid ArXiv ID")
        
        processor = CSVProcessor()
        result = processor._extract_arxiv_id_from_link('https://arxiv.org/abs/1234.5678')
        
        self.assertIsNone(result)
    
    def test_extract_arxiv_ids_success(self):
        """Test successful ArXiv ID extraction from DataFrame."""
        df = pd.DataFrame({
            'Link': [
                'https://arxiv.org/abs/1234.5678',
                'https://arxiv.org/abs/1234.5679',
                'invalid_link'
            ],
            'Parameters': ['175 billion', '11 billion', '70 billion']
        })
        
        processor = CSVProcessor()
        result = processor._extract_arxiv_ids(df, 'Link', 'Parameters')
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)  # Only valid ArXiv IDs
        self.assertEqual(result[0]['arxiv_id'], '1234.5678')
        self.assertEqual(result[1]['arxiv_id'], '1234.5679')
    
    @patch('analyser.csv_processor.get_connection')
    def test_match_with_database_success(self, mock_get_connection):
        """Test successful database matching."""
        # Mock database connection
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock database results
        mock_db_results = [
            ('1234.5678', '2020-01-15'),
            ('1234.5679', '2021-03-20')
        ]
        mock_cursor.fetchall.return_value = mock_db_results
        
        extracted_data = [
            {'arxiv_id': '1234.5678', 'parameters': '175 billion'},
            {'arxiv_id': '1234.5679', 'parameters': '11 billion'},
            {'arxiv_id': '1234.5680', 'parameters': '70 billion'}  # Not in database
        ]
        
        processor = CSVProcessor()
        result = processor._match_with_database(extracted_data)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)  # Only matched records
        self.assertEqual(list(result.columns), ['arxiv_id', 'publication_date', 'parameters'])
        
        mock_conn.close.assert_called_once()
    
    def test_match_with_database_empty_data(self):
        """Test database matching with empty data."""
        processor = CSVProcessor()
        result = processor._match_with_database([])
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 0)
        self.assertEqual(list(result.columns), ['arxiv_id', 'publication_date', 'parameters'])
    
    @patch('analyser.csv_processor.pd.read_csv')
    def test_explore_csv_structure_success(self, mock_read_csv):
        """Test successful CSV structure exploration."""
        mock_df = pd.DataFrame({
            'Link': ['https://arxiv.org/abs/1234.5678', 'https://arxiv.org/abs/1234.5679'],
            'Parameters': ['175 billion', '11 billion'],
            'Model': ['GPT-3', 'GPT-4']
        })
        mock_read_csv.return_value = mock_df
        
        processor = CSVProcessor()
        result = processor.explore_csv_structure(self.temp_csv.name, show_sample_rows=2)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
    
    @patch('analyser.csv_processor.pd.read_csv')
    def test_explore_csv_structure_file_not_found(self, mock_read_csv):
        """Test CSV structure exploration with file not found."""
        mock_read_csv.side_effect = FileNotFoundError("File not found")
        
        processor = CSVProcessor()
        result = processor.explore_csv_structure("nonexistent.csv")
        
        self.assertIsNone(result)
    
    @patch('analyser.csv_processor.pd.read_csv')
    def test_extract_arxiv_ids_preview_success(self, mock_read_csv):
        """Test successful ArXiv ID extraction preview."""
        mock_df = pd.DataFrame({
            'Link': [
                'https://arxiv.org/abs/1234.5678',
                'https://arxiv.org/abs/1234.5679',
                'invalid_link'
            ]
        })
        mock_read_csv.return_value = mock_df
        
        processor = CSVProcessor()
        result = processor.extract_arxiv_ids_preview(self.temp_csv.name, max_examples=5)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)  # Only valid ArXiv IDs
        self.assertIn('1234.5678', result)
        self.assertIn('1234.5679', result)
    
    @patch('analyser.csv_processor.pd.read_csv')
    def test_extract_arxiv_ids_preview_file_not_found(self, mock_read_csv):
        """Test ArXiv ID extraction preview with file not found."""
        mock_read_csv.side_effect = FileNotFoundError("File not found")
        
        processor = CSVProcessor()
        result = processor.extract_arxiv_ids_preview("nonexistent.csv")
        
        self.assertEqual(result, [])


class TestCompareCSVWithExtractions(unittest.TestCase):
    """Test cases for compare_csv_with_extractions function."""
    
    def test_compare_csv_with_extractions_no_csv_data(self):
        """Test comparison with no CSV data."""
        result = compare_csv_with_extractions(None, 'parameters')
        
        self.assertEqual(result, (None, None))
    
    def test_compare_csv_with_extractions_empty_csv_data(self):
        """Test comparison with empty CSV data."""
        empty_df = pd.DataFrame()
        result = compare_csv_with_extractions(empty_df, 'parameters')
        
        self.assertEqual(result, (None, None))
    
    @patch('analyser.trend_analysis.TrendAnalyzer')
    def test_compare_csv_with_extractions_success(self, mock_analyzer_class):
        """Test successful CSV comparison with database extractions."""
        # Mock CSV data
        csv_df = pd.DataFrame({
            'arxiv_id': ['1234.5678', '1234.5679'],
            'publication_date': pd.to_datetime(['2020-01-15', '2021-03-20']),
            'parameters': ['175 billion', '11 billion']
        })
        
        # Mock database data
        db_df = pd.DataFrame({
            'value': ['175 billion', '11 billion'],
            'confidence': [95, 90],
            'run_id': [1, 2],
            'published_date': pd.to_datetime(['2020-01-15', '2021-03-20']),
            'arxiv_id': ['1234.5678', '1234.5679'],
            'model_provider': ['deepseek', 'anthropic']
        })
        
        # Mock TrendAnalyzer
        mock_analyzer = Mock()
        mock_analyzer._get_field_data.return_value = db_df
        mock_analyzer_class.return_value = mock_analyzer
        
        result = compare_csv_with_extractions(csv_df, 'parameters')
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertIsNotNone(result[0])  # CSV data
        self.assertIsNotNone(result[1])  # DB data
    
    @patch('analyser.trend_analysis.TrendAnalyzer')
    def test_compare_csv_with_extractions_no_db_data(self, mock_analyzer_class):
        """Test CSV comparison with no database data."""
        # Mock CSV data
        csv_df = pd.DataFrame({
            'arxiv_id': ['1234.5678'],
            'publication_date': pd.to_datetime(['2020-01-15']),
            'parameters': ['175 billion']
        })
        
        # Mock TrendAnalyzer
        mock_analyzer = Mock()
        mock_analyzer._get_field_data.return_value = None
        mock_analyzer_class.return_value = mock_analyzer
        
        result = compare_csv_with_extractions(csv_df, 'parameters')
        
        self.assertEqual(result, (csv_df, None))


if __name__ == '__main__':
    unittest.main()
