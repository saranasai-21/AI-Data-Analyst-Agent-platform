---
title: AI Data Analyst
emoji: 📊
colorFrom: indigo
colorTo: purple
sdk: docker
pinned: false
license: apache-2.0
---


# AI Data Analyst Agent

An autonomous, multi-agent AI data analyst that assesses data quality, profiles datasets, executes pandas code dynamically in a safe evaluation sandbox, creates visualization charts, and generates business reports (PDF & PowerPoint presentations) based on your natural language questions.

## Features
- **Multi-Agent Orchestration**: Powered by a parallelized LangGraph agent graph (`DataQualityAgent`, `ProfilingAgent`, `AnalysisAgent`, `VisualizationAgent`, `InsightAgent`, `RecommendationAgent`).
- **Flexible UI**: Streamlit web interface with interactive tables, charts, execution trace logging, and PDF/PPTX builders.
- **Programmatic SDK**: Fully decoupled `sdk/` package allows importing and running sessions directly in Python scripts and Jupyter notebooks.
- **Support for Multi-format Inputs**: Load datasets via CSV, Excel, JSON, SQLite, or PDF files (via Gemini table parsing).

## Getting Started

### Local Setup
1. Clone the repository.
2. Initialize virtual environment and install packages:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Or `.venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and set your `GEMINI_API_KEY`:
   ```bash
   cp .env.example .env
   ```
4. Run the Streamlit application:
   ```bash
   streamlit run app.py
   ```

### Docker Setup
1. Build the image:
   ```bash
   docker build -t ai-data-analyst .
   ```
2. Run the container:
   ```bash
   docker run -p 7860:7860 -e GEMINI_API_KEY="your_api_key_here" ai-data-analyst
   ```

### Programmatic SDK Usage
```python
import pandas as pd
from sdk.client import AIAnalystClient

# Initialize client
client = AIAnalystClient(api_key="your_gemini_api_key")

# Load a local dataset or SQLite database
df = client.load_data("data/sales.csv")

# Create a session
session = client.create_session(df, file_name="sales_data")

# Run agentic query analysis
result = session.analyze("Show average revenue by product line.")

# Export generated documents
pdf_report = session.export_pdf("outputs/report.pdf")
ppt_presentation = session.export_presentation("outputs/presentation.pptx")
```

## Security & Safety
- **Safe Evaluation Sandbox**: The code evaluation engine checks the syntax tree using `ast` parser before execution, prohibiting forbidden commands (`exec`, `eval`, `open`, etc.) or module imports (`os`, `sys`, `subprocess`, etc.) to prevent shell escapes or data exposure.
- **Environment Exclusions**: Local secrets (`.env`) and cache/venv directories are fully ignored by `.gitignore` and `.dockerignore`.
>>>>>>> 59e8bc6 (Initial commit)
