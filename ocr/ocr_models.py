from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional

class ImageType(str, Enum):
    GRAPH = "graph"
    CHART = "chart"
    DIAGRAM = "diagram"
    TABLE = "table"
    FIGURE = "figure"
    SCREENSHOT = "screenshot"
    PHOTO = "photo"
    ILLUSTRATION = "illustration"
    TEXT_IMAGE = "text_image"
    LOGO = "logo"
    OTHER = "other"

class DataVisualizationType(str, Enum):
    BAR_CHART = "bar_chart"
    LINE_GRAPH = "line_graph"
    SCATTER_PLOT = "scatter_plot"
    PIE_CHART = "pie_chart"
    HISTOGRAM = "histogram"
    BOX_PLOT = "box_plot"
    HEATMAP = "heatmap"
    FLOW_CHART = "flow_chart"
    NETWORK_DIAGRAM = "network_diagram"
    ARCHITECTURE_DIAGRAM = "architecture_diagram"
    OTHER = "other"

class ImageAnnotation(BaseModel):
    image_type: ImageType = Field(
        ..., 
        description="The primary type/category of the image content"
    )
    
    title: Optional[str] = Field(
        None,
        description="The title or caption of the image if visible"
    )
    
    detailed_description: str = Field(
        ...,
        description="Comprehensive description of what is shown in the image, including all visible text, data, patterns, and visual elements"
    )
    
    data_content: Optional[str] = Field(
        None,
        description="Specific data values, numbers, labels, or quantitative information visible in the image"
    )
    
    visualization_type: Optional[DataVisualizationType] = Field(
        None,
        description="Specific type of data visualization if the image contains charts or graphs"
    )
    
    key_insights: Optional[str] = Field(
        None,
        description="Key findings, trends, or important information that can be derived from the image"
    )
    
    text_content: Optional[str] = Field(
        None,
        description="Any text visible within the image (labels, annotations, legends, etc.)"
    )
    
    technical_details: Optional[str] = Field(
        None,
        description="Technical specifications, methodological details, or scientific information shown"
    )
    
    context_relevance: Optional[str] = Field(
        None,
        description="How this image relates to the surrounding document content and its importance"
    )

def response_format_from_pydantic_model(model_class):
    """Convert Pydantic model to response format for Mistral OCR API"""
    return {
        "type": "json_schema",
        "json_schema": {
            "name": model_class.__name__,
            "schema": model_class.model_json_schema(),
            "strict": True
        }
    }
