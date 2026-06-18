import re

import pandas as pd

import plotly.express as px
import plotly.graph_objects as go

from core.code_validator import CodeValidator
from core.gemini_service import generate_text
from core.safe_executor import SafeExecutor


class VisualizationAgent:

    def __init__(
        self,
        api_key
    ):

        self.api_key = api_key

    def _build_prompt(
        self,
        query,
        columns,
        conversation
    ):

        return f"""
You are a Senior Data Visualization Expert.

Dataset Columns:
{columns}

Conversation Context:
{conversation}

User Query:
{query}

The dataframe is available as:

df

Available Libraries:

px
go
pd

Rules:

1. Generate ONLY executable Plotly code.
2. No markdown.
3. No explanations.
4. No imports.
5. No networking.
6. No file operations.
7. Store final chart in variable:

fig

8. If a column represents numeric values but contains symbols or formats (e.g. percentages like '85%', or rates/ratios like '2 / 14'), clean the values (e.g. stripping '%', extracting numeric parts, or evaluating fractions) and convert them to numeric type using pd.to_numeric before plotting.
9. Always generate a graphical chart (e.g., px.bar, px.line, px.scatter, px.pie, etc.) rather than a table structure like go.Table. Never use go.Table. If the query asks for summary statistics (like averages of multiple columns), compute the values first (e.g., using pd.DataFrame or pd.Series) and plot them as a bar chart (using px.bar or go.Bar) so it displays as an actual graph.
10. If the user query is asking for "insights" or contains the word "insight" (case-insensitive), you MUST generate a 3D Plotly graph (e.g. `px.scatter_3d` or `go.Scatter3d` using three relevant numerical columns). For all other queries, generate a related 2D Plotly graph (e.g. `px.bar`, `px.line`, `px.scatter`, `px.pie`, etc.) and NEVER a 3D graph.

Examples:

fig = px.bar(
    df,
    x="Region",
    y="Revenue"
)

Return code only.
"""

    def _extract_code(self, text):
        """Robustly extract Python code from LLM response text."""
        match = re.search(r"```python\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

        match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

        code = text.strip()
        code = re.sub(r"```python|```", "", code)
        return code.strip()

    def generate_code(
        self,
        query,
        columns,
        conversation,
        error_context=None,
    ):
        if error_context:
            prompt = (
                self._build_prompt(query, columns, conversation)
                + f"\n\nYour previous code had a syntax error:\n{error_context}\n"
                  "Fix the error and return ONLY valid, executable Plotly code. No markdown, no explanations."
            )
        else:
            prompt = self._build_prompt(query, columns, conversation)

        text = generate_text(
            self.api_key,
            prompt,
            temperature=0.15,
            max_output_tokens=900,
            is_code=True,
        )

        return self._extract_code(text)

    def validate_code(
        self,
        code
    ):

        CodeValidator.validate(
            code
        )

        return True

    def execute_code(
        self,
        code,
        df
    ):

        return SafeExecutor.execute_plotly(
            code,
            df
        )

    def _build_column_context(self, df):
        lines = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            non_null_samples = df[col].dropna().unique()[:3]
            samples_str = ", ".join(repr(s) for s in non_null_samples)
            lines.append(f"- {col} (type: {dtype}, samples: [{samples_str}])")
        return "\n".join(lines)

    MAX_RETRIES = 2

    def run(
        self,
        query,
        df,
        conversation
    ):

        column_context = self._build_column_context(df)
        code = ""
        last_error = None

        for attempt in range(1 + self.MAX_RETRIES):
            try:
                code = self.generate_code(
                    query=query,
                    columns=column_context,
                    conversation=conversation,
                    error_context=last_error,
                )

                self.validate_code(code)

                fig = self.execute_code(code, df)

                return {
                    "success": True,
                    "generated_code": code,
                    "figure": fig,
                }

            except Exception as e:
                last_error = f"Code:\n{code}\n\nError: {e}"
                if attempt == self.MAX_RETRIES:
                    return {
                        "success": False,
                        "generated_code": code,
                        "figure": None,
                        "error": str(e),
                    }

