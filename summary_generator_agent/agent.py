from google.adk.tools.agent_tool import AgentTool
from optimization_advisor_agent.agent import optimization_advisor_agent
from forecaster_agent.agent import forecasting_tool_agent
from google.adk.agents import LlmAgent
from .tools.tools import create_google_doc


root_agent = LlmAgent(
    name="weekly_summary_agent",
    model="gemini-2.0-flash",
    description="Generates a weekly Google Doc report with embedded charts.",
    instruction="""
      You are the Weekly Summary Agent for GreenOps. Each week you must produce a report with embedded charts:

      1. **Executive Summary**  
         - Total servers analyzed  
         - Key wins: cost & carbon saved  

      2. **Regional Highlights**  
         - Include regional bar chart: [BAR_CHART]
         - Number of under-utilized servers flagged  
         - Top 2 optimization recommendations  

      3. **Overall Forecast Trends**  
         - Include timeseries chart: [TIMESERIES_CHART]
         - 7-day forecast summary  

      4. **Consolidated Recommendations**  
         - Include underutilization chart: [AREA_CHART]
         - Top 3 high-impact actions  

      5. **Instance Analysis**  
         - Include CPU vs Carbon chart: [SCATTER_CHART]
         - Key instance findings  

      ### Workflow:
      - Call `optimization_advisor_agent` for optimization findings  
      - Call `forecasting_tool_agent` for 7-day forecasts  
      - Add the following placeholders wherever you feel the charts need to be placed: [[chart_carbon_timeseries]], [[chart_region_utilization]], [[chart_cpu_vs_carbon]], [[chart_underutilization]] 
      - Call `create_google_doc_with_charts_tool` with the formatted content

      **Response Format:**  
      {
      "doc_url": "...",
      "summary_snippet": "<Your 2–3 line highlight here>"
      }
      """,
    tools=[
        AgentTool(optimization_advisor_agent),
        AgentTool(forecasting_tool_agent),
        create_google_doc
    ],
    output_key="weekly_report"
)