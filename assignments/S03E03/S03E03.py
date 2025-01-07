import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from assignments.utils.aidevs3_utils import connect_to_apidb, send_report
from assignments.utils.openai_api import ask_gpt

def main():
    # Get all table structures
    connections = connect_to_apidb("database", "show create table connections")
    correct_order = connect_to_apidb("database", "show create table correct_order")
    datacenters = connect_to_apidb("database", "show create table datacenters")
    users = connect_to_apidb("database", "show create table users")

    # Combine all structures with clear separation
    tables_structure = f"""
    Table: connections
    {connections}

    Table: correct_order
    {correct_order}

    Table: datacenters
    {datacenters}

    Table: users
    {users}
    """
    
    print("Database structure:")
    print(tables_structure)

    prompt = f"""You are a database expert. You are given a database structure and a question. Answer ONLY with SQL query and nothing else.

    <database_structure>
    {tables_structure}
    </database_structure>

    <rules>
    - write query in one line
    - don't add "```sql" or "```"
    - you can only perform operations like: select, show tables, desc table, show create table
    </rules>
    """
    question = "które aktywne datacenter (DC_ID) są zarządzane przez pracowników, którzy są na urlopie (is_active=0)"
    answer = ask_gpt(prompt, question, "gpt-4o")
    # print("answer: ", answer)

    result = connect_to_apidb("database", answer)
    # print("result: ", result)
    
    # Extract dc_id values from the result
    answer = [int(item['dc_id']) for item in result['reply']]
    print("answer: ", answer)

    # Send the answer to the task
    send_report("database", answer)
    
if __name__ == "__main__":
    main()