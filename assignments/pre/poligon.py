import os
import sys
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.aidevs3_api import send_answer

def download_data(url):
    response = requests.get(url)
    return response.text

task = "POLIGON"
url = "https://poligon.aidevs.pl/dane.txt"

data = download_data(url)
data = data.split("\n")
data = data[:-1]

response = send_answer(task, data, print_response=True)