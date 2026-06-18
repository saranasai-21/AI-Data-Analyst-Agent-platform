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

8. Do NOT truncate or limit results using .head() or similar methods unless specifically requested by the user. Always return the full matching dataset.
9. If a column represents numeric values but contains symbols or formats (e.g. percentages like '85%', or rates/ratios like '2 / 14'), clean the values (e.g. stripping '%', extracting numeric parts, or evaluating fractions) and convert them to numeric type using pd.to_numeric before performing aggregations like .mean().

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
            is_code=True,
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

    def _build_column_context(self, df):
        lines = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            non_null_samples = df[col].dropna().unique()[:3]
            samples_str = ", ".join(repr(s) for s in non_null_samples)
            lines.append(f"- {col} (type: {dtype}, samples: [{samples_str}])")
        return "\n".join(lines)

    def run(
        self,
        query,
        df,
        conversation
    ):

        try:

            column_context = self._build_column_context(df)
            code = self.generate_code(

                query=query,

                columns=column_context,

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
