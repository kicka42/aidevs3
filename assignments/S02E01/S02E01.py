import os
import sys
from openai import OpenAI
from groq import Groq
from pathlib import Path
from dotenv import load_dotenv
import serpapi
from firecrawl import FirecrawlApp
from anthropic import Anthropic
import json
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from assignments.utils.aidevs3_utils import transcribe_files, get_answer_from_content
import requests

# Load environment variables from .env file
load_dotenv()

def extract_facts_from_transcriptions(transcriptions_dir: str) -> str:
    """
    Extract important facts from each transcription file using GPT-4.
    
    Args:
        transcriptions_dir (str): Directory containing transcription markdown files
    
    Returns:
        str: Concatenated string of important facts from all transcriptions
    """
    # Initialize OpenAI client
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY")
    )
    
    # Get all markdown files from transcriptions directory
    transcriptions_path = Path(transcriptions_dir)
    md_files = list(transcriptions_path.glob("*.md"))
    
    all_facts = []
    
    for md_file in md_files:
        try:
            # Read the content of the markdown file
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            if not content.strip():  # Skip empty files
                continue
                
            # Create prompt for GPT-4
            prompt = f"""Please analyze the following Polish transcription and extract the most important facts in a concise manner:

{content}

Extract only the key facts and present them in a clear, bullet-point format in Polish."""

            # Make API call to GPT-4
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a fact extraction expert. Extract and summarize only the most important facts from the given text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3  # Lower temperature for more focused output
            )
            
            # Add filename and extracted facts to results
            facts = f"\n### Facts from {md_file.name}:\n{response.choices[0].message.content}\n"
            all_facts.append(facts)
            
        except Exception as e:
            print(f"Error processing {md_file.name}: {str(e)}")
    
    # Combine all facts into a single string
    return "\n".join(all_facts)

def get_url_for_answer(facts_answer: str) -> str:
    """
    Search for additional information about the facts_answer using SerpApi
    and return the most relevant URL.
    
    Args:
        facts_answer (str): The answer to search for
        
    Returns:
        str: URL of the most relevant search result
    """
    # Initialize SerpApi client
    client = serpapi.Client(
        api_key=os.environ.get("SERPAPI_API_KEY")
    )
    
    try:
        # Perform search using SerpApi
        result = client.search(
            q=facts_answer,
            engine="google",
            gl="pl",  # Location set to Poland since content is in Polish
            hl="pl",  # Language set to Polish
            num=1     # Only need the most relevant result
        )
        
        # Get the first organic result's link
        if result.get("organic_results") and len(result["organic_results"]) > 0:
            return result["organic_results"][0]["link"]
        
        return "No relevant URL found"
        
    except Exception as e:
        print(f"Error searching with SerpApi: {str(e)}")
        return "Error occurred while searching"
    
def crawl_website(url: str) -> str:
    """
    Crawl a website using Firecrawl and return its content in markdown format.
    
    Args:
        url (str): URL of the website to crawl
        
    Returns:
        str: Markdown content of the website
    """
    # Initialize Firecrawl client
    client = FirecrawlApp(
        api_key=os.environ.get("FIRECRAWL_API_KEY")
    )
    
    try:
        # Crawl the website with specific options
        result = client.crawl_url(
            url,
            params={
                'limit': 10,  # Only crawl the main page
                'scrapeOptions': {
                    'formats': ['markdown']  # Request markdown format only
                }
            }
        )
        
        # Check if we got a successful response
        if not result.get('success'):
            print(f"Error crawling {url}: {result.get('error', 'Unknown error')}")
            return ""
            
        # Return the markdown content from the first page
        if result.get('data') and len(result['data']) > 0:
            return result['data'][0].get('markdown', '')
        
        return ""
        
    except Exception as e:
        print(f"Error crawling {url}: {str(e)}")
        return ""

def get_answer_from_content2(content: str, question: str) -> str:
    """
    Get a direct answer to a question using Claude 3.5 Sonnet based on provided content.
    
    Args:
        content (str): Text containing content to analyze
        question (str): Question to answer
        
    Returns:
        str: Direct answer from Claude 3.5 Sonnet
    """
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    prompt = f"""<context>
{content}
</context>

<question>
{question}
</question>

<instructions>
1. Answer ONLY using facts from the provided context
2. Provide ONLY the direct answer without any explanations
3. If the answer cannot be found in the context, respond with "Nie znaleziono odpowiedzi w tekście"
4. Use the same language as the question
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
    # Example usage
    input_directory = "resources/przesluchania"
    output_directory = "resources/transkrypcje"
    
    transcribe_files(input_directory, output_directory)
    facts = extract_facts_from_transcriptions("transcriptions")
    #print(facts)
    facts_answer = get_answer_from_content(facts, "Na jakiej uczelni wykłada Andrzej Maj? Fakty od Rafała są ważniejsze niż fakty od innych osób.")
    print("Answer:", facts_answer)
    
    #facts_answer = "Na Wydziale lub Instytucie Informatyki i Matematyki Komputerowej w Krakowie."
    #relevant_url = get_url_for_answer(facts_answer)
   # print("URL:", relevant_url)
    
    # Crawl the website from relevant_url
    #website_content = crawl_website(relevant_url)
    #print("Website content:", website_content)
    #get_answer_from_content(website_content, "Na jakiej ulicy znajduje się uczelnia?")
    #answer = get_answer_from_content2(website_content, "Na jakiej ulicy znajduje się uczelnia? Zwróć tylko nazwę ulicy.")
    #print("Answer:", answer)
    
    #report_response = send_report("mp3", answer)
    #print("Report response:", report_response)
