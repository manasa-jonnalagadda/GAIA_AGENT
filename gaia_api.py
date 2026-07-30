import os
import requests

BASE_URL = "https://agents-course-unit4-scoring.hf.space"

def get_questions():
    """
    Fetches all GAIA questions from the scoring API.
    """
    url = f"{BASE_URL}/questions"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching questions from {url}: {e}")
        raise e

def get_file(task_id, file_name):
    """
    Downloads file associated with a task_id and saves it locally.
    Prefixes the filename with task_id to avoid collision.
    """
    url = f"{BASE_URL}/files/{task_id}"
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        # Ensure the downloads directory exists
        os.makedirs("./downloads", exist_ok=True)
        
        # Prefix the filename with the task_id to avoid collision
        prefixed_filename = f"{task_id}_{file_name}"
        dest_path = os.path.join("./downloads", prefixed_filename)
        
        with open(dest_path, "wb") as f:
            f.write(response.content)
            
        print(f"Downloaded file for task {task_id} to {dest_path}")
        return dest_path
    except Exception as e:
        print(f"Error downloading file for task {task_id} from {url}: {e}")
        raise e

def submit_answers(username, agent_code_url, answers):
    """
    Submits answers to the scoring API.
    """
    url = f"{BASE_URL}/submit"
    payload = {
        "username": username,
        "agent_code": agent_code_url,
        "answers": answers
    }
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        print(f"Submission response: {result}")
        return result
    except Exception as e:
        print(f"Error submitting answers to {url}: {e}")
        raise e
