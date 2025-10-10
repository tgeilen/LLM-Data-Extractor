# Master Thesis: Streamlined OCR and LLM Pipeline for Scientific Paper Analysis

This repository contains an advanced, production-ready pipeline for large-scale processing of scientific papers using OCR and Large Language Models (LLMs) for structured data extraction with parallel processing capabilities.

## Overview

The streamlined pipeline performs the following steps with advanced optimizations:
1. **Parallel Paper Acquisition**: Intelligent sequential downloads to avoid rate limiting
2. **Enhanced OCR Processing**: Convert PDFs to markdown using Azure OCR API with detailed image annotations
3. **Smart Token Analysis**: Determine optimal chunking strategy based on document size and token distribution
4. **Parallel LLM Analysis**: Extract structured data using multiple LLM providers with concurrent processing
5. **Optimized Database Storage**: Efficient storage with existing file detection and reuse
6. **Performance Analytics**: Real-time metrics and processing optimization

## Advanced Features

-  **Production-Grade Parallel Processing**: ThreadPoolExecutor-based concurrent OCR and LLM analysis
-  **Intelligent Batch Operations**: Sequential downloads + parallel processing to prevent rate limiting
-  **Smart File Management**: Automatic detection and reuse of existing PDFs and markdown files
-  **Enhanced OCR**: Azure OCR with detailed image annotations and fallback mechanisms
-  **Advanced Chunking**: Progressive chunking with token distribution analysis
-  **Multi-Provider Support**: DeepSeek and Gemini analyzers with load balancing
-  **Performance Optimization**: Real-time progress tracking and processing metrics
-  **Robust Error Handling**: Comprehensive error recovery and detailed logging
-  **Token Analytics**: Statistical analysis of document token distributions
-  **Memory Efficiency**: Optimized for processing hundreds of papers simultaneously

## Quick Start

### 1. Environment Setup

```bash
# Clone the repository
git clone https://github.com/tgeilen/Masterarbeit.git
cd Masterarbeit

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### 2. Database Setup

```bash
# Initialize database
python db/manage_db.py setup
```

### 3. Choose Your Workflow

The project provides **three main notebooks** that aggregate all relevant functions for different use cases:

#### 🔍 **RUN_THIS_4_arxivFilter.ipynb** - Paper Discovery & Filtering  
- **Purpose**: Search arXiv and filter papers using custom keywords
- **Features**: Customizable search, LLM-based classification, export arXiv IDs
- **Use when**: You need to find relevant papers for your research domain

#### 🚀 **RUN_THIS_4_extractionPipeline.ipynb** - Complete Processing Pipeline
- **Purpose**: Process papers from PDF/arXiv ID to extracted data in database
- **Features**: OCR processing, LLM analysis, database storage
- **Use when**: You want to extract structured data from scientific papers

#### 📊 **RUN_THIS_4_dataVisualisations.ipynb** - Analysis & Visualization
- **Purpose**: Analyze and visualize your extracted research data
- **Features**: Publication trends, model analysis, domain insights, interactive charts
- **Use when**: You want to analyze patterns in your processed data

### 4. Getting Started

Simply open the notebook that matches your needs in Jupyter and follow the step-by-step instructions. Each notebook is self-contained with detailed explanations and configuration options.

## Typical Workflow

For a complete research pipeline, use the notebooks in this order:

1. **🔍 Discovery**: Use `RUN_THIS_4_arxivFilter.ipynb` to find and filter relevant papers
2. **🚀 Processing**: Use `RUN_THIS_4_extractionPipeline.ipynb` to extract data from your papers  
3. **📊 Analysis**: Use `RUN_THIS_4_dataVisualisations.ipynb` to analyze and visualize your results

Each step can also be used independently based on your specific needs.

## Configuration

### Environment Variables

Create a `.env` file with your API credentials:

```env
# Azure OCR
AZURE_OCR_API_KEY=your_azure_ocr_key
AZURE_OCR_ENDPOINT=your_azure_endpoint

# LLM Providers
DEEPSEEK_API_TOKEN=your_deepseek_token
GEMINI_API_KEY=your_gemini_key
# OpenAI support removed

