from concurrent.futures import ThreadPoolExecutor
import time
from typing import TypedDict, Any

from langgraph.graph import StateGraph, END

from agents.data_quality_agent import DataQualityAgent
from agents.profiling_agent import ProfilingAgent
from agents.analysis_agent import AnalysisAgent
from agents.visualization_agent import VisualizationAgent
from agents.insight_agent import InsightAgent
from agents.recommendation_agent import RecommendationAgent

from core.config import GEMINI_API_KEY


class AgentState(TypedDict):

    query: str

    df: Any

    conversation: list

    profile: dict

    quality_report: dict

    dataset_summary: str

    analysis_result: dict

    visualization_result: dict

    insights: str

    recommendations: str

    execution_trace: list


def add_trace(state, message):

    trace = state.get(
        "execution_trace",
        []
    )

    trace.append(message)

    state["execution_trace"] = trace

    return state


def quality_node(state):

    agent = DataQualityAgent()

    state["quality_report"] = agent.run(
        state["df"]
    )

    add_trace(
        state,
        "✅ Data Quality Agent Completed"
    )

    return state


def profiling_node(state):

    agent = ProfilingAgent()

    profile = agent.run(
        state["df"]
    )

    state["profile"] = profile

    summary = f"""
Rows: {profile['rows']}
Columns: {profile['columns']}
Duplicates: {profile['duplicates']}

Columns:
{profile['column_names']}

Data Types:
{profile['data_types']}
"""

    state["dataset_summary"] = summary

    add_trace(
        state,
        "✅ Profiling Agent Completed"
    )

    return state


def analysis_node(state):

    if not GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY is not set. Set the GEMINI_API_KEY environment variable or add it to Streamlit secrets. See https://ai.google.dev/gemini-api/docs/api-key"
        )

    agent = AnalysisAgent(
        GEMINI_API_KEY
    )

    result = agent.run(

        query=state["query"],

        df=state["df"],

        conversation=
        state["conversation"]

    )

    state["analysis_result"] = result

    add_trace(
        state,
        "✅ Analysis Agent Completed"
    )

    return state


def visualization_node(state):

    if not GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY is not set. Set the GEMINI_API_KEY environment variable or add it to Streamlit secrets. See https://ai.google.dev/gemini-api/docs/api-key"
        )

    agent = VisualizationAgent(
        GEMINI_API_KEY
    )

    result = agent.run(

        query=state["query"],

        df=state["df"],

        conversation=
        state["conversation"]

    )

    state["visualization_result"] = result

    add_trace(
        state,
        "✅ Visualization Agent Completed"
    )

    return state


def insight_node(state):

    if not GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY is not set. Set the GEMINI_API_KEY environment variable or add it to Streamlit secrets. See https://ai.google.dev/gemini-api/docs/api-key"
        )

    agent = InsightAgent(
        GEMINI_API_KEY
    )

    analysis_text = ""

    if state.get(
        "analysis_result"
    ):

        analysis_text = str(

            state[
                "analysis_result"
            ].get(
                "result",
                ""
            )

        )

    insights = agent.run(

        query=
        state["query"],

        dataset_summary=
        state["dataset_summary"],

        analysis_result=
        analysis_text

    )

    state["insights"] = insights

    add_trace(
        state,
        "✅ Insight Agent Completed"
    )

    return state


def recommendation_node(state):

    if not GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY is not set. Set the GEMINI_API_KEY environment variable or add it to Streamlit secrets. See https://ai.google.dev/gemini-api/docs/api-key"
        )

    agent = RecommendationAgent(
        GEMINI_API_KEY
    )

    analysis_text = ""

    if state.get(
        "analysis_result"
    ):

        analysis_text = str(

            state[
                "analysis_result"
            ].get(
                "result",
                ""
            )

        )

    recommendations = agent.run(

        query=
        state["query"],

        dataset_summary=
        state["dataset_summary"],

        analysis_result=
        analysis_text,

        insights=
        state["insights"]

    )

    state[
        "recommendations"
    ] = recommendations

    add_trace(
        state,
        "✅ Recommendation Agent Completed"
    )

    return state


