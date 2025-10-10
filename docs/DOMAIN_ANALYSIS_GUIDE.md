# Domain Analysis Guide

This guide explains how to use the new domain analysis capabilities to implement your comprehensive analysis plan.

##  **Your Analysis Plan Implementation**

The new system implements **all** the analyses you requested with **enhanced array parsing** for multi-value fields.

###  **Array Value Parsing**

The system now automatically handles multi-value fields that contain arrays like:
- `{vision, language, robotics}` → counts as 3 separate domains
- `[transformer, cnn, rnn]` → counts as 3 separate architectures  
- `"text, image, audio"` → counts as 3 separate modalities

**This gives much more accurate counts and trends!**

##  **Your Analysis Plan Implementation**

The new system implements **all** the analyses you requested:

### 1. **Publication Trends** 
- **1a) Publication count over time** → `get_publication_trends()`
- **1b) Domain trends (stacked chart)** → `get_domain_trends()`
- **1c) Robotics focus** → `get_robotics_trends()`

### 2. **Model Size Analysis** 
- **2a) Parameter size over time** → `get_parameter_size_analysis()`
- **2b) Domain parameter comparison** → `get_domain_parameter_comparison()`
- **2c) Modality parameter analysis** → `get_modality_analysis()`
- **2d) Architecture parameter analysis** → `get_architecture_trends()`

### 3. **Modality Analysis** 
- **3a) Modality trends over time** → `get_modality_analysis()`
- **3b) Domain-modality matrices** → `create_domain_modality_matrix()`

### 4. **Architecture Analysis** 
- **4a) Architecture trends over time** → `get_architecture_trends()`
- **4b) Domain-architecture matrices** → `create_domain_architecture_matrix()`

##  **Quick Start Options**

### **Option 1: Run Everything at Once**
```bash
python examples/comprehensive_domain_analysis.py
```
This runs all analyses from your plan in one go.

### **Option 2: Quick Insights Only**
```bash
python examples/quick_insights.py
```
This runs the most important analyses for quick insights.

### **Option 3: Interactive Notebook**
Open `domain_analysis_demo.ipynb` in Jupyter and run cells step by step.

### **Option 4: Custom Analysis**
```python
from analyser.domain_analysis import DomainAnalyzer

# Initialize
analyzer = DomainAnalyzer()

# Run specific analyses
pub_trends = analyzer.get_publication_trends()
domain_trends = analyzer.get_domain_trends(top_k=10)
robotics_trends = analyzer.get_robotics_trends()
```

##  **Available Data Fields**

Based on your database, you have access to:

**Core Fields:**
- `model_name` (34,093 entries)
- `domain` (33,888 entries)
- `architecture` (33,515 entries)
- `parameters` (33,407 entries)
- `task` (33,387 entries)
- `organization` (32,881 entries)
- `authors` (32,724 entries)
- `training_dataset` (32,586 entries)
- `input_modality` (32,476 entries)
- `output_modality` (32,437 entries)

**Robotics-Specific Fields:**
- `environment_types` (689 entries)
- `robot_type` (689 entries)
- `sensor_modalities` (689 entries)
- `sim2real_transfer` (689 entries)
- `control_type` (689 entries)
- `policy_representation` (689 entries)

**Training Fields:**
- `training_dataset_size` (31,628 entries)
- `training_hardware` (31,548 entries)
- `batch_size` (31,512 entries)
- `epochs` (31,400 entries)
- `training_time` (31,287 entries)

##  **Analysis Examples**

### **Publication Trends**
```python
# Get publication trends by year
pub_trends = analyzer.get_publication_trends(group_by='year')

# Get domain trends (top 10 domains)
domain_trends = analyzer.get_domain_trends(top_k=10)

# Focus on robotics
robotics_trends = analyzer.get_robotics_trends()
```

