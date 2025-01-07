import os
import requests
import json
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from openai import OpenAI
from anthropic import Anthropic
from groq import Groq
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv
import base64
from bs4 import BeautifulSoup
import markdown

load_dotenv()


def send_answer_centrala(task, answer):
    """
    Sends the corrected JSON data to the specified endpoint.
    """
    api_key = os.getenv('AIDEVS3_API_KEY')
    url_report = os.getenv('URL_REPORT')

    try:
        # Prepare the payload
        payload = {
            "task": task,
            "apikey": api_key,
            "answer": answer
        }

        print(payload)
        
        # Send POST request
        print("Sending answer...")
        response = requests.post(
            url_report,
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        # Check response
        response.raise_for_status()
        print(f"Success! Response: {response.text}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error sending request: {str(e)}")

def send_report(task: str, answer: str) -> str:
    """
    Send a report to the AIDEVS3 API.
    
    Args:
        task (str): Task identifier
        answer (str): Answer to submit
        
    Returns:
        str: Response from the API
    """
    try:
        url = os.getenv('URL_REPORT')
        api_key = os.getenv('AIDEVS3_API_KEY')
        
        if not url or not api_key:
            raise ValueError("URL_REPORT or AIDEVS3_API_KEY environment variable is not set")
        
        data = {
            "task": task,
            "apikey": api_key,
            "answer": answer
        }
        
        json_data = json.dumps(data).encode('utf-8')
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        request = Request(url, data=json_data, headers=headers, method='POST')
        
        with urlopen(request) as response:
            # Print response headers
            print("\nResponse Headers:")
            for header, value in response.headers.items():
                print(f"{header}: {value}")
            
            # Get and print response body
            response_text = response.read().decode('utf-8')
            print(f"\nResponse Body:\n{response_text}")
            return response_text
    
    except (HTTPError, URLError, Exception) as e:
        print(f"Error in send_report: {str(e)}")
        return None

# S02E05
def process_audio(audio_url):
    """Process audio using Whisper and return transcription"""
    client = OpenAI()
    
    # Download the audio file
    response = requests.get(audio_url)
    print(f"Downloaded audio from {audio_url}, status code: {response.status_code}")
    
    # Save temporarily
    temp_audio_path = "temp_audio.mp3"
    with open(temp_audio_path, "wb") as f:
        f.write(response.content)
    print(f"Audio saved to {temp_audio_path}")
    
    # Get transcription using Whisper
    try:
        with open(temp_audio_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        print(f"Transcription received: {transcription.text}")
        print(f"Transcription length: {len(transcription.text)} characters")
        # Return just the transcription text
        return transcription.text
        
    finally:
        # Clean up temporary file
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        print(f"Temporary file {temp_audio_path} removed")

# S02E04
def transcribe_audio_with_groq(input_folder: str, overwrite: bool = False) -> dict:


    """
    Transcribe audio files to markdown files.
    
    Args:
        input_dir (str): Directory containing audio files
        overwrite (bool): Whether to overwrite existing transcriptions
        
    Returns:
        dict: Summary of transcription results
    """
    # Initialize Groq client
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    # Define supported audio formats
    SUPPORTED_FORMATS = {".m4a", ".mp3", ".wav", ".ogg", ".flac", ".aac"}
    
    # Get all audio files
    audio_files = [
        f for f in Path(input_folder).iterdir()
        if f.suffix.lower() in SUPPORTED_FORMATS
    ]
    
    results = {"processed": 0, "skipped": 0, "failed": 0}
    
    for audio_file in audio_files:
        output_file = audio_file.parent / f"{audio_file.stem}.md"
        
        # Skip if file exists and not overwriting
        if output_file.exists() and not overwrite:
            print(f"Skipping {audio_file.name} - transcription exists")
            results["skipped"] += 1
            continue
        
        print(f"Transcribing {audio_file.name}...")
        
        try:
            # Validate file size (25MB limit)
            if audio_file.stat().st_size > 25 * 1024 * 1024:
                raise ValueError("File too large (max 25MB)")
            
            with open(audio_file, "rb") as file:
                transcription = client.audio.transcriptions.create(
                    file=(str(audio_file), file.read()),
                    model="whisper-large-v3-turbo",
                    response_format="text"
                )
            
            # Create content with YAML front matter metadata and content
            content = f"""---
filename: {audio_file.name}
---

{transcription}"""
            
            # Write transcription to file
            output_file.write_text(content, encoding="utf-8")
            print(f"✓ Successfully transcribed to {output_file}")
            results["processed"] += 1
            
        except Exception as e:
            print(f"✗ Error transcribing {audio_file.name}: {str(e)}")
            results["failed"] += 1
    
    return results

# S02E05
def process_image(image_url, caption=""):
    """Process image using GPT-4V and return markdown-formatted description"""
    client = OpenAI()
    
    # Ensure the image URL is complete
    if not image_url.startswith(('http://', 'https://')):
        image_url = f"https://{image_url}"
    
    # Download and encode image
    response = requests.get(image_url)
    image_data = base64.b64encode(response.content).decode('utf-8')
    
    # Get image description from GPT-4V
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Describe this image briefly with attention to details and context. Do it all in Polish. Context: {caption}"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}"
                        }
                    }
                ]
            }
        ],
        max_tokens=100
    )
    
    description = response.choices[0].message.content
    return description

