import os
import json
import requests
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from dotenv import load_dotenv

load_dotenv()

def get_content(url):
    try:
        # Create a Request object with headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        request = Request(url, headers=headers)
        
        # Download the content and display headers
        with urlopen(request) as response:
            # Print response headers
            #print("\nResponse Headers:")
            #for key, value in response.headers.items():
            #    print(f"{key}: {value}")
            
            content = response.read().decode('utf-8')
        
        # Find text after the first colon
        if content:
            return content
            
        return None
        
    except HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
        return None
    except URLError as e:
        print(f"URL Error: {e.reason}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def send_to_ai(content):
    try:
        url = os.getenv('URL_CLOUDFLARE_LAMA-3-2')
        if not url:
            raise ValueError("URL_CLOUDFLARE_LAMA-3-2 environment variable is not set")
            
        # Prepare the data
        data = f"text={content}"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Create request object
        request = Request(
            url,
            data=data.encode('utf-8'),  # Convert string to bytes
            headers=headers,
            method='POST'
        )
        
        # Send request and get response
        with urlopen(request) as response:
            return response.read().decode('utf-8')
            
    except HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
        return None
    except URLError as e:
        print(f"URL Error: {e.reason}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def send_report(task, answer):
    try:
        url = os.getenv('URL_REPORT')
        api_key = os.getenv('AIDEVS3_API_KEY')
        
        if not url or not api_key:
            raise ValueError("URL_REPORT or AIDEVS3_API_KEY environment variable is not set")
        
        # Prepare the JSON data
        data = {
            "task": task,
            "apikey": api_key,
            "answer": answer
        }
        
        # Display JSON data before sending
        print("\nSending JSON data:")
        print(json.dumps(data, indent=2))

        # Convert data to JSON string
        json_data = json.dumps(data).encode('utf-8')
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Create request object
        request = Request(
            url,
            data=json_data,
            headers=headers,
            method='POST'
        )
        
        # Send request and get response
        with urlopen(request) as response:
            return response.read().decode('utf-8')
            
    except HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
        return None
    except URLError as e:
        print(f"URL Error: {e.reason}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    URL_CENZURA = os.getenv('URL_CENZURA')
    
    if not URL_CENZURA:
        raise ValueError("URL_CENZURA environment variable is not set")
        
    content = get_content(URL_CENZURA)
    print("Content:", content)
    if content:
        ai_response = send_to_ai(content)
        print(f"AI Response: {ai_response}")
        if ai_response:
            # Send the report with task name and AI response
            report_response = send_report("CENZURA", ai_response)
            print(f"Report Response: {report_response}")

# Prompt for llama-32-3b-instruct
# Replace all personal information with the word CENZURA while maintaining the exact original text structure, punctuation, and spacing. Return only the censored text without any additional explanations or formatting.
#
# <rules>
# 1. Replace with CENZURA:
#    - First and last names (as a single unit)
#    - City names 
#    - Street names with numbers (as a single unit)
#    - Age numbers
#
# 2. Keep unchanged:
#    - All periods, commas, and spaces
#    - All descriptive text and phrases
#    - Words that are not personal data
#    - Original sentence structure
#
# 3. Important:
#    - Always use CENZURA in its base form (never CENZURY, CENZURZE, etc.)
#    - The word CENZURA must stay exactly the same regardless of the grammatical case in the original text
# </rules>
#
# <example 1>
# Input: Dane personalne podejrzanego: Wojciech Górski. Przebywa w Lublinie, ul. Akacjowa 7. Wiek: 27 lat.
# Output: Dane personalne podejrzanego: CENZURA. Przebywa w CENZURA, ul. CENZURA. Wiek: CENZURA lat.
# </example 1>
#
# <example 2>
# Input: Nazywam się James Bond. Mieszkam w Warszawie na ulicy Pięknej 5. Mam 28 lat.
# Output: Nazywam się CENZURA. Mieszkam w CENZURA na ulicy CENZURA. Mam CENZURA lat.
# </example 2>
#
# Replace all personal information with the word CENZURA while maintaining the exact original text structure, punctuation, and spacing. Return only the censored text without any additional explanations or formatting.
