from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools import google_search
import requests
from bs4 import BeautifulSoup

def get_on_demand_price(instance_type: str, region: str) -> dict:
    url = f"https://sparecores.com/server/gcp/{instance_type}?showDetails=true"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.select_one("#availability > table")

        if not table:
            return {"error": "Could not find the pricing table on the page."}

        rows = table.find_all("tr")

        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 3:
                region_cell = cols[0].text.strip()
                if region in region_cell:
                    on_demand_price = cols[2].text.strip()
                    return {
                        "instance_type": instance_type,
                        "region": region,
                        "on_demand_price": on_demand_price
                    }

        return {"error": f"No matching region '{region}' found for instance type '{instance_type}'."}

    except Exception as e:
        return {"error": str(e)}



impact_calculator_agent = Agent(
    name="impact_calculator_agent",
    model="gemini-2.0-flash",
    description="Agent to calculate and fetch hourly prices of on-demand GCP instance types.",
    instruction="""
    You are an assistant that helps users find the current hourly price of Google Cloud VM instances based on instance type and region.

    You do not calculate the price — instead, use the tool `google_search` to locate the relevant information on the internet.

    When the user asks for the cost of an instance (e.g., "a2-highgpu-1g in asia-south1"), follow these steps:

    A) Use the tool get_on_demand_price by passing the instance and region to get the on_demand_price (Recommended)

    B) If the price is not retrieved from option A then use the tool google_search with below steps

    1. Generate a search query like:
    "GCP pricing a2-highgpu-1g asia-south1 on-demand sparecores.com"
    Use the link for sparecores.com only for accurate results

    2. Use the `google_search` tool to run the query.

    3. Give the exact amount not approximate


    Respond with:
    - A short summary (if found)
    - If no results are found, apologize and suggest the user visit: https://cloud.google.com/compute/vm-instance-pricing

    Do not hallucinate or guess prices.
    Always rely on the search results only.
    """,
    tools=[get_on_demand_price, AgentTool(google_search)]
)
