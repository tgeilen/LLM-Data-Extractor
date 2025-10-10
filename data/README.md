# Data Directory

This directory contains organized data files used throughout the OCR project.

## Directory Structure

```
data/
├── arxiv_ids/          # ArXiv paper ID lists
│   ├── arxivIDs_clean.txt              # Curated robotics/foundation model papers
│   ├── arxivIDs_random_500.txt         # Random non-robotics papers for testing
│   ├── arxivIDs_ROBOTICS.txt           # Robotics-focused papers
│   ├── arxivIDs_ROBOTICS_SINGLE.txt    # Single robotics paper for testing
│   ├── arxivIDs_SINGLE.txt             # Single paper for testing
│   └── arxivIDs_random_nonrobot.txt    # Random non-robotics papers
└── epoch_ids/             # Epoch-based paper collections
    ├── epochRobot.txt                   # Robot-related papers by epoch
    ├── epochRobot_clean.txt             # Cleaned robot papers
    ├── epochVision.txt                  # Computer vision papers by epoch
    ├── epochVision_clean.txt            # Cleaned vision papers
    ├── epochNonRobot.txt                # Non-robot papers by epoch
    ├── epochNonRobot_clean.txt          # Cleaned non-robot papers
    ├── epochNonVision.txt               # Non-vision papers by epoch
    └── epochNonVision_clean.txt         # Cleaned non-vision papers
```

## File Descriptions

### ArXiv IDs Directory (`arxiv_ids/`)

Contains text files with arXiv paper IDs (one per line) used for:
- **Training data**: Positive and negative examples for model evaluation
- **Testing**: Single papers or small batches for development
- **Random sampling**: Diverse papers for baseline comparisons

### Epochs Directory (`epoch_ids/`)

Contains epoch-based collections of papers organized by:
- **Domain**: Robot vs Vision vs General
- **Quality**: Raw vs cleaned versions
- **Purpose**: Training, validation, or testing datasets

## Usage

These files are referenced throughout the codebase:

```python
# Load arXiv IDs for processing
arxiv_papers = import_arxiv_ids('data/arxiv_ids/arxivIDs_clean.txt')

# Use in evaluation notebooks
CONFIG = {
    'positive_samples_file': 'data/arxiv_ids/arxivIDs_clean.txt',
    'negative_samples_file': 'data/arxiv_ids/arxivIDs_random_500.txt',
}
```

## File Format

All files use simple text format:
```
2301.12345
2302.67890
2303.11111
```

Each line contains one arXiv ID without prefixes (no "arXiv:" prefix needed).
