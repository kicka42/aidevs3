import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load API keys from environments variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize the OpenAI client
client_openai = OpenAI(api_key=OPENAI_API_KEY)

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