def _require_gemini_key():
    if not GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY is not set. Set the GEMINI_API_KEY environment variable or add it to Streamlit secrets. See https://ai.google.dev/gemini-api/docs/api-key"
        )


def _build_dataset_summary(profile):
    return f"""
Rows: {profile['rows']}
Columns: {profile['columns']}
Duplicates: {profile['duplicates']}

Columns:
{profile['column_names']}

Data Types:
{profile['data_types']}
"""


def _analysis_text(state):
    if state.get("analysis_result"):
        return str(state["analysis_result"].get("result", ""))

    return ""


def invoke_fast_workflow(state):
    """Run the same analysis workflow with independent steps in parallel."""
    _require_gemini_key()

    state = dict(state)
    state["execution_trace"] = []
    workflow_started = time.perf_counter()

    local_started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=2) as executor:
        quality_future = executor.submit(DataQualityAgent().run, state["df"])
        profile_future = executor.submit(ProfilingAgent().run, state["df"])

        state["quality_report"] = quality_future.result()
        state["profile"] = profile_future.result()

    state["dataset_summary"] = _build_dataset_summary(state["profile"])
    add_trace(
        state,
        f"Completed: Data Quality and Profiling Agents in {time.perf_counter() - local_started:.1f}s",
    )

    analysis_started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=2) as executor:
        analysis_future = executor.submit(
            AnalysisAgent(GEMINI_API_KEY).run,
            query=state["query"],
            df=state["df"],
            conversation=state["conversation"],
        )
        visualization_future = executor.submit(
            VisualizationAgent(GEMINI_API_KEY).run,
            query=state["query"],
            df=state["df"],
            conversation=state["conversation"],
        )

        state["analysis_result"] = analysis_future.result()
        state["visualization_result"] = visualization_future.result()

    add_trace(
        state,
        f"Completed: Analysis and Visualization Agents in {time.perf_counter() - analysis_started:.1f}s",
    )

    insight_started = time.perf_counter()
    insight_agent = InsightAgent(GEMINI_API_KEY)
    state["insights"] = insight_agent.run(
        query=state["query"],
        dataset_summary=state["dataset_summary"],
        analysis_result=_analysis_text(state),
    )
    add_trace(
        state,
        f"Completed: Insight Agent in {time.perf_counter() - insight_started:.1f}s",
    )

    recommendation_started = time.perf_counter()
    recommendation_agent = RecommendationAgent(GEMINI_API_KEY)
    state["recommendations"] = recommendation_agent.run(
        query=state["query"],
        dataset_summary=state["dataset_summary"],
        analysis_result=_analysis_text(state),
        insights=state["insights"],
    )
    add_trace(
        state,
        f"Completed: Recommendation Agent in {time.perf_counter() - recommendation_started:.1f}s",
    )
    add_trace(
        state,
        f"Completed: Full workflow in {time.perf_counter() - workflow_started:.1f}s",
    )

    return state


builder = StateGraph(
    AgentState
)

builder.add_node(
    "quality",
    quality_node
)

builder.add_node(
    "profiling",
    profiling_node
)

builder.add_node(
    "analysis",
    analysis_node
)

builder.add_node(
    "visualization",
    visualization_node
)

builder.add_node(
    "insights",
    insight_node
)

builder.add_node(
    "recommendations",
    recommendation_node
)

builder.set_entry_point(
    "quality"
)

builder.add_edge(
    "quality",
    "profiling"
)

builder.add_edge(
    "profiling",
    "analysis"
)

builder.add_edge(
    "analysis",
    "visualization"
)

builder.add_edge(
    "visualization",
    "insights"
)

builder.add_edge(
    "insights",
    "recommendations"
)

builder.add_edge(
    "recommendations",
    END
)

graph = builder.compile()
