#!/usr/bin/env python3
"""
Extract arXiv IDs from JSON results and save to text file.
Similar format to data/epoch_ids/epochRobot.txt
"""

import json
import sys
import os
from datetime import datetime

def extract_arxiv_ids_from_json(json_file_path, output_file_path=None):
    """
    Extract arXiv IDs from a JSON results file and save to text file.
    
    Args:
        json_file_path: Path to the JSON file with search results
        output_file_path: Path for output text file (optional)
    """
    # Read the JSON file
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f" Error reading JSON file: {e}")
        return
    
    # Extract arXiv IDs
    arxiv_ids = []
    if 'papers' in data:
        for paper in data['papers']:
            if 'arxiv_id' in paper:
                arxiv_ids.append(paper['arxiv_id'])
    
    if not arxiv_ids:
        print(" No arXiv IDs found in the JSON file")
        return
    
    # Generate output filename if not provided
    if output_file_path is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file_path = f"data/arxiv_ids/arxivIDs_random_{timestamp}.txt"
    
    # Save to text file
    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            for arxiv_id in arxiv_ids:
                f.write(f"{arxiv_id}\n")
        
        print(f" Extracted {len(arxiv_ids)} arXiv IDs")
        print(f" Saved to: {output_file_path}")
        
        # Show first few IDs as preview
        print(f"\n Preview (first 10 IDs):")
        for i, arxiv_id in enumerate(arxiv_ids[:10]):
            print(f"   {arxiv_id}")
        
        if len(arxiv_ids) > 10:
            print(f"   ... and {len(arxiv_ids) - 10} more")
            
    except Exception as e:
        print(f" Error saving to file: {e}")

def main():
    """Main function to handle command line usage."""
    if len(sys.argv) < 2:
        print("Usage: python extract_arxiv_ids.py <json_file> [output_file]")
        print("\nExample:")
        print("  python extract_arxiv_ids.py results/random_arxiv_results_20250828_175910.json")
        print("  python extract_arxiv_ids.py results/random_arxiv_results_20250828_175910.json data/arxiv_ids/arxivIDs_random.txt")
        return
    
    json_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(json_file):
        print(f" JSON file not found: {json_file}")
        return
    
    extract_arxiv_ids_from_json(json_file, output_file)

if __name__ == "__main__":
    main()
