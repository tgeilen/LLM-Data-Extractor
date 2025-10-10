#!/usr/bin/env python3
"""
Test script for the chunked analyser module.

This script demonstrates how to use the chunked analyser to process
large scientific publications that exceed the token limits of LLMs.
"""

import os
import argparse
import time
import json
from typing import Optional, List

# Import the tokenizer
from tokenizer import get_tokenizer

# Import analyzers
from analyser.base_analyser import BaseAnalyser
from analyser.deepseek_analyser import DeepSeekAnalyser
from analyser.gemini_analyser import GeminiAnalyser
from analyser.chunked_analyser import ChunkedAnalyser, create_chunked_analyser

# Import database integration
from analyser.db_integration import (
    analyze_and_store, 
    store_paper_from_md_file, 
    get_or_create_model, 
    store_extraction_results
)


def test_chunked_analysis(
    file_path: str,
    provider: str = "deepseek",
    api_key: Optional[str] = None,
    max_tokens: Optional[int] = None,
    progressive: bool = True,
    exclude_sections: List[str] = None,
    save_to_db: bool = False,
    arxiv_id: Optional[str] = None,
    title: Optional[str] = None
) -> None:
    """
    Test the chunked analyser on a scientific publication.
    
    Args:
        file_path: Path to the markdown file to analyze
        provider: LLM provider to use (deepseek, gemini)
        api_key: API key for the provider
        max_tokens: Maximum tokens per chunk
        progressive: Whether to use progressive chunking
        exclude_sections: List of section names to exclude (e.g. ["References"])
        save_to_db: Whether to save results to database
        arxiv_id: ArXiv ID of the paper (for database storage)
        title: Title of the paper (for database storage)
    """
    # Default to excluding References if not specified
    if exclude_sections is None:
        exclude_sections = ["References"]
    
    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return
    
    # Create the base analyser based on provider
    if provider.lower() == "deepseek":
        base_analyser = DeepSeekAnalyser()
        print(f"Created DeepSeek analyser with model: {base_analyser.model}")
        model_name = base_analyser.model
    
    elif provider.lower() == "gemini":
        # Use the Gemini API key from environment if not provided
        if not api_key:
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                print("Error: Gemini API key not provided and not found in environment variable GEMINI_API_KEY.")
                return
        
        base_analyser = GeminiAnalyser(api_key=api_key)
        print(f"Created Gemini analyser with model: {base_analyser.model_name}")
        model_name = base_analyser.model_name
    
    else:
        print(f"Error: Unsupported provider: {provider}. Available: deepseek, gemini")
        return
    
    # Create the chunked analyser
    chunked_analyser = create_chunked_analyser(
        base_analyser=base_analyser,
        provider=provider,  # Use same provider for tokenizer
        max_tokens=max_tokens,
        progressive=progressive
    )
    
    print(f"Using {'progressive' if progressive else 'standard'} chunking mode")
    
    # Get the file size
    file_size_kb = os.path.getsize(file_path) / 1024
    print(f"Analyzing file: {file_path} ({file_size_kb:.2f} KB)")
    
    # Count tokens in the file
    tokenizer = get_tokenizer(provider)
    if tokenizer:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        token_count = tokenizer.count_tokens(content)
        print(f"File contains approximately {token_count} tokens")
    
    # Set the excluded sections in the tokenizer
    if hasattr(chunked_analyser, 'tokenizer'):
        if exclude_sections:
            print(f"Excluding sections: {', '.join(exclude_sections)}")
            chunked_analyser.exclude_sections = exclude_sections
    
    # Measure analysis time
    start_time = time.time()
    
    # Analyze the publication
    text_file, json_file = chunked_analyser.analyze_publication(file_path)
    
    elapsed_time = time.time() - start_time
    
    # Report results
    if text_file or json_file:
        print(f"\nAnalysis completed in {elapsed_time:.2f} seconds.")
        if text_file:
            print(f"Text response saved to: {text_file}")
        if json_file:
            print(f"JSON response saved to: {json_file}")
            
            # Print a summary of the extracted models
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    response = json.load(f)
                
                if isinstance(response, list):
                    print(f"\nExtracted {len(response)} model variants:")
                    for i, model in enumerate(response):
                        if isinstance(model, dict) and "model_name" in model:
                            model_name_value = model["model_name"]["value"]
                            fields_count = sum(1 for field in model if model[field].get("value") != "n/a")
                            total_fields = len(model)
                            print(f"  {i+1}. {model_name_value}: {fields_count}/{total_fields} fields with data")
                
                # Save to database if requested
                if save_to_db:
                    print(f"\n️ Saving results to database...")
                    try:
                        # Store the paper in database
                        paper_id = store_paper_from_md_file(
                            file_path, 
                            arxiv_id=arxiv_id, 
                            title=title
                        )
                        
                        if paper_id:
                            print(f" Paper stored with ID: {paper_id}")
                            
                            # Get or create model record
                            model_id = get_or_create_model(
                                model_name=model_name,
                                provider=provider.title(),
                                context_size=max_tokens
                            )
                            
                            if model_id:
                                print(f" Model stored with ID: {model_id}")
                                
                                # Store extraction results
                                run_ids = store_extraction_results(
                                    paper_id=paper_id,
                                    model_id=model_id,
                                    response=response,
                                    temperature=getattr(base_analyser, 'temperature', None)
                                )
                                
                                if run_ids:
                                    print(f" Extraction results stored with run IDs: {run_ids}")
                                    print(f" Database storage completed successfully!")
                                else:
                                    print(" Failed to store extraction results")
                            else:
                                print(" Failed to store model")
                        else:
                            print(" Failed to store paper")
                            
                    except Exception as e:
                        print(f" Error saving to database: {e}")
                        import traceback
                        traceback.print_exc()
                
            except Exception as e:
                print(f"Error reading response: {e}")
    else:
        print(f"\nAnalysis failed after {elapsed_time:.2f} seconds.")


def main():
    """
    Main function to run the test script.
    """
    parser = argparse.ArgumentParser(description="Test the chunked analyser on a scientific publication.")
    parser.add_argument("file_path", help="Path to the markdown file to analyze")
    parser.add_argument("--provider", choices=["deepseek", "gemini"], default="deepseek",
                       help="LLM provider to use")
    parser.add_argument("--api-key", help="API key for the provider")
    parser.add_argument("--max-tokens", type=int, help="Maximum tokens per chunk")
    parser.add_argument("--no-progressive", action="store_true", 
                       help="Disable progressive chunking (don't pass results between chunks)")
    parser.add_argument("--include-references", action="store_true",
                       help="Include References section (excluded by default)")
    parser.add_argument("--exclude-sections", nargs="+", 
                       help="Additional section names to exclude (e.g. Appendix)")
    
    # Database options
    parser.add_argument("--save-to-db", action="store_true",
                       help="Save extraction results to database")
    parser.add_argument("--arxiv-id", help="ArXiv ID of the paper (for database)")
    parser.add_argument("--title", help="Title of the paper (for database)")
    
    args = parser.parse_args()
    
    # Determine which sections to exclude
    exclude_sections = []
    if not args.include_references:
        exclude_sections.append("References")
    if args.exclude_sections:
        exclude_sections.extend(args.exclude_sections)
    
    test_chunked_analysis(
        file_path=args.file_path,
        provider=args.provider,
        api_key=args.api_key,
        max_tokens=args.max_tokens,
        progressive=not args.no_progressive,
        exclude_sections=exclude_sections if exclude_sections else None,
        save_to_db=args.save_to_db,
        arxiv_id=args.arxiv_id,
        title=args.title
    )


if __name__ == "__main__":
    main()