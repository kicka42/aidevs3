import sys
import os
from bs4 import BeautifulSoup
import requests
import markdown
from openai import OpenAI
from dotenv import load_dotenv
import base64
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from assignments.utils.openai_api import get_answer_from_content
from assignments.utils.aidevs3_utils import send_report, process_image

def fetch_questions(url):
    """Fetch and parse questions from the given URL"""
    print("\nFetching questions from URL")
    response = requests.get(url)
    print(f"Questions response status code: {response.status_code}")
    questions = response.text.strip().split('\n')
    print(f"Number of questions: {len(questions)}")
    return questions

def process_questions(questions, content):
    """Process each question and return answers dictionary"""
    answers = {}
    print("\nProcessing questions:")
    for question in questions:
        # Split question ID and text using '=' as separator
        q_id, q_text = question.split('=', 1)
        formatted_id = f"{q_id.zfill(2)}"
        print(f"\nProcessing question {formatted_id}")
        print(f"Question text: {q_text}")
        
        # Get answer using the utility function
        answer = get_answer_from_content(content, q_text)
        print(f"Generated answer: {answer}")
        answers[formatted_id] = answer
    return answers

def main():
    load_dotenv()
    AIDEVS3_API_KEY = os.getenv('AIDEVS3_API_KEY')
    S02E05_ARTICLE_URL = os.getenv('S02E05_ARTICLE_URL')
    S02E05_QUESTIONS_URL = os.getenv('S02E05_QUESTIONS_URL')
    
    if not AIDEVS3_API_KEY:
        raise ValueError("AIDEVS3_API_KEY not found in environment variables")
    
    print("\n=== Starting main execution ===")
    print(f"Questions URL: {S02E05_QUESTIONS_URL}")

    # Uncomment these lines to generate the markdown file
    markdown_content = html_to_markdown(S02E05_ARTICLE_URL)
    output_file = "resources/article.md"
    print(f"\nReading content from {output_file}")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    
    # Read the markdown content
    with open(output_file, "r", encoding="utf-8") as f:
        content = f.read()
    print(f"Content length: {len(content)} characters")
    
    # Get and process questions
    questions = fetch_questions(S02E05_QUESTIONS_URL)
    answers = process_questions(questions, content)

    # Print the final JSON response
    print("\n=== Final JSON response ===")
    print(json.dumps(answers, indent=2, ensure_ascii=False))
    return answers

if __name__ == "__main__":
    answer = main()
    response = send_report("arxiv", answer)
    print(response)
    
