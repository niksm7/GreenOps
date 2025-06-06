from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools import google_search
import requests
from bs4 import BeautifulSoup
import re
from greenops_agent.secrets_access_manager import CLIMATIQ_API_KEY

def format_region_for_climatiq(region: str) -> str:
    """
    Converts 'us-central1' → 'us_central_1' (Climatiq format).
    """
    match = re.match(r"([a-z]+)-([a-z]+)(\d)", region.lower())
    if match:
        return f"{match.group(1)}_{match.group(2)}_{match.group(3)}"
    else:
        return region.lower().replace("-", "_")


def normalize_to_gcp_region(region: str) -> str:
    """
    Converts formats like 'us_east_1' or 'us-east-1' to standard GCP format like 'us-east1'.
    
    Examples:
    - 'us_east_1' → 'us-east1'
    - 'us-east-1' → 'us-east1'
    """
    if not region:
        return ""
    
    region = region.lower().replace("_", "-")
    match = re.match(r"([a-z]+)-([a-z]+)-(\d+)", region)
    if match:
        return f"{match.group(1)}-{match.group(2)}{match.group(3)}"
    return region


def get_on_demand_price(instance_type: str, region: str) -> dict:

    region = normalize_to_gcp_region(region)

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



def get_carbon_emissions_per_hour(current_instance_type: str, current_region: str,
                                   target_instance_type: str, target_region: str,
                                   duration_hours: float = 24.0):

    target_region = format_region_for_climatiq(target_region)
    current_region = format_region_for_climatiq(current_region)

    if not CLIMATIQ_API_KEY:
        raise ValueError("Please set the CLIMATIQ_API_KEY environment variable.")

    # Define the API endpoint
    endpoint = "https://api.climatiq.io/compute/v1/gcp/instance/batch"

    # Prepare the payload for both instances
    payload = [
        {
            "region": current_region,
            "instance": current_instance_type,
            "duration": duration_hours,
            "duration_unit": "h"
        },
        {
            "region": target_region,
            "instance": target_instance_type,
            "duration": duration_hours,
            "duration_unit": "h"
        }
    ]

    # Set up the headers with the API key
    headers = {
        "Authorization": f"Bearer {CLIMATIQ_API_KEY}",
        "Content-Type": "application/json"
    }

    # Send the POST request to the Climatiq API
    response = requests.post(endpoint, json=payload, headers=headers)

    # Raise an exception if the request was unsuccessful
    if response.status_code != 200:
        raise Exception(f"Climatiq API request failed with status code {response.status_code}: {response.text}")

    # Parse the JSON response
    results = response.json().get("results", [])

    # print(results)

    # Process the results for each instance
    emissions_data = {}
    instance_labels = [current_instance_type, target_instance_type]
    for label, result in zip(instance_labels, results):
        if "error" in result:
            emissions_data[label] = {"error": result["error"]}
            continue
        
        # print(result)

        cpu_estimate = result.get("cpu_estimate", {}).get("co2e", 0.0)
        memory_estimate = result.get("memory_estimate", {}).get("co2e", 0.0)
        embodied_cpu_estimate = result.get("embodied_cpu_estimate", {}).get("co2e", 0.0)
        total_emissions = result.get("total_co2e")

        emissions_data[label] = {
            "cpu_estimate": cpu_estimate,
            "memory_estimate": memory_estimate,
            "embodied_cpu_estimate": embodied_cpu_estimate,
            "total_emissions": total_emissions
        }

    return emissions_data



impact_calculator_agent = Agent(
    name="impact_calculator_agent",
    model="gemini-2.0-flash",
    description="Agent that compares cost and carbon impact of changing GCP VM instance types.",
    instruction="""
    You are a Green Cloud Optimization Assistant that helps users understand the environmental and financial impact of changing their GCP VM instance type.

    Your responsibilities include:
    1. Estimating the **hourly and daily cost difference** between a current and target instance.
    2. Estimating the **hourly and daily carbon footprint difference** between the two instances.
    3. Concluding whether the change has a **positive or negative impact**.

    To accomplish this, follow this logic:

    ### 🧮 PRICE ESTIMATION

    Use the tool `get_on_demand_price` to get the **hourly on-demand price** for each instance (current and target).  
    If this fails, fall back to the `google_search` tool by querying:

    > "GCP pricing [INSTANCE_TYPE] [REGION] on-demand site:sparecores.com"

    Only use sparecores.com results, and always return **exact** prices (not approximations).

    Then compute:
    > **price_change_per_day = (target_price - current_price) × 24**

    ---

    ### 🌍 CARBON IMPACT ESTIMATION

    Use the tool `get_carbon_emissions_per_hour` with:
    - current_instance_type
    - current_region (if no region provided ask from user)
    - target_instance_type
    - target_region (If no target region given use the current region)

    This will give you:
    - total_emissions
    - cpu_estimate
    - memory_estimate
    - embodied_cpu_estimate

    Compute:
    > **carbon_change_per_day = (target_total - current_total) × 24**

    ---

    ### FINAL RESPONSE

    Return a clear and structured message that includes:
    - Daily cost for both instances
    - Daily carbon emissions for both instances
    - Whether the impact is positive or negative (in both cost and carbon)
    - Mention if any fallback (search-based pricing) was used

    Do not guess or hallucinate. Only respond when data from tools is available.
    If either tool fails, return a partial answer or suggest user visit official pricing page: https://cloud.google.com/compute/vm-instance-pricing

    Examples of valid queries:
    - “I want to move from `n1-standard-4` in `us-central1` to `e2-standard-2` in `asia-south1`. What will I save?”
    - “Is it better (carbon-wise) to use `a2-highgpu-1g` or `n2-standard-8`?”

    """,
    tools=[
        get_on_demand_price,
        get_carbon_emissions_per_hour,
        AgentTool(google_search)
    ]
)