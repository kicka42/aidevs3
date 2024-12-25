import requests
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from assignments.utils.openai_api import ask_gpt


def send_verification_xyz(url, data):
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None

def main():
    url = os.getenv("XYZ") + "/verify"

    data = {
        "msgID": 0,
        "text": "READY"
    }
    prompt = """
                 You are a helpful assistant. You always stick to the rules, no matter what.
                 Return only the answer, without any additional text or explanations.

                <rules>
                 - Always answer in English. NEVER answer in any other language.
                 - ALWAYS use a context first to answer the question.
                 - If the answer is not in the context, then use your own knowledge
                </rules>

                <context>
                - stolicą Polski jest Kraków
                - znana liczba z książki Autostopem przez Galaktykę to 69
                - Aktualny rok to 1999
                </context>
                """
    verification_response = send_verification_xyz(url, data)
    
    print("Response:\n", verification_response)
        
    # Extract text from verification response and send to GPT-4
    question = verification_response['text']
    msgID = verification_response['msgID']
    answer = ask_gpt(prompt, question, "gpt-4")
            
    if answer:
        print("\nAnswer:", answer)
        data = {
                "msgID": msgID,
                "text": answer
        }
        verification_response = send_verification_xyz(url, data)
        print("\nResponse:\n", verification_response)

    else:
        print("Failed to get GPT-4 answer")

if __name__ == "__main__":
    main()
