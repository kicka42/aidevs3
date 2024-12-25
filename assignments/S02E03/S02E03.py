import requests
from dotenv import load_dotenv
import os
from anthropic import Anthropic
import json
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import requests
from assignments.utils.aidevs3_utils import send_report

load_dotenv()

def get_robot_description():
    try:
        # Fetch data from URL
        url = f"https://centrala.ag3nts.org/data/{os.getenv('AIDEVS3_API_KEY')}/robotid.json"
        response = requests.get(url)
        data = response.json()
        
        # Extract and return description
        if 'description' in data:
            return data['description']
        else:
            return "No description found in the JSON data"
            
    except Exception as e:
        return f"Error fetching robot data: {str(e)}"

def request_anthropic_prompt(content: str, question: str = "") -> str:
    """
    Generate a Midjourney-optimized prompt based on input description.
    
    Args:
        content (str): Input description to convert into Midjourney prompt
        question (str): Ignored in this version
        
    Returns:
        str: Midjourney-optimized prompt with advanced parameters
    """
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    prompt = f"""<context>
{content}
</context>

<instructions>
You are a professional Midjourney prompt engineer
 Your task is to create a prompt that will generate exactly the image described in the context.
 Take pride in your work and give it your best - this is very important for creating the perfect visualization.

Return ONLY the final prompt text with no additional commentary.
</instructions>"""

    response = client.messages.create(
        model="claude-3-5-sonnet-latest",
        max_tokens=200,
        temperature=0.7,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )
    
    return response.content[0].text

def request_anthropic(content):
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    prompt = f"""<context>
{content}
</context>

<instructions>
Analyze the description of the image above. Provide detailed description of enviromental and objects.

Format the response as a clear, concise description with no explanations or prefixes.
</instructions>"""

    response = client.messages.create(
        model="claude-3-5-sonnet-latest",
        max_tokens=100,
        temperature=0.1,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )
    
    return response.content[0].text

if __name__ == "__main__":
    api_key = os.getenv("AIDEVS3_API_KEY")
    
    # Get the description first
    description = get_robot_description()
    print("DESCRIPTION:", description + "\n")

    description_simplyfy = request_anthropic(description)
    print("SIMPLIFIED DESCRIPTION:", description_simplyfy + "\n")
    #print(prompt)
    prompt = request_anthropic_prompt(description_simplyfy)
    print("PROMPT:", prompt + "\n")
    
    IMGURL = "https://cdn.midjourney.com/2ae8d2f2-9343-405b-86ca-af5b5a3451d8/0_0.png"
    answer = send_report("robotid", IMGURL)
    print(answer + "\n")

