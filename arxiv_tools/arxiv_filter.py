#!/usr/bin/env python3
"""
ArXiv Paper Classification Module

This module provides LLM-based filtering to identify foundational models in robotics
from arXiv papers based on their titles and abstracts.
"""

import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

# Import existing LLM analyzers with fallback
try:
    from analyser.deepseek_analyser import DeepSeekAnalyser
    DEEPSEEK_AVAILABLE = True
except ImportError:
    DEEPSEEK_AVAILABLE = False
    print("Warning: DeepSeek analyzer not available")

try:
    from analyser.gemini_analyser import GeminiAnalyser
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: Gemini analyzer not available")

# Classification prompt template
FOUNDATIONAL_MODEL_CLASSIFIER_PROMPT = """
Analyze this paper title and abstract to determine if it introduces a new foundational model in robotics.

Title: {title}

Abstract: {abstract}

Criteria for foundational model in robotics:
1. Introduces a NEW model/architecture (not just applications of existing models)
2. Specifically targets robotics applications or robot learning
3. Claims to be general-purpose, foundational, or broadly applicable
4. Shows applicability across multiple robot tasks or domains
5. Focuses on model architecture, training methodology, or core capabilities

Examples of what QUALIFIES:
- New transformer architectures for robot learning
- Foundation models specifically trained for robotics
- General-purpose robot policies or world models
- Novel multi-modal models for robot perception and control

Examples of what does NOT qualify:
- Applications of existing models to specific robot tasks
- Task-specific solutions (single-purpose controllers, planners)
- Datasets, benchmarks, or evaluation frameworks
- Hardware or mechanical innovations
- Simulation environments or tools

IMPORTANT: Respond with ONLY valid JSON. No markdown formatting. Use this exact format:
{{
  "is_foundational_model": boolean,
  "confidence": float between 0.0 and 1.0,
  "reasoning": "brief explanation",
  "model_name": "extracted model name or null",
  "robotics_domains": ["list of relevant domains"]
}}"""

# Classification prompt template
FOUNDATIONAL_MODEL_CLASSIFIER_PROMPT_AGNOSTIC = """
Analyze this paper title and abstract to determine if it introduces a new foundational model or is related to an advanced AI model.

Title: {title}

Abstract: {abstract}

Criteria for qualifying foundational model / AI research (not all need to be met):
1. Introduces a NEW model/architecture or is a significant adaptation of an existing one
2. Specifically targets advanced and generic AI applications or tasks
3. Claims to be general-purpose, foundational, or broadly applicable
4. Shows applicability across multiple tasks or domains
5. Focuses on model architecture, training methodology, or core capabilities


Examples of what QUALIFIES:
- Any paper referencing new foundation models
- New transformer architectures
- General-purpose vision policies or world models
- Novel multi-modal models for vision and perception

Examples of what does NOT qualify:
- Task-specific solutions (single-purpose controllers, planners)
- Datasets, benchmarks, or evaluation frameworks
- Hardware or mechanical innovations
- Simulation environments or tools

IMPORTANT: Respond with ONLY valid JSON. No markdown formatting. Use this exact format:
{{
  "is_foundational_model": boolean,
  "confidence": float between 0.0 and 1.0,
  "reasoning": "brief explanation",
  "model_name": "extracted model name or null"
}}
"""


