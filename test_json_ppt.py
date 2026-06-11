from core.config import GEMINI_API_KEY
from services.presentation_service import PresentationService

def main():
    prs = PresentationService()
    
    # Mock data
    file_name = "sales_data.csv"
    profile = {"rows": 1000, "columns": 5, "duplicates": 0, "column_names": ["A", "B", "C"]}
    quality_report = {"duplicates": 0, "constant_columns": [], "high_cardinality": {}, "missing_values": {}}
    analysis_result = "Sales increased by 20% in Q4. Customer churn reduced by 5%."
    query = "What are the main insights from this data?"
    dataset_summary = "A dataset containing sales figures for 2023."
    
    output_path = prs.create_report(
        file_name=file_name,
        profile=profile,
        quality_report=quality_report,
        analysis_result=analysis_result,
        insights="Mock insights",
        recommendations="Mock recommendations",
        chart_items=[],
        query=query,
        dataset_summary=dataset_summary,
        output_path="test_output.pptx"
    )
    print(f"Successfully generated PPT at {output_path}")

if __name__ == "__main__":
    main()
