"""
DeepSeek tokenizer implementation.

This module provides a concrete implementation of the BaseTokenizer
for DeepSeek models using deepseek-tokenizer library.
"""

from typing import List, Optional

try:
    from deepseek_tokenizer import ds_token
except ImportError:
    raise ImportError(
        "The deepseek_tokenizer package is not installed. "
        "Please install it with `pip install deepseek_tokenizer`"
    )

from tokenizer.base_tokenizer import BaseTokenizer

# Default models and their context sizes
DEEPSEEK_MODELS = {
    "deepseek-chat": 8192,
    "deepseek-coder": 32768,
    "deepseek-llm": 8192
}

class DeepSeekTokenizer(BaseTokenizer):
    """
    DeepSeek tokenizer implementation.
    """
    
    def __init__(self, 
                 model_name: str = "deepseek-chat",
                 max_tokens: Optional[int] = None,
                 overlap_tokens: int = 500,
                 prompt_template_tokens: int = 1000,
                 response_buffer_tokens: int = 1000):
        """
        Initialize the DeepSeek tokenizer.
        
        Args:
            model_name: Name of the DeepSeek model (deepseek-chat, deepseek-coder, etc.)
            max_tokens: Maximum context length for this model (default: based on model name)
            overlap_tokens: Default token overlap between chunks
            prompt_template_tokens: Estimated tokens for prompt template
            response_buffer_tokens: Buffer tokens to leave for response
        """
        # Set max_tokens based on model if not provided
        if max_tokens is None:
            max_tokens = DEEPSEEK_MODELS.get(model_name, 8192)
        
        # Initialize base class
        super().__init__(
            model_name=model_name,
            max_tokens=max_tokens,
            overlap_tokens=overlap_tokens,
            prompt_template_tokens=prompt_template_tokens,
            response_buffer_tokens=response_buffer_tokens
        )
    
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a string using DeepSeek's tokenizer.
        
        Args:
            text: The text to tokenize
            
        Returns:
            The number of tokens in the text
        """
        tokens = ds_token.encode(text)
        return len(tokens)
    
    def encode(self, text: str) -> List[int]:
        """
        Convert text to token IDs using DeepSeek's tokenizer.
        
        Args:
            text: The text to encode
            
        Returns:
            List of token IDs
        """
        return ds_token.encode(text)
    
    def decode(self, tokens: List[int]) -> str:
        """
        Convert token IDs back to text using DeepSeek's tokenizer.
        
        Args:
            tokens: List of token IDs
            
        Returns:
            The decoded text
        """
        return ds_token.decode(tokens)


def main():
    """
    Example usage function to demonstrate the tokenizer's capabilities.
    """
    import os
    
    # Create a DeepSeek tokenizer
    tokenizer = DeepSeekTokenizer(model_name="deepseek-chat")
    
    # Example file path
    file_path = os.path.join("results", "samplePDF", "samplePDF.md")
    
    # Process the file
    tokenizer.process_file(file_path)


if __name__ == "__main__":
    main() 