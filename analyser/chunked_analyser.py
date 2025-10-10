"""
Enhanced analysis module for handling chunked papers with LLMs.

This module extends the base analyser functionality to handle papers that
exceed the token limit of LLMs by:
1. Breaking them into chunks using the tokenizer
2. Processing each chunk separately
3. Combining the results
"""

import os
import json
import re
from typing import List, Dict, Any, Optional, Tuple, Union

# Import tokenizer
from tokenizer import get_tokenizer, factory

# Import base analyser components
from analyser.base_analyser import BaseAnalyser
from analyser.prompt_templates import (
    PUBLICATION_ANALYSIS_TEMPLATE,
    CHUNKED_ANALYSIS_TEMPLATE,
    CHUNKED_ANALYSIS_FINAL_TEMPLATE,
    CHUNKED_PROGRESSIVE_TEMPLATE,
    CHUNKED_PROGRESSIVE_FINAL_TEMPLATE
)
from analyser.utils import read_markdown_file, save_analysis_results, clean_json_response
from analyser.db_integration import extract_json_from_text


class ChunkedAnalyser:
    """
    Wrapper class that extends any BaseAnalyser implementation with chunking capabilities.
    
    This class handles papers that exceed the token limit by:
    1. Breaking them into chunks
    2. Processing each chunk separately
    3. Combining the results
    """
    
    def __init__(self, 
                 base_analyser: BaseAnalyser,
                 provider: str = "auto",
                 max_tokens: Optional[int] = None,
                 overlap_tokens: int = 500,
                 output_dir: str = "results/output",
                 progressive: bool = True,
                 template_module = None):  # NEW: Allow custom template module
        """
        Initialize the chunked analyser.
        
        Args:
            base_analyser: The base analyser to use for LLM queries
            provider: Tokenizer provider to use (auto, deepseek, gemini)
            max_tokens: Maximum tokens per chunk (default: based on provider)
            overlap_tokens: Number of tokens to overlap between chunks
            output_dir: Directory to save results to
            progressive: Whether to use progressive chunking (passing results between chunks)
        """
        self.base_analyser = base_analyser
        self.output_dir = output_dir
        self.progressive = progressive
        self.exclude_sections = None  # Initialize attribute for excluded sections

        print(f"Initializing ChunkedAnalyser with provider: {provider}, max_tokens: {max_tokens}, overlap_tokens: {overlap_tokens}, progressive: {progressive}")

        # Determine the tokenizer provider based on base_analyser if set to auto
        if provider == "auto":
            if "DeepSeek" in base_analyser.__class__.__name__:
                provider = "deepseek"
            elif "Gemini" in base_analyser.__class__.__name__:
                provider = "gemini"
            else:
                # Default to deepseek if unknown
                provider = "deepseek"
        
        # Get tokenizer

        if max_tokens is None:
            # If max_tokens is not specified, break the code to avoid errors
            print(f"Max tokens not specified for {provider} in chunked_analyser.py. Breaking the code to avoid errors.")
            return None
        else :
            print(f"Using max_tokens: {max_tokens} for provider: {provider} in chunked_analyser.py")
         
        self.tokenizer = get_tokenizer(
            provider=provider,
            max_tokens=max_tokens,
            overlap_tokens=overlap_tokens,
            prompt_template_tokens=1000,
            response_buffer_tokens=1000
        )
        
        if not self.tokenizer:
            raise ValueError(f"Failed to create tokenizer for provider: {provider}")
        
        # Import templates from specified module or default
        if template_module is None:
            from analyser.prompt_templates import (
                CHUNKED_ANALYSIS_TEMPLATE,
                CHUNKED_PROGRESSIVE_TEMPLATE, 
                CHUNKED_PROGRESSIVE_FINAL_TEMPLATE,
                CHUNKED_ANALYSIS_FINAL_TEMPLATE
            )
        else:
            CHUNKED_ANALYSIS_TEMPLATE = template_module.CHUNKED_ANALYSIS_TEMPLATE
            CHUNKED_PROGRESSIVE_TEMPLATE = template_module.CHUNKED_PROGRESSIVE_TEMPLATE
            CHUNKED_PROGRESSIVE_FINAL_TEMPLATE = template_module.CHUNKED_PROGRESSIVE_FINAL_TEMPLATE
            CHUNKED_ANALYSIS_FINAL_TEMPLATE = template_module.CHUNKED_ANALYSIS_FINAL_TEMPLATE
        
        # Use the appropriate templates based on progressive setting
        if progressive:
            # Progressive templates that pass results between chunks
            self.prompt_template_first = CHUNKED_ANALYSIS_TEMPLATE  # First chunk doesn't have previous results
            self.prompt_template_middle = CHUNKED_PROGRESSIVE_TEMPLATE
            self.prompt_template_final = CHUNKED_PROGRESSIVE_FINAL_TEMPLATE
        else:
            # Standard templates that don't share results between chunks
            self.prompt_template_first = CHUNKED_ANALYSIS_TEMPLATE
            self.prompt_template_middle = CHUNKED_ANALYSIS_TEMPLATE
            self.prompt_template_final = CHUNKED_ANALYSIS_FINAL_TEMPLATE
    
    def analyze_publication(self, markdown_file: str, arxiv_id: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """
        Analyze a scientific publication in markdown format, handling chunking if needed.
        
        Args:
            markdown_file: Path to the markdown file containing the publication
            arxiv_id: Optional ArXiv ID for unique temporary file naming
            
        Returns:
            Tuple containing paths to the saved text and JSON files (if any)
        """
        # Check if the file exists
        if not os.path.exists(markdown_file):
            print(f"Error: Markdown file not found at {markdown_file}")
            return None, None
        
        # Read the content of the Markdown file
        markdown_content = read_markdown_file(markdown_file)
        if not markdown_content:
            print("No content to process")
            return None, None
        
        # Count tokens to determine if chunking is needed
        token_count = self.tokenizer.count_tokens(markdown_content)
        effective_limit = self.tokenizer.max_tokens - self.tokenizer.prompt_template_tokens - self.tokenizer.response_buffer_tokens
        
        # If the content is small enough, use the base analyser directly
        if token_count <= effective_limit:
            print(f"Content is within token limit ({token_count} tokens). Using direct analysis.")
            return self.base_analyser.analyze_publication(markdown_file)
        
        print(f"Content exceeds token limit ({token_count} tokens). Using chunked analysis.")
        
        # Split the content into chunks, excluding specified sections if any
        chunks = self.tokenizer.chunk_document(
            markdown_content, 
            exclude_sections=self.exclude_sections
        )
        
        # Check if chunking hit the limit (empty chunks indicates failure)
        if not chunks or len(chunks) == 0:
            # If chunking failed or returned no valid chunks, return empty results
            print("ERROR: Document chunking failed or hit chunk count limit. Returning empty results.")
            return None, None
        
        #print max tokens and chunk count for debugging
        print(f"Max tokens per chunk: {self.tokenizer.max_tokens}")
        print(f"Effective limit for content: {effective_limit} tokens")
        print(f"Total tokens in document: {token_count} tokens")
        print(f"Total chunks created: {len(chunks)}")
        
        # Process each chunk, potentially feeding results from one to the next
        chunk_responses = []
        previous_results = None
        processed_previous_results = None
        
        # Constants for retry logic
        MIN_RESPONSE_LENGTH = 100  # Minimum acceptable response length in characters
        MAX_RETRIES = 3  # Maximum number of retry attempts per chunk
        
        for i, chunk in enumerate(chunks):
            print(f"\nProcessing chunk {i+1}/{len(chunks)} ({chunk['total_tokens']} tokens)...")
            
            # Select the appropriate prompt template based on position
            if i == 0:
                prompt_template = self.prompt_template_first
            elif i == len(chunks) - 1:
                prompt_template = self.prompt_template_final
            else:
                prompt_template = self.prompt_template_middle
            
            # Store original prompt template
            original_template = self.base_analyser.prompt_template
            
            # Retry logic for processing this chunk
            retry_count = 0
            success = False
            
            while retry_count < MAX_RETRIES and not success:
                if retry_count > 0:
                    print(f"Retry attempt {retry_count}/{MAX_RETRIES} for chunk {i+1}...")
                
                # Apply previous results to the template if using progressive mode
                if self.progressive and i > 0 and previous_results:
                    # Process the previous results properly based on its structure
                    if processed_previous_results is None:
                        # Convert array to object if necessary
                        if isinstance(previous_results, list) and len(previous_results) > 0:
                            # If it's an array but the template expects an object,
                            # use just the first item if the prompt has "{previous_results}" (not wrapped in [ ])
                            if "{previous_results}" in prompt_template and not "[{previous_results}]" in prompt_template:
                                processed_result = json.dumps(previous_results[0], indent=2)
                                print(f"Converting array of {len(previous_results)} items to single object for prompt template")
                            else:
                                # Otherwise keep it as an array
                                processed_result = json.dumps(previous_results, indent=2)
                        elif isinstance(previous_results, dict):
                            # If it's already an object, keep it that way
                            processed_result = json.dumps(previous_results, indent=2)
                        else:
                            # If it's something else, just convert to string and hope for the best
                            processed_result = json.dumps(previous_results, indent=2)
                        
                        processed_previous_results = processed_result
                    
                    # Use the processed results
                    prompt_template = prompt_template.replace("{previous_results}", processed_previous_results)
                elif self.progressive and "{previous_results}" in prompt_template:
                    # If no previous results yet, use empty array or object depending on template
                    if "[{previous_results}]" in prompt_template:
                        prompt_template = prompt_template.replace("{previous_results}", "[]")
                    else:
                        prompt_template = prompt_template.replace("{previous_results}", "{}")
                
                # Override prompt template temporarily
                self.base_analyser.prompt_template = prompt_template
                
                # Create a temporary file for this chunk
                chunk_file = self._save_temp_chunk(chunk['text'], i+1, arxiv_id)
                
                # Process this chunk
                try:
                    # Print a portion of the prompt for debugging
                    prompt_start = prompt_template[:500] + "..." if len(prompt_template) > 500 else prompt_template
                    #print(f"Prompt template starts with: {prompt_start}")
                    
                    #print(f"DEBUG: chunked_analyser - About to call base_analyser.analyze_publication for chunk {i+1}")
                    text_file, chunk_json_file = self.base_analyser.analyze_publication(chunk_file)
                    #print(f"DEBUG: chunked_analyser - base_analyser returned: text_file={text_file}, json_file={chunk_json_file}")
                    
                    # Check if we have a valid JSON response
                    if chunk_json_file and os.path.exists(chunk_json_file):
                        #print(f"DEBUG: chunked_analyser - Reading JSON file: {chunk_json_file}")
                        # Read the raw response directly
                        with open(chunk_json_file, 'r', encoding='utf-8') as f:
                            raw_response = f.read()
                            #print(f"DEBUG: chunked_analyser - Raw response length: {len(raw_response)} characters")
                            #print(f"DEBUG: chunked_analyser - Raw response first 100 chars: {repr(raw_response[:100])}")
                            
                            # Check if response is too short
                            if len(raw_response) < MIN_RESPONSE_LENGTH:
                                #print(f"Response too short ({len(raw_response)} chars). Minimum is {MIN_RESPONSE_LENGTH}.")
                                retry_count += 1
                                continue
                            
                            # Valid response, parse and store it
                            try:
                                #print(f"DEBUG: chunked_analyser - Attempting to parse JSON...")
                                chunk_response = extract_json_from_text(raw_response)
                                
                                if chunk_response is not None:
                                    #print(f"DEBUG: chunked_analyser - JSON parsing SUCCESS. Type: {type(chunk_response)}")
                                    if isinstance(chunk_response, list):
                                        #print(f"DEBUG: chunked_analyser - Parsed as list with {len(chunk_response)} items")
                                        pass
                                    elif isinstance(chunk_response, dict):
                                        #print(f"DEBUG: chunked_analyser - Parsed as dict with {len(chunk_response)} keys")
                                        pass

                                    # In progressive mode, store response for the next chunk
                                    if self.progressive:
                                        previous_results = chunk_response
                                        #print(f"DEBUG: chunked_analyser - Stored results for next chunk (progressive mode)")
                                        # Reset processed results so it will be recalculated for next chunk
                                        processed_previous_results = None
                                    
                                    # Always save for final combination
                                    chunk_responses.append(chunk_response)
                                    #print(f"DEBUG: chunked_analyser - Added response to chunk_responses list. Total chunks processed: {len(chunk_responses)}")
                                    success = True
                                else:
                                    #print(f"DEBUG: chunked_analyser - JSON parsing FAILED: extract_json_from_text returned None")
                                    #print(f"DEBUG: chunked_analyser - Raw response that failed: {repr(raw_response[:200])}...")
                                    retry_count += 1
                                    continue
                            except Exception as e:
                                #print(f"DEBUG: chunked_analyser - JSON parsing FAILED: {e}")
                                #print(f"DEBUG: chunked_analyser - Raw response that failed: {repr(raw_response[:200])}...")
                                retry_count += 1
                                continue

                    else:
                        #print(f"DEBUG: chunked_analyser - No JSON response file or file doesn't exist")
                        retry_count += 1
                        continue
                    
                    # If we have a text file, we can also read that for debugging
                    if text_file and os.path.exists(text_file):
                        with open(text_file, 'r', encoding='utf-8') as f:
                            text_response = f.read()
                           #print(f"DEBUG: chunked_analyser - Text response length: {len(text_response)} characters")

                except Exception as e:
                    #print(f"DEBUG: chunked_analyser - Error processing chunk {i+1}: {e}")
                    import traceback
                    traceback.print_exc()
                    retry_count += 1
                    continue
                finally:
                    # Remove temporary chunk file
                    if os.path.exists(chunk_file):
                        os.remove(chunk_file)
                    
                    # Restore original prompt template
                    self.base_analyser.prompt_template = original_template
            
            # Check if we had a successful response after retries
            if not success:
                print(f"Failed to get valid response for chunk {i+1} after {MAX_RETRIES} attempts. Skipping chunk.")
                # Continue with next chunk
                continue
        
        print(f"DEBUG: chunked_analyser - Finished processing all chunks. Total successful responses: {len(chunk_responses)}")
        
        # In progressive mode, the last response is already our combined response
        if self.progressive and chunk_responses:
            final_response = chunk_responses[-1]
            print(f"DEBUG: chunked_analyser - Using progressive final response (last chunk)")
            print(f"DEBUG: chunked_analyser - Final response type: {type(final_response)}")
        # Otherwise combine responses from all chunks
        elif chunk_responses:
            print(f"DEBUG: chunked_analyser - Combining responses from {len(chunk_responses)} chunks")
            final_response = self._combine_chunk_responses(chunk_responses)
            print(f"DEBUG: chunked_analyser - Combined response type: {type(final_response)}")
        else:
            print("DEBUG: chunked_analyser - No valid responses received from any chunk.")
            return None, None
        
        # Save final results
        base_filename = os.path.basename(markdown_file).split('.')[0]
        print(f"DEBUG: chunked_analyser - Saving final results with base filename: {base_filename}")
        print(f"DEBUG: chunked_analyser - Final response before saving: {type(final_response)}")
        if isinstance(final_response, list):
            print(f"DEBUG: chunked_analyser - Final response is list with {len(final_response)} items")
        elif isinstance(final_response, dict):
            print(f"DEBUG: chunked_analyser - Final response is dict with {len(final_response)} keys")
        
        text_file, json_file = save_analysis_results(
            json.dumps(final_response, indent=2),
            self.output_dir,
            f"{base_filename}_{'progressive' if self.progressive else 'combined'}"
        )
        
        print(f"DEBUG: chunked_analyser - Final response saved to: {json_file}")
        return text_file, json_file
    
    def _save_temp_chunk(self, chunk_text: str, chunk_index: int, arxiv_id: Optional[str] = None) -> str:
        """
        Save a chunk to a temporary file with unique naming to avoid parallel processing collisions.
        
        Args:
            chunk_text: The chunk text
            chunk_index: The chunk index
            arxiv_id: Optional ArXiv ID for unique naming
            
        Returns:
            Path to the temporary file
        """
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create unique filename using arxiv_id if available, otherwise fallback to timestamp
        if arxiv_id:
            # Clean arxiv_id for filename usage (replace problematic characters)
            clean_arxiv_id = re.sub(r'[^\w\-_.]', '_', arxiv_id)
            temp_filename = f"temp_chunk_{clean_arxiv_id}_{chunk_index}.md"
        else:
            # Fallback to timestamp-based naming for uniqueness
            import time
            timestamp = int(time.time() * 1000)  # millisecond precision
            temp_filename = f"temp_chunk_{timestamp}_{chunk_index}.md"
        
        temp_file = os.path.join(self.output_dir, temp_filename)
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(chunk_text)
        
        return temp_file
    
    def _combine_chunk_responses(self, chunk_responses: List[Any]) -> Dict[str, Any]:
        """
        Combine responses from multiple chunks into a single coherent response.
        
        Args:
            chunk_responses: List of responses from each chunk
            
        Returns:
            Combined response as a dictionary
        """
        if not chunk_responses:
            return {}
        
        # This is a simplified combination strategy:
        # For multiple model variants, we collect all distinct models
        # For overlapping/duplicate models, we take the version with the highest confidence
        
        # First, collect all model variants by name
        all_models: Dict[str, List[Dict]] = {}
        
        for response in chunk_responses:
            # Each response is a list of model objects
            if isinstance(response, list):
                for model_obj in response:
                    if isinstance(model_obj, dict) and "model_name" in model_obj:
                        model_name = model_obj["model_name"]["value"]
                        if model_name == "n/a":
                            continue
                            
                        if model_name not in all_models:
                            all_models[model_name] = []
                        
                        all_models[model_name].append(model_obj)
        
        # Now combine information for each model variant
        combined_models = []
        
        for model_name, model_versions in all_models.items():
            # Start with the first version
            combined_model = model_versions[0].copy()
            
            # For each field, find the version with the highest confidence
            for field in combined_model:
                if field == "model_name":
                    continue  # Skip, we already know the model name
                
                highest_confidence = int(combined_model[field]["confidence"])
                best_version = combined_model[field]
                
                # Check all other versions
                for model in model_versions[1:]:
                    if field in model:
                        confidence = int(model[field]["confidence"])
                        # If this version has higher confidence, use it
                        if confidence > highest_confidence:
                            highest_confidence = confidence
                            best_version = model[field]
                
                # Use the best version for this field
                combined_model[field] = best_version
            
            combined_models.append(combined_model)
        
        return combined_models
    
    def _identify_model_variants(self, content: str) -> List[str]:
        """
        Identify model variants mentioned in the content.
        
        Args:
            content: The publication content
            
        Returns:
            List of identified model variants
        """
        # Simple regex pattern to identify model variants
        # This could be improved with more sophisticated NLP techniques
        patterns = [
            r'([A-Z][A-Za-z0-9]+-[A-Za-z0-9]+)',  # e.g. "GPT-4", "BERT-large"
            r'([A-Z][A-Za-z0-9]+\s+[A-Za-z0-9]+)',  # e.g. "BERT Base"
            r'([A-Z][A-Za-z0-9]+ [Ss]mall)',
            r'([A-Z][A-Za-z0-9]+ [Bb]ase)',
            r'([A-Z][A-Za-z0-9]+ [Ll]arge)',
            r'([A-Z][A-Za-z0-9]+ [Xx][Ll])',
            r'([A-Z][A-Za-z0-9]+-[0-9]+[Bb])',  # e.g. "GPT-175B"
        ]
        
        variants = set()
        for pattern in patterns:
            matches = re.findall(pattern, content)
            variants.update(matches)
        
        return list(variants)


def create_chunked_analyser(
    base_analyser: BaseAnalyser,
    provider: str = "auto",
    max_tokens: Optional[int] = None,
    progressive: bool = True,
    template_module = None  # NEW: Allow custom template module
) -> ChunkedAnalyser:
    """
    Factory function to create a chunked analyser from a base analyser.
    
    Args:
        base_analyser: The base analyser to extend
        provider: Tokenizer provider to use
        max_tokens: Maximum tokens per chunk
        progressive: Whether to use progressive chunking (passing results between chunks)
        
    Returns:
        A chunked analyser instance
    """
    print(f"Creating ChunkedAnalyser with provider: {provider}, max_tokens: {max_tokens}, progressive: {progressive}")
   
    return ChunkedAnalyser(
        base_analyser=base_analyser,
        provider=provider,
        max_tokens=max_tokens,
        progressive=progressive,
        template_module=template_module
    )