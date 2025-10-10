#!/usr/bin/env python3
"""
Generate 500 random arXiv IDs from various domains (non-robotics, non-foundation-model)
and save directly to a text file like data/epoch_ids/epochRobot.txt
"""

import arxiv
import random
import time
from datetime import datetime, timedelta

# Various academic domains excluding robotics and AI/ML
SEARCH_CATEGORIES = [
    'math.CO',      # Combinatorics
    'physics.optics',  # Optics
    'q-bio.BM',     # Biomolecules
    'cs.DB',        # Databases
    'econ.EM',      # Econometrics
    'stat.ML',      # Machine Learning (but we'll filter out foundation models)
    'cs.CG',        # Computational Geometry
    'physics.chem-ph',  # Chemical Physics
    'cs.IR',        # Information Retrieval
    'math.NT',      # Number Theory
    'physics.soc-ph',   # Physics and Society
    'cs.CY',        # Computers and Society
    'q-bio.QM',     # Quantitative Methods
    'cs.SE',        # Software Engineering
    'math.ST',      # Statistics Theory
    'physics.atom-ph',  # Atomic Physics
    'cs.DS',        # Data Structures and Algorithms
    'math.AP',      # Analysis of PDEs
    'physics.bio-ph',   # Biological Physics
    'cs.GT',        # Computer Science and Game Theory
]

# Terms to exclude (robotics, foundation models, etc.)
EXCLUDE_TERMS = [
    'foundation model', 'foundational model', 'robotics', 'robot', 'robotic',
    'manipulation', 'grasping', 'navigation', 'autonomous', 'LLM',
    'large language model', 'vision language model', 'transformer',
    'BERT', 'GPT', 'multimodal', 'reinforcement learning', 'deep learning'
]

def should_exclude_paper(title, summary):
    """Check if paper should be excluded based on title and summary."""
    text = (title + ' ' + summary).lower()
    return any(term.lower() in text for term in EXCLUDE_TERMS)

def get_random_papers_from_category(category, target_count=50):
    """Get random papers from a specific category."""
    papers = []
    
    print(f"  Searching category: {category}")
    
    try:
        # Search recent papers (last 2 years)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=730)
        
        query = f"cat:{category}"
        search = arxiv.Search(
            query=query,
            max_results=200,  # Get more than needed to have selection
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )
        
        candidate_papers = []
        for paper in search.results():
            # Filter by date and exclusion terms
            if (paper.published.date() >= start_date.date() and 
                not should_exclude_paper(paper.title, paper.summary)):
                
                arxiv_id = paper.entry_id.split('/')[-1]
                candidate_papers.append(arxiv_id)
        
        # Randomly sample from candidates
        if candidate_papers:
            sample_size = min(target_count, len(candidate_papers))
            papers = random.sample(candidate_papers, sample_size)
        
        print(f"    Found {len(papers)} papers")
        time.sleep(2)  # Be respectful to API
        
    except Exception as e:
        print(f"    Error searching {category}: {e}")
    
    return papers

def generate_random_arxiv_ids(target_total=500, output_file="data/arxiv_ids/arxivIDs_random_500.txt"):
    """Generate random arXiv IDs and save to text file."""
    
    print(f" Target: {target_total} random arXiv IDs")
    print(f" Categories: {len(SEARCH_CATEGORIES)} different domains")
    print(f" Excluding: robotics, foundation models, etc.")
    
    all_papers = []
    papers_per_category = target_total // len(SEARCH_CATEGORIES) + 5  # Get a few extra
    
    # Collect papers from each category
    for category in SEARCH_CATEGORIES:
        category_papers = get_random_papers_from_category(category, papers_per_category)
        all_papers.extend(category_papers)
        
        if len(all_papers) >= target_total * 1.2:  # Stop if we have enough
            break
    
    # Remove duplicates and randomly sample
    unique_papers = list(set(all_papers))
    random.shuffle(unique_papers)
    
    final_papers = unique_papers[:target_total]
    
    print(f"\n Summary:")
    print(f"   Total collected: {len(unique_papers)}")
    print(f"   Final selection: {len(final_papers)}")
    
    # Save to file
    with open(output_file, 'w') as f:
        for paper_id in final_papers:
            f.write(f"{paper_id}\n")
    
    print(f" Saved to: {output_file}")
    
    # Show preview
    print(f"\n Preview (first 10 IDs):")
    for i, paper_id in enumerate(final_papers[:10]):
        print(f"   {paper_id}")
    
    if len(final_papers) > 10:
        print(f"   ... and {len(final_papers) - 10} more")

if __name__ == "__main__":
    random.seed(42)  # For reproducibility
    generate_random_arxiv_ids(target_total=500)
