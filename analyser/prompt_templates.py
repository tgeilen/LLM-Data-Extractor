"""
This module contains prompt templates used by various LLM-based analyzers.
"""

# Prompt template for scientific publication analysis
PUBLICATION_ANALYSIS_TEMPLATE = """
You are a PHD-level computer scientist and research analyst. Your task is to extract key information from a scientific publication provided in Markdown format.

The publication content will appear after the marker <<<PubStart>>>.

Your extraction goals are to identify and extract technical details for **each distinct model variant** described in the paper (e.g., ModelName-Mini, ModelName-Large, ModelName-Pro). Each model variant must be represented as a separate JSON object.

For each model variant, extract the following items (if present):

1. Model name
2. Domain — Select all fitting domains from the following standardized list (do not invent or paraphrase):
[
  "3D modeling",
  "Audio",
  "Biology",
  "Driving",
  "Earth science",
  "Games",
  "Image generation",
  "Language",
  "Materials science",
  "Mathematics",
  "Medicine",
  "Multimodal",
  "Other",
  "Recommendation",
  "Robotics",
  "Search",
  "Speech",
  "Video",
  "Vision"
]
3. Organization (institution or company that developed the model)
4. Authors
5. Publication date
6. Parameters (model size in parameters) — For Mixture of Experts models, report only the TOTAL parameter count, not activated parameters (e.g., if you see "389B total, 52B activated", report "389B"). When a range is given (e.g., "50-70B parameters"), always select the LARGEST value ("70B"). Format as numeric values or with M/B suffixes (e.g., "4.5M", "273.9B") - never use commas, scientific notation strings, or other formats.
7. Training dataset
8. Training dataset size (number of datapoints / tokens)
9. Epochs
10. Training time (in hours)
11. Training hardware
12. Hardware quantity
13. Hardware utilization
14. Base model (if the model builds upon another)
15. Batch size
16. Input Modality — one or more of: "text", "image", "audio", "video", "multimodal"
17. Output Modality — one or more of: "text", "image", "audio", "video", "multimodal"
18. Architecture — Select **one** from the following standardized list. If the exact architecture isn't listed, choose the CLOSEST match rather than using "Other". Only use "Other - {High-Level Architecture Name}" when truly novel architectures don't fit any category:
[
  "Transformer (Encoder-only)",
  "Transformer (Decoder-only)",
  "Transformer (Encoder-Decoder)",
  "Vision Transformer (ViT)",
  "Multimodal Transformer",
  "State Space Model (Mamba/S4)",
  "Convolutional Neural Network (CNN)",
  "ResNet Architecture",
  "EfficientNet Architecture",
  "Hybrid CNN-Transformer",
  "CNN-RNN Hybrid",
  "Recurrent Neural Network (RNN)",
  "Long Short-Term Memory (LSTM)",
  "Diffusion Model",
  "Latent Diffusion Model",
  "Generative Adversarial Network (GAN)",
  "Graph Neural Network (GNN)",
  "Autoencoder (AE)",
  "Variational Autoencoder (VAE)",
  "Attention-based Architecture",
  "Perceiver-style Architecture",
  "Mixture of Experts (MoE)",
  "Retrieval-Augmented Model (RAG)",
  "Generalist Agent Architecture",
  "Multi-architecture Ensemble",
  "Other - {High-Level Architecture Name}"
]

**Architecture Selection Guidelines:**
- For variations of Transformers (BERT, GPT, T5, etc.) → choose appropriate Transformer category
- For CNN variants (ResNet, VGG, DenseNet, etc.) → choose "ResNet Architecture" or "Convolutional Neural Network (CNN)"
- For state space models (Mamba, S4, etc.) → choose "State Space Model (Mamba/S4)"
- For hybrid models → choose the DOMINANT architecture type or specific hybrid category
- For LSTM/GRU variants → choose "Long Short-Term Memory (LSTM)" or "Recurrent Neural Network (RNN)"
- **For novel architectures:** Use "Other - {High-Level Architecture Name}" format (e.g., "Other - Neural ODE", "Other - Capsule Network", "Other - Memory Network")

19. Task — Specific tasks or applications the model was designed for (e.g., "text classification", "image generation", "speech recognition", "question answering")

---

## OUTPUT FORMAT REQUIREMENTS

**CRITICAL**: Your response must be a **valid JSON array** containing one or more model objects. Follow this exact structure:

### Single Model Example:
```
[
  {
    "model_name": {
      "value": "GPT-4",
      "confidence": 100,
      "references": "Abstract, Section 1"
    },
    "domain": {
      "value": ["Language"],
      "confidence": 100,
      "references": "Abstract"
    },
    "parameters": {
      "value": "1.7T",
      "confidence": 85,
      "references": "Section 3.2"
    },
    "task": {
      "value": ["language modeling/generation", "chat", "question answering"],
      "confidence": 90,
      "references": "Abstract, Section 1"
    }
  }
]
```

### Multiple Models Example:
```
[
  {
    "model_name": {
      "value": "BERT-Base",
      "confidence": 100,
      "references": "Table 1"
    },
    "parameters": {
      "value": "110M",
      "confidence": 100,
      "references": "Table 1"
    },
    "task": {
      "value": ["language modeling/generation"],
      "confidence": 95,
      "references": "Section 2"
    }
  },
  {
    "model_name": {
      "value": "BERT-Large", 
      "confidence": 100,
      "references": "Table 1"
    },
    "parameters": {
      "value": "340M",
      "confidence": 100,
      "references": "Table 1"
    },
    "task": {
      "value": ["language modeling/generation"],
      "confidence": 95,
      "references": "Section 2"
    }
  }
]
```

### Key Format Rules:
- **Always start with `[` and end with `]`** - this creates a JSON array
- **Each model is a JSON object `{...}` inside the array**
- **Separate multiple models with commas**: `[{model1}, {model2}]`
- **Each field has exactly three properties**: "value", "confidence", "references"
- **Use arrays for multi-value fields**: `["Language", "Multimodal"]` or `["text", "image"]` or `["chat", "question answering"]`

---

The result must be returned as a **JSON array**. Each element in the array must be a JSON object corresponding to a **distinct model variant**.

For each model, follow this structure:

[
  {
    "model_name": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "domain": {
      "value": [<<list of domains or "n/a">>],
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "organization": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "authors": {
      "value": [<<list of names>> or "n/a"],
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "publication_date": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "parameters": {
      "value": "<<value (as a number) or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "training_dataset": {
      "value": [<<list of datasets or "n/a">>],
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "training_dataset_size": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "epochs": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "training_time": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "training_hardware": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "hardware_quantity": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "hardware_utilization": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "base_model": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "batch_size": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "input_modality": {
      "value": [<<list of modalities or "n/a">>],
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "output_modality": {
      "value": [<<list of modalities or "n/a">>],
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "architecture": {
      "value": "<<value from list or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "task": {
      "value": [<<list of tasks or "n/a">>],
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    }
  }
]

---

Additional Instructions:

- If multiple model variants are described (e.g., Mini, Base, Large), extract one object per variant.
- **CRITICAL**: When a paper lists multiple parameter counts for different model sizes (e.g., "2.0M, 2.4M, 3.2M, 37M, 47M, 49M"), create separate model objects for each parameter size. Do NOT combine parameter counts into a single value like "{2.0m,2.4m,3.2m,37m,47m,49m}".
- Do not combine multiple model variants into a single object unless **no distinct technical details are available** for each variant.
- Only use the information provided in the publication. If a field is not found, use `"n/a"` as the value.
- Use verbatim quotes or section titles as references (e.g., "Section 3.2" or "Table 1"). If from a table, write `(Table: <table name>)`.
- Do not infer from external knowledge or model naming alone — rely strictly on the publication content.

---

Confidence Scoring Guidelines (0–100):
- **100**: Direct, unambiguous quote (e.g., "The model has 70B parameters.")
- **90–99**: Explicit but slightly indirect (e.g., "Parameters: 70B" in a table)
- **80–89**: Strongly implied (e.g., "We scale to 70B parameters" in figure caption)
- **70–79**: Contextual (e.g., "Our model is 10x the size of GPT-3 (175B)" → inferred 1.75T)
- **50–69**: Weak implication (e.g., "Trained on 1M samples" in a related section)
- **0–49**: Unreliable or speculative

---

**FINAL REMINDER**: Only output the JSON array. No markdown code blocks (no ```json```), no commentary, no explanation. Start directly with `[` and end with `]`.

<<PubStart>>
"""

