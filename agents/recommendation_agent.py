from core.gemini_service import generate_text


class RecommendationAgent:

    def __init__(self, api_key):

        self.api_key = api_key

    def build_prompt(
        self,
        query,
        dataset_summary,
        analysis_result,
        insights
    ):

        return f"""You are a Senior Business Consultant writing actionable recommendations.

## Dataset Summary
{dataset_summary}

## Analysis Output
{analysis_result}

## Analyst Insights
{insights}

## User Question
{query}

## Instructions
Write SPECIFIC, ACTIONABLE recommendations based ONLY on the actual data and insights above. Do NOT use placeholder text, vague phrases, or generic statements. Every recommendation must reference specific columns, values or patterns from the data.

Structure your response with these exact sections using markdown:

**Strategic Recommendations:**
1. Write 2-3 concrete strategic actions with specific measurable targets based on the data.

**Immediate Actions (This Week):**
1. List 2-3 quick wins that can be acted on immediately from the data findings.

**Business Improvements:**
1. Identify 2-3 process or operational improvements supported by the data.

**Growth Opportunities:**
1. List 2-3 specific growth vectors evidenced in the dataset.

**Risk Mitigation:**
1. List 2-3 specific risks with concrete mitigation steps derived from the data.

Be direct, specific and data-driven. Reference actual column names and values where relevant.
"""

    def run(
        self,
        query,
        dataset_summary,
        analysis_result,
        insights
    ):

        try:

            return generate_text(
                self.api_key,
                self.build_prompt(
                    query,
                    dataset_summary,
                    analysis_result,
                    insights,
                ),
                temperature=0.15,
                max_output_tokens=3000,
            )

        except Exception as e:

            return f"Recommendation generation failed: {str(e)}"
