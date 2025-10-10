#!/usr/bin/env python3
"""
Simple example showing direct tokenizer usage for counting tokens.
"""

import os

def count_tokens_simple(file_path: str):
    """
    Simple token counting using DeepSeek or Gemini tokenizer (OpenAI removed).
    This is the most straightforward approach.
    """
    
    # Read the file
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return None
    
    # Try to use DeepSeek tokenizer first (most reliable for coding)
    try:
        from .deepseek_tokenizer_impl import DeepSeekTokenizer
        tokenizer = DeepSeekTokenizer(model_name="deepseek-chat", max_tokens=8192)
        token_count = tokenizer.count_tokens(text)
        
        print(f"File: {file_path}")
        print(f"Characters: {len(text):,}")
        print(f"Tokens (DeepSeek): {token_count:,}")
        return token_count
        
    except ImportError:
        print("DeepSeek tokenizer not available.")
        
        # Fallback: rough estimation (4 characters ≈ 1 token)
        estimated_tokens = len(text) // 4
        print(f"File: {file_path}")
        print(f"Characters: {len(text):,}")
        print(f"Estimated tokens (rough): {estimated_tokens:,}")
        return estimated_tokens

def count_tokens_with_deepseek(file_path: str):
    """
    Count tokens using DeepSeek tokenizer.
    """
    try:
        from .deepseek_tokenizer_impl import DeepSeekTokenizer
        
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        
        # Create tokenizer
        tokenizer = DeepSeekTokenizer(model_name="deepseek-chat", max_tokens=8192)
        token_count = tokenizer.count_tokens(text)
        
        print(f"File: {file_path}")
        print(f"Characters: {len(text):,}")
        print(f"Tokens (DeepSeek): {token_count:,}")
        return token_count
        
    except ImportError:
        print("DeepSeek tokenizer not available.")
        return None

def main():
    # Change this to your file path
    file_path = "samplePDF.md"
    
    if not os.path.exists(file_path):
        print(f"File {file_path} not found. Please update the file_path variable.")
        return
    
    print("=== Simple Token Counting ===")
    count_tokens_simple(file_path)
    
    print("\n=== DeepSeek Token Counting ===")
    count_tokens_with_deepseek(file_path)

if __name__ == "__main__":
    main()
