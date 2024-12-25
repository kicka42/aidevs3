import os
import json
import re
import sys
import frontmatter
from pathlib import Path
from typing import Dict, List
from openai import OpenAI
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from assignments.utils.aidevs3_utils import transcribe_audio_with_groq, extract_text_from_images, send_report, txt_to_markdown


def categorize_files(directory_path: str) -> Dict[str, List[str]]:
    """
    Categorize markdown files into people, hardware, or other using GPT-4.
    """
    print("\n=== Starting file categorization ===")
    
    # Initialize categories
    categories = {
        "people": [],
        "hardware": [],
        "other": []
    }
    print(f"Processing files from directory: {directory_path}")
    
    # Initialize OpenAI client
    client = OpenAI()
    
    # Get all markdown files
    md_files = [f for f in os.listdir(directory_path) if f.endswith('.md')]
    print(f"Found {len(md_files)} markdown files to process")
    
    system_prompt = """You are a Technical Content Classifier. Categorize files into: `people`, `hardware`, or `other`.

1. STRIP METADATA
   - Remove headers, timestamps, signatures, departments, approvals

2. CATEGORIZE BY PRIORITY:

   FIRST check for `people` - REQUIRES ALL:
   - Direct evidence of captured intruders
   - Physical signs of unauthorized entry
   - NOT routine personnel reports
   - NOT general human mentions
   - NOT communication logs
   - NOT patrol records

   THEN check for `hardware` - REQUIRES ALL:
   - Physical component repairs
   - Mechanical fixes
   - Manual maintenance
   - NOT software changes
   - NOT system updates
   - NOT performance metrics
   - NOT communication systems

   OTHERWISE `other`:
   - Default category unless strict people/hardware criteria met
   - ALL software/system content
   - ALL communication content
   - ALL updates/monitoring
   - ALL routine activities
   - ALL patrol reports
   - ALL maintenance logs

3. VERIFY:
   - Metadata stripped
   - Meets ALL category requirements
   - System/software = `other`
   - When in doubt = `other`

<thinking>
1. Content
2. Indicators
3. Rule
4. Category
</thinking>

<examples>
<example_one>był tam Jan Kowalski którego aresztowalismy → people</example_one>
<example_two>kamera została zdemontowana i wymieniona → hardware</example_two>
<example_three>roboty udały się do lasu → other</example_three>
</examples>
"""

    # Process each markdown file
    for md_file in md_files:
        print(f"\nProcessing file: {md_file}")
        md_path = os.path.join(directory_path, md_file)
        
        # Read markdown content
        with open(md_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
            content = post.content
            original_filename = post.get('filename', md_file)
            print(f"Original filename: {original_filename}")
            print(f"Content length: {len(content)} characters")
        
        # Get category from GPT-4
        print("Sending to GPT-4 for categorization...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ],
            temperature=0
        )
        
        # Extract category from response
        category_response = response.choices[0].message.content.lower()
        print(f"GPT-4 response: {category_response}")
        
        # Determine category
        if 'people' in category_response:
            categories['people'].append(original_filename)
            print(f"Categorized as: people")
        elif 'hardware' in category_response:
            categories['hardware'].append(original_filename)
            print(f"Categorized as: hardware") 
        else:
            categories['other'].append(original_filename)
            print(f"Categorized as: other")

    # Remove 'other' category files
    print("\n=== Final Results ===")
    print(f"People files: {len(categories['people'])}")
    print(f"Hardware files: {len(categories['hardware'])}")
    print(f"Other files: {len(categories['other'])} (will be removed)")
    del categories['other']
    
    return categories

def main():

    resources_files_path = "resources/pliki_z_fabryki/"

    txt_to_markdown(resources_files_path, overwrite=False)

    transcribe_files_results = transcribe_audio_with_groq(resources_files_path, overwrite=False)
    #print(transcribe_files_results)

    transcribe_images_results = extract_text_from_images(resources_files_path, overwrite=False)
    #print(transcribe_images_results)

    results = categorize_files(resources_files_path)
    print(json.dumps(results, indent=2))

    report_response = send_report("kategorie", results)
    print(report_response)

if __name__ == "__main__":
    main()
