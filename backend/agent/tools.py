"""LangChain tools for the Smart Building agent."""
from __future__ import annotations

from typing import List, Dict, Any

from langchain_core.tools import StructuredTool

from backend.rag.manager import DocumentAssistant
from backend.services.mcp import fetch_live_data
from backend.predictive.maintenance import HealthPredictor

# Shared helpers
_doc_assist = DocumentAssistant()
_predictor = HealthPredictor()


def _vector_search(query: str, k: int = 4) -> List[str]:
    """Return top-k text chunks relevant to `query`."""
    chunks = _doc_assist.similarity_search(query, k)
    if not chunks:
        return ["(no documents ingested yet)"]
    return chunks


def _sensor_live_data(equipment_id: str) -> Dict[str, Any]:
    """Fetch latest sensor data for given equipment."""
    return fetch_live_data(equipment_id)


def _predict_failure(sensor_dict: Dict[str, Any]) -> float:
    """Given sensor readings, return probability of failure (0-1)."""
    return _predictor.predict(sensor_dict)


def _sql_query(sql: str) -> str:  # pragma: no cover – placeholder
    """Execute an ad-hoc SQL query against the Postgres DB.

    NOTE: For now this is read-only and limited to small result sets.
    """
    import os, psycopg2, textwrap

    conn_str = os.getenv("PG_CONN", "postgresql://pguser:pgpass@localhost:5432/building_ai")
    try:
        with psycopg2.connect(conn_str) as conn, conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchmany(20)
            header = [desc[0] for desc in cur.description]
            lines = [" | ".join(map(str, row)) for row in rows]
            return textwrap.dedent("""
            Columns: {cols}
            {rows}
            """).format(cols=", ".join(header), rows="\n".join(lines))
    except Exception as e:  # pragma: no cover
        return f"SQL error: {e}"


TOOLS: List[StructuredTool] = [
    StructuredTool.from_function(_vector_search, name="vector_search", description="Search building document chunks relevant to a question."),
    StructuredTool.from_function(_sensor_live_data, name="sensor_live_data", description="Get latest sensor readings for a piece of equipment."),
    StructuredTool.from_function(_predict_failure, name="predict_failure", description="Predict probability of equipment failure based on sensor data (dict)."),
    StructuredTool.from_function(_sql_query, name="sql_query", description="Run a read-only SQL query against the building DB."),
] 