### **Model Size Analysis**
```python
# Parameter size evolution
param_trends = analyzer.get_parameter_size_analysis(log_scale=True)

# Compare domains
domain_comparison = analyzer.get_domain_parameter_comparison(top_domains=10)

# Analyze by modality
input_modalities = analyzer.get_modality_analysis(modality_type='input')
output_modalities = analyzer.get_modality_analysis(modality_type='output')
```

### **Cross-Domain Analysis**
```python
# Domain-modality relationships
domain_input_matrix = create_domain_modality_matrix(
    analyzer, modality_type='input'
)

# Domain-architecture relationships
domain_arch_matrix = create_domain_architecture_matrix(analyzer)
```

##  **Customization Options**

### **Filter by Date Range**
```python
# Analyze only recent data (last 2 years)
recent_trends = analyzer.get_publication_trends(
    run_id_start=8000,  # Adjust based on your data
    run_id_end=None
)
```

### **Filter by Run ID Range**
```python
# Analyze specific extraction runs
filtered_analysis = analyzer.get_domain_trends(
    run_id_start=1000,
    run_id_end=5000
)
```

### **Custom Visualization Settings**
```python
# Custom figure sizes
large_plot = analyzer.get_domain_trends(
    top_k=15,
    figsize=(20, 12)
)

# Logarithmic scaling
log_analysis = analyzer.get_parameter_size_analysis(
    log_scale=True,
    figsize=(16, 10)
)
```

##  **Expected Insights**

### **Publication Trends**
- **Acceleration patterns**: Look for exponential growth in publication counts
- **Domain shifts**: Identify which domains gained/lost research focus
- **Robotics timeline**: Track when robotics research started accelerating

### **Model Size Analysis**
- **Scaling trends**: Observe parameter count evolution over time
- **Domain differences**: Compare parameter sizes across domains
- **Modality impact**: See how input/output modalities affect model size
- **Architecture influence**: Understand architecture-parameter relationships

### **Modality Analysis**
- **Adoption patterns**: Track which modalities became popular when
- **Domain preferences**: See which domains use which modalities
- **Technology evolution**: Understand modality capability development

### **Architecture Analysis**
- **Usage evolution**: Track architecture popularity over time
- **Domain specialization**: See which domains prefer which architectures
- **Innovation patterns**: Identify new architecture introductions

##  **Best Practices**

### **1. Start with Quick Insights**
```bash
python examples/quick_insights.py
```
Get an overview before diving deep.

### **2. Use the Notebook for Exploration**
Open `domain_analysis_demo.ipynb` to explore interactively.

### **3. Export Data for Further Analysis**
```python
# Save results to CSV
pub_trends.to_csv('publication_trends.csv')
domain_trends.to_csv('domain_trends.csv')
```

### **4. Create Custom Visualizations**
```python
import matplotlib.pyplot as plt
import seaborn as sns

# Custom styling
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# Your custom analysis
custom_plot = analyzer.get_domain_trends(top_k=8)
```

### **5. Combine Multiple Analyses**
```python
# Get comprehensive view
pub_trends = analyzer.get_publication_trends()
domain_trends = analyzer.get_domain_trends()
param_trends = analyzer.get_parameter_size_analysis()

# Combine insights
print(f"Peak publication year: {pub_trends.loc[pub_trends['publication_count'].idxmax(), 'period']}")
print(f"Top domain: {domain_trends.sum().idxmax()}")
```

##  **Next Steps**

1. **Run the quick insights** to get familiar with the system
2. **Explore the notebook** for interactive analysis
3. **Run the comprehensive analysis** for full insights
4. **Customize analyses** for your specific research questions
5. **Export data** for publication-ready figures
6. **Extend the system** with your own analysis functions

##  **File Structure**

```
analyser/
├── domain_analysis.py          #  Core domain analysis functions
├── trend_analysis.py           #  Basic trend analysis
├── csv_processor.py            #  CSV integration
├── config.py                   # ️ Configuration
└── validation.py               # ️ Input validation

examples/
├── comprehensive_domain_analysis.py  #  Full analysis suite
└── quick_insights.py                #  Quick insights

domain_analysis_demo.ipynb      #  Interactive demo notebook
```

