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
web_search_agent = ToolCallingAgent(
    model=model,
    tools=[DuckDuckGoSearchTool(), VisitWebpageTool()],
    max_steps=10,
    name="web_search_agent",
    description="runs web searches and visits pages to find current/external information."
)

# 3. Manager Agent (CodeAgent)
# Create a CodeAgent named "manager_agent"
manager_agent = CodeAgent(
    model=model,
    tools=[FileReaderTool()],
    managed_agents=[web_search_agent],
    additional_authorized_imports=["pandas", "numpy", "json", "re", "requests"],
    max_steps=15,
    name="manager_agent",
    description="Manager agent that coordinates tasks, reads local files, and delegates web searches."
)
