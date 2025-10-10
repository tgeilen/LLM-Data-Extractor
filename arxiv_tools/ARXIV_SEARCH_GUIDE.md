# ArXiv API Search Strategy Guide

## Understanding the Issues with Your Current Implementation

After analyzing the arXiv API documentation and your current implementation, here are the key issues and solutions:

##  Core Problems Identified

### 1. **Search Query Construction Issues**

**Problem**: Your current search transformations don't properly follow arXiv API syntax.

**Current problematic approach**:
```python
# This creates queries that don't work as expected
"all:foundation+model"  # URL encoding handled incorrectly
"all:foundation AND all:model AND all:robotics"  # Too restrictive
```

**Correct approach**:
```python
# The arxiv library handles URL encoding automatically
'robotics AND "foundation model"'  # Natural, effective
'all:robotics AND all:"foundation model"'  # Field-specific
'ti:"robotics foundation model"'  # Title-focused
```

### 2. **Search Mode Problems**

**Issue**: Your current search modes create overly complex or ineffective queries.

**Better search modes**:
- `natural`: Use queries as-is (like typing in web interface)
- `balanced`: Smart field targeting with proper phrase handling
- `exact`: Exact phrase matching in quotes
- `title_focus`: Focus on paper titles
- `comprehensive`: Broad field searching

### 3. **Pagination and Rate Limiting**

**Problem**: Complex chunking and potential API violations.

**Solution**: Use the arxiv library's built-in pagination and proper 3-second delays.

##  Testing the Search Strategies

Use the `test_arxiv_search_comparison.py` script to test different approaches:

```bash
# Test all search strategies
python test_arxiv_search_comparison.py

# Test only basic queries  
python test_arxiv_search_comparison.py --basic-only

# Quick test with fewer results
python test_arxiv_search_comparison.py --quick
```

This will help find which search strategy gives results closest to the web interface.

##  Recommended Search Strategies

### For "foundation model AND robotics" searches:

1. **Most Web-Like** (Recommended):
   ```python
   query = 'robotics AND "foundation model"'
   ```

2. **Broader Coverage**:
   ```python
   query = '(robotics OR robotic) AND ("foundation model" OR "foundational model")'
   ```

3. **Title-Focused**:
   ```python
   query = 'ti:robotics AND ti:"foundation model"'
   ```

4. **Multi-Field**:
   ```python
   query = '(ti:robotics OR abs:robotics) AND (ti:"foundation model" OR abs:"foundation model")'
   ```

##  arXiv API Best Practices

### Search Query Syntax (from documentation):

- **Field Prefixes**: `ti:` (title), `abs:` (abstract), `au:` (author), `cat:` (category), `all:` (all fields)
- **Boolean Operators**: `AND`, `OR`, `ANDNOT` (must be uppercase)
- **Phrases**: Use double quotes `"foundation model"`
- **Grouping**: Use parentheses `(ti:robotics OR abs:robotics)`
- **Date Filtering**: `submittedDate:[20230101 TO 20240101]`

### Rate Limiting:
- **Mandatory**: 3-second delay between requests
- **Page Size**: 100 results per request (maximum 2000)
- **Total Limit**: 30,000 results maximum per query

### Sorting:
- **Relevance**: `sortBy=relevance` (default, matches web interface)
- **Date**: `sortBy=lastUpdatedDate` or `sortBy=submittedDate`
- **Order**: `sortOrder=descending` or `sortOrder=ascending`

##  Using the Improved Implementation

### Basic Usage:
```python
from arxiv_tools.arxiv_discovery import ArXivDiscovery

# Create discovery instance
config = {
    'search_terms': ['robotics AND "foundation model"'],
    'categories': [],  # Search all categories
    'search_mode': 'balanced',  # Web-like behavior
    'sort_by': 'relevance',
    'max_papers_per_search': 0  # Get all results
}

discovery = ArXivDiscovery(config)
papers = discovery.run_discovery()

# Save results
discovery.save_results()
discovery.export_arxiv_ids()  # For use with other tools
```

### Command Line Usage:
```bash
# Basic search
python -m arxiv.arxiv_discovery --search-terms "robotics foundation model"

# Multiple terms with category filtering
python -m arxiv.arxiv_discovery --search-terms "foundation model" "foundational model" --categories cs.RO cs.AI

# Title-focused search
python -m arxiv.arxiv_discovery --search-terms "transformer" --mode title_focus

# Recent papers only
python -m arxiv.arxiv_discovery --search-terms "robotics" --months 12
```

##  Expected Improvements

With the improved implementation, you should see:

1. **Better Result Quality**: More relevant papers, fewer false positives
2. **Web Interface Alignment**: Results closer to what you see on arxiv.org
3. **Faster Performance**: Simpler, more efficient queries
4. **Better Rate Limiting**: Compliant with arXiv guidelines
5. **More Reliable**: Proper error handling and retries

