"""
Trend Analysis Module for Research Paper Data

This module provides functions for analyzing trends in extracted fields from research papers
over time, including visualization, statistical analysis, and data integration capabilities.
"""

import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import re
import json
from typing import Optional, List, Tuple, Dict, Union
from pathlib import Path

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.db_utils import get_connection
from .validation import (
    validate_analysis_parameters, validate_dataframe, validate_database_connection,
    ValidationError, DataValidationError, safe_execute
)


class TrendAnalyzer:
    """
    Main class for trend analysis operations.
    
    This class encapsulates all trend analysis functionality and provides
    a clean interface for analyzing research paper data trends.
    """
    
    def __init__(self, default_na_values: Optional[List[str]] = None):
        """
        Initialize the TrendAnalyzer.
        
        Args:
            default_na_values: List of values to treat as N/A by default
        """
        self.default_na_values = default_na_values or [
            'n/a', '', 'N/A', 'unknown', 'None', 'null', 'not specified',
            'not available', 'not reported', 'unclear', '-'
        ]
        
        # Validate database connection on initialization
        try:
            validate_database_connection()
        except ValidationError as e:
            print(f"️ Database validation warning: {e}")
        
        # Set up matplotlib style
        plt.style.use('default')
        sns.set_palette("husl")
    
    def visualize_field_trends(
        self,
        field_name: str,
        run_id_start: Optional[int] = None,
        run_id_end: Optional[int] = None,
        figsize: Tuple[int, int] = (12, 10),
        show_numeric_trend: bool = True,
        na_values: Optional[List[str]] = None,
        log_scale: bool = False
    ) -> Optional[pd.DataFrame]:
        """
        Visualize trends in extracted field values over time.
        
        Args:
            field_name: Name of the field to analyze (e.g., 'parameters', 'architecture')
            run_id_start: Starting extraction run ID (inclusive)
            run_id_end: Ending extraction run ID (inclusive)
            figsize: Figure size for the plot
            show_numeric_trend: Whether to show trend line for numeric values
            na_values: Custom list of values to treat as N/A
            log_scale: Whether to use logarithmic scale for y-axis
        
        Returns:
            DataFrame with the data used for plotting, or None if no data found
        
        Raises:
            ValidationError: If input parameters are invalid
        """
        na_values = na_values or self.default_na_values
        
        # Validate all input parameters
        try:
            validate_analysis_parameters(field_name, run_id_start, run_id_end, figsize, na_values)
        except ValidationError as e:
            print(f" Validation error: {e}")
            return None
        
        print(f" Analyzing {field_name} field trends...")
        if log_scale:
            print(" Using logarithmic scale for y-axis")
        
        # Get data from database
        df = self._get_field_data(field_name, run_id_start, run_id_end)
        if df is None or df.empty:
            return None
        
        # Validate the retrieved data
        try:
            validate_dataframe(df, ['value', 'published_date', 'arxiv_id'], min_rows=1)
        except DataValidationError as e:
            print(f" Data validation error: {e}")
            return None
        
        # Process and visualize data
        self._process_and_visualize_data(
            df, field_name, figsize, show_numeric_trend, na_values, log_scale
        )
        
        return df
    
    def _get_field_data(
        self,
        field_name: str,
        run_id_start: Optional[int] = None,
        run_id_end: Optional[int] = None
    ) -> Optional[pd.DataFrame]:
        """Get field data from database with optional run ID filtering."""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT ef.value, ef.confidence, ef.run_id, p.published_date, p.arxiv_id, 
                   COALESCE(m.provider, 'unknown') as model_provider
            FROM extracted_fields ef
            JOIN extraction_runs er ON ef.run_id = er.id
            JOIN papers p ON er.paper_id = p.id
            LEFT JOIN models m ON er.model_id = m.id
            WHERE ef.field_name = %s
            AND p.published_date IS NOT NULL
            """
            params = [field_name]
            
            if run_id_start is not None:
                query += " AND ef.run_id >= %s"
                params.append(run_id_start)
            if run_id_end is not None:
                query += " AND ef.run_id <= %s"
                params.append(run_id_end)
            
            query += " ORDER BY p.published_date"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if not results:
                print(f" No data found for field '{field_name}'")
                return None
            
            df = pd.DataFrame(results, columns=[
                'value', 'confidence', 'run_id', 'published_date', 'arxiv_id', 'model_provider'
            ])
            df['published_date'] = pd.to_datetime(df['published_date'], utc=True)
            
            print(f" Found {len(df)} data points")
            print(f" Date range: {df['published_date'].min()} to {df['published_date'].max()}")
            print(f" Run ID range: {df['run_id'].min()} to {df['run_id'].max()}")
            
            return df
            
        except Exception as e:
            print(f" Error querying database: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def _process_and_visualize_data(
        self,
        df: pd.DataFrame,
        field_name: str,
        figsize: Tuple[int, int],
        show_numeric_trend: bool,
        na_values: List[str],
        log_scale: bool
    ) -> None:
        """Process data and create visualization."""
        # Identify N/A values
        na_mask = df['value'].isin(na_values)
        print(f"N/A values found: {na_mask.sum()} ({na_mask.sum() / len(df) * 100:.1f}%)")
        
        # Extract numeric values
        df['numeric_value'] = df['value'].apply(self._extract_numeric)
        
        
        numeric_mask = ~pd.isna(df['numeric_value'])
        
        print(f"Numeric values extracted: {numeric_mask.sum()} ({numeric_mask.sum() / len(df) * 100:.1f}%)")
        
        # Create visualization
        self._create_trend_plot(
            df, field_name, figsize, show_numeric_trend, na_values, log_scale,
            numeric_mask, na_mask
        )
        
        # Print statistics
        self._print_statistics(df, field_name, numeric_mask, na_mask, log_scale)
    
    def _extract_numeric(self, value: str) -> float:
        """Extract numeric value from text, handling various formats."""
        if pd.isna(value):
            return np.nan
        
        value_str = str(value).lower().strip()
        
        # Handle scientific notation (e format)
        e_sci_match = re.search(r'(\d+\.?\d*)\s*e\s*(\d+)', value_str)
        if e_sci_match:
            base, exp = float(e_sci_match.group(1)), int(e_sci_match.group(2))
            return base * (10 ** exp)
        
        # Handle scientific notation (× 10^ format)
        sci_match = re.search(r'(\d+\.?\d*)\s*[×x*]\s*10\^?(\d+)', value_str)
        if sci_match:
            base, exp = float(sci_match.group(1)), int(sci_match.group(2))
            return base * (10 ** exp)
        
        # Handle billions
        billion_match = re.search(r'(\d+\.?\d*)\s*b(?:illion)?', value_str)
        if billion_match:
            return float(billion_match.group(1)) * 1_000_000_000
        
        # Handle millions
        million_match = re.search(r'(\d+\.?\d*)\s*m(?:illion)?', value_str)
        if million_match:
            return float(million_match.group(1)) * 1_000_000
        
        # Handle thousands
        thousand_match = re.search(r'(\d+\.?\d*)\s*(?:thousand|k(?:ilo)?)', value_str)
        if thousand_match:
            return float(thousand_match.group(1)) * 1_000
        
        # Handle raw numbers
        number_match = re.search(r'(\d+\.?\d*)', value_str)
        if number_match:
            return float(number_match.group(1))
        
        return np.nan
    
    def _create_trend_plot(
        self,
        df: pd.DataFrame,
        field_name: str,
        figsize: Tuple[int, int],
        show_numeric_trend: bool,
        na_values: List[str],
        log_scale: bool,
        numeric_mask: pd.Series,
        na_mask: pd.Series
    ) -> None:
        """Create the main trend visualization plot."""
        fig, axes = plt.subplots(2, 1, figsize=figsize, sharex=True)
        ax1, ax2 = axes
        
        # Get unique providers for color mapping
        providers = df['model_provider'].unique()
        colors = plt.cm.Set3(np.linspace(0, 1, len(providers)))
        provider_colors = dict(zip(providers, colors))
        
        # Plot numeric values by provider
        for provider in providers:
            mask = (df['model_provider'] == provider) & numeric_mask
            if mask.sum() > 0:
                ax1.scatter(df[mask]['published_date'], df[mask]['numeric_value'], 
                           c=[provider_colors[provider]], label=f'{provider} (numeric)',
                           alpha=0.7, s=60)
        
        # Add trend line if requested
        if show_numeric_trend and numeric_mask.sum() > 2:
            self._add_trend_line(df, numeric_mask, ax1, log_scale)
        
        # Set scale and labels
        if log_scale and numeric_mask.sum() > 0:
            positive_values = df[numeric_mask]['numeric_value']
            if (positive_values > 0).sum() > 0:
                ax1.set_yscale('log')
                ax1.set_ylabel(f'{field_name} (log scale)')
            else:
                print("️ Cannot use log scale: no positive values found")
                ax1.set_ylabel(f'{field_name}')
        else:
            ax1.set_ylabel(f'{field_name} (Millions if numeric)')
        
        # Plot N/A values
        self._plot_na_values(df, na_mask, ax1, log_scale, numeric_mask, provider_colors)
        
        # Configure main plot
        ax1.set_xlabel('Publication Date')
        scale_info = " (log scale)" if log_scale else ""
        ax1.set_title(f'Trend Analysis: {field_name} Over Time{scale_info}')
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax1.grid(True, alpha=0.3)
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        
        # Bottom plot: Confidence distribution
        self._create_confidence_plot(df, na_mask, ax2)
        
        plt.tight_layout()
        plt.show()
    
    def _add_trend_line(
        self,
        df: pd.DataFrame,
        numeric_mask: pd.Series,
        ax: plt.Axes,
        log_scale: bool
    ) -> None:
        """Add trend line to the plot."""
        try:
            numeric_df = df[numeric_mask].copy()
            numeric_df['date_numeric'] = numeric_df['published_date'].astype('int64') // 10**9
            
            if log_scale:
                positive_mask = numeric_df['numeric_value'] > 0
                if positive_mask.sum() > 2:
                    log_numeric_df = numeric_df[positive_mask].copy()
                    log_values = np.log10(log_numeric_df['numeric_value'])
                    z = np.polyfit(log_numeric_df['date_numeric'], log_values, 1)
                    p = np.poly1d(z)
                    trend_log_values = p(log_numeric_df['date_numeric'])
                    trend_values = 10 ** trend_log_values
                    ax.plot(log_numeric_df['published_date'], trend_values,
                           "r--", alpha=0.8, linewidth=2, label='Trend (log scale)')
            else:
                z = np.polyfit(numeric_df['date_numeric'], numeric_df['numeric_value'], 1)
                p = np.poly1d(z)
                ax.plot(numeric_df['published_date'], p(numeric_df['date_numeric']),
                       "r--", alpha=0.8, linewidth=2, label='Trend (numeric)')
        except Exception as e:
            print(f"️ Could not compute trend line: {e}")
    
    def _plot_na_values(
        self,
        df: pd.DataFrame,
        na_mask: pd.Series,
        ax: plt.Axes,
        log_scale: bool,
        numeric_mask: pd.Series,
        provider_colors: Dict[str, str]
    ) -> None:
        """Plot N/A values on the chart."""
        if na_mask.sum() > 0:
            providers = df['model_provider'].unique()
            
            if log_scale:
                min_positive = df[numeric_mask & (df['numeric_value'] > 0)]['numeric_value'].min() if (df[numeric_mask]['numeric_value'] > 0).sum() > 0 else 0.001
                y_na = min_positive / 10
            else:
                current_ylim = ax.get_ylim()
                y_na = current_ylim[0] - 0.05 * (current_ylim[1] - current_ylim[0])
            
            for provider in providers:
                mask = (df['model_provider'] == provider) & na_mask
                if mask.sum() > 0:
                    ax.scatter(df[mask]['published_date'], [y_na] * mask.sum(),
                             c=[provider_colors[provider]], label=f'{provider} (N/A)',
                             alpha=0.5, s=30, marker='x')
    
    def _create_confidence_plot(self, df: pd.DataFrame, na_mask: pd.Series, ax: plt.Axes) -> None:
        """Create the confidence distribution subplot."""
        confidence_colors = ['red' if na else 'gray' for na in na_mask]
        ax.scatter(df['published_date'], df['confidence'], alpha=0.6, c=confidence_colors, s=30)
        ax.set_xlabel('Publication Date')
        ax.set_ylabel('Confidence')
        ax.set_title('Extraction Confidence Over Time (Red = N/A values)')
        ax.grid(True, alpha=0.3)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    def _print_statistics(
        self,
        df: pd.DataFrame,
        field_name: str,
        numeric_mask: pd.Series,
        na_mask: pd.Series,
        log_scale: bool
    ) -> None:
        """Print comprehensive statistics."""
        print(f"\n Statistics for '{field_name}':")
        print(f"  • Total extractions: {len(df)}")
        print(f"  • Numeric values found: {numeric_mask.sum()}")
        print(f"  • N/A values: {na_mask.sum()} ({na_mask.sum()/len(df)*100:.1f}%)")
        print(f"  • Average confidence: {df['confidence'].mean():.1f}")
        print(f"  • Average confidence (excluding N/A): {df[~na_mask]['confidence'].mean():.1f}")
        print(f"  • Unique models: {df['model_provider'].nunique()}")
        print(f"  • Model providers: {', '.join(df['model_provider'].unique())}")
        
        if numeric_mask.sum() > 0:
            numeric_data = df[numeric_mask]['numeric_value']
            if log_scale:
                print(f"  • Value range: {numeric_data.min():.0f} - {numeric_data.max():.0f}")
            else:
                max_val = numeric_data.max()
                if max_val > 1_000_000:
                    print(f"  • Numeric range: {numeric_data.min()/1_000_000:.2f}M - {max_val/1_000_000:.2f}M")
                else:
                    print(f"  • Value range: {numeric_data.min():.0f} - {max_val:.0f}")


# Utility functions for data exploration
def explore_available_fields(run_id_start: Optional[int] = None, run_id_end: Optional[int] = None) -> pd.DataFrame:
    """
    Explore what fields are available in the database and their frequency.
    
    Args:
        run_id_start: Starting extraction run ID (inclusive)
        run_id_end: Ending extraction run ID (inclusive)
    
    Returns:
        DataFrame with field information
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
    SELECT ef.field_name, COUNT(*) as count,
           MIN(ef.run_id) as min_run_id,
           MAX(ef.run_id) as max_run_id
    FROM extracted_fields ef
    """
    
    params = []
    if run_id_start is not None or run_id_end is not None:
        query += " WHERE"
        conditions = []
        if run_id_start is not None:
            conditions.append("ef.run_id >= %s")
            params.append(run_id_start)
        if run_id_end is not None:
            conditions.append("ef.run_id <= %s")
            params.append(run_id_end)
        query += " " + " AND ".join(conditions)
    
    query += " GROUP BY ef.field_name ORDER BY count DESC"
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    
    df = pd.DataFrame(results, columns=['field_name', 'count', 'min_run_id', 'max_run_id'])
    
    print(" Available Fields in Database:")
    print("=" * 60)
    for _, row in df.iterrows():
        print(f"  {row['field_name']:<20} | Count: {row['count']:<6} | Run IDs: {row['min_run_id']}-{row['max_run_id']}")
    
    return df


def get_run_id_ranges() -> Dict[str, Union[int, str]]:
    """
    Get information about extraction run ID ranges.
    
    Returns:
        Dictionary with run ID information
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
    SELECT 
        MIN(er.id) as min_run_id,
        MAX(er.id) as max_run_id,
        COUNT(*) as total_runs,
        COUNT(DISTINCT p.id) as unique_papers,
        MIN(p.published_date) as earliest_paper,
        MAX(p.published_date) as latest_paper
    FROM extraction_runs er
    JOIN papers p ON er.paper_id = p.id
    WHERE p.published_date IS NOT NULL
    """
    
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()
    
    if result is None:
        return {
            'min_run_id': None,
            'max_run_id': None,
            'total_runs': 0,
            'unique_papers': 0,
            'earliest_paper': None,
            'latest_paper': None
        }
    
    run_info = {
        'min_run_id': result[0],
        'max_run_id': result[1],
        'total_runs': result[2],
        'unique_papers': result[3],
        'earliest_paper': result[4],
        'latest_paper': result[5]
    }
    
    print(" Extraction Run Information:")
    print("=" * 40)
    print(f"  Run ID range: {run_info['min_run_id']} - {run_info['max_run_id']}")
    print(f"  Total runs: {run_info['total_runs']}")
    print(f"  Unique papers: {run_info['unique_papers']}")
    print(f"  Paper date range: {run_info['earliest_paper']} to {run_info['latest_paper']}")
    
    return run_info
