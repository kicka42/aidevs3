import os
from openai import OpenAI
from dotenv import load_dotenv

client = OpenAI()

# Load environment variables from .env file
load_dotenv()

# Load API keys from environments variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize the OpenAI client
client_openai = OpenAI(api_key=OPENAI_API_KEY)

def ask_gpt(prompt, question, model):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": question}
            ]
        )
        
        # Return just the answer text
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"Error getting GPT-4 response: {e}")
        return None

def get_answer_from_content(content: str, question: str) -> str:
    """
    Get an answer to a question using GPT-4 based on provided content.
    
    Args:
        content (str): Text containing content to analyze
        question (str): Question to answer
        
    Returns:
        str: Answer from GPT-4
    """
    # Initialize OpenAI client
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY")
    )
    
    # Create prompt combining content and question
    prompt = f"""Based on the following content, please answer the question. 
    Provide only the direct answer in the same language as the question without any additional explanations or context.

<rules>
1. while answering, use only facts provided in <content> section
</rules>

<content>
{content}
</content>

<question>
{question}
</question>"""
    # Make API call to GPT-4
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a precise answering assistant. Provide direct, concise answers based only on the given content."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1  # Low temperature for more focused answers
    )
    
    return response.choices[0].message.content.strip()

def connect_openai(model_name: str) -> bool:
    """
    Validates connection to OpenAI API and checks model availability.
    
    Args:
        model_name (str): The OpenAI model ID to validate (e.g. 'gpt-4-turbo-preview')
        
    Returns:
        bool: True if connection and model are valid, False otherwise
    """
    try:
        # List available models and check if requested model is available
        available_models = client_openai.models.list()
        model_exists = any(model.id == model_name for model in available_models)
        
        if not model_exists:
            print(f"Model {model_name} is not available")
            return False
            
        return True
        
    except Exception as e:
        print(f"OpenAI API error: {str(e)}")
        return False

