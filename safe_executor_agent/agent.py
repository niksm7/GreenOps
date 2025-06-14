from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from tools import *
from forecaster_agent.agent import forecasting_tool_agent

safe_executor_agent = LlmAgent(
    name="safe_executor_agent",
    model="gemini-2.0-flash",
    description="Safely executes infra migration from current to target instance.",
    instruction="""
You are responsible for validating whether an instance migration is safe. 

Steps to follow:

1. **Forecast CPU and Memory** for the given current_instance_id using `forecast_cpu_util` and `forecast_memory_util`.
2. **Decide if migration is safe**:
   - Safe if CPU avg < 50% and Memory avg < 70%
   - If not safe, stop and report
3. **Create snapshot of current instance** (use `create_snapshot`)
4. **Create new instance** of type target_instance_type using that snapshot in the same region
5. **Wait for the new instance to be RUNNING** (`check_instance_status`)
6. **Delete the old instance**
7. Return new instance ID and confirmation.

Always handle errors gracefully and report if snapshot or boot fails.
""",
    tools=[
        AgentTool(forecasting_tool_agent),
        create_snapshot,
        create_target_instance,
        check_instance_status,
        delete_instance
    ],
    output_key="safe_execution_result"
)
