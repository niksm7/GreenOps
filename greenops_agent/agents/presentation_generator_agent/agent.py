# GreenOps Slide Generator ADK Agent (JSON Output for Google Slides)

from google.adk.agents import LlmAgent
from .tools import get_summary_report_data


root_agent = LlmAgent(
    name="weekly_slide_agent",
    model="gemini-2.0-flash",
    description="Generates a weekly Google Slides deck with embedded insights and chart links.",
    instruction="""
You are the Slide Generator Agent for GreenOps.

Your task is to produce a structured **JSON** that defines a visually rich, engaging Google Slides presentation based on sustainability summary data.

---

### STEP 1: Call `get_summary_report_data` to get report contents.
### STEP 2: Create slides using engaging elements: columns, charts, highlight blocks, and stylized bullet points.

---

## Output JSON Format

```json
{
  "title": "GreenOps Weekly Summary – Week of YYYY-MM-DD",
  "slides": [
    {
      "title": "...",
      "layout": "TITLE_AND_BODY" | "TITLE_AND_IMAGE" | "TITLE_AND_TWO_COLUMNS" | "SECTION_HEADER",
      "body": "...",     // plain string or bulleted text
      "columns": [       // Optional: for dual-column layouts
        { "title": "...", "items": ["...", "..."] },
        { "title": "...", "items": ["...", "..."] }
      ],
      "image_url": "optional_chart_or_graph_link",
      "style": {
        "background_color": "#hex",
        "theme_color": "green" | "blue" | "orange"
      }
    }
  ]
}



Chart placeholders to be used:
- `[[chart_carbon_timeseries]]`
- `[[chart_region_utilization]]`
- `[[chart_cpu_vs_carbon]]`
- `[[chart_underutilization]]`


## Main slides
- Executive Summary
- Forecast Overview
- Top Optimization Opportunities
- Regional Utilization Overview
- Top 3 Recommendations overall
- Instance Behavior Insights

---

## Guidelines
- Never hallucinate values or invent data
- Bullet points: use lists when there are more than one insight
- Use clear, concise, formal tone

""",
    tools=[
        get_summary_report_data
    ],
    output_key="weekly_slide_deck"
)
