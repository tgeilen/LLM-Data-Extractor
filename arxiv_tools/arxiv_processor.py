#!/usr/bin/env python3
"""
Script to download papers from arXiv, process them with OCR, and store them in the database.
"""

import os
import argparse
import json
from dotenv import load_dotenv

# Import arXiv downloader
from .arxiv_downloader import download_arxiv_paper

# Import OCR processor
from ..ocr.OCR_test import process_pdf_with_ocr, save_text_to_file, save_json_to_file

# Import database modules
from ..db.db_utils import create_schema
from ..db.paper_dao import PaperDAO
from ..db.image_dao import insert_paper_image, save_image_from_base64

# Import analysis modules (optional)
from ..analyser.deepseek_analyser import DeepSeekAnalyser
from ..analyser.gemini_analyser import GeminiAnalyser
from ..analyser.db_integration import analyze_and_store

# Load environment variables
load_dotenv()

def store_ocr_images(ocr_result, paper_id, image_dir):
    """
    Extract and store images from OCR response
    
    Args:
        ocr_result: The OCR API response
        paper_id: Database ID of the associated paper
        image_dir: Directory to save images to
        
    Returns:
        List of image metadata (page, position, path)
    """
    os.makedirs(image_dir, exist_ok=True)
    image_metadata = []
    
    if 'pages' in ocr_result:
        for page_idx, page in enumerate(ocr_result['pages']):
            if 'images' in page and page['images']:
                for img_idx, image in enumerate(page['images']):
                    if 'image_base64' in image and image['image_base64']:
                        # Create image filename
                        image_id = image.get('id', f"page{page_idx}_img{img_idx}")
                        image_path = os.path.join(image_dir, f"{image_id}.png")
                        
                        # Save image
                        if save_image_from_base64(image['image_base64'], image_path):
                            # Extract position if available
                            position = {
                                "x": image.get('x', 0),
                                "y": image.get('y', 0),
                                "width": image.get('width', 0),
                                "height": image.get('height', 0)
                            }
                            
                            # Store in database
                            image_db_id = insert_paper_image(
                                paper_id,
                                page.get('index', page_idx),
                                image_id,
                                image_path,
                                image.get('caption', ''),
                                position
                            )
                            
                            if image_db_id:
                                # Add to metadata list
                                metadata = {
                                    "id": image_db_id,
                                    "paper_id": paper_id,
                                    "page_number": page.get('index', page_idx),
                                    "image_id": image_id,
                                    "path": image_path,
                                    "caption": image.get('caption', ''),
                                    "position": position
                                }
                                image_metadata.append(metadata)
                                print(f"- Stored image in database with ID: {image_db_id}")
    
    return image_metadata

