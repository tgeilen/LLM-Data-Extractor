"""
Google Cloud Gemini implementation of the scientific publication analyzer.
"""

import os
from typing import Dict, Any, Optional

import google.generativeai as genai

from analyser.base_analyser import BaseAnalyser
from analyser import utils

class GeminiAnalyser(BaseAnalyser):
    """
    Implementation of BaseAnalyser for Google Cloud Gemini API.
    """
    API_KEY = os.getenv('GEMINI_API_KEY', 'your_gemini_api_key_here')
    
    
    def __init__(self, api_key: Optional[str] = None, 
                 model_name: str = "gemini-2.0-flash-001",
                 output_dir: str = "results/output", prompt_template: Optional[str] = None):
        """
        Initialize the Gemini analyzer.
        
        Args:
            api_key: Your Google Cloud API key (or None to use GOOGLE_API_KEY env var)
            model_name: The Gemini model to use for analysis
            output_dir: Directory to save results to
            prompt_template: Custom prompt template to use instead of default
        """
        super().__init__(prompt_template=prompt_template, output_dir=output_dir)
        
        # Configure the API key - either from parameter or environment variable
        if api_key:
            genai.configure(api_key=api_key)
        else:
            # The library will automatically use GOOGLE_API_KEY if configured
            if self.API_KEY:
                genai.configure(api_key=self.API_KEY)
        
        self.model_name = model_name
        self.model = genai.GenerativeModel(self.model_name)
    
    def query_llm(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Send a prompt to the Gemini API and return the response.
        
        Args:
            prompt: The prompt to send to the API
            
        Returns:
            The response from the API or None if there was an error
        """
        try:
            # Generate content using the Gemini model
            response = self.model.generate_content(prompt)
            
            # Return in a format similar to other models for consistent handling
            #print("XXX - Response:")
            #print(response)
            return {
                "response": response,
                "text": response.text
            }
        except Exception as e:
            print(f"Error making request to Google Cloud Gemini API: {e}")
            return None
    
    def extract_response_content(self, response: Dict[str, Any]) -> str:
        """
        Extract the content from the Gemini API response.
        
        Args:
            response: The response from the Gemini API
            
        Returns:
            The content of the response as a string
        """
        # Extract the text content from the response
        #print first 100 characters of the response
        #print(f"Full response: {response['text']}")
        print(f"Uncomment here for full response")
        response_text = utils.clean_json_response(response["text"])
        #print(f"Cleaned response: {response_text}")
        return response_text


def main():
    """
    Main function to run the Gemini analyzer.
    """
    # API key can be provided directly or via GEMINI_API_KEY environment variable
    api_key = os.getenv('GEMINI_API_KEY', 'your_gemini_api_key_here')
    
    # Initialize the analyzer
    analyzer = GeminiAnalyser(api_key=api_key)
    
    # Path to the Markdown file
    markdown_file = "results/samplePDF/samplePDF.md"
    
    # Analyze the publication
    text_file, json_file = analyzer.analyze_publication(markdown_file)
    
    # Report results
    if text_file:
        print(f"\nResponse text saved to: {text_file}")
    if json_file:
        print(f"JSON response saved to: {json_file}")


if __name__ == "__main__":
    main() 