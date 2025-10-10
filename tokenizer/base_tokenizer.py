"""
Base tokenizer module with abstract classes for document chunking.

This module provides a base tokenizer class that can be extended
for different LLM providers, ensuring consistent chunking behavior
across different tokenizers.
"""

import os
import re
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#logger = logging.getLogger(__name__)

class BaseTokenizer(ABC):
    """
    Abstract base class for tokenizers.
    
    Classes that extend this must implement:
    - count_tokens: Count tokens in text using model-specific tokenizer
    - encode: Convert text to token IDs
    - decode: Convert token IDs back to text
    """
    
    def __init__(self, 
                 model_name: str,
                 max_tokens: int = 8192,
                 overlap_tokens: int = 500,
                 prompt_template_tokens: int = 1000,
                 response_buffer_tokens: int = 1000):
        """
        Initialize the base tokenizer.
        
        Args:
            model_name: Name of the model this tokenizer is for
            max_tokens: Maximum context length for this model
            overlap_tokens: Default token overlap between chunks
            prompt_template_tokens: Estimated tokens for prompt template
            response_buffer_tokens: Buffer tokens to leave for response
        """
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.prompt_template_tokens = prompt_template_tokens
        self.response_buffer_tokens = response_buffer_tokens

        print(f"Initializing {self.__class__.__name__} for model '{self.model_name}'")
        print(f"Max tokens set in initialization: {self.max_tokens}, Overlap tokens: {self.overlap_tokens}")

        # Effective token limit (context size minus prompt and response space)
        self.effective_token_limit = max_tokens - prompt_template_tokens - response_buffer_tokens
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a string.
        
        Args:
            text: The text to tokenize
            
        Returns:
            The number of tokens in the text
        """
        pass
    
    @abstractmethod
    def encode(self, text: str) -> List[int]:
        """
        Convert text to token IDs.
        
        Args:
            text: The text to encode
            
        Returns:
            List of token IDs
        """
        pass
    
    @abstractmethod
    def decode(self, tokens: List[int]) -> str:
        """
        Convert token IDs back to text.
        
        Args:
            tokens: List of token IDs
            
        Returns:
            The decoded text
        """
        pass
    
    def get_section_boundaries(self, markdown_text: str) -> List[Tuple[int, int, str]]:
        """
        Find the boundary indices for sections in a markdown document.
        
        Args:
            markdown_text: The markdown text to analyze
            
        Returns:
            List of tuples (start_idx, end_idx, heading) for each section
        """
        # Pattern to match markdown headings (# through ######)
        heading_pattern = re.compile(r'^(#{1,6})\s+(.+?)(?:\s+#+)?$', re.MULTILINE)
        
        # Find all headings
        headings = list(heading_pattern.finditer(markdown_text))
        
        # Create sections based on heading positions
        boundaries = []
        
        for i in range(len(headings)):
            start_idx = headings[i].start()
            heading_text = headings[i].group(2).strip()
            
            # If this is the last heading, the section ends at the end of the document
            if i == len(headings) - 1:
                end_idx = len(markdown_text)
            else:
                end_idx = headings[i + 1].start()
            
            boundaries.append((start_idx, end_idx, heading_text))
        
        # If the document starts with content before the first heading,
        # add that as an initial section
        if headings and headings[0].start() > 0:
            boundaries.insert(0, (0, headings[0].start(), "Introduction"))
        
        # If no headings were found, treat the entire document as one section
        if not boundaries:
            boundaries.append((0, len(markdown_text), "Content"))
            
        return boundaries
    
    def get_overlap_text(self, text: str, overlap_tokens: int) -> str:
        """
        Extract the last n tokens of text for overlap purposes.
        
        Args:
            text: The text to extract from
            overlap_tokens: Number of tokens to extract
            
        Returns:
            Text containing approximately the last n tokens
        """
        tokens = self.encode(text)
        
        # If text is shorter than desired overlap, return all of it
        if len(tokens) <= overlap_tokens:
            return text
        
        # Otherwise, get the last overlap_tokens tokens
        overlap_tokens_list = tokens[-overlap_tokens:]
        
        # Convert back to text
        overlap_text = self.decode(overlap_tokens_list)
        
        return overlap_text
    
    def chunk_document(self, 
                      markdown_text: str, 
                      max_tokens: Optional[int] = None,
                      overlap_tokens: Optional[int] = None,
                      exclude_sections: List[str] = None) -> List[Dict[str, str]]:
        """
        Split a markdown document into chunks, respecting section boundaries where possible.
        
        Args:
            markdown_text: The markdown document to split
            max_tokens: Maximum tokens per chunk (default: self.max_tokens)
            overlap_tokens: Number of tokens to overlap between chunks (default: self.overlap_tokens)
            exclude_sections: List of section names to exclude from processing (e.g. ["References"])
            
        Returns:
            List of dictionaries containing chunk text and metadata
        """
        #logger.info(f"Starting document chunking with {self.model_name} tokenizer")
        #logger.info(f"Document length: {len(markdown_text)} characters")
        
        # Default to empty list if None
        exclude_sections = exclude_sections or []
        if exclude_sections:
            #logger.info(f"Excluding sections: {', '.join(exclude_sections)}")
            pass
            
        
        # Use provided values or defaults
        max_tokens = max_tokens or self.max_tokens
        overlap_tokens = overlap_tokens or self.overlap_tokens
        
        # Safety check to prevent divide-by-zero or negative values
        if max_tokens <= (self.prompt_template_tokens + self.response_buffer_tokens):
            #logger.warning(f"max_tokens ({max_tokens}) is less than or equal to prompt_template_tokens ({self.prompt_template_tokens}) + response_buffer_tokens ({self.response_buffer_tokens})")
            #logger.warning(f"Setting effective token limit to default minimum of 1000")
            effective_token_limit = 1000
        else:
            effective_token_limit = max_tokens - self.prompt_template_tokens - self.response_buffer_tokens
        
        #logger.info(f"Parameters: max_tokens={max_tokens}, overlap_tokens={overlap_tokens}")
        #logger.info(f"Effective token limit: {effective_token_limit}")
        
        # Safety check for overlap tokens
        if overlap_tokens >= effective_token_limit:
            #logger.warning(f"overlap_tokens ({overlap_tokens}) is greater than or equal to effective_token_limit ({effective_token_limit})")
            overlap_tokens = min(499, int(effective_token_limit * 0.3))
            #logger.warning(f"Adjusted overlap_tokens to {overlap_tokens}")
        
        # Get document metadata from the beginning (title, authors, etc.)
        # This simple approach assumes title is the first heading 
        title_match = re.search(r'^#\s+(.+?)$', markdown_text, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else "Untitled Document"
        #logger.info(f"Document title: {title}")
        
        # Extract abstract if available
        abstract = ""
        abstract_match = re.search(r'(?:^|\n)## Abstract\s*\n(.*?)(?:\n##|\Z)', 
                                  markdown_text, re.DOTALL)
        if abstract_match:
            abstract = abstract_match.group(1).strip()
            #logger.info("Abstract found and extracted")
        
        # Get section boundaries
        sections = self.get_section_boundaries(markdown_text)
        
        # Filter out excluded sections
        original_section_count = len(sections)
        sections = [section for section in sections 
                   if not any(excluded in section[2] for excluded in exclude_sections)]
        excluded_count = original_section_count - len(sections)
        
        #logger.info(f"Found {len(sections)} sections in document (excluded {excluded_count} sections)")
        for i, (_, _, heading) in enumerate(sections[:5]):
            #logger.info(f"Section {i+1}: {heading}")
            pass
        if len(sections) > 5:
            #logger.info(f"... and {len(sections)-5} more sections")
            pass
        
        # Prepare chunks
        chunks = []
        current_chunk_text = ""
        current_chunk_tokens = 0
        chunk_index = 1
        section_index = 0
        section_offset = 0  # Track how much of current section has been processed
        chunk_count_limit = 1000  # Safety limit to prevent infinite loops
        
        # Add document metadata to first chunk
        metadata = f"# {title}\n\n"
        if abstract:
            metadata += f"## Abstract\n\n{abstract}\n\n"
        
        metadata_tokens = self.count_tokens(metadata)
        #logger.info(f"Metadata size: {metadata_tokens} tokens")
        
        # Safety check for metadata size
        if metadata_tokens > effective_token_limit:
            #logger.warning(f"Metadata size ({metadata_tokens}) exceeds effective token limit ({effective_token_limit})")
            #logger.warning("Will still proceed but chunks might be larger than expected")
            pass
        
        while section_index < len(sections) and chunk_index < chunk_count_limit:
            start_idx, end_idx, heading = sections[section_index]
            # Apply offset to get remaining section text
            section_text = markdown_text[start_idx + section_offset:end_idx]
            section_tokens = self.count_tokens(section_text)
            
            #logger.info(f"Processing section: '{heading}' ({section_tokens} tokens, offset: {section_offset})")
            
            # If this section fits in the current chunk, add it
            if current_chunk_tokens + section_tokens <= effective_token_limit:
                #logger.info(f"Section '{heading}' fits in current chunk ({current_chunk_tokens} + {section_tokens} <= {effective_token_limit})")
                current_chunk_text += section_text
                current_chunk_tokens += section_tokens
                section_index += 1
                section_offset = 0  # Reset offset when moving to next section
            # If this section is too large on its own, split it
            elif section_tokens > effective_token_limit:
                #logger.info(f"Section '{heading}' too large ({section_tokens} tokens), splitting it")
                # Split large sections by paragraphs
                paragraphs = re.split(r'\n\s*\n', section_text)
                #logger.info(f"Split section into {len(paragraphs)} paragraphs")
                para_index = 0
                
                # If this is a new chunk, add the section heading first
                section_heading = f"## {heading}\n\n" if not heading.startswith('#') else f"{heading}\n\n"
                
                while para_index < len(paragraphs) and chunk_index < chunk_count_limit:
                    para_text = paragraphs[para_index]
                    para_tokens = self.count_tokens(para_text)
                    
                    #logger.info(f"Processing paragraph {para_index+1}/{len(paragraphs)} ({para_tokens} tokens)")
                    
                    # Start a new chunk with metadata if needed
                    if current_chunk_tokens == 0:
                        # Add part indicator and metadata to each chunk
                        prefix = f"{metadata}[Part {chunk_index}]\n\n{section_heading}"
                        current_chunk_text = prefix
                        current_chunk_tokens = self.count_tokens(prefix)
                        #logger.info(f"Starting new chunk {chunk_index} with prefix ({current_chunk_tokens} tokens)")
                    
                    # If paragraph is small enough to fit, add it to current chunk
                    if current_chunk_tokens + para_tokens + 2 <= effective_token_limit:  # +2 for newlines
                        #logger.info(f"Paragraph fits in current chunk ({current_chunk_tokens} + {para_tokens} <= {effective_token_limit})")
                        current_chunk_text += para_text + "\n\n"
                        current_chunk_tokens += para_tokens + 2
                        para_index += 1
                    # Handle paragraphs that are too large for a single chunk
                    elif para_tokens > effective_token_limit:
                        #logger.info(f"Paragraph too large ({para_tokens} tokens), splitting by sentences")
                        # Simple sentence splitting based on periods, question marks, and exclamation points
                        sentences = re.split(r'(?<=[.!?])\s+', para_text)
                        #logger.info(f"Split paragraph into {len(sentences)} sentences")
                        sentence_index = 0
                        
                        while sentence_index < len(sentences) and chunk_index < chunk_count_limit:
                            sentence = sentences[sentence_index]
                            sentence_tokens = self.count_tokens(sentence)
                            
                            #logger.info(f"Processing sentence {sentence_index+1}/{len(sentences)} ({sentence_tokens} tokens)")
                            
                            # Catch extremely large sentences that exceed the limit
                            if sentence_tokens > effective_token_limit:
                                #logger.warning(f"Sentence is extremely large ({sentence_tokens} tokens)")
                                # Try to add part of the sentence if possible
                                if current_chunk_tokens < effective_token_limit:
                                    # Add what we can of the sentence
                                    truncated_tokens = self.encode(sentence)[:effective_token_limit - current_chunk_tokens]
                                    truncated_text = self.decode(truncated_tokens)
                                    current_chunk_text += truncated_text + "..."
                                    current_chunk_tokens += len(truncated_tokens)
                                    #logger.info(f"Added truncated sentence ({len(truncated_tokens)} tokens)")
                                
                                # Finalize current chunk
                                chunks.append({
                                    "text": current_chunk_text.strip(),
                                    "chunk_index": chunk_index,
                                    "total_tokens": current_chunk_tokens,
                                    "model": self.model_name
                                })
                                
                                # Skip to next sentence
                                sentence_index += 1
                                
                                # Start new chunk with overlap
                                overlap_text = self.get_overlap_text(current_chunk_text, overlap_tokens)
                                overlap_tokens_count = self.count_tokens(overlap_text)
                                #logger.info(f"Creating overlap with {overlap_tokens_count} tokens")
                                
                                # Reset for next chunk
                                current_chunk_text = f"{metadata}[Part {chunk_index + 1}]\n\nContinuation:\n\n"
                                
                                if overlap_text:
                                    current_chunk_text += f"Previous content: {overlap_text}\n\n"
                                
                                current_chunk_tokens = self.count_tokens(current_chunk_text)
                                chunk_index += 1
                                #logger.info(f"Started new chunk {chunk_index} with {current_chunk_tokens} tokens")
                                continue
                            
                            # If sentence fits, add it
                            if current_chunk_tokens + sentence_tokens + 1 <= effective_token_limit:  # +1 for space
                                #logger.info(f"Sentence fits in current chunk")
                                current_chunk_text += sentence + " "
                                current_chunk_tokens += sentence_tokens + 1
                                sentence_index += 1
                            else:
                                #logger.info(f"Sentence doesn't fit, finalizing chunk {chunk_index} with {current_chunk_tokens} tokens")
                                # Finalize current chunk
                                chunks.append({
                                    "text": current_chunk_text.strip(),
                                    "chunk_index": chunk_index,
                                    "total_tokens": current_chunk_tokens,
                                    "model": self.model_name
                                })
                                
                                # Start new chunk with overlap
                                if len(chunks) > 0:
                                    # Create overlap by taking the end of the previous chunk
                                    overlap_text = self.get_overlap_text(current_chunk_text, overlap_tokens)
                                    overlap_tokens_count = self.count_tokens(overlap_text)
                                    #logger.info(f"Creating overlap with {overlap_tokens_count} tokens")
                                    
                                    # Reset for next chunk
                                    current_chunk_text = f"{metadata}[Part {chunk_index + 1}]\n\nContinuation:\n\n"
                                    
                                    if overlap_text:
                                        current_chunk_text += f"Previous content: {overlap_text}\n\n"
                                    
                                    current_chunk_tokens = self.count_tokens(current_chunk_text)
                                    chunk_index += 1
                                    #logger.info(f"Started new chunk {chunk_index} with {current_chunk_tokens} tokens")
                                else:
                                    # Should not happen but just in case
                                    #logger.warning("Unexpected condition: Creating new chunk with empty previous chunks list")
                                    current_chunk_text = ""
                                    current_chunk_tokens = 0
                                    chunk_index += 1
                        
                        para_index += 1
                    else:
                        #logger.info(f"Paragraph doesn't fit, finalizing chunk {chunk_index} with {current_chunk_tokens} tokens")
                        # Finalize current chunk since paragraph doesn't fit
                        chunks.append({
                            "text": current_chunk_text.strip(),
                            "chunk_index": chunk_index,
                            "total_tokens": current_chunk_tokens,
                            "model": self.model_name
                        })
                        
                        # Start new chunk with overlap
                        overlap_text = self.get_overlap_text(current_chunk_text, overlap_tokens)
                        overlap_tokens_count = self.count_tokens(overlap_text)
                        #logger.info(f"Creating overlap with {overlap_tokens_count} tokens")
                        
                        # Reset for next chunk
                        current_chunk_text = f"{metadata}[Part {chunk_index + 1}]\n\nContinuation:\n\n"
                        
                        if overlap_text:
                            current_chunk_text += f"Previous content: {overlap_text}\n\n"
                        
                        current_chunk_tokens = self.count_tokens(current_chunk_text)
                        chunk_index += 1
                        #logger.info(f"Started new chunk {chunk_index} with {current_chunk_tokens} tokens")
                        
                        # Don't increment para_index - let the paragraph be processed in the new chunk
                        # The while loop will continue and try to fit this paragraph in the new chunk
                        
                # Move to next section
                section_index += 1
                section_offset = 0  # Reset offset when moving to next section
            else:
                #logger.info(f"Section '{heading}' doesn't fit, finalizing chunk {chunk_index} with {current_chunk_tokens} tokens")
                
                # Calculate how much of the section we can fit in current chunk
                available_tokens = effective_token_limit - current_chunk_tokens
                if available_tokens > 0:
                    # Try to fit part of the section
                    section_tokens_list = self.encode(section_text)
                    if len(section_tokens_list) > available_tokens:
                        # Take what we can fit
                        partial_tokens = section_tokens_list[:available_tokens]
                        partial_text = self.decode(partial_tokens)
                        current_chunk_text += partial_text
                        current_chunk_tokens += len(partial_tokens)
                        section_offset += len(self.encode(partial_text))  # Update offset
                        #logger.info(f"Added partial section ({len(partial_tokens)} tokens), offset now: {section_offset}")
                    else:
                        # Entire remaining section fits
                        current_chunk_text += section_text
                        current_chunk_tokens += section_tokens
                        section_index += 1
                        section_offset = 0
                        #logger.info(f"Added entire remaining section, moving to next section")
                
                # Finalize current chunk
                chunks.append({
                    "text": current_chunk_text.strip(),
                    "chunk_index": chunk_index,
                    "total_tokens": current_chunk_tokens,
                    "model": self.model_name
                })
                
                # Start new chunk with overlap
                overlap_text = self.get_overlap_text(current_chunk_text, overlap_tokens)
                overlap_tokens_count = self.count_tokens(overlap_text)
                #logger.info(f"Creating overlap with {overlap_tokens_count} tokens")
                
                # Reset for next chunk
                current_chunk_text = f"{metadata}[Part {chunk_index + 1}]\n\nContinuation:\n\n"
                
                if overlap_text:
                    current_chunk_text += f"Previous content: {overlap_text}\n\n"
                
                current_chunk_tokens = self.count_tokens(current_chunk_text)
                chunk_index += 1
                #logger.info(f"Started new chunk {chunk_index} with {current_chunk_tokens} tokens")  
                
        
        # Safety check for max chunks
        if chunk_index >= chunk_count_limit:
            #logger.warning(f"Reached chunk count limit of {chunk_count_limit}. Document chunking may be incomplete.")
            #return empyt list when max chunk count is reached
            #logger.info(f"Returning empty list due to chunk count limit reached")
            return []
        
        # Add the final chunk if there's content
        if current_chunk_text and chunk_index < chunk_count_limit:
            #logger.info(f"Adding final chunk {chunk_index} with {current_chunk_tokens} tokens")
            chunks.append({
                "text": current_chunk_text.strip(),
                "chunk_index": chunk_index,
                "total_tokens": current_chunk_tokens,
                "model": self.model_name
            })
        
        # Add total chunks info to each chunk
        total_chunks = len(chunks)
        for i, chunk in enumerate(chunks):
            chunk["total_chunks"] = total_chunks
            chunk["chunk_id"] = f"{i+1}/{total_chunks}"
        
        #logger.info(f"Document chunking complete: created {total_chunks} chunks for {self.model_name}")
        return chunks
    
    def read_markdown_file(self, file_path: str) -> Optional[str]:
        """
        Read a markdown file and return its contents.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            The file contents as a string, or None if an error occurred
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error reading markdown file: {e}")
            return None
    
    def save_chunks_to_files(self, chunks: List[Dict[str, str]], 
                           output_dir: str, 
                           base_filename: str) -> List[str]:
        """
        Save chunks to individual files.
        
        Args:
            chunks: List of chunk dictionaries
            output_dir: Directory to save chunks to
            base_filename: Base name for chunk files
            
        Returns:
            List of saved file paths
        """
        os.makedirs(output_dir, exist_ok=True)
        saved_files = []
        
        for chunk in chunks:
            chunk_index = chunk["chunk_index"]
            filename = f"{base_filename}_{self.model_name}_chunk_{chunk_index}.md"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(chunk["text"])
            
            saved_files.append(filepath)
            print(f"Saved chunk {chunk_index}/{chunk['total_chunks']} with {chunk['total_tokens']} tokens to {filepath}")
        
        return saved_files
    
    def process_file(self, 
                    file_path: str, 
                    output_dir: str = "results/chunked",
                    max_tokens: Optional[int] = None,
                    overlap_tokens: Optional[int] = None,
                    exclude_sections: List[str] = None) -> List[str]:
        """
        Process a markdown file: read, tokenize, chunk, and save.
        
        Args:
            file_path: Path to the markdown file
            output_dir: Directory to save chunks to
            max_tokens: Maximum tokens per chunk (default: self.max_tokens)
            overlap_tokens: Number of tokens to overlap between chunks (default: self.overlap_tokens)
            exclude_sections: List of section names to exclude (e.g. ["References"])
            
        Returns:
            List of saved file paths
        """
        # Read the markdown file
        markdown_text = self.read_markdown_file(file_path)
        if not markdown_text:
            return []
        
        # Count tokens in the entire document
        total_tokens = self.count_tokens(markdown_text)
        print(f"The document contains {total_tokens} tokens with {self.model_name} tokenizer.")
        
        # Return the original file if it's under the limit
        if total_tokens <= (self.max_tokens - self.prompt_template_tokens - self.response_buffer_tokens):
            print(f"Document is under the token limit ({total_tokens} tokens). No chunking needed.")
            return [file_path]
        
        # Split into chunks
        chunks = self.chunk_document(markdown_text, max_tokens, overlap_tokens, exclude_sections)
        print(f"AAA Split into {len(chunks)} chunks for {self.model_name}.")
        
        # Save chunks to files
        base_filename = os.path.basename(file_path).split('.')[0]
        saved_files = self.save_chunks_to_files(chunks, output_dir, base_filename)
        
        print(f"Saved {len(saved_files)} chunk files to {output_dir}.")
        return saved_files