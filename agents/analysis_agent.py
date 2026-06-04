import re
import pandas as pd

from core.code_validator import CodeValidator
from core.gemini_service import generate_text
from core.safe_executor import SafeExecutor


class AnalysisAgent:

    def __init__(self, api_key):

        self.api_key = api_key

    def _build_prompt(
        self,
        query,
        columns,
        conversation
    ):

        return f"""
You are an expert Data Analyst.

Dataset Columns:
{columns}

Conversation Context:
{conversation}

Current User Question:
{query}

The dataframe is already available as:

df

Rules:

1. Generate ONLY executable pandas code.
2. No markdown.
3. No explanations.
4. No imports.
5. No file operations.
6. No networking.
7. Store final answer in variable:

result

Examples:

result = df["Sales"].mean()

result = (
    df.groupby("Region")["Revenue"]
    .sum()
    .sort_values(ascending=False)
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
            temperature=0.1,
            max_output_tokens=700,
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

        return SafeExecutor.execute_pandas(
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

            result = self.execute_code(
                code,
                df
            )

            return {

                "success": True,

                "generated_code": code,

                "result": result

            }

        except Exception as e:

            return {

                "success": False,

                "generated_code": "",

                "result": str(e)

            }
