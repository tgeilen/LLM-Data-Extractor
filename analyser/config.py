"""
Configuration settings for trend analysis.

This module contains default configuration values and settings for the trend analysis system.
"""

from typing import List, Dict, Any
from pathlib import Path

# Default N/A values to treat as missing data
DEFAULT_NA_VALUES: List[str] = [
    'n/a', '', 'N/A', 'unknown', 'None', 'null', 'not specified',
    'not available', 'not reported', 'unclear', '-', 'not mentioned',
    'missing', 'none', 'null', 'TBD', 'to be determined'
]

# Common fields to analyze
COMMON_FIELDS: List[str] = [
    'Parameters', 'Architecture', 'Dataset', 'Performance', 'Task', 'Domain'
]

# Default visualization settings
DEFAULT_PLOT_SETTINGS: Dict[str, Any] = {
    'figsize': (12, 10),
    'dpi': 100,
    'style': 'default',
    'palette': 'husl',
    'alpha': 0.7,
    'marker_size': 60,
    'line_width': 2,
    'grid_alpha': 0.3
}

# Time grouping options
TIME_GROUPING_OPTIONS: Dict[str, int] = {
    'monthly': 1,
    'quarterly': 3,
    'yearly': 12,
    'biannual': 6
}

# CSV processing settings
CSV_SETTINGS: Dict[str, Any] = {
    'default_link_column': 'Link',
    'default_parameters_column': 'Parameters',
    'arxiv_patterns': [
        r'arxiv\.org/abs/(\d{4}\.\d{4,5})',  # abs URL
        r'arxiv\.org/pdf/(\d{4}\.\d{4,5})',  # pdf URL
        r'^(\d{4}\.\d{4,5})$',               # direct ID
        r'(\d{4}\.\d{4,5})v\d+'             # versioned ID
    ],
    'max_preview_examples': 10
}

# Database query settings
DB_SETTINGS: Dict[str, Any] = {
    'default_timeout': 30,
    'batch_size': 1000,
    'max_retries': 3
}

# File paths
PATHS: Dict[str, Path] = {
    'data_dir': Path('data'),
    'results_dir': Path('results'),
    'csv_dir': Path('csv_data'),
    'plots_dir': Path('plots')
}

# Statistical analysis settings
STATS_SETTINGS: Dict[str, Any] = {
    'min_samples_for_trend': 3,
    'confidence_level': 0.95,
    'rolling_window_years': 2,
    'outlier_threshold': 3.0  # standard deviations
}

# Color schemes for different data sources
COLOR_SCHEMES: Dict[str, str] = {
    'database_range1': '#1f77b4',  # Blue
    'database_range2': '#ff7f0e',  # Orange
    'csv_data': '#2E8B57',         # Sea Green
    'na_values': '#d62728',        # Red
    'trend_line': '#9467bd'        # Purple
}

# Logging configuration
LOGGING_CONFIG: Dict[str, Any] = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'trend_analysis.log'
}

def get_config() -> Dict[str, Any]:
    """
    Get complete configuration dictionary.
    
    Returns:
        Dictionary containing all configuration settings
    """
    return {
        'na_values': DEFAULT_NA_VALUES,
        'common_fields': COMMON_FIELDS,
        'plot_settings': DEFAULT_PLOT_SETTINGS,
        'time_grouping': TIME_GROUPING_OPTIONS,
        'csv_settings': CSV_SETTINGS,
        'db_settings': DB_SETTINGS,
        'paths': PATHS,
        'stats_settings': STATS_SETTINGS,
        'colors': COLOR_SCHEMES,
        'logging': LOGGING_CONFIG
    }

def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration settings.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        True if configuration is valid, False otherwise
    """
    required_keys = ['na_values', 'common_fields', 'plot_settings']
    
    for key in required_keys:
        if key not in config:
            print(f" Missing required configuration key: {key}")
            return False
    
    # Validate plot settings
    plot_settings = config.get('plot_settings', {})
    if 'figsize' not in plot_settings:
        print(" Missing figsize in plot_settings")
        return False
    
    figsize = plot_settings['figsize']
    if not isinstance(figsize, (list, tuple)) or len(figsize) != 2:
        print(" figsize must be a tuple/list of length 2")
        return False
    
    return True
