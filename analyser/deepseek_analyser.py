"""
DeepSeek API implementation of the scientific publication analyzer.
"""

import os
import requests
import json
from analyser import utils
from typing import Dict, Any, Optional
import time
from analyser.base_analyser import BaseAnalyser

from tokenizer import get_tokenizer

# DeepSeek API endpoint
API_URL = "https://api.deepseek.com/v1/chat/completions"

class DeepSeekAnalyser(BaseAnalyser):
    
    API_KEY = os.environ.get("DEEPSEEK_API_TOKEN", "your_deepseek_api_token_here")
    """
    Implementation of BaseAnalyser for the DeepSeek API.
    """
    
    def __init__(self, api_token: Optional[str] = None, model: str = "deepseek-chat", 
                 output_dir: str = "results/output", prompt_template: Optional[str] = None):
        """
        Initialize the DeepSeek analyzer.
        
        Args:
            api_token: Your DeepSeek API token
            model: The model to use for analysis
            output_dir: Directory to save results to
            prompt_template: Custom prompt template to use instead of default
        """
        super().__init__(prompt_template=prompt_template, output_dir=output_dir)
        
        if api_token:
            self.api_token = api_token
        else:
            self.api_token = self.API_KEY
        
        self.model = model
    
    def query_llm(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Send a prompt to the DeepSeek API and return the response.
        
        Args:
            prompt: The prompt to send to the API
            
        Returns:
            The response from the API or None if there was an error
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        try:
            #tokenizer = get_tokenizer("deepseek")
            #print(tokenizer)
            #if tokenizer:
                # Check if the prompt exceeds the model's context size
               # prompt_length = tokenizer.count_tokens(prompt)
               # print(f"Prompt length: {prompt_length} tokens")

            response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
            
            response.raise_for_status()  # Raise an exception for HTTP errors
            
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request to DeepSeek API response:  {response}")
            print(f"Error making request to DeepSeek API: {e}")
            return None
    
    def extract_response_content(self, response: Dict[str, Any]) -> str:
        """
        Extract the content from the DeepSeek API response.
        
        Args:
            response: The response from the DeepSeek API
            
        Returns:
            The content of the response as a string
        """
        
        #print(f"Full response: {response['choices'][0]['message']['content']}")
        #print(f"Full DeepSeek response: {response['choices'][0]['message']['content']}")
        if response["choices"][0]["message"]["content"] == "" or response["choices"][0]["message"]["content"] == "null" or response["choices"][0]["message"]["content"] == [] or response["choices"][0]["message"]["content"].strip() == '[]\n```json\n[]\n```' or response["choices"][0]["message"]["content"].strip() == '[]\n```':
            print(f"No response from DeepSeek API")
            print(f"Response: {response}")
            time.sleep(1)
        response_text = utils.clean_json_response(response["choices"][0]["message"]["content"])
        #print(f"Cleaned response: {response_text}")
        
        return response_text
        
        return response["choices"][0]["message"]["content"]


def main():
    """
    Main function to run the DeepSeek analyzer.
    """
    # API token (to be replaced with more secure handling in production)
    api_token = os.environ.get("DEEPSEEK_API_TOKEN", "your_deepseek_api_token_here")
    
    # Initialize the analyzer
    analyzer = DeepSeekAnalyser(api_token=api_token)
    
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
