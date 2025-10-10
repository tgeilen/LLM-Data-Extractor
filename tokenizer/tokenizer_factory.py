"""
Tokenizer factory for creating tokenizers for different LLM providers.

This module provides a unified interface for creating and managing
tokenizers for different LLM providers, with configuration options
for each provider's tokenizer.
"""

from typing import Dict, Optional, List, Any, Union

from tokenizer.base_tokenizer import BaseTokenizer

# Import tokenizer implementations
try:
    from tokenizer.deepseek_tokenizer_impl import DeepSeekTokenizer
    DEEPSEEK_AVAILABLE = True
except ImportError:
    DEEPSEEK_AVAILABLE = False


try:
    from tokenizer.gemini_tokenizer_impl import GeminiTokenizer
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class TokenizerFactory:
    """
    Factory class for creating and managing tokenizers.
    """
    
    def __init__(self):
        """
        Initialize the TokenizerFactory.
        """
        # Dictionary to store tokenizer instances by provider and model
        self.tokenizers: Dict[str, Dict[str, BaseTokenizer]] = {}
    
    def get_tokenizer(self, 
                     provider: str, 
                     model_name: Optional[str] = None,
                     max_tokens: Optional[int] = None,
                     overlap_tokens: int = 500,
                     prompt_template_tokens: int = 1000,
                     response_buffer_tokens: int = 1000,
                     api_key: Optional[str] = None,
                     **kwargs) -> Optional[BaseTokenizer]:
        """
        Get a tokenizer instance for the given provider and model.
        
        Args:
            provider: The provider name (deepseek, gemini, etc.)
            model_name: The model name
            max_tokens: Maximum context length for this model
            overlap_tokens: Default token overlap between chunks
            prompt_template_tokens: Estimated tokens for prompt template
            response_buffer_tokens: Buffer tokens to leave for response
            api_key: API key for the provider (for some providers)
            **kwargs: Additional provider-specific parameters
            
        Returns:
            A tokenizer instance or None if provider is not supported
        """
        provider = provider.lower()

        #print parameters for debugging
        print(f"Creating tokenizer for provider in tokenizer_factory.py: {provider}, model: {model_name}, max_tokens: {max_tokens}, "
              f"overlap_tokens: {overlap_tokens}, prompt_template_tokens: {prompt_template_tokens}, "
              f"response_buffer_tokens: {response_buffer_tokens}, api_key: {api_key}")
        
        # Use default model name if not provided
        if model_name is None:
            model_name = self._get_default_model_for_provider(provider)
        
        # Check if tokenizer for this provider and model already exists
        if provider in self.tokenizers and model_name in self.tokenizers[provider]:
            return self.tokenizers[provider][model_name]
        
        # Create new tokenizer based on provider
        if not max_tokens:
            # If max_tokens is not specified, break the code to avoid errors
            print(f"Max tokens not specified for {provider} in tokenizer_factory.py. Breaking the code to avoid errors.")
            return None
        else:
            print(f"Using max_tokens: {max_tokens} for provider: {provider} in tokenizer_factory.py")
        
        tokenizer = self._create_tokenizer(
            provider=provider,
            model_name=model_name,
            max_tokens=max_tokens,
            overlap_tokens=overlap_tokens,
            prompt_template_tokens=prompt_template_tokens,
            response_buffer_tokens=response_buffer_tokens,
            api_key=api_key,
            **kwargs
        )
        
        # Store tokenizer if created successfully
        if tokenizer:
            if provider not in self.tokenizers:
                self.tokenizers[provider] = {}
            self.tokenizers[provider][model_name] = tokenizer
        
        return tokenizer
    
    def _create_tokenizer(self, 
                         provider: str, 
                         model_name: str,
                         max_tokens: Optional[int],
                         overlap_tokens: int,
                         prompt_template_tokens: int,
                         response_buffer_tokens: int,
                         api_key: Optional[str],
                         **kwargs) -> Optional[BaseTokenizer]:
        """
        Create a new tokenizer instance.
        
        Args:
            provider: The provider name
            model_name: The model name
            max_tokens: Maximum context length for this model
            overlap_tokens: Default token overlap between chunks
            prompt_template_tokens: Estimated tokens for prompt template
            response_buffer_tokens: Buffer tokens to leave for response
            api_key: API key for the provider (for some providers)
            **kwargs: Additional provider-specific parameters
            
        Returns:
            A tokenizer instance or None if provider is not supported
        """
        # Create tokenizer based on provider
        if provider == "deepseek":
            if not DEEPSEEK_AVAILABLE:
                print("DeepSeek tokenizer not available. Please install the deepseek_tokenizer package.")
                return None
            
            if max_tokens is None:
                print("Max tokens not specified for DeepSeek in tokenizer_factory.py. Breaking the code to avoid errors.")
                return None
            
            return DeepSeekTokenizer(
                model_name=model_name,
                max_tokens=max_tokens,
                overlap_tokens=overlap_tokens,
                prompt_template_tokens=prompt_template_tokens,
                response_buffer_tokens=response_buffer_tokens
            )
        
        elif provider == "gemini" or provider == "google":
            if not GEMINI_AVAILABLE:
                print("Gemini tokenizer not available.")
                return None
            
            return GeminiTokenizer(
                model_name=model_name,
                max_tokens=max_tokens,
                overlap_tokens=overlap_tokens,
                prompt_template_tokens=prompt_template_tokens,
                response_buffer_tokens=response_buffer_tokens,
                api_key=api_key
            )
        
        else:
            available_providers = ["deepseek", "gemini"]
            print(f"Unsupported provider: {provider}. Available: {available_providers}")
            return None
    
    def _get_default_model_for_provider(self, provider: str) -> str:
        """
        Get the default model name for a provider.
        
        Args:
            provider: The provider name
            
        Returns:
            The default model name for the provider
        """
        defaults = {
            "deepseek": "deepseek-chat",
            "gemini": "gemini-pro",
            "google": "gemini-pro"
        }
        
        return defaults.get(provider, "")
    
    def process_file(self, 
                    file_path: str,
                    provider: str,
                    model_name: Optional[str] = None,
                    output_dir: str = "results/chunked",
                    max_tokens: Optional[int] = None,
                    overlap_tokens: Optional[int] = None,
                    api_key: Optional[str] = None,
                    **kwargs) -> List[str]:
        """
        Process a markdown file using the appropriate tokenizer.
        
        Args:
            file_path: Path to the markdown file
            provider: The provider name
            model_name: The model name (optional)
            output_dir: Directory to save chunks to
            max_tokens: Maximum tokens per chunk
            overlap_tokens: Number of tokens to overlap between chunks
            api_key: API key for the provider (for some providers)
            **kwargs: Additional provider-specific parameters
            
        Returns:
            List of saved file paths
        """
        # Get the appropriate tokenizer
        tokenizer = self.get_tokenizer(
            provider=provider,
            model_name=model_name,
            max_tokens=max_tokens,
            api_key=api_key,
            **kwargs
        )
        
        if not tokenizer:
            print(f"Failed to create tokenizer for provider: {provider}")
            return []
        
        # Process the file
        return tokenizer.process_file(
            file_path=file_path,
            output_dir=output_dir,
            max_tokens=max_tokens,
            overlap_tokens=overlap_tokens
        )
    
    def compare_tokenizers(self, text: str) -> Dict[str, int]:
        """
        Compare token counts across different tokenizers.
        
        Args:
            text: The text to tokenize
            
        Returns:
            Dictionary of provider/model to token count
        """
        results = {}
        
        # Try each available tokenizer
        if DEEPSEEK_AVAILABLE:
            tokenizer = self.get_tokenizer("deepseek")
            if tokenizer:
                results[f"deepseek/{tokenizer.model_name}"] = tokenizer.count_tokens(text)
        
        if GEMINI_AVAILABLE:
            tokenizer = self.get_tokenizer("gemini")
            if tokenizer:
                results[f"gemini/{tokenizer.model_name}"] = tokenizer.count_tokens(text)
        
        return results


