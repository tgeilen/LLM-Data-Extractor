"""
Domain Analysis Module

This module provides specialized functions for analyzing publication trends,
model characteristics, and domain-specific patterns in the research data.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from typing import Optional, List, Dict, Tuple, Union
import sys
import os
import re

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.db_utils import get_connection
from .trend_analysis import TrendAnalyzer
from .validation import validate_field_name, validate_run_id_range, ValidationError


class DomainAnalyzer:
    """
    Specialized analyzer for domain-specific research trends and patterns.
    
    This class extends the basic TrendAnalyzer with domain-focused analysis
    capabilities for publication trends, model characteristics, and cross-domain comparisons.
    """
    
    def __init__(self, default_na_values: Optional[List[str]] = None, title_fontsize: int = 18):
        """
        Initialize the DomainAnalyzer.
        
        Args:
            default_na_values: List of values to treat as N/A by default
            title_fontsize: Font size for chart titles (default: 24)
        """
        self.trend_analyzer = TrendAnalyzer(default_na_values)
        self.default_na_values = default_na_values or [
            'n/a', '', 'N/A', 'unknown', 'None', 'null', 'not specified',
            'not available', 'not reported', 'unclear', '-'
        ]
        self.title_fontsize = title_fontsize
        
        # Set up unified plotting style and color palette
        self._setup_plotting_style()
        self._setup_color_palette()
    
    def _setup_plotting_style(self):
        """Set up consistent plotting style for all charts optimized for A4 print."""
        plt.style.use('default')
        plt.rcParams.update({
            'figure.facecolor': 'white',
            'axes.facecolor': 'white',
            'axes.grid': True,
            'grid.alpha': 0.3,
            'grid.color': 'lightgray',
            'axes.edgecolor': 'black',
            'axes.linewidth': 0.8,
            'font.size': 18,  # Significantly increased for A4 print readability
            'axes.titlesize': 24,  # Much larger for titles
            'axes.labelsize': 20,  # Much larger for axis labels
            'xtick.labelsize': 18,  # Much larger for tick labels
            'ytick.labelsize': 18,  # Much larger for tick labels
            'legend.fontsize': 18,  # Much larger for legends
            'figure.titlesize': 28  # Much larger for figure titles
        })
    
    def _setup_color_palette(self):
        """Set up unified color palette for all charts."""
        # Primary color palette - professional and accessible
        self.primary_colors = [
            '#1f77b4',  # Blue
            '#ff7f0e',  # Orange
            '#2ca02c',  # Green
            '#d62728',  # Red
            '#9467bd',  # Purple
            '#8c564b',  # Brown
            '#e377c2',  # Pink
            '#7f7f7f',  # Gray
            '#bcbd22',  # Olive
            '#17becf'   # Cyan
        ]
        
        # Secondary color palette for additional categories
        self.secondary_colors = [
            '#aec7e8',  # Light Blue
            '#ffbb78',  # Light Orange
            '#98df8a',  # Light Green
            '#ff9896',  # Light Red
            '#c5b0d5',  # Light Purple
            '#c49c94',  # Light Brown
            '#f7b6d3',  # Light Pink
            '#c7c7c7',  # Light Gray
            '#dbdb8d',  # Light Olive
            '#9edae5'   # Light Cyan
        ]
        
        # Specialized palettes for different chart types
        self.heatmap_palette = 'viridis'  # Professional heatmap colors
        self.pie_palette = 'Set3'  # Distinct colors for pie charts
        self.gradient_palette = 'Blues'  # For gradients and sequential data
        
        # Set seaborn palette
        sns.set_palette(self.primary_colors)
    
    def _get_colors(self, n_colors: int, palette_type: str = 'primary') -> List[str]:
        """
        Get a list of colors from the specified palette.
        
        Args:
            n_colors: Number of colors needed
            palette_type: 'primary', 'secondary', or 'mixed'
        
        Returns:
            List of color codes
        """
        if palette_type == 'primary':
            base_colors = self.primary_colors
        elif palette_type == 'secondary':
            base_colors = self.secondary_colors
        elif palette_type == 'mixed':
            base_colors = self.primary_colors + self.secondary_colors
        else:
            base_colors = self.primary_colors
        
        # Cycle through colors if we need more than available
        if n_colors <= len(base_colors):
            return base_colors[:n_colors]
        else:
            # Repeat colors if needed
            return (base_colors * ((n_colors // len(base_colors)) + 1))[:n_colors]
    
    def _apply_chart_style(self, ax, chart_type: str = 'default'):
        """
        Apply consistent styling to a chart axis.
        
        Args:
            ax: Matplotlib axis object
            chart_type: Type of chart for specific styling
        """
        # Common styling
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('black')
        ax.spines['bottom'].set_color('black')
        
        # Chart-specific styling
        if chart_type == 'bar':
            ax.set_axisbelow(True)
        elif chart_type == 'line':
            ax.set_axisbelow(True)
        elif chart_type == 'pie':
            ax.set_aspect('equal')
        elif chart_type == 'scatter':
            ax.set_axisbelow(True)
    
    def _sort_stacked_chart_data(self, df_pivot: pd.DataFrame) -> pd.DataFrame:
        """
        Sort stacked chart data so the largest value is at the bottom and others are sorted by size above.
        
        Args:
            df_pivot: Pivot table with data for stacked chart
        
        Returns:
            Sorted pivot table with columns reordered
        """
        # Calculate total values for each column
        column_totals = df_pivot.sum().sort_values(ascending=False)
        
        # Reorder columns: largest total first (will be at bottom of stack)
        sorted_columns = column_totals.index.tolist()
        
        return df_pivot[sorted_columns]
    
    def _format_year_labels(self, ax, rotation: int = 45):
        """
        Format x-axis labels to show only year values for datetime indices.
        
        Args:
            ax: Matplotlib axis object
            rotation: Rotation angle for labels
        """
        # Get current x-axis labels
        labels = ax.get_xticklabels()
        
        # Format labels to show only year
        formatted_labels = []
        for label in labels:
            try:
                # Try to parse as datetime and extract year
                if hasattr(label, '_text'):
                    text = label._text
                else:
                    text = str(label)
                
                # Handle different datetime formats
                if isinstance(text, str) and len(text) > 4:
                    # Extract year from datetime string
                    year = text.split('-')[0] if '-' in text else text[:4]
                    formatted_labels.append(year)
                else:
                    formatted_labels.append(text)
            except:
                # Fallback to original text if parsing fails
                formatted_labels.append(str(label))
        
        # Set the formatted labels
        ax.set_xticklabels(formatted_labels, rotation=rotation)
    
    def _parse_array_values(self, value: str, field_name: str = None, excluded_values: List[str] = None) -> List[str]:
        """
        Parse array-like values from database fields.
        
        Handles formats like:
        - {value1, value2, value3}
        - [value1, value2, value3]
        - "value1, value2, value3"
        - Single values
        
        Special handling for modality fields:
        - If "multimodal" is not present but multiple values exist, add "multimodal"
        - If "multimodal" is already present, count it normally
        
        Args:
            value: String value that may contain array-like data
            field_name: Name of the field (for special handling)
            excluded_values: List of values to exclude from the result
        
        Returns:
            List of individual values (excluding specified values)
        """
        if pd.isna(value) or value in self.default_na_values:
            return []
        
        value_str = str(value).strip()
        
        # Handle empty values
        if not value_str or value_str.lower() in ['none', 'null', '']:
            return []
        
        # Handle curly brace format: {value1, value2, value3}
        if value_str.startswith('{') and value_str.endswith('}'):
            inner = value_str[1:-1].strip()
            if inner:
                parsed_values = [v.strip().strip('"\'') for v in inner.split(',') if v.strip()]
            else:
                parsed_values = []
        # Handle square bracket format: [value1, value2, value3]
        elif value_str.startswith('[') and value_str.endswith(']'):
            inner = value_str[1:-1].strip()
            if inner:
                parsed_values = [v.strip().strip('"\'') for v in inner.split(',') if v.strip()]
            else:
                parsed_values = []
        # Handle quoted format: "value1, value2, value3"
        elif value_str.startswith('"') and value_str.endswith('"'):
            inner = value_str[1:-1].strip()
            if inner:
                parsed_values = [v.strip().strip('"\'') for v in inner.split(',') if v.strip()]
            else:
                parsed_values = []
        # Handle comma-separated values
        elif ',' in value_str:
            parsed_values = [v.strip().strip('"\'') for v in value_str.split(',') if v.strip()]
        # Single value
        else:
            parsed_values = [value_str.strip().strip('"\'')]
        
        # Special handling for modality fields
        if field_name and ('modality' in field_name.lower() or 'modalities' in field_name.lower()):
            # Check if we have multiple values and "multimodal" is not already present
            if len(parsed_values) > 1 and 'multimodal' not in [v.lower() for v in parsed_values]:
                parsed_values.append('multimodal')
        
        # Filter out excluded values
        if excluded_values:
            parsed_values = [v for v in parsed_values if v not in excluded_values]
        
        return parsed_values
    
    def _expand_array_data(self, df: pd.DataFrame, field_name: str, excluded_values: List[str] = None) -> pd.DataFrame:
        """
        Expand DataFrame by parsing array values in a field.
        
        Args:
            df: DataFrame with the field containing array values
            field_name: Name of the field to expand
            excluded_values: List of values to exclude from expansion
        
        Returns:
            Expanded DataFrame with one row per individual value
        """
        if field_name not in df.columns:
            return df
        
        expanded_rows = []
        
        for _, row in df.iterrows():
            values = self._parse_array_values(row[field_name], field_name, excluded_values)
            
            if values:
                # Create one row for each value
                for value in values:
                    if value and value not in self.default_na_values:
                        new_row = row.copy()
                        new_row[field_name] = value
                        expanded_rows.append(new_row)
            # Note: We don't keep the original row if no valid values are found
            # This ensures that filtered values (like "Other") are completely removed
        
        return pd.DataFrame(expanded_rows)
    
    def get_publication_trends(self, 
                             run_id_start: Optional[int] = None,
                             run_id_end: Optional[int] = None,
                             group_by: str = 'year',
                             figsize: Tuple[int, int] = (16, 10)) -> pd.DataFrame:
        """
        Analyze publication trends over time.
        
        Args:
            run_id_start: Starting extraction run ID (inclusive)
            run_id_end: Ending extraction run ID (inclusive)
            group_by: Grouping period ('year', 'month', 'quarter')
            figsize: Figure size for the plot
        
        Returns:
            DataFrame with publication counts by time period
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get publication data with date grouping
            if group_by == 'year':
                date_format = "DATE_TRUNC('year', p.published_date)"
            elif group_by == 'month':
                date_format = "DATE_TRUNC('month', p.published_date)"
            elif group_by == 'quarter':
                date_format = "DATE_TRUNC('quarter', p.published_date)"
            else:
                raise ValueError("group_by must be 'year', 'month', or 'quarter'")
            
            query = f"""
            SELECT 
                {date_format} as period,
                COUNT(DISTINCT p.id) as publication_count,
                COUNT(DISTINCT ef.run_id) as extraction_count
            FROM papers p
            JOIN extraction_runs er ON p.id = er.paper_id
            JOIN extracted_fields ef ON er.id = ef.run_id
            WHERE p.published_date IS NOT NULL
            """
            
            params = []
            if run_id_start is not None:
                query += " AND ef.run_id >= %s"
                params.append(run_id_start)
            if run_id_end is not None:
                query += " AND ef.run_id <= %s"
                params.append(run_id_end)
            
            query += f" GROUP BY {date_format} ORDER BY period"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if not results:
                print(" No publication data found")
                return pd.DataFrame()
            
            df = pd.DataFrame(results, columns=['period', 'publication_count', 'extraction_count'])
            df['period'] = pd.to_datetime(df['period'])
            
            # Create visualization
            fig, ax = plt.subplots(figsize=figsize)
            colors = self._get_colors(1, 'primary')
            ax.bar(df['period'], df['publication_count'], alpha=0.8, color=colors[0], edgecolor='white', linewidth=0.5)
            ax.set_xlabel('Publication Period')
            ax.set_ylabel('Number of Publications')
            ax.set_title(f'Publication Trends by {group_by.title()}', fontsize=self.title_fontsize, fontweight='bold')
            self._apply_chart_style(ax, 'bar')
            
            # Rotate x-axis labels for better readability
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.show()
            
            print(f" Publication Trends Analysis:")
            print(f"  • Total periods: {len(df)}")
            print(f"  • Total publications: {df['publication_count'].sum()}")
            print(f"  • Date range: {df['period'].min()} to {df['period'].max()}")
            print(f"  • Peak period: {df.loc[df['publication_count'].idxmax(), 'period']} ({df['publication_count'].max()} publications)")
            
            return df
            
        except Exception as e:
            print(f" Error analyzing publication trends: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()
    
    def get_domain_trends(self,
                         run_id_start: Optional[int] = None,
                         run_id_end: Optional[int] = None,
                         top_k: int = 10,
                         figsize: Tuple[int, int] = (18, 12)) -> pd.DataFrame:
        """
        Analyze domain trends over time with stacked column chart.
        
        Args:
            run_id_start: Starting extraction run ID (inclusive)
            run_id_end: Ending extraction run ID (inclusive)
            top_k: Number of top domains to show
            figsize: Figure size for the plot
        
        Returns:
            DataFrame with domain trends by year
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get domain data by year
            query = """
            SELECT 
                DATE_TRUNC('year', p.published_date) as year,
                ef.value as domain,
                COUNT(DISTINCT p.id) as publication_count
            FROM papers p
            JOIN extraction_runs er ON p.id = er.paper_id
            JOIN extracted_fields ef ON er.id = ef.run_id
            WHERE ef.field_name = 'domain'
            AND p.published_date IS NOT NULL
            AND ef.value NOT IN %s
            """
            
            params = [tuple(self.default_na_values)]
            if run_id_start is not None:
                query += " AND ef.run_id >= %s"
                params.append(run_id_start)
            if run_id_end is not None:
                query += " AND ef.run_id <= %s"
                params.append(run_id_end)
            
            query += " GROUP BY year, domain ORDER BY year, publication_count DESC"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if not results:
                print(" No domain data found")
                return pd.DataFrame()
            
            df = pd.DataFrame(results, columns=['year', 'domain', 'publication_count'])
            df['year'] = pd.to_datetime(df['year'])
            
            # Expand array values in domain field
            df_expanded = self._expand_array_data(df, 'domain')
            
            # Recalculate publication counts after expansion
            df_expanded = df_expanded.groupby(['year', 'domain'])['publication_count'].sum().reset_index()
            
            # Get top K domains overall
            domain_totals = df_expanded.groupby('domain')['publication_count'].sum().sort_values(ascending=False)
            top_domains = domain_totals.head(top_k).index.tolist()
            
            # Filter to top domains
            df_top = df_expanded[df_expanded['domain'].isin(top_domains)]
            
            # Pivot for stacked chart
            df_pivot = df_top.pivot(index='year', columns='domain', values='publication_count').fillna(0)
            
            # Sort data for better stacked chart visualization (largest at bottom)
            df_pivot = self._sort_stacked_chart_data(df_pivot)
            
            # Create stacked column chart
            fig, ax = plt.subplots(figsize=figsize)
            colors = self._get_colors(len(df_pivot.columns), 'primary')
            df_pivot.plot(kind='bar', stacked=True, ax=ax, color=colors, alpha=0.8)
            
            ax.set_xlabel('Year')
            ax.set_ylabel('Number of Publications')
            ax.set_title(f'Top {top_k} Domains by Publication Count Over Time', fontsize=self.title_fontsize, fontweight='bold')
            ax.legend(title='Domain', loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=min(len(df_pivot.columns), 6))
            self._apply_chart_style(ax, 'bar')
            
            # Format year labels to show only year
            self._format_year_labels(ax, rotation=45)
            plt.subplots_adjust(bottom=0.3)  # Extra space for bottom legend with larger fonts
            plt.show()
            
            print(f" Domain Trends Analysis:")
            print(f"  • Top {top_k} domains analyzed")
            print(f"  • Date range: {df['year'].min()} to {df['year'].max()}")
            print(f"  • Total domains: {df['domain'].nunique()}")
            print(f"\nTop domains by total publications:")
            for i, (domain, count) in enumerate(domain_totals.head(top_k).items(), 1):
                print(f"  {i:2d}. {domain}: {count} publications")
            
            return df_pivot
            
        except Exception as e:
            print(f" Error analyzing domain trends: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()
    
    def get_robotics_trends(self,
                           run_id_start: Optional[int] = None,
                           run_id_end: Optional[int] = None,
                           figsize: Tuple[int, int] = (16, 10)) -> pd.DataFrame:
        """
        Analyze robotics-specific trends over time.
        
        Args:
            run_id_start: Starting extraction run ID (inclusive)
            run_id_end: Ending extraction run ID (inclusive)
            figsize: Figure size for the plot
        
        Returns:
            DataFrame with robotics trends
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get robotics data by year
            query = """
            SELECT 
                DATE_TRUNC('year', p.published_date) as year,
                COUNT(DISTINCT p.id) as robotics_publications,
                COUNT(DISTINCT ef.run_id) as robotics_extractions
            FROM papers p
            JOIN extraction_runs er ON p.id = er.paper_id
            JOIN extracted_fields ef ON er.id = ef.run_id
            WHERE ef.field_name = 'domain'
            AND LOWER(ef.value) LIKE '%robot%'
            AND p.published_date IS NOT NULL
            """
            
            params = []
            if run_id_start is not None:
                query += " AND ef.run_id >= %s"
                params.append(run_id_start)
            if run_id_end is not None:
                query += " AND ef.run_id <= %s"
                params.append(run_id_end)
            
            query += " GROUP BY year ORDER BY year"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if not results:
                print(" No robotics data found")
                return pd.DataFrame()
            
            df = pd.DataFrame(results, columns=['year', 'robotics_publications', 'robotics_extractions'])
            df['year'] = pd.to_datetime(df['year'])
            
            # Create visualization
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True)
            colors = self._get_colors(2, 'primary')
            
            # Publications over time
            ax1.bar(df['year'], df['robotics_publications'], alpha=0.8, color=colors[0], edgecolor='white', linewidth=0.5)
            ax1.set_ylabel('Robotics Publications')
            ax1.set_title('Robotics Research Development Over Time', fontsize=self.title_fontsize, fontweight='bold')
            self._apply_chart_style(ax1, 'bar')
            
            # Extractions over time
            ax2.bar(df['year'], df['robotics_extractions'], alpha=0.8, color=colors[1], edgecolor='white', linewidth=0.5)
            ax2.set_xlabel('Year')
            ax2.set_ylabel('Robotics Extractions')
            self._apply_chart_style(ax2, 'bar')
            
            # Format year labels to show only year
            self._format_year_labels(ax1, rotation=45)
            self._format_year_labels(ax2, rotation=45)
            plt.tight_layout()
            plt.show()
            
            print(f" Robotics Trends Analysis:")
            print(f"  • Total robotics publications: {df['robotics_publications'].sum()}")
            print(f"  • Date range: {df['year'].min()} to {df['year'].max()}")
            print(f"  • Peak year: {df.loc[df['robotics_publications'].idxmax(), 'year'].year} ({df['robotics_publications'].max()} publications)")
            
            # Calculate growth rate
            if len(df) > 1:
                first_year = df['robotics_publications'].iloc[0]
                last_year = df['robotics_publications'].iloc[-1]
                years_span = len(df)
                growth_rate = ((last_year / first_year) ** (1 / years_span) - 1) * 100 if first_year > 0 else 0
                print(f"  • Average annual growth rate: {growth_rate:.1f}%")
            
            return df
            
        except Exception as e:
            print(f" Error analyzing robotics trends: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()
    
    def get_parameter_size_analysis(self,
                                  run_id_start: Optional[int] = None,
                                  run_id_end: Optional[int] = None,
                                  log_scale: bool = True,
                                  figsize: Tuple[int, int] = (12, 8)) -> pd.DataFrame:
        """
        Analyze parameter size trends over time.
        
        Args:
            run_id_start: Starting extraction run ID (inclusive)
            run_id_end: Ending extraction run ID (inclusive)
            log_scale: Whether to use logarithmic scale
            figsize: Figure size for the plot
        
        Returns:
            DataFrame with parameter size data
        """
        # Use the existing trend analyzer for parameters
        df = self.trend_analyzer.visualize_field_trends(
            field_name='parameters',
            run_id_start=run_id_start,
            run_id_end=run_id_end,
            log_scale=log_scale,
            figsize=figsize
        )
        
        if df is not None:
            print(f" Parameter Size Analysis:")
            print(f"  • Total models analyzed: {len(df)}")
            print(f"  • Numeric parameter values: {df['numeric_value'].notna().sum()}")
            
            if df['numeric_value'].notna().sum() > 0:
                param_stats = df['numeric_value'].describe()
                print(f"  • Parameter range: {param_stats['min']:,.0f} - {param_stats['max']:,.0f}")
                print(f"  • Median parameters: {param_stats['50%']:,.0f}")
                print(f"  • Mean parameters: {param_stats['mean']:,.0f}")
        
        return df
    
    def get_parameter_trends_with_categories(self,
                                           run_id_start: Optional[int] = None,
                                           run_id_end: Optional[int] = None,
                                           field_name: str = 'parameters',
                                           color_by: str = 'domain',
                                           shape_by: Optional[str] = None,
                                           top_k_categories: int = 10,
                                           log_scale: bool = True,
                                           figsize: Tuple[int, int] = (18, 12)) -> pd.DataFrame:
        """
        Analyze parameter trends over time with categorical coloring and shaping.
        
        Args:
            run_id_start: Starting extraction run ID (inclusive)
            run_id_end: Ending extraction run ID (inclusive)
            field_name: Name of the field to analyze (e.g., 'parameters')
            color_by: Field to use for coloring points (e.g., 'domain', 'architecture')
            shape_by: Field to use for shaping points (e.g., 'architecture', 'organization')
            top_k_categories: Number of top categories to show for each field
            log_scale: Whether to use logarithmic scale for y-axis
            figsize: Figure size for the plot
        
        Returns:
            DataFrame with parameter trends and categorical data
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Build query to get parameter data with categorical fields
            query = f"""
            SELECT 
                p.published_date,
                ef_params.value as {field_name},
                ef_params.confidence,
                ef_color.value as {color_by},
                {f"ef_shape.value as {shape_by}," if shape_by else ""}
                p.arxiv_id,
                COALESCE(m.provider, 'unknown') as model_provider
            FROM papers p
            JOIN extraction_runs er ON p.id = er.paper_id
            JOIN extracted_fields ef_params ON er.id = ef_params.run_id
            JOIN extracted_fields ef_color ON er.id = ef_color.run_id
            {f"JOIN extracted_fields ef_shape ON er.id = ef_shape.run_id" if shape_by else ""}
            LEFT JOIN models m ON er.model_id = m.id
            WHERE ef_params.field_name = '{field_name}'
            AND ef_color.field_name = '{color_by}'
            {f"AND ef_shape.field_name = '{shape_by}'" if shape_by else ""}
            AND p.published_date IS NOT NULL
            AND ef_params.value NOT IN %s
            AND ef_color.value NOT IN %s
            {f"AND ef_shape.value NOT IN %s" if shape_by else ""}
            AND p.published_date >= '2013-01-01'
            AND p.published_date <= '2024-12-31'
            
            """
            
            params = [tuple(self.default_na_values), tuple(self.default_na_values)]
            if shape_by:
                params.append(tuple(self.default_na_values))
            
            if run_id_start is not None:
                query += " AND ef_params.run_id >= %s"
                params.append(run_id_start)
            if run_id_end is not None:
                query += " AND ef_params.run_id <= %s"
                params.append(run_id_end)
            
            query += " ORDER BY p.published_date"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if not results:
                print(f" No {field_name} data found with {color_by} categorization")
                return pd.DataFrame()
            
            # Create DataFrame
            columns = ['published_date', field_name, 'confidence', color_by, 'arxiv_id', 'model_provider']
            if shape_by:
                columns.insert(-2, shape_by)
            
            df = pd.DataFrame(results, columns=columns)
            df['published_date'] = pd.to_datetime(df['published_date'], utc=True)
            
            # Extract numeric values for the main field
            df['numeric_value'] = df[field_name].apply(self.trend_analyzer._extract_numeric)
            
            # Filter out non-numeric values
            df_numeric = df[df['numeric_value'].notna()].copy()
            
            if df_numeric.empty:
                print(f" No numeric {field_name} values found")
                return pd.DataFrame()
            
            # Expand array values for categorical fields
            excluded_values = {}
            if color_by == 'architecture':
                excluded_values[color_by] = ["Other - {High-Level Architecture Name}"]
            if shape_by == 'architecture':
                excluded_values[shape_by] = ["Other - {High-Level Architecture Name}"]
            
            df_expanded = self._expand_array_data(df_numeric, color_by, excluded_values.get(color_by))
            if shape_by:
                df_expanded = self._expand_array_data(df_expanded, shape_by, excluded_values.get(shape_by))
            
            # Additional filtering to ensure "Other" values are completely removed
            if color_by == 'architecture':
                df_expanded = df_expanded[~df_expanded[color_by].str.contains('Other', case=False, na=False)]
            if shape_by == 'architecture':
                df_expanded = df_expanded[~df_expanded[shape_by].str.contains('Other', case=False, na=False)]
            
            # Get top categories for each field
            color_categories = df_expanded[color_by].value_counts().head(top_k_categories).index.tolist()
            df_filtered = df_expanded[df_expanded[color_by].isin(color_categories)]
            
            if shape_by:
                shape_categories = df_filtered[shape_by].value_counts().head(top_k_categories).index.tolist()
                df_filtered = df_filtered[df_filtered[shape_by].isin(shape_categories)]
            
            # Create visualization
            fig, ax = plt.subplots(figsize=figsize)
            
            # Define colors and shapes
            colors = self._get_colors(len(color_categories), 'primary')
            color_map = {cat: colors[i] for i, cat in enumerate(color_categories)}
            
            if shape_by:
                markers = ['o', 's', '^', 'v', 'D', 'p', '*', 'h', 'H', '+', 'x', 'X']
                shape_map = {cat: markers[i % len(markers)] for i, cat in enumerate(shape_categories)}
            
            # Plot points for each color category
            for i, color_cat in enumerate(color_categories):
                cat_data = df_filtered[df_filtered[color_by] == color_cat]
                
                if shape_by:
                    # Plot with both color and shape
                    for j, shape_cat in enumerate(shape_categories):
                        shape_data = cat_data[cat_data[shape_by] == shape_cat]
                        if not shape_data.empty:
                            ax.scatter(shape_data['published_date'], 
                                     shape_data['numeric_value'],
                                     c=color_map[color_cat], 
                                     marker=shape_map[shape_cat],
                                     s=80, alpha=0.7, edgecolors='white', linewidth=0.5,
                                     label=f'{color_cat} + {shape_cat}' if len(shape_categories) > 1 else color_cat)
                else:
                    # Plot with color only
                    ax.scatter(cat_data['published_date'], 
                             cat_data['numeric_value'],
                             c=color_map[color_cat], 
                             marker='o',
                             s=80, alpha=0.7, edgecolors='white', linewidth=0.5,
                             label=color_cat)
            
            # Set log scale if requested
            if log_scale:
                positive_values = df_filtered[df_filtered['numeric_value'] > 0]['numeric_value']
                if len(positive_values) > 0:
                    ax.set_yscale('log')
                    ax.set_ylabel(f'{field_name.title()} (log scale)')
                else:
                    print("️ Cannot use log scale: no positive values found")
                    ax.set_ylabel(f'{field_name.title()}')
            else:
                ax.set_ylabel(f'{field_name.title()}')
            
            ax.set_xlabel('Publication Date')
            ax.set_title(f'{field_name.title()} Trends by {color_by.title()}' + 
                        (f' and {shape_by.title()}' if shape_by else '') + 
                        (' (log scale)' if log_scale else ''), 
                        fontsize=self.title_fontsize, fontweight='bold')
            
            # Position legend below chart
            ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=min(len(color_categories), 4))
            self._apply_chart_style(ax, 'scatter')
            
            # Rotate x-axis labels
            plt.xticks(rotation=45)
            plt.subplots_adjust(bottom=0.3)  # Extra space for bottom legend
            plt.show()
            
            # Print statistics
            print(f" {field_name.title()} Trends with {color_by.title()} Categorization:")
            print(f"  • Total data points: {len(df_filtered)}")
            print(f"  • Date range: {df_filtered['published_date'].min()} to {df_filtered['published_date'].max()}")
            print(f"  • {color_by.title()} categories: {len(color_categories)}")
            if shape_by:
                print(f"  • {shape_by.title()} categories: {len(shape_categories)}")
            
            # Print category statistics
            print(f"\n{color_by.title()} distribution:")
            for cat in color_categories:
                cat_count = len(df_filtered[df_filtered[color_by] == cat])
                cat_avg = df_filtered[df_filtered[color_by] == cat]['numeric_value'].mean()
                print(f"  • {cat}: {cat_count} points, avg {field_name}: {cat_avg:,.0f}")
            
            if shape_by:
                print(f"\n{shape_by.title()} distribution:")
                for cat in shape_categories:
                    cat_count = len(df_filtered[df_filtered[shape_by] == cat])
                    cat_avg = df_filtered[df_filtered[shape_by] == cat]['numeric_value'].mean()
                    print(f"  • {cat}: {cat_count} points, avg {field_name}: {cat_avg:,.0f}")
            
            return df_filtered
            
        except Exception as e:
            print(f" Error analyzing {field_name} trends with categories: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()
    
    def get_parameter_trends_spotlight(self,
                                     run_id_start: Optional[int] = None,
                                     run_id_end: Optional[int] = None,
                                     field_name: str = 'parameters',
                                     category_field: str = 'architecture',
                                     top_k_categories: int = 8,
                                     log_scale: bool = True,
                                     min_value_threshold: float = 10000,
                                     largest_model_only: bool = True,
                                     show_trend_lines: bool = True,
                                     figsize: Tuple[int, int] = (20, 16)) -> pd.DataFrame:
        """
        Create a multi-panel visualization where each subplot highlights one specific category
        while showing all others in grey for context.
        
        Args:
            run_id_start: Starting extraction run ID (inclusive)
            run_id_end: Ending extraction run ID (inclusive)
            field_name: Name of the field to analyze (e.g., 'parameters')
            category_field: Field to use for categorization (e.g., 'architecture', 'domain')
            top_k_categories: Number of top categories to show (will create this many subplots)
            log_scale: Whether to use logarithmic scale for y-axis
            min_value_threshold: Minimum value threshold for trend analysis (default: 10,000)
            largest_model_only: If True, use only the largest model per paper; if False, use all models
            show_trend_lines: If True, display trend lines and calculate growth statistics; if False, show only data points
            figsize: Figure size for the entire multi-panel plot
        
        Returns:
            Tuple of (DataFrame with parameter trends, DataFrame with growth statistics)
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Build query to get parameter data with categorical field
            query = f"""
            SELECT 
                p.published_date,
                ef_params.value as {field_name},
                ef_params.confidence,
                ef_category.value as {category_field},
                p.arxiv_id,
                COALESCE(m.provider, 'unknown') as model_provider
            FROM papers p
            JOIN extraction_runs er ON p.id = er.paper_id
            JOIN extracted_fields ef_params ON er.id = ef_params.run_id
            JOIN extracted_fields ef_category ON er.id = ef_category.run_id
            LEFT JOIN models m ON er.model_id = m.id
            WHERE ef_params.field_name = '{field_name}'
            AND ef_category.field_name = '{category_field}'
            AND p.published_date IS NOT NULL
            AND ef_params.value NOT IN %s
            AND ef_category.value NOT IN %s
            AND p.published_date >= '2013-01-01'
            AND p.published_date <= '2024-12-31'
            """
            
            params = [tuple(self.default_na_values), tuple(self.default_na_values)]
            if run_id_start is not None:
                query += " AND ef_params.run_id >= %s"
                params.append(run_id_start)
            if run_id_end is not None:
                query += " AND ef_params.run_id <= %s"
                params.append(run_id_end)
            
            query += " ORDER BY p.published_date"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if not results:
                print(f" No {field_name} data found with {category_field} categorization")
                return pd.DataFrame()
            
            # Create DataFrame
            df = pd.DataFrame(results, columns=['published_date', field_name, 'confidence', category_field, 'arxiv_id', 'model_provider'])
            df['published_date'] = pd.to_datetime(df['published_date'], utc=True)
            
            # Extract numeric values for the main field
            df['numeric_value'] = df[field_name].apply(self.trend_analyzer._extract_numeric)
            
            # Filter out non-numeric values
            df_numeric = df[df['numeric_value'].notna()].copy()
            
            if df_numeric.empty:
                print(f" No numeric {field_name} values found")
                return pd.DataFrame()
            
            # Apply filtering based on largest_model_only parameter
            if largest_model_only:
                print(f" Filtering to largest model per paper...")
                print(f"  • Total models before filtering: {len(df_numeric)}")
                
                # Group by paper (arxiv_id) and keep the row with maximum numeric_value
                df_filtered_data = df_numeric.loc[df_numeric.groupby('arxiv_id')['numeric_value'].idxmax()].copy()
                
                print(f"  • Total models after filtering: {len(df_filtered_data)}")
                print(f"  • Papers analyzed: {df_filtered_data['arxiv_id'].nunique()}")
            else:
                print(f" Using all models (no filtering)...")
                print(f"  • Total models: {len(df_numeric)}")
                df_filtered_data = df_numeric.copy()
            
            # Expand array values for categorical field, excluding "Other" values
            excluded_values = {}
            if category_field == 'architecture':
                excluded_values[category_field] = ["Other - {High-Level Architecture Name}"]
            
            df_expanded = self._expand_array_data(df_filtered_data, category_field, excluded_values.get(category_field))
            
            # Additional filtering to ensure "Other" values are completely removed
            if category_field == 'architecture':
                df_expanded = df_expanded[~df_expanded[category_field].str.contains('Other', case=False, na=False)]
            
            # Get top K categories
            category_totals = df_expanded[category_field].value_counts()
            top_categories = category_totals.head(top_k_categories).index.tolist()
            df_filtered = df_expanded[df_expanded[category_field].isin(top_categories)]
            
            if len(top_categories) == 0:
                print(f" No valid {category_field} categories found")
                return pd.DataFrame()
            
            # Create multi-panel visualization
            n_categories = len(top_categories)
            n_cols = min(2, n_categories)  # Max 4 columns
            n_rows = (n_categories + n_cols - 1) // n_cols  # Ceiling division
            
            fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
            if n_categories == 1:
                axes = [axes]
            elif n_rows == 1:
                axes = axes if isinstance(axes, list) else [axes]
            else:
                axes = axes.flatten()
            
            # Define colors for highlighting
            highlight_colors = self._get_colors(n_categories, 'primary')
            grey_color = '#CCCCCC'  # Light grey for background points
            grey_alpha = 0.3  # Lower alpha for grey points
            
            # Store growth statistics for table output
            growth_stats = []
            
            # Create each subplot
            for i, category in enumerate(top_categories):
                ax = axes[i]
                
                # Plot all data points in grey first (background context)
                ax.scatter(df_filtered['published_date'], 
                          df_filtered['numeric_value'],
                          c=grey_color, 
                          alpha=grey_alpha,
                          s=40, 
                          edgecolors='white', 
                          linewidth=0.3,
                          label='Other categories')
                
                # Plot the specific category in color (highlighted)
                category_data = df_filtered[df_filtered[category_field] == category]
                if not category_data.empty:
                    ax.scatter(category_data['published_date'], 
                              category_data['numeric_value'],
                              c=highlight_colors[i], 
                              alpha=0.8,
                              s=80, 
                              edgecolors='white', 
                              linewidth=0.5,
                              label=category)
                    
                    # Calculate and plot trend line if log scale is used and show_trend_lines is True
                    if log_scale and show_trend_lines:
                        # Filter positive values and remove outliers (values below threshold)
                        positive_data = category_data[(category_data['numeric_value'] > 0) & (category_data['numeric_value'] >= min_value_threshold)].copy()
                        if len(positive_data) > 1:
                            # Convert dates to numeric for regression
                            positive_data['date_numeric'] = (positive_data['published_date'] - positive_data['published_date'].min()).dt.days
                            
                            # Perform linear regression on log values
                            from scipy import stats
                            log_values = np.log10(positive_data['numeric_value'])
                            slope, intercept, r_value, p_value, std_err = stats.linregress(positive_data['date_numeric'], log_values)
                            
                            # Calculate exponential growth rate (per year)
                            days_per_year = 365.25
                            annual_growth_rate = slope * days_per_year
                            growth_factor = 10 ** annual_growth_rate  # This is the factor by which values multiply each year
                            
                            # Plot trend line
                            x_trend = np.linspace(positive_data['date_numeric'].min(), positive_data['date_numeric'].max(), 100)
                            y_trend = 10 ** (slope * x_trend + intercept)
                            ax.plot(positive_data['published_date'].min() + pd.to_timedelta(x_trend, unit='D'), 
                                   y_trend, 
                                   color=highlight_colors[i], 
                                   linewidth=2, 
                                   linestyle='--', 
                                   alpha=0.8,
                                   label=f'Trend (R²={r_value**2:.3f})')
                            
                            # Store growth statistics
                            growth_stats.append({
                                'category': category,
                                'data_points': len(positive_data),
                                'annual_growth_rate': annual_growth_rate,
                                'growth_factor': growth_factor,
                                'r_squared': r_value**2,
                                'p_value': p_value,
                                'slope': slope,
                                'intercept': intercept
                            })
                        else:
                            # Not enough data for trend analysis
                            growth_stats.append({
                                'category': category,
                                'data_points': len(positive_data),
                                'annual_growth_rate': np.nan,
                                'growth_factor': np.nan,
                                'r_squared': np.nan,
                                'p_value': np.nan,
                                'slope': np.nan,
                                'intercept': np.nan
                            })
                
                # Set log scale if requested
                if log_scale:
                    positive_values = df_filtered[df_filtered['numeric_value'] > 0]['numeric_value']
                    if len(positive_values) > 0:
                        ax.set_yscale('log')
                        ax.set_ylabel(f'{field_name.title()} (log scale)')
                    else:
                        ax.set_ylabel(f'{field_name.title()}')
                else:
                    ax.set_ylabel(f'{field_name.title()}')
                
                # Set labels and title
                ax.set_xlabel('Publication Date')
                ax.set_title(f'{category}', fontsize=self.title_fontsize, fontweight='bold')
                
                # Apply consistent styling
                self._apply_chart_style(ax, 'scatter')
                
                # Rotate x-axis labels
                ax.tick_params(axis='x', rotation=45)
                
                # Add legend for this subplot
                ax.legend(loc='lower right', fontsize=10)
            
            # Hide unused subplots
            for i in range(n_categories, len(axes)):
                axes[i].set_visible(False)
            
            # Add overall title
            fig.suptitle(f'{field_name.title()} Trends by {category_field.title()}', 
                        fontsize=self.title_fontsize, fontweight='bold', y=0.95)
            
            plt.tight_layout()
            plt.subplots_adjust(top=0.9)  # Make room for suptitle
            plt.show()
            
            # Print statistics
            mode_text = "Largest Model per Paper" if largest_model_only else "All Models"
            print(f" {field_name.title()} Trends Spotlight Analysis ({mode_text}):")
            print(f"  • Total data points: {len(df_filtered)}")
            print(f"  • Date range: {df_filtered['published_date'].min()} to {df_filtered['published_date'].max()}")
            print(f"  • {category_field.title()} categories: {len(top_categories)}")
            print(f"  • Categories analyzed: {', '.join(top_categories)}")
            
            # Print category statistics
            print(f"\n{category_field.title()} distribution:")
            for i, category in enumerate(top_categories):
                cat_count = len(df_filtered[df_filtered[category_field] == category])
                cat_avg = df_filtered[df_filtered[category_field] == category]['numeric_value'].mean()
                print(f"  • {category}: {cat_count} points, avg {field_name}: {cat_avg:,.0f}")
            
            # Print growth statistics
            if growth_stats and log_scale and show_trend_lines:
                mode_text = "Largest Models per Paper" if largest_model_only else "All Models"
                print(f"\n Growth Analysis ({mode_text}, values ≥ {min_value_threshold:,}):")
                print(f"{'Category':<20} {'Data Points':<12} {'Growth Factor':<15} {'Annual Rate':<12} {'R²':<8}")
                print("-" * 70)
                for stat in growth_stats:
                    if not pd.isna(stat['growth_factor']):
                        print(f"{stat['category']:<20} {stat['data_points']:<12} {stat['growth_factor']:<15.3f} {stat['annual_growth_rate']:<12.3f} {stat['r_squared']:<8.3f}")
                    else:
                        print(f"{stat['category']:<20} {stat['data_points']:<12} {'N/A':<15} {'N/A':<12} {'N/A':<8}")
            elif not show_trend_lines:
                print(f"\n Trend lines disabled - showing data points only")
            
            # Create growth statistics DataFrame for table output
            growth_df = pd.DataFrame(growth_stats) if growth_stats else pd.DataFrame()
            
            return df_filtered, growth_df
            
        except Exception as e:
            print(f" Error analyzing {field_name} trends spotlight: {e}")
            return pd.DataFrame(), pd.DataFrame()
        finally:
            if conn:
                conn.close()
    
    def get_domain_parameter_comparison(self,
                                      run_id_start: Optional[int] = None,
                                      run_id_end: Optional[int] = None,
                                      top_domains: int = 10,
                                      figsize: Tuple[int, int] = (14, 10)) -> pd.DataFrame:
        """
        Compare parameter sizes across different domains.
        
        Args:
            run_id_start: Starting extraction run ID (inclusive)
            run_id_end: Ending extraction run ID (inclusive)
            top_domains: Number of top domains to compare
            figsize: Figure size for the plot
        
        Returns:
            DataFrame with domain parameter comparisons
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get parameter and domain data
            query = """
            SELECT 
                p.published_date,
                ef_params.value as parameters,
                ef_domain.value as domain,
                COALESCE(m.provider, 'unknown') as model_provider
            FROM papers p
            JOIN extraction_runs er ON p.id = er.paper_id
            JOIN extracted_fields ef_params ON er.id = ef_params.run_id
            JOIN extracted_fields ef_domain ON er.id = ef_domain.run_id
            LEFT JOIN models m ON er.model_id = m.id
            WHERE ef_params.field_name = 'parameters'
            AND ef_domain.field_name = 'domain'
            AND p.published_date IS NOT NULL
            AND ef_params.value NOT IN %s
            AND ef_domain.value NOT IN %s
            """
            
            params = [tuple(self.default_na_values), tuple(self.default_na_values)]
            if run_id_start is not None:
                query += " AND ef_params.run_id >= %s"
                params.append(run_id_start)
            if run_id_end is not None:
                query += " AND ef_params.run_id <= %s"
                params.append(run_id_end)
            
            query += " ORDER BY p.published_date"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if not results:
                print(" No domain parameter data found")
                return pd.DataFrame()
            
            df = pd.DataFrame(results, columns=['published_date', 'parameters', 'domain', 'model_provider'])
            df['published_date'] = pd.to_datetime(df['published_date'])
            
            # Extract numeric values
            df['numeric_value'] = df['parameters'].apply(self.trend_analyzer._extract_numeric)
            df = df[df['numeric_value'].notna()]
            
            if df.empty:
                print(" No numeric parameter values found")
                return pd.DataFrame()
            
            # Get top domains by count
            domain_counts = df['domain'].value_counts()
            top_domain_list = domain_counts.head(top_domains).index.tolist()
            df_top = df[df['domain'].isin(top_domain_list)]
            
            # Create box plot comparison
            fig, ax = plt.subplots(figsize=figsize)
            
            # Create box plot
            df_top.boxplot(column='numeric_value', by='domain', ax=ax)
            ax.set_yscale('log')
            ax.set_xlabel('Domain')
            ax.set_ylabel('Parameter Count (log scale)')
            ax.set_title(f'Parameter Size Distribution by Domain (Top {top_domains})', fontsize=self.title_fontsize, fontweight='bold')
            
            # Rotate x-axis labels
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.show()
            
            # Print statistics
            print(f" Domain Parameter Comparison:")
            print(f"  • Domains analyzed: {len(top_domain_list)}")
            print(f"  • Total models: {len(df_top)}")
            
            domain_stats = df_top.groupby('domain')['numeric_value'].agg([
                'count', 'mean', 'median', 'std', 'min', 'max'
            ]).round(0)
            
            print(f"\nDomain Statistics:")
            print(domain_stats)
            
            return df_top
            
        except Exception as e:
            print(f" Error analyzing domain parameter comparison: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()
    
    def get_modality_analysis(self,
                            run_id_start: Optional[int] = None,
                            run_id_end: Optional[int] = None,
                            modality_type: str = 'input',
                            figsize: Tuple[int, int] = (14, 10)) -> pd.DataFrame:
        """
        Analyze modality trends over time.
        
        Args:
            run_id_start: Starting extraction run ID (inclusive)
            run_id_end: Ending extraction run ID (inclusive)
            modality_type: 'input' or 'output' modality
            figsize: Figure size for the plot
        
        Returns:
            DataFrame with modality trends
        """
        if modality_type not in ['input', 'output']:
            raise ValueError("modality_type must be 'input' or 'output'")
        
        field_name = f'{modality_type}_modality'
        
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get modality data by year
            query = f"""
            SELECT 
                DATE_TRUNC('year', p.published_date) as year,
                ef.value as modality,
                COUNT(DISTINCT p.id) as publication_count
            FROM papers p
            JOIN extraction_runs er ON p.id = er.paper_id
            JOIN extracted_fields ef ON er.id = ef.run_id
            WHERE ef.field_name = '{field_name}'
            AND p.published_date IS NOT NULL
            AND ef.value NOT IN %s
            """
            
            params = [tuple(self.default_na_values)]
            if run_id_start is not None:
                query += " AND ef.run_id >= %s"
                params.append(run_id_start)
            if run_id_end is not None:
                query += " AND ef.run_id <= %s"
                params.append(run_id_end)
            
            query += " GROUP BY year, modality ORDER BY year, publication_count DESC"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if not results:
                print(f" No {modality_type} modality data found")
                return pd.DataFrame()
            
            df = pd.DataFrame(results, columns=['year', 'modality', 'publication_count'])
            df['year'] = pd.to_datetime(df['year'])
            
            # Expand array values in modality field
            df_expanded = self._expand_array_data(df, 'modality')
            
            # Recalculate publication counts after expansion
            df_expanded = df_expanded.groupby(['year', 'modality'])['publication_count'].sum().reset_index()
            
            # Get top modalities
            modality_totals = df_expanded.groupby('modality')['publication_count'].sum().sort_values(ascending=False)
            top_modalities = modality_totals.head(10).index.tolist()
            df_top = df_expanded[df_expanded['modality'].isin(top_modalities)]
            
            # Pivot for stacked chart
            df_pivot = df_top.pivot(index='year', columns='modality', values='publication_count').fillna(0)
            
            # Sort data for better stacked chart visualization (largest at bottom)
            df_pivot = self._sort_stacked_chart_data(df_pivot)
            
            # Create stacked column chart
            fig, ax = plt.subplots(figsize=figsize)
            colors = self._get_colors(len(df_pivot.columns), 'primary')
            df_pivot.plot(kind='bar', stacked=True, ax=ax, color=colors, alpha=0.8)
            
            ax.set_xlabel('Year')
            ax.set_ylabel('Number of Publications')
            ax.set_title(f'{modality_type.title()} Modality Trends Over Time', fontsize=self.title_fontsize, fontweight='bold')
            ax.legend(title='Modality', loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=min(len(df_pivot.columns), 6))
            self._apply_chart_style(ax, 'bar')
            
            # Format year labels to show only year
            self._format_year_labels(ax, rotation=45)
            plt.subplots_adjust(bottom=0.3)  # Extra space for bottom legend with larger fonts
            plt.show()
            
            print(f" {modality_type.title()} Modality Analysis:")
            print(f"  • Total modalities: {df['modality'].nunique()}")
            print(f"  • Date range: {df['year'].min()} to {df['year'].max()}")
            print(f"  • Top modalities by total usage:")
            for i, (modality, count) in enumerate(modality_totals.head(10).items(), 1):
                print(f"    {i:2d}. {modality}: {count} publications")
            
            return df_pivot
            
        except Exception as e:
            print(f" Error analyzing {modality_type} modality trends: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()
    
    def get_architecture_trends(self,
                              run_id_start: Optional[int] = None,
                              run_id_end: Optional[int] = None,
                              top_k: int = 10,
                              visualization_type: str = 'grouped',  # 'grouped' or 'stacked_percentage'
                              figsize: Tuple[int, int] = (14, 10)) -> pd.DataFrame:
        """
        Analyze architecture trends over time.
        
        Args:
            run_id_start: Starting extraction run ID (inclusive)
            run_id_end: Ending extraction run ID (inclusive)
            top_k: Number of top architectures to show
            visualization_type: 'grouped' for grouped bars or 'stacked_percentage' for stacked percentage bars
            figsize: Figure size for the plot
        
        Returns:
            DataFrame with architecture trends
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get architecture data by year
            query = """
            SELECT 
                DATE_TRUNC('year', p.published_date) as year,
                ef.value as architecture,
                COUNT(DISTINCT p.id) as publication_count
            FROM papers p
            JOIN extraction_runs er ON p.id = er.paper_id
            JOIN extracted_fields ef ON er.id = ef.run_id
            WHERE ef.field_name = 'architecture'
            AND p.published_date IS NOT NULL
            AND ef.value NOT IN %s
            """
            
            params = [tuple(self.default_na_values)]
            if run_id_start is not None:
                query += " AND ef.run_id >= %s"
                params.append(run_id_start)
            if run_id_end is not None:
                query += " AND ef.run_id <= %s"
                params.append(run_id_end)
            
            query += " GROUP BY year, architecture ORDER BY year, publication_count DESC"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if not results:
                print(" No architecture data found")
                return pd.DataFrame()
            
            df = pd.DataFrame(results, columns=['year', 'architecture', 'publication_count'])
            df['year'] = pd.to_datetime(df['year'])
            
            # Expand array values in architecture field, excluding "Other" values
            excluded_architectures = ["Other - {High-Level Architecture Name}"]
            df_expanded = self._expand_array_data(df, 'architecture', excluded_architectures)
            
            # Additional filtering to ensure "Other" values are completely removed
            df_expanded = df_expanded[~df_expanded['architecture'].str.contains('Other', case=False, na=False)]
            
            # Recalculate publication counts after expansion
            df_expanded = df_expanded.groupby(['year', 'architecture'])['publication_count'].sum().reset_index()
            
            # Get top architectures
            arch_totals = df_expanded.groupby('architecture')['publication_count'].sum().sort_values(ascending=False)
            top_architectures = arch_totals.head(top_k).index.tolist()
            df_top = df_expanded[df_expanded['architecture'].isin(top_architectures)]
            
            # Create visualization based on type
            if visualization_type == 'stacked_percentage':
                # Create stacked percentage chart
                self._create_stacked_percentage_chart(
                    df_top, 'architecture', 'publication_count', 
                    f'Top {top_k} Architectures Over Time (Percentage)', figsize, top_k, 'primary'
                )
            else:  # default 'grouped'
                # Create grouped bar chart
                fig, ax = plt.subplots(figsize=figsize)
                df_pivot = df_top.pivot(index='year', columns='architecture', values='publication_count').fillna(0)
                colors = self._get_colors(len(df_pivot.columns), 'primary')
                df_pivot.plot(kind='bar', ax=ax, color=colors, alpha=0.8)
                
                ax.set_xlabel('Year')
                ax.set_ylabel('Number of Models')
                ax.set_title(f'Top {top_k} Architectures Over Time', fontsize=self.title_fontsize, fontweight='bold')
                ax.legend(title='Architecture', loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=min(len(df_pivot.columns), 6))
                self._apply_chart_style(ax, 'bar')
                
                # Format year labels to show only year
                self._format_year_labels(ax, rotation=45)
                plt.subplots_adjust(bottom=0.3)  # Extra space for bottom legend with larger fonts
                plt.show()
            
            print(f" Architecture Trends Analysis:")
            print(f"  • Total architectures: {df['architecture'].nunique()}")
            print(f"  • Date range: {df['year'].min()} to {df['year'].max()}")
            print(f"  • Top architectures by total usage:")
            for i, (arch, count) in enumerate(arch_totals.head(top_k).items(), 1):
                print(f"    {i:2d}. {arch}: {count} models")
            
            return df_pivot
            
        except Exception as e:
            print(f" Error analyzing architecture trends: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()
    
    def get_robot_type_analysis(self, run_id_start: int = 7866, 
                               run_id_end: int = 8087,
                               top_k: int = 20,
                               include_temporal: bool = True,
                               visualization_type: str = 'histogram',  # 'histogram' or 'stacked_percentage'
                               figsize: Tuple[int, int] = (15, 8)) -> pd.DataFrame:
        """
        Analyze robot types in robotics models.
        
        Args:
            run_id_start: Starting extraction run ID (default: 7866 for robotics data)
            run_id_end: Ending extraction run ID (default: 8087 for robotics data)
            top_k: Number of top robot types to show (default: 20)
            include_temporal: Whether to include temporal analysis
            visualization_type: 'histogram' for simple histogram or 'stacked_percentage' for temporal stacked percentage
            figsize: Figure size for the plot
        
        Returns:
            DataFrame with robot type analysis
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get robot type data - count each robot type only once per paper
            query = """
            SELECT ef.value as robot_type, COUNT(DISTINCT p.id) as count
            FROM papers p
            JOIN extraction_runs er ON p.id = er.paper_id
            JOIN extracted_fields ef ON er.id = ef.run_id
            WHERE er.id BETWEEN %s AND %s 
            AND ef.field_name = 'robot_type'
            AND ef.value IS NOT NULL 
            AND ef.value NOT IN ('n/a', 'unknown', '')
            GROUP BY ef.value
            ORDER BY count DESC
            """
            
            cursor.execute(query, (run_id_start, run_id_end))
            results = cursor.fetchall()
            
            if not results:
                print(" No robot type data found")
                return pd.DataFrame()
            
            df = pd.DataFrame(results, columns=['robot_type', 'count'])
            
            # Expand array values in robot_type field
            df_expanded = self._expand_array_data(df, 'robot_type')
            df_expanded = df_expanded.groupby('robot_type')['count'].sum().reset_index()
            
            # Sort by count (descending) and take top K
            df_expanded = df_expanded.sort_values('count', ascending=False).head(top_k)
            
            # Create visualization based on type
            if visualization_type == 'stacked_percentage' and include_temporal:
                # Skip the histogram and go directly to temporal analysis
                pass
            else:
                # Create histogram
                self._create_histogram_chart(
                    df_expanded, 'robot_type', 'count', 
                    f'Top {top_k} Robot Types in Robotics Papers', figsize, top_k, 'primary', False
                )
            
            # Temporal analysis if requested
            if include_temporal:
                temporal_query = """
                SELECT ef.value as robot_type, 
                       EXTRACT(YEAR FROM p.published_date) as year,
                       COUNT(DISTINCT p.id) as count
                FROM papers p
                JOIN extraction_runs er ON p.id = er.paper_id
                JOIN extracted_fields ef ON er.id = ef.run_id
                WHERE er.id BETWEEN %s AND %s 
                AND ef.field_name = 'robot_type'
                AND ef.value IS NOT NULL 
                AND ef.value NOT IN ('n/a', 'unknown', '')
                AND p.published_date IS NOT NULL
                GROUP BY ef.value, EXTRACT(YEAR FROM p.published_date)
                ORDER BY year, count DESC
                """
                
                cursor.execute(temporal_query, (run_id_start, run_id_end))
                temporal_results = cursor.fetchall()
                
                if temporal_results:
                    df_temporal = pd.DataFrame(temporal_results, columns=['robot_type', 'year', 'count'])
                    
                    # Expand array values in temporal data
                    df_temporal_expanded = self._expand_array_data(df_temporal, 'robot_type')
                    df_temporal_expanded = df_temporal_expanded.groupby(['robot_type', 'year'])['count'].sum().reset_index()
                    
                    # Filter temporal data to only include top K robot types from main analysis
                    top_robot_types = df_expanded['robot_type'].tolist()
                    df_temporal_filtered = df_temporal_expanded[df_temporal_expanded['robot_type'].isin(top_robot_types)]
                    
                    # Create temporal plot based on visualization type
                    if visualization_type == 'stacked_percentage':
                        # Create stacked percentage chart
                        self._create_stacked_percentage_chart(
                            df_temporal_filtered, 'robot_type', 'count', 
                            f'Top {top_k} Robot Types Over Time (Percentage)', figsize, top_k, 'primary'
                        )
                    else:  # default 'histogram' - show counts
                        fig, ax = plt.subplots(figsize=figsize)
                        
                        # Get unique robot types and years from filtered data
                        robot_types = df_temporal_filtered['robot_type'].unique()
                        years = sorted(df_temporal_filtered['year'].unique())
                        
                        # Create stacked bar chart with sorted data (largest at bottom)
                        # First, calculate totals for each robot type to determine order
                        robot_type_totals = df_temporal_filtered.groupby('robot_type')['count'].sum().sort_values(ascending=False)
                        sorted_robot_types = robot_type_totals.index.tolist()
                        
                        bottom = np.zeros(len(years))
                        colors = self._get_colors(len(sorted_robot_types), 'primary')
                        
                        for i, robot_type in enumerate(sorted_robot_types):
                            type_data = df_temporal_filtered[df_temporal_filtered['robot_type'] == robot_type]
                            year_counts = [type_data[type_data['year'] == year]['count'].sum() for year in years]
                            ax.bar(years, year_counts, bottom=bottom, label=robot_type, color=colors[i], alpha=0.8, edgecolor='white', linewidth=0.5)
                            bottom += year_counts
                        
                        ax.set_title(f'Top {top_k} Robot Types Over Time', fontsize=self.title_fontsize, fontweight='bold')
                        ax.set_xlabel('Year', fontsize=20)
                        ax.set_ylabel('Number of Papers', fontsize=20)
                        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=min(len(sorted_robot_types), 6))
                        self._apply_chart_style(ax, 'bar')
                        
                        # Format year labels to show only year
                        self._format_year_labels(ax, rotation=45)
                        plt.subplots_adjust(bottom=0.3)  # Extra space for bottom legend with larger fonts
                        plt.show()
            
            return df_expanded
            
        except Exception as e:
            print(f" Error in robot type analysis: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()
    
    def get_robotics_modality_analysis(self, run_id_start: int = 7866, 
                                      run_id_end: int = 8087,
                                      top_k: int = 10,
                                      figsize: Tuple[int, int] = (15, 10)) -> pd.DataFrame:
        """
        Analyze modalities (including sensor modalities) in robotics models over time.
        
        Args:
            run_id_start: Starting extraction run ID (default: 7866 for robotics data)
            run_id_end: Ending extraction run ID (default: 8087 for robotics data)
            top_k: Number of top modalities to show per year
            figsize: Figure size for the plot
        
        Returns:
            DataFrame with robotics modality analysis
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get input modalities over time
            input_query = """
            SELECT ef.value as input_modality,
                   EXTRACT(YEAR FROM p.published_date) as year,
                   COUNT(*) as count
            FROM papers p
            JOIN extraction_runs er ON p.id = er.paper_id
            JOIN extracted_fields ef ON er.id = ef.run_id
            WHERE er.id BETWEEN %s AND %s 
            AND ef.field_name = 'input_modality'
            AND ef.value IS NOT NULL 
            AND ef.value NOT IN ('n/a', 'unknown', '')
            AND p.published_date IS NOT NULL
            GROUP BY ef.value, EXTRACT(YEAR FROM p.published_date)
            ORDER BY year, count DESC
            """
            
            cursor.execute(input_query, (run_id_start, run_id_end))
            input_results = cursor.fetchall()
            
            # Get sensor modalities over time
            sensor_query = """
            SELECT ef.value as sensor_modalities,
                   EXTRACT(YEAR FROM p.published_date) as year,
                   COUNT(*) as count
            FROM papers p
            JOIN extraction_runs er ON p.id = er.paper_id
            JOIN extracted_fields ef ON er.id = ef.run_id
            WHERE er.id BETWEEN %s AND %s 
            AND ef.field_name = 'sensor_modalities'
            AND ef.value IS NOT NULL 
            AND ef.value NOT IN ('n/a', 'unknown', '')
            AND p.published_date IS NOT NULL
            GROUP BY ef.value, EXTRACT(YEAR FROM p.published_date)
            ORDER BY year, count DESC
            """
            
            cursor.execute(sensor_query, (run_id_start, run_id_end))
            sensor_results = cursor.fetchall()
            
            if not input_results and not sensor_results:
                print(" No robotics modality data found")
                return pd.DataFrame()
            
            # Process input modalities
            if input_results:
                df_input = pd.DataFrame(input_results, columns=['modality', 'year', 'count'])
                df_input['modality_type'] = 'input'
                
                # Expand array values
                df_input_expanded = self._expand_array_data(df_input, 'modality')
                df_input_expanded = df_input_expanded.groupby(['modality', 'year'])['count'].sum().reset_index()
                df_input_expanded['modality_type'] = 'input'
            
            # Process sensor modalities
            if sensor_results:
                df_sensor = pd.DataFrame(sensor_results, columns=['modality', 'year', 'count'])
                df_sensor['modality_type'] = 'sensor'
                
                # Expand array values
                df_sensor_expanded = self._expand_array_data(df_sensor, 'modality')
                df_sensor_expanded = df_sensor_expanded.groupby(['modality', 'year'])['count'].sum().reset_index()
                df_sensor_expanded['modality_type'] = 'sensor'
            
            # Combine data
            if input_results and sensor_results:
                df_combined = pd.concat([df_input_expanded, df_sensor_expanded], ignore_index=True)
            elif input_results:
                df_combined = df_input_expanded
            else:
                df_combined = df_sensor_expanded
            
            # Create visualization
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize)
            
            # Plot 1: Input modalities over time
            if input_results:
                input_data = df_combined[df_combined['modality_type'] == 'input']
                if not input_data.empty:
                    years = sorted(input_data['year'].unique())
                    modalities = input_data.groupby('modality')['count'].sum().nlargest(top_k).index.tolist()
                    
                    colors = self._get_colors(len(modalities), 'primary')
                    for i, modality in enumerate(modalities):
                        modality_data = input_data[input_data['modality'] == modality]
                        year_counts = [modality_data[modality_data['year'] == year]['count'].sum() for year in years]
                        ax1.plot(years, year_counts, marker='o', label=modality, linewidth=2, color=colors[i], markersize=6)
                    
                    ax1.set_title('Input Modalities in Robotics Models Over Time', fontsize=self.title_fontsize, fontweight='bold')
                    ax1.set_xlabel('Year', fontsize=20)
                    ax1.set_ylabel('Number of Models', fontsize=20)
                    ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=min(len(df_pivot.columns), 6))
                    self._apply_chart_style(ax1, 'line')
                    # Format year labels to show only year
                    self._format_year_labels(ax1, rotation=45)
            
            # Plot 2: Sensor modalities over time
            if sensor_results:
                sensor_data = df_combined[df_combined['modality_type'] == 'sensor']
                if not sensor_data.empty:
                    years = sorted(sensor_data['year'].unique())
                    modalities = sensor_data.groupby('modality')['count'].sum().nlargest(top_k).index.tolist()
                    
                    colors = self._get_colors(len(modalities), 'secondary')
                    for i, modality in enumerate(modalities):
                        modality_data = sensor_data[sensor_data['modality'] == modality]
                        year_counts = [modality_data[modality_data['year'] == year]['count'].sum() for year in years]
                        ax2.plot(years, year_counts, marker='s', label=modality, linewidth=2, color=colors[i], markersize=6)
                    
                    ax2.set_title('Sensor Modalities in Robotics Models Over Time', fontsize=self.title_fontsize, fontweight='bold')
                    ax2.set_xlabel('Year', fontsize=20)
                    ax2.set_ylabel('Number of Models', fontsize=20)
                    ax2.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=min(len(df_pivot.columns), 6))
                    self._apply_chart_style(ax2, 'line')
                    # Format year labels to show only year
                    self._format_year_labels(ax2, rotation=45)
            
            plt.subplots_adjust(bottom=0.3)  # Extra space for bottom legend with larger fontss
            plt.show()
            
            return df_combined
            
        except Exception as e:
            print(f" Error in robotics modality analysis: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()
    
    def get_modality_development_analysis(self, run_id_start: int = 7866, 
                                         run_id_end: int = 8087,
                                         figsize: Tuple[int, int] = (12, 8)) -> pd.DataFrame:
        """
        Analyze the development of number of modalities per model over time.
        
        Args:
            run_id_start: Starting extraction run ID (default: 7866 for robotics data)
            run_id_end: Ending extraction run ID (default: 8087 for robotics data)
            figsize: Figure size for the plot
        
        Returns:
            DataFrame with modality development analysis
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get data for each model with modality counts
            query = """
            SELECT er.id as run_id,
                   EXTRACT(YEAR FROM p.published_date) as year,
                   ef_input.value as input_modality,
                   ef_sensor.value as sensor_modalities,
                   COUNT(*) as model_count
            FROM papers p
            JOIN extraction_runs er ON p.id = er.paper_id
            LEFT JOIN extracted_fields ef_input ON er.id = ef_input.run_id AND ef_input.field_name = 'input_modality'
            LEFT JOIN extracted_fields ef_sensor ON er.id = ef_sensor.run_id AND ef_sensor.field_name = 'sensor_modalities'
            WHERE er.id BETWEEN %s AND %s 
            AND p.published_date IS NOT NULL
            GROUP BY er.id, EXTRACT(YEAR FROM p.published_date), ef_input.value, ef_sensor.value
            ORDER BY year, er.id
            """
            
            cursor.execute(query, (run_id_start, run_id_end))
            results = cursor.fetchall()
            
            if not results:
                print(" No modality development data found")
                return pd.DataFrame()
            
            df = pd.DataFrame(results, columns=['run_id', 'year', 'input_modality', 'sensor_modalities', 'model_count'])
            
            # Calculate modality counts for each model
            modality_counts = []
            
            for _, row in df.iterrows():
                input_count = 0
                sensor_count = 0
                
                # Count input modalities
                if row['input_modality'] and row['input_modality'] not in ['n/a', 'unknown', '']:
                    input_modalities = self._parse_array_values(row['input_modality'])
                    input_count = len(input_modalities)
                
                # Count sensor modalities
                if row['sensor_modalities'] and row['sensor_modalities'] not in ['n/a', 'unknown', '']:
                    sensor_modalities = self._parse_array_values(row['sensor_modalities'])
                    sensor_count = len(sensor_modalities)
                
                total_modalities = input_count + sensor_count
                modality_counts.append({
                    'run_id': row['run_id'],
                    'year': row['year'],
                    'input_modality_count': input_count,
                    'sensor_modality_count': sensor_count,
                    'total_modality_count': total_modalities,
                    'model_count': row['model_count']
                })
            
            df_modality = pd.DataFrame(modality_counts)
            
            # Create visualization
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
            
            # Plot 1: Average modalities per model over time
            yearly_avg = df_modality.groupby('year').agg({
                'total_modality_count': 'mean',
                'input_modality_count': 'mean',
                'sensor_modality_count': 'mean'
            }).reset_index()
            
            colors = self._get_colors(3, 'primary')
            ax1.plot(yearly_avg['year'], yearly_avg['total_modality_count'], 
                    marker='o', linewidth=2, label='Total Modalities', color=colors[0], markersize=6)
            ax1.plot(yearly_avg['year'], yearly_avg['input_modality_count'], 
                    marker='s', linewidth=2, label='Input Modalities', color=colors[1], markersize=6)
            ax1.plot(yearly_avg['year'], yearly_avg['sensor_modality_count'], 
                    marker='^', linewidth=2, label='Sensor Modalities', color=colors[2], markersize=6)
            
            ax1.set_title('Average Modalities per Model Over Time', fontsize=self.title_fontsize, fontweight='bold')
            ax1.set_xlabel('Year', fontsize=20)
            ax1.set_ylabel('Average Number of Modalities', fontsize=20)
            ax1.legend()
            self._apply_chart_style(ax1, 'line')
            # Format year labels to show only year
            self._format_year_labels(ax1, rotation=45)
            
            # Plot 2: Distribution of modality counts
            modality_dist = df_modality['total_modality_count'].value_counts().sort_index()
            colors = self._get_colors(1, 'primary')
            ax2.bar(modality_dist.index, modality_dist.values, color=colors[0], edgecolor='white', linewidth=0.5, alpha=0.8)
            #ax2.set_title('Distribution of Modality Counts per Model', fontsize=self.title_fontsize, fontweight='bold')
            ax2.set_xlabel('Number of Modalities', fontsize=20)
            ax2.set_ylabel('Number of Models', fontsize=20)
            self._apply_chart_style(ax2, 'bar')
            
            plt.tight_layout()
            plt.show()
            
            return df_modality
            
        except Exception as e:
            print(f" Error in modality development analysis: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()
    
    def compare_modality_development_ranges(self, 
                                          range1_start: int, range1_end: int,
                                          range2_start: int, range2_end: int,
                                          range1_label: str = "Range 1",
                                          range2_label: str = "Range 2",
                                          normalize_by_count: bool = True,
                                          figsize: Tuple[int, int] = (16, 12)) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Compare modality development between two different run ID ranges.
        
        Args:
            range1_start: Starting run ID for first range
            range1_end: Ending run ID for first range
            range2_start: Starting run ID for second range
            range2_end: Ending run ID for second range
            range1_label: Label for first range (e.g., "Early Period", "Robotics Only")
            range2_label: Label for second range (e.g., "Later Period", "All Domains")
            normalize_by_count: If True, normalize distributions by total count; if False, show raw counts
            figsize: Figure size for the plot
        
        Returns:
            Tuple of (DataFrame for range 1, DataFrame for range 2)
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Function to get modality data for a range
            def get_modality_data_for_range(start_id, end_id, label):
                query = """
                SELECT er.id as run_id,
                       EXTRACT(YEAR FROM p.published_date) as year,
                       ef_input.value as input_modality,
                       ef_sensor.value as sensor_modalities,
                       COUNT(*) as model_count
                FROM papers p
                JOIN extraction_runs er ON p.id = er.paper_id
                LEFT JOIN extracted_fields ef_input ON er.id = ef_input.run_id AND ef_input.field_name = 'input_modality'
                LEFT JOIN extracted_fields ef_sensor ON er.id = ef_sensor.run_id AND ef_sensor.field_name = 'sensor_modalities'
                WHERE er.id BETWEEN %s AND %s 
                AND p.published_date IS NOT NULL
                GROUP BY er.id, EXTRACT(YEAR FROM p.published_date), ef_input.value, ef_sensor.value
                ORDER BY year, er.id
                """
                
                cursor.execute(query, (start_id, end_id))
                results = cursor.fetchall()
                
                if not results:
                    print(f" No modality development data found for {label}")
                    return pd.DataFrame()
                
                df = pd.DataFrame(results, columns=['run_id', 'year', 'input_modality', 'sensor_modalities', 'model_count'])
                
                # Calculate modality counts for each model
                modality_counts = []
                
                for _, row in df.iterrows():
                    input_count = 0
                    sensor_count = 0
                    
                    
                    
                    # Count input modalities
                    if row['input_modality'] and row['input_modality'] not in ['n/a', 'unknown', '']:
                        if label != "Robotics":
                            input_modalities = self._parse_array_values(row['input_modality'])
                            input_count = len(input_modalities)
                        else:
                            #do not count "multimodal", "vision", "image", "video", "depth"
                            input_modalities = self._parse_array_values(row['input_modality'])
                            input_count = len(input_modalities)
                            input_count = input_count - 1 if "multimodal" in input_modalities else input_count
                            input_count = input_count - 1 if "vision" in input_modalities else input_count
                            input_count = input_count - 1 if "image" in input_modalities else input_count
                            input_count = input_count - 1 if "video" in input_modalities else input_count
                            input_count = input_count - 1 if "depth" in input_modalities else input_count
                    
                    # Count sensor modalities
                    if row['sensor_modalities'] and row['sensor_modalities'] not in ['n/a', 'unknown', '']:
                        sensor_modalities = self._parse_array_values(row['sensor_modalities'])
                        sensor_count = len(sensor_modalities)
                    
                    total_modalities = input_count + sensor_count
                    modality_counts.append({
                        'run_id': row['run_id'],
                        'year': row['year'],
                        'input_modality_count': input_count,
                        'sensor_modality_count': sensor_count,
                        'total_modality_count': total_modalities,
                        'model_count': row['model_count'],
                        'range_label': label
                    })
                
                return pd.DataFrame(modality_counts)
            
            # Get data for both ranges
            df_range1 = get_modality_data_for_range(range1_start, range1_end, range1_label)
            df_range2 = get_modality_data_for_range(range2_start, range2_end, range2_label)
            
            if df_range1.empty or df_range2.empty:
                print(" Cannot compare ranges - one or both ranges have no data")
                return df_range1, df_range2
            
            # Create visualization - only distribution comparison
            fig, ax = plt.subplots(1, 1, figsize=figsize)
            
            # Distribution comparison (histogram)
            modality_dist1 = df_range1['total_modality_count'].value_counts().sort_index()
            modality_dist2 = df_range2['total_modality_count'].value_counts().sort_index()
            
            # Get all unique modality counts for consistent x-axis
            all_modality_counts = sorted(set(modality_dist1.index) | set(modality_dist2.index))
            
            # Prepare data for plotting
            counts1 = [modality_dist1.get(count, 0) for count in all_modality_counts]
            counts2 = [modality_dist2.get(count, 0) for count in all_modality_counts]
            
            # Normalize if requested
            if normalize_by_count:
                total1 = sum(counts1)
                total2 = sum(counts2)
                counts1 = [count/total1*100 if total1 > 0 else 0 for count in counts1]
                counts2 = [count/total2*100 if total2 > 0 else 0 for count in counts2]
                ylabel = 'Percentage of Models (%)'
            else:
                ylabel = 'Number of Models'
            
            # Plot distributions side by side
            x_pos = np.arange(len(all_modality_counts))
            width = 0.35
            
            ax.bar(x_pos - width/2, counts1, width, label=range1_label, 
                   color=self.primary_colors[0], alpha=0.8, edgecolor='white', linewidth=0.5)
            ax.bar(x_pos + width/2, counts2, width, label=range2_label, 
                   color=self.primary_colors[1], alpha=0.8, edgecolor='white', linewidth=0.5)
            
            ax.set_xlabel('Number of Modalities', fontsize=20)
            ax.set_ylabel(ylabel, fontsize=20)
            #ax.set_title('Distribution of Modality Counts per Model', fontsize=self.title_fontsize, fontweight='bold')
            ax.set_xticks(x_pos)
            ax.set_xticklabels(all_modality_counts, fontsize=20)
            ax.legend(fontsize=20)
            self._apply_chart_style(ax, 'bar')
            
            plt.tight_layout()
            plt.show()
            
            # Print comparison statistics
            print(f" Modality Development Comparison:")
            print(f"  • {range1_label} (Run IDs {range1_start}-{range1_end}):")
            print(f"    - Total models: {len(df_range1)}")
            print(f"    - Average total modalities: {df_range1['total_modality_count'].mean():.2f}")
            print(f"    - Average input modalities: {df_range1['input_modality_count'].mean():.2f}")
            print(f"    - Average sensor modalities: {df_range1['sensor_modality_count'].mean():.2f}")
            print(f"    - Date range: {df_range1['year'].min()}-{df_range1['year'].max()}")
            
            print(f"  • {range2_label} (Run IDs {range2_start}-{range2_end}):")
            print(f"    - Total models: {len(df_range2)}")
            print(f"    - Average total modalities: {df_range2['total_modality_count'].mean():.2f}")
            print(f"    - Average input modalities: {df_range2['input_modality_count'].mean():.2f}")
            print(f"    - Average sensor modalities: {df_range2['sensor_modality_count'].mean():.2f}")
            print(f"    - Date range: {df_range2['year'].min()}-{df_range2['year'].max()}")
            
            # Calculate differences
            total_diff = df_range2['total_modality_count'].mean() - df_range1['total_modality_count'].mean()
            input_diff = df_range2['input_modality_count'].mean() - df_range1['input_modality_count'].mean()
            sensor_diff = df_range2['sensor_modality_count'].mean() - df_range1['sensor_modality_count'].mean()
            
            print(f"\n Differences ({range2_label} - {range1_label}):")
            print(f"  • Total modalities: {total_diff:+.2f}")
            print(f"  • Input modalities: {input_diff:+.2f}")
            print(f"  • Sensor modalities: {sensor_diff:+.2f}")
            
            return df_range1, df_range2
            
        except Exception as e:
            print(f" Error comparing modality development ranges: {e}")
            return pd.DataFrame(), pd.DataFrame()
        finally:
            if conn:
                conn.close()
    
    def get_control_type_analysis(self, run_id_start: int = 7866, 
                                 run_id_end: int = 8087,
                                 visualization_type: str = 'pie',  # 'pie' or 'stacked_percentage'
                                 figsize: Tuple[int, int] = (10, 8)) -> pd.DataFrame:
        """
        Analyze control types in robotics models.
        
        Args:
            run_id_start: Starting extraction run ID (default: 7866 for robotics data)
            run_id_end: Ending extraction run ID (default: 8087 for robotics data)
            visualization_type: 'pie' for pie chart or 'stacked_percentage' for temporal stacked percentage
            figsize: Figure size for the plot
        
        Returns:
            DataFrame with control type analysis
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get control type data
            query = """
            SELECT ef.value as control_type, COUNT(*) as count
            FROM papers p
            JOIN extraction_runs er ON p.id = er.paper_id
            JOIN extracted_fields ef ON er.id = ef.run_id
            WHERE er.id BETWEEN %s AND %s 
            AND ef.field_name = 'control_type'
            AND ef.value IS NOT NULL 
            AND ef.value NOT IN ('n/a', 'unknown', '')
            GROUP BY ef.value
            ORDER BY count DESC
            """
            
            cursor.execute(query, (run_id_start, run_id_end))
            results = cursor.fetchall()
            
            if not results:
                print(" No control type data found")
                return pd.DataFrame()
            
            df = pd.DataFrame(results, columns=['control_type', 'count'])
            
            # Expand array values in control_type field
            df_expanded = self._expand_array_data(df, 'control_type')
            df_expanded = df_expanded.groupby('control_type')['count'].sum().reset_index()
            
            # Create visualization based on type
            if visualization_type == 'stacked_percentage':
                # For stacked percentage, we need temporal data
                temporal_query = """
                SELECT ef.value as control_type, 
                       EXTRACT(YEAR FROM p.published_date) as year,
                       COUNT(*) as count
                FROM papers p
                JOIN extraction_runs er ON p.id = er.paper_id
                JOIN extracted_fields ef ON er.id = ef.run_id
                WHERE er.id BETWEEN %s AND %s 
                AND ef.field_name = 'control_type'
                AND ef.value IS NOT NULL 
                AND ef.value NOT IN ('n/a', 'unknown', '')
                AND p.published_date IS NOT NULL
                GROUP BY ef.value, EXTRACT(YEAR FROM p.published_date)
                ORDER BY year, count DESC
                """
                
                cursor.execute(temporal_query, (run_id_start, run_id_end))
                temporal_results = cursor.fetchall()
                
                if temporal_results:
                    df_temporal = pd.DataFrame(temporal_results, columns=['control_type', 'year', 'count'])
                    
                    # Expand array values in temporal data
                    df_temporal_expanded = self._expand_array_data(df_temporal, 'control_type')
                    df_temporal_expanded = df_temporal_expanded.groupby(['control_type', 'year'])['count'].sum().reset_index()
                    
                    # Create stacked percentage chart
                    self._create_stacked_percentage_chart(
                        df_temporal_expanded, 'control_type', 'count', 
                        'Control Types Over Time (Percentage)', figsize, 10, 'primary'
                    )
                else:
                    print(" No temporal control type data found for stacked percentage visualization")
                    # Fall back to pie chart
                    self._create_pie_chart(df_expanded, 'control_type', 'count', 
                                         'Control Types in Robotics Models', figsize, 'primary')
            else:  # default 'pie'
                # Create pie chart
                self._create_pie_chart(df_expanded, 'control_type', 'count', 
                                     'Control Types in Robotics Models', figsize, 'primary')
            
            return df_expanded
            
        except Exception as e:
            print(f" Error in control type analysis: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()
    
    def get_environment_type_analysis(self, run_id_start: int = 7866, 
                                     run_id_end: int = 8087,
                                     visualization_type: str = 'pie',  # 'pie' or 'stacked_percentage'
                                     figsize: Tuple[int, int] = (10, 8)) -> pd.DataFrame:
        """
        Analyze environment types in robotics models.
        
        Args:
            run_id_start: Starting extraction run ID (default: 7866 for robotics data)
            run_id_end: Ending extraction run ID (default: 8087 for robotics data)
            visualization_type: 'pie' for pie chart or 'stacked_percentage' for temporal stacked percentage
            figsize: Figure size for the plot
        
        Returns:
            DataFrame with environment type analysis
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get environment type data
            query = """
            SELECT ef.value as environment_types, COUNT(*) as count
            FROM papers p
            JOIN extraction_runs er ON p.id = er.paper_id
            JOIN extracted_fields ef ON er.id = ef.run_id
            WHERE er.id BETWEEN %s AND %s 
            AND ef.field_name = 'environment_types'
            AND ef.value IS NOT NULL 
            AND ef.value NOT IN ('n/a', 'unknown', '')
            GROUP BY ef.value
            ORDER BY count DESC
            """
            
            cursor.execute(query, (run_id_start, run_id_end))
            results = cursor.fetchall()
            
            if not results:
                print(" No environment type data found")
                return pd.DataFrame()
            
            df = pd.DataFrame(results, columns=['environment_types', 'count'])
            
            # Expand array values
            df_expanded = self._expand_array_data(df, 'environment_types')
            df_expanded = df_expanded.groupby('environment_types')['count'].sum().reset_index()
            df_expanded = df_expanded.sort_values('count', ascending=False)
            
            # Create visualization based on type
            if visualization_type == 'stacked_percentage':
                # For stacked percentage, we need temporal data
                temporal_query = """
                SELECT ef.value as environment_types, 
                       EXTRACT(YEAR FROM p.published_date) as year,
                       COUNT(*) as count
                FROM papers p
                JOIN extraction_runs er ON p.id = er.paper_id
                JOIN extracted_fields ef ON er.id = ef.run_id
                WHERE er.id BETWEEN %s AND %s 
                AND ef.field_name = 'environment_types'
                AND ef.value IS NOT NULL 
                AND ef.value NOT IN ('n/a', 'unknown', '')
                AND p.published_date IS NOT NULL
                GROUP BY ef.value, EXTRACT(YEAR FROM p.published_date)
                ORDER BY year, count DESC
                """
                
                cursor.execute(temporal_query, (run_id_start, run_id_end))
                temporal_results = cursor.fetchall()
                
                if temporal_results:
                    df_temporal = pd.DataFrame(temporal_results, columns=['environment_types', 'year', 'count'])
                    
                    # Expand array values in temporal data
                    df_temporal_expanded = self._expand_array_data(df_temporal, 'environment_types')
                    df_temporal_expanded = df_temporal_expanded.groupby(['environment_types', 'year'])['count'].sum().reset_index()
                    
                    # Create stacked percentage chart
                    self._create_stacked_percentage_chart(
                        df_temporal_expanded, 'environment_types', 'count', 
                        'Environment Types Over Time (Percentage)', figsize, 10, 'secondary'
                    )
                else:
                    print(" No temporal environment type data found for stacked percentage visualization")
                    # Fall back to pie chart
                    self._create_pie_chart(df_expanded, 'environment_types', 'count', 
                                         'Environment Types in Robotics Models', figsize, 'secondary')
            else:  # default 'pie'
                # Create pie chart
                self._create_pie_chart(df_expanded, 'environment_types', 'count', 
                                     'Environment Types in Robotics Models', figsize, 'secondary')
            
            return df_expanded
            
        except Exception as e:
            print(f" Error in environment type analysis: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()
    
    def get_control_type_spotlight(self,
                                 run_id_start: int = 7866,
                                 run_id_end: int = 8087,
                                 top_k_control_types: int = 6,
                                 figsize: Tuple[int, int] = (18, 12)) -> pd.DataFrame:
        """
        Create a multi-panel visualization where each subplot shows a pie chart for one specific control type,
        displaying the proportion of models that have vs. don't have that control type.
        
        Args:
            run_id_start: Starting extraction run ID (default: 7866 for robotics data)
            run_id_end: Ending extraction run ID (default: 8087 for robotics data)
            top_k_control_types: Number of top control types to analyze (will create this many subplots)
            figsize: Figure size for the entire multi-panel plot
        
        Returns:
            DataFrame with control type presence analysis
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # First, get all models in the specified range to establish the total population
            total_models_query = """
            SELECT DISTINCT er.id as run_id
            FROM papers p
            JOIN extraction_runs er ON p.id = er.paper_id
            WHERE er.id BETWEEN %s AND %s
            """
            
            cursor.execute(total_models_query, (run_id_start, run_id_end))
            total_models = cursor.fetchall()
            total_model_count = len(total_models)
            
            if total_model_count == 0:
                print(" No models found in the specified range")
                return pd.DataFrame()
            
            # Get all control type data
            query = """
            SELECT er.id as run_id, ef.value as control_type
            FROM papers p
            JOIN extraction_runs er ON p.id = er.paper_id
            JOIN extracted_fields ef ON er.id = ef.run_id
            WHERE er.id BETWEEN %s AND %s 
            AND ef.field_name = 'control_type'
            AND ef.value IS NOT NULL 
            AND ef.value NOT IN ('n/a', 'unknown', '')
            """
            
            cursor.execute(query, (run_id_start, run_id_end))
            results = cursor.fetchall()
            
            if not results:
                print(" No control type data found")
                return pd.DataFrame()
            
            df = pd.DataFrame(results, columns=['run_id', 'control_type'])
            
            # Expand array values in control_type field
            df_expanded = self._expand_array_data(df, 'control_type')
            
            # Get top K control types by frequency
            control_type_counts = df_expanded['control_type'].value_counts()
            top_control_types = control_type_counts.head(top_k_control_types).index.tolist()
            
            if len(top_control_types) == 0:
                print(" No valid control types found")
                return pd.DataFrame()
            
            # Create multi-panel visualization - single row layout
            n_control_types = len(top_control_types)
            n_cols = n_control_types  # All charts in one row
            n_rows = 1  # Force single row
            
            fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
            if n_control_types == 1:
                axes = [axes]
            elif n_cols > 1:
                # When we have multiple columns, axes is a numpy array, convert to list
                axes = axes.tolist() if hasattr(axes, 'tolist') else list(axes)
            else:
                axes = [axes]
            
            # Store results for analysis
            analysis_results = []
            
            # Create each subplot
            for i, control_type in enumerate(top_control_types):
                ax = axes[i]
                
                # Find models that have this specific control type
                models_with_control_type = set(df_expanded[df_expanded['control_type'] == control_type]['run_id'].unique())
                
                # Calculate counts
                has_control_type = len(models_with_control_type)
                doesnt_have_control_type = total_model_count - has_control_type
                
                # Store results
                analysis_results.append({
                    'control_type': control_type,
                    'models_with_control_type': has_control_type,
                    'models_without_control_type': doesnt_have_control_type,
                    'total_models': total_model_count,
                    'percentage_with': (has_control_type / total_model_count) * 100,
                    'percentage_without': (doesnt_have_control_type / total_model_count) * 100
                })
                
                # Create pie chart data
                pie_data = [has_control_type, doesnt_have_control_type]
                #pie_labels = [f'Has {control_type}', f'No {control_type}']
                
                # Define colors: primary color for "has", light grey for "doesn't have"
                colors = [self.primary_colors[i % len(self.primary_colors)], '#CCCCCC']
                
                # Create pie chart
                wedges, texts, autotexts = ax.pie(pie_data, labels=None, 
                                                autopct='%1.1f%%', colors=colors, startangle=90,
                                                textprops={'fontsize': 12})
                
                # Enhance text
                for autotext in autotexts:
                    #make this text invisible
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
                    autotext.set_fontsize(18)
                
                # Set title
                ax.set_title(f'{control_type}\n({has_control_type}/{total_model_count} models)', 
                           fontsize=self.title_fontsize, fontweight='bold', pad=20)
                
                # Apply consistent styling
                self._apply_chart_style(ax, 'pie')
            
            # No need to hide unused subplots since we create exactly the number we need
            
            # Add overall title
            #fig.suptitle(f'Control Type Presence Analysis', 
            
            #            fontsize=self.title_fontsize, fontweight='bold', y=0.95)
            
            plt.tight_layout()
            plt.subplots_adjust(top=0.85)  # Make room for suptitle
            plt.show()
            
            # Create results DataFrame
            results_df = pd.DataFrame(analysis_results)
            
            # Print statistics
            print(f" Control Type Spotlight Analysis:")
            print(f"  • Total models analyzed: {total_model_count}")
            print(f"  • Control types analyzed: {len(top_control_types)}")
            print(f"  • Run ID range: {run_id_start} - {run_id_end}")
            
            print(f"\nControl Type Presence Statistics:")
            print(f"{'Control Type':<25} {'Models With':<12} {'Models Without':<15} {'Percentage With':<15}")
            print("-" * 70)
            for _, row in results_df.iterrows():
                print(f"{row['control_type']:<25} {row['models_with_control_type']:<12} {row['models_without_control_type']:<15} {row['percentage_with']:<15.1f}%")
            
            return results_df
            
        except Exception as e:
            print(f" Error in control type spotlight analysis: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()
    
    def get_robot_type_control_level_matrix(self,
                                          run_id_start: int = 7866,
                                          run_id_end: int = 8087,
                                          top_k_robot_types: int = 10,
                                          show_percentages: bool = False,
                                          figsize: Tuple[int, int] = (12, 8)) -> pd.DataFrame:
        """
        Create a matrix showing the relationship between robot types and control type levels.
        
        Args:
            run_id_start: Starting extraction run ID (default: 7866 for robotics data)
            run_id_end: Ending extraction run ID (default: 8087 for robotics data)
            top_k_robot_types: Number of top robot types to include in the matrix
            show_percentages: If True, show percentage distribution per robot type; if False, show absolute counts
            figsize: Figure size for the plot
        
        Returns:
            DataFrame matrix with robot types vs control levels
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get robot type and control type data together - count each combination once per paper
            query = """
            SELECT 
                ef_robot.value as robot_type,
                ef_control.value as control_type,
                COUNT(DISTINCT p.id) as count
            FROM papers p
            JOIN extraction_runs er ON p.id = er.paper_id
            JOIN extracted_fields ef_robot ON er.id = ef_robot.run_id
            JOIN extracted_fields ef_control ON er.id = ef_control.run_id
            WHERE er.id BETWEEN %s AND %s 
            AND ef_robot.field_name = 'robot_type'
            AND ef_control.field_name = 'control_type'
            AND ef_robot.value IS NOT NULL 
            AND ef_robot.value NOT IN ('n/a', 'unknown', '')
            AND ef_control.value IS NOT NULL 
            AND ef_control.value NOT IN ('n/a', 'unknown', '')
            GROUP BY ef_robot.value, ef_control.value
            ORDER BY count DESC
            """
            
            cursor.execute(query, (run_id_start, run_id_end))
            results = cursor.fetchall()
            
            if not results:
                print(" No robot type and control type combination data found")
                return pd.DataFrame()
            
            df = pd.DataFrame(results, columns=['robot_type', 'control_type', 'count'])
            
            # Expand array values in both robot_type and control_type fields
            df_expanded = self._expand_array_data(df, 'robot_type')
            df_expanded = self._expand_array_data(df_expanded, 'control_type')
            
            # Recalculate counts after expansion
            df_expanded = df_expanded.groupby(['robot_type', 'control_type'])['count'].sum().reset_index()
            
            # Get top K robot types by total occurrence
            robot_type_totals = df_expanded.groupby('robot_type')['count'].sum().sort_values(ascending=False)
            top_robot_types = robot_type_totals.head(top_k_robot_types).index.tolist()
            
            # Filter to only include top robot types
            df_filtered = df_expanded[df_expanded['robot_type'].isin(top_robot_types)]
            
            # Define control type level mapping
            control_level_mapping = {
                'low-level': ['low-level', 'low level', 'pid', 'pid control', 'torque control', 'force control', 
                             'position control', 'velocity control', 'joint control', 'motor control'],
                'high-level': ['high-level', 'high level', 'path planning', 'motion planning', 'task planning',
                              'behavioral control', 'navigation', 'slam', 'mapping'],
                'mid-level': ['mid-level', 'mid level', 'intermediate', 'model predictive control', 'mpc',
                             'adaptive control', 'robust control', 'feedback control'],
                'end-to-end': ['end-to-end', 'end to end', 'e2e', 'reinforcement learning', 'rl', 'neural network',
                              'deep learning', 'machine learning', 'imitation learning', 'learning-based']
            }
            
            # Map control types to levels
            def map_control_to_level(control_type):
                control_type_lower = control_type.lower()
                for level, keywords in control_level_mapping.items():
                    for keyword in keywords:
                        if keyword in control_type_lower:
                            return level
                return 'mid-level'  # Map unmatched control types to mid-level instead of other
            
            df_filtered['control_level'] = df_filtered['control_type'].apply(map_control_to_level)
            
            # Group by robot type and control level, summing counts
            df_matrix = df_filtered.groupby(['robot_type', 'control_level'])['count'].sum().reset_index()
            
            # Create pivot table for matrix
            matrix = df_matrix.pivot(index='robot_type', columns='control_level', values='count').fillna(0)
            
            # Ensure we have all control levels as columns (even if some are 0)
            desired_columns = ['low-level', 'mid-level', 'high-level', 'end-to-end']
            for col in desired_columns:
                if col not in matrix.columns:
                    matrix[col] = 0
            
            # Reorder columns in logical order
            matrix = matrix[desired_columns]
            
            # Convert to percentages if requested
            if show_percentages:
                # Calculate percentages for each robot type (row-wise)
                matrix_percentages = matrix.div(matrix.sum(axis=1), axis=0) * 100
                matrix_percentages = matrix_percentages.fillna(0)  # Handle division by zero
                display_matrix = matrix_percentages
                fmt_string = '.1f'
                cbar_label = 'Percentage (%)'
                value_suffix = '%'
            else:
                display_matrix = matrix
                fmt_string = '.0f'
                cbar_label = 'Number of Papers'
                value_suffix = ''
            
            # Sort rows by total count (descending) - use original counts for sorting even in percentage mode
            matrix['total'] = matrix.sum(axis=1)
            sorted_order = matrix.sort_values('total', ascending=False).index
            matrix = matrix.drop('total', axis=1)
            display_matrix = display_matrix.loc[sorted_order]
            
            # Create heatmap visualization
            fig, ax = plt.subplots(figsize=figsize)
            
            # Create the heatmap
            sns.heatmap(display_matrix, annot=True, fmt=fmt_string, cmap=self.heatmap_palette, ax=ax,
                       cbar_kws={'label': cbar_label}, 
                       linewidths=0.5, linecolor='white', annot_kws={"size": 18})
            
            ax.set_xlabel('Control Type Level', fontsize=20)
            ax.set_ylabel('Robot Type', fontsize=20)
            
            if show_percentages:
                title = f'Robot Type vs Control Level Matrix (Percentages)\n(Top {top_k_robot_types} Robot Types)'
            else:
                title = f'Robot Type vs Control Level Matrix (Counts)\n(Top {top_k_robot_types} Robot Types)'
            
            #ax.set_title(title, fontsize=self.title_fontsize, fontweight='bold')
            
            # Rotate labels for better readability
            plt.xticks(rotation=45, ha='right', fontsize=16)
            plt.yticks(rotation=0, fontsize=16)
            
            plt.tight_layout()
            plt.show()
            
            # Print summary statistics
            mode_text = "Percentages" if show_percentages else "Counts"
            print(f" Robot Type vs Control Level Matrix Analysis ({mode_text}):")
            print(f"  • Robot types analyzed: {len(matrix.index)}")
            print(f"  • Control levels: {len(matrix.columns)}")
            print(f"  • Total paper-robot type-control level combinations: {matrix.sum().sum():.0f}")
            
            print(f"\nTop robot types by total papers:")
            row_totals = matrix.sum(axis=1).sort_values(ascending=False)
            for i, (robot_type, total) in enumerate(row_totals.items(), 1):
                print(f"  {i:2d}. {robot_type}: {total:.0f} papers")
            
            if show_percentages:
                print(f"\nControl level preferences per robot type (showing percentages):")
                for robot_type in display_matrix.index:
                    print(f"\n  {robot_type}:")
                    robot_row = display_matrix.loc[robot_type].sort_values(ascending=False)
                    for level, percentage in robot_row.items():
                        if percentage > 0:
                            print(f"    • {level}: {percentage:.1f}%")
            else:
                print(f"\nControl level distribution across all top robot types:")
                col_totals = matrix.sum(axis=0).sort_values(ascending=False)
                for level, total in col_totals.items():
                    percentage = (total / col_totals.sum()) * 100
                    print(f"  • {level}: {total:.0f} papers ({percentage:.1f}%)")
            
            # Return the appropriate matrix based on mode
            return display_matrix if show_percentages else matrix
            
        except Exception as e:
            print(f" Error creating robot type vs control level matrix: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()
    
    def get_training_dataset_analysis(self, run_id_start: Optional[int] = None, 
                                     run_id_end: Optional[int] = None,
                                     top_k: int = 20,
                                     visualization_type: str = 'histogram',  # 'histogram' or 'stacked_percentage'
                                     one_per_paper: bool = True,
                                     figsize: Tuple[int, int] = (15, 10)) -> pd.DataFrame:
        """
        Analyze training datasets used in models.
        
        Args:
            run_id_start: Starting extraction run ID (inclusive)
            run_id_end: Ending extraction run ID (inclusive)
            top_k: Number of top datasets to show
            visualization_type: 'histogram' for simple histogram or 'stacked_percentage' for temporal stacked percentage
            one_per_paper: If True, count each dataset only once per paper; if False, count all model extractions
            figsize: Figure size for the plot
        
        Returns:
            DataFrame with training dataset analysis
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get training dataset data with optional paper-level deduplication
            if one_per_paper:
                # Count each dataset only once per paper
                query = """
                SELECT ef.value as training_dataset, COUNT(DISTINCT p.id) as count
                FROM papers p
                JOIN extraction_runs er ON p.id = er.paper_id
                JOIN extracted_fields ef ON er.id = ef.run_id
                WHERE ef.field_name = 'training_dataset'
                AND ef.value IS NOT NULL 
                AND ef.value NOT IN ('n/a', 'unknown', '')
                """
                
                if run_id_start is not None:
                    query += " AND er.id >= %s"
                if run_id_end is not None:
                    query += " AND er.id <= %s"
                
                query += """
                GROUP BY ef.value
                ORDER BY count DESC
                """
            else:
                # Count all model extractions (original behavior)
                query = """
                SELECT ef.value as training_dataset, COUNT(*) as count
                FROM papers p
                JOIN extraction_runs er ON p.id = er.paper_id
                JOIN extracted_fields ef ON er.id = ef.run_id
                WHERE ef.field_name = 'training_dataset'
                AND ef.value IS NOT NULL 
                AND ef.value NOT IN ('n/a', 'unknown', '')
                """
                
                if run_id_start is not None:
                    query += " AND er.id >= %s"
                if run_id_end is not None:
                    query += " AND er.id <= %s"
                
                query += """
                GROUP BY ef.value
                ORDER BY count DESC
                """
            
            params = []
            if run_id_start is not None:
                params.append(run_id_start)
            if run_id_end is not None:
                params.append(run_id_end)
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if not results:
                print(" No training dataset data found")
                return pd.DataFrame()
            
            # Print analysis mode information
            mode_text = "\nEach dataset counted only once per paper" if one_per_paper else "\nAll model extractions counted separately"
            print(f" Training Dataset Analysis ({mode_text}):")
            print(f"  • Analysis mode: {mode_text}")
            if one_per_paper:
                print(f"  • Each dataset counted only once per paper")
            else:
                print(f"  • All model extractions counted separately")
            
            df = pd.DataFrame(results, columns=['training_dataset', 'count'])
            
            # Expand array values in training_dataset field
            df_expanded = self._expand_array_data(df, 'training_dataset')
            df_expanded = df_expanded.groupby('training_dataset')['count'].sum().reset_index()
            df_expanded = df_expanded.sort_values('count', ascending=False)
            
            # Take top K for visualization
            df_top = df_expanded.head(top_k)
            
            
            
            # Create visualization based on type
            if visualization_type == 'stacked_percentage':
                # For stacked percentage, we need temporal data
                if one_per_paper:
                    # Count each dataset only once per paper per year
                    temporal_query = """
                    SELECT 
                        DATE_TRUNC('year', p.published_date) as year,
                        ef.value as training_dataset,
                        COUNT(DISTINCT p.id) as publication_count
                    FROM papers p
                    JOIN extraction_runs er ON p.id = er.paper_id
                    JOIN extracted_fields ef ON er.id = ef.run_id
                    WHERE ef.field_name = 'training_dataset'
                    AND p.published_date IS NOT NULL
                    AND ef.value NOT IN %s
                    """
                else:
                    # Count all model extractions per year (original behavior)
                    temporal_query = """
                    SELECT 
                        DATE_TRUNC('year', p.published_date) as year,
                        ef.value as training_dataset,
                        COUNT(*) as publication_count
                    FROM papers p
                    JOIN extraction_runs er ON p.id = er.paper_id
                    JOIN extracted_fields ef ON er.id = ef.run_id
                    WHERE ef.field_name = 'training_dataset'
                    AND p.published_date IS NOT NULL
                    AND ef.value NOT IN %s
                    """
                
                temporal_params = [tuple(self.default_na_values)]
                if run_id_start is not None:
                    temporal_query += " AND ef.run_id >= %s"
                    temporal_params.append(run_id_start)
                if run_id_end is not None:
                    temporal_query += " AND ef.run_id <= %s"
                    temporal_params.append(run_id_end)
                
                temporal_query += " GROUP BY year, training_dataset ORDER BY year, publication_count DESC"
                
                cursor.execute(temporal_query, temporal_params)
                temporal_results = cursor.fetchall()
                
                if temporal_results:
                    df_temporal = pd.DataFrame(temporal_results, columns=['year', 'training_dataset', 'publication_count'])
                    df_temporal['year'] = pd.to_datetime(df_temporal['year'])
                    
                    # Expand array values in temporal data
                    df_temporal_expanded = self._expand_array_data(df_temporal, 'training_dataset')
                    df_temporal_expanded = df_temporal_expanded.groupby(['year', 'training_dataset'])['publication_count'].sum().reset_index()
                    
                    # Create stacked percentage chart
                    chart_title = f'Top Training Datasets Over Time (Percentage) - {mode_text}'
                    self._create_stacked_percentage_chart(
                        df_temporal_expanded, 'training_dataset', 'publication_count', 
                        chart_title, figsize, top_k, 'primary'
                    )
                else:
                    print(" No temporal training dataset data found for stacked percentage visualization")
                    # Fall back to histogram
                    chart_title = f'Top {top_k} Training Datasets - {mode_text}'
                    self._create_histogram_chart(
                        df_top, 'training_dataset', 'count', 
                        chart_title, figsize, top_k, 'primary', True
                    )
            else:  # default 'histogram'
                # Create histogram
                chart_title = f'Top {top_k} Training Datasets - {mode_text}'
                self._create_histogram_chart(
                    df_top, 'training_dataset', 'count', 
                    chart_title, figsize, top_k, 'primary', True
                )
            
            return df_expanded
            
        except Exception as e:
            print(f" Error in training dataset analysis: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()
    
    def get_training_dataset_analysis_by_domain(self, 
                                              run_id_start: Optional[int] = None, 
                                              run_id_end: Optional[int] = None,
                                              target_domain: str = 'vision',
                                              exclude_domains: Optional[List[str]] = None,
                                              top_k: int = 20,
                                              include_na: bool = True,
                                              visualization_type: str = 'histogram',  # 'histogram' or 'stacked_percentage'
                                              one_per_paper: bool = True,
                                              figsize: Tuple[int, int] = (15, 10)) -> pd.DataFrame:
        """
        Analyze training datasets used in models filtered by a specific domain.
        N/A values are included as their own category.
        
        Args:
            run_id_start: Starting extraction run ID (inclusive)
            run_id_end: Ending extraction run ID (inclusive)
            target_domain: Domain to filter by (e.g., 'vision', 'language', 'audio')
            exclude_domains: List of domains to exclude from analysis (e.g., ['robotics', 'multimodal'])
            top_k: Number of top datasets to show
            include_na: If True, include N/A datasets as their own category; if False, exclude them
            visualization_type: 'histogram' for simple histogram or 'stacked_percentage' for temporal stacked percentage
            one_per_paper: If True, count each dataset only once per paper; if False, count all model extractions
            figsize: Figure size for the plot
        
        Returns:
            DataFrame with training dataset analysis filtered by domain
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get training dataset data filtered by domain with optional paper-level deduplication
            if one_per_paper:
                # Count each dataset only once per paper
                query = """
                SELECT ef_dataset.value as training_dataset, COUNT(DISTINCT p.id) as count
                FROM papers p
                JOIN extraction_runs er ON p.id = er.paper_id
                JOIN extracted_fields ef_dataset ON er.id = ef_dataset.run_id
                JOIN extracted_fields ef_domain ON er.id = ef_domain.run_id
                WHERE ef_dataset.field_name = 'training_dataset'
                AND ef_domain.field_name = 'domain'
                AND ef_dataset.value IS NOT NULL
                """
                
                # Handle N/A inclusion
                if not include_na:
                    query += " AND ef_dataset.value NOT IN %s"
                    na_params = [tuple(self.default_na_values)]
                else:
                    na_params = []
                
                params = na_params.copy()
                if run_id_start is not None:
                    query += " AND er.id >= %s"
                    params.append(run_id_start)
                if run_id_end is not None:
                    query += " AND er.id <= %s"
                    params.append(run_id_end)
                
                # Build domain filtering conditions
                domain_conditions = []
                domain_params = []
                
                # Include target domain
                domain_conditions.append("ef_domain.value ILIKE %s")
                domain_params.append(f'%{target_domain}%')
                
                # Exclude specified domains
                if exclude_domains:
                    for exclude_domain in exclude_domains:
                        domain_conditions.append("ef_domain.value NOT ILIKE %s")
                        domain_params.append(f'%{exclude_domain}%')
                
                query += """
                GROUP BY ef_dataset.value
                HAVING COUNT(DISTINCT CASE WHEN """ + " AND ".join(domain_conditions) + """ THEN p.id END) > 0
                ORDER BY count DESC
                """
                params.extend(domain_params)
                
            else:
                # Count all model extractions (original behavior)
                query = """
                SELECT ef_dataset.value as training_dataset, COUNT(*) as count
                FROM papers p
                JOIN extraction_runs er ON p.id = er.paper_id
                JOIN extracted_fields ef_dataset ON er.id = ef_dataset.run_id
                JOIN extracted_fields ef_domain ON er.id = ef_domain.run_id
                WHERE ef_dataset.field_name = 'training_dataset'
                AND ef_domain.field_name = 'domain'
                AND ef_dataset.value IS NOT NULL
                """
                
                # Handle N/A inclusion
                if not include_na:
                    query += " AND ef_dataset.value NOT IN %s"
                    na_params = [tuple(self.default_na_values)]
                else:
                    na_params = []
                
                params = na_params.copy()
                if run_id_start is not None:
                    query += " AND er.id >= %s"
                    params.append(run_id_start)
                if run_id_end is not None:
                    query += " AND er.id <= %s"
                    params.append(run_id_end)
                
                # Build domain filtering conditions
                domain_conditions = []
                domain_params = []
                
                # Include target domain
                domain_conditions.append("ef_domain.value ILIKE %s")
                domain_params.append(f'%{target_domain}%')
                
                # Exclude specified domains
                if exclude_domains:
                    for exclude_domain in exclude_domains:
                        domain_conditions.append("ef_domain.value NOT ILIKE %s")
                        domain_params.append(f'%{exclude_domain}%')
                
                query += """
                GROUP BY ef_dataset.value
                HAVING COUNT(CASE WHEN """ + " AND ".join(domain_conditions) + """ THEN 1 END) > 0
                ORDER BY count DESC
                """
                params.extend(domain_params)
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if not results:
                print(f" No training dataset data found for domain: {target_domain}")
                return pd.DataFrame()
            
            # Print analysis mode information
            mode_text = f"Each dataset counted only once per paper" if one_per_paper else "All model extractions counted separately"
            na_text = "including N/A values" if include_na else "excluding N/A values"
            exclude_text = f", excluding {exclude_domains}" if exclude_domains else ""
            print(f" Training Dataset Analysis for '{target_domain}' Domain ({mode_text}, {na_text}{exclude_text}):")
            
            df = pd.DataFrame(results, columns=['training_dataset', 'count'])
            
            # Handle N/A values specifically
            if include_na:
                # Replace N/A values with a consistent label
                na_mask = df['training_dataset'].isin(self.default_na_values)
                df.loc[na_mask, 'training_dataset'] = 'N/A or Not Specified'
                
                # Group N/A values together
                df = df.groupby('training_dataset')['count'].sum().reset_index()
                df = df.sort_values('count', ascending=False)
            
            # Expand array values in training_dataset field (only for non-N/A values)
            if include_na:
                # Separate N/A and non-N/A entries for processing
                na_entries = df[df['training_dataset'] == 'N/A or Not Specified']
                non_na_entries = df[df['training_dataset'] != 'N/A or Not Specified']
                
                if not non_na_entries.empty:
                    # Expand only non-N/A entries
                    df_expanded = self._expand_array_data(non_na_entries, 'training_dataset')
                    df_expanded = df_expanded.groupby('training_dataset')['count'].sum().reset_index()
                    
                    # Combine with N/A entries
                    if not na_entries.empty:
                        df_expanded = pd.concat([df_expanded, na_entries], ignore_index=True)
                else:
                    df_expanded = na_entries
            else:
                # Normal expansion for non-N/A only data
                df_expanded = self._expand_array_data(df, 'training_dataset')
                df_expanded = df_expanded.groupby('training_dataset')['count'].sum().reset_index()
            
            df_expanded = df_expanded.sort_values('count', ascending=False)
            
            # Take top K for visualization
            df_top = df_expanded.head(top_k)
            
            # Create visualization based on type
            if visualization_type == 'stacked_percentage':
                # For stacked percentage, we need temporal data
                self._create_domain_filtered_temporal_dataset_chart(
                    target_domain, exclude_domains, run_id_start, run_id_end, top_k, one_per_paper, include_na, figsize
                )
            else:  # default 'histogram'
                # Create histogram
                chart_title = f'Top {top_k} Training Datasets in {target_domain.title()} Domain'
                if include_na:
                    chart_title += ' (including N/A)'
                if exclude_domains:
                    chart_title += f' (excluding {", ".join(exclude_domains)})'
                self._create_histogram_chart(
                    df_top, 'training_dataset', 'count', 
                    chart_title, figsize, top_k, 'primary', True
                )
            
            # Print summary statistics
            print(f"  • Total unique datasets: {len(df_expanded)}")
            print(f"  • Total papers/models: {df_expanded['count'].sum()}")
            
            if include_na:
                na_count = df_expanded[df_expanded['training_dataset'] == 'N/A or Not Specified']['count'].sum()
                na_percentage = (na_count / df_expanded['count'].sum()) * 100
                print(f"  • N/A or unspecified datasets: {na_count} ({na_percentage:.1f}%)")
            
            print(f"\nTop {min(10, len(df_expanded))} datasets in {target_domain} domain:")
            for i, (_, row) in enumerate(df_expanded.head(10).iterrows(), 1):
                print(f"  {i:2d}. {row['training_dataset']}: {row['count']} papers")
            
            return df_expanded
            
        except Exception as e:
            print(f" Error in domain-filtered training dataset analysis: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()
    
    def _create_domain_filtered_temporal_dataset_chart(self, target_domain: str, exclude_domains: Optional[List[str]], 
                                                     run_id_start: Optional[int], run_id_end: Optional[int], 
                                                     top_k: int, one_per_paper: bool,
                                                     include_na: bool, figsize: Tuple[int, int]) -> None:
        """
        Create temporal stacked percentage chart for domain-filtered dataset analysis.
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get temporal data for the domain
            if one_per_paper:
                # Count each dataset only once per paper per year
                temporal_query = """
                SELECT 
                    DATE_TRUNC('year', p.published_date) as year,
                    ef_dataset.value as training_dataset,
                    COUNT(DISTINCT p.id) as publication_count
                FROM papers p
                JOIN extraction_runs er ON p.id = er.paper_id
                JOIN extracted_fields ef_dataset ON er.id = ef_dataset.run_id
                JOIN extracted_fields ef_domain ON er.id = ef_domain.run_id
                WHERE ef_dataset.field_name = 'training_dataset'
                AND ef_domain.field_name = 'domain'
                AND p.published_date IS NOT NULL
                AND ef_dataset.value IS NOT NULL
                """
            else:
                # Count all model extractions per year
                temporal_query = """
                SELECT 
                    DATE_TRUNC('year', p.published_date) as year,
                    ef_dataset.value as training_dataset,
                    COUNT(*) as publication_count
                FROM papers p
                JOIN extraction_runs er ON p.id = er.paper_id
                JOIN extracted_fields ef_dataset ON er.id = ef_dataset.run_id
                JOIN extracted_fields ef_domain ON er.id = ef_domain.run_id
                WHERE ef_dataset.field_name = 'training_dataset'
                AND ef_domain.field_name = 'domain'
                AND p.published_date IS NOT NULL
                AND ef_dataset.value IS NOT NULL
                """
            
            # Handle N/A inclusion
            temporal_params = []
            if not include_na:
                temporal_query += " AND ef_dataset.value NOT IN %s"
                temporal_params.append(tuple(self.default_na_values))
            
            if run_id_start is not None:
                temporal_query += " AND ef_dataset.run_id >= %s"
                temporal_params.append(run_id_start)
            if run_id_end is not None:
                temporal_query += " AND ef_dataset.run_id <= %s"
                temporal_params.append(run_id_end)
            
            # Build domain filtering conditions for temporal query
            domain_conditions = []
            domain_params = []
            
            # Include target domain
            domain_conditions.append("ef_domain.value ILIKE %s")
            domain_params.append(f'%{target_domain}%')
            
            # Exclude specified domains
            if exclude_domains:
                for exclude_domain in exclude_domains:
                    domain_conditions.append("ef_domain.value NOT ILIKE %s")
                    domain_params.append(f'%{exclude_domain}%')
            
            temporal_query += """
            GROUP BY year, ef_dataset.value
            HAVING COUNT(CASE WHEN """ + " AND ".join(domain_conditions) + """ THEN 1 END) > 0
            ORDER BY year, publication_count DESC
            """
            temporal_params.extend(domain_params)
            
            cursor.execute(temporal_query, temporal_params)
            temporal_results = cursor.fetchall()
            
            if temporal_results:
                df_temporal = pd.DataFrame(temporal_results, columns=['year', 'training_dataset', 'publication_count'])
                df_temporal['year'] = pd.to_datetime(df_temporal['year'])
                
                # Handle N/A values
                if include_na:
                    na_mask = df_temporal['training_dataset'].isin(self.default_na_values)
                    df_temporal.loc[na_mask, 'training_dataset'] = 'N/A or Not Specified'
                    df_temporal = df_temporal.groupby(['year', 'training_dataset'])['publication_count'].sum().reset_index()
                
                # Expand array values in temporal data (only for non-N/A values)
                if include_na:
                    na_temporal = df_temporal[df_temporal['training_dataset'] == 'N/A or Not Specified']
                    non_na_temporal = df_temporal[df_temporal['training_dataset'] != 'N/A or Not Specified']
                    
                    if not non_na_temporal.empty:
                        df_temporal_expanded = self._expand_array_data(non_na_temporal, 'training_dataset')
                        df_temporal_expanded = df_temporal_expanded.groupby(['year', 'training_dataset'])['publication_count'].sum().reset_index()
                        
                        if not na_temporal.empty:
                            df_temporal_expanded = pd.concat([df_temporal_expanded, na_temporal], ignore_index=True)
                    else:
                        df_temporal_expanded = na_temporal
                else:
                    df_temporal_expanded = self._expand_array_data(df_temporal, 'training_dataset')
                    df_temporal_expanded = df_temporal_expanded.groupby(['year', 'training_dataset'])['publication_count'].sum().reset_index()
                
                # Create stacked percentage chart
                chart_title = f'Top Training Datasets in {target_domain.title()} Domain Over Time (Percentage)'
                if include_na:
                    chart_title += ' (including N/A)'
                if exclude_domains:
                    chart_title += f' (excluding {", ".join(exclude_domains)})'
                
                self._create_stacked_percentage_chart(
                    df_temporal_expanded, 'training_dataset', 'publication_count', 
                    chart_title, figsize, top_k, 'primary'
                )
            else:
                print(" No temporal training dataset data found for stacked percentage visualization")
                
        except Exception as e:
            print(f" Error creating temporal domain-filtered dataset chart: {e}")
        finally:
            if conn:
                conn.close()
    
    def get_training_dataset_analysis_by_task(self, 
                                            run_id_start: Optional[int] = None, 
                                            run_id_end: Optional[int] = None,
                                            include_task_keywords: Optional[List[str]] = None,
                                            exclude_task_keywords: Optional[List[str]] = None,
                                            top_k: int = 20,
                                            include_na: bool = True,
                                            visualization_type: str = 'histogram',  # 'histogram' or 'stacked_percentage'
                                            one_per_paper: bool = True,
                                            figsize: Tuple[int, int] = (15, 10)) -> pd.DataFrame:
        """
        Analyze training datasets used in models filtered by task keywords.
        Tasks are filtered by word matching within task arrays like {"language modeling/generation"}.
        N/A values are included as their own category.
        
        Args:
            run_id_start: Starting extraction run ID (inclusive)
            run_id_end: Ending extraction run ID (inclusive)
            include_task_keywords: List of keywords that must be present in task (e.g., ['language', 'text'])
            exclude_task_keywords: List of keywords to exclude from task (e.g., ['image', 'vision'])
            top_k: Number of top datasets to show
            include_na: If True, include N/A datasets as their own category; if False, exclude them
            visualization_type: 'histogram' for simple histogram or 'stacked_percentage' for temporal stacked percentage
            one_per_paper: If True, count each dataset only once per paper; if False, count all model extractions
            figsize: Figure size for the plot
        
        Returns:
            DataFrame with training dataset analysis filtered by task keywords
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Build task filtering conditions
            task_conditions = []
            task_params = []
            
            # Include task keywords (at least one must match)
            if include_task_keywords:
                include_conditions = []
                for keyword in include_task_keywords:
                    include_conditions.append("ef_task.value ILIKE %s")
                    task_params.append(f'%{keyword}%')
                
                if include_conditions:
                    task_conditions.append(f"({' OR '.join(include_conditions)})")
            
            # Exclude task keywords (none should match)
            if exclude_task_keywords:
                for keyword in exclude_task_keywords:
                    task_conditions.append("ef_task.value NOT ILIKE %s")
                    task_params.append(f'%{keyword}%')
            
            # Build the base query based on counting method
            if one_per_paper:
                # Count each dataset only once per paper
                query = """
                SELECT ef_dataset.value as training_dataset, COUNT(DISTINCT p.id) as count
                FROM papers p
                JOIN extraction_runs er ON p.id = er.paper_id
                JOIN extracted_fields ef_dataset ON er.id = ef_dataset.run_id
                JOIN extracted_fields ef_task ON er.id = ef_task.run_id
                WHERE ef_dataset.field_name = 'training_dataset'
                AND ef_task.field_name = 'task'
                AND ef_dataset.value IS NOT NULL
                AND ef_task.value IS NOT NULL
                """
            else:
                # Count all model extractions
                query = """
                SELECT ef_dataset.value as training_dataset, COUNT(*) as count
                FROM papers p
                JOIN extraction_runs er ON p.id = er.paper_id
                JOIN extracted_fields ef_dataset ON er.id = ef_dataset.run_id
                JOIN extracted_fields ef_task ON er.id = ef_task.run_id
                WHERE ef_dataset.field_name = 'training_dataset'
                AND ef_task.field_name = 'task'
                AND ef_dataset.value IS NOT NULL
                AND ef_task.value IS NOT NULL
                """
            
            # Handle N/A inclusion for datasets
            params = []
            if not include_na:
                query += " AND ef_dataset.value NOT IN %s"
                params.append(tuple(self.default_na_values))
            
            # Add run ID filters
            if run_id_start is not None:
                query += " AND er.id >= %s"
                params.append(run_id_start)
            if run_id_end is not None:
                query += " AND er.id <= %s"
                params.append(run_id_end)
            
            # Add task filtering
            if task_conditions:
                query += " AND " + " AND ".join(task_conditions)
                params.extend(task_params)
            
            query += """
            GROUP BY ef_dataset.value
            ORDER BY count DESC
            """
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if not results:
                filter_desc = self._build_task_filter_description(include_task_keywords, exclude_task_keywords)
                print(f" No training dataset data found for task filter: {filter_desc}")
                return pd.DataFrame()
            
            # Print analysis mode information
            mode_text = f"Each dataset counted only once per paper" if one_per_paper else "All model extractions counted separately"
            na_text = "including N/A values" if include_na else "excluding N/A values"
            filter_desc = self._build_task_filter_description(include_task_keywords, exclude_task_keywords)
            print(f" Training Dataset Analysis by Task ({filter_desc}) - ({mode_text}, {na_text}):")
            
            df = pd.DataFrame(results, columns=['training_dataset', 'count'])
            
            # Handle N/A values specifically
            if include_na:
                # Replace N/A values with a consistent label
                na_mask = df['training_dataset'].isin(self.default_na_values)
                df.loc[na_mask, 'training_dataset'] = 'N/A or Not Specified'
                
                # Group N/A values together
                df = df.groupby('training_dataset')['count'].sum().reset_index()
                df = df.sort_values('count', ascending=False)
            
            # Expand array values in training_dataset field (only for non-N/A values)
            if include_na:
                # Separate N/A and non-N/A entries for processing
                na_entries = df[df['training_dataset'] == 'N/A or Not Specified']
                non_na_entries = df[df['training_dataset'] != 'N/A or Not Specified']
                
                if not non_na_entries.empty:
                    # Expand only non-N/A entries
                    df_expanded = self._expand_array_data(non_na_entries, 'training_dataset')
                    df_expanded = df_expanded.groupby('training_dataset')['count'].sum().reset_index()
                    
                    # Combine with N/A entries
                    if not na_entries.empty:
                        df_expanded = pd.concat([df_expanded, na_entries], ignore_index=True)
                else:
                    df_expanded = na_entries
            else:
                # Normal expansion for non-N/A only data
                df_expanded = self._expand_array_data(df, 'training_dataset')
                df_expanded = df_expanded.groupby('training_dataset')['count'].sum().reset_index()
            
            df_expanded = df_expanded.sort_values('count', ascending=False)
            
            # Take top K for visualization
            df_top = df_expanded.head(top_k)
            
            # Create visualization based on type
            if visualization_type == 'stacked_percentage':
                # For stacked percentage, we need temporal data
                self._create_task_filtered_temporal_dataset_chart(
                    include_task_keywords, exclude_task_keywords, run_id_start, run_id_end, 
                    top_k, one_per_paper, include_na, figsize
                )
            else:  # default 'histogram'
                # Create histogram
                chart_title = f'Top {top_k} Training Datasets by Task ({filter_desc})'
                if include_na:
                    chart_title += ' (including N/A)'
                
                self._create_histogram_chart(
                    df_top, 'training_dataset', 'count', 
                    chart_title, figsize, top_k, 'primary', True
                )
            
            # Print summary statistics
            print(f"  • Total unique datasets: {len(df_expanded)}")
            print(f"  • Total papers/models: {df_expanded['count'].sum()}")
            
            if include_na:
                na_count = df_expanded[df_expanded['training_dataset'] == 'N/A or Not Specified']['count'].sum()
                na_percentage = (na_count / df_expanded['count'].sum()) * 100
                print(f"  • N/A or unspecified datasets: {na_count} ({na_percentage:.1f}%)")
            
            print(f"\nTop {min(10, len(df_expanded))} datasets for task filter ({filter_desc}):")
            for i, (_, row) in enumerate(df_expanded.head(10).iterrows(), 1):
                print(f"  {i:2d}. {row['training_dataset']}: {row['count']} papers")
            
            return df_expanded
            
        except Exception as e:
            print(f" Error in task-filtered training dataset analysis: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()
    
    def _build_task_filter_description(self, include_keywords: Optional[List[str]], 
                                     exclude_keywords: Optional[List[str]]) -> str:
        """
        Build a human-readable description of the task filtering criteria.
        """
        parts = []
        
        if include_keywords:
            if len(include_keywords) == 1:
                parts.append(f"including '{include_keywords[0]}'")
            else:
                parts.append(f"including {include_keywords}")
        
        if exclude_keywords:
            if len(exclude_keywords) == 1:
                parts.append(f"excluding '{exclude_keywords[0]}'")
            else:
                parts.append(f"excluding {exclude_keywords}")
        
        if not parts:
            return "all tasks"
        
        return ", ".join(parts)
    
    def _create_task_filtered_temporal_dataset_chart(self, include_task_keywords: Optional[List[str]], 
                                                   exclude_task_keywords: Optional[List[str]],
                                                   run_id_start: Optional[int], run_id_end: Optional[int], 
                                                   top_k: int, one_per_paper: bool,
                                                   include_na: bool, figsize: Tuple[int, int]) -> None:
        """
        Create temporal stacked percentage chart for task-filtered dataset analysis.
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Build task filtering conditions
            task_conditions = []
            task_params = []
            
            # Include task keywords (at least one must match)
            if include_task_keywords:
                include_conditions = []
                for keyword in include_task_keywords:
                    include_conditions.append("ef_task.value ILIKE %s")
                    task_params.append(f'%{keyword}%')
                
                if include_conditions:
                    task_conditions.append(f"({' OR '.join(include_conditions)})")
            
            # Exclude task keywords (none should match)
            if exclude_task_keywords:
                for keyword in exclude_task_keywords:
                    task_conditions.append("ef_task.value NOT ILIKE %s")
                    task_params.append(f'%{keyword}%')
            
            # Get temporal data for the task filter
            if one_per_paper:
                # Count each dataset only once per paper per year
                temporal_query = """
                SELECT 
                    DATE_TRUNC('year', p.published_date) as year,
                    ef_dataset.value as training_dataset,
                    COUNT(DISTINCT p.id) as publication_count
                FROM papers p
                JOIN extraction_runs er ON p.id = er.paper_id
                JOIN extracted_fields ef_dataset ON er.id = ef_dataset.run_id
                JOIN extracted_fields ef_task ON er.id = ef_task.run_id
                WHERE ef_dataset.field_name = 'training_dataset'
                AND ef_task.field_name = 'task'
                AND p.published_date IS NOT NULL
                AND ef_dataset.value IS NOT NULL
                AND ef_task.value IS NOT NULL
                """
            else:
                # Count all model extractions per year
                temporal_query = """
                SELECT 
                    DATE_TRUNC('year', p.published_date) as year,
                    ef_dataset.value as training_dataset,
                    COUNT(*) as publication_count
                FROM papers p
                JOIN extraction_runs er ON p.id = er.paper_id
                JOIN extracted_fields ef_dataset ON er.id = ef_dataset.run_id
                JOIN extracted_fields ef_task ON er.id = ef_task.run_id
                WHERE ef_dataset.field_name = 'training_dataset'
                AND ef_task.field_name = 'task'
                AND p.published_date IS NOT NULL
                AND ef_dataset.value IS NOT NULL
                AND ef_task.value IS NOT NULL
                """
            
            # Handle N/A inclusion
            temporal_params = []
            if not include_na:
                temporal_query += " AND ef_dataset.value NOT IN %s"
                temporal_params.append(tuple(self.default_na_values))
            
            if run_id_start is not None:
                temporal_query += " AND ef_dataset.run_id >= %s"
                temporal_params.append(run_id_start)
            if run_id_end is not None:
                temporal_query += " AND ef_dataset.run_id <= %s"
                temporal_params.append(run_id_end)
            
            # Add task filtering
            if task_conditions:
                temporal_query += " AND " + " AND ".join(task_conditions)
                temporal_params.extend(task_params)
            
            temporal_query += """
            GROUP BY year, ef_dataset.value
            ORDER BY year, publication_count DESC
            """
            
            cursor.execute(temporal_query, temporal_params)
            temporal_results = cursor.fetchall()
            
            if temporal_results:
                df_temporal = pd.DataFrame(temporal_results, columns=['year', 'training_dataset', 'publication_count'])
                df_temporal['year'] = pd.to_datetime(df_temporal['year'])
                
                # Handle N/A values
                if include_na:
                    na_mask = df_temporal['training_dataset'].isin(self.default_na_values)
                    df_temporal.loc[na_mask, 'training_dataset'] = 'N/A or Not Specified'
                    df_temporal = df_temporal.groupby(['year', 'training_dataset'])['publication_count'].sum().reset_index()
                
                # Expand array values in temporal data (only for non-N/A values)
                if include_na:
                    na_temporal = df_temporal[df_temporal['training_dataset'] == 'N/A or Not Specified']
                    non_na_temporal = df_temporal[df_temporal['training_dataset'] != 'N/A or Not Specified']
                    
                    if not non_na_temporal.empty:
                        df_temporal_expanded = self._expand_array_data(non_na_temporal, 'training_dataset')
                        df_temporal_expanded = df_temporal_expanded.groupby(['year', 'training_dataset'])['publication_count'].sum().reset_index()
                        
                        if not na_temporal.empty:
                            df_temporal_expanded = pd.concat([df_temporal_expanded, na_temporal], ignore_index=True)
                    else:
                        df_temporal_expanded = na_temporal
                else:
                    df_temporal_expanded = self._expand_array_data(df_temporal, 'training_dataset')
                    df_temporal_expanded = df_temporal_expanded.groupby(['year', 'training_dataset'])['publication_count'].sum().reset_index()
                
                # Create stacked percentage chart
                filter_desc = self._build_task_filter_description(include_task_keywords, exclude_task_keywords)
                chart_title = f'Top Training Datasets by Task ({filter_desc}) Over Time (Percentage)'
                if include_na:
                    chart_title += ' (including N/A)'
                
                self._create_stacked_percentage_chart(
                    df_temporal_expanded, 'training_dataset', 'publication_count', 
                    chart_title, figsize, top_k, 'primary'
                )
            else:
                print(" No temporal training dataset data found for stacked percentage visualization")
                
        except Exception as e:
            print(f" Error creating temporal task-filtered dataset chart: {e}")
        finally:
            if conn:
                conn.close()
    
    def get_organization_analysis(self, run_id_start: Optional[int] = None, 
                                 run_id_end: Optional[int] = None,
                                 top_k: int = 20,
                                 csv_file: str = "ai_orgs.csv",
                                 count_type: str = 'models',  # 'models', 'papers', or 'both'
                                 sort_by: str = 'models',  # 'models' or 'papers' (only used when count_type='both')
                                 visualization_type: str = 'histogram',  # 'histogram' or 'stacked_percentage'
                                 figsize: Tuple[int, int] = (15, 10)) -> pd.DataFrame:
        """
        Analyze organizations involved in research, grouped by main organizations.
        
        Args:
            run_id_start: Starting extraction run ID (inclusive)
            run_id_end: Ending extraction run ID (inclusive)
            top_k: Number of top organizations to show
            csv_file: Path to CSV file with organization mappings
            count_type: 'models' for model count, 'papers' for publication count, 'both' for side-by-side comparison
            sort_by: 'models' or 'papers' - determines sorting order when count_type='both'
            visualization_type: 'histogram' for simple histogram or 'stacked_percentage' for temporal stacked percentage
            figsize: Figure size for the plot
        
        Returns:
            DataFrame with organization analysis grouped by main organizations
        """
        conn = None
        try:
            # Validate count_type parameter
            if count_type not in ['models', 'papers', 'both']:
                raise ValueError("count_type must be 'models', 'papers', or 'both'")
            
            # Validate sort_by parameter
            if sort_by not in ['models', 'papers']:
                raise ValueError("sort_by must be 'models' or 'papers'")
            
            # Load main organization mapping
            main_org_mapping = self._load_main_org_mapping(csv_file)
            if not main_org_mapping:
                print(" No main organization mapping loaded")
                return pd.DataFrame()
            
            conn = get_connection()
            cursor = conn.cursor()
            
            def get_organization_data(metric_type: str):
                """Helper function to get organization data for models or papers"""
                if metric_type == 'models':
                    # Count models (extraction runs)
                    query = """
                    SELECT ef.value as organization, COUNT(*) as count
                    FROM papers p
                    JOIN extraction_runs er ON p.id = er.paper_id
                    JOIN extracted_fields ef ON er.id = ef.run_id
                    WHERE ef.field_name = 'organization'
                    AND ef.value IS NOT NULL 
                    AND ef.value NOT IN ('n/a', 'unknown', '')
                    """
                else:  # papers
                    # Count distinct papers
                    query = """
                    SELECT ef.value as organization, COUNT(DISTINCT p.id) as count
                    FROM papers p
                    JOIN extraction_runs er ON p.id = er.paper_id
                    JOIN extracted_fields ef ON er.id = ef.run_id
                    WHERE ef.field_name = 'organization'
                    AND ef.value IS NOT NULL 
                    AND ef.value NOT IN ('n/a', 'unknown', '')
                    """
                
                params = []
                if run_id_start is not None:
                    query += " AND er.id >= %s"
                    params.append(run_id_start)
                if run_id_end is not None:
                    query += " AND er.id <= %s"
                    params.append(run_id_end)
                
                query += " GROUP BY ef.value ORDER BY count DESC"
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                if not results:
                    return pd.DataFrame()
                
                df = pd.DataFrame(results, columns=['organization', f'{metric_type}_count'])
                
                # Expand array values in organization field
                df_expanded = self._expand_array_data(df, 'organization')
                df_expanded = df_expanded.groupby('organization')[f'{metric_type}_count'].sum().reset_index()
                
                # Map organizations to main organizations
                main_org_data = []
                
                for _, row in df_expanded.iterrows():
                    organizations = self._split_organization_names(row['organization'])
                    main_orgs = self._map_organizations_to_main_org(organizations, main_org_mapping)
                    
                    # If no main org mapping found, use original organization name
                    if not main_orgs:
                        main_orgs = [row['organization']]
                    
                    # Create one entry per main organization
                    for main_org in main_orgs:
                        main_org_data.append({
                            'organization': main_org,
                            f'{metric_type}_count': row[f'{metric_type}_count']
                        })
                
                if not main_org_data:
                    return pd.DataFrame()
                
                # Aggregate by main organization
                df_main_org = pd.DataFrame(main_org_data)
                df_main_org = df_main_org.groupby('organization')[f'{metric_type}_count'].sum().reset_index()
                
                return df_main_org
            
            # Get data based on count_type
            if count_type == 'models':
                df_main_org = get_organization_data('models')
                if df_main_org.empty:
                    print(" No organization data found")
                    return pd.DataFrame()
                df_main_org = df_main_org.sort_values('models_count', ascending=False)
                
            elif count_type == 'papers':
                df_main_org = get_organization_data('papers')
                if df_main_org.empty:
                    print(" No organization data found")
                    return pd.DataFrame()
                df_main_org = df_main_org.sort_values('papers_count', ascending=False)
                
            else:  # both
                df_models = get_organization_data('models')
                df_papers = get_organization_data('papers')
                
                if df_models.empty or df_papers.empty:
                    print(" No organization data found")
                    return pd.DataFrame()
                
                # Merge the two dataframes
                df_main_org = pd.merge(df_models, df_papers, on='organization', how='outer').fillna(0)
                df_main_org['models_count'] = df_main_org['models_count'].astype(int)
                df_main_org['papers_count'] = df_main_org['papers_count'].astype(int)
                
                # Sort by specified metric
                sort_column = f'{sort_by}_count'
                df_main_org = df_main_org.sort_values(sort_column, ascending=False)
            
            # Take top K for visualization
            df_top = df_main_org.head(top_k)
            
            # Create visualization based on count_type
            if count_type == 'both':
                # Create side-by-side comparison chart
                self._create_dual_metric_chart(df_top, 'organization', 'models_count', 'papers_count', 
                                             f'Top {top_k} Organizations: Models vs Papers', figsize)
            
            elif visualization_type == 'stacked_percentage':
                # For stacked percentage, we need temporal data
                metric_column = 'models_count' if count_type == 'models' else 'papers_count'
                count_query = "COUNT(*)" if count_type == 'models' else "COUNT(DISTINCT p.id)"
                
                temporal_query = f"""
                SELECT 
                    DATE_TRUNC('year', p.published_date) as year,
                    ef.value as organization,
                    {count_query} as count
                FROM papers p
                JOIN extraction_runs er ON p.id = er.paper_id
                JOIN extracted_fields ef ON er.id = ef.run_id
                WHERE ef.field_name = 'organization'
                AND p.published_date IS NOT NULL
                AND p.published_date >= '2013-01-01'
                AND p.published_date <= '2024-12-31'
                AND ef.value NOT IN %s
                """
                
                temporal_params = [tuple(self.default_na_values)]
                if run_id_start is not None:
                    temporal_query += " AND ef.run_id >= %s"
                    temporal_params.append(run_id_start)
                if run_id_end is not None:
                    temporal_query += " AND ef.run_id <= %s"
                    temporal_params.append(run_id_end)
                
                temporal_query += " GROUP BY year, organization ORDER BY year, count DESC"
                
                cursor.execute(temporal_query, temporal_params)
                temporal_results = cursor.fetchall()
                
                if temporal_results:
                    df_temporal = pd.DataFrame(temporal_results, columns=['year', 'organization', 'count'])
                    df_temporal['year'] = pd.to_datetime(df_temporal['year'])
                    
                    # Process organizations and map to main organizations
                    temporal_main_org_data = []
                    
                    for _, row in df_temporal.iterrows():
                        organizations = self._split_organization_names(row['organization'])
                        main_orgs = self._map_organizations_to_main_org(organizations, main_org_mapping)
                        
                        # If no main org mapping found, use original organizations
                        if not main_orgs:
                            main_orgs = organizations
                        
                        # Create one entry per main organization
                        for main_org in main_orgs:
                            temporal_main_org_data.append({
                                'year': row['year'],
                                'organization': main_org,
                                'count': row['count']
                            })
                    
                    if temporal_main_org_data:
                        df_temporal_main_org = pd.DataFrame(temporal_main_org_data)
                        df_temporal_main_org = df_temporal_main_org.groupby(['year', 'organization'])['count'].sum().reset_index()
                        
                        # Create stacked percentage chart
                        chart_title = f'Top Organizations Over Time ({count_type.title()} - Percentage)'
                        self._create_stacked_percentage_chart(
                            df_temporal_main_org, 'organization', 'count', 
                            chart_title, figsize, top_k, 'primary'
                        )
                    else:
                        print(" No temporal organization data found for stacked percentage visualization")
                        # Fall back to histogram
                        self._create_single_metric_histogram(df_top, count_type, top_k, figsize)
                else:
                    print(" No temporal organization data found for stacked percentage visualization")
                    # Fall back to histogram
                    self._create_single_metric_histogram(df_top, count_type, top_k, figsize)
            else:  # default 'histogram'
                # Create histogram
                self._create_single_metric_histogram(df_top, count_type, top_k, figsize)
            
            # Print results based on count_type
            self._print_organization_results(df_main_org, df_top, count_type, sort_by, top_k)
            
            return df_main_org
            
        except Exception as e:
            print(f" Error in organization analysis: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()
    
    def _create_dual_metric_chart(self, df: pd.DataFrame, org_column: str, 
                                 models_column: str, papers_column: str, 
                                 title: str, figsize: Tuple[int, int]) -> None:
        """Create side-by-side comparison chart for models and papers counts."""
        fig, ax = plt.subplots(figsize=figsize)
        
        # Set up the bar positions
        x = np.arange(len(df))
        width = 0.35
        
        # Get colors (orange for models, blue for papers)
        colors = self._get_colors(2, 'primary')
        models_color = '#ff7f0e'  # Orange
        papers_color = '#1f77b4'  # Blue
        
        # Create bars
        bars1 = ax.bar(x - width/2, df[models_column], width, label='Models', color=models_color, alpha=0.8)
        bars2 = ax.bar(x + width/2, df[papers_column], width, label='Papers', color=papers_color, alpha=0.8)
        
        # Customize the chart
        ax.set_xlabel('Organization', fontsize=20)
        ax.set_ylabel('Count', fontsize=20)
        #ax.set_title(title, fontsize=self.title_fontsize, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(df[org_column], rotation=45, ha='right', fontsize=14)
        ax.legend(fontsize=18)
        
        # Add value labels on bars
        for bar in bars1:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height + max(df[models_column])*0.01,
                       f'{int(height)}', ha='center', va='bottom', fontsize=14)
        
        for bar in bars2:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height + max(df[papers_column])*0.01,
                       f'{int(height)}', ha='center', va='bottom', fontsize=14)
        
        # Apply chart styling
        self._apply_chart_style(ax)
        
        plt.tight_layout()
        plt.show()
    
    def _create_single_metric_histogram(self, df: pd.DataFrame, count_type: str, 
                                      top_k: int, figsize: Tuple[int, int]) -> None:
        """Create histogram for single metric (models or papers)."""
        metric_column = f'{count_type}_count'
        chart_title = f'Top {top_k} Organizations ({count_type.title()} Count)'
        
        self._create_histogram_chart(
            df, 'organization', metric_column, 
            chart_title, figsize, top_k, 'secondary', True
        )
    
    def _print_organization_results(self, df_main_org: pd.DataFrame, df_top: pd.DataFrame, 
                                  count_type: str, sort_by: str, top_k: int) -> None:
        """Print organization analysis results based on count_type."""
        print(f" Organization Analysis (Grouped by Main Organization):")
        print(f"  • Total main organizations: {len(df_main_org)}")
        
        if count_type == 'models':
            print(f"  • Top {top_k} main organizations by model count:")
            for i, (_, row) in enumerate(df_top.iterrows(), 1):
                print(f"    {i:2d}. {row['organization']}: {row['models_count']} models")
        
        elif count_type == 'papers':
            print(f"  • Top {top_k} main organizations by paper count:")
            for i, (_, row) in enumerate(df_top.iterrows(), 1):
                print(f"    {i:2d}. {row['organization']}: {row['papers_count']} papers")
        
        else:  # both
            print(f"  • Top {top_k} main organizations (sorted by {sort_by} count):")
            for i, (_, row) in enumerate(df_top.iterrows(), 1):
                print(f"    {i:2d}. {row['organization']}: {row['models_count']} models, {row['papers_count']} papers")
    
    def _load_organization_mapping(self, csv_file: str = "ai_orgs.csv") -> Dict[str, Dict[str, str]]:
        """
        Load organization to country/region mapping from CSV file.
        
        Args:
            csv_file: Path to the CSV file containing organization mappings
            
        Returns:
            Dictionary mapping organization names to country and region
        """
        try:
            # Read the CSV file with tab separator since it appears to be tab-delimited
            df = pd.read_csv(csv_file, sep='\t')
            
            # Create mapping dictionary
            org_mapping = {}
            
            for _, row in df.iterrows():
                institution = str(row['Instiution']).strip()
                country = str(row['Country']).strip()
                region = str(row['Region']).strip()
                
                # Skip entries with n/a values
                if country.lower() == 'n/a' or region.lower() == 'n/a':
                    continue
                
                org_mapping[institution] = {
                    'country': country,
                    'region': region
                }
            
            print(f" Loaded {len(org_mapping)} organization mappings from {csv_file}")
            return org_mapping
            
        except Exception as e:
            print(f" Error loading organization mapping: {e}")
            return {}
    
    def _load_main_org_mapping(self, csv_file: str = "ai_orgs.csv") -> Dict[str, str]:
        """
        Load organization to main organization mapping from CSV file.
        
        Args:
            csv_file: Path to the CSV file containing organization mappings
            
        Returns:
            Dictionary mapping organization names to their main organization
        """
        try:
            # Read the CSV file with tab separator since it appears to be tab-delimited
            df = pd.read_csv(csv_file, sep='\t')
            
            # Create mapping dictionary
            main_org_mapping = {}
            
            for _, row in df.iterrows():
                institution = str(row['Instiution']).strip()
                main_org = str(row['MainOrg']).strip()
                
                # Skip entries with n/a values
                if main_org.lower() == 'n/a' or main_org == '':
                    continue
                
                main_org_mapping[institution] = main_org
            
            print(f" Loaded {len(main_org_mapping)} main organization mappings from {csv_file}")
            return main_org_mapping
            
        except Exception as e:
            print(f" Error loading main organization mapping: {e}")
            return {}
    
    def _clean_organization_name(self, name: str) -> str:
        """
        Clean organization name using the same logic as the institution cleaner.
        
        Args:
            name: Raw organization name
            
        Returns:
            Cleaned organization name
        """
        # Remove extra whitespace
        name = name.strip()
        
        # Remove all quotes (single and double)
        name = re.sub(r'["\']', '', name)
        
        # Remove brackets and parentheses
        name = re.sub(r'[\[\](){}]', '', name)
        
        # Remove common prefixes/suffixes that might be artifacts
        name = re.sub(r'^n/a$', '', name, flags=re.IGNORECASE)
        name = re.sub(r'^unknown$', '', name, flags=re.IGNORECASE)
        name = re.sub(r'^not specified$', '', name, flags=re.IGNORECASE)
        
        # Clean up extra spaces
        name = re.sub(r'\s+', ' ', name)
        
        return name.strip()
    
    def _split_organization_names(self, text: str) -> List[str]:
        """
        Split organization names by various separators using the same logic as the institution cleaner.
        
        Args:
            text: Text containing organization names
            
        Returns:
            List of individual organization names
        """
        if not text or text.lower() in ['n/a', 'unknown', 'not specified', '']:
            return []
        
        # Define separators in order of preference (most specific first)
        separators = [';', ',', ' & ', ' and ']
        
        # Start with the original text
        current_parts = [text.strip()]
        
        # Apply each separator to all current parts
        for sep in separators:
            new_parts = []
            for part in current_parts:
                if sep in part:
                    # Split this part by the separator
                    split_parts = [p.strip() for p in part.split(sep) if p.strip()]
                    new_parts.extend(split_parts)
                else:
                    # Keep the part as is
                    new_parts.append(part)
            current_parts = new_parts
        
        # Filter out empty parts and clean each part
        cleaned_parts = []
        for part in current_parts:
            cleaned = self._clean_organization_name(part)
            if cleaned:
                cleaned_parts.append(cleaned)
        
        return cleaned_parts
    
    def _map_organizations_to_location(self, organizations: List[str], org_mapping: Dict[str, Dict[str, str]], 
                                     location_type: str = 'country') -> List[str]:
        """
        Map organization names to countries or regions.
        
        Args:
            organizations: List of organization names
            org_mapping: Dictionary mapping organizations to locations
            location_type: 'country' or 'region'
            
        Returns:
            List of mapped locations
        """
        locations = []
        
        for org in organizations:
            cleaned_org = self._clean_organization_name(org)
            
            # Try exact match first
            if cleaned_org in org_mapping:
                location = org_mapping[cleaned_org][location_type]
                if location.lower() != 'n/a':
                    locations.append(location)
                continue
            
            # Try partial matching for common variations
            for mapped_org, mapping in org_mapping.items():
                if (cleaned_org.lower() in mapped_org.lower() or 
                    mapped_org.lower() in cleaned_org.lower()):
                    location = mapping[location_type]
                    if location.lower() != 'n/a':
                        locations.append(location)
                        break
        
        return locations
    
    def _map_organizations_to_main_org(self, organizations: List[str], main_org_mapping: Dict[str, str]) -> List[str]:
        """
        Map organization names to their main organizations.
        
        Args:
            organizations: List of organization names
            main_org_mapping: Dictionary mapping organizations to main organizations
            
        Returns:
            List of mapped main organizations
        """
        main_orgs = []
        
        for org in organizations:
            cleaned_org = self._clean_organization_name(org)
            
            # Try exact match first
            if cleaned_org in main_org_mapping:
                main_org = main_org_mapping[cleaned_org]
                if main_org.lower() != 'n/a' and main_org != '':
                    main_orgs.append(main_org)
                continue
            
            # Try partial matching for common variations
            for mapped_org, main_org in main_org_mapping.items():
                if (cleaned_org.lower() in mapped_org.lower() or 
                    mapped_org.lower() in cleaned_org.lower()):
                    if main_org.lower() != 'n/a' and main_org != '':
                        main_orgs.append(main_org)
                        break
        
        return main_orgs
    
    def _load_organization_type_mapping(self, csv_file: str = "ai_orgs.csv", include_na: bool = False) -> Dict[str, str]:
        """
        Load organization to type mapping from CSV file.
        
        Args:
            csv_file: Path to the CSV file containing organization mappings
            include_na: If True, include N/A organizations; if False, exclude them
            
        Returns:
            Dictionary mapping organization names to their type (ACADEMIA, INDUSTRY, N/A)
        """
        try:
            # Read the CSV file with tab separator since it appears to be tab-delimited
            df = pd.read_csv(csv_file, sep='\t')
            
            # Create mapping dictionary
            org_type_mapping = {}
            
            for _, row in df.iterrows():
                institution = str(row['Instiution']).strip()
                org_type = str(row['Type']).strip()
                
                # Skip entries with empty values
                if org_type == '':
                    continue
                
                # Handle N/A values based on include_na parameter
                if org_type.lower() == 'n/a':
                    if include_na:
                        org_type_mapping[institution] = 'N/A'
                    # If include_na is False, skip these entries
                    continue
                
                org_type_mapping[institution] = org_type
            
            included_text = " (including N/A)" if include_na else " (excluding N/A)"
            print(f" Loaded {len(org_type_mapping)} organization type mappings from {csv_file}{included_text}")
            return org_type_mapping
            
        except Exception as e:
            print(f" Error loading organization type mapping: {e}")
            return {}
    
    def _categorize_dataset_specificity(self, dataset_name: str) -> str:
        """
        Categorize a dataset name by specificity level.
        
        Args:
            dataset_name: The training dataset name to categorize
            
        Returns:
            Category: 'specific', 'vague', or 'generic'
        """
        if pd.isna(dataset_name) or dataset_name in self.default_na_values:
            return 'generic'
        
        dataset_lower = dataset_name.lower().strip()
        
        # Define patterns for different specificity levels
        specific_indicators = [
            # Named datasets (vision)
            'imagenet', 'coco', 'cifar', 'mnist', 'pascal voc', 'open images', 'ade20k',
            'cityscapes', 'kinetics', 'youtube-8m', 'something-something', 'ucf-101',
            'hmdb-51', 'activitynet', 'charades', 'epic-kitchens',
            
            # Named datasets (language)
            'wikitext', 'bookcorpus', 'common crawl', 'openwebtext', 'pile', 'c4',
            'wikipedia', 'books1', 'books3', 'arxiv', 'pubmed', 'stack overflow',
            'reddit', 'news crawl', 'web crawl', 'cc-news', 'realnews',
            
            # Multimodal datasets
            'conceptual captions', 'visual genome', 'flickr30k', 'ms-coco captions',
            'nocaps', 'sbu captions', 'cc3m', 'cc12m',
            
            # Version numbers or years (indicating specific versions)
            'v1', 'v2', 'v3', 'v4', 'v5', '2020', '2021', '2022', '2023', '2024',
            '2019', '2018', '2017', '2016', '2015',
            
            # Institution-specific datasets
            'laion', 'huggingface', 'google', 'microsoft', 'facebook', 'openai',
            'anthropic', 'deepmind'
        ]
        
        vague_indicators = [
            # Generic descriptions without naming
            'web data', 'internet data', 'crawled data', 'scraped data',
            'text corpus', 'image dataset', 'video dataset', 'audio dataset',
            'proprietary data', 'internal dataset', 'private dataset',
            'curated dataset', 'filtered data', 'processed data',
            'large-scale dataset', 'massive dataset', 'custom dataset',
            'self-collected', 'in-house', 'company data'
        ]
        
        generic_indicators = [
            # Very high-level categories
            'books', 'websites', 'articles', 'papers', 'documents', 'images',
            'videos', 'text', 'data', 'corpus', 'collection', 'archive',
            'database', 'repository', 'source', 'content', 'material'
        ]
        
        # Check for specific indicators first (most precise)
        for indicator in specific_indicators:
            if indicator in dataset_lower:
                return 'specific'
        
        # Check for vague indicators
        for indicator in vague_indicators:
            if indicator in dataset_lower:
                return 'vague'
        
        # Check for generic indicators
        for indicator in generic_indicators:
            if indicator in dataset_lower:
                return 'generic'
        
        # If no patterns match, consider it vague (could be custom/unnamed)
        return 'vague'
    
    def _create_dataset_specificity_visualization(self, df: pd.DataFrame, analysis_df: pd.DataFrame, 
                                                target_domains: List[str], figsize: Tuple[int, int]) -> None:
        """
        Create comprehensive visualization for dataset specificity analysis.
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=figsize)
        
        # 1. Specificity ratio comparison (bar chart)
        colors = self._get_colors(len(target_domains), 'primary')
        x_pos = np.arange(len(target_domains))
        
        specificity_ratios = [analysis_df[analysis_df['domain'] == domain]['specificity_ratio'].iloc[0] 
                            for domain in target_domains if not analysis_df[analysis_df['domain'] == domain].empty]
        vagueness_ratios = [analysis_df[analysis_df['domain'] == domain]['vagueness_ratio'].iloc[0] 
                          for domain in target_domains if not analysis_df[analysis_df['domain'] == domain].empty]
        
        width = 0.35
        bars1 = ax1.bar(x_pos - width/2, specificity_ratios, width, label='Specific Datasets', 
                       color=colors[0], alpha=0.8, edgecolor='white', linewidth=0.5)
        bars2 = ax1.bar(x_pos + width/2, vagueness_ratios, width, label='Vague Datasets', 
                       color=colors[1], alpha=0.8, edgecolor='white', linewidth=0.5)
        
        ax1.set_xlabel('Domain')
        ax1.set_ylabel('Proportion of Papers')
        ax1.set_title('Dataset Specificity by Domain', fontsize=self.title_fontsize, fontweight='bold')
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(target_domains)
        ax1.legend()
        self._apply_chart_style(ax1, 'bar')
        
        # Add value labels
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                   f'{height:.2f}', ha='center', va='bottom', fontsize=14)
        for bar in bars2:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                   f'{height:.2f}', ha='center', va='bottom', fontsize=14)
        
        # 2. Stacked bar chart showing all categories
        specific_counts = [analysis_df[analysis_df['domain'] == domain]['specific_papers'].iloc[0] 
                         for domain in target_domains if not analysis_df[analysis_df['domain'] == domain].empty]
        vague_counts = [analysis_df[analysis_df['domain'] == domain]['vague_papers'].iloc[0] 
                       for domain in target_domains if not analysis_df[analysis_df['domain'] == domain].empty]
        generic_counts = [analysis_df[analysis_df['domain'] == domain]['generic_papers'].iloc[0] 
                        for domain in target_domains if not analysis_df[analysis_df['domain'] == domain].empty]
        
        ax2.bar(target_domains, specific_counts, label='Specific', color=colors[0], alpha=0.8)
        ax2.bar(target_domains, vague_counts, bottom=specific_counts, label='Vague', color=colors[1], alpha=0.8)
        ax2.bar(target_domains, generic_counts, 
               bottom=[s+v for s,v in zip(specific_counts, vague_counts)], 
               label='Generic', color=colors[2] if len(colors) > 2 else '#cccccc', alpha=0.8)
        
        ax2.set_xlabel('Domain')
        ax2.set_ylabel('Number of Papers')
        ax2.set_title('Dataset Specificity Distribution', fontsize=self.title_fontsize, fontweight='bold')
        ax2.legend()
        self._apply_chart_style(ax2, 'bar')
        
        # 3. Unique datasets per domain
        unique_datasets = [analysis_df[analysis_df['domain'] == domain]['unique_datasets'].iloc[0] 
                         for domain in target_domains if not analysis_df[analysis_df['domain'] == domain].empty]
        
        bars3 = ax3.bar(target_domains, unique_datasets, color=colors[0], alpha=0.8, 
                       edgecolor='white', linewidth=0.5)
        ax3.set_xlabel('Domain')
        ax3.set_ylabel('Number of Unique Datasets')
        ax3.set_title('Dataset Diversity by Domain', fontsize=self.title_fontsize, fontweight='bold')
        self._apply_chart_style(ax3, 'bar')
        
        # Add value labels
        for bar in bars3:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                   f'{int(height)}', ha='center', va='bottom', fontsize=14)
        
        # 4. Papers per dataset ratio
        avg_papers_per_dataset = [analysis_df[analysis_df['domain'] == domain]['avg_papers_per_dataset'].iloc[0] 
                                for domain in target_domains if not analysis_df[analysis_df['domain'] == domain].empty]
        
        bars4 = ax4.bar(target_domains, avg_papers_per_dataset, color=colors[1], alpha=0.8, 
                       edgecolor='white', linewidth=0.5)
        ax4.set_xlabel('Domain')
        ax4.set_ylabel('Average Papers per Dataset')
        ax4.set_title('Dataset Reuse Frequency', fontsize=self.title_fontsize, fontweight='bold')
        self._apply_chart_style(ax4, 'bar')
        
        # Add value labels
        for bar in bars4:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{height:.1f}', ha='center', va='bottom', fontsize=14)
        
        plt.tight_layout()
        plt.show()
    
    def _print_dataset_specificity_analysis(self, df: pd.DataFrame, analysis_df: pd.DataFrame, 
                                           target_domains: List[str]) -> None:
        """
        Print detailed analysis results for dataset specificity.
        """
        print(f" Dataset Specificity Analysis:")
        print(f"  • Domains compared: {', '.join(target_domains)}")
        print(f"  • Total domain-dataset combinations: {len(df)}")
        
        for domain in target_domains:
            domain_stats = analysis_df[analysis_df['domain'] == domain]
            if domain_stats.empty:
                continue
                
            stats = domain_stats.iloc[0]
            print(f"\n {domain.title()} Domain:")
            print(f"  • Total papers: {stats['total_papers']}")
            print(f"  • Unique datasets: {stats['unique_datasets']}")
            print(f"  • Avg papers per dataset: {stats['avg_papers_per_dataset']:.1f}")
            print(f"  • Specific datasets: {stats['specific_papers']} papers ({stats['specificity_ratio']:.1%})")
            print(f"  • Vague datasets: {stats['vague_papers']} papers ({stats['vagueness_ratio']:.1%})")
            print(f"  • Generic datasets: {stats['generic_papers']} papers ({stats['generic_ratio']:.1%})")
        
        # Compare domains
        if len(target_domains) == 2:
            domain1, domain2 = target_domains
            stats1 = analysis_df[analysis_df['domain'] == domain1].iloc[0]
            stats2 = analysis_df[analysis_df['domain'] == domain2].iloc[0]
            
            specificity_diff = stats2['specificity_ratio'] - stats1['specificity_ratio']
            vagueness_diff = stats2['vagueness_ratio'] - stats1['vagueness_ratio']
            
            print(f"\n Comparison ({domain2} vs {domain1}):")
            print(f"  • Specificity difference: {specificity_diff:+.1%}")
            print(f"  • Vagueness difference: {vagueness_diff:+.1%}")
            
            if specificity_diff > 0.1:
                print(f"  •  {domain2} is significantly more specific about datasets")
            elif specificity_diff < -0.1:
                print(f"  •  {domain1} is significantly more specific about datasets")
            else:
                print(f"  • ️ Both domains have similar dataset specificity levels")
        
        # Show example datasets by category
        print(f"\n Example Datasets by Specificity:")
        for domain in target_domains:
            domain_data = df[df['domain'] == domain]
            if domain_data.empty:
                continue
                
            print(f"\n{domain.title()} Domain Examples:")
            
            for category in ['specific', 'vague', 'generic']:
                category_data = domain_data[domain_data['specificity_category'] == category]
                if not category_data.empty:
                    top_datasets = category_data.nlargest(3, 'paper_count')['training_dataset'].tolist()
                    print(f"  • {category.title()}: {', '.join(top_datasets[:3])}")

    def _map_organizations_to_type(self, organizations: List[str], org_type_mapping: Dict[str, str], include_na: bool = False) -> List[str]:
        """
        Map organization names to their types.
        
        Args:
            organizations: List of organization names
            org_type_mapping: Dictionary mapping organizations to types
            include_na: If True, include N/A types; if False, exclude them
            
        Returns:
            List of mapped organization types
        """
        org_types = []
        valid_types = ['ACADEMIA', 'INDUSTRY']
        if include_na:
            valid_types.append('N/A')
        
        for org in organizations:
            cleaned_org = self._clean_organization_name(org)
            
            # Try exact match first
            if cleaned_org in org_type_mapping:
                org_type = org_type_mapping[cleaned_org]
                if org_type.upper() in valid_types:
                    org_types.append(org_type.upper())
                continue
            
            # Try partial matching for common variations
            for mapped_org, org_type in org_type_mapping.items():
                if (cleaned_org.lower() in mapped_org.lower() or 
                    mapped_org.lower() in cleaned_org.lower()):
                    if org_type.upper() in valid_types:
                        org_types.append(org_type.upper())
                        break
        
        return org_types
    
    def _create_stacked_percentage_chart(self, df: pd.DataFrame, category_column: str, 
                                       value_column: str, title: str, figsize: Tuple[int, int],
                                       top_k: int = 10, palette_type: str = 'primary') -> None:
        """
        Create a stacked percentage chart showing trends over time.
        
        Args:
            df: DataFrame with temporal data
            category_column: Name of the category column
            value_column: Name of the value column
            title: Chart title
            figsize: Figure size
            top_k: Number of top categories to show
            palette_type: Color palette type
        """
        # Get top K categories overall
        category_totals = df.groupby(category_column)[value_column].sum().sort_values(ascending=False)
        top_categories = category_totals.head(top_k).index.tolist()
        
        # Filter to top categories
        df_top = df[df[category_column].isin(top_categories)]
        
        # Calculate percentages by year
        yearly_totals = df_top.groupby('year')[value_column].sum()
        df_top = df_top.copy()  # Avoid SettingWithCopyWarning
        df_top['percentage'] = df_top.apply(
            lambda row: (row[value_column] / yearly_totals[row['year']]) * 100, axis=1
        )
        
        # Pivot for stacked chart
        df_pivot = df_top.pivot(index='year', columns=category_column, values='percentage').fillna(0)
        
        # Sort data for better stacked chart visualization (largest at bottom)
        df_pivot = self._sort_stacked_chart_data(df_pivot)
        
        # Create stacked bar chart
        fig, ax = plt.subplots(figsize=figsize)
        colors = self._get_colors(len(df_pivot.columns), palette_type)
        df_pivot.plot(kind='bar', stacked=True, ax=ax, color=colors, alpha=0.8)
        
        ax.set_xlabel('Year')
        ax.set_ylabel('Percentage (%)')
        ax.set_title(title, fontsize=self.title_fontsize, fontweight='bold')
        ax.legend(title=category_column.replace('_', ' ').title(), loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=min(len(df[category_column].unique()), 6), fontsize=16, title_fontsize=18)
        self._apply_chart_style(ax, 'bar')
        
        # Format year labels to show only year
        self._format_year_labels(ax, rotation=45)
        plt.subplots_adjust(bottom=0.3)  # Extra space for bottom legend with larger fonts
        plt.show()
    
    def _create_histogram_chart(self, df: pd.DataFrame, category_column: str, 
                              value_column: str, title: str, figsize: Tuple[int, int],
                              top_k: int = 20, palette_type: str = 'primary', 
                              horizontal: bool = True) -> None:
        """
        Create a histogram chart showing category counts.
        
        Args:
            df: DataFrame with category data
            category_column: Name of the category column
            value_column: Name of the value column
            title: Chart title
            figsize: Figure size
            top_k: Number of top categories to show
            palette_type: Color palette type
            horizontal: Whether to create horizontal bar chart
        """
        # Take top K for visualization
        df_top = df.head(top_k)
        
        # Create histogram
        fig, ax = plt.subplots(figsize=figsize)
        colors = self._get_colors(1, palette_type)
        
        if horizontal:
            bars = ax.barh(df_top[category_column], df_top[value_column], 
                          color=colors[0], edgecolor='white', linewidth=0.5, alpha=0.8)
            ax.set_xlabel('Count')
            ax.set_ylabel(category_column.replace('_', ' ').title())
            # Invert y-axis to show highest values at top
            ax.invert_yaxis()
            # Increase font size for y-axis labels (dataset names)
            ax.tick_params(axis='y', labelsize=20)
        else:
            bars = ax.bar(df_top[category_column], df_top[value_column], 
                         color=colors[0], edgecolor='white', linewidth=0.5, alpha=0.8)
            ax.set_xlabel(category_column.replace('_', ' ').title())
            ax.set_ylabel('Count')
            # Rotate x-axis labels and increase font size
            plt.xticks(rotation=45, ha='right', fontsize=20)
        
        #ax.set_title(title, fontsize=self.title_fontsize, fontweight='bold')
        self._apply_chart_style(ax, 'bar')
        
        # Add value labels on bars
        for bar in bars:
            if horizontal:
                width = bar.get_width()
                ax.text(width + 0.1, bar.get_y() + bar.get_height()/2.,
                       f'{int(width)}', ha='left', va='center', fontsize=24)
            else:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       f'{int(height)}', ha='center', va='bottom', fontsize=20)
        
        plt.tight_layout()
        plt.show()
    
    def _create_pie_chart(self, df: pd.DataFrame, category_column: str, 
                         value_column: str, title: str, figsize: Tuple[int, int],
                         palette_type: str = 'primary') -> None:
        """
        Create a pie chart showing category distribution.
        
        Args:
            df: DataFrame with category data
            category_column: Name of the category column
            value_column: Name of the value column
            title: Chart title
            figsize: Figure size
            palette_type: Color palette type
        """
        fig, ax = plt.subplots(figsize=figsize)
        colors = self._get_colors(len(df), palette_type)
        
        wedges, texts, autotexts = ax.pie(df[value_column], labels=df[category_column], 
                                        autopct='%1.1f%%', colors=colors, startangle=90, 
                                        textprops={'fontsize': 10})
        
        # Enhance text
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        #ax.set_title(title, fontsize=self.title_fontsize)
        self._apply_chart_style(ax, 'pie')
        
        # Add legend with counts
        legend_labels = [f'{row[category_column]}: {row[value_column]}' for _, row in df.iterrows()]
        ax.legend(wedges, legend_labels, title=category_column.replace('_', ' ').title(), 
                 loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        
        plt.tight_layout()
        plt.show()
    
    def get_country_distribution_analysis(self,
                                        run_id_start: Optional[int] = None,
                                        run_id_end: Optional[int] = None,
                                        csv_file: str = "ai_orgs.csv",
                                        top_k: int = 10,
                                        figsize: Tuple[int, int] = (15, 10)) -> pd.DataFrame:
        """
        Analyze country distribution of organizations over time with stacked bar chart.
        
        Args:
            run_id_start: Starting extraction run ID (inclusive)
            run_id_end: Ending extraction run ID (inclusive)
            csv_file: Path to CSV file with organization mappings
            top_k: Number of top countries to show
            figsize: Figure size for the plot
        
        Returns:
            DataFrame with country distribution by year
        """
        conn = None
        try:
            # Load organization mapping
            org_mapping = self._load_organization_mapping(csv_file)
            if not org_mapping:
                print(" No organization mapping loaded")
                return pd.DataFrame()
            
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get organization data by year
            query = """
            SELECT 
                DATE_TRUNC('year', p.published_date) as year,
                ef.value as organization,
                COUNT(DISTINCT p.id) as publication_count
            FROM papers p
            JOIN extraction_runs er ON p.id = er.paper_id
            JOIN extracted_fields ef ON er.id = ef.run_id
            WHERE ef.field_name = 'organization'
            AND p.published_date IS NOT NULL
            AND p.published_date >= '2013-01-01'
            AND p.published_date <= '2024-12-31'
            AND ef.value NOT IN %s
            """
            
            params = [tuple(self.default_na_values)]
            if run_id_start is not None:
                query += " AND ef.run_id >= %s"
                params.append(run_id_start)
            if run_id_end is not None:
                query += " AND ef.run_id <= %s"
                params.append(run_id_end)
            
            query += " GROUP BY year, organization ORDER BY year, publication_count DESC"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if not results:
                print(" No organization data found")
                return pd.DataFrame()
            
            df = pd.DataFrame(results, columns=['year', 'organization', 'publication_count'])
            df['year'] = pd.to_datetime(df['year'])
            
            # Load main organization mapping for better grouping
            main_org_mapping = self._load_main_org_mapping(csv_file)
            
            # Process organizations and map to countries
            country_data = []
            
            for _, row in df.iterrows():
                organizations = self._split_organization_names(row['organization'])
                
                # First map to main organizations, then to countries
                main_orgs = self._map_organizations_to_main_org(organizations, main_org_mapping)
                
                # If no main org mapping found, use original organizations
                if not main_orgs:
                    main_orgs = organizations
                
                # Map main organizations to countries
                countries = self._map_organizations_to_location(main_orgs, org_mapping, 'country')
                
                # Create one entry per country
                for country in countries:
                    country_data.append({
                        'year': row['year'],
                        'country': country,
                        'publication_count': row['publication_count']
                    })
            
            if not country_data:
                print(" No country mappings found")
                return pd.DataFrame()
            
            df_countries = pd.DataFrame(country_data)
            
            # Aggregate by year and country to handle duplicates
            df_countries = df_countries.groupby(['year', 'country'])['publication_count'].sum().reset_index()
            
            # Get top K countries overall
            country_totals = df_countries.groupby('country')['publication_count'].sum().sort_values(ascending=False)
            top_countries = country_totals.head(top_k).index.tolist()
            
            # Filter to top countries
            df_top = df_countries[df_countries['country'].isin(top_countries)]
            
            # Calculate percentages by year
            yearly_totals = df_top.groupby('year')['publication_count'].sum()
            df_top = df_top.copy()  # Avoid SettingWithCopyWarning
            df_top['percentage'] = df_top.apply(
                lambda row: (row['publication_count'] / yearly_totals[row['year']]) * 100, axis=1
            )
            
            # Pivot for stacked chart
            df_pivot = df_top.pivot(index='year', columns='country', values='percentage').fillna(0)
            
            # Sort data for better stacked chart visualization (largest at bottom)
            df_pivot = self._sort_stacked_chart_data(df_pivot)
            
            # Create stacked bar chart
            fig, ax = plt.subplots(figsize=figsize)
            colors = self._get_colors(len(df_pivot.columns), 'primary')
            df_pivot.plot(kind='bar', stacked=True, ax=ax, color=colors, alpha=0.8)
            
            ax.set_xlabel('Year')
            ax.set_ylabel('Percentage of Publications (%)')
            ax.set_title(f'Country Distribution of Organizations Over Time\n(Top {top_k} Countries)', fontsize=self.title_fontsize, fontweight='bold')
            ax.legend(title='Country', loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=min(len(df_pivot.columns), 6))
            self._apply_chart_style(ax, 'bar')
            
            # Format year labels to show only year
            self._format_year_labels(ax, rotation=45)
            plt.subplots_adjust(bottom=0.3)  # Extra space for bottom legend with larger fonts
            plt.show()
            
            print(f" Country Distribution Analysis:")
            print(f"  • Top {top_k} countries analyzed")
            print(f"  • Date range: {df['year'].min()} to {df['year'].max()}")
            print(f"  • Total countries mapped: {len(country_totals)}")
            print(f"\nTop countries by total publications:")
            for i, (country, count) in enumerate(country_totals.head(top_k).items(), 1):
                print(f"  {i:2d}. {country}: {count} publications")
            
            return df_pivot
            
        except Exception as e:
            print(f" Error analyzing country distribution: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()
    
    def get_region_distribution_analysis(self,
                                       run_id_start: Optional[int] = None,
                                       run_id_end: Optional[int] = None,
                                       csv_file: str = "ai_orgs.csv",
                                       figsize: Tuple[int, int] = (15, 10)) -> pd.DataFrame:
        """
        Analyze region distribution of organizations over time with stacked bar chart.
        
        Args:
            run_id_start: Starting extraction run ID (inclusive)
            run_id_end: Ending extraction run ID (inclusive)
            csv_file: Path to CSV file with organization mappings
            figsize: Figure size for the plot
        
        Returns:
            DataFrame with region distribution by year
        """
        conn = None
        try:
            # Load organization mapping
            org_mapping = self._load_organization_mapping(csv_file)
            if not org_mapping:
                print(" No organization mapping loaded")
                return pd.DataFrame()
            
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get organization data by year
            query = """
            SELECT 
                DATE_TRUNC('year', p.published_date) as year,
                ef.value as organization,
                COUNT(DISTINCT p.id) as publication_count
            FROM papers p
            JOIN extraction_runs er ON p.id = er.paper_id
            JOIN extracted_fields ef ON er.id = ef.run_id
            WHERE ef.field_name = 'organization'
            AND p.published_date IS NOT NULL
            AND p.published_date >= '2013-01-01'
            AND p.published_date <= '2024-12-31'
            AND ef.value NOT IN %s
            """
            
            params = [tuple(self.default_na_values)]
            if run_id_start is not None:
                query += " AND ef.run_id >= %s"
                params.append(run_id_start)
            if run_id_end is not None:
                query += " AND ef.run_id <= %s"
                params.append(run_id_end)
            
            query += " GROUP BY year, organization ORDER BY year, publication_count DESC"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if not results:
                print(" No organization data found")
                return pd.DataFrame()
            
            df = pd.DataFrame(results, columns=['year', 'organization', 'publication_count'])
            df['year'] = pd.to_datetime(df['year'])
            
            # Load main organization mapping for better grouping
            main_org_mapping = self._load_main_org_mapping(csv_file)
            
            # Process organizations and map to regions
            region_data = []
            
            for _, row in df.iterrows():
                organizations = self._split_organization_names(row['organization'])
                
                # First map to main organizations, then to regions
                main_orgs = self._map_organizations_to_main_org(organizations, main_org_mapping)
                
                # If no main org mapping found, use original organizations
                if not main_orgs:
                    main_orgs = organizations
                
                # Map main organizations to regions
                regions = self._map_organizations_to_location(main_orgs, org_mapping, 'region')
                
                # Create one entry per region
                for region in regions:
                    region_data.append({
                        'year': row['year'],
                        'region': region,
                        'publication_count': row['publication_count']
                    })
            
            if not region_data:
                print(" No region mappings found")
                return pd.DataFrame()
            
            df_regions = pd.DataFrame(region_data)
            
            # Aggregate by year and region to handle duplicates
            df_regions = df_regions.groupby(['year', 'region'])['publication_count'].sum().reset_index()
            
            # Get all regions (usually fewer than countries)
            region_totals = df_regions.groupby('region')['publication_count'].sum().sort_values(ascending=False)
            
            # Calculate percentages by year
            yearly_totals = df_regions.groupby('year')['publication_count'].sum()
            df_regions = df_regions.copy()  # Avoid SettingWithCopyWarning
            df_regions['percentage'] = df_regions.apply(
                lambda row: (row['publication_count'] / yearly_totals[row['year']]) * 100, axis=1
            )
            
            # Pivot for stacked chart
            df_pivot = df_regions.pivot(index='year', columns='region', values='percentage').fillna(0)
            
            # Sort data for better stacked chart visualization (largest at bottom)
            df_pivot = self._sort_stacked_chart_data(df_pivot)
            
            # Create stacked bar chart
            fig, ax = plt.subplots(figsize=figsize)
            colors = self._get_colors(len(df_pivot.columns), 'primary')
            df_pivot.plot(kind='bar', stacked=True, ax=ax, color=colors, alpha=0.8)
            
            ax.set_xlabel('Year')
            ax.set_ylabel('Percentage of Publications (%)')
            ax.set_title('Region Distribution of Organizations Over Time', fontsize=self.title_fontsize, fontweight='bold')
            ax.legend(title='Region', loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=min(len(df_pivot.columns), 6))
            self._apply_chart_style(ax, 'bar')
            
            # Format year labels to show only year
            self._format_year_labels(ax, rotation=45)
            plt.subplots_adjust(bottom=0.3)  # Extra space for bottom legend with larger fonts
            plt.show()
            
            print(f" Region Distribution Analysis:")
            print(f"  • Total regions: {len(region_totals)}")
            print(f"  • Date range: {df['year'].min()} to {df['year'].max()}")
            print(f"\nRegions by total publications:")
            for i, (region, count) in enumerate(region_totals.items(), 1):
                print(f"  {i:2d}. {region}: {count} publications")
            
            return df_pivot
            
        except Exception as e:
            print(f" Error analyzing region distribution: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()
    
    def get_papers_vs_models_by_year(self,
                                   run_id_start: Optional[int] = None,
                                   run_id_end: Optional[int] = None,
                                   figsize: Tuple[int, int] = (14, 10)) -> pd.DataFrame:
        """
        Analyze the number of papers and total number of models (extraction runs) for each year side by side.
        
        Args:
            run_id_start: Starting extraction run ID (inclusive)
            run_id_end: Ending extraction run ID (inclusive)
            figsize: Figure size for the plot
        
        Returns:
            DataFrame with papers and models count by year
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get papers and models count by year
            # Models are counted by distinct combinations of run_id and model_instance_id
            query = """
            SELECT 
                DATE_TRUNC('year', p.published_date) as year,
                COUNT(DISTINCT p.id) as paper_count,
                COUNT(DISTINCT CONCAT(er.id, '_', ef.model_instance_id)) as model_count
            FROM papers p
            JOIN extraction_runs er ON p.id = er.paper_id
            JOIN extracted_fields ef ON er.id = ef.run_id
            WHERE p.published_date IS NOT NULL
            """
            
            params = []
            if run_id_start is not None:
                query += " AND er.id >= %s"
                params.append(run_id_start)
            if run_id_end is not None:
                query += " AND er.id <= %s"
                params.append(run_id_end)
            
            query += " GROUP BY DATE_TRUNC('year', p.published_date) ORDER BY year"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if not results:
                print(" No papers and models data found")
                return pd.DataFrame()
            
            df = pd.DataFrame(results, columns=['year', 'paper_count', 'model_count'])
            df['year'] = pd.to_datetime(df['year'])
            
            # Create side-by-side bar chart
            fig, ax = plt.subplots(figsize=figsize)
            
            # Extract years for x-axis
            years = [year.year for year in df['year']]
            x_pos = np.arange(len(years))
            width = 0.35  # Width of bars
            
            # Get colors for the bars
            colors = self._get_colors(2, 'primary')
            
            # Create bars
            bars1 = ax.bar(x_pos - width/2, df['paper_count'], width, 
                          label='Papers', color=colors[0], alpha=0.8, 
                          edgecolor='white', linewidth=0.5)
            bars2 = ax.bar(x_pos + width/2, df['model_count'], width, 
                          label='Models', color=colors[1], alpha=0.8, 
                          edgecolor='white', linewidth=0.5)
            
            # Customize the chart
            ax.set_xlabel('Year', fontsize=20)
            ax.set_ylabel('Count', fontsize=20)
            #ax.set_title('Papers vs Models by Year', fontsize=self.title_fontsize, fontweight='bold')
            ax.set_xticks(x_pos)
            ax.set_xticklabels(years, rotation=45)
            ax.legend(fontsize=18)
            self._apply_chart_style(ax, 'bar')
            
            # Add value labels on bars
            for bar in bars1:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                       f'{int(height)}', ha='center', va='bottom', fontsize=14)
            
            for bar in bars2:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                       f'{int(height)}', ha='center', va='bottom', fontsize=14)
            
            plt.tight_layout()
            plt.show()
            
            # Print statistics
            print(f" Papers vs Models Analysis:")
            print(f"  • Total papers: {df['paper_count'].sum()}")
            print(f"  • Total models: {df['model_count'].sum()}")
            print(f"  • Date range: {df['year'].min().year} to {df['year'].max().year}")
            print(f"  • Average models per paper: {df['model_count'].sum() / df['paper_count'].sum():.1f}")
            
            # Print year-by-year breakdown
            print(f"\nYear-by-year breakdown:")
            print(f"{'Year':<6} {'Papers':<8} {'Models':<8} {'Models/Paper':<12}")
            print("-" * 36)
            for _, row in df.iterrows():
                ratio = row['model_count'] / row['paper_count'] if row['paper_count'] > 0 else 0
                print(f"{row['year'].year:<6} {row['paper_count']:<8} {row['model_count']:<8} {ratio:<12.1f}")
            
            return df
            
        except Exception as e:
            print(f" Error analyzing papers vs models by year: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()
    
    def get_dataset_specificity_analysis(self,
                                        run_id_start: Optional[int] = None,
                                        run_id_end: Optional[int] = None,
                                        target_domains: List[str] = ['language', 'vision'],
                                        figsize: Tuple[int, int] = (16, 12)) -> pd.DataFrame:
        """
        Analyze dataset specificity across different domains to investigate whether
        certain domains (e.g., language) tend to be more vague about training datasets
        compared to others (e.g., vision).
        
        Args:
            run_id_start: Starting extraction run ID (inclusive)
            run_id_end: Ending extraction run ID (inclusive)
            target_domains: List of domains to compare (default: ['language', 'vision'])
            figsize: Figure size for the plot
        
        Returns:
            DataFrame with dataset specificity analysis by domain
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get training dataset and domain data together
            query = """
            SELECT 
                ef_domain.value as domain,
                ef_dataset.value as training_dataset,
                COUNT(DISTINCT p.id) as paper_count
            FROM papers p
            JOIN extraction_runs er ON p.id = er.paper_id
            JOIN extracted_fields ef_domain ON er.id = ef_domain.run_id
            JOIN extracted_fields ef_dataset ON er.id = ef_dataset.run_id
            WHERE ef_domain.field_name = 'domain'
            AND ef_dataset.field_name = 'training_dataset'
            AND p.published_date IS NOT NULL
            AND ef_domain.value NOT IN %s
            AND ef_dataset.value NOT IN %s
            """
            
            params = [tuple(self.default_na_values), tuple(self.default_na_values)]
            if run_id_start is not None:
                query += " AND ef_domain.run_id >= %s"
                params.append(run_id_start)
            if run_id_end is not None:
                query += " AND ef_domain.run_id <= %s"
                params.append(run_id_end)
            
            query += " GROUP BY ef_domain.value, ef_dataset.value ORDER BY paper_count DESC"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if not results:
                print(" No domain-dataset data found")
                return pd.DataFrame()
            
            df = pd.DataFrame(results, columns=['domain', 'training_dataset', 'paper_count'])
            
            # Expand array values in both domain and dataset fields
            df_expanded = self._expand_array_data(df, 'domain')
            df_expanded = self._expand_array_data(df_expanded, 'training_dataset')
            df_expanded = df_expanded.groupby(['domain', 'training_dataset'])['paper_count'].sum().reset_index()
            
            # Filter to target domains
            df_filtered = df_expanded[df_expanded['domain'].isin(target_domains)]
            
            if df_filtered.empty:
                print(f" No data found for domains: {target_domains}")
                return pd.DataFrame()
            
            # Categorize dataset specificity
            df_filtered['specificity_category'] = df_filtered['training_dataset'].apply(self._categorize_dataset_specificity)
            
            # Calculate specificity metrics by domain
            domain_analysis = []
            
            for domain in target_domains:
                domain_data = df_filtered[df_filtered['domain'] == domain]
                
                if domain_data.empty:
                    continue
                
                total_papers = domain_data['paper_count'].sum()
                
                # Count by specificity category
                category_counts = domain_data.groupby('specificity_category')['paper_count'].sum()
                
                specific_count = category_counts.get('specific', 0)
                vague_count = category_counts.get('vague', 0)
                generic_count = category_counts.get('generic', 0)
                
                # Calculate metrics
                specificity_ratio = specific_count / total_papers if total_papers > 0 else 0
                vagueness_ratio = vague_count / total_papers if total_papers > 0 else 0
                generic_ratio = generic_count / total_papers if total_papers > 0 else 0
                
                # Count unique datasets
                unique_datasets = domain_data['training_dataset'].nunique()
                avg_papers_per_dataset = total_papers / unique_datasets if unique_datasets > 0 else 0
                
                domain_analysis.append({
                    'domain': domain,
                    'total_papers': total_papers,
                    'unique_datasets': unique_datasets,
                    'avg_papers_per_dataset': avg_papers_per_dataset,
                    'specific_papers': specific_count,
                    'vague_papers': vague_count,
                    'generic_papers': generic_count,
                    'specificity_ratio': specificity_ratio,
                    'vagueness_ratio': vagueness_ratio,
                    'generic_ratio': generic_ratio
                })
            
            analysis_df = pd.DataFrame(domain_analysis)
            
            # Create comprehensive visualization
            self._create_dataset_specificity_visualization(df_filtered, analysis_df, target_domains, figsize)
            
            # Print detailed analysis
            self._print_dataset_specificity_analysis(df_filtered, analysis_df, target_domains)
            
            return df_filtered
            
        except Exception as e:
            print(f" Error analyzing dataset specificity: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()
    
    def get_dataset_specificity_temporal_analysis(self,
                                                run_id_start: Optional[int] = None,
                                                run_id_end: Optional[int] = None,
                                                target_domains: List[str] = ['language', 'vision'],
                                                figsize: Tuple[int, int] = (16, 10)) -> pd.DataFrame:
        """
        Analyze how dataset specificity practices have evolved over time across domains.
        
        Args:
            run_id_start: Starting extraction run ID (inclusive)
            run_id_end: Ending extraction run ID (inclusive)
            target_domains: List of domains to compare (default: ['language', 'vision'])
            figsize: Figure size for the plot
        
        Returns:
            DataFrame with temporal dataset specificity analysis by domain
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get training dataset and domain data together with publication years
            query = """
            SELECT 
                DATE_TRUNC('year', p.published_date) as year,
                ef_domain.value as domain,
                ef_dataset.value as training_dataset,
                COUNT(DISTINCT p.id) as paper_count
            FROM papers p
            JOIN extraction_runs er ON p.id = er.paper_id
            JOIN extracted_fields ef_domain ON er.id = ef_domain.run_id
            JOIN extracted_fields ef_dataset ON er.id = ef_dataset.run_id
            WHERE ef_domain.field_name = 'domain'
            AND ef_dataset.field_name = 'training_dataset'
            AND p.published_date IS NOT NULL
            AND p.published_date >= '2015-01-01'
            AND p.published_date <= '2024-12-31'
            AND ef_domain.value NOT IN %s
            AND ef_dataset.value NOT IN %s
            """
            
            params = [tuple(self.default_na_values), tuple(self.default_na_values)]
            if run_id_start is not None:
                query += " AND ef_domain.run_id >= %s"
                params.append(run_id_start)
            if run_id_end is not None:
                query += " AND ef_domain.run_id <= %s"
                params.append(run_id_end)
            
            query += " GROUP BY year, ef_domain.value, ef_dataset.value ORDER BY year, paper_count DESC"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if not results:
                print(" No temporal domain-dataset data found")
                return pd.DataFrame()
            
            df = pd.DataFrame(results, columns=['year', 'domain', 'training_dataset', 'paper_count'])
            df['year'] = pd.to_datetime(df['year'])
            
            # Expand array values in both domain and dataset fields
            df_expanded = self._expand_array_data(df, 'domain')
            df_expanded = self._expand_array_data(df_expanded, 'training_dataset')
            df_expanded = df_expanded.groupby(['year', 'domain', 'training_dataset'])['paper_count'].sum().reset_index()
            
            # Filter to target domains
            df_filtered = df_expanded[df_expanded['domain'].isin(target_domains)]
            
            if df_filtered.empty:
                print(f" No temporal data found for domains: {target_domains}")
                return pd.DataFrame()
            
            # Categorize dataset specificity
            df_filtered['specificity_category'] = df_filtered['training_dataset'].apply(self._categorize_dataset_specificity)
            
            # Calculate yearly specificity metrics by domain
            yearly_analysis = []
            
            for year in sorted(df_filtered['year'].unique()):
                year_data = df_filtered[df_filtered['year'] == year]
                
                for domain in target_domains:
                    domain_year_data = year_data[year_data['domain'] == domain]
                    
                    if domain_year_data.empty:
                        continue
                    
                    total_papers = domain_year_data['paper_count'].sum()
                    
                    # Count by specificity category
                    category_counts = domain_year_data.groupby('specificity_category')['paper_count'].sum()
                    
                    specific_count = category_counts.get('specific', 0)
                    vague_count = category_counts.get('vague', 0)
                    generic_count = category_counts.get('generic', 0)
                    
                    # Calculate ratios
                    specificity_ratio = specific_count / total_papers if total_papers > 0 else 0
                    vagueness_ratio = vague_count / total_papers if total_papers > 0 else 0
                    generic_ratio = generic_count / total_papers if total_papers > 0 else 0
                    
                    yearly_analysis.append({
                        'year': year,
                        'domain': domain,
                        'total_papers': total_papers,
                        'specific_papers': specific_count,
                        'vague_papers': vague_count,
                        'generic_papers': generic_count,
                        'specificity_ratio': specificity_ratio,
                        'vagueness_ratio': vagueness_ratio,
                        'generic_ratio': generic_ratio
                    })
            
            temporal_df = pd.DataFrame(yearly_analysis)
            
            if temporal_df.empty:
                print(" No temporal analysis data generated")
                return pd.DataFrame()
            
            # Create temporal visualization
            self._create_temporal_specificity_visualization(temporal_df, target_domains, figsize)
            
            # Print temporal analysis
            self._print_temporal_specificity_analysis(temporal_df, target_domains)
            
            return temporal_df
            
        except Exception as e:
            print(f" Error analyzing temporal dataset specificity: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()
    
    def _create_temporal_specificity_visualization(self, df: pd.DataFrame, target_domains: List[str], 
                                                 figsize: Tuple[int, int]) -> None:
        """
        Create temporal visualization for dataset specificity trends.
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True)
        
        colors = self._get_colors(len(target_domains), 'primary')
        years = [year.year for year in sorted(df['year'].unique())]
        
        # 1. Specificity ratio over time
        for i, domain in enumerate(target_domains):
            domain_data = df[df['domain'] == domain].sort_values('year')
            if not domain_data.empty:
                domain_years = [year.year for year in domain_data['year']]
                specificity_ratios = domain_data['specificity_ratio'].tolist()
                
                ax1.plot(domain_years, specificity_ratios, marker='o', linewidth=3, markersize=8,
                        label=f'{domain.title()}', color=colors[i], alpha=0.8)
        
        ax1.set_ylabel('Proportion of Specific Datasets')
        ax1.set_title('Dataset Specificity Trends Over Time', fontsize=self.title_fontsize, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        self._apply_chart_style(ax1, 'line')
        
        # 2. Vagueness ratio over time
        for i, domain in enumerate(target_domains):
            domain_data = df[df['domain'] == domain].sort_values('year')
            if not domain_data.empty:
                domain_years = [year.year for year in domain_data['year']]
                vagueness_ratios = domain_data['vagueness_ratio'].tolist()
                
                ax2.plot(domain_years, vagueness_ratios, marker='s', linewidth=3, markersize=8,
                        label=f'{domain.title()}', color=colors[i], alpha=0.8, linestyle='--')
        
        ax2.set_xlabel('Year')
        ax2.set_ylabel('Proportion of Vague Datasets')
        ax2.set_title('Dataset Vagueness Trends Over Time', fontsize=self.title_fontsize, fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        self._apply_chart_style(ax2, 'line')
        
        # Format x-axis
        ax2.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.show()
    
    def _print_temporal_specificity_analysis(self, df: pd.DataFrame, target_domains: List[str]) -> None:
        """
        Print temporal analysis results for dataset specificity.
        """
        print(f" Temporal Dataset Specificity Analysis:")
        print(f"  • Domains compared: {', '.join(target_domains)}")
        print(f"  • Years analyzed: {df['year'].dt.year.min()} - {df['year'].dt.year.max()}")
        
        # Calculate trends for each domain
        for domain in target_domains:
            domain_data = df[df['domain'] == domain].sort_values('year')
            if len(domain_data) < 2:
                continue
            
            # Calculate trend (simple linear regression slope)
            years_numeric = [(year.year - domain_data['year'].dt.year.min()) for year in domain_data['year']]
            specificity_trend = np.polyfit(years_numeric, domain_data['specificity_ratio'], 1)[0]
            vagueness_trend = np.polyfit(years_numeric, domain_data['vagueness_ratio'], 1)[0]
            
            # Get first and last year values
            first_year_spec = domain_data['specificity_ratio'].iloc[0]
            last_year_spec = domain_data['specificity_ratio'].iloc[-1]
            first_year_vague = domain_data['vagueness_ratio'].iloc[0]
            last_year_vague = domain_data['vagueness_ratio'].iloc[-1]
            
            print(f"\n {domain.title()} Domain Trends:")
            print(f"  • Specificity trend: {specificity_trend:+.3f} per year")
            print(f"  • Specificity change: {first_year_spec:.2%} → {last_year_spec:.2%} ({last_year_spec - first_year_spec:+.1%})")
            print(f"  • Vagueness trend: {vagueness_trend:+.3f} per year")
            print(f"  • Vagueness change: {first_year_vague:.2%} → {last_year_vague:.2%} ({last_year_vague - first_year_vague:+.1%})")
            
            if specificity_trend > 0.01:
                print(f"  •  {domain.title()} is becoming MORE specific over time")
            elif specificity_trend < -0.01:
                print(f"  • ️ {domain.title()} is becoming LESS specific over time")
            else:
                print(f"  • ️ {domain.title()} specificity remains stable over time")
        
        # Compare domains
        if len(target_domains) == 2:
            domain1_data = df[df['domain'] == target_domains[0]].sort_values('year')
            domain2_data = df[df['domain'] == target_domains[1]].sort_values('year')
            
            if not domain1_data.empty and not domain2_data.empty:
                print(f"\n Domain Comparison:")
                
                # Find common years for comparison
                common_years = set(domain1_data['year'].dt.year) & set(domain2_data['year'].dt.year)
                if common_years:
                    latest_year = max(common_years)
                    
                    dom1_latest = domain1_data[domain1_data['year'].dt.year == latest_year]['specificity_ratio'].iloc[0]
                    dom2_latest = domain2_data[domain2_data['year'].dt.year == latest_year]['specificity_ratio'].iloc[0]
                    
                    print(f"  • Latest year ({latest_year}) specificity:")
                    print(f"    - {target_domains[0].title()}: {dom1_latest:.1%}")
                    print(f"    - {target_domains[1].title()}: {dom2_latest:.1%}")
                    print(f"    - Difference: {dom2_latest - dom1_latest:+.1%}")
                    
                    if abs(dom2_latest - dom1_latest) > 0.15:
                        winner = target_domains[1] if dom2_latest > dom1_latest else target_domains[0]
                        print(f"  •  {winner.title()} shows significantly higher dataset specificity")
    
    def get_organization_type_analysis(self,
                                     run_id_start: Optional[int] = None,
                                     run_id_end: Optional[int] = None,
                                     csv_file: str = "ai_orgs.csv",
                                     include_na: bool = False,
                                     visualization_type: str = 'pie',  # 'pie', 'stacked_percentage', or 'both'
                                     figsize: Tuple[int, int] = (15, 10)) -> pd.DataFrame:
        """
        Analyze organization type distribution (academia vs industry) over time.
        
        Args:
            run_id_start: Starting extraction run ID (inclusive)
            run_id_end: Ending extraction run ID (inclusive)
            csv_file: Path to CSV file with organization mappings
            include_na: If True, include N/A organizations in the analysis; if False, ignore them
            visualization_type: 'pie' for pie chart, 'stacked_percentage' for temporal, or 'both' for both
            figsize: Figure size for the plot
        
        Returns:
            DataFrame with organization type distribution
        """
        conn = None
        try:
            # Load organization type mapping
            org_type_mapping = self._load_organization_type_mapping(csv_file, include_na)
            if not org_type_mapping:
                print(" No organization type mapping loaded")
                return pd.DataFrame()
            
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get organization data by year
            query = """
            SELECT 
                DATE_TRUNC('year', p.published_date) as year,
                ef.value as organization,
                COUNT(DISTINCT p.id) as publication_count
            FROM papers p
            JOIN extraction_runs er ON p.id = er.paper_id
            JOIN extracted_fields ef ON er.id = ef.run_id
            WHERE ef.field_name = 'organization'
            AND p.published_date IS NOT NULL
            AND p.published_date >= '2013-01-01'
            AND p.published_date <= '2024-12-31'
            AND ef.value NOT IN %s
            """
            
            params = [tuple(self.default_na_values)]
            if run_id_start is not None:
                query += " AND ef.run_id >= %s"
                params.append(run_id_start)
            if run_id_end is not None:
                query += " AND ef.run_id <= %s"
                params.append(run_id_end)
            
            query += " GROUP BY year, organization ORDER BY year, publication_count DESC"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if not results:
                print(" No organization data found")
                return pd.DataFrame()
            
            df = pd.DataFrame(results, columns=['year', 'organization', 'publication_count'])
            df['year'] = pd.to_datetime(df['year'])
            
            # Load main organization mapping for better grouping
            main_org_mapping = self._load_main_org_mapping(csv_file)
            
            # Process organizations and map to types
            type_data = []
            
            for _, row in df.iterrows():
                organizations = self._split_organization_names(row['organization'])
                
                # First map to main organizations, then to types
                main_orgs = self._map_organizations_to_main_org(organizations, main_org_mapping)
                
                # If no main org mapping found, use original organizations
                if not main_orgs:
                    main_orgs = organizations
                
                # Map main organizations to types
                org_types = self._map_organizations_to_type(main_orgs, org_type_mapping, include_na)
                
                # Create one entry per organization type
                valid_types = ['ACADEMIA', 'INDUSTRY']
                if include_na:
                    valid_types.append('N/A')
                
                for org_type in org_types:
                    if org_type in valid_types:
                        type_data.append({
                            'year': row['year'],
                            'organization_type': org_type,
                            'publication_count': row['publication_count']
                        })
            
            if not type_data:
                print(" No organization type mappings found")
                return pd.DataFrame()
            
            df_types = pd.DataFrame(type_data)
            
            # Aggregate by year and organization type to handle duplicates
            df_types = df_types.groupby(['year', 'organization_type'])['publication_count'].sum().reset_index()
            
            # Create visualizations based on type
            if visualization_type == 'both':
                # Create both pie chart and temporal analysis
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
                
                # Pie chart for overall distribution
                overall_totals = df_types.groupby('organization_type')['publication_count'].sum()
                # Use colors based on number of categories
                n_categories = len(overall_totals)
                colors = self._get_colors(n_categories, 'primary')
                wedges, texts, autotexts = ax1.pie(overall_totals.values, labels=overall_totals.index, 
                                                 autopct='%1.1f%%', colors=colors, startangle=90,
                                                 textprops={'fontsize': 14})
                
                # Enhance pie chart text
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
                    autotext.set_fontsize(16)
                
                #ax1.set_title('Overall Organization Type Distribution', fontsize=18, fontweight='bold')
                
                # Stacked percentage chart for temporal analysis
                yearly_totals = df_types.groupby('year')['publication_count'].sum()
                df_types_copy = df_types.copy()
                df_types_copy['percentage'] = df_types_copy.apply(
                    lambda row: (row['publication_count'] / yearly_totals[row['year']]) * 100, axis=1
                )
                
                df_pivot = df_types_copy.pivot(index='year', columns='organization_type', values='percentage').fillna(0)
                n_categories = len(df_pivot.columns)
                colors = self._get_colors(n_categories, 'primary')
                df_pivot.plot(kind='bar', stacked=True, ax=ax2, color=colors, alpha=0.8)
                
                ax2.set_xlabel('Year')
                ax2.set_ylabel('Percentage (%)')
               # ax2.set_title('Organization Type Distribution Over Time', fontsize=18, fontweight='bold')
                ax2.legend(title='Organization Type')
                self._apply_chart_style(ax2, 'bar')
                
                # Format year labels
                self._format_year_labels(ax2, rotation=45)
                
                plt.tight_layout()
                plt.show()
                
            elif visualization_type == 'stacked_percentage':
                # Temporal stacked percentage chart only
                yearly_totals = df_types.groupby('year')['publication_count'].sum()
                df_types_copy = df_types.copy()
                df_types_copy['percentage'] = df_types_copy.apply(
                    lambda row: (row['publication_count'] / yearly_totals[row['year']]) * 100, axis=1
                )
                
                df_pivot = df_types_copy.pivot(index='year', columns='organization_type', values='percentage').fillna(0)
                
                fig, ax = plt.subplots(figsize=figsize)
                n_categories = len(df_pivot.columns)
                colors = self._get_colors(n_categories, 'primary')
                df_pivot.plot(kind='bar', stacked=True, ax=ax, color=colors, alpha=0.8)
                
                ax.set_xlabel('Year')
                ax.set_ylabel('Percentage (%)')
                #ax.set_title('Organization Type Distribution Over Time (Percentage)', fontsize=self.title_fontsize, fontweight='bold')
                ax.legend(title='Organization Type', loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2)
                self._apply_chart_style(ax, 'bar')
                
                # Format year labels
                self._format_year_labels(ax, rotation=45)
                plt.subplots_adjust(bottom=0.2)
                plt.show()
                
            else:  # default 'pie'
                # Pie chart only
                overall_totals = df_types.groupby('organization_type')['publication_count'].sum()
                
                fig, ax = plt.subplots(figsize=(10, 8))
                n_categories = len(overall_totals)
                colors = self._get_colors(n_categories, 'primary')
                wedges, texts, autotexts = ax.pie(overall_totals.values, labels=overall_totals.index, 
                                                 autopct='%1.1f%%', colors=colors, startangle=90,
                                                 textprops={'fontsize': 16})
                
                # Enhance text
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
                    autotext.set_fontsize(18)
                
                #ax.set_title('Organization Type Distribution\n(Academia vs Industry)', fontsize=self.title_fontsize, fontweight='bold')
                self._apply_chart_style(ax, 'pie')
                
                # Add legend with counts
                legend_labels = [f'{org_type}: {count} papers' for org_type, count in overall_totals.items()]
                ax.legend(wedges, legend_labels, title='Organization Type', 
                         loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
                
                plt.tight_layout()
                plt.show()
            
            # Print summary statistics
            print(f" Organization Type Analysis:")
            overall_totals = df_types.groupby('organization_type')['publication_count'].sum()
            total_papers = overall_totals.sum()
            
            print(f"  • Total papers analyzed: {total_papers}")
            print(f"  • Date range: {df['year'].min()} to {df['year'].max()}")
            
            print(f"\nOrganization type distribution:")
            for org_type, count in overall_totals.items():
                percentage = (count / total_papers) * 100
                print(f"  • {org_type}: {count} papers ({percentage:.1f}%)")
            
            # Calculate trend over time
            if len(df_types['year'].unique()) > 1:
                print(f"\nTrend analysis:")
                yearly_percentages = df_types.groupby(['year', 'organization_type'])['publication_count'].sum().unstack(fill_value=0)
                yearly_percentages = yearly_percentages.div(yearly_percentages.sum(axis=1), axis=0) * 100
                
                if 'ACADEMIA' in yearly_percentages.columns:
                    first_year_academia = yearly_percentages['ACADEMIA'].iloc[0]
                    last_year_academia = yearly_percentages['ACADEMIA'].iloc[-1]
                    academia_change = last_year_academia - first_year_academia
                    print(f"  • Academia percentage change: {academia_change:+.1f}% points")
                
                if 'INDUSTRY' in yearly_percentages.columns:
                    first_year_industry = yearly_percentages['INDUSTRY'].iloc[0]
                    last_year_industry = yearly_percentages['INDUSTRY'].iloc[-1]
                    industry_change = last_year_industry - first_year_industry
                    print(f"  • Industry percentage change: {industry_change:+.1f}% points")
            
            return df_types
            
        except Exception as e:
            print(f" Error analyzing organization type distribution: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()


# Utility functions for cross-domain analysis
def create_domain_modality_matrix(domain_analyzer: DomainAnalyzer,
                                run_id_start: Optional[int] = None,
                                run_id_end: Optional[int] = None,
                                modality_type: str = 'input',
                                top_k_domains: int = 10,
                                top_k_modalities: int = 10,
                                figsize: Tuple[int, int] = (12, 10)) -> pd.DataFrame:
    """
    Create a matrix showing domain-modality relationships.
    
    Args:
        domain_analyzer: DomainAnalyzer instance
        run_id_start: Starting extraction run ID (inclusive)
        run_id_end: Ending extraction run ID (inclusive)
        modality_type: 'input' or 'output' modality
        top_k_domains: Number of top domains to include
        top_k_modalities: Number of top modalities to include
        figsize: Figure size for the plot
    
    Returns:
        DataFrame with domain-modality matrix
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        field_name = f'{modality_type}_modality'
        
        # Get domain-modality relationships
        query = f"""
        SELECT 
            ef_domain.value as domain,
            ef_modality.value as modality,
            COUNT(DISTINCT p.id) as count
        FROM papers p
        JOIN extraction_runs er ON p.id = er.paper_id
        JOIN extracted_fields ef_domain ON er.id = ef_domain.run_id
        JOIN extracted_fields ef_modality ON er.id = ef_modality.run_id
        WHERE ef_domain.field_name = 'domain'
        AND ef_modality.field_name = '{field_name}'
        AND p.published_date IS NOT NULL
        AND ef_domain.value NOT IN %s
        AND ef_modality.value NOT IN %s
        """
        
        params = [tuple(domain_analyzer.default_na_values), tuple(domain_analyzer.default_na_values)]
        if run_id_start is not None:
            query += " AND ef_domain.run_id >= %s"
            params.append(run_id_start)
        if run_id_end is not None:
            query += " AND ef_domain.run_id <= %s"
            params.append(run_id_end)
        
        query += " GROUP BY domain, modality ORDER BY count DESC"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        if not results:
            print(f" No domain-{modality_type} modality data found")
            return pd.DataFrame()
        
        df = pd.DataFrame(results, columns=['domain', 'modality', 'count'])
        
        # Expand array values in both domain and modality fields
        df_expanded = domain_analyzer._expand_array_data(df, 'domain')
        df_expanded = domain_analyzer._expand_array_data(df_expanded, 'modality')
        
        # Recalculate counts after expansion
        df_expanded = df_expanded.groupby(['domain', 'modality'])['count'].sum().reset_index()
        
        # Get top K domains and modalities
        top_domains = df_expanded.groupby('domain')['count'].sum().nlargest(top_k_domains).index.tolist()
        top_modalities = df_expanded.groupby('modality')['count'].sum().nlargest(top_k_modalities).index.tolist()
        
        # Filter to top K values
        df_filtered = df_expanded[
            (df_expanded['domain'].isin(top_domains)) & 
            (df_expanded['modality'].isin(top_modalities))
        ]
        
        # Create pivot table
        matrix = df_filtered.pivot(index='domain', columns='modality', values='count').fillna(0)
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=figsize)
        sns.heatmap(matrix, annot=True, fmt='.0f', cmap=domain_analyzer.heatmap_palette, ax=ax, 
                   cbar_kws={'label': 'Count'})
        ax.set_title(f'Domain-{modality_type.title()} Modality Matrix\n(Top {top_k_domains} Domains × Top {top_k_modalities} Modalities)', fontsize=self.title_fontsize, fontweight='bold')
        ax.set_xlabel(f'{modality_type.title()} Modality')
        ax.set_ylabel('Domain')
        
        plt.tight_layout()
        plt.show()
        
        print(f" Domain-{modality_type.title()} Modality Matrix:")
        print(f"  • Domains: {len(matrix.index)}")
        print(f"  • {modality_type.title()} modalities: {len(matrix.columns)}")
        print(f"  • Total relationships: {df['count'].sum()}")
        
        return matrix
        
    except Exception as e:
        print(f" Error creating domain-modality matrix: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


def create_domain_architecture_matrix(domain_analyzer: DomainAnalyzer,
                                    run_id_start: Optional[int] = None,
                                    run_id_end: Optional[int] = None,
                                    top_k_domains: int = 10,
                                    top_k_architectures: int = 10,
                                    figsize: Tuple[int, int] = (12, 10)) -> pd.DataFrame:
    """
    Create a matrix showing domain-architecture relationships.
    
    Args:
        domain_analyzer: DomainAnalyzer instance
        run_id_start: Starting extraction run ID (inclusive)
        run_id_end: Ending extraction run ID (inclusive)
        top_k_domains: Number of top domains to include
        top_k_architectures: Number of top architectures to include
        figsize: Figure size for the plot
    
    Returns:
        DataFrame with domain-architecture matrix
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get domain-architecture relationships
        query = """
        SELECT 
            ef_domain.value as domain,
            ef_arch.value as architecture,
            COUNT(DISTINCT p.id) as count
        FROM papers p
        JOIN extraction_runs er ON p.id = er.paper_id
        JOIN extracted_fields ef_domain ON er.id = ef_domain.run_id
        JOIN extracted_fields ef_arch ON er.id = ef_arch.run_id
        WHERE ef_domain.field_name = 'domain'
        AND ef_arch.field_name = 'architecture'
        AND p.published_date IS NOT NULL
        AND ef_domain.value NOT IN %s
        AND ef_arch.value NOT IN %s
        """
        
        params = [tuple(domain_analyzer.default_na_values), tuple(domain_analyzer.default_na_values)]
        if run_id_start is not None:
            query += " AND ef_domain.run_id >= %s"
            params.append(run_id_start)
        if run_id_end is not None:
            query += " AND ef_domain.run_id <= %s"
            params.append(run_id_end)
        
        query += " GROUP BY domain, architecture ORDER BY count DESC"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        if not results:
            print(" No domain-architecture data found")
            return pd.DataFrame()
        
        df = pd.DataFrame(results, columns=['domain', 'architecture', 'count'])
        
        # Expand array values in both domain and architecture fields
        excluded_architectures = ["Other - {High-Level Architecture Name}"]
        df_expanded = domain_analyzer._expand_array_data(df, 'domain')
        df_expanded = domain_analyzer._expand_array_data(df_expanded, 'architecture', excluded_architectures)
        
        # Additional filtering to ensure "Other" values are completely removed
        df_expanded = df_expanded[~df_expanded['architecture'].str.contains('Other', case=False, na=False)]
        
        # Recalculate counts after expansion
        df_expanded = df_expanded.groupby(['domain', 'architecture'])['count'].sum().reset_index()
        
        # Get top K domains and architectures
        top_domains = df_expanded.groupby('domain')['count'].sum().nlargest(top_k_domains).index.tolist()
        top_architectures = df_expanded.groupby('architecture')['count'].sum().nlargest(top_k_architectures).index.tolist()
        
        # Filter to top K values
        df_filtered = df_expanded[
            (df_expanded['domain'].isin(top_domains)) & 
            (df_expanded['architecture'].isin(top_architectures))
        ]
        
        # Create pivot table
        matrix = df_filtered.pivot(index='domain', columns='architecture', values='count').fillna(0)
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=figsize)
        sns.heatmap(matrix, annot=True, fmt='.0f', cmap=domain_analyzer.gradient_palette, ax=ax,
                   cbar_kws={'label': 'Count'})
        ax.set_title(f'Domain-Architecture Matrix\n(Top {top_k_domains} Domains × Top {top_k_architectures} Architectures)', fontsize=self.title_fontsize, fontweight='bold')
        ax.set_xlabel('Architecture')
        ax.set_ylabel('Domain')
        
        plt.tight_layout()
        plt.show()
        
        print(f" Domain-Architecture Matrix:")
        print(f"  • Domains: {len(matrix.index)}")
        print(f"  • Architectures: {len(matrix.columns)}")
        print(f"  • Total relationships: {df['count'].sum()}")
        
        return matrix
        
    except Exception as e:
        print(f" Error creating domain-architecture matrix: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()
