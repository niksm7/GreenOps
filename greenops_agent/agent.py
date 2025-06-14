from google.adk.agents import Agent
from optimization_advisor_agent.agent import optimization_advisor_agent
from forecaster_agent.agent import forecasting_tool_agent
import os
from impact_calculator_agent.agent import impact_calculator_agent
from safe_executor_agent.agent import safe_executor_agent

os.environ["CLIMATIQ_API_KEY"] = "9FJ1F02DJH58B115200WB05JK0"

root_agent = Agent(
    name="greenops_agent",
    model="gemini-2.0-flash",
    description="GreenOps Manager agent",
    instruction="""
        You are the GreenOps manager agent responsible for orchestrating the following agents:

        - `optimization_advisor_agent`: Returns infrastructure optimization recommendations (e.g., underutilized instances, cost/carbon savings).
        - `forecasting_tool_agent`: Provides time-series forecasts for CPU, memory, and carbon emissions.
        - `impact_calculator_agent`: Compares cost and emissions impact between two instance types.
        - `safe_executor_agent`: Executes safe instance migrations based on recommendations.

        ### Instructions:

        1. If the user asks for **recommendations**, call `optimization_advisor_agent`.
        2. Once recommendations are returned ask the user if they want to execute any recommendation, check if the user responds with a request to **execute** them (e.g., "Execute recommendation 1").
        - If yes, extract `Instance ID` and `target instance type` from the corresponding recommendation.
        - Call `safe_executor_agent` with this data something like "migrate instance id <`Instance ID`> to instance type <`target instance type`>
        3. If the user asks about **forecasts** or predictions, delegate to `forecasting_tool_agent`.
        4. If the user wants to **compare impact of changing instance types**, delegate to `impact_calculator_agent`.

        ALWAYS clearly state which agent you're delegating to, and return user-friendly summaries for each action taken.
    """,
    sub_agents=[
        optimization_advisor_agent,
        forecasting_tool_agent,
        impact_calculator_agent,
        safe_executor_agent
    ]
)
