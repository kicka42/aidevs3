import requests
from time import sleep
import re
import openai
from openai.types.chat import ChatCompletionMessage, ChatCompletionChunk
from typing import List, Dict
from urllib.parse import urlencode


class OpenAIService:
    def __init__(self):
        self.client = openai.OpenAI()

    def completion(self, messages: List[Dict[str, str]], model: str, stream: bool = False):
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=stream
            )
            return response
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

openai_service = OpenAIService()

def get_question(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            # Use regex to find content between Question:<br> and </p>
            pattern = r'Question:<br />(.*?)</p>'
            match = re.search(pattern, response.text)
            if match:
                return match.group(1)
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching question: {e}")
        return None
    
def send_question(question: str) -> str:
    try:
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Provide only the direct answer without any additional text or explanations. The answer is ALWAYS a number."},
            {"role": "user", "content": question}
        ]
        
        response = openai_service.completion(
            messages=messages,
            model="gpt-4"
        )
        
        # Return just the answer text
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"Error getting GPT-4 response: {e}")
        return None

def submit_form(url: str, login: str, password: str, answer: str) -> tuple[bool, str]:
    """Submit the form with login credentials and answer"""
    try:
        data = urlencode({
            "username": login,
            "password": password,
            "answer": answer
        })
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = requests.post(
            url, 
            data=data,
            headers=headers
        )
        
        # Print the response content
        print("\nResponse:")
        print(response.text)
        
        # Check if login was successful
        if "Question:" in response.text:
            return False, "Login failed - form still present"
            
        return True, response.text
        
    except Exception as e:
        return False, f"Error submitting form: {str(e)}"

def main():
    url = "https://xyz.ag3nts.org/"
    login = "tester"
    password = "574e112a"
    
    while True:
        try:
            question = get_question(url)
            if not question:
                print("Failed to get question, retrying in 25 seconds...")
                sleep(25)
                continue
                
            answer = send_question(question)
            if not answer:
                print("Failed to get answer, retrying in 25 seconds...")
                sleep(25)
                continue
            
            # Submit and print response
            success, response = submit_form(url, login, password, answer)
            
            print(f"Question: {question}")
            print(f"Answer: {answer}")


            # Check for href link in response
            href_match = re.search(r'<a href="(.*?)"', response)
            if href_match:
                next_path = href_match.group(1)
                url = url.rstrip('/') + '/' + next_path.lstrip('/')
                print(f"\nURL found: {url}")
            
            if "FLG:" in response:
                flag_match = re.search(r'FLG:(.*?)}', response)
                if flag_match:
                    print(f"\nFlag found: {flag_match.group(1)}")
            
            if success:
                print("\nSuccessfully submitted form!")
                break

            
            print("\nSubmission failed, retrying in 25 seconds...")
            sleep(25)
            
        except Exception as e:
            print(f"\nError occurred: {e}")
            print("Retrying in 25 seconds...")
            sleep(25)

if __name__ == "__main__":
    main() 