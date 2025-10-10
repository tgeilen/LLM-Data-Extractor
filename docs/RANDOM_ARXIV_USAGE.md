# Random ArXiv Discovery - Usage Examples

This script helps you get random arXiv papers from various domains while excluding foundation models and robotics papers.

## Basic Usage

### Get 500 random papers (default):
```bash
python3 random_arxiv_discovery.py
```

### Get 100 papers from the last 6 months:
```bash
python3 random_arxiv_discovery.py --target 100 --months 6
```

### Get papers from specific categories only:
```bash
python3 random_arxiv_discovery.py --target 200 --categories math.CO physics.optics cs.DB
```

### Export only arXiv IDs (not full paper data):
```bash
python3 random_arxiv_discovery.py --target 500 --ids-only --output my_random_ids.txt
```

## What the script does:

1. **Searches diverse categories**: Mathematics, Physics, Biology, Computer Science (non-robotics), Economics, etc.
2. **Excludes unwanted papers**: Filters out papers mentioning foundation models, robotics, LLMs, etc.
3. **Ensures diversity**: Limits papers per category and randomizes selection
4. **Respects rate limits**: Uses proper 3-second delays between API calls
5. **Provides random sampling**: If more papers found than requested, randomly samples

## Output files:

- `random_arxiv_results_YYYYMMDD_HHMMSS.json`: Full paper data
- `random_arxiv_ids_YYYYMMDD_HHMMSS.txt`: Just the arXiv IDs (one per line)

## Categories searched by default:

- `math.CO` - Combinatorics
- `physics.optics` - Optics
- `q-bio.BM` - Biomolecules
- `cs.DB` - Databases
- `econ.EM` - Econometrics
- `stat.ML` - Machine Learning (Statistics)
- `cs.CG` - Computational Geometry
- `physics.chem-ph` - Chemical Physics
- `cs.IR` - Information Retrieval
- `math.NT` - Number Theory
- `physics.soc-ph` - Physics and Society
- `cs.CY` - Computers and Society
- `q-bio.QM` - Quantitative Methods
- `cs.SE` - Software Engineering
- `math.ST` - Statistics Theory

You can override these with `--categories` if you want specific domains.