##  **Robotics-Specific Analysis**

The system includes specialized analysis for robotics models (run IDs 7866-8087) with **full array parsing support** for multi-value fields:

### **5a) Robot Type Analysis**
```python
# Analyze robot types with temporal trends
robot_types = analyzer.get_robot_type_analysis(
    run_id_start=7866,
    run_id_end=8087,
    include_temporal=True,
    figsize=(15, 8)
)
```

### **5b) Robotics Modality Analysis**
```python
# Analyze input and sensor modalities over time
robotics_modalities = analyzer.get_robotics_modality_analysis(
    run_id_start=7866,
    run_id_end=8087,
    top_k=10,
    figsize=(15, 10)
)
```

### **5c) Modality Development Analysis**
```python
# Track how many modalities each model uses over time
modality_development = analyzer.get_modality_development_analysis(
    run_id_start=7866,
    run_id_end=8087,
    figsize=(12, 8)
)
```

### **5d) Control Type Analysis**
```python
# Analyze control types (pie chart)
control_types = analyzer.get_control_type_analysis(
    run_id_start=7866,
    run_id_end=8087,
    figsize=(10, 8)
)
```

### **5e) Environment Type Analysis**
```python
# Analyze environment types (pie chart)
environment_types = analyzer.get_environment_type_analysis(
    run_id_start=7866,
    run_id_end=8087,
    figsize=(10, 8)
)
```

### **Array Parsing for Robotics Fields**
The robotics analysis automatically handles multi-value fields:
- **Robot types**: `{manipulator, mobile}` → counts as 2 separate types
- **Control types**: `[high_level, low_level]` → counts as 2 separate types  
- **Environment types**: `{indoor, outdoor, simulation}` → counts as 3 separate types
- **Sensor modalities**: `{vision, lidar, imu}` → counts as 3 separate modalities

### **Special Multimodal Handling**
For modality fields (input_modality, output_modality, sensor_modalities), the system automatically:
- **Adds "multimodal"** when multiple values exist but "multimodal" is not present
- **Preserves "multimodal"** when it's already included in the array
- **Does not add "multimodal"** for single values or non-modality fields

Examples:
- `{vision, language}` → `[vision, language, multimodal]` (added)
- `{vision, language, multimodal}` → `[vision, language, multimodal]` (preserved)
- `vision` → `[vision]` (single value, no addition)
- `{manipulator, mobile}` → `[manipulator, mobile]` (non-modality field, no addition)

### **Run Complete Robotics Analysis**
```bash
python examples/robotics_analysis.py
```

##  **Additional Analysis: Training Datasets & Organizations**

### **6a) Training Dataset Analysis**
```python
# Analyze most commonly used training datasets
training_datasets = analyzer.get_training_dataset_analysis(
    run_id_start=1,
    run_id_end=1000,
    top_k=20,
    figsize=(15, 10)
)
```

### **6b) Organization Analysis**
```python
# Analyze organizations involved in model development
organizations = analyzer.get_organization_analysis(
    run_id_start=1,
    run_id_end=1000,
    top_k=20,
    figsize=(15, 10)
)
```

### **Key Features:**
- **Horizontal Bar Charts**: Better readability for long dataset/organization names
- **Array Parsing**: Handles multi-value entries like `{ImageNet, COCO, OpenImages}`
- **Value Labels**: Precise counts displayed on each bar
- **Configurable Top-K**: Focus on most relevant results
- **Statistical Insights**: Distribution analysis and major player identification

##  **You're Ready!**

The system is now set up to implement **all** your analysis requirements, including specialized robotics analysis. Start with the quick insights script and then dive deeper with the comprehensive analysis or interactive notebook.

**Happy analyzing!** 
