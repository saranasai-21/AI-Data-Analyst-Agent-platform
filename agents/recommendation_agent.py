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
CRITICAL: Do NOT include any formal greetings, conversational openings (like "Good morning", "Hello everyone"), or pleasantries. Start immediately with the required sections.


Structure your response with 2-4 relevant recommendations sections using markdown.
The section titles must be dynamic, context-aware, and directly related to the User Question, Analysis Output, and Analyst Insights (e.g., if the query is about revenue optimization, sections should be about 'Pricing Action Items', 'Marketing Budget Adjustments', etc.). Do NOT use generic section titles like 'Strategic Recommendations' if they don't fit the question.
Each section must start with a clear markdown heading (e.g. '## Section Title') and contain 2-4 bullet points (start each with a dash '- ') with concrete, data-driven actionable items.

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
