import os
import requests

from dotenv import load_dotenv

load_dotenv()

aidevs3_api_key = os.getenv("AIDEVS3_API_KEY")

endpoint = "https://poligon.aidevs.pl/verify"

def download_data(url):
    response = requests.get(url)
    return response.text

def send_answer(task, data, print_response=False):
    json = {
        "task": task,
        "apikey": aidevs3_api_key,
        "answer": data
    }

    response = requests.post(endpoint, json=json)
    
    if print_response:
        print(response.json())
    
    return response.json()