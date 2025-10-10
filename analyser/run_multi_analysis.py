#!/usr/bin/env python3
"""
Run multiple analyses on the same paper using different models.
"""

import os
import argparse
import json
from dotenv import load_dotenv

# Import the analyzers
from .base_analyser import BaseAnalyser
from .deepseek_analyser import DeepSeekAnalyser
from .gemini_analyser import GeminiAnalyser
from .chunked_analyser import create_chunked_analyser

# Import the tokenizer
from ..tokenizer import get_tokenizer

# Import database utilities
from ..db.db_utils import create_schema
from ..db.paper_dao import PaperDAO
from ..db.model_dao import ModelDAO
from ..db.extraction_dao import ExtractionDAO
from .db_integration import store_paper_from_md_file, analyze_and_store

# Load environment variables
load_dotenv()

def run_analysis_with_model(analyzer_class, md_file_path, model_name, provider, version=None,
                           runs=1, temperature=None, context_size=None, use_chunking=True, 
                           progressive_chunking=True):
    """
    Run analysis with a specific model multiple times
    
    Args:
        analyzer_class: Analyzer class to instantiate
        md_file_path: Path to the markdown file
        model_name: Name of the model
        provider: Provider of the model
        version: Version of the model (optional)
        runs: Number of runs to perform (default: 1)
        temperature: Temperature to use (optional)
        context_size: Context size in tokens (optional)
        use_chunking: Whether to use chunking for large files (default: True)
        progressive_chunking: Whether to use progressive chunking (passing results between chunks)
        
    Returns:
        A list of run IDs
    """
    # Get the paper ID or add it if not exists
    paper_id = store_paper_from_md_file(md_file_path)
    if not paper_id:
        print(f"Error: Could not store paper from {md_file_path}")
        return []
    
    # Get or add the model
    model = ModelDAO.get_model_by_name_provider(model_name, provider, version)
    if model:
        model_id = model['id']
    else:
        model_id = ModelDAO.insert_model(model_name, provider, context_size, version)
    
    # Initialize analyzer based on class
    if analyzer_class == DeepSeekAnalyser:
        api_token = os.environ.get("DEEPSEEK_API_TOKEN")
        if not api_token:
            print("Error: DEEPSEEK_API_TOKEN environment variable not set")
            return []
        base_analyzer = analyzer_class(api_token=api_token, model=model_name)
        tokenizer_provider = "deepseek"
    elif analyzer_class == GeminiAnalyser:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("Error: GEMINI_API_KEY environment variable not set")
            return []
        base_analyzer = analyzer_class(api_key=api_key, model=model_name)
        tokenizer_provider = "gemini"
    else:
        print(f"Error: Unsupported analyzer class: {analyzer_class.__name__}")
        return []
    
    # Check if we need chunking
    needs_chunking = False
    if use_chunking:
        try:
            # Get tokenizer and count tokens
            tokenizer = get_tokenizer(tokenizer_provider)
            if tokenizer:
                with open(md_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                token_count = tokenizer.count_tokens(content)
                effective_limit = tokenizer.max_tokens - tokenizer.prompt_template_tokens - tokenizer.response_buffer_tokens
                
                if token_count > effective_limit:
                    needs_chunking = True
                    chunking_mode = "progressive" if progressive_chunking else "standard"
                    print(f"File has {token_count} tokens, exceeding the {effective_limit} token limit. Using {chunking_mode} chunked analysis.")
                else:
                    print(f"File has {token_count} tokens, within the {effective_limit} token limit. Using direct analysis.")
        except Exception as e:
            print(f"Error checking token count: {e}")
            # If we can't check tokens, assume direct analysis
    
    # Wrap with chunked analyzer if needed
    if needs_chunking:
        analyzer = create_chunked_analyser(
            base_analyser=base_analyzer,
            provider=tokenizer_provider,
            max_tokens=context_size,
            progressive=progressive_chunking
        )
        print(f"Created chunked analyzer for {provider} {model_name}")
    else:
        analyzer = base_analyzer
    
    # Perform multiple runs
    all_run_ids = []
    for i in range(runs):
        print(f"\nRunning analysis {i+1}/{runs} with {provider} {model_name}...")
        
        # Set temperature for this run (vary it slightly if multiple runs)
        current_temp = temperature
        if temperature is not None and runs > 1:
            current_temp = temperature + (i * 0.05)  # Slight variation
            print(f"Using temperature: {current_temp}")
        
        # Run the analysis - now returns a list of run_ids (one per model)
        paper_id, model_id, run_ids = analyze_and_store(
            analyzer, md_file_path, model_name, provider, version,
            temperature=current_temp, context_size=context_size
        )
        
        if run_ids:
            # Add all run IDs to our list
            for j, run_id in enumerate(run_ids):
                all_run_ids.append(run_id)
                print(f"Analysis run {i+1}, model {j+1} complete. Run ID: {run_id}")
        else:
            print(f"Analysis run {i+1} failed.")
    
    return all_run_ids

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run multiple LLM analyses on a paper")
    parser.add_argument("file_path", help="Path to the markdown file to analyze")
    parser.add_argument("--deepseek-runs", type=int, default=0, help="Number of DeepSeek runs")
    parser.add_argument("--gemini-runs", type=int, default=0, help="Number of Gemini runs")
    parser.add_argument("--temperature", type=float, default=0.2, help="Base temperature to use")
    parser.add_argument("--no-chunking", action="store_true", help="Disable chunking for large files")
    parser.add_argument("--no-progressive", action="store_true", 
                        help="Disable progressive chunking (don't pass results between chunks)")
    args = parser.parse_args()
    
    # Make sure database schema exists
    create_schema()
    
    # Get or store the paper
    paper_id = store_paper_from_md_file(args.file_path)
    if not paper_id:
        print(f"Error: Could not store paper from {args.file_path}")
        return
    
    paper = PaperDAO.get_paper_by_id(paper_id)
    print(f"Analyzing paper: {paper['title']} (ID: {paper_id})")
    
    # Track all run IDs
    all_run_ids = []
    
    # Run analyses with DeepSeek
    if args.deepseek_runs > 0:
        print(f"\nRunning {args.deepseek_runs} DeepSeek analyses...")
        deepseek_run_ids = run_analysis_with_model(
            DeepSeekAnalyser,
            args.file_path,
            "deepseek-chat",
            "DeepSeek",
            runs=args.deepseek_runs,
            temperature=args.temperature,
            use_chunking=not args.no_chunking,
            progressive_chunking=not args.no_progressive
        )
        all_run_ids.extend(deepseek_run_ids)
        print(f"Completed {len(deepseek_run_ids)} DeepSeek extractions")
    
    # Run analyses with Gemini
    if args.gemini_runs > 0:
        print(f"\nRunning {args.gemini_runs} Gemini analyses...")
        gemini_run_ids = run_analysis_with_model(
            GeminiAnalyser,
            args.file_path,
            "gemini-pro",
            "Google",
            runs=args.gemini_runs,
            temperature=args.temperature,
            use_chunking=not args.no_chunking,
            progressive_chunking=not args.no_progressive
        )
        all_run_ids.extend(gemini_run_ids)
        print(f"Completed {len(gemini_run_ids)} Gemini extractions")
    
    return all_run_ids

if __name__ == "__main__":
    main() 