# S02E04
def extract_text_from_images(input_folder: str, overwrite: bool = False) -> dict:

    """
    Extract text from images using GPT-4 Vision and save as markdown files.
    
    Args:
        input_folder (str): Path to folder containing image files
        overwrite (bool): If True, overwrite existing markdown files. If False, skip existing files.
    
    Returns:
        dict: Dictionary of transcriptions {filename: text}
    """
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    # Define supported image formats
    SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    
    # Get all image files
    image_files = [
        f for f in Path(input_folder).iterdir()
        if f.suffix.lower() in SUPPORTED_FORMATS
    ]
    
    transcriptions = {}
    
    for image_file in image_files:
        md_filename = image_file.stem + ".md"
        md_path = Path(input_folder) / md_filename
        
        if md_path.exists() and not overwrite:
            print(f"Skipping existing file: {md_filename}")
            continue
            
        try:
            # Read image file as base64
            with open(image_file, "rb") as img_file:
                response = client.chat.completions.create(
                    model="gpt-4o",  # Using the correct model name
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Please extract and return ONLY the text content from this image. Do not include any additional formatting, comments, or metadata."},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64.b64encode(img_file.read()).decode('utf-8')}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=1000
                )
                
            text = response.choices[0].message.content
            transcriptions[image_file.name] = text
            
            # Create content with YAML front matter metadata and content
            content = f"""---
filename: {image_file.name}
---

{text}"""
    
            
            # Write to markdown file
            md_path.write_text(content, encoding="utf-8")
            print(f"Created markdown file: {md_filename}")
            
        except Exception as e:
            print(f"Error processing {image_file.name}: {e}")
    
    return transcriptions

# S02E02
def request_anthropic(content: str, question: str, prompt: str) -> str:
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    prompt = prompt.format(content=content, question=question)

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

