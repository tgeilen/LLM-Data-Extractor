#!/usr/bin/env python3
"""
Example script showing how to count tokens in a file using the tokenizer system.
"""

import os
from . import get_tokenizer

def count_tokens_in_file(file_path: str, provider: str = "deepseek", model_name: str = None):
    """
    Count tokens in a file using the specified tokenizer.
    
    Args:
        file_path: Path to the file to analyze
        provider: Tokenizer provider ("deepseek", "gemini")
        model_name: Specific model name (optional)
    
    Returns:
        Number of tokens in the file
    """
    
    # Read the file
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None
    
    # Get the appropriate tokenizer
    # For DeepSeek, you need to specify max_tokens
    if provider == "deepseek":
        tokenizer = get_tokenizer(provider, model_name=model_name, max_tokens=8192)
    elif provider == "gemini":
        tokenizer = get_tokenizer(provider, model_name=model_name or "gemini-pro", max_tokens=32000)
    else:
        available_providers = ["deepseek", "gemini"]
        print(f"Unsupported provider: {provider}. Available: {available_providers}")
        return None
    
    if not tokenizer:
        print(f"Failed to create tokenizer for provider: {provider}")
        return None
    
    # Count tokens
    token_count = tokenizer.count_tokens(text)
    
    print(f"File: {file_path}")
    print(f"Provider: {provider} ({tokenizer.model_name})")
    print(f"Character count: {len(text):,}")
    print(f"Token count: {token_count:,}")
    
    return token_count

def compare_tokenizers_for_file(file_path: str):
    """
    Compare token counts across different providers for the same file.
    """
    from . import compare_tokenizers
    
    # Read the file
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return
    
    print(f"Comparing tokenizers for file: {file_path}")
    print(f"Character count: {len(text):,}")
    print("\nToken counts by provider:")
    
    # Compare across all available tokenizers
    token_counts = compare_tokenizers(text)
    
    for model, count in token_counts.items():
        print(f"  {model}: {count:,} tokens")

def main():
    """
    Example usage
    """
    # Example file path - modify this to point to your file
    file_path = "modelOutput.md"  # Change this to your file path
    
    if not os.path.exists(file_path):
        print(f"Example file {file_path} not found.")
        print("Please modify the file_path variable to point to your file.")
        return
    
    # Method 1: Count with a specific provider
    print("=== Method 1: Specific Provider ===")
    count_tokens_in_file(file_path, provider="deepseek")
    
    print("\n" + "="*50 + "\n")
    
    # Method 2: Compare across all providers
    print("=== Method 2: Compare All Providers ===")
    compare_tokenizers_for_file(file_path)

if __name__ == "__main__":
    main()
