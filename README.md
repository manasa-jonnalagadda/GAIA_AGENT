# GAIA Benchmark Agent System

A complete GAIA benchmark agent system built in Python using Hugging Face's `smolagents` library and `LiteLLM`. It implements a hierarchical multi-agent structure to solve complex tasks requiring file reading, web research, and reasoning.

## Architecture

The system consists of two specialized agents:

1. **Manager Agent (`CodeAgent`)**: The orchestrator that coordinates task execution. It writes Python code dynamically to solve tasks, parses file content using a custom `FileReaderTool`, and delegates external research to the search agent.
2. **Search Agent (`ToolCallingAgent`)**: A specialized agent equipped with `DuckDuckGoSearchTool` and `VisitWebpageTool` to query the web and extract content from websites.

```
       [User Task]
            |
            v
    [Manager Agent]  <--->  [FileReaderTool] (CSV, Excel, PDF, Images, Text)
            |
     (Delegates query)
            |
            v
     [Search Agent]  <--->  [DuckDuckGo & VisitWebpage Tools]
```

## Features

- **Robust File Reader (`FileReaderTool`)**:
  - Automatically dispatches parsing logic by file extension.
  - Smart CSV and Excel sheets preview limit ($> 200$ rows) to prevent blowing up the LLM context window.
  - Automatic PDF extraction using `pypdf` with truncation protection ($> 8000$ characters).
  - Multimodal image analysis (transcription and description) using `litellm.completion`.
- **Automatic Retry Wrapper**: Implements exponential backoff retry logic using the `tenacity` library. Automatically retries up to 3 times on API rate limit or capacity errors (delays: 5s, 15s, 45s) before saving an error status and continuing.
- **Windows Console Encoding Fix**: Enforces UTF-8 stdout/stderr stream formatting on Windows to prevent `UnicodeEncodeError` crashes from emojis printed by `smolagents`.
- **Predefined File Naming**: Avoids download collisions by prefixing downloaded files with their unique GAIA `task_id`.
- **Terse Formatting Constraint**: Pre-formats all prompts to enforce GAIA-compliant answer output constraints, with a clean post-processing parser that extracts text after `FINAL ANSWER:`.

## Setup Instructions

### 1. Initialize Virtual Environment
To bypass Windows path length limit constraints (`MAX_PATH`) when installing deeply nested libraries like `litellm`, it is recommended to use a local virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install Dependencies
Install all package requirements:
```bash
pip install -r requirements.txt
```

### 3. Configuration
Copy the `.env.example` file to `.env`:
```bash
copy .env.example .env
```
Open `.env` and fill in your API key and model ID:
```env
LLM_API_KEY=your_actual_api_key
LLM_MODEL_ID=gemini/gemini-2.5-flash
```

## Running the Pipeline

### Test Mode (First 3 Questions Only)
Run a cheap verification test to ensure the fetching, downloading, and model execution works:
```bash
python run.py --test
```
*Outputs are saved to `answers_test.json` so you do not overwrite production results.*

### Full Run
Execute the complete benchmark:
```bash
python run.py
```
*Outputs are saved to `answers.json`.*

### Manual Submission
To submit your answers to the GAIA Hugging Face Course Space, uncomment the block at the bottom of `run.py` and run it:
```python
from gaia_api import submit_answers
import json
with open("answers.json", "r") as f:
    answers = json.load(f)
submit_answers(
    username="your_hf_username",
    agent_code_url="https://github.com/manasa-jonnalagadda/GAIA_AGENT",
    answers=answers
)
```
