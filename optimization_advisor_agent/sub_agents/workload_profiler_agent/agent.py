from google.adk.agents import LlmAgent
from impact_calculator_agent.agent import get_on_demand_price

workload_profiler_agent = LlmAgent(
    name="workload_profiler",
    model="gemini-2.0-flash",
    description="Analyzes infrastructure data for optimization opportunities",
    instruction="""
    You analyze GCP server metrics to identify:
    1. Underutilized resources (CPU < 30% or MEM < 40%)
    2. High carbon emitters (>1kg CO2/day)
    3. Cost-saving opportunities (overprovisioned instances)
    
    For each finding include:
    - Instance details
    - Current metrics
    - Recommended action
    - Estimated savings (carbon & cost)
    
    Format recommendations as:
    ### [Region] Optimization Opportunities
    #### [Instance Type]
    - **Instance ID**: [value]
    - **Issue**: [description]
    - **Current Instance Type**: [value]
    - **Recommendation**: [action] [Always give the target replacement instance and explain why this instance type]
    - **Potential Savings**: [estimate]

    Always make sure that for each potential savings section calculate the hourly cost using the tool get_on_demand_price by passing current and target instance types for each and their respective regions (should be in the form us-east1) then use this hourly price to give saving of a month

    For the following data:
    {infra_data}
    """,
    output_key="analysis_results",
    tools=[get_on_demand_price]
)