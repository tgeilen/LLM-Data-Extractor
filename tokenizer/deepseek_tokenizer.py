



"""
DeepSeek tokenizer module with document chunking capabilities.

This module provides functions to:
1. Count tokens in a string using DeepSeek's tokenizer
2. Split markdown documents into appropriately sized chunks
3. Implement chunking strategies that respect document structure
"""

import os
import re
from typing import List, Dict, Tuple, Optional

try:
    from deepseek_tokenizer import ds_token
except ImportError:
    raise ImportError(
        "The deepseek_tokenizer package is not installed. "
        "Please install it with `pip install deepseek_tokenizer`"
    )

# Default maximum token limit for DeepSeek models
DEFAULT_MAX_TOKENS = 8192  
# Default overlap size between chunks (in tokens)
DEFAULT_OVERLAP_TOKENS = 500
# Estimated tokens for the prompt template
PROMPT_TEMPLATE_TOKENS = 1000
# Buffer to leave space for the response
RESPONSE_BUFFER_TOKENS = 1000

def count_tokens(text: str) -> int:
    """
    Count the number of tokens in a string using DeepSeek's tokenizer.
    
    Args:
        text: The text to tokenize
        
    Returns:
        The number of tokens in the text
    """
    tokens = ds_token.encode(text)
    return len(tokens)

def get_section_boundaries(markdown_text: str) -> List[Tuple[int, int, str]]:
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

