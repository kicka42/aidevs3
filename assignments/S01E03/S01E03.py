import json
from typing import List, Dict
import operator
import requests
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from assignments.utils.openai_api import ask_gpt
from assignments.utils.aidevs3_utils import send_report

def validate_math_equations(json_file_path: str) -> None:
    """
    Validates and corrects math equations in JSON file.
    Processes data in chunks to handle large files efficiently.
    """
    print(f"Starting validation of {json_file_path}")
    
    # Define operators mapping
    operators_map = {
        '+': operator.add,
        '-': operator.sub,
        '*': operator.mul,
        '/': operator.truediv
    }
    
    # Read JSON file
    print("Reading JSON file...")
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    
    # Get test data array
    test_data = data.get('test-data', [])
    total_items = len(test_data)
    chunk_size = 10  # Changed to process 10 items at a time
    total_chunks = (total_items + chunk_size - 1) // chunk_size
    
    print(f"Found {total_items} equations to validate")
    print(f"Processing in {total_chunks} chunks of {chunk_size} items")
    
    # Process in chunks
    corrections_made = 0
    for i in range(0, total_items, chunk_size):
        chunk = test_data[i:i + chunk_size]
        chunk_num = (i // chunk_size) + 1
        print(f"\nProcessing chunk {chunk_num}/{total_chunks} (items {i}-{min(i+chunk_size, total_items)})")
        corrections = process_chunk(chunk, operators_map)
        corrections_made += corrections
    
    print(f"\nValidation complete!")
    print(f"Total corrections made: {corrections_made}")
    
    # Save corrected data back to file
    print(f"Saving corrected data back to {json_file_path}")
    with open(json_file_path, 'w') as file:
        json.dump(data, file, indent=4)
    print("Done!")

def process_test_questions(json_file_path: str) -> None:
    """
    Process only the test questions from the JSON file using GPT-4.
    Updates the 'a' property with one-word answers from GPT-4.
    """
    prompt = """
    You must provide only a single word as an answer. No punctuation or explanation.
    """
    print(f"Starting test questions processing for {json_file_path}")
    
    # Read JSON file
    print("Reading JSON file...")
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
                print(f"\nProcessing test question: {question}")
                
                try:
                    answer = ask_gpt(prompt, question, "gpt-4")
                    
                    if answer:
                        # Update the answer in the data
                        item['test']['a'] = answer
                        questions_processed += 1
                        print(f"Answer received: {answer}")
                    
                except Exception as e:
                    print(f"Error processing question: {str(e)}")
                    continue
    
    print(f"\nProcessed {questions_processed} test questions")
    
    # Save updated data back to file
    print(f"Saving updated data back to {json_file_path}")
    with open(json_file_path, 'w') as file:
        json.dump(data, file, indent=4)
    print("Done!")

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
                        print(f"Found incorrect equation: {equation} = {item.get('answer')} (should be {correct_answer})")
                        item['answer'] = correct_answer
                        corrections += 1
                        
            except (ValueError, TypeError, ZeroDivisionError) as e:
                # Skip invalid equations
                print(f"Error processing equation '{equation}': {str(e)}")
                continue
    
    if corrections:
        print(f"Made {corrections} corrections in this chunk")
    else:
        print("All equations in this chunk are correct")
    
    return corrections

def main():
    json_file_path = 'resources/json.txt'

    # Read JSON file once
    try:
        with open(json_file_path, 'r') as file:
            json_data = json.load(file)
    except FileNotFoundError:
        print(f"Error: File {json_file_path} not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: Invalid JSON file")
        sys.exit(1)

    # Run the validation first
    validate_math_equations(json_file_path)
    
    # Then process the test questions
    process_test_questions(json_file_path)
    
    # Finally, send the corrected JSON to the endpoint
    send_report("centrala", json_data)

if __name__ == "__main__":
    main()