# Prompt template for chunked analysis (first/middle chunks)
CHUNKED_ANALYSIS_TEMPLATE = """
You are a PHD-level computer scientist and research analyst. Your task is to extract key information from a scientific publication provided in Markdown format.

IMPORTANT: This is PART of a longer document that has been split due to length limitations. Focus on extracting information ONLY from this part. You may see incomplete sections. Do NOT try to guess information that isn't clearly stated in THIS part of the text.

The publication content will appear after the marker <<<PubStart>>>.

Your extraction goals are to identify and extract technical details for **each distinct model variant** described in THIS PART of the paper (e.g., ModelName-Mini, ModelName-Large, ModelName-Pro). Each model variant must be represented as a separate JSON object.

For each model variant, extract the following items (ONLY if present in THIS PART):

1. Model name
2. Domain — Select all fitting domains from the following standardized list (do not invent or paraphrase):
[
  "3D modeling",
  "Audio",
  "Biology",
  "Driving",
  "Earth science",
  "Games",
  "Image generation",
  "Language",
  "Materials science",
  "Mathematics",
  "Medicine",
  "Multimodal",
  "Other",
  "Recommendation",
  "Robotics",
  "Search",
  "Speech",
  "Video",
  "Vision"
]
3. Organization (institution or company that developed the model)
4. Authors
5. Publication date
6. Parameters (model size in parameters) — For Mixture of Experts models, report only the TOTAL parameter count, not activated parameters (e.g., if you see "389B total, 52B activated", report "389B"). When a range is given (e.g., "50-70B parameters"), always select the LARGEST value ("70B"). Format as numeric values or with M/B suffixes (e.g., "4.5M", "273.9B") - never use commas, scientific notation strings, or other formats.
7. Training dataset
8. Training dataset size (number of datapoints / tokens)
9. Epochs
10. Training time (in hours)
11. Training hardware
12. Hardware quantity
13. Hardware utilization
14. Base model (if the model builds upon another)
15. Batch size
16. Input Modality — one or more of: "text", "image", "audio", "video", "multimodal"
17. Output Modality — one or more of: "text", "image", "audio", "video", "multimodal"
18. Architecture — Select **one** from the following standardized list. If the exact architecture isn't listed, choose the CLOSEST match rather than using "Other". Only use "Other - {High-Level Architecture Name}" when truly novel architectures don't fit any category:
[
  "Transformer (Encoder-only)",
  "Transformer (Decoder-only)",
  "Transformer (Encoder-Decoder)",
  "Vision Transformer (ViT)",
  "Multimodal Transformer",
  "State Space Model (Mamba/S4)",
  "Convolutional Neural Network (CNN)",
  "ResNet Architecture",
  "EfficientNet Architecture",
  "Hybrid CNN-Transformer",
  "CNN-RNN Hybrid",
  "Recurrent Neural Network (RNN)",
  "Long Short-Term Memory (LSTM)",
  "Diffusion Model",
  "Latent Diffusion Model",
  "Generative Adversarial Network (GAN)",
  "Graph Neural Network (GNN)",
  "Autoencoder (AE)",
  "Variational Autoencoder (VAE)",
  "Attention-based Architecture",
  "Perceiver-style Architecture",
  "Mixture of Experts (MoE)",
  "Retrieval-Augmented Model (RAG)",
  "Generalist Agent Architecture",
  "Multi-architecture Ensemble",
  "Other - {High-Level Architecture Name}"
]

**Architecture Selection Guidelines:**
- For variations of Transformers (BERT, GPT, T5, etc.) → choose appropriate Transformer category
- For CNN variants (ResNet, VGG, DenseNet, etc.) → choose "ResNet Architecture" or "Convolutional Neural Network (CNN)"
- For state space models (Mamba, S4, etc.) → choose "State Space Model (Mamba/S4)"
- For hybrid models → choose the DOMINANT architecture type or specific hybrid category
- For LSTM/GRU variants → choose "Long Short-Term Memory (LSTM)" or "Recurrent Neural Network (RNN)"
- **For novel architectures:** Use "Other - {High-Level Architecture Name}" format (e.g., "Other - Neural ODE", "Other - Capsule Network", "Other - Memory Network")

19. Task — Specific tasks or applications the model was designed for (e.g., "text classification", "image generation", "speech recognition", "question answering")

---

## OUTPUT FORMAT REQUIREMENTS (PARTIAL DOCUMENT)

**CRITICAL**: Your response must be a **valid JSON array**. Since this is a partial document, you may have incomplete information.

### Partial Information Example:
```
[
  {
    "model_name": {
      "value": "NewModel-7B",
      "confidence": 100,
      "references": "Section 1"
    },
    "domain": {
      "value": ["Language"],
      "confidence": 90,
      "references": "Abstract mentions language tasks"
    },
    "task": {
      "value": ["question answering", "chat"],
      "confidence": 85,
      "references": "Abstract mentions QA and chat capabilities"
    }
  }
]
```

### Key Points for Partial Documents:
- **Include only fields you find information for in THIS PART**
- **It's OK to have incomplete models** - other parts will fill in missing information
- **Use lower confidence (30-40) for incomplete/fragmented information**
- **Always return a valid JSON array even if mostly empty**

---

The result must be returned as a **JSON array**. Each element in the array must be a JSON object corresponding to a **distinct model variant**.

For each model, follow this structure:

[
  {
    "model_name": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "domain": {
      "value": [<<list of domains or "n/a">>],
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "task": {
      "value": [<<list of tasks or "n/a">>],
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    // Include other fields only if they are found in THIS PART of the document
  }
]

---

Additional Instructions:

- Remember, you are only analyzing THIS PART of the document. Other parts will be analyzed separately.
- Focus on what's clearly stated in THIS PART. If information is only partially available, extract what you can.
- For each field, ONLY include it if you find relevant information in THIS PART.
- Use "n/a" as the value and lower confidence (30-40) if information is hinted at but incomplete.
- It's perfectly acceptable to have incomplete models or missing fields. The information will be combined later.
- Include the exact quote and location for references to help with later verification.
- **CRITICAL**: When a paper lists multiple parameter counts for different model sizes (e.g., "2.0M, 2.4M, 3.2M, 37M, 47M, 49M"), create separate model objects for each parameter size. Do NOT combine parameter counts into a single value like "{2.0m,2.4m,3.2m,37m,47m,49m}".

---

Confidence Scoring Guidelines (0–100):
- **100**: Direct, unambiguous quote (e.g., "The model has 70B parameters.")
- **90–99**: Explicit but slightly indirect (e.g., "Parameters: 70B" in a table)
- **80–89**: Strongly implied (e.g., "We scale to 70B parameters" in figure caption)
- **70–79**: Contextual (e.g., "Our model is 10x the size of GPT-3 (175B)" → inferred 1.75T)
- **50–69**: Weak implication (e.g., "Trained on 1M samples" in a related section)
- **30–49**: Incomplete or fragmented information
- **0–29**: Unreliable or extremely speculative

---

**FINAL REMINDER**: Only output the JSON array. No markdown code blocks, no commentary. Start with `[` and end with `]`.

<<PubStart>>
"""

