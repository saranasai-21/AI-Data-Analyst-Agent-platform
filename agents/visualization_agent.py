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

Examples:

fig = px.bar(
    df,
    x="Region",
    y="Revenue"
)

Return code only.
"""

    def generate_code(
        self,
        query,
        columns,
        conversation
    ):

        text = generate_text(
            self.api_key,
            self._build_prompt(
                query,
                columns,
                conversation,
            ),
            temperature=0.15,
            max_output_tokens=900,
        )

        code = text.strip()

        code = re.sub(
            r"```python|```",
            "",
            code
        )

        return code.strip()

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

    def run(
        self,
        query,
        df,
        conversation
    ):

        try:

            code = self.generate_code(

                query=query,

                columns=list(df.columns),

                conversation=conversation

            )

            self.validate_code(
                code
            )

            fig = self.execute_code(
                code,
                df
            )

            return {

                "success": True,

                "generated_code": code,

                "figure": fig

            }

        except Exception as e:

            return {

                "success": False,

                "generated_code": "",

                "figure": None,

                "error": str(e)

            }
