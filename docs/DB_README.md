# OCR Analysis Database System

This module enhances the existing OCR and PDF analysis system by adding a PostgreSQL database to improve extraction quality and reliability.

## Overview

The system now includes:

1. **PostgreSQL Database**: Stores papers, extraction results, and analysis outputs
2. **Multiple LLM Support**: Run analyses with different providers and models
3. **CLI Tools**: Manage the database and run analyses
4. **ArXiv Integration**: Download papers directly from arXiv for processing

## Setup

### Prerequisites

- Python 3.6+
- PostgreSQL database server
- Required Python packages (see requirements.txt)

### Installation

1. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your database and API credentials:
   ```
   # PostgreSQL DB credentials
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=ocr_analysis
   DB_USER=postgres
   DB_PASSWORD=yourpassword
   
   # OCR API credentials
   AZURE_API_KEY=your_api_key
   AZURE_OCR_ENDPOINT=your_api_endpoint
   
   # LLM API credentials
   DEEPSEEK_API_TOKEN=your_deepseek_token
   GEMINI_API_KEY=your_gemini_key
   ```

3. Initialize the database:
   ```bash
   python db/manage_db.py setup
   ```

## Usage

### Database Management

The `db/manage_db.py` script provides various commands to manage the database:

```bash
# Set up the database schema
python db/manage_db.py setup

# Reset the database (drop and recreate schema)
python db/manage_db.py reset

# Add a paper to the database
python db/manage_db.py add-paper path/to/paper.md --arxiv-id "2012.12345" --title "Paper Title"

# Add a model
python db/manage_db.py add-model "deepseek-chat" "DeepSeek" --context-size 8192

# List papers
python db/manage_db.py list-papers --verbose

# List models
python db/manage_db.py list-models --verbose

# Download and process a paper from arXiv
python db/manage_db.py process-arxiv 2012.12345 --run-analysis --deepseek-runs 2
```

### ArXiv Processing

The system now supports downloading and processing papers directly from arXiv:

```bash
# Download, OCR, and analyze a paper from arXiv
python arxiv_tools/arxiv_processor.py 2012.12345 --run-analysis --deepseek-runs 2

# Or use the manage_db.py script
python db/manage_db.py process-arxiv 2012.12345 --run-analysis
```

Options for arXiv processing:

- `--skip-ocr`: Download the paper but don't run OCR processing
- `--run-analysis`: Run LLM analysis after OCR processing
- `--deepseek-runs N`: Number of DeepSeek analysis runs to perform
- `--gemini-runs N`: Number of Gemini analysis runs to perform
- `--output-dir DIR`: Custom directory to store outputs

### Multi-Model Analysis

The `analyser/run_multi_analysis.py` script allows you to run multiple analyses on the same paper using different models:

```bash
# Run 3 DeepSeek analyses and 2 Gemini analyses
python analyser/run_multi_analysis.py path/to/paper.md --deepseek-runs 3 --gemini-runs 2
```

### Integration with Existing Analyzers

To integrate an existing analyzer with the database, use the functions in `analyser/db_integration.py`:

```python
from analyser.deepseek_analyser import DeepSeekAnalyser
from analyser.db_integration import analyze_and_store

# Initialize your analyzer
analyzer = DeepSeekAnalyser(api_token="your_token")

# Run analysis and store in database
paper_id, model_id, run_id = analyze_and_store(
    analyzer, 
    "path/to/paper.md", 
    "deepseek-chat", 
    "DeepSeek",
    temperature=0.2
)
```

## Database Schema

The database consists of the following tables:

- **papers**: Stores information about research papers
- **models**: Information about LLM models used for extraction
- **extraction_runs**: Tracks each analysis run
- **extracted_fields**: Individual extracted fields with confidence
- **paper_images**: Images extracted from papers during OCR

## Future Enhancements

Possible future improvements:

1. Add semantic similarity for text fields (using embeddings)
2. Implement statistical methods for numerical value analysis
3. Add confidence interval calculations for extracted values
4. Create a web interface for exploring extraction results
5. Add automatic validation against known reference values 