# Prompt template for chunked analysis (final chunk)
CHUNKED_ANALYSIS_FINAL_TEMPLATE = """
You are a PHD-level computer scientist and research analyst. Your task is to extract key information from a scientific publication provided in Markdown format.

IMPORTANT: This is the FINAL PART of a longer document that has been split due to length limitations. Focus on extracting information ONLY from this part. Previous parts have already been analyzed separately.

The publication content will appear after the marker <<<PubStart>>>.

Your extraction goals are to identify and extract technical details for **each distinct model variant** described in THIS PART of the paper (e.g., ModelName-Mini, ModelName-Large, ModelName-Pro). Each model variant must be represented as a separate JSON object.

For each model variant, extract the following items (ONLY if present in THIS PART):

1. Model name
2. Domain — Select all fitting domains from the following standardized list (do not invent or paraphrase):
[
  "3D modeling",
  "Audio",
  "Biology",
  "Driving",
  "Earth science",
  "Games",
  "Image generation",
  "Language",
  "Materials science",
  "Mathematics",
  "Medicine",
  "Multimodal",
  "Other",
  "Recommendation",
  "Robotics",
  "Search",
  "Speech",
  "Video",
  "Vision"
]
3. Organization (institution or company that developed the model)
4. Authors
5. Publication date
6. Parameters (model size in parameters) — For Mixture of Experts models, report only the TOTAL parameter count, not activated parameters (e.g., if you see "389B total, 52B activated", report "389B"). When a range is given (e.g., "50-70B parameters"), always select the LARGEST value ("70B"). Format as numeric values or with M/B suffixes (e.g., "4.5M", "273.9B") - never use commas, scientific notation strings, or other formats.
7. Training dataset
8. Training dataset size (number of datapoints / tokens)
9. Epochs
10. Training time (in hours)
11. Training hardware
12. Hardware quantity
13. Hardware utilization
14. Base model (if the model builds upon another)
15. Batch size
16. Input Modality — one or more of: "text", "image", "audio", "video", "multimodal"
17. Output Modality — one or more of: "text", "image", "audio", "video", "multimodal"
18. Architecture — Select **one** from the following standardized list. If the exact architecture isn't listed, choose the CLOSEST match rather than using "Other". Only use "Other - {High-Level Architecture Name}" when truly novel architectures don't fit any category:
[
  "Transformer (Encoder-only)",
  "Transformer (Decoder-only)",
  "Transformer (Encoder-Decoder)",
  "Vision Transformer (ViT)",
  "Multimodal Transformer",
  "State Space Model (Mamba/S4)",
  "Convolutional Neural Network (CNN)",
  "ResNet Architecture",
  "EfficientNet Architecture",
  "Hybrid CNN-Transformer",
  "CNN-RNN Hybrid",
  "Recurrent Neural Network (RNN)",
  "Long Short-Term Memory (LSTM)",
  "Diffusion Model",
  "Latent Diffusion Model",
  "Generative Adversarial Network (GAN)",
  "Graph Neural Network (GNN)",
  "Autoencoder (AE)",
  "Variational Autoencoder (VAE)",
  "Attention-based Architecture",
  "Perceiver-style Architecture",
  "Mixture of Experts (MoE)",
  "Retrieval-Augmented Model (RAG)",
  "Generalist Agent Architecture",
  "Multi-architecture Ensemble",
  "Other - {High-Level Architecture Name}"
]

**Architecture Selection Guidelines:**
- For variations of Transformers (BERT, GPT, T5, etc.) → choose appropriate Transformer category
- For CNN variants (ResNet, VGG, DenseNet, etc.) → choose "ResNet Architecture" or "Convolutional Neural Network (CNN)"
- For state space models (Mamba, S4, etc.) → choose "State Space Model (Mamba/S4)"
- For hybrid models → choose the DOMINANT architecture type or specific hybrid category
- For LSTM/GRU variants → choose "Long Short-Term Memory (LSTM)" or "Recurrent Neural Network (RNN)"
- **For novel architectures:** Use "Other - {High-Level Architecture Name}" format (e.g., "Other - Neural ODE", "Other - Capsule Network", "Other - Memory Network")

19. Task — Specific tasks or applications the model was designed for (e.g., "text classification", "image generation", "speech recognition", "question answering")

---

## OUTPUT FORMAT REQUIREMENTS (FINAL PART)

**CRITICAL**: Your response must be a **valid JSON array**. This is the final part, so focus on conclusions, results, and any summary information.

### Final Part Example:
```
[
  {
    "model_name": {
      "value": "FinalModel",
      "confidence": 95,
      "references": "Conclusion"
    },
    "training_time": {
      "value": "48 hours",
      "confidence": 100,
      "references": "Appendix A"
    },
    "task": {
      "value": ["language modeling/generation", "question answering"],
      "confidence": 90,
      "references": "Conclusion section"
    }
  }
]
```

---

The result must be returned as a **JSON array**. Each element in the array must be a JSON object corresponding to a **distinct model variant**.

For each model, follow this structure:

[
  {
    "model_name": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "domain": {
      "value": [<<list of domains or "n/a">>],
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "organization": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "authors": {
      "value": [<<list of names>> or "n/a"],
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "publication_date": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "parameters": {
      "value": "<<value (as a number) or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "training_dataset": {
      "value": [<<list of datasets or "n/a">>],
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "training_dataset_size": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "epochs": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "training_time": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "training_hardware": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "hardware_quantity": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "hardware_utilization": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "base_model": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "batch_size": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "input_modality": {
      "value": [<<list of modalities or "n/a">>],
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "output_modality": {
      "value": [<<list of modalities or "n/a">>],
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "architecture": {
      "value": "<<value from list or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "task": {
      "value": [<<list of tasks or "n/a">>],
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    }
  }
]

---

Additional Instructions:

- If multiple model variants are described (e.g., Mini, Base, Large), extract one object per variant.
- **CRITICAL**: When a paper lists multiple parameter counts for different model sizes (e.g., "2.0M, 2.4M, 3.2M, 37M, 47M, 49M"), create separate model objects for each parameter size. Do NOT combine parameter counts into a single value like "{2.0m,2.4m,3.2m,37m,47m,49m}".
- Do not combine multiple model variants into a single object unless **no distinct technical details are available** for each variant.
- Only use the information provided in the publication. If a field is not found, use `"n/a"` as the value.
- Use verbatim quotes or section titles as references (e.g., "Section 3.2" or "Table 1"). If from a table, write `(Table: <table name>)`.
- Do not infer from external knowledge or model naming alone — rely strictly on the publication content.

---

Confidence Scoring Guidelines (0–100):
- **100**: Direct, unambiguous quote (e.g., "The model has 70B parameters.")
- **90–99**: Explicit but slightly indirect (e.g., "Parameters: 70B" in a table)
- **80–89**: Strongly implied (e.g., "We scale to 70B parameters" in figure caption)
- **70–79**: Contextual (e.g., "Our model is 10x the size of GPT-3 (175B)" → inferred 1.75T)
- **50–69**: Weak implication (e.g., "Trained on 1M samples" in a related section)
- **0–49**: Unreliable or speculative

---

**FINAL REMINDER**: Only output the JSON array. No markdown code blocks, no commentary. Start with `[` and end with `]`.

<<PubStart>>
"""

