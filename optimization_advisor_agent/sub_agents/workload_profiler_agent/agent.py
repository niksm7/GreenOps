from google.adk.agents import LlmAgent

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
    - **Recommendation**: [action]
    - **Potential Savings**: [estimate]

    For the following data:
    {infra_data}
    """,
    output_key="analysis_results"  # Stores analysis in memory
)