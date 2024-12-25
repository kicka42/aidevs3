import os
import sys
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def send_answer_poligon(task, answer, print_response=False):
    json = {
        "task": task,
        "apikey": os.getenv("AIDEVS3_API_KEY"),
        "answer": answer
    }

    response = requests.post(os.getenv("POLIGON"), json=json)
    
    if print_response:
        print(response.json())
    
    return response.json()

def download_data(url):
    response = requests.get(url)
    return response.text

def main():
    task = "POLIGON"
    url = os.getenv("URL_POLIGON")

    data = download_data(url)
    data = data.split("\n")
    data = data[:-1]

    response = send_answer_poligon(task, data, print_response=True)

if __name__ == "__main__":
    main()