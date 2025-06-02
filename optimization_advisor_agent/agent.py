from infra_scout_agent.agent import infra_scout_agent
from workload_profiler_agent.agent import workload_profiler_agent
from recommender_agent.agent import infra_recommender_agent

from google.adk.agents import SequentialAgent

# Create the sequential agent with minimal callback
root_agent = SequentialAgent(
    name="OptimizationAdvisor",
    sub_agents=[infra_scout_agent, workload_profiler_agent, infra_recommender_agent],
    description="A pipeline that recommends optimization for the infrastructure",
)