# Prompt template for progressive chunked analysis (subsequent chunks)
CHUNKED_PROGRESSIVE_TEMPLATE = """
You are a PHD-level computer scientist and research analyst. Your task is to extract key information from a scientific publication provided in Markdown format.

IMPORTANT: This is PART of a longer document that has been split due to length limitations. Focus on extracting information ONLY from this part. You may see incomplete sections. Do NOT try to guess information that isn't clearly stated in THIS part of the text.

IMPORTANT: You will see previous results extracted from earlier parts of the document after the marker <<<PreviousResults>>>. Use this information as context, but focus on extracting NEW or MORE DETAILED information from the current part. If you find information that contradicts previous results, use the version with higher confidence.

The publication content will appear after the marker <<<PubStart>>>.

Your extraction goals are to identify and extract technical details for **each distinct model variant** described in THIS PART of the paper (e.g., ModelName-Mini, ModelName-Large, ModelName-Pro). Each model variant must be represented as a separate JSON object.

For each model variant, extract the following items (ONLY if present in THIS PART):

1. Model name
2. Domain — Select all fitting domains from the following standardized list (do not invent or paraphrase):
[
  "3D modeling",
  "Audio",
  "Biology",
  "Driving",
  "Earth science",
  "Games",
  "Image generation",
  "Language",
  "Materials science",
  "Mathematics",
  "Medicine",
  "Multimodal",
  "Other",
  "Recommendation",
  "Robotics",
  "Search",
  "Speech",
  "Video",
  "Vision"
]
3. Organization (institution or company that developed the model)
4. Authors
5. Publication date
6. Parameters (model size in parameters) — For Mixture of Experts models, report only the TOTAL parameter count, not activated parameters (e.g., if you see "389B total, 52B activated", report "389B"). When a range is given (e.g., "50-70B parameters"), always select the LARGEST value ("70B"). Format as numeric values or with M/B suffixes (e.g., "4.5M", "273.9B") - never use commas, scientific notation strings, or other formats.
7. Training dataset
8. Training dataset size (number of datapoints / tokens)
9. Epochs
10. Training time (in hours)
11. Training hardware
12. Hardware quantity
13. Hardware utilization
14. Base model (if the model builds upon another)
15. Batch size
16. Input Modality — one or more of: "text", "image", "audio", "video", "multimodal"
17. Output Modality — one or more of: "text", "image", "audio", "video", "multimodal"
18. Architecture — Select **one** from the following standardized list. If the exact architecture isn't listed, choose the CLOSEST match rather than using "Other". Only use "Other - {High-Level Architecture Name}" when truly novel architectures don't fit any category:
[
  "Transformer (Encoder-only)",
  "Transformer (Decoder-only)",
  "Transformer (Encoder-Decoder)",
  "Vision Transformer (ViT)",
  "Multimodal Transformer",
  "State Space Model (Mamba/S4)",
  "Convolutional Neural Network (CNN)",
  "ResNet Architecture",
  "EfficientNet Architecture",
  "Hybrid CNN-Transformer",
  "CNN-RNN Hybrid",
  "Recurrent Neural Network (RNN)",
  "Long Short-Term Memory (LSTM)",
  "Diffusion Model",
  "Latent Diffusion Model",
  "Generative Adversarial Network (GAN)",
  "Graph Neural Network (GNN)",
  "Autoencoder (AE)",
  "Variational Autoencoder (VAE)",
  "Attention-based Architecture",
  "Perceiver-style Architecture",
  "Mixture of Experts (MoE)",
  "Retrieval-Augmented Model (RAG)",
  "Generalist Agent Architecture",
  "Multi-architecture Ensemble",
  "Other - {High-Level Architecture Name}"
]

**Architecture Selection Guidelines:**
- For variations of Transformers (BERT, GPT, T5, etc.) → choose appropriate Transformer category
- For CNN variants (ResNet, VGG, DenseNet, etc.) → choose "ResNet Architecture" or "Convolutional Neural Network (CNN)"
- For state space models (Mamba, S4, etc.) → choose "State Space Model (Mamba/S4)"
- For hybrid models → choose the DOMINANT architecture type or specific hybrid category
- For LSTM/GRU variants → choose "Long Short-Term Memory (LSTM)" or "Recurrent Neural Network (RNN)"
- **For novel architectures:** Use "Other - {High-Level Architecture Name}" format (e.g., "Other - Neural ODE", "Other - Capsule Network", "Other - Memory Network")

19. Task — Specific tasks or applications the model was designed for (e.g., "text classification", "image generation", "speech recognition", "question answering")

---

## OUTPUT FORMAT REQUIREMENTS (PROGRESSIVE UPDATE)

**CRITICAL**: Your response must be a **valid JSON array**. You should build upon the previous results while adding new information from this part.

### Progressive Example:
Previous results: `[{"model_name": {"value": "GPT-X", "confidence": 100, "references": "Title"}}]`

Current part adds architecture and task info, so you return:
```
[
  {
    "model_name": {
      "value": "GPT-X",
      "confidence": 100,
      "references": "Title"
    },
    "architecture": {
      "value": "Transformer (Decoder-only)",
      "confidence": 100,
      "references": "Section 2"
    },
    "task": {
      "value": ["language modeling/generation", "chat"],
      "confidence": 95,
      "references": "Section 2.1"
    }
  }
]
```

### Rules for Progressive Updates:
- **Always return COMPLETE model objects** (include previous + new information)
- **Merge information from previous results with new findings**
- **When conflicts arise, use the higher confidence value**
- **Add new model variants if found in this part**

---

The result must be returned as a **JSON array**. Each element in the array must be a JSON object corresponding to a **distinct model variant**.

For each model, follow this structure:

[
  {
    "model_name": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "domain": {
      "value": [<<list of domains or "n/a">>],
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "task": {
      "value": [<<list of tasks or "n/a">>],
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    // Include other fields only if they are found in THIS PART of the document or in previous results
  }
]

---

Additional Instructions:

- Remember, you are only analyzing THIS PART of the document along with previous results.
- For model variants found in previous results, add or update fields based on new information in this part.
- For new model variants not in previous results, create new model objects.
- When you have both previous and new information for a field, use the one with higher confidence.
- Include exact quotes and locations for references to help with later verification.
- Always return COMPLETE model objects, including fields from previous results you're not updating.
- **CRITICAL**: When a paper lists multiple parameter counts for different model sizes (e.g., "2.0M, 2.4M, 3.2M, 37M, 47M, 49M"), create separate model objects for each parameter size. Do NOT combine parameter counts into a single value like "{2.0m,2.4m,3.2m,37m,47m,49m}".

---

Confidence Scoring Guidelines (0–100):
- **100**: Direct, unambiguous quote (e.g., "The model has 70B parameters.")
- **90–99**: Explicit but slightly indirect (e.g., "Parameters: 70B" in a table)
- **80–89**: Strongly implied (e.g., "We scale to 70B parameters" in figure caption)
- **70–79**: Contextual (e.g., "Our model is 10x the size of GPT-3 (175B)" → inferred 1.75T)
- **50–69**: Weak implication (e.g., "Trained on 1M samples" in a related section)
- **30–49**: Incomplete or fragmented information
- **0–29**: Unreliable or extremely speculative

---

**FINAL REMINDER**: Only output the JSON array. No markdown code blocks, no commentary. Start with `[` and end with `]`.

<<<PreviousResults>>>
{previous_results}
<<<PubStart>>>
"""