# S02E05
def html_to_markdown(url):

    """Convert HTML article to markdown with processed images and audio in their original positions"""
    print(f"\n=== Starting HTML to Markdown conversion for {url} ===")
    
    # Fetch the article
    response = requests.get(url)
    print(f"Fetched article with status code: {response.status_code}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Get base URL for resolving relative paths
    base_url = '/'.join(url.split('/')[:-1]) + '/'
    print(f"Base URL for resolving paths: {base_url}")
    
    # Process the content
    markdown_content = []
    
    # First, find the main article content
    article = soup.find('article') or soup
    
    for element in article.find_all(['p', 'h1', 'h2', 'h3', 'figure', 'audio', 'a']):
        print(f"\nProcessing element: {element.name}")
        
        if element.name in ['h1', 'h2', 'h3']:
            header_text = element.get_text().strip()
            header_level = int(element.name[1])
            markdown_line = f"{'#' * header_level} {header_text}\n\n"
            markdown_content.append(markdown_line)
            print(f"Added header: {header_text}")
            
        elif element.name == 'figure':
            # Handle figure elements (images with captions)
            img = element.find('img')
            if img and img.get('src'):
                img_url = img['src']
                if not img_url.startswith(('http://', 'https://')):
                    img_url = base_url + img_url.lstrip('/')
                    if 'i/' not in img_url:  # Add 'i/' directory if not present
                        img_url = base_url + 'i/' + img_url.split('/')[-1]
                
                print(f"Processing image: {img_url}")
                
                # Get caption if exists
                caption = element.find('figcaption')
                caption_text = caption.get_text().strip() if caption else ""
                print(f"Image caption: {caption_text}")
                
                # Add image markdown with caption
                markdown_content.append(f"![{caption_text}]({img_url})\n\n")
                
                # Generate and add image description with context
                description = process_image(img_url, caption_text)
                markdown_content.append(f"*Image Description:* {description}\n\n")
                print(f"Added image with description")
                
        elif element.name == 'audio':
            # Handle audio elements
            source = element.find('source')
            if source and source.get('src'):
                audio_url = source['src']
                if not audio_url.startswith(('http://', 'https://')):
                    audio_url = base_url + audio_url.lstrip('/')
                
                print(f"Processing audio: {audio_url}")
                
                # Add audio file reference
                file_name = audio_url.split('/')[-1]
                markdown_content.append(f"🔊 *Audio File:* [{file_name}]({audio_url})\n\n")
                
                # Generate and add transcription
                transcription = process_audio(audio_url)
                markdown_content.append(f"*Transcription:* {transcription}\n\n")
                print(f"Added audio with transcription")
                
        elif element.name == 'a' and element.get('href', '').endswith('.mp3'):
            # Handle direct audio download links
            audio_url = element['href']
            if not audio_url.startswith(('http://', 'https://')):
                audio_url = base_url + audio_url.lstrip('/')
            
            print(f"Processing audio link: {audio_url}")
            
            # Check if this audio link hasn't been processed yet
            file_name = audio_url.split('/')[-1]
            if not any(file_name in content for content in markdown_content):
                markdown_content.append(f"🔊 *Audio File:* [{file_name}]({audio_url})\n\n")
                
                # Generate and add transcription
                transcription = process_audio(audio_url)
                markdown_content.append(f"*Transcription:* {transcription}\n\n")
                print(f"Added audio link with transcription")
                
        elif element.name == 'p':
            # Skip paragraphs that are part of figure captions or audio controls
            if element.find_parent('figure') or element.find_parent('audio'):
                continue
                
            para_text = element.get_text().strip()
            if para_text:  # Only add non-empty paragraphs
                markdown_content.append(f"{para_text}\n\n")
                print(f"Added paragraph: {para_text[:50]}...")
    
    print("\n=== Finished processing HTML to Markdown ===")
    print(f"Total elements processed: {len(markdown_content)}")
    
    return ''.join(markdown_content)

# S02E04
def txt_to_markdown(directory_path: str, overwrite: bool = False) -> List[str]:
    """
    Convert all .txt files in a directory to .md files with metadata.
    
    Args:
        directory_path (str): Path to directory containing .txt files
        overwrite (bool): If True, overwrites existing .md files. If False, skips existing files.
        
    Returns:
        List[str]: List of created markdown file paths
    """
    created_files = []
    
    # Ensure directory exists
    if not os.path.exists(directory_path):
        raise ValueError(f"Directory not found: {directory_path}")
        
    # Get all .txt files in directory
    txt_files = [f for f in os.listdir(directory_path) if f.endswith('.txt')]
    
    for txt_file in txt_files:
        txt_path = os.path.join(directory_path, txt_file)
        md_file = txt_file.replace('.txt', '.md')
        md_path = os.path.join(directory_path, md_file)
        
        # Skip if file exists and overwrite is False
        if os.path.exists(md_path) and not overwrite:
            continue
            
        # Read content from txt file
        with open(txt_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Create markdown content with metadata
        md_content = f"""---
filename: {txt_file}
---

{content}"""
        
        # Write markdown file
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
            
        created_files.append(md_path)
        
    return created_files

#
def connect_to_apidb(task, query):
    """
    Connect to the API using credentials from .env file
    
    Args:
        task (str): Task type to be performed
        query (str): SQL query to be executed
        
    Returns:
        str: Table structure if 'show create table' query, otherwise full response
    """
    # Load environment variables
    load_dotenv()
    
    api_key = os.getenv('AIDEVS3_API_KEY')
    apidb_url = os.getenv('APIDB_URL')

    print(f"Connecting to API: {apidb_url}")
    
    # Prepare request payload
    payload = {
        "task": task,
        "apikey": api_key,
        "query": query
    }
    
    # Convert payload to JSON string
    json_payload = json.dumps(payload)
    
    try:
        response = requests.post(apidb_url, data=json_payload)
        response.raise_for_status()
        
        # Print response headers and body for debugging
        print("\nResponse Headers:")
        for header, value in response.headers.items():
            print(f"{header}: {value}")
        print(f"\nResponse Body:\n{response.text}")
        
        # Parse the response
        json_response = response.json()
        
        # If it's a 'show create table' query, extract just the table structure
        if query.lower().startswith('show create table'):
            return json_response['reply'][0]['Create Table']
        
        return json_response
        
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to API: {e}")
        return None
