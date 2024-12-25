import os
import anthropic
import sys
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from assignments.utils.aidevs3_utils import send_report
from openai import OpenAI

def merge_facts_to_markdown():
    print("\n=== Starting merge_facts_to_markdown() ===")
    facts_dir = "resources/pliki_z_fabryki/facts"
    print(f"Looking for files in: {facts_dir}")
    
    markdown_content = ""  # Content for facts.md
    
    fact_files = sorted([f for f in os.listdir(facts_dir) if f.startswith('f') and f.endswith('.txt')])
    print(f"Found {len(fact_files)} fact files: {fact_files}")
    
    for file_name in fact_files:
        file_path = os.path.join(facts_dir, file_name)
        print(f"Processing file: {file_name}")
        
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read().strip()
            print(f"Read {len(content)} characters from {file_name}")
            
            if content.startswith("Sektor"):
                sector = content.split()[1]  # Get the sector letter
                section_name = f"# Sektor_{sector}"
            # Check for name pattern (two capitalized words)
            elif len(content.split()) >= 2 and all(word[0].isupper() for word in content.split()[:2]):
                name_parts = content.split()[:2]
                section_name = f"# {' '.join(name_parts)}"
            elif content.startswith("Azazel"):
                section_name = "# Azazel"
            else:
                section_name = f"## {file_name[:-4]}"
            
            markdown_content += f"{section_name}\n\n{content}\n\n"
    
    # Write all content to facts.md
    with open("facts.md", 'w', encoding='utf-8') as facts_file:
        facts_file.write(markdown_content)
    print("Created facts.md with all content")

def convert_reports_to_markdown():
    print("\n=== Starting convert_reports_to_markdown() ===")
    reports_dir = "resources/pliki_z_fabryki"
    output_dir = "resources/pliki_z_fabryki"
    print(f"Looking for reports in: {reports_dir}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    report_files = [f for f in os.listdir(reports_dir) if f.endswith('.txt')]
    print(f"Found {len(report_files)} report files: {report_files}")
    
    for file_name in report_files:
        print(f"\nProcessing report: {file_name}")
        input_path = os.path.join(reports_dir, file_name)
        output_file = file_name.replace('.txt', '.md')
        output_path = os.path.join(output_dir, output_file)
        
        with open(input_path, 'r', encoding='utf-8') as file:
            content = file.read().strip()
            print(f"Read {len(content)} characters from {file_name}")
        
        markdown_content = f"# {file_name}\n\n{content}\n"
        
        with open(output_path, 'w', encoding='utf-8') as output_file:
            output_file.write(markdown_content)
        print(f"Converted {file_name} to {output_file}")
    
    return output_dir

def add_keywords_to_sections(file_path):
    print(f"\n=== Processing file: {file_path} ===")
    
    client = OpenAI()  # Make sure OPENAI_API_KEY is set in your environment
    
    # Read the content of the markdown file
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Split content into lines while keeping the title
    lines = content.split('\n', 1)
    title = lines[0]
    content_without_title = content
    
    print(f"Getting keywords for: {title}")
    
    # Get keywords from GPT-4
    prompt = f"""Analyze this text and provide only a comma-separated list of Polish keywords. Always first include in the keywords the Sektor name and the name of the person:

{content_without_title}"""
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": """You are a keyword extractor focused on identifying:
- Names of individuals
- Skills of individuals
- Sector identifiers (e.g., Sektor A, B, C)
- Specific locations or areas
- Key events and activities
- Technical terms and equipment mentioned
Respond only with comma-separated keywords in Polish, no other text."""},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    
    keywords = response.choices[0].message.content.strip()
    print(f"Keywords received: {keywords}")
    
    # Create updated content with YAML frontmatter
    updated_content = f"---\nkeywords: {keywords}\n---\n{content}"
    
    # Write updated content back to the file
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(updated_content)
    
    print(f"Added keywords to {file_path}")

def process_all_markdown_files():
    print("\n=== Starting to process all markdown files ===")
    directory = "resources/pliki_z_fabryki"
    
    # Get all .md files in the directory
    md_files = [f for f in os.listdir(directory) if f.endswith('.md')]
    print(f"Found {len(md_files)} markdown files")
    
    for file_name in md_files:
        file_path = os.path.join(directory, file_name)
        add_keywords_to_sections(file_path)

def merge_keywords_with_facts():
    print("\n=== Starting merge_keywords_with_facts() ===")
    
    client = OpenAI()
    facts_dir = "resources/pliki_z_fabryki"
    result = {}
    
    # Read facts.md content first
    with open("facts.md", 'r', encoding='utf-8') as file:
        facts_content = file.read()
    
    # Extract sections with their content for better matching
    sections = {}
    current_section = None
    current_content = []
    
    for line in facts_content.split('\n'):
        if line.startswith('# '):
            if current_section:
                sections[current_section] = '\n'.join(current_content)
            current_section = line.replace('# ', '').strip()
            current_content = []
        else:
            current_content.append(line)
    if current_section:
        sections[current_section] = '\n'.join(current_content)
    
    # Process each markdown file
    md_files = [f for f in os.listdir(facts_dir) if f.endswith('.md')]
    for file_name in md_files:
        if file_name == 'facts.md':
            continue
            
        file_path = os.path.join(facts_dir, file_name)
        print(f"\n=== Processing {file_name} ===")
        
        # Read the content of the current file
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Extract the H1 title from the content
        lines = content.split('\n')
        title = next((line.replace('# ', '') for line in lines if line.startswith('# ')), '')
        
        # Find the most relevant section
        prompt = f"""Given this report:
{content}

Which of these sections is most relevant (respond with just the section name):
{', '.join(sections.keys())}"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a document matcher. Respond only with the most relevant section name from the list, nothing else."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        
        matched_section = response.choices[0].message.content.strip()
        print(f"Matched with section: {matched_section}")
        
        # Create merged keywords prompt using the matched section
        prompt = f"""Given these two texts:

1. Main section:
{sections[matched_section]}

2. Report to analyze:
{content}

Task: Create a comprehensive list of keywords that combines:
1. Keywords from the report
2. Keywords from the matched section
3. Any names of people mentioned
4. Any sector names mentioned
5. Any specific locations or areas mentioned

Provide only comma-separated keywords in Polish, no other text."""

        # Get merged keywords from GPT-4
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a keyword merger. Respond only with comma-separated keywords, nothing else."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        merged_keywords = response.choices[0].message.content.strip()
        result[str(title)] = str(merged_keywords)
        print(f"Merged keywords for: {title} {merged_keywords}")
        #print(f"Generated merged keywords for: {title}")
    
    return json.loads(json.dumps(result))

def main():
    output_dir = convert_reports_to_markdown()
    print(f"\nReports converted to markdown in: {output_dir}")
    merge_facts_to_markdown()
    add_keywords_to_sections("resources/pliki_z_fabryki/facts/facts.md")
    process_all_markdown_files()
    merged_keywords = merge_keywords_with_facts()
    send_report("dokumenty", merged_keywords)

if __name__ == "__main__":
    main()