# Prompt template for progressive chunked analysis (final chunk)
CHUNKED_PROGRESSIVE_FINAL_TEMPLATE = """
You are a PHD-level computer scientist and research analyst. Your task is to extract key information from a scientific publication provided in Markdown format.

IMPORTANT: This is the FINAL PART of a longer document that has been split due to length limitations. You have been provided with information extracted from previous parts to help with your analysis. Focus on completing and finalizing all model details.

IMPORTANT: You will see previous results extracted from earlier parts of the document after the marker <<<PreviousResults>>>. Use this information as context and incorporate it into your final response. If you find information that contradicts previous results, use the version with higher confidence or more detail.

The publication content will appear after the marker <<<PubStart>>>.

Your extraction goals are to identify and extract technical details for **each distinct model variant** described across ALL PARTS of the paper (e.g., ModelName-Mini, ModelName-Large, ModelName-Pro). Each model variant must be represented as a separate JSON object.

For each model variant, extract or finalize the following items:

1. Model name
2. Domain — Select all fitting domains from the following standardized list (do not invent or paraphrase):
[
  "3D modeling",
  "Audio",
  "Biology",
  "Driving",
  "Earth science",
  "Games",
  "Image generation",
  "Language",
  "Materials science",
  "Mathematics",
  "Medicine",
  "Multimodal",
  "Other",
  "Recommendation",
  "Robotics",
  "Search",
  "Speech",
  "Video",
  "Vision"
]
3. Organization (institution or company that developed the model)
4. Authors
5. Publication date
6. Parameters (model size in parameters) — For Mixture of Experts models, report only the TOTAL parameter count, not activated parameters (e.g., if you see "389B total, 52B activated", report "389B"). When a range is given (e.g., "50-70B parameters"), always select the LARGEST value ("70B"). Format as numeric values or with M/B suffixes (e.g., "4.5M", "273.9B") - never use commas, scientific notation strings, or other formats.
7. Training dataset
8. Training dataset size (number of datapoints / tokens)
9. Epochs
10. Training time (in hours)
11. Training hardware
12. Hardware quantity
13. Hardware utilization
14. Base model (if the model builds upon another)
15. Batch size
16. Input Modality — one or more of: "text", "image", "audio", "video", "multimodal"
17. Output Modality — one or more of: "text", "image", "audio", "video", "multimodal"
18. Architecture — Select **one** from the following standardized list. If the exact architecture isn't listed, choose the CLOSEST match rather than using "Other". Only use "Other - {High-Level Architecture Name}" when truly novel architectures don't fit any category:
[
  "Transformer (Encoder-only)",
  "Transformer (Decoder-only)",
  "Transformer (Encoder-Decoder)",
  "Vision Transformer (ViT)",
  "Multimodal Transformer",
  "State Space Model (Mamba/S4)",
  "Convolutional Neural Network (CNN)",
  "ResNet Architecture",
  "EfficientNet Architecture",
  "Hybrid CNN-Transformer",
  "CNN-RNN Hybrid",
  "Recurrent Neural Network (RNN)",
  "Long Short-Term Memory (LSTM)",
  "Diffusion Model",
  "Latent Diffusion Model",
  "Generative Adversarial Network (GAN)",
  "Graph Neural Network (GNN)",
  "Autoencoder (AE)",
  "Variational Autoencoder (VAE)",
  "Attention-based Architecture",
  "Perceiver-style Architecture",
  "Mixture of Experts (MoE)",
  "Retrieval-Augmented Model (RAG)",
  "Generalist Agent Architecture",
  "Multi-architecture Ensemble",
  "Other - {High-Level Architecture Name}"
]

**Architecture Selection Guidelines:**
- For variations of Transformers (BERT, GPT, T5, etc.) → choose appropriate Transformer category
- For CNN variants (ResNet, VGG, DenseNet, etc.) → choose "ResNet Architecture" or "Convolutional Neural Network (CNN)"
- For state space models (Mamba, S4, etc.) → choose "State Space Model (Mamba/S4)"
- For hybrid models → choose the DOMINANT architecture type or specific hybrid category
- For LSTM/GRU variants → choose "Long Short-Term Memory (LSTM)" or "Recurrent Neural Network (RNN)"
- **For novel architectures:** Use "Other - {High-Level Architecture Name}" format (e.g., "Other - Neural ODE", "Other - Capsule Network", "Other - Memory Network")

19. Task — Specific tasks or applications the model was designed for (e.g., "text classification", "image generation", "speech recognition", "question answering")

---

## OUTPUT FORMAT REQUIREMENTS (FINAL CONSOLIDATION)

**CRITICAL**: This is your FINAL response for the entire document. Return a **complete JSON array** with all model information consolidated.

### Final Consolidated Example:
```
[
  {
    "model_name": {
      "value": "CompleteModel-7B",
      "confidence": 100,
      "references": "Abstract, Section 1"
    },
    "domain": {
      "value": ["Language", "Multimodal"],
      "confidence": 100,
      "references": "Abstract, Section 2"
    },
    "parameters": {
      "value": "7B",
      "confidence": 100,
      "references": "Table 1"
    },
    "architecture": {
      "value": "Transformer (Decoder-only)",
      "confidence": 100,
      "references": "Section 2.1"
    },
    "task": {
      "value": ["language modeling/generation", "question answering", "chat"],
      "confidence": 100,
      "references": "Abstract, Section 1, Section 3"
    },
    "base_model": {
      "value": "n/a",
      "confidence": 0,
      "references": "Not mentioned in document"
    }
  }
]
```

### Final Consolidation Rules:
- **Include ALL available fields for each model** (use "n/a" if never found)
- **Combine information from all parts of the document**
- **Resolve conflicts by using highest confidence or most detailed information**
- **Ensure every model object is complete and coherent**

---

The result must be returned as a **JSON array**. Each element in the array must be a JSON object corresponding to a **distinct model variant**.

For each model, follow this structure:

[
  {
      "model_name": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "domain": {
      "value": [<<list of domains or "n/a">>],
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "organization": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "authors": {
      "value": [<<list of names>> or "n/a"],
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "publication_date": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "parameters": {
      "value": "<<value (as a number) or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "training_dataset": {
      "value": [<<list of datasets or "n/a">>],
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "training_dataset_size": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "epochs": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "training_time": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "training_hardware": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "hardware_quantity": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "hardware_utilization": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "base_model": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "batch_size": {
      "value": "<<value or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "input_modality": {
      "value": [<<list of modalities or "n/a">>],
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "output_modality": {
      "value": [<<list of modalities or "n/a">>],
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "architecture": {
      "value": "<<value from list or n/a>>",
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    },
    "task": {
      "value": [<<list of tasks or "n/a">>],
      "confidence": <<integer 0–100>>,
      "references": "<<section name or quote>>"
    }
  }
]

---

Additional Instructions:

- If multiple model variants are described (e.g., Mini, Base, Large), extract one object per variant.
- **CRITICAL**: When a paper lists multiple parameter counts for different model sizes (e.g., "2.0M, 2.4M, 3.2M, 37M, 47M, 49M"), create separate model objects for each parameter size. Do NOT combine parameter counts into a single value like "{2.0m,2.4m,3.2m,37m,47m,49m}".
- Do not combine multiple model variants into a single object unless **no distinct technical details are available** for each variant.
- Only use the information provided in the publication. If a field is not found, use `"n/a"` as the value.
- Use verbatim quotes or section titles as references (e.g., "Section 3.2" or "Table 1"). If from a table, write `(Table: <table name>)`.
- Do not infer from external knowledge or model naming alone — rely strictly on the publication content.

---

Confidence Scoring Guidelines (0–100):
- **100**: Direct, unambiguous quote (e.g., "The model has 70B parameters.")
- **90–99**: Explicit but slightly indirect (e.g., "Parameters: 70B" in a table)
- **80–89**: Strongly implied (e.g., "We scale to 70B parameters" in figure caption)
- **70–79**: Contextual (e.g., "Our model is 10x the size of GPT-3 (175B)" → inferred 1.75T)
- **50–69**: Weak implication (e.g., "Trained on 1M samples" in a related section)
- **0–49**: Unreliable or speculative

---

**FINAL REMINDER**: Only output the JSON array. No markdown code blocks, no commentary. Start with `[` and end with `]`.

<<<PreviousResults>>>
{previous_results}
<<<PubStart>>>
"""