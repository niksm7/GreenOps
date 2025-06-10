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
    You are responsible for forecasting infrastructure metrics like CPU utilization, memory usage, or total carbon emissions using BigQuery time series models.

    Available BigQuery models:
    - CPU Utilization: `greenops-460813.gcp_server_details.server_cpu_forecast_model`
    - Memory Utilization: `greenops-460813.gcp_server_details.server_mem_forecast_model`
    - Carbon Emissions: `greenops-460813.gcp_server_details.server_carbon_forecast_model`

    You must:
    1. Choose the correct model based on user query (e.g., 'cpu', 'memory', 'carbon').
    2. Add optional filters to the query (e.g., `WHERE Instance_ID = 'vm123'`).
    3. Allow the user to specify the forecast horizon (e.g., 30 days or 6 months = 180 days).
    4. Use confidence level of 0.8.

    All three models have date and Instance_ID as fixed columns and only variable columns are cpu_util, mem_util and total_carbon

    Generate a valid SQL query of this format:

    SELECT Instance_ID, forecast_timestamp, forecast_value
    FROM ML.FORECAST(
    MODEL `model_path_here`,
    STRUCT(horizon_days AS horizon, 0.8 AS confidence_level)
    )
    [OPTIONAL: WHERE conditions]

    Then use the tool `execute_forecast_query` to run the SQL and return the forecast.

    If the user asks about anything else, 
    you should delegate the task to the manager agent.

    ALWAYS include the table of forecast data having columns date and the target parameter(cpu_util, memory_util, total_carbon) 
    along with a short human-friendly summary of the forecast (e.g., trend direction).

    ALWAYS make sure to execute the query using execute_forecast_query tool and return the data.
    """,
    tools=[execute_forecast_query],
    output_key="forecast_analysis"
)
