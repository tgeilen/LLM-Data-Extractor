#!/usr/bin/env python3
"""
Test script for the tokenizer module.

This script demonstrates the capabilities of the tokenizer module,
including token counting, document chunking, and cross-provider comparison.
"""

import os
import argparse
import time
from typing import Dict, List, Optional

# Import the tokenizer package
from tokenizer import get_tokenizer, process_file, compare_tokenizers, factory


def test_token_counting(text: str) -> None:
    """
    Test token counting with different providers.
    
    Args:
        text: Text to tokenize
    """
    print("\n=== Testing Token Counting ===")
    
    # Compare token counts across available providers
    token_counts = compare_tokenizers(text)
    
    if not token_counts:
        print("No tokenizers available. Please install required packages.")
        return
    
    # Print results
    print(f"Sample text: {text[:60]}..." if len(text) > 60 else f"Sample text: {text}")
    print("\nToken counts:")
    for model, count in token_counts.items():
        print(f"  {model}: {count} tokens")


def test_document_chunking(file_path: str, providers: List[str]) -> None:
    """
    Test document chunking with different providers.
    
    Args:
        file_path: Path to the markdown file to chunk
        providers: List of providers to test
    """
    print(f"\n=== Testing Document Chunking ===")
    
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return
    
    # Process the file with each provider
    for provider in providers:
        print(f"\nProcessing with {provider} tokenizer:")
        
        start_time = time.time()
        chunk_files = process_file(
            file_path=file_path,
            provider=provider,
            output_dir=f"results/chunked/{provider}"
        )
        elapsed_time = time.time() - start_time
        
        if chunk_files:
            print(f"Successfully chunked into {len(chunk_files)} files in {elapsed_time:.2f} seconds.")
            print(f"Output directory: results/chunked/{provider}/")
        else:
            print(f"Failed to chunk document with {provider} tokenizer.")


def test_performance(text: str, iterations: int = 10) -> None:
    """
    Test tokenizer performance across different providers.
    
    Args:
        text: Text to tokenize
        iterations: Number of iterations for performance testing
    """
    print(f"\n=== Testing Tokenizer Performance ({iterations} iterations) ===")
    
    # Get available tokenizers
    available_tokenizers = {}
    
    if hasattr(factory, 'tokenizers'):
        for provider, models in factory.tokenizers.items():
            for model_name, tokenizer in models.items():
                available_tokenizers[f"{provider}/{model_name}"] = tokenizer
    
    if not available_tokenizers:
        # Try to create tokenizers if none exist yet
        providers = ["deepseek", "gemini"]
        for provider in providers:
            tokenizer = get_tokenizer(provider)
            if tokenizer:
                available_tokenizers[f"{provider}/{tokenizer.model_name}"] = tokenizer
    
    if not available_tokenizers:
        print("No tokenizers available for performance testing.")
        return
    
    # Run performance tests
    results = {}
    for name, tokenizer in available_tokenizers.items():
        print(f"Testing {name}...", end="", flush=True)
        
        start_time = time.time()
        for _ in range(iterations):
            tokenizer.count_tokens(text)
        elapsed_time = time.time() - start_time
        
        avg_time = elapsed_time / iterations
        results[name] = avg_time
        print(f" Average time: {avg_time*1000:.2f} ms")
    
    # Print summary
    if results:
        print("\nPerformance Summary:")
        for name, avg_time in sorted(results.items(), key=lambda x: x[1]):
            print(f"  {name}: {avg_time*1000:.2f} ms per call")


def test_chunking_strategy(text: str, providers: List[str]) -> None:
    """
    Test and compare the chunking strategies of different tokenizers.
    
    Args:
        text: Text to chunk
        providers: List of providers to test
    """
    print("\n=== Testing Chunking Strategy ===")
    
    for provider in providers:
        tokenizer = get_tokenizer(provider)
        if not tokenizer:
            print(f"Tokenizer for {provider} not available.")
            continue
        
        print(f"\nChunking with {provider}/{tokenizer.model_name}:")
        
        # Set a small token limit to force chunking
        chunks = tokenizer.chunk_document(
            text, 
            max_tokens=1000,  # Small limit to force chunking
            overlap_tokens=100
        )
        
        print(f"Generated {len(chunks)} chunks:")
        for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks only
            print(f"  Chunk {i+1}/{len(chunks)}: {chunk['total_tokens']} tokens")
            # Show the first 50 characters of each chunk
            print(f"    {chunk['text'][:50]}...")
        
        if len(chunks) > 3:
            print(f"  ... and {len(chunks) - 3} more chunks")


def main():
    """
    Main function to run the tests.
    """
    parser = argparse.ArgumentParser(description="Test the tokenizer module")
    parser.add_argument("--file", type=str, default="results/2402.07827/2402.07827.md",
                       help="Path to the markdown file to process")
    parser.add_argument("--test", type=str, choices=["all", "count", "chunk", "perf", "strategy"],
                       default="all", help="Test to run")
    args = parser.parse_args()
    
    # Determine available providers
    available_providers = []
    providers_to_check = ["deepseek", "gemini"]
    
    for provider in providers_to_check:
        tokenizer = get_tokenizer(provider)
        if tokenizer:
            available_providers.append(provider)
    
    if not available_providers:
        print("No tokenizer providers available. Please install required packages:")
        print("  - DeepSeek: pip install deepseek_tokenizer")
        print("  - Gemini: pip install google-generativeai")
        return
    
    print(f"Available tokenizer providers: {', '.join(available_providers)}")
    
    # Sample text for testing
    sample_text = """
    This is a sample text to test the tokenizer module. It includes various elements 
    that might affect tokenization, such as numbers (12345), special characters (!@#$%),
    and technical terms like "transformer architecture" and "tokenization".
    
    Some longer words: supercalifragilisticexpialidocious, antidisestablishmentarianism.
    
    Multi-paragraph content is also important to test, as it affects chunking strategies.
    """
    
    # Run the requested tests
    if args.test in ["all", "count"]:
        test_token_counting(sample_text)
    
    if args.test in ["all", "chunk"]:
        test_document_chunking(args.file, available_providers)
    
    if args.test in ["all", "perf"]:
        test_performance(sample_text)
    
    if args.test in ["all", "strategy"]:
        test_chunking_strategy(sample_text, available_providers)


if __name__ == "__main__":
    main() 