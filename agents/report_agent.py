import json
from core.gemini_service import generate_text

class ReportAgent:
    def __init__(self, api_key):
        self.api_key = api_key
        
    def build_prompt(self, section_name, query, dataset_summary, analysis_result):
        return f"""You are a Senior Data Analyst generating a specific section for an enterprise presentation deck.

## Section to Generate: {section_name}

## Dataset Summary
{dataset_summary}

## Analysis Output
{analysis_result}

## User Question
{query}

## Instructions
Write REAL, SPECIFIC insights for the "{section_name}" section based ONLY on the actual data above.
Do NOT use placeholder text, template phrases, or generic statements.
Do NOT include formal greetings.
CRITICAL: You MUST provide strictly 5-8 concise bullet points per slide. 
Do NOT write long paragraphs. Keep each bullet point brief and actionable.
Do NOT create sub-sections.
"""

    def run_section(self, section_name, query, dataset_summary, analysis_result):
        prompt = self.build_prompt(section_name, query, dataset_summary, analysis_result)
        
        response_schema = {
            "type": "OBJECT",
            "properties": {
                "slides": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "title": {"type": "STRING", "description": "The title of the slide"},
                            "bullets": {
                                "type": "ARRAY",
                                "items": {"type": "STRING", "description": "A bullet point"}
                            }
                        },
                        "required": ["title", "bullets"]
                    }
                }
            },
            "required": ["slides"]
        }
        
        try:
            response_text = generate_text(
                self.api_key,
                prompt,
                temperature=0.15,
                max_output_tokens=2000,
                response_schema=response_schema
            )
            return json.loads(response_text)
        except Exception as e:
            return {"slides": [{"title": f"Error: {section_name}", "bullets": [f"Failed to generate: {str(e)}"]}]}

    def generate_full_report_sections(self, query, dataset_summary, analysis_result):
        sections = [
            "Executive Summary",
            "Key Findings",
            "Trends",
            "Opportunities",
            "Risks",
            "Recommendations",
            "Conclusion"
        ]
        
        report_data = {}
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(sections)) as executor:
            future_to_section = {
                executor.submit(self.run_section, section, query, dataset_summary, analysis_result): section
                for section in sections
            }
            for future in concurrent.futures.as_completed(future_to_section):
                section = future_to_section[future]
                try:
                    report_data[section] = future.result()
                except Exception as exc:
                    report_data[section] = {"slides": [{"title": f"Error: {section}", "bullets": [f"Generation failed: {str(exc)}"]}]}
            
        return report_data
