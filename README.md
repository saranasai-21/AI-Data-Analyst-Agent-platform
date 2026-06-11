
---
title: AI Data Analyst
emoji: 📊
colorFrom: indigo
colorTo: purple
sdk: streamlit
sdk_version: 1.58.0
app_file: app.py
pinned: false
---

# 📊 AI Data Analyst Agent

An advanced, autonomous multi-agent data analytics and reporting system developed using **Google Gemini, LangGraph, and Streamlit**.
This project profiles datasets, performs data quality checks, executes pandas code dynamically in a secure sandbox, renders interactive plotly visualizations, and generates professional PDF/PowerPoint reports based on natural language queries.

# 📌 Project Overview

Automated data analysis and insight generation is critical for:

- Assessing data quality and profiling anomalies
- Fast exploratory data analysis (EDA)
- Creating visual representations of complex patterns
- Accelerating business decision-making
- Generating structured executive business reports
- Democratizing data access via natural language interfaces

This project uses a **LangGraph-based multi-agent orchestration workflow** to analyze datasets, write/execute Python code, extract insights, and format findings into PDFs/PowerPoints.

# 🤖 Multi-Agent Architecture

The multi-agent graph orchestrates several specialized agents:

- **DataQualityAgent**: Performs null checks, duplicate checks, and outlier detection.
- **ProfilingAgent**: Summarizes columns, data types, and basic statistics.
- **AnalysisAgent**: Formulates and executes Pandas-based queries in a secure AST evaluation sandbox.
- **VisualizationAgent**: Automatically plots interactive figures using Plotly.
- **InsightAgent**: Synthesizes execution results to draft bulleted analytical findings.
- **RecommendationAgent**: Translates data insights into tactical business recommendations.
- **MemoryAgent**: Manages session memory and history for conversational context.

# 📊 Key Features & Security

The system was built with the following features:

- **Multi-format Input Ingestion**: Supports CSV, Excel, JSON, SQLite, and PDF files (via Gemini table parsing).
- **AST-based Safe Evaluation Sandbox**: The code evaluation engine checks the syntax tree using `ast` parser before execution, prohibiting forbidden commands (`exec`, `eval`, `open`, etc.) or module imports (`os`, `sys`, `subprocess`, etc.) to prevent shell escapes or data exposure.
- **Programmatic Python SDK**: Fully decoupled `sdk/` package allows importing and running sessions directly in Python scripts and Jupyter notebooks.
- **Auto-generated Business Documents**: Automatically builds and exports PDF reports (via ReportLab) and PowerPoint presentations (via python-pptx).

# 📈 System Workflow & Pipeline

| Stage | Agent / Component | Input | Output / Action |
|---|---|---|---|
| 1. Ingestion | `DataLoader` | Raw file (CSV/Excel/JSON/SQLite/PDF) | Cleaned pandas DataFrame |
| 2. Quality Check | `DataQualityAgent` | DataFrame | Null value, outlier & duplicate detection |
| 3. Profiling | `ProfilingAgent` | DataFrame | Column types, summary stats & shape |
| 4. Code Execution | `AnalysisAgent` | Query + DataFrame | Validated and executed Python code results |
| 5. Visualization | `VisualizationAgent` | Query + DataFrame | Dynamic and interactive Plotly chart specs |
| 6. Insights | `InsightAgent` | Analysis Result | Key analytical and business findings |
| 7. Recommendations | `RecommendationAgent` | Insights | Tactical business recommendations |

# Interpretation

- The multi-agent architecture operates on a LangGraph state graph.
- The parallelized fast-track workflow uses ThreadPoolExecutor to run Data Quality + Profiling and Analysis + Visualization in parallel, speeding up end-to-end execution.
- The safe executor intercepts and parses code using python's AST parser to prevent execution of unauthorized system commands.
- Report builders convert plotly charts and structured text directly to PDF and slide formats.

# Technologies Used

- Python
- LangGraph (Agentic Workflow orchestration)
- Google Gemini API (`google-genai`)
- Streamlit (Web interface)
- Pandas & NumPy (Data manipulation)
- Plotly (Data visualization)
- ReportLab (PDF generator)
- python-pptx (PowerPoint presentation generator)
- SQLAlchemy (SQLite database connection)
- python-dotenv

# 🚀 Streamlit Application

The Streamlit dashboard allows users to:

- Upload raw datasets in various formats
- Explore profile summaries and quality report tabs
- Chat with agents using natural language
- View executed python code, plotly charts, and insights
- Download generated PDF reports and PPT presentations
- Inspect agent execution traces and latency metrics

## Run the Project

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

# 📂 Project Structure

```text
AI-Data-Analyst-Agent/
│
├── agents/                     # Specialized LangGraph Agent Definitions
│   ├── analysis_agent.py
│   ├── data_quality_agent.py
│   ├── insight_agent.py
│   ├── memory_agent.py
│   ├── planner_agent.py
│   ├── profiling_agent.py
│   ├── recommendation_agent.py
│   └── visualization_agent.py
│
├── core/                       # Core system logic and services
│   ├── code_validator.py       # AST validator for safe code execution
│   ├── config.py               # Settings and configuration
│   ├── data_loader.py          # Data ingestion (CSV, Excel, SQLite, etc.)
│   ├── gemini_service.py       # Wrapper for Google Gemini Client
│   ├── safe_executor.py        # Secure sandbox execution environment
│   └── state_manager.py        # Streamlit state manager
│
├── orchestrator/               # Agent orchestration & workflow definitions
│   └── graph.py                # LangGraph state graph definitions
│
├── sdk/                        # Decoupled python SDK package
│   ├── __init__.py
│   ├── client.py
│   └── session.py
│
├── services/                   # Export and document services
│   ├── pdf_service.py          # PDF report generator
│   └── presentation_service.py # PPTX slide generator
│
├── app.py                      # Streamlit application entry point
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```

Developed as a multi-agent and data analytics assistant using LangGraph and Google Gemini.

# 🌐 Live Demo

Hugging Face Space: https://huggingface.co/spaces/saranasai/AI-Data-Analyst

# Interface

<img width="1904" height="708" alt="Screenshot 2026-06-11 154256" src="https://github.com/user-attachments/assets/b1d7ce4d-0f92-4e13-9e7d-8a0d216c5d00" />


