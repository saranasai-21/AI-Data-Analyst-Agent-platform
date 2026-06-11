"""
ReportAgent -- generates structured JSON slide data per section.

Each section is generated concurrently with a strict schema that
enforces 3-6 concise bullet **fragments** (not sentences) and an
optional ``cards`` array for metric-heavy sections like Key Findings.
"""

import json
import concurrent.futures

from core.gemini_service import generate_text


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPORT_SECTIONS = [
    "Executive Summary",
    "Key Findings",
    "Trends",
    "Opportunities",
    "Risks",
    "Strategic Recommendations",
    "Conclusion",
]

# Sections that should return metric cards instead of bullets.
CARD_SECTIONS = {"Key Findings"}

BULLET_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "slides": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "title": {
                        "type": "STRING",
                        "description": "Short slide title, 2-5 words.",
                    },
                    "bullets": {
                        "type": "ARRAY",
                        "items": {
                            "type": "STRING",
                            "description": "A concise bullet FRAGMENT (not a sentence). Max 10 words.",
                        },
                    },
                },
                "required": ["title", "bullets"],
            },
        }
    },
    "required": ["slides"],
}

CARD_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "slides": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "title": {
                        "type": "STRING",
                        "description": "Short slide title, 2-5 words.",
                    },
                    "cards": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "label": {
                                    "type": "STRING",
                                    "description": "Metric label, e.g. 'Average Income'.",
                                },
                                "value": {
                                    "type": "STRING",
                                    "description": "Metric value, e.g. '$108K'.",
                                },
                            },
                            "required": ["label", "value"],
                        },
                    },
                },
                "required": ["title", "cards"],
            },
        }
    },
    "required": ["slides"],
}


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

_BULLET_PROMPT = """You are a Senior Management Consultant preparing an executive presentation deck.

## Section to Generate: {section_name}

## Dataset Summary
{dataset_summary}

## Analysis Output
{analysis_result}

## User Question
{query}

## STRICT Rules
1. Return exactly ONE slide object for the "{section_name}" section.
2. The slide must contain between 3 and 6 bullet points.
3. Each bullet must be a SHORT FRAGMENT -- NOT a full sentence.
   GOOD: "Revenue up 20% YoY"
   BAD:  "The revenue increased by 20% compared to last year."
4. Max 10 words per bullet.
5. Use REAL numbers from the data -- no placeholders.
6. No greetings, no markdown, no sub-sections.
7. Title must be 2-5 words.
"""

_CARD_PROMPT = """You are a Senior Management Consultant preparing an executive presentation deck.

## Section to Generate: {section_name}

## Dataset Summary
{dataset_summary}

## Analysis Output
{analysis_result}

## User Question
{query}

## STRICT Rules
1. Return exactly ONE slide object for the "{section_name}" section.
2. The slide must contain between 3 and 6 METRIC CARDS.
3. Each card has a short "label" (e.g. "Average Income") and a "value" (e.g. "$108K").
4. Use REAL numbers from the data -- no placeholders or generic text.
5. No greetings, no markdown, no sub-sections.
6. Title must be 2-5 words.
"""


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class ReportAgent:
    """Generates structured JSON slide content for each report section."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    # ------------------------------------------------------------------
    # Single-section generation
    # ------------------------------------------------------------------

    def run_section(
        self,
        section_name: str,
        query: str,
        dataset_summary: str,
        analysis_result: str,
    ) -> dict:
        is_card = section_name in CARD_SECTIONS

        if is_card:
            prompt = _CARD_PROMPT.format(
                section_name=section_name,
                dataset_summary=dataset_summary,
                analysis_result=analysis_result,
                query=query,
            )
            schema = CARD_SCHEMA
        else:
            prompt = _BULLET_PROMPT.format(
                section_name=section_name,
                dataset_summary=dataset_summary,
                analysis_result=analysis_result,
                query=query,
            )
            schema = BULLET_SCHEMA

        try:
            raw = generate_text(
                self.api_key,
                prompt,
                temperature=0.15,
                max_output_tokens=1500,
                response_schema=schema,
            )
            data = json.loads(raw)
            return self._enforce_constraints(data, section_name, is_card)
        except Exception:
            if is_card:
                return {
                    "slides": [
                        {
                            "title": section_name,
                            "cards": [{"label": "Status", "value": "Unavailable"}],
                        }
                    ]
                }
            return {
                "slides": [
                    {
                        "title": section_name,
                        "bullets": ["Content generation temporarily unavailable."],
                    }
                ]
            }

    # ------------------------------------------------------------------
    # Full report (concurrent)
    # ------------------------------------------------------------------

    def generate_full_report_sections(
        self,
        query: str,
        dataset_summary: str,
        analysis_result: str,
    ) -> dict:
        report: dict[str, dict] = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(REPORT_SECTIONS)) as pool:
            futures = {
                pool.submit(
                    self.run_section, sec, query, dataset_summary, analysis_result
                ): sec
                for sec in REPORT_SECTIONS
            }
            for future in concurrent.futures.as_completed(futures):
                section = futures[future]
                try:
                    report[section] = future.result()
                except Exception:
                    report[section] = {
                        "slides": [
                            {
                                "title": section,
                                "bullets": ["Content generation temporarily unavailable."],
                            }
                        ]
                    }

        return report

    # ------------------------------------------------------------------
    # Post-processing
    # ------------------------------------------------------------------

    @staticmethod
    def _enforce_constraints(data: dict, section_name: str, is_card: bool) -> dict:
        if "slides" not in data:
            if is_card:
                return {"slides": [{"title": section_name, "cards": [{"label": "Status", "value": "N/A"}]}]}
            return {"slides": [{"title": section_name, "bullets": ["No content generated."]}]}

        for slide in data["slides"]:
            if is_card:
                cards = slide.get("cards", [])
                if len(cards) > 6:
                    slide["cards"] = cards[:6]
            else:
                bullets = slide.get("bullets", [])
                trimmed = []
                for b in bullets:
                    words = b.split()
                    if len(words) > 15:
                        b = " ".join(words[:15])
                    trimmed.append(b)
                if len(trimmed) > 6:
                    trimmed = trimmed[:6]
                slide["bullets"] = trimmed

        return data