class ArXivClassifier:
    """
    LLM-based classifier for identifying foundational robotics models from paper abstracts.
    """
    
    def __init__(self, provider: str = "deepseek", rate_limit_delay: float = 1.0):
        """
        Initialize the classifier with specified LLM provider.
        
        Args:
            provider: LLM provider ("deepseek" or "gemini")
            rate_limit_delay: Delay between API calls in seconds
        """
        self.provider = provider.lower()
        self.rate_limit_delay = rate_limit_delay
        self.analyzer = self._initialize_analyzer()
        
    def _initialize_analyzer(self):
        """Initialize the appropriate LLM analyzer."""
        try:
            if self.provider == "deepseek" and DEEPSEEK_AVAILABLE:
                return DeepSeekAnalyser()
            elif self.provider == "gemini" and GEMINI_AVAILABLE:
                return GeminiAnalyser()
            elif self.provider == "deepseek" and not DEEPSEEK_AVAILABLE:
                print(f" DeepSeek analyzer not available")
                return None
            elif self.provider == "gemini" and not GEMINI_AVAILABLE:
                print(f" Gemini analyzer not available")
                return None
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        except Exception as e:
            print(f" Error initializing {self.provider} analyzer: {e}")
            return None
    
    def classify_paper(self, paper: Dict) -> Dict:
        """
        Classify a single paper to determine if it's a foundational robotics model.
        
        Args:
            paper: Paper dictionary with 'title' and 'abstract' keys
            
        Returns:
            Classification result dictionary
        """
        if not self.analyzer:
            return {
                "error": "Analyzer not initialized",
                "is_foundational_model": False,
                "confidence": 0.0
            }
        
        try:
            # Prepare the prompt
            prompt = FOUNDATIONAL_MODEL_CLASSIFIER_PROMPT_AGNOSTIC.format(
                title=paper.get('title', ''),
                abstract=paper.get('abstract', '')
            )
            
            # Query the LLM
            print(f"   Querying LLM for paper {paper.get('arxiv_id', 'unknown')} with prompt: {prompt[:100]}...")
            response = self.analyzer.query_llm(prompt)
            print(f"LLM response: {response}")
            
            if not response:
                return {
                    "error": "No response from LLM",
                    "is_foundational_model": False,
                    "confidence": 0.0
                }
            
            # Extract response content
            response_content = self.analyzer.extract_response_content(response)
            
            # Parse JSON response
            try:
                classification = json.loads(response_content)
                
                # Validate required fields
                required_fields = ["is_foundational_model", "confidence", "reasoning"]
                for field in required_fields:
                    if field not in classification:
                        classification[field] = None
                
                # Add metadata
                classification.update({
                    "arxiv_id": paper.get('arxiv_id'),
                    "title": paper.get('title'),
                    "classification_timestamp": datetime.now().isoformat(),
                    "provider": self.provider
                })
                
                return classification
                
            except json.JSONDecodeError as e:
                print(f"️ Failed to parse JSON response for {paper.get('arxiv_id', 'unknown')}: {e}")
                return {
                    "error": f"JSON parsing failed: {e}",
                    "raw_response": response_content,
                    "is_foundational_model": False,
                    "confidence": 0.0,
                    "arxiv_id": paper.get('arxiv_id'),
                    "provider": self.provider
                }
                
        except Exception as e:
            print(f" Error classifying paper {paper.get('arxiv_id', 'unknown')}: {e}")
            return {
                "error": str(e),
                "is_foundational_model": False,
                "confidence": 0.0,
                "arxiv_id": paper.get('arxiv_id'),
                "provider": self.provider
            }
    
    def classify_papers(self, papers: List[Dict], confidence_threshold: float = 0.7) -> Dict:
        """
        Classify multiple papers and return filtered results.
        
        Args:
            papers: List of paper dictionaries
            confidence_threshold: Minimum confidence for positive classification
            
        Returns:
            Dictionary with classification results and statistics
        """
        print(f" Starting LLM classification with {self.provider.upper()}...")
        print(f"   Papers to classify: {len(papers)}")
        print(f"   Confidence threshold: {confidence_threshold}")
        
        all_classifications = []
        positive_classifications = []
        errors = []

        num_matches = 0
        
        for i, paper in enumerate(papers, 1):
            print(f"   Classifying {i}/{len(papers)}: {paper.get('arxiv_id', 'unknown')}")
            
            # Add rate limiting
            if i > 1:
                time.sleep(self.rate_limit_delay)
            
            classification = self.classify_paper(paper)
            all_classifications.append(classification)
            
            # Check if this is a positive classification
            if (classification.get('is_foundational_model', False) and 
                classification.get('confidence', 0.0) >= confidence_threshold):
                positive_classifications.append(classification)
                print(f"       MATCH: {classification.get('confidence', 0.0):.2f} confidence")
                print(f"       Classification added: {classification}")
                num_matches += 1
                print(f"       Total matches so far: {num_matches}")
            elif classification.get('error'):
                errors.append(classification)
                print(f"       ERROR: {classification.get('error')}")
            else:
                conf = classification.get('confidence', 0.0)
                print(f"       No match: {conf:.2f} confidence")
        
        results = {
            "classification_summary": {
                "total_papers": len(papers),
                "positive_classifications": len(positive_classifications),
                "errors": len(errors),
                "success_rate": (len(papers) - len(errors)) / len(papers) if papers else 0,
                "match_rate": len(positive_classifications) / len(papers) if papers else 0,
                "confidence_threshold": confidence_threshold,
                "provider": self.provider,
                "timestamp": datetime.now().isoformat()
            },
            "positive_matches": positive_classifications,
            "all_classifications": all_classifications,
            "errors": errors
        }
        
        print(f" Classification complete:")
        print(f"   Positive matches: {len(positive_classifications)}/{len(papers)}")
        print(f"   Success rate: {results['classification_summary']['success_rate']:.1%}")
        print(f"   Match rate: {results['classification_summary']['match_rate']:.1%}")
        
        return results
    
    def save_classification_results(self, results: Dict, filename: Optional[str] = None) -> str:
        """
        Save classification results to a JSON file.
        
        Args:
            results: Classification results dictionary
            filename: Optional filename
            
        Returns:
            Path to saved file
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"classification_results_{timestamp}.json"
        
        filepath = f"results/{filename}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f" Classification results saved to: {filepath}")
        return filepath
    
    def export_positive_arxiv_ids(self, results: Dict, filename: Optional[str] = None) -> str:
        """
        Export arXiv IDs of positively classified papers to a text file.
        
        Args:
            results: Classification results dictionary
            filename: Optional filename
            
        Returns:
            Path to saved file
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"discovered_arxiv_ids_{timestamp}.txt"
        
        filepath = f"results/{filename}"
        
        positive_matches = results.get('positive_matches', [])
        arxiv_ids = [match.get('arxiv_id') for match in positive_matches if match.get('arxiv_id')]
        
        with open(filepath, 'w') as f:
            for arxiv_id in arxiv_ids:
                f.write(f"{arxiv_id}\n")
        
        print(f" Exported {len(arxiv_ids)} arXiv IDs to: {filepath}")
        return filepath


def main():
    """Example usage of the classifier."""
    # Example papers for testing
    test_papers = [
        {
            "arxiv_id": "2401.00001",
            "title": "RobotTransformer: A Foundation Model for General Robot Manipulation",
            "abstract": "We present RobotTransformer, a new foundation model architecture specifically designed for general robot manipulation tasks. Our model demonstrates superior performance across diverse robotic domains including manipulation, navigation, and perception."
        },
        {
            "arxiv_id": "2401.00002", 
            "title": "Evaluating GPT-4 for Robot Task Planning",
            "abstract": "This paper evaluates the performance of GPT-4 when applied to robot task planning problems. We test the model on various benchmarks and compare with existing planning algorithms."
        }
    ]
    
    # Initialize classifier
    classifier = ArXivClassifier(provider="deepseek")
    
    # Run classification
    results = classifier.classify_papers(test_papers, confidence_threshold=0.7)
    
    # Save results
    classifier.save_classification_results(results)
    classifier.export_positive_arxiv_ids(results)


if __name__ == "__main__":
    main()
