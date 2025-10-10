"""
Module for downloading scientific papers from arXiv.
"""

import os
import arxiv
import requests
from pathlib import Path

def download_arxiv_paper(arxiv_id, output_dir="downloaded_papers"):
    """
    Download a paper from arXiv by its ID using the arxiv Python library.
    
    Args:
        arxiv_id: The arXiv ID (e.g., "2101.12345")
        output_dir: Directory to save the paper to
        
    Returns:
        tuple: (path to saved PDF file, paper metadata) or (None, None) on failure
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Search for the paper
    search = arxiv.Search(id_list=[arxiv_id])
    
    try:
        # Get the first result
        for paper in search.results():
            # Paper metadata available:
            # - paper.title
            # - paper.authors
            # - paper.summary
            # - paper.published (datetime)
            # - paper.updated (datetime)
            # - paper.categories
            # - paper.pdf_url
            
            # Create filename from arXiv ID
            safe_id = arxiv_id.replace('/', '_')
            filename = f"{safe_id}.pdf"
            filepath = os.path.join(output_dir, filename)
            
            # Get the PDF URL
            pdf_url = paper.pdf_url
            
            # Download using requests instead of the library's method
            print(f"Downloading from: {pdf_url}")
            response = requests.get(pdf_url)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            # Save the PDF
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print(f"Downloaded paper: {paper.title}")
            print(f"Saved to: {filepath}")
            
            # Return the filepath and paper metadata
            return filepath, {
                "title": paper.title,
                "authors": [str(author) for author in paper.authors],
                "published": paper.published,
                "updated": paper.updated,
                "categories": paper.categories,
                "summary": paper.summary
            }
        
        print(f"Paper with ID {arxiv_id} not found")
        return None, None
        
    except Exception as e:
        print(f"Error downloading paper {arxiv_id}: {str(e)}")
        return None, None

if __name__ == "__main__":
    # Simple test for the download functionality
    import argparse
    
    parser = argparse.ArgumentParser(description="Download a paper from arXiv")
    parser.add_argument("arxiv_id", help="arXiv ID of the paper to download")
    parser.add_argument("--output-dir", default="downloaded_papers", help="Directory to save the paper to")
    
    args = parser.parse_args()
    
    pdf_path, metadata = download_arxiv_paper(args.arxiv_id, args.output_dir)
    
    if pdf_path:
        print(f"Paper downloaded to: {pdf_path}")
        print("Metadata:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")
    else:
        print("Failed to download paper") 