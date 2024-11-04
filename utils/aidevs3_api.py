import os
import requests
import json

from dotenv import load_dotenv

load_dotenv()

endpoint = "https://poligon.aidevs.pl/verify"
AIDEVS3_API_KEY = os.getenv("AIDEVS3_API_KEY")


def get_auth_token(task_name, print_json=False):
    
    url = f"https://zadania.aidevs.pl/token/{task_name}"
    
    data = {"apikey": AIDEVS3_API_KEY}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        
        response_json = response.json()
        if print_json:
            print(response_json)
            
        return response_json.get('token')
        
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {str(e)}")
        return None
    except json.JSONDecodeError:
        print("Failed to decode JSON response")
        return None

def get_task(token_key: str, print_task: bool = False) -> dict:
    url = f"https://zadania.aidevs.pl/task/{token_key}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        response_json = response.json()

        if print_task:
            print('\n----------- Task description -----------')
            # Skip first key which is typically just status
            for key, value in list(response_json.items())[1:]:
                print(f'{key}: {value}')
            print('-----------    ----------    -----------\n')

        return response_json
        
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve task: {str(e)}")
        raise
    except json.JSONDecodeError:
        print("Failed to decode JSON response")
        raise

def send_answer(task, answer, print_response=False):
    json = {
        "task": task,
        "apikey": AIDEVS3_API_KEY,
        "answer": answer
    }

    response = requests.post(endpoint, json=json)
    
    if print_response:
        print(response.json())
    
    return response.json()
