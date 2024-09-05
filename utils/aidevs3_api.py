import os
import requests
import openai

from dotenv import load_dotenv

load_dotenv()

aidevs3_api_key = os.getenv("AIDEVS3_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

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

def connect_to_openai(prompt, model="text-davinci-003"):
    openai.api_key = openai_api_key
    response = openai.Completion.create(
        engine=model,
        prompt=prompt,
        max_tokens=150
    )
    return response.choices[0].text.strip()
