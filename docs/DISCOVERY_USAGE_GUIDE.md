# ArXiv Discovery Script - Usage Guide

## Overview

The standalone ArXiv discovery script has been optimized to closely match the behavior of the arXiv web interface when searching for foundational robotics papers.

## Key Findings

### Search Mode Performance

For the query **"foundational model AND robotics"**:

| Search Mode | Results | Query Generated | Best For |
|-------------|---------|-----------------|----------|
| `split-terms` ⭐ | 1,107 | `all:foundational AND all:model AND all:robotics` | **Closest to web interface (~927)** |
| `compound-terms` ⭐ | 1,107 | `all:foundational AND all:model AND all:robotics` | **Same as split-terms** |
| `phrase` | 609 | `all:"foundational model" AND all:robotics` | Conservative, exact phrases |
| `precise` | 468 | `abs:"foundational model" AND all:robotics` | Abstract-only search |
| `boolean` | 24,940 | `foundational model AND robotics` | Too broad, many false positives |
| `title-phrase` | 65 | `ti:"foundational model" AND all:robotics` | Very precise, title-only |

### Why Split-Terms Works Best

1. **API Limitation**: arXiv doesn't handle compound phrases like `all:"foundational model"` as effectively as individual terms
2. **Better Coverage**: Searching for `all:foundational AND all:model AND all:robotics` captures more relevant papers
3. **Web Interface Match**: This approach most closely mimics how the arXiv web interface processes search queries

## Recommended Usage

### Basic Usage (Recommended)
```bash
python3 standalone_discovery.py --search-terms "foundational model AND robotics" --search-mode split-terms
```

### For Maximum Discovery
```bash
python3 standalone_discovery.py \
  --search-terms "foundational model AND robotics" "foundation model AND robotics" \
  --search-mode split-terms \
  --max-results 0 \
  --months 0
```

### For Conservative/Precise Results
```bash
python3 standalone_discovery.py \
  --search-terms "foundational model AND robotics" \
  --search-mode phrase \
  --categories cs.RO cs.AI cs.LG
```

### For Title-Only Search
```bash
python3 standalone_discovery.py \
  --search-terms "foundational model AND robotics" \
  --search-mode title-phrase
```

## Search Mode Details

### `split-terms` (Default & Recommended)
- **What it does**: Splits multi-word terms into individual `all:word` searches
- **Example**: `"foundational model AND robotics"` → `"all:foundational AND all:model AND all:robotics"`
- **Best for**: Matching web interface behavior, comprehensive discovery

### `phrase`
- **What it does**: Uses exact phrase matching with quotes
- **Example**: `"foundational model AND robotics"` → `"all:\"foundational model\" AND all:robotics"`
- **Best for**: Conservative searches, exact terminology matching

### `compound-terms`
- **What it does**: Same as `split-terms` for the target queries
- **Example**: Same output as `split-terms`
- **Best for**: Alias for `split-terms` behavior

### `boolean`
- **What it does**: Uses default arXiv API boolean logic
- **Example**: `"foundational model AND robotics"` → `"foundational model AND robotics"`
- **Best for**: Very broad discovery (but expect many false positives)

## Query Construction Logic

The script transforms user queries based on the selected mode:

1. **Input**: `"foundational model AND robotics"`
2. **Split-terms processing**:
   - Split on " AND " → `["foundational model", "robotics"]`
   - Split multi-word terms → `["foundational", "model", "robotics"]`
   - Add field prefixes → `["all:foundational", "all:model", "all:robotics"]`
   - Join with " AND " → `"all:foundational AND all:model AND all:robotics"`

## Rate Limiting & Performance

- **Chunked Search**: Automatically handles large result sets with proper pagination
- **Rate Limiting**: 0.5s delay between API calls to respect arXiv limits
- **Progress Tracking**: Shows progress for large searches
- **Comprehensive Mode**: For `max-results=0`, retrieves ALL available papers

## Output Files

The script generates several output files in the `results/` directory:

- `search_results_YYYYMMDD_HHMMSS.json`: Raw search results
- `classified_results_YYYYMMDD_HHMMSS.json`: LLM classification results  
- `discovered_arxiv_ids_YYYYMMDD_HHMMSS.txt`: Final list of relevant arXiv IDs
- Custom filename via `--output` parameter

## API Verification

We've verified that our query construction matches the arXiv API expectations:

```bash
# Manual API verification shows:
curl "https://export.arxiv.org/api/query?search_query=all%3Afoundational+AND+all%3Amodel+AND+all%3Arobotics&max_results=1"
# Returns: 1107 total results (closest to web interface ~927)
```

## Troubleshooting

### Too Many Results
- Use `phrase` or `title-phrase` mode for more precision
- Add specific categories: `--categories cs.RO cs.AI`
- Reduce date range: `--months 12`

### Too Few Results  
- Use `split-terms` or `boolean` mode for broader search
- Remove category filters
- Increase date range: `--months 0` (all dates)

### Rate Limiting Issues
- The script automatically handles rate limiting
- For very large searches, expect longer execution times
- Use `--max-results 100` for testing

## Examples

### Comprehensive Foundation Model Discovery
```bash
python3 standalone_discovery.py \
  --search-terms \
    "foundational model AND robotics" \
    "foundation model AND robotics" \
    "large language model AND robotics" \
    "vision language model AND robotics" \
  --search-mode split-terms \
  --max-results 0 \
  --output comprehensive_foundation_models.txt
```

### Recent Papers Only
```bash
python3 standalone_discovery.py \
  --search-terms "foundational model AND robotics" \
  --search-mode split-terms \
  --months 6 \
  --categories cs.RO cs.AI cs.LG cs.CV
```

This guide reflects our thorough testing and optimization to ensure the script produces results that closely match the arXiv web interface behavior.
