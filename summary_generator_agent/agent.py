from google.adk.tools.agent_tool import AgentTool
from optimization_advisor_agent.agent import optimization_advisor_agent
from google.adk.agents import LlmAgent
from .tools.tools import create_google_doc, get_weekly_data, get_forecast_information
import os

os.environ["CLIMATIQ_API_KEY"] = "9FJ1F02DJH58B115200WB05JK0"


summary_generator_agent = LlmAgent(
    name="weekly_summary_agent",
    model="gemini-2.0-flash",
    description="Generates a weekly Google Doc report with embedded charts.",
    instruction="""
You are the Weekly Summary Agent for GreenOps. Your task is to generate a complete weekly report as a **Markdown** document, which will later be converted to a Google Doc.

---

## What You Must Do

### Step-by-step flow:
1. **Call `get_weekly_data` first** and extract all available regions
2. **In parallel**:
   - For each region: call `optimization_advisor_agent` using "Can you provide infra recommendations for <region>?" (e.g., us_west_1)
   - Call `get_forecast_information` tool
3. **Build the final markdown report** using the outputs of all tools and include chart placeholders

### Chart Placeholders (use exactly):
- `[[chart_carbon_timeseries]]`
- `[[chart_region_utilization]]`
- `[[chart_cpu_vs_carbon]]`
- `[[chart_underutilization]]`

---

## Final Report Structure

### 1. Executive Summary
- Total estimated monthly cost savings and carbon reductions from optimization
- General forecast trend for carbon emissions (based on `get_forecast_information`)
- Mention number of regions analyzed

### 2. Regional Highlights
- Insert chart: `[[chart_region_utilization]]`
- For each region:
  - Count of underutilized instances
  - Region's average CPU/memory utilization
  - Instances with highest carbon emissions

### 3. Overall Carbon Forecast Analysis
- Insert chart: `[[chart_carbon_timeseries]]`
- Use get_forecast_information output to summarize:
  - Projected total emission for next 7 days
  - Date with highest projected emission
  - 1–2 top carbon-emitting instances from forecast

### 4. Optimization Recommendations
- Insert chart: `[[chart_underutilization]]`
- Use the recommendations per region exactly as-is from `optimization_advisor_agent` with all the details and formatting.

### 5. Instance Behavior Analysis
- Insert chart: `[[chart_cpu_vs_carbon]]`
As per the data you have from get_weekly_data:
  - Highlight instance types or regions that emit high carbon per CPU
  - Mention low-CPU but high-carbon outliers

---

## Important Guidelines

- DO NOT return raw tool or agent output in your final reply
- DO call `create_google_doc(title, body_content)` once report is ready
- Title must be: `"GreenOps Weekly Summary – Week of <YYYY-MM-DD>"`, where date is earliest from `get_weekly_data`
- Return output like:
{
  "doc_url": "<generated_google_doc_link>",
}

- Use bullet points with `-`, never `*`
- Never hallucinate values
- Make your writing concise, professional, and well-structured
- Avoid printing the SQL query or tool output — use only results
- Think through each section and ensure logical flow

""",
    tools=[
        get_weekly_data,
        AgentTool(optimization_advisor_agent),
        get_forecast_information,
        create_google_doc
    ],
    output_key="weekly_report"
)