def process_paper_from_arxiv(arxiv_id, run_ocr=True, run_analysis=False, 
                            deepseek_runs=0, gemini_runs=0, output_dir=None):
    """
    Download a paper from arXiv, process it with OCR, and optionally run analysis.
    
    Args:
        arxiv_id: The arXiv ID to process
        run_ocr: Whether to run OCR on the paper
        run_analysis: Whether to run analysis on the OCR results
        deepseek_runs: Number of DeepSeek analysis runs
        gemini_runs: Number of Gemini analysis runs
        output_dir: Directory to save outputs to (default: results/{arxiv_id})
        
    Returns:
        paper_id: Database ID of the paper
    """
    # Determine output directory
    if output_dir is None:
        output_dir = os.path.join("results", arxiv_id.replace('/', '_'))
    
    # Create output directories
    os.makedirs(output_dir, exist_ok=True)
    pdf_dir = os.path.join(output_dir, "pdf")
    os.makedirs(pdf_dir, exist_ok=True)
    
    print(f"Processing paper {arxiv_id} from arXiv...")
    
    # Download the paper
    pdf_path, metadata = download_arxiv_paper(arxiv_id, pdf_dir)
    
    if not pdf_path:
        print(f"Failed to download paper {arxiv_id}")
        return None
    
    print(f"Downloaded paper to {pdf_path}")
    
    # Store paper in database with metadata from arXiv
    paper_id = PaperDAO.insert_paper(
        arxiv_id=arxiv_id,
        title=metadata["title"],
        pdf_path=pdf_path,
        published_date=metadata.get("published")
    )
    
    if not paper_id:
        print("Failed to store paper in database")
        return None
    
    print(f"Stored paper in database with ID: {paper_id}")
    
    # Run OCR if requested
    if run_ocr:
        # Get API credentials
        
            
        print(f"Processing PDF with OCR...")
        
        # Process with OCR
        result = process_pdf_with_ocr(pdf_path)
        
        if result:
            # Save OCR results
            md_path = os.path.join(output_dir, f"{arxiv_id.replace('/', '_')}.md")
            json_path = os.path.join(output_dir, f"{arxiv_id.replace('/', '_')}_response.json")
            
            # Extract text
            extracted_text = ""
            if 'pages' in result:
                for page in result['pages']:
                    if 'markdown' in page:
                        extracted_text += page['markdown'] + "\n\n"
            
            # Save text and JSON
            save_text_to_file(extracted_text, md_path)
            save_json_to_file(result, json_path)
            
            print(f"Saved OCR results to {md_path}")
            
            # Store images
            image_dir = os.path.join(output_dir, "images")
            image_metadata = store_ocr_images(result, paper_id, image_dir)
            
            print(f"Stored {len(image_metadata)} images from OCR results")
            
            # Update paper record with MD path
            PaperDAO.update_paper_md_path(paper_id, md_path)
            
            print(f"Updated paper record with markdown path")
            
            # Run analysis if requested
            if run_analysis and (deepseek_runs > 0 or gemini_runs > 0):
                print(f"Running analysis on OCR results...")
                
                # DeepSeek analyses
                if deepseek_runs > 0:
                    print(f"Running {deepseek_runs} DeepSeek analyses...")
                    all_deepseek_run_ids = []
                    
                    # Run DeepSeek analysis multiple times
                    for i in range(deepseek_runs):
                        print(f"DeepSeek analysis run {i+1}/{deepseek_runs}")
                        # Create a new analyzer instance for each run (with different temperature)
                        temperature = 0.2 + (i * 0.05)  # Slight variation in temperature for diversity
                        analyzer = DeepSeekAnalyser()
                        
                        paper_id, model_id, run_ids = analyze_and_store(
                            analyzer,
                            md_path,
                            "deepseek-chat",
                            "DeepSeek",
                            temperature=temperature
                        )
                        
                        if run_ids:
                            all_deepseek_run_ids.extend(run_ids)
                    
                    print(f"Completed {len(all_deepseek_run_ids)} DeepSeek extractions")
                
                # Gemini analyses
                if gemini_runs > 0:
                    print(f"Running {gemini_runs} Gemini analyses...")
                    all_gemini_run_ids = []
                    
                    # Run Gemini analysis multiple times
                    for i in range(gemini_runs):
                        print(f"Gemini analysis run {i+1}/{gemini_runs}")
                        # Create a new analyzer instance for each run (with different temperature)
                        temperature = 0.2 + (i * 0.05)  # Slight variation in temperature for diversity
                        analyzer = GeminiAnalyser()
                        
                        paper_id, model_id, run_ids = analyze_and_store(
                            analyzer,
                            md_path,
                            "gemini-pro",
                            "Google",
                            temperature=temperature
                        )
                        
                        if run_ids:
                            all_gemini_run_ids.extend(run_ids)
                    
                    print(f"Completed {len(all_gemini_run_ids)} Gemini extractions")
        else:
            print("OCR processing failed")
    
    return paper_id

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Download and process a paper from arXiv")
    parser.add_argument("arxiv_id", help="arXiv ID of the paper to process")
    parser.add_argument("--skip-ocr", action="store_true", help="Skip OCR processing")
    parser.add_argument("--run-analysis", action="store_true", help="Run analysis after OCR")
    parser.add_argument("--deepseek-runs", type=int, default=0, help="Number of DeepSeek runs")
    parser.add_argument("--gemini-runs", type=int, default=0, help="Number of Gemini runs")
    parser.add_argument("--output-dir", help="Directory to save outputs to")
    
    args = parser.parse_args()
    
    # Make sure database schema exists
    create_schema()
    
    # Process the paper
    paper_id = process_paper_from_arxiv(
        arxiv_id=args.arxiv_id,
        run_ocr=not args.skip_ocr,
        run_analysis=args.run_analysis,
        deepseek_runs=args.deepseek_runs,
        gemini_runs=args.gemini_runs,
        output_dir=args.output_dir
    )
    
    if paper_id:
        print(f"Paper processed successfully. Paper ID: {paper_id}")
    else:
        print("Failed to process paper completely")

if __name__ == "__main__":
    main() 