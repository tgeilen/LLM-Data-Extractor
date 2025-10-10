"""
Base class for scientific publication analyzers using LLMs.
"""

import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple

from analyser.prompt_templates import PUBLICATION_ANALYSIS_TEMPLATE
from analyser.utils import read_markdown_file, save_analysis_results


class BaseAnalyser(ABC):
    """
    Base class for scientific publication analysis using LLMs.
    This class should be extended by specific LLM API implementations.
    """
    
    def __init__(self, prompt_template: str = PUBLICATION_ANALYSIS_TEMPLATE, 
                 output_dir: str = "results/output"):
        """
        Initialize the base analyzer.
        
        Args:
            prompt_template: The template prompt to send to the LLM
            output_dir: Directory to save results to
        """
        self.prompt_template = prompt_template
        self.output_dir = output_dir
    
    def analyze_publication(self, markdown_file: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Analyze a scientific publication in markdown format.
        
        Args:
            markdown_file: Path to the markdown file containing the publication
            
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
        
        # Prepare the prompt with markdown content
        prompt = self.prepare_prompt(markdown_content)
        
        # Query the LLM API
        #print(f"Prompt: {prompt}")
        response = self.query_llm(prompt)
        
        # Process the response
        if response:
            try:
                response_content = self.extract_response_content(response)
                print("\nLLM Response:")
                #print(response_content)
                
                # Save results
                base_filename = os.path.basename(markdown_file).split('.')[0]
                return save_analysis_results(response_content, self.output_dir, base_filename)
                
            except Exception as e:
                print(f"Error processing response: {e}")
                return None, None
        else:
            print("No response received from LLM API.")
            return None, None
    
    def prepare_prompt(self, markdown_content: str) -> str:
        """
        Prepare the prompt by combining the template with the markdown content.
        
        Args:
            markdown_content: The markdown content to analyze
            
        Returns:
            The complete prompt for the LLM
        """
        return self.prompt_template + markdown_content + " <<<PubEnd>>>"
    
    @abstractmethod
    def query_llm(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Send a prompt to the LLM API and return the response.
        This method should be implemented by subclasses.
        
        Args:
            prompt: The prompt to send to the API
            
        Returns:
            The response from the API or None if there was an error
        """
        pass
    
    @abstractmethod
    def extract_response_content(self, response: Dict[str, Any]) -> str:
        """
        Extract the content from the LLM API response.
        This method should be implemented by subclasses.
        
        Args:
            response: The response from the LLM API
            
        Returns:
            The content of the response as a string
        """
        pass 