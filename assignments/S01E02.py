import requests
from openai import OpenAI

def send_verification(data):
    url = "https://xyz.ag3nts.org/verify"

    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None

def send_question(text):
    try:
        client = OpenAI()  # Uses OPENAI_API_KEY from environment variables
        
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": """
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
                """},
                {"role": "user", "content": text}
            ]
        )
        
        return completion.choices[0].message.content
        
    except Exception as e:
        print(f"Error calling GPT-4: {e}")
        return None

def main():
    data = {
        "msgID": 0,
        "text": "READY"
    }
    verification_response = send_verification(data)
    
    print("Response:\n", verification_response)
        
    # Extract text from verification response and send to GPT-4
    question = verification_response['text']
    msgID = verification_response['msgID']
    answer = send_question(question)
            
    if answer:
        print("\nAnswer:", answer)
        data = {
                "msgID": msgID,
                "text": answer
        }
        verification_response = send_verification(data)
        print("\nResponse:\n", verification_response)

    else:
        print("Failed to get GPT-4 answer")

if __name__ == "__main__":
    main()
