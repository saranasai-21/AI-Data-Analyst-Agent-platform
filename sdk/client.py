import os
import pandas as pd
from typing import Optional
from .session import AnalysisSession
from core.data_loader import DataLoader

class AIAnalystClient:
    """
    Client for configuring keys, loading datasets, and starting analysis sessions.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

    def load_data(self, file_path: str, **kwargs) -> pd.DataFrame:
        """
        Loads dataset files of supported formats into a pandas DataFrame.
        """
        ext = os.path.splitext(file_path.lower())[1]
        
        if ext in (".db", ".sqlite", ".sqlite3"):
            query = kwargs.get("query", "SELECT name FROM sqlite_master WHERE type='table';")
            return DataLoader.load_sqlite(file_path, query)
        elif ext == ".pdf":
            import io
            from core.gemini_service import parse_pdf_to_csv
            if not self.api_key:
                raise ValueError("An API key is required to parse PDF data using Gemini.")
            with open(file_path, "rb") as f:
                pdf_bytes = f.read()
            csv_text = parse_pdf_to_csv(self.api_key, pdf_bytes)
            return pd.read_csv(io.StringIO(csv_text))
        elif ext == ".csv":
            return pd.read_csv(file_path, **kwargs)
        elif ext in (".xlsx", ".xls"):
            return pd.read_excel(file_path, **kwargs)
        elif ext == ".json":
            return pd.read_json(file_path, **kwargs)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def create_session(self, df: pd.DataFrame, file_name: str = "dataset") -> AnalysisSession:
        """
        Spawns a stateful AnalysisSession for a loaded DataFrame.
        """
        df = df.copy()
        df.columns = [str(col).strip().replace("\r", "").replace("\n", "") for col in df.columns]
        return AnalysisSession(self, df, file_name)
