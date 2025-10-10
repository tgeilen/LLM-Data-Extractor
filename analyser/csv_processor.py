"""
CSV Data Processing Module

This module provides functions for processing external CSV data and integrating it
with the database for enhanced trend analysis.
"""

import pandas as pd
import numpy as np
import re
from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path
import logging

from db.db_utils import get_connection
from .config import CSV_SETTINGS, DEFAULT_NA_VALUES
from .validation import (
    validate_csv_file, validate_na_values, validate_arxiv_id,
    ValidationError, DataValidationError, safe_execute
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CSVProcessor:
    """
    Class for processing CSV files and integrating with database.
    """
    
    def __init__(self, na_values: Optional[List[str]] = None):
        """
        Initialize CSV processor.
        
        Args:
            na_values: List of values to treat as N/A
        
        Raises:
            ValidationError: If na_values is invalid
        """
        self.na_values = na_values or DEFAULT_NA_VALUES
        
        # Validate N/A values
        try:
            validate_na_values(self.na_values)
        except ValidationError as e:
            logger.warning(f"Invalid N/A values provided: {e}")
            self.na_values = DEFAULT_NA_VALUES
        
        self.arxiv_patterns = CSV_SETTINGS['arxiv_patterns']
    
    def process_csv_with_arxiv_lookup(
        self,
        csv_file_path: str,
        link_column: str = None,
        parameters_column: str = None
    ) -> Optional[pd.DataFrame]:
        """
        Process CSV file to extract ArXiv IDs from links and match with database publication dates.
        
        Args:
            csv_file_path: Path to the CSV file
            link_column: Name of the column containing links
            parameters_column: Name of the column containing parameters
        
        Returns:
            DataFrame with columns ['arxiv_id', 'publication_date', 'parameters']
        """
        link_column = link_column or CSV_SETTINGS['default_link_column']
        parameters_column = parameters_column or CSV_SETTINGS['default_parameters_column']
        
        logger.info(f"Processing CSV file: {csv_file_path}")
        
        try:
            # Validate CSV file
            validate_csv_file(csv_file_path)
            
            # Read the CSV file
            df = pd.read_csv(csv_file_path)
            logger.info(f"Loaded CSV with {len(df)} rows")
            
            # Validate columns
            if not self._validate_columns(df, link_column, parameters_column):
                return None
            
            # Filter for rows with links and parameters
            filtered_df = df[[link_column, parameters_column]].dropna()
            logger.info(f"Found {len(filtered_df)} rows with both link and parameters data")
            
            # Extract ArXiv IDs
            extracted_data = self._extract_arxiv_ids(filtered_df, link_column, parameters_column)
            if not extracted_data:
                return pd.DataFrame(columns=['arxiv_id', 'publication_date', 'parameters'])
            
            # Match with database
            result_df = self._match_with_database(extracted_data)
            
            logger.info(f"Final dataset: {len(result_df)} papers with ArXiv ID, publication date, and parameters")
            return result_df
            
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return None
        except FileNotFoundError:
            logger.error(f"File not found: {csv_file_path}")
            return None
        except Exception as e:
            logger.error(f"Error processing CSV: {e}")
            return None
    
    def _validate_columns(self, df: pd.DataFrame, link_column: str, parameters_column: str) -> bool:
        """Validate that required columns exist in the DataFrame."""
        if link_column not in df.columns:
            logger.error(f"Column '{link_column}' not found in CSV")
            logger.info(f"Available columns: {list(df.columns)}")
            return False
            
        if parameters_column not in df.columns:
            logger.error(f"Column '{parameters_column}' not found in CSV")
            logger.info(f"Available columns: {list(df.columns)}")
            return False
        
        return True
    
    def _extract_arxiv_ids(
        self,
        df: pd.DataFrame,
        link_column: str,
        parameters_column: str
    ) -> List[Dict[str, Any]]:
        """Extract ArXiv IDs from links in the DataFrame."""
        arxiv_ids = []
        parameters_list = []
        
        for idx, row in df.iterrows():
            link = str(row[link_column]).strip()
            parameters = row[parameters_column]
            
            arxiv_id = self._extract_arxiv_id_from_link(link)
            if arxiv_id:
                arxiv_ids.append(arxiv_id)
                parameters_list.append(parameters)
        
        logger.info(f"Extracted {len(arxiv_ids)} ArXiv IDs from links")
        
        # Create DataFrame and remove duplicates
        extracted_df = pd.DataFrame({
            'arxiv_id': arxiv_ids,
            'parameters': parameters_list
        }).drop_duplicates(subset=['arxiv_id'])
        
        logger.info(f"Unique ArXiv IDs: {len(extracted_df)}")
        
        return extracted_df.to_dict('records')
    
    def _extract_arxiv_id_from_link(self, link: str) -> Optional[str]:
        """Extract ArXiv ID from a single link using various patterns."""
        for pattern in self.arxiv_patterns:
            match = re.search(pattern, link, re.IGNORECASE)
            if match:
                arxiv_id = match.group(1)
                # Validate the extracted ArXiv ID
                try:
                    validate_arxiv_id(arxiv_id)
                    return arxiv_id
                except ValidationError:
                    logger.warning(f"Invalid ArXiv ID extracted: {arxiv_id}")
                    continue
        return None
    
    def _match_with_database(self, extracted_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Match extracted ArXiv IDs with database publication dates."""
        if not extracted_data:
            return pd.DataFrame(columns=['arxiv_id', 'publication_date', 'parameters'])
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Build query to get publication dates
        arxiv_ids = [item['arxiv_id'] for item in extracted_data]
        placeholders = ','.join(['%s'] * len(arxiv_ids))
        
        query = f"""
        SELECT arxiv_id, published_date 
        FROM papers 
        WHERE arxiv_id IN ({placeholders})
        AND published_date IS NOT NULL
        """
        
        cursor.execute(query, arxiv_ids)
        db_results = cursor.fetchall()
        conn.close()
        
        logger.info(f"Found {len(db_results)} papers in database with publication dates")
        
        # Create DataFrame from database results
        db_df = pd.DataFrame(db_results, columns=['arxiv_id', 'publication_date'])
        
        # Create DataFrame from extracted data
        extracted_df = pd.DataFrame(extracted_data)
        
        # Merge with database data
        result_df = extracted_df.merge(db_df, on='arxiv_id', how='inner')
        
        # Convert publication_date to datetime
        result_df['publication_date'] = pd.to_datetime(result_df['publication_date'], utc=True)
        
        # Reorder columns
        result_df = result_df[['arxiv_id', 'publication_date', 'parameters']]
        
        return result_df
    
    def explore_csv_structure(self, csv_file_path: str, show_sample_rows: int = 5) -> Optional[pd.DataFrame]:
        """
        Explore the structure of a CSV file to understand its columns and data.
        
        Args:
            csv_file_path: Path to the CSV file
            show_sample_rows: Number of sample rows to display
        
        Returns:
            The loaded DataFrame for further inspection
        """
        logger.info(f"Exploring CSV file structure: {csv_file_path}")
        
        try:
            df = pd.read_csv(csv_file_path)
            
            print(f"\n Basic Information:")
            print(f"  • Total rows: {len(df)}")
            print(f"  • Total columns: {len(df.columns)}")
            print(f"  • File size: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
            
            print(f"\n Column Names:")
            for i, col in enumerate(df.columns, 1):
                print(f"  {i:2d}. {col}")
            
            # Analyze link column
            self._analyze_link_column(df)
            
            # Analyze parameters column
            self._analyze_parameters_column(df)
            
            # Show sample data
            self._show_sample_data(df, show_sample_rows)
            
            return df
            
        except FileNotFoundError:
            logger.error(f"File not found: {csv_file_path}")
            return None
        except Exception as e:
            logger.error(f"Error reading CSV: {e}")
            return None
    
    def _analyze_link_column(self, df: pd.DataFrame) -> None:
        """Analyze the link column for ArXiv links."""
        print(f"\n Link Column Analysis:")
        if 'Link' in df.columns:
            link_col = df['Link'].dropna()
            print(f"  • Non-null links: {len(link_col)}/{len(df)} ({len(link_col)/len(df)*100:.1f}%)")
            
            # Check for ArXiv links
            arxiv_links = link_col[link_col.str.contains('arxiv', case=False, na=False)]
            print(f"  • ArXiv links: {len(arxiv_links)} ({len(arxiv_links)/len(link_col)*100:.1f}% of links)")
            
            if len(arxiv_links) > 0:
                print(f"  • Sample ArXiv links:")
                for link in arxiv_links.head(3):
                    print(f"    - {link}")
        else:
            print("  • 'Link' column not found")
    
    def _analyze_parameters_column(self, df: pd.DataFrame) -> None:
        """Analyze the parameters column."""
        print(f"\n Parameters Column Analysis:")
        if 'Parameters' in df.columns:
            params_col = df['Parameters'].dropna()
            print(f"  • Non-null parameters: {len(params_col)}/{len(df)} ({len(params_col)/len(df)*100:.1f}%)")
            
            if len(params_col) > 0:
                print(f"  • Sample parameter values:")
                for param in params_col.head(3):
                    print(f"    - {param}")
        else:
            print("  • 'Parameters' column not found")
    
    def _show_sample_data(self, df: pd.DataFrame, show_sample_rows: int) -> None:
        """Show sample data from the DataFrame."""
        print(f"\n Sample Data (first {show_sample_rows} rows):")
        if 'Link' in df.columns and 'Parameters' in df.columns:
            sample_cols = ['Link', 'Parameters']
            if 'Model' in df.columns:
                sample_cols.insert(0, 'Model')
            print(df[sample_cols].head(show_sample_rows).to_string(index=False))
        else:
            print(df.head(show_sample_rows).to_string(index=False))
    
    def extract_arxiv_ids_preview(self, csv_file_path: str, max_examples: int = None) -> List[str]:
        """
        Preview ArXiv ID extraction without database lookup.
        
        Args:
            csv_file_path: Path to the CSV file
            max_examples: Maximum number of examples to show
        
        Returns:
            List of extracted ArXiv IDs
        """
        max_examples = max_examples or CSV_SETTINGS['max_preview_examples']
        
        logger.info(f"Previewing ArXiv ID extraction from: {csv_file_path}")
        
        try:
            df = pd.read_csv(csv_file_path)
            
            if 'Link' not in df.columns:
                logger.error("'Link' column not found")
                return []
            
            link_col = df['Link'].dropna()
            extracted_ids = []
            extraction_details = []
            
            for link in link_col:
                link_str = str(link).strip()
                arxiv_id = self._extract_arxiv_id_from_link(link_str)
                
                if arxiv_id:
                    extracted_ids.append(arxiv_id)
                    # Find which pattern matched
                    for i, pattern in enumerate(self.arxiv_patterns):
                        if re.search(pattern, link_str, re.IGNORECASE):
                            method = ['abs URL', 'pdf URL', 'direct ID', 'versioned ID'][i]
                            extraction_details.append((link_str, arxiv_id, method))
                            break
            
            print(f"\n Extracted {len(extracted_ids)} ArXiv IDs from {len(link_col)} links")
            print(f" Success rate: {len(extracted_ids)/len(link_col)*100:.1f}%")
            
            if extraction_details:
                print(f"\n Examples (showing up to {max_examples}):")
                for i, (original, extracted, method) in enumerate(extraction_details[:max_examples], 1):
                    print(f"  {i:2d}. {extracted} ({method})")
                    print(f"      From: {original[:80]}{'...' if len(original) > 80 else ''}")
            
            # Show unique IDs
            unique_ids = list(set(extracted_ids))
            print(f"\n Unique ArXiv IDs: {len(unique_ids)}")
            
            return unique_ids
            
        except Exception as e:
            logger.error(f"Error: {e}")
            return []


# Utility functions for CSV processing
def compare_csv_with_extractions(
    csv_df: pd.DataFrame,
    field_name: str = 'parameters',
    run_id_start: Optional[int] = None,
    run_id_end: Optional[int] = None,
    figsize: Tuple[int, int] = (16, 10),
    log_scale: bool = True,
    csv_label: str = "CSV Data",
    db_label: str = "Database Extractions"
) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    Compare CSV data with database extractions on the same plot.
    
    Args:
        csv_df: DataFrame from process_csv_with_arxiv_lookup()
        field_name: Field name to compare from database extractions
        run_id_start/end: Run ID range for database extractions
        figsize: Figure size for the plot
        log_scale: Whether to use logarithmic scale
        csv_label: Label for CSV data in legend
        db_label: Label for database extractions in legend
    
    Returns:
        Tuple of (csv_df, db_extractions_df) for further analysis
    """
    import matplotlib.pyplot as plt
    from .trend_analysis import TrendAnalyzer
    
    if csv_df is None or csv_df.empty:
        logger.error("No CSV data provided")
        return None, None
    
    logger.info(f"Comparing CSV data ({len(csv_df)} papers) with database extractions...")
    
    # Use TrendAnalyzer to get database data
    analyzer = TrendAnalyzer()
    db_df = analyzer._get_field_data(field_name, run_id_start, run_id_end)
    
    if db_df is None or db_df.empty:
        logger.error(f"No database extractions found for field '{field_name}'")
        return csv_df, None
    
    # Process and compare the data
    # This would involve creating a comparison plot similar to the notebook
    # For now, return the dataframes for further processing
    
    return csv_df, db_df
