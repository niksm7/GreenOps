from google.cloud import bigquery
from google.adk.agents import LlmAgent

import pandas as pd
import datetime

bq_client = bigquery.Client()

def serialize_row(row):
    return {
        k: (v.isoformat() if hasattr(v, 'isoformat') else v)
        for k, v in dict(row).items()
    }

def execute_forecast_query(sql: str) -> dict:
    try:
        query_job = bq_client.query(sql)
        results = query_job.result()
        
        # Convert to DataFrame for easier manipulation
        df = results.to_dataframe()
        
        # Pivot the table to have dates as columns
        if not df.empty:
            df['forecast_timestamp'] = pd.to_datetime(df['forecast_timestamp']).dt.date
            # Pivot the table
            pivoted_df = df.pivot(
                index='Instance_ID',
                columns='forecast_timestamp',
                values='forecast_value'
            ).reset_index()
            
            # Convert dates to string for JSON serialization
            pivoted_df.columns = [
                col.strftime("%Y-%m-%d") if isinstance(col, (datetime.date, pd.Timestamp)) else col
                for col in pivoted_df.columns
            ]

            # Convert to dictionary format
            rows = pivoted_df.to_dict('records')
            return {
                "status": "success",
                "row_count": len(rows),
                "rows": rows,
            }
        else:
            return {"status": "success", "row_count": 0, "rows": [], "metric": None}
            
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


forecasting_tool_agent = LlmAgent(
    name="forecasting_tool_agent",
    model="gemini-2.0-flash",
    description="Forecasts CPU, memory, or carbon usage for GCP servers using BigQuery ML models.",
    instruction="""
    You are a forecasting agent that ONLY provides numeric predictions of CPU, memory, or carbon usage for GCP instances. Your job is to:

    1. Understand the metric to forecast: CPU, memory, or carbon emissions.
    2. Use the correct BigQuery ML model from:
        - CPU Utilization: `greenops-460813.gcp_server_details.server_cpu_forecast_model`
        - Memory Utilization: `greenops-460813.gcp_server_details.server_mem_forecast_model`
        - Carbon Emissions: `greenops-460813.gcp_server_details.server_carbon_forecast_model`
    3. Always forecast the next 7, 30, or 180 days based on the user input.
    4. Always include WHERE filters if the user specifies a region or instance.
    5. NEVER write the SQL in your response. DO NOT show SQL to the user.

    Instead, you MUST always:
    - Build the query
    - Call the tool `execute_forecast_query`
    - Return only the data returned from the tool — never write your own explanation.

    A valid SQL query is of this format:

    SELECT Instance_ID, forecast_timestamp, forecast_value
    FROM ML.FORECAST(
    MODEL model_path_here,
    STRUCT(<horizon_days> AS horizon, 0.8 AS confidence_level)
    )
    [OPTIONAL: WHERE conditions]

    Return format:
    {
    "forecast_analysis": {
        "status": "success",
        "row_count": X,
        "rows": [ ... pivoted table with Instance_ID + forecast values ]
        }
    }

    DO NOT write summaries or describe what the forecast shows.
    DO NOT say “here’s the forecast” or “it seems stable” — JUST return the tool output.
    """,
    tools=[execute_forecast_query],
    output_key="forecast_analysis"
)
