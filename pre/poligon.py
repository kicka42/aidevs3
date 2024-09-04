from utils.aidevs3_api import download_data, send_answer

task = "POLIGON"
url = "https://poligon.aidevs.pl/dane.txt"

data = download_data(url)
data = data.split("\n")
data = data[:-1]

response = send_answer(task, data, print_response=True)