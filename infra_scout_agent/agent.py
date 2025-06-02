from google.adk.agents import LlmAgent
from google.cloud import bigquery
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Instantiate BigQuery client
bq_client = bigquery.Client()

def execute_server_query(sql: str) -> dict:
    """Executes a BigQuery SQL query and returns up to 10 rows."""
    try:
        logger.info(f"Executing SQL: {sql}")
        query_job = bq_client.query(sql)
        results = query_job.result()
        data = [dict(row) for row in results]

        if not data:
            return {"status": "error", "error_message": "No matching records found"}

        return {
            "status": "success",
            "row_count": len(data),
            "rows": data[:10]
        }
    except Exception as e:
        logger.error(f"Query execution error: {e}")
        return {"status": "error", "error_message": str(e)}

# Define the ADK agent
infra_scout_agent = LlmAgent(
    name="gcp_server_analyst",
    model="gemini-2.0-flash",
    description="Fetches GCP server metrics from BigQuery for use in downstream analysis.",
    instruction="""
    You are responsible for retrieving server data from the BigQuery table:
    `greenops-460813.gcp_server_details.server_metrics`.

    You must:
    1. Extract only the **filters** (such as Region, Instance_Type) from the user query.
    2. Ignore any intent like "optimize", "recommend", or "analyze". You do **not** provide interpretations or recommendations.
    3. Generate a SQL query that returns all rows matching those filters (e.g., Region = 'us_west_1').
    4. Call the `execute_server_query` tool with the generated SQL.
    5. Return the query result directly without explanation.

    Important rules:
    - If the user query mentions a region (e.g., "us_west_1"), filter the SQL by Region.
    - If the user doesn't provide filters, return all rows.
    - Limit results to 10 rows using `LIMIT 10`.

    Example:
    User: "Give me server data for us_west_1"
    → You generate: SELECT * FROM `greenops-460813.gcp_server_details.server_metrics` WHERE Region = 'us_west_1' LIMIT 10
    """,
    tools=[execute_server_query],
    output_key="infra_data"
)

