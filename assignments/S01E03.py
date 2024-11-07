import json
from typing import List, Dict
import operator
import asyncio
from openai import AsyncOpenAI
import requests

async def process_test_questions(json_file_path: str, openai_client) -> None:
    """
    Process only the test questions from the JSON file using GPT-4.
    Updates the 'a' property with one-word answers from GPT-4.
    """
    print(f"🔍 Starting test questions processing for {json_file_path}")
    
    # Read JSON file
    print("📖 Reading JSON file...")
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    
    # Get test data array
    test_data = data.get('test-data', [])
    questions_processed = 0
    
    # Process each item that has a test question
    for item in test_data:
        if 'test' in item and isinstance(item['test'], dict):
            question = item['test'].get('q')
            if question:
                print(f"\n❓ Processing test question: {question}")
                
                try:
                    # Create GPT-4 prompt requesting one-word answer
                    response = await openai_client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You must provide only a single word as an answer. No punctuation or explanation."},
                            {"role": "user", "content": question}
                        ],
                        temperature=0.7,
                        max_tokens=10  # Limiting tokens since we only need one word
                    )
                    
                    # Extract the one-word answer
                    answer = response.choices[0].message.content.strip()
                    
                    # Update the answer in the data
                    item['test']['a'] = answer
                    questions_processed += 1
                    print(f"✅ Answer received: {answer}")
                    
                except Exception as e:
                    print(f"⚠️ Error processing question: {str(e)}")
                    continue
    
    print(f"\n📝 Processed {questions_processed} test questions")
    
    # Save updated data back to file
    print(f"💾 Saving updated data back to {json_file_path}")
    with open(json_file_path, 'w') as file:
        json.dump(data, file, indent=4)
    print("✨ Done!")

def validate_math_equations(json_file_path: str) -> None:
    """
    Validates and corrects math equations in JSON file.
    Processes data in chunks to handle large files efficiently.
    """
    print(f"🔍 Starting validation of {json_file_path}")
    
    # Define operators mapping
    operators_map = {
        '+': operator.add,
        '-': operator.sub,
        '*': operator.mul,
        '/': operator.truediv
    }
    
    # Read JSON file
    print("📖 Reading JSON file...")
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    
    # Get test data array
    test_data = data.get('test-data', [])
    total_items = len(test_data)
    chunk_size = 10  # Changed to process 10 items at a time
    total_chunks = (total_items + chunk_size - 1) // chunk_size
    
    print(f"📊 Found {total_items} equations to validate")
    print(f"🔄 Processing in {total_chunks} chunks of {chunk_size} items")
    
    # Process in chunks
    corrections_made = 0
    for i in range(0, total_items, chunk_size):
        chunk = test_data[i:i + chunk_size]
        chunk_num = (i // chunk_size) + 1
        print(f"\n⚙️ Processing chunk {chunk_num}/{total_chunks} (items {i}-{min(i+chunk_size, total_items)})")
        corrections = process_chunk(chunk, operators_map)
        corrections_made += corrections
    
    print(f"\n✅ Validation complete!")
    print(f"📝 Total corrections made: {corrections_made}")
    
    # Save corrected data back to file
    print(f"💾 Saving corrected data back to {json_file_path}")
    with open(json_file_path, 'w') as file:
        json.dump(data, file, indent=4)
    print("✨ Done!")

def process_chunk(chunk: List[Dict], operators_map: Dict) -> int:
    """Process a chunk of test data items."""
    corrections = 0
    
    for item in chunk:
        if 'question' in item and isinstance(item['question'], str):
            try:
                # Parse the equation
                equation = item['question'].strip()
                nums = []
                operator_char = None
                
                # Extract numbers and operator
                for op in operators_map.keys():
                    if op in equation:
                        operator_char = op
                        nums = [int(x.strip()) for x in equation.split(op)]
                        break
                
                if len(nums) == 2 and operator_char:
                    # Calculate correct answer
                    correct_answer = operators_map[operator_char](nums[0], nums[1])
                    
                    # Update answer if it's different
                    if item.get('answer') != correct_answer:
                        print(f"❌ Found incorrect equation: {equation} = {item.get('answer')} (should be {correct_answer})")
                        item['answer'] = correct_answer
                        corrections += 1
                        
            except (ValueError, TypeError, ZeroDivisionError) as e:
                # Skip invalid equations
                print(f"⚠️ Error processing equation '{equation}': {str(e)}")
                continue
    
    if corrections:
        print(f"🔧 Made {corrections} corrections in this chunk")
    else:
        print("✅ All equations in this chunk are correct")
    
    return corrections

def send_json_to_endpoint(json_file_path: str, api_key: str) -> None:
    """
    Sends the corrected JSON file to the specified endpoint.
    """
    print(f"📤 Preparing to send JSON from {json_file_path} to endpoint...")
    
    try:
        # Read the JSON file
        with open(json_file_path, 'r') as file:
            json_data = json.load(file)
        
        # Prepare the payload
        payload = {
            "task": "JSON",
            "apikey": api_key,
            "answer": json_data
        }
        
        # Send POST request
        print("🌐 Sending request to centrala.ag3nts.org...")
        response = requests.post(
            "https://centrala.ag3nts.org/report",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        # Check response
        response.raise_for_status()
        print(f"✅ Success! Response: {response.text}")
        
    except FileNotFoundError:
        print(f"❌ Error: File {json_file_path} not found")
    except json.JSONDecodeError:
        print("❌ Error: Invalid JSON file")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending request: {str(e)}")

# Example usage
if __name__ == "__main__":
    # API key for the endpoint
    API_KEY = "bcab1589-581d-4e97-b98b-56f8e25b0f0e"
    
    # Initialize OpenAI client with API key from environment
    client = AsyncOpenAI()  # This will automatically use OPENAI_API_KEY from environment
    
    # Run the validation first
    validate_math_equations('json.txt')
    
    # Then process the test questions
    asyncio.run(process_test_questions('json.txt', client))
    
    # Finally, send the corrected JSON to the endpoint
    send_json_to_endpoint('json.txt', API_KEY)