def chunk_document(
    markdown_text: str, 
    max_tokens: int = DEFAULT_MAX_TOKENS,
    overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
    prompt_template_tokens: int = PROMPT_TEMPLATE_TOKENS,
    response_buffer_tokens: int = RESPONSE_BUFFER_TOKENS
) -> List[Dict[str, str]]:
    """
    Split a markdown document into chunks, respecting section boundaries where possible.
    
    Args:
        markdown_text: The markdown document to split
        max_tokens: Maximum tokens per chunk (default: 8192 for DeepSeek)
        overlap_tokens: Number of tokens to overlap between chunks
        prompt_template_tokens: Estimated tokens for the prompt template
        response_buffer_tokens: Buffer tokens to leave for the model response
        
    Returns:
        List of dictionaries containing chunk text and metadata
    """
    # DEBUG: Add comprehensive logging
    print(f" DEBUG: Starting chunk_document")
    print(f"  - Input text length: {len(markdown_text):,} chars")
    print(f"  - Max tokens: {max_tokens:,}")
    print(f"  - Overlap tokens: {overlap_tokens}")
    print(f"  - Prompt template tokens: {prompt_template_tokens}")
    print(f"  - Response buffer tokens: {response_buffer_tokens}")
    
    # Effective token limit per chunk, accounting for prompt and response space
    effective_token_limit = max_tokens - prompt_template_tokens - response_buffer_tokens
    print(f"  - Effective token limit: {effective_token_limit:,}")
    
    # Get document metadata from the beginning (title, authors, etc.)
    # This simple approach assumes title is the first heading 
    title_match = re.search(r'^#\s+(.+?)$', markdown_text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else "Untitled Document"
    print(f"  - Document title: {title[:50]}...")
    
    # Extract abstract if available
    abstract = ""
    abstract_match = re.search(r'(?:^|\n)## Abstract\s*\n(.*?)(?:\n##|\Z)', 
                              markdown_text, re.DOTALL)
    if abstract_match:
        abstract = abstract_match.group(1).strip()
    
    # Get section boundaries
    sections = get_section_boundaries(markdown_text)
    print(f"  - Found {len(sections)} sections")
    
    # Prepare chunks
    chunks = []
    current_chunk_text = ""
    current_chunk_tokens = 0
    chunk_index = 1
    section_index = 0
    
    # Add document metadata to first chunk
    metadata = f"# {title}\n\n"
    if abstract:
        metadata += f"## Abstract\n\n{abstract}\n\n"
    
    metadata_tokens = count_tokens(metadata)
    print(f"  - Metadata tokens: {metadata_tokens}")
    
    # DEBUG: Add loop monitoring
    max_iterations = len(sections) * 10  # Safety limit
    iteration_count = 0
    
    while section_index < len(sections):
        iteration_count += 1
        
        # DEBUG: Safety check for infinite loops
        if iteration_count > max_iterations:
            print(f" DEBUG: Breaking infinite loop after {iteration_count} iterations!")
            print(f"  - Current section_index: {section_index}/{len(sections)}")
            print(f"  - Current chunk_index: {chunk_index}")
            print(f"  - Current chunk tokens: {current_chunk_tokens}")
            print(f"  - Chunks created so far: {len(chunks)}")
            break
        
        start_idx, end_idx, heading = sections[section_index]
        section_text = markdown_text[start_idx:end_idx]
        section_tokens = count_tokens(section_text)
        
        print(f"\n DEBUG: Iteration {iteration_count}")
        print(f"  - Processing section {section_index + 1}/{len(sections)}: '{heading[:30]}...'")
        print(f"  - Section tokens: {section_tokens:,}")
        print(f"  - Current chunk tokens: {current_chunk_tokens}")
        print(f"  - Current chunk index: {chunk_index}")
        
        # If this section fits in the current chunk, add it
        if current_chunk_tokens + section_tokens <= effective_token_limit:
            print(f"  -  Section fits in current chunk")
            current_chunk_text += section_text
            current_chunk_tokens += section_tokens
            section_index += 1
            print(f"  - Moving to next section (index now: {section_index})")
        # If this section is too large on its own, split it
        elif section_tokens > effective_token_limit:
            print(f"  - ️ Section too large ({section_tokens:,} > {effective_token_limit:,}), splitting...")
            
            # Split large sections by paragraphs
            paragraphs = re.split(r'\n\s*\n', section_text)
            para_index = 0
            
            print(f"    - BBB Split into {len(paragraphs)} paragraphs")
            
            # If this is a new chunk, add the section heading first
            section_heading = f"## {heading}\n\n" if not heading.startswith('#') else f"{heading}\n\n"
            
            # DEBUG: Add paragraph processing monitoring
            para_iterations = 0
            max_para_iterations = len(paragraphs) * 5
            
            while para_index < len(paragraphs):
                para_iterations += 1
                
                # DEBUG: Safety check for paragraph loop
                if para_iterations > max_para_iterations:
                    print(f"     DEBUG: Breaking paragraph loop after {para_iterations} iterations!")
                    print(f"      - Current para_index: {para_index}/{len(paragraphs)}")
                    break
                
                para_text = paragraphs[para_index]
                para_tokens = count_tokens(para_text)
                
                print(f"     Para iteration {para_iterations}: Processing paragraph {para_index + 1}/{len(paragraphs)}")
                print(f"      - Paragraph tokens: {para_tokens}")
                print(f"      - Current chunk tokens: {current_chunk_tokens}")
                
                # Start a new chunk with metadata if needed
                if current_chunk_tokens == 0:
                    # Add part indicator and metadata to each chunk
                    prefix = f"{metadata}[Part {chunk_index}]\n\n{section_heading}"
                    current_chunk_text = prefix
                    current_chunk_tokens = count_tokens(prefix)
                    print(f"      - Started new chunk with {current_chunk_tokens} tokens")
                
                # If paragraph fits in current chunk, add it
                if current_chunk_tokens + para_tokens + 2 <= effective_token_limit:  # +2 for newlines
                    print(f"      -  Paragraph fits, adding to chunk")
                    current_chunk_text += para_text + "\n\n"
                    current_chunk_tokens += para_tokens + 2
                    para_index += 1
                    print(f"      - Para index now: {para_index}")
                # If paragraph is too large, we need to split it by sentences
                elif para_tokens > effective_token_limit:
                    print(f"      - ️ Paragraph too large ({para_tokens:,} > {effective_token_limit:,}), splitting sentences...")
                    
                    # Simple sentence splitting based on periods, question marks, and exclamation points
                    sentences = re.split(r'(?<=[.!?])\s+', para_text)
                    sentence_index = 0
                    
                    print(f"        - CCC Split into {len(sentences)} sentences")
                    
                    # DEBUG: Add sentence processing monitoring
                    sentence_iterations = 0
                    max_sentence_iterations = len(sentences) * 3
                    
                    while sentence_index < len(sentences):
                        sentence_iterations += 1
                        
                        # DEBUG: Safety check for sentence loop
                        if sentence_iterations > max_sentence_iterations:
                            print(f"         DEBUG: Breaking sentence loop after {sentence_iterations} iterations!")
                            print(f"          - Current sentence_index: {sentence_index}/{len(sentences)}")
                            break
                        
                        sentence = sentences[sentence_index]
                        sentence_tokens = count_tokens(sentence)
                        
                        print(f"         Sentence iteration {sentence_iterations}: Processing sentence {sentence_index + 1}/{len(sentences)}")
                        print(f"          - Sentence tokens: {sentence_tokens}")
                        
                        # If sentence fits, add it
                        if current_chunk_tokens + sentence_tokens + 1 <= effective_token_limit:  # +1 for space
                            print(f"          -  Sentence fits")
                            current_chunk_text += sentence + " "
                            current_chunk_tokens += sentence_tokens + 1
                            sentence_index += 1
                            print(f"          - Sentence index now: {sentence_index}")
                        else:
                            print(f"          -  Sentence doesn't fit, finalizing chunk")
                            # Finalize current chunk
                            chunks.append({
                                "text": current_chunk_text.strip(),
                                "chunk_index": chunk_index,
                                "total_tokens": current_chunk_tokens
                            })
                            print(f"          - Created chunk {chunk_index} with {current_chunk_tokens} tokens")
                            
                            # Start new chunk with overlap
                            if len(chunks) > 0:
                                # Create overlap by taking the end of the previous chunk
                                overlap_text = get_overlap_text(current_chunk_text, overlap_tokens)
                                
                                # Reset for next chunk
                                current_chunk_text = f"{metadata}[Part {chunk_index + 1}]\n\nContinuation:\n\n"
                                
                                if overlap_text:
                                    current_chunk_text += f"Previous content: {overlap_text}\n\n"
                                
                                current_chunk_tokens = count_tokens(current_chunk_text)
                                chunk_index += 1
                                print(f"          - Started new chunk {chunk_index} with overlap ({current_chunk_tokens} tokens)")
                            else:
                                # Should not happen but just in case
                                current_chunk_text = ""
                                current_chunk_tokens = 0
                                chunk_index += 1
                                print(f"          - Reset chunk variables")
                    
                    para_index += 1
                    print(f"      - Finished processing paragraph, para_index now: {para_index}")
                else:
                    print(f"      -  Paragraph doesn't fit, finalizing chunk")
                    # Finalize current chunk since paragraph doesn't fit
                    chunks.append({
                        "text": current_chunk_text.strip(),
                        "chunk_index": chunk_index,
                        "total_tokens": current_chunk_tokens
                    })
                    print(f"      - Created chunk {chunk_index} with {current_chunk_tokens} tokens")
                    
                    # Start new chunk with overlap
                    overlap_text = get_overlap_text(current_chunk_text, overlap_tokens)
                    
                    # Reset for next chunk
                    current_chunk_text = f"{metadata}[Part {chunk_index + 1}]\n\nContinuation:\n\n"
                    
                    if overlap_text:
                        current_chunk_text += f"Previous content: {overlap_text}\n\n"
                    
                    current_chunk_tokens = count_tokens(current_chunk_text)
                    chunk_index += 1
                    print(f"      - Started new chunk {chunk_index} with overlap ({current_chunk_tokens} tokens)")
            
            # Move to next section
            section_index += 1
            print(f"  - Finished processing large section, section_index now: {section_index}")
        else:
            print(f"  -  Section doesn't fit, finalizing chunk")
            # Finalize current chunk since section doesn't fit
            chunks.append({
                "text": current_chunk_text.strip(),
                "chunk_index": chunk_index,
                "total_tokens": current_chunk_tokens
            })
            print(f"  - Created chunk {chunk_index} with {current_chunk_tokens} tokens")
            
            # Start new chunk with overlap
            overlap_text = get_overlap_text(current_chunk_text, overlap_tokens)
            
            # Reset for next chunk
            current_chunk_text = f"{metadata}[Part {chunk_index + 1}]\n\nContinuation:\n\n"
            
            if overlap_text:
                current_chunk_text += f"Previous content: {overlap_text}\n\n"
            
            current_chunk_tokens = count_tokens(current_chunk_text)
            chunk_index += 1
            print(f"  - Started new chunk {chunk_index} with overlap ({current_chunk_tokens} tokens)")
    
    # Add the final chunk if there's content
    if current_chunk_text:
        chunks.append({
            "text": current_chunk_text.strip(),
            "chunk_index": chunk_index,
            "total_tokens": current_chunk_tokens
        })
        print(f" DEBUG: Added final chunk {chunk_index} with {current_chunk_tokens} tokens")
    
    # Add total chunks info to each chunk
    total_chunks = len(chunks)
    for i, chunk in enumerate(chunks):
        chunk["total_chunks"] = total_chunks
        chunk["chunk_id"] = f"{i+1}/{total_chunks}"
    
    print(f" DEBUG: Chunking completed")
    print(f"  - Total iterations: {iteration_count}")
    print(f"  - Total chunks created: {total_chunks}")
    print(f"  - Average tokens per chunk: {sum(c['total_tokens'] for c in chunks) / total_chunks:.1f}")
    
    return chunks

def get_overlap_text(text: str, overlap_tokens: int) -> str:
    """
    Extract the last n tokens of text for overlap purposes.
    
    Args:
        text: The text to extract from
        overlap_tokens: Number of tokens to extract
        
    Returns:
        Text containing approximately the last n tokens
    """
    tokens = ds_token.encode(text)
    
    # If text is shorter than desired overlap, return all of it
    if len(tokens) <= overlap_tokens:
        return text
    
    # Otherwise, get the last overlap_tokens tokens
    overlap_tokens_list = tokens[-overlap_tokens:]
    
    # Convert back to text
    overlap_text = ds_token.decode(overlap_tokens_list)
    
    return overlap_text

def read_markdown_file(file_path: str) -> Optional[str]:
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

def save_chunks_to_files(chunks: List[Dict[str, str]], output_dir: str, base_filename: str) -> List[str]:
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
        filename = f"{base_filename}_chunk_{chunk_index}.md"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(chunk["text"])
        
        saved_files.append(filepath)
        print(f"Saved chunk {chunk_index}/{chunk['total_chunks']} with {chunk['total_tokens']} tokens to {filepath}")
    
    return saved_files

def main():
    """
    Example usage function to demonstrate the module's capabilities.
    """
    # Example file path
    file_path = os.path.join("results", "samplePDF", "samplePDF.md")
    
    # Read the markdown file
    markdown_text = read_markdown_file(file_path)
    if not markdown_text:
        return
    
    # Count tokens in the entire document
    total_tokens = count_tokens(markdown_text)
    print(f"The document contains {total_tokens} tokens.")
    
    # Split into chunks
    chunks = chunk_document(markdown_text)
    print(f"DDD Split into {len(chunks)} chunks.")
    
    # Save chunks to files
    output_dir = os.path.join("results", "chunked")
    base_filename = os.path.basename(file_path).split('.')[0]
    saved_files = save_chunks_to_files(chunks, output_dir, base_filename)
    
    print(f"Saved {len(saved_files)} chunk files to {output_dir}.")

if __name__ == "__main__":
    main()