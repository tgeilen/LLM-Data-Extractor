"""
Configuration settings for arXiv paper discovery.

This file contains default configurations for searching and classifying papers
to discover foundational robotics models.
"""

# Default search configuration
DEFAULT_DISCOVERY_CONFIG = {
    # Search terms for arXiv queries
    'search_terms': [
        'robotics AND foundation model',
        'robot AND large model', 
        'robotics AND transformer',
        'robot AND multimodal AND model',
        'robotics AND general purpose',
        'robot AND world model'
    ],
    
    # ArXiv categories to search within
    'categories': [
        'cs.RO',  # Robotics
        'cs.AI',  # Artificial Intelligence
        'cs.LG',  # Machine Learning
        'cs.CV',  # Computer Vision
        'cs.CL'   # Computation and Language
    ],
    
    # Search parameters
    'max_papers_per_search': 50,
    'date_range_months': 12,  # Last 12 months
    
    # Classification parameters
    'classification_provider': 'deepseek',  # 'deepseek' or 'gemini'
    'confidence_threshold': 0.7,
    'rate_limit_delay': 1.0,  # Seconds between API calls
    
    # Output settings
    'output_file': 'discovered_foundational_robotics_models.txt',
    'save_intermediate_results': True
}

# Robotics domains for classification
ROBOTICS_DOMAINS = [
    'manipulation',
    'navigation', 
    'perception',
    'planning',
    'control',
    'grasping',
    'locomotion',
    'vision',
    'language',
    'multi-task',
    'general-purpose'
]

# Keywords that indicate foundational models
FOUNDATIONAL_KEYWORDS = [
    'foundation model',
    'foundation',
    'general-purpose',
    'general purpose',
    'multi-task',
    'multitask',
    'unified',
    'universal',
    'large-scale',
    'pre-trained',
    'pretrained',
    'transformer',
    'world model',
    'multimodal'
]

# Keywords that indicate NOT foundational models (exclusions)
NON_FOUNDATIONAL_KEYWORDS = [
    'specific task',
    'single task',
    'specialized',
    'dataset',
    'benchmark',
    'evaluation',
    'survey',
    'review',
    'simulation',
    'hardware',
    'mechanical'
]
