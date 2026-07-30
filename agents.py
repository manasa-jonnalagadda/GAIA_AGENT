import os
from dotenv import load_dotenv
from smolagents import LiteLLMModel, ToolCallingAgent, CodeAgent, DuckDuckGoSearchTool, VisitWebpageTool
from tools import FileReaderTool

# Load environment variables
load_dotenv()

# 1. Model Setup
api_key = os.environ.get("LLM_API_KEY")
model_id = os.environ.get("LLM_MODEL_ID", "gpt-4o")

# Instantiate one shared model object and reuse it across agents
model = LiteLLMModel(
    model_id=model_id,
    api_key=api_key
)

# 2. Web Agent (ToolCallingAgent)
# Create a ToolCallingAgent named "web_search_agent"
# We attempt to pass name and description directly, falling back to setting them as attributes
try:
    web_search_agent = ToolCallingAgent(
        model=model,
        tools=[DuckDuckGoSearchTool(), VisitWebpageTool()],
        max_steps=10,
        name="web_search_agent",
        description="runs web searches and visits pages to find current/external information."
    )
except TypeError:
    web_search_agent = ToolCallingAgent(
        model=model,
        tools=[DuckDuckGoSearchTool(), VisitWebpageTool()],
        max_steps=10
    )
    web_search_agent.name = "web_search_agent"
    web_search_agent.description = "runs web searches and visits pages to find current/external information."

# 3. Manager Agent (CodeAgent)
# Instantiate the custom FileReaderTool passing the shared model configuration
file_reader_tool = FileReaderTool(model_id=model_id, api_key=api_key)

# Create a CodeAgent named "manager_agent"
# We pass the web_search_agent directly in managed_agents
manager_agent = CodeAgent(
    model=model,
    tools=[file_reader_tool],
    managed_agents=[web_search_agent],
    additional_authorized_imports=["pandas", "numpy", "json", "re", "requests"],
    max_steps=15,
    name="manager_agent",
    description="Manager agent that coordinates tasks, reads local files, and delegates web searches."
)
