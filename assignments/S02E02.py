import anthropic
from anthropic import Anthropic
import base64
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def analyze_map_images(map_directory: str, api_key: str) -> list:
    """
    Analyze historical map images using Anthropic's Claude API.
    
    Args:
        map_directory (str): Path to directory containing map images
        api_key (str): Anthropic API key
    
    Returns:
        list: List of analysis results for each map
    """
    # Get API key from environment variable
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
    
    # Initialize Anthropic client
    client = anthropic.Anthropic(api_key=api_key)
    
    # Get list of supported image formats
    supported_formats = ['.jpg', '.jpeg', '.png']
    results = []
    
    def get_base64_encoded_image(image_path):
        with open(image_path, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    # Process each image in directory
    for image_file in Path(map_directory).iterdir():
        if image_file.suffix.lower() in supported_formats:
            print(f"\nProcessing image: {image_file.name}")
            try:
                # Updated prompt with more specific cartographic analysis
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": f"image/{image_file.suffix[1:]}",
                                    "data": get_base64_encoded_image(str(image_file))
                                }
                            },
                            {
                                "type": "text",
                                "text": """You are a specialized historical cartographer with expertise in Polish city maps, particularly from regions with German influence. Examining this map fragment, your task is to identify which Polish city this represents, keeping in mind it was known for its granaries and fortresses.

Using your perfect attention to detail, analyze this map section in <thinking> tags using these exact steps:

1. First, identify and list ALL visible street names in the image:
   - List each street name exactly as written
   - Note any partial street names
   - Pay attention to language (Polish/German elements)

2. Examine the map's visual style and features:
   - Determine if it's a historical map
   - Note the time period based on style and texture
   - List all circular or special symbols
   - Describe what these symbols might represent

3. Study the geographical elements:
   - Describe the street layout (grid/irregular)
   - Note any signs of city center or important districts
   - Look for evidence of fortifications
   - Identify any major structures or facilities

4. Review the historical context:
   - Consider what you know about granary cities
   - Look for fortress-related elements
   - Note any Polish-German historical connections
   - Think about strategic city locations

5. Connect all evidence to identify the city:
   - Link street names to known Polish cities
   - Connect layout to historical records
   - Consider the granary/fortress context
   - Look for matches to Grudziądz/Graudenz characteristics

After your step-by-step analysis, provide your final identification in <answer> tags, including:
- City name (both Polish and German versions)
- How the street names support this identification
- Connection to granaries and fortresses
- Relevance of any special symbols or features

Be explicit about how each observed detail supports your conclusion about the city's identity."""
                            }
                        ]
                    }
                ]

                print(f"Sending request to Claude API...")
                response = client.messages.create(
                    model="claude-3-5-sonnet-latest",
                    max_tokens=1000,
                    temperature=0,
                    messages=messages
                )
                print(f"Received response from Claude API")

                # Store results
                results.append({
                    'image_path': str(image_file),
                    'analysis': response.content[0].text
                })

            except Exception as e:
                print(f"Error processing {image_file.name}: {str(e)}")
                results.append({
                    'image_path': str(image_file),
                    'analysis': f"Error: {str(e)}"
                })
    
    return results

def request_anthropic(content: str, question: str) -> str:
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

if __name__ == "__main__":
    api_key = os.getenv("ANTHROPIC_API_KEY")
    map_directory = "resources/map/"
    
    analyses = analyze_map_images(map_directory, api_key)
    
    # Convert analyses to a single string
    analyses_text = "\n\n".join([f"Analysis for {a['image_path']}:\n{a['analysis']}" for a in analyses])
    
    # Ask which Polish city is shown in most maps
    answer = request_anthropic(
        content=analyses_text,
        question="które polskie miasto przedstawia większośc tych map?"
    )
    
    # Print results
    print("\n=== Individual Analyses ===")
    for analysis in analyses:
        print(f"\nAnalysis for {analysis['image_path']}:")
        print(analysis['analysis'])
        
    print("\n=== City Identification ===")
    print(answer)