# Database
DATABASE_URL=postgresql://user:pass@localhost/dbname
```

### Advanced Pipeline Configuration

Key configuration options for the streamlined pipeline:

- `force_reprocess`: Force redownload/reprocess even if files exist (default: False)
- `use_enhanced_ocr`: Enable detailed image annotations (default: True)
- `use_annotations`: Control annotation usage - set to False if endpoint doesn't support (default: False)
- `max_chunk_size`: Maximum tokens per chunk (default: 16384)
- `chunk_overlap`: Overlap between chunks (default: 200)
- `temperature`: LLM sampling temperature (default: 0.3)
- `use_robotics_prompts`: Toggle between standard and robotics-specific prompts (default: False)
- `max_workers`: Number of parallel workers for batch processing (default: 16)
- `delay_seconds`: Delay between OCR requests to avoid rate limits (default: 0.1)

## Main Notebooks (Start Here!)

### 🚀 RUN_THIS_4_extractionPipeline.ipynb
**Complete PDF-to-Database Pipeline**
- Download papers from arXiv using paper IDs
- Process PDFs with Azure OCR (with enhanced image annotations)
- Smart chunking for large documents using intelligent tokenization
- Multi-provider LLM analysis (DeepSeek, Gemini, OpenAI)
- Complete database integration with storage and retrieval
- Progressive analysis with context-aware chunking

### 🔍 RUN_THIS_4_arxivFilter.ipynb  
**Paper Discovery and Filtering**
- Search arXiv with customizable keywords and search terms
- Smart filtering using LLM-based classification to identify relevant papers
- Multiple search modes and strategies
- Export results as text files compatible with existing data structure
- Perfect for building custom datasets for your research domain

### 📊 RUN_THIS_4_dataVisualisations.ipynb
**Research Data Analysis and Visualization**
- **Publication Trends**: Analyze publication counts over time, domain trends
- **Model Analysis**: Parameter size evolution, architecture trends, modality analysis  
- **Domain Insights**: Cross-domain comparisons, research focus areas
- **Interactive Visualizations**: Comprehensive charts and statistical analysis
- **Configurable Analysis**: Set run ID ranges to analyze specific datasets or time periods

## File Structure

```
OCR/code/
├── RUN_THIS_4_extractionPipeline.ipynb    # 🚀 Main processing pipeline
├── RUN_THIS_4_arxivFilter.ipynb           # 🔍 Paper discovery & filtering  
├── RUN_THIS_4_dataVisualisations.ipynb    # 📊 Data analysis & visualization
├── analyser/                    # LLM analyzers and advanced features
│   ├── base_analyser.py
│   ├── chunked_analyser.py
│   ├── deepseek_analyser.py
│   ├── gemini_analyser.py
│   ├── db_integration.py
│   ├── config.py               # Configuration management
│   ├── csv_processor.py        # CSV data processing
│   ├── trend_analysis.py       # Performance analytics
│   └── validation.py           # Data validation
├── ocr/                          # OCR processing modules
│   ├── ocr_analysis.py           # Enhanced OCR processing
│   ├── ocr_models.py             # OCR data models
│   └── OCR_test.py               # OCR testing script
├── arxiv_tools/                       # ArXiv discovery and processing
│   ├── arxiv_discovery.py       # Enhanced arXiv search
│   ├── arxiv_filter.py          # LLM-based paper classification
│   ├── discovery_pipeline.py    # Complete discovery pipeline
│   ├── simple_arxiv_discovery.py # Simple arXiv search
│   ├── standalone_discovery.py  # Standalone discovery script
│   ├── random_arxiv_discovery.py # Random paper discovery
│   ├── search_mode_summary.py   # Search mode analysis
│   ├── extract_arxiv_ids.py     # Extract IDs from results
│   └── generate_500_random_ids.py # Generate random ArXiv IDs
├── tokenizer/                   # Advanced token counting utilities
├── scripts/                     # Utility and management scripts
│   ├── code_analyzer.py         # Code analysis and duplicate detection
│   └── run_tests.py             # Test runner script
├── docs/                        # Documentation and guides
├── db/                          # Database models and DAOs
│   ├── manage_db.py             # Database management CLI
├── tests/                       # Comprehensive test suite
├── misc/                        # Additional analysis notebooks
└── requirements.txt             # Python dependencies
```

## Usage Examples

### 🔍 Finding Papers (RUN_THIS_4_arxivFilter.ipynb)

**For discovering relevant papers:**
1. Open `RUN_THIS_4_arxivFilter.ipynb`
2. Configure your search terms and keywords
3. Run the search and classification pipeline
4. Export arXiv IDs for further processing

**Example search configuration:**
- Search terms: "robotics", "machine learning", "computer vision"
- Classification: LLM-based relevance filtering
- Output: Text files compatible with extraction pipeline

### 🚀 Processing Papers (RUN_THIS_4_extractionPipeline.ipynb)

**For single paper processing:**
1. Open `RUN_THIS_4_extractionPipeline.ipynb`
2. Configure your arXiv ID or PDF path in the notebook
3. Run all cells to process from PDF to database

**Key features available in the notebook:**
- Enhanced OCR with image annotations
- Smart file reuse (skips existing files)
- Multiple LLM providers (DeepSeek, Gemini, OpenAI)
- Configurable chunking and temperature settings
- Real-time progress tracking

### 📊 Analyzing Results (RUN_THIS_4_dataVisualisations.ipynb)

**For data analysis and visualization:**
1. Open `RUN_THIS_4_dataVisualisations.ipynb`
2. Configure run ID ranges (optional - leave None for all data)
3. Run analysis cells to generate insights

**Available analyses:**
- Publication trends over time
- Model parameter evolution
- Domain and architecture analysis
- Interactive visualizations and statistical summaries

## Database Management

```bash
# List all papers
python db/manage_db.py list-papers --verbose

# Export results  
python db/manage_db.py export-results --output results.json

# Backup database
python db/manage_db.py backup --output backup.sql
```

## Parallel Processing and Batch Operations

### Sequential Download + Parallel Processing Architecture

The streamlined pipeline uses a two-phase approach for optimal performance:

```python
# Phase 1: Sequential Download (prevents rate limiting)
download_results = download_papers_sequentially(
    arxiv_papers,
    download_dir="downloaded_papers"
)

# Phase 2: Parallel OCR and Analysis
with ThreadPoolExecutor(max_workers=16) as executor:
    futures = [executor.submit(process_paper_parallel, id, info) 
               for id, info in download_results.items()]
    results = [future.result() for future in as_completed(futures)]
```

### Smart File Management

- **Existing File Detection**: Automatically detects and reuses existing PDFs and markdown files
- **Force Reprocess Control**: Override existing file detection with `force_reprocess=True`
- **Progressive Processing**: Skip completed steps to resume interrupted batch operations
- **Storage Optimization**: Efficient disk space usage with smart file organization
