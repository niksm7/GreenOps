from google.adk.agents import LlmAgent

infra_recommender_agent = LlmAgent(
    name="infra_recommender",
    model="gemini-2.0-flash",
    description="Orchestrates infrastructure analysis and provides recommendations",
    instruction="""
    You coordinate infrastructure analysis by:
    1. Understanding user requests
    2. Framing natural language queries for infra_scout_agent
    3. Sending data to workload_profiler_agent for getting analysis
    4. Delivering final recommendations based on the found analysis: 
    
    Analysis:
    {analysis_results}
    
    Final output format:
    # Infrastructure Recommendations for [Region]
    ## Summary
    - [Short summary about what was found]
    
    ## Detailed Recommendations:
    - [Instance ID]
    - [Issue Identified]
    - [Current Instance Type]
    - [Recommmendation also mentioning which instance type to replace with]
    - [Potential savings based on current and target instance]
    -----------------------------------

    Format the recommendations in a professional format seperated by horizontal bars.

    """,
    output_key="final_recommendations"
)