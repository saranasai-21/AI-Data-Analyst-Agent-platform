from core.gemini_service import generate_text


class InsightAgent:

    def __init__(self, api_key):

        self.api_key = api_key

    def build_prompt(
        self,
        query,
        dataset_summary,
        analysis_result
    ):

        return f"""You are a Senior Data Analyst writing a concise business insight report.

## Dataset Summary
{dataset_summary}

## Analysis Output
{analysis_result}

## User Question
{query}

## Instructions
Write REAL, SPECIFIC insights based ONLY on the actual data above. Do NOT use placeholder text, template phrases, or generic statements. Do NOT write things like "[Insert description]" or "[mention time period]".
CRITICAL: Do NOT include any formal greetings, conversational openings (like "Good morning", "Hello everyone"), or pleasantries. Start immediately with the required sections.


Structure your response with these exact sections using markdown:

**Executive Summary:**
Write 2-3 sentences summarising the most important findings from the data above.

**Key Findings:**
- List 3-4 specific, numbered observations directly drawn from the analysis result.

**Trends:**
- Identify 3-4 patterns visible in the numbers or categories.

**Opportunities:**
- List 3-4 actionable opportunities based on the data findings.

**Risks:**
- List 3-4 risks or concerns evident in the data.

Use only facts from the dataset summary and analysis output above. Be direct and specific.
"""

    def run(
        self,
        query,
        dataset_summary,
        analysis_result
    ):

        try:

            return generate_text(
                self.api_key,
                self.build_prompt(
                    query,
                    dataset_summary,
                    analysis_result,
                ),
                temperature=0.15,
                max_output_tokens=3000,
            )

        except Exception as e:

            return f"Insight generation failed: {str(e)}"
