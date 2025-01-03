from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Filter, FieldCondition, MatchAny
from openai import OpenAI
import json
import os
from dotenv import load_dotenv

def connect_to_qdrant():
    """
    Establishes connection to Qdrant vector database using environment variables.
    Returns a QdrantClient instance.
    """
    load_dotenv()
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    
    if not qdrant_url or not qdrant_api_key:
        raise ValueError("QDRANT_URL and QDRANT_API_KEY must be set in .env file")
    
    try:
        client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key
        )
        client.get_collections()
        print("Successfully connected to Qdrant")
        return client
    except Exception as e:
        print(f"Error connecting to Qdrant: {str(e)}")
        raise

def generate_embedding(model, file_path):
    print(f"\n=== Generating embedding for {file_path} ===")
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    print("OpenAI client initialized")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    print(f"File content read: {len(content)} characters")
    
    print("Generating embedding...")
    response = client.embeddings.create(
        input=content,
        model=model
    )
    print("Embedding generated successfully")
    return response.data[0].embedding

def extract_metadata(file_path):
    print(f"\n=== Extracting metadata for {file_path} ===")
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    print("OpenAI client initialized")
    
    filename = os.path.basename(file_path)
    date_str = filename.split('.')[0]
    try:
        year, month, day = date_str.split('_')
        formatted_date = f"{year}-{month}-{day}"
    except ValueError:
        print("WARNING: Could not parse date from filename")
        formatted_date = None
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    print(f"File content read: {len(content)} characters")
    
    print("Creating GPT-4 prompt...")
    prompt = """Analyze the following text and provide:
1. A title (it always in the first line of the file)
2. 5-7 relevant keywords

Respond in JSON format like this:
{
    "title": "your_title_here",
    "keywords": ["keyword1", "keyword2", "etc"]
}

Text to analyze:

"""
    
    print("Sending request to GPT-4...")
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a precise document analyzer. Respond only with the requested JSON format."},
            {"role": "user", "content": prompt + content}
        ],
        temperature=0.3
    )
    print("Received response from GPT-4")
    
    try:
        gpt_analysis = json.loads(response.choices[0].message.content)
        print("Successfully parsed GPT-4 response")
        
        metadata = {
            "filename": filename,
            "date": formatted_date,
            "title": gpt_analysis["title"],
            "keywords": gpt_analysis["keywords"]
        }
        print(f"Metadata extracted: {json.dumps(metadata, indent=2)}")
        return metadata
        
    except json.JSONDecodeError:
        print("ERROR: Failed to parse GPT-4 response")
        raise Exception("Failed to parse GPT-4 response into JSON format")

class QdrantManager:
    def __init__(self):
        self.client = connect_to_qdrant()

    def index_documents(self, reports_folder, collection_name):
        print(f"\n=== Indexing documents from {reports_folder} to Qdrant ===")
        
        print("Creating/resetting Qdrant collection...")
        self.client.recreate_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=1536,
                distance=models.Distance.COSINE
            )
        )
        print(f"Collection '{collection_name}' created/reset successfully")

        txt_files = [f for f in os.listdir(reports_folder) if f.endswith('.txt')]
        total_files = len(txt_files)
        print(f"\nFound {total_files} text files to process")

        for idx, filename in enumerate(txt_files, 1):
            print(f"\nProcessing file {idx}/{total_files}: {filename}")
            file_path = os.path.join(reports_folder, filename)
            try:
                print("Generating embedding...")
                embedding = generate_embedding("text-embedding-3-small", file_path)
                print("Embedding generated successfully")
                
                print("Extracting metadata...")
                metadata = extract_metadata(file_path)
                print("Metadata extracted successfully")
                
                point_id = abs(hash(filename)) % (2**63)
                
                print("Uploading to Qdrant...")
                self.client.upsert(
                    collection_name=collection_name,
                    points=[
                        models.PointStruct(
                            id=point_id,
                            vector=embedding,
                            payload=metadata
                        )
                    ]
                )
                print(f"✓ Successfully indexed {filename}")
                
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
                continue

        print(f"\n=== Indexing complete. Processed {total_files} files ===")

    def search(self, question, collection_name):
        print(f"\n=== Searching for answer to: {question} ===")
        
        question_embedding = generate_embedding("text-embedding-3-small", question)
        print("Question embedding generated")
        
        # Search for the single best match across all documents
        search_results = self.client.search(
            collection_name=collection_name,
            query_vector=question_embedding,
            limit=1  # Get only the top match
        )
        
        if search_results:
            best_match = search_results[0]  # This will be the highest scoring match
            print(f"\nFound match with score: {best_match.score}")
            print(f"Document metadata: {json.dumps(best_match.payload, indent=2)}")
            print(f"\nAnswer found in document dated: {best_match.payload.get('date')}")
            return best_match.payload.get('date')
        else:
            print("No matching documents found")
            return None
