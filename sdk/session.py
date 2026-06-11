import os
import pandas as pd
from typing import List, Dict, Any, Optional
from orchestrator.graph import invoke_fast_workflow
from services.pdf_service import PDFService
from services.presentation_service import PresentationService

class AnalysisSession:
    """
    Manages conversational analysis state and document generation.
    """
    def __init__(self, client: Any, df: pd.DataFrame, file_name: str = "dataset"):
        self.client = client
        self.df = df
        self.file_name = file_name
        self.conversation: List[Dict[str, str]] = []
        self.latest_result: Optional[Dict[str, Any]] = None
        self.profile: Dict[str, Any] = {}
        self.quality_report: Dict[str, Any] = {}
        self.dataset_summary: str = ""

    def get_conversation(self) -> List[Dict[str, str]]:
        return self.conversation

    def set_conversation(self, conversation: List[Dict[str, str]]):
        self.conversation = list(conversation)

    def clear_conversation(self):
        self.conversation = []
        self.latest_result = None

    def _compact_conversation(self, conversation: List[Dict[str, str]], max_messages: int = 6, max_chars: int = 2200) -> List[Dict[str, str]]:
        trimmed = conversation[-max_messages:]
        compacted = []
        used = 0

        for item in reversed(trimmed):
            role = item.get("role", "assistant")
            content = str(item.get("content", "")).strip()

            if not content:
                continue

            remaining = max_chars - used
            if remaining <= 0:
                break

            if len(content) > remaining:
                content = content[:remaining]

            compacted.append({"role": role, "content": content})
            used += len(content)

        return list(reversed(compacted))

    def _dict_to_markdown_table(self, d: dict) -> Optional[str]:
        try:
            outer_keys = list(d.keys())
            if not isinstance(d[outer_keys[0]], dict):
                return None
            inner_keys = list(d[outer_keys[0]].keys())
            
            markdown = "| Metric | " + " | ".join(outer_keys) + " |\n"
            markdown += "| :--- | " + " | ".join([":---:" for _ in outer_keys]) + " |\n"
            
            for k in inner_keys:
                row = [f"**{k}**"]
                for col in outer_keys:
                    val = d[col].get(k, "")
                    if isinstance(val, float):
                        row.append(f"{val:,.2f}")
                    else:
                        row.append(str(val))
                markdown += "| " + " | ".join(row) + " |\n"
            return markdown
        except Exception:
            return None

    def _format_agent_value(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, pd.DataFrame):
            try:
                return value.head(12).to_markdown()
            except Exception:
                df_temp = value.head(12)
                cols = list(df_temp.columns)
                markdown = "| " + " | ".join(map(str, cols)) + " |\n"
                markdown += "| " + " | ".join([":---:" for _ in cols]) + " |\n"
                for _, row in df_temp.iterrows():
                    markdown += "| " + " | ".join([f"{val:,.2f}" if isinstance(val, float) else str(val) for val in row]) + " |\n"
                return markdown
        if isinstance(value, pd.Series):
            try:
                return value.to_markdown()
            except Exception:
                df_temp = value.reset_index()
                cols = list(df_temp.columns)
                markdown = "| " + " | ".join(map(str, cols)) + " |\n"
                markdown += "| " + " | ".join([":---:" for _ in cols]) + " |\n"
                for _, row in df_temp.iterrows():
                    markdown += "| " + " | ".join([f"{val:,.2f}" if isinstance(val, float) else str(val) for val in row]) + " |\n"
                return markdown
        if isinstance(value, dict):
            tbl = self._dict_to_markdown_table(value)
            if tbl:
                return tbl
            try:
                items = []
                for k, v in value.items():
                    items.append(f"- **{k}**: {v}")
                return "\n".join(items)
            except Exception:
                pass
        return str(value)

    def analyze(self, query: str) -> Dict[str, Any]:
        """
        Executes the agentic workflow, updating the conversational history state.
        """
        api_key = self.client.api_key
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set.")

        self.conversation.append({"role": "user", "content": query})

        state = {
            "query": query,
            "df": self.df,
            "conversation": self._compact_conversation(self.conversation),
            "profile": self.profile or {},
            "quality_report": self.quality_report or {},
            "dataset_summary": self.dataset_summary or "",
            "analysis_result": {},
            "visualization_result": {},
            "insights": "",
            "recommendations": "",
            "execution_trace": [],
        }

        # Dynamically patch API Key bindings inside the Graph / Agents
        import orchestrator.graph
        import core.config
        orig_graph_key = getattr(orchestrator.graph, "GEMINI_API_KEY", None)
        orig_config_key = getattr(core.config, "GEMINI_API_KEY", None)
        orchestrator.graph.GEMINI_API_KEY = api_key
        core.config.GEMINI_API_KEY = api_key

        try:
            result = invoke_fast_workflow(state)
        finally:
            orchestrator.graph.GEMINI_API_KEY = orig_graph_key
            core.config.GEMINI_API_KEY = orig_config_key

        if result.get("profile"):
            self.profile = result["profile"]
        if result.get("quality_report"):
            self.quality_report = result["quality_report"]
        if result.get("dataset_summary"):
            self.dataset_summary = result["dataset_summary"]

        analysis_res = result.get("analysis_result", {}).get("result")
        insights = result.get("insights")
        ar = self._format_agent_value(analysis_res)
        ir = self._format_agent_value(insights)
        assistant_reply = ar if ar is not None and ar != [] else (ir if ir is not None and ir != [] else "Analysis complete.")

        self.conversation.append({"role": "assistant", "content": str(assistant_reply)})
        self.latest_result = result
        return result

    def export_pdf(self, output_path: str = None) -> str:
        """
        Builds and saves a PDF report.
        """
        if not self.latest_result:
            raise ValueError("No analysis result found. Please run analyze() first.")
        if not output_path:
            clean_name = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in self.file_name).strip("_") or "AI_Report"
            output_path = f"outputs/{clean_name}_report.pdf"

        # Fallback to run quality/profiling if not already present
        if not self.profile or not self.quality_report:
            from agents.data_quality_agent import DataQualityAgent
            from agents.profiling_agent import ProfilingAgent
            if not self.quality_report:
                self.quality_report = DataQualityAgent().run(self.df)
            if not self.profile:
                self.profile = ProfilingAgent().run(self.df)

        pdf_service = PDFService()
        pdf_service.create_report(
            file_name=self.file_name,
            profile=self.profile,
            quality_report=self.quality_report,
            analysis_result=self.latest_result.get("analysis_result", {}),
            insights=self.latest_result.get("insights", ""),
            recommendations=self.latest_result.get("recommendations", ""),
            output_path=output_path
        )
        return output_path

    def export_presentation(self, output_path: str = None, chart_items: list = None) -> str:
        """
        Builds and saves a PowerPoint presentation.
        """
        if not self.latest_result:
            raise ValueError("No analysis result found. Please run analyze() first.")
        if not output_path:
            clean_name = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in self.file_name).strip("_") or "AI_Report"
            output_path = f"outputs/{clean_name}_presentation.pptx"

        if not self.profile or not self.quality_report:
            from agents.data_quality_agent import DataQualityAgent
            from agents.profiling_agent import ProfilingAgent
            if not self.quality_report:
                self.quality_report = DataQualityAgent().run(self.df)
            if not self.profile:
                self.profile = ProfilingAgent().run(self.df)

        presentation_service = PresentationService()
        presentation_service.create_report(
            file_name=self.file_name,
            profile=self.profile,
            quality_report=self.quality_report,
            analysis_result=self.latest_result.get("analysis_result", {}),
            insights=self.latest_result.get("insights", ""),
            recommendations=self.latest_result.get("recommendations", ""),
            chart_items=chart_items,
            query=self.latest_result.get("query", ""),
            dataset_summary=self.latest_result.get("dataset_summary", ""),
            output_path=output_path
        )
        return output_path