# Create a singleton instance
factory = TokenizerFactory()


def get_tokenizer(*args, **kwargs) -> Optional[BaseTokenizer]:
    """
    Convenience function to get a tokenizer from the factory.
    
    Args:
        *args: Positional arguments to pass to TokenizerFactory.get_tokenizer
        **kwargs: Keyword arguments to pass to TokenizerFactory.get_tokenizer
        
    Returns:
        A tokenizer instance or None if provider is not supported
    """
    return factory.get_tokenizer(*args, **kwargs)


def process_file(*args, **kwargs) -> List[str]:
    """
    Convenience function to process a file using the appropriate tokenizer.
    
    Args:
        *args: Positional arguments to pass to TokenizerFactory.process_file
        **kwargs: Keyword arguments to pass to TokenizerFactory.process_file
        
    Returns:
        List of saved file paths
    """
    return factory.process_file(*args, **kwargs)


def compare_tokenizers(text: str) -> Dict[str, int]:
    """
    Convenience function to compare token counts across different tokenizers.
    
    Args:
        text: The text to tokenize
        
    Returns:
        Dictionary of provider/model to token count
    """
    return factory.compare_tokenizers(text)


def main():
    """
    Example usage function to demonstrate the factory's capabilities.
    """
    import os
    
    # Example file path
    file_path = os.path.join("results", "samplePDF", "samplePDF.md")
    
    # Process with different tokenizers
    providers = []
    
    if DEEPSEEK_AVAILABLE:
        providers.append("deepseek")
    
    if GEMINI_AVAILABLE:
        providers.append("gemini")
    
    for provider in providers:
        print(f"\nProcessing with {provider} tokenizer:")
        process_file(file_path, provider)
    
    # Compare tokenizers on a sample text
    sample_text = """
    This is a sample text to compare tokenization across different LLM providers.
    It includes some technical terms like 'transformer architecture' and 'tokenization'.
    Also some numbers: 12345 and special characters: !@#$%.
    """
    
    print("\nComparing tokenizers:")
    token_counts = compare_tokenizers(sample_text)
    
    for model, count in token_counts.items():
        print(f"{model}: {count} tokens")


if __name__ == "__main__":
    main() 