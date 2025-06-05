from google.adk.agents import Agent
from optimization_advisor_agent.agent import optimization_advisor_agent
from forecaster_agent.agent import forecasting_tool_agent
from impact_calculator_agent.agent import impact_calculator_agent

root_agent = Agent(
    name="greenops_agent",
    model="gemini-2.0-flash",
    description="GreenOps Manager agent",
    instruction="""
    You are a manager agent that is responsible for overseeing the work of the other agents.

    Always delegate the task to the appropriate agent. Use your best judgement 
    to determine which agent to delegate to.

    You are responsible for delegating tasks to the following agent:
    - optimization_advisor_agent: Sequential agent for handling infra and carbon optimization recommendations.
    - infra_scout_agent: Provides data from the BigQuery using efficient queries
    - forecasting_tool_agent: Predicts resource metrics (CPU, memory and carbon) using time series forecasting.

    """,
    sub_agents=[optimization_advisor_agent, forecasting_tool_agent, impact_calculator_agent]
)