#!/usr/bin/env python3
"""
Generate 50 random arXiv IDs for testing
"""

import arxiv
import random
import time
from datetime import datetime, timedelta

def get_sample_ids():
    """Get a small sample of random arXiv IDs."""
    
    categories = ['math.CO', 'physics.optics', 'cs.CG']
    exclude_terms = ['foundation model', 'robotics', 'robot', 'LLM', 'transformer']
    
    all_ids = []
    
    for category in categories:
        print(f"Searching {category}...")
        
        try:
            client = arxiv.Client()
            search = arxiv.Search(
                query=f"cat:{category}",
                max_results=30,
                sort_by=arxiv.SortCriterion.SubmittedDate
            )
            
            for paper in client.results(search):
                text = (paper.title + ' ' + paper.summary).lower()
                if not any(term.lower() in text for term in exclude_terms):
                    arxiv_id = paper.entry_id.split('/')[-1]
                    all_ids.append(arxiv_id)
                    
            time.sleep(1)
            
        except Exception as e:
            print(f"Error: {e}")
    
    # Randomly sample 20 IDs
    random.shuffle(all_ids)
    sample_ids = all_ids[:20]
    
    # Save to file
    with open('data/arxiv_ids/arxivIDs_test_sample.txt', 'w') as f:
        for paper_id in sample_ids:
            f.write(f"{paper_id}\n")
    
    print(f" Saved {len(sample_ids)} IDs to data/arxiv_ids/arxivIDs_test_sample.txt")
    
    # Show them
    for paper_id in sample_ids:
        print(paper_id)

if __name__ == "__main__":
    get_sample_ids()
