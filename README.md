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

# 🚀 Autonomous AI Data Analyst Platform
**A High-Performance, Multi-Agent Data Analytics Engine powered by LangGraph & Google Gemini**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Hugging%20Face-blue?style=for-the-badge&logo=huggingface)](https://huggingface.co/spaces/saranasai/AI-Data-Analyst)
[![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)](#)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-orange?style=for-the-badge)](#)
[![Gemini](https://img.shields.io/badge/LLM-Gemini%202.5%20Flash-green?style=for-the-badge)](#)

---

## 🎯 Executive Summary
The **Autonomous AI Data Analyst** is an enterprise-grade platform designed to democratize data science. By bridging natural language processing with a secure, sandboxed execution environment, it allows business stakeholders to instantly ingest raw datasets, profile anomalies, generate interactive 3D visualizations, and export comprehensive PDF reports—all within seconds.

This project demonstrates advanced architectural patterns in **Agentic AI**, securely turning raw data into strategic business value with zero coding required from the end-user.

---

## 💡 Key Capabilities
- **🧠 Multi-Agent Orchestration**: Utilizes a directed acyclic graph (via `LangGraph`) of specialized agents (Profiling, Quality, Analysis, Visualization, Insights, and Recommendations) that divide and conquer complex analytical tasks.
- **⚡ Ultra-Low Latency AI**: Fully optimized with **Gemini 2.5 Flash** and multithreaded workflow parallelization to deliver exhaustively detailed analysis and charts in a fraction of traditional LLM wait times.
- **🛡️ Secure Code Sandbox**: Employs an AST (Abstract Syntax Tree) code validator to safely execute AI-generated Pandas queries dynamically while aggressively preventing system-level vulnerabilities.
- **📈 Dynamic Visual Engine**: Automatically writes Plotly code to render interactive, multi-dimensional charts (including 3D scatter/surface plots) tailored precisely to user queries.
- **📑 Automated PDF Reporting**: Features a headless engine (ReportLab + Kaleido Chromium) to invisibly snap UI visualizations and embed them into structured, paginated executive PDF documents.

---

## 🏗️ Technical Architecture

The platform architecture is built around a decoupled **Agentic State Graph**. Instead of relying on a monolithic LLM prompt, the system routes the user's dataset through a pipeline of micro-agents:

1. **Ingestion Layer (`DataLoader`)**: Parses CSV, Excel, SQLite, JSON, and uses Gemini Vision to extract tabular data directly from PDFs.
2. **Quality & Profiling Agents**: Run parallel scans across the dataset to identify nulls, duplicates, outliers, and schema definitions.
3. **Execution Layer (`AnalysisAgent` & `VisualizationAgent`)**: Translates human queries into valid Python logic. Runs the code within `SafeExecutor` to extract literal answers and interactive chart blueprints.
4. **Synthesis Layer (`InsightAgent` & `RecommendationAgent`)**: Interprets the raw Python execution results and formulates exhaustive, deeply analytical business recommendations.

### 🛠️ Technology Stack
* **AI & Orchestration**: Google Gemini 2.5, LangGraph
* **Data Engine**: Pandas, NumPy, SQLAlchemy
* **Visualization**: Plotly, Kaleido (Headless Export)
* **Frontend**: Streamlit
* **Document Generation**: ReportLab

---

## 🚀 Live Demo & Interface

Experience the speed and depth of the platform live on Hugging Face:
🔗 **[Launch the AI Data Analyst](https://huggingface.co/spaces/saranasai/AI-Data-Analyst)**

<img width="1904" height="708" alt="Platform Interface" src="https://github.com/user-attachments/assets/b1d7ce4d-0f92-4e13-9e7d-8a0d216c5d00" />

---

## 💻 Local Quick Start

1. **Clone & Environment Setup**
   ```bash
   git clone https://github.com/saranasai-21/AI-Data-Analyst-Agent-platform.git
   cd AI-Data-Analyst-Agent-platform
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configuration**
   Copy the `.env.example` file to `.env` and insert your Gemini API Key.
   ```bash
   GEMINI_API_KEY="your_api_key_here"
   ```

3. **Boot the Application**
   ```bash
   streamlit run app.py
   ```

---

## 📂 Codebase Structure

```text
AI-Data-Analyst-Agent/
├── agents/             # Specialized Micro-Agents (Profiling, Insights, Viz)
├── core/               # System Engine (AST Sandbox, Config, LLM API wrapper)
├── orchestrator/       # LangGraph routing and parallel ThreadPoolExecution
├── services/           # Document processors (PDF generation & Kaleido snap)
├── sdk/                # Python-native library for programmatic access
├── app.py              # Main Streamlit UI deployment
└── requirements.txt    # Frozen dependency graph
```
