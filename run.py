import os
import sys
import argparse
import json
import io
from dotenv import load_dotenv

# Ensure Windows console supports UTF-8 to prevent emoji/unicode encode errors
if sys.platform.startswith("win"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Load env variables before importing agent (which also loads them)
load_dotenv()

from gaia_api import get_questions, get_file
from agents import manager_agent

def parse_answer(agent_response):
    """
    Parses the agent output to extract only the text after 'FINAL ANSWER:'.
    """
    if str(agent_response).startswith("ERROR:"):
        return agent_response
    
    target = "FINAL ANSWER:"
    # Search for exactly 'FINAL ANSWER:'
    if target in agent_response:
        # Split and take the last part in case it was printed multiple times
        ans = agent_response.split(target)[-1].strip()
        return ans
    
    # Case-insensitive fallback
    target_lower = "final answer:"
    idx = agent_response.lower().rfind(target_lower)
    if idx != -1:
        return agent_response[idx + len(target_lower):].strip()
    
    # Fallback to the last line if the agent failed to format it
    lines = [line.strip() for line in agent_response.splitlines() if line.strip()]
    if lines:
        return lines[-1]
        
    return agent_response.strip()

def main():
    parser = argparse.ArgumentParser(description="Run GAIA Benchmark Agent System")
    parser.add_argument(
        "--test", 
        action="store_true", 
        help="Run in test mode (limit to the first 3 questions)"
    )
    args = parser.parse_args()
    
    # Determine test mode (CLI flag or TEST_MODE env var)
    is_test_mode = args.test or os.environ.get("TEST_MODE", "").lower() in ("true", "1", "yes")
    
    print("Fetching questions from GAIA API...")
    try:
        questions = get_questions()
        print(f"Successfully fetched {len(questions)} questions.")
    except Exception as e:
        print(f"Failed to fetch questions: {e}")
        return

    if is_test_mode:
        print("Running in TEST MODE: Limiting to the first 3 questions.")
        questions = questions[:3]

    results = []
    
    formatting_instructions = (
        "You must report your reasoning first, then end your response with exactly one line:\n"
        "FINAL ANSWER: [answer]\n"
        "The answer must be as terse as possible — no explanations, no extra words.\n"
        "Use digits unless the question asks numbers to be spelled out.\n"
        "Use plural form only if explicitly asked.\n"
        "For comma-separated lists, no space-padding inconsistencies — keep it clean and consistent.\n\n"
    )

    for i, q in enumerate(questions):
        task_id = q.get("task_id")
        question_text = q.get("question")
        level = q.get("Level")
        file_name = q.get("file_name")
        
        print(f"\n--- Processing Question {i+1}/{len(questions)} (ID: {task_id}, Level: {level}) ---")
        
        file_path = None
        if file_name:
            print(f"Downloading associated file: {file_name}")
            try:
                file_path = get_file(task_id, file_name)
            except Exception as e:
                print(f"Skipping download due to error, will run agent anyway: {e}")
        
        # Build prompt
        prompt = formatting_instructions + question_text
        if file_path:
            # Get absolute path to be clear for FileReaderTool
            abs_path = os.path.abspath(file_path)
            prompt += f"\n\nAttached file is saved at: {abs_path}"
            
        print(f"Question: {question_text}")
        print(f"File involved: {file_name if file_name else 'None'}")
        
        # Run agent
        try:
            print("Running manager agent...")
            agent_response = manager_agent.run(prompt)
        except Exception as e:
            print(f"Error running agent for task {task_id}: {e}")
            agent_response = f"ERROR: {str(e)}"
            
        parsed_ans = parse_answer(agent_response)
        
        print(f"Parsed Final Answer: {parsed_ans}")
        
        results.append({
            "task_id": task_id,
            "model_answer": parsed_ans
        })
        
    # Write to answers_test.json in test mode, and answers.json in full run
    output_file = "answers_test.json" if is_test_mode else "answers.json"
    
    try:
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nSaved {len(results)} answers to {output_file} successfully.")
    except Exception as e:
        print(f"Failed to save answers to {output_file}: {e}")

if __name__ == "__main__":
    main()
    
    # SUBMISSION STEP (Manually triggered)
    # To submit your answers, uncomment the block below and run:
    # 
    # from gaia_api import submit_answers
    # import json
    # with open("answers.json", "r") as f:
    #     answers = json.load(f)
    # submit_answers(
    #     username="your_hf_username",
    #     agent_code_url="https://github.com/your_username/your_repo",
    #     answers=answers
    # )
