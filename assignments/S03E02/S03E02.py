import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from assignments.utils.aidevs3_utils import send_report
from assignments.utils.qdrant_utils import QdrantManager

def main():
    qdrant_manager = QdrantManager()
    reports_folder = "resources/do-not-share"
    question = "W raporcie, z którego dnia znajduje się wzmianka o kradzieży prototypu broni?"
    print("question = ", question)

    with open("question.txt", 'w', encoding='utf-8') as f:
        f.write(question)

    qdrant_manager.index_documents(reports_folder, "reports")
    result = qdrant_manager.search("question.txt", "reports")
    print("\nresult = ", result)

    send_report("wektory", result)

if __name__ == "__main__":
    main()