import sys
import os

# 让 scripts 能找到 src
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from src.db.neo4j_client import Neo4jClient
from src.qa.qa_service import QAService

def main():
    client = Neo4jClient()
    service = QAService(client)

    print("古代壁画矿物颜料知识图谱问答系统（命令行版）")
    print("输入 exit 退出\n")

    while True:
        question = input("请输入问题：").strip()
        if question.lower() in ["exit", "quit"]:
            break

        result = service.answer_question(question)
        print("\n系统回答：")
        if result.get("data"):
            print(result["data"].get("answer"))
        else:
            print(result.get("msg"))
        print("-" * 50)

    client.close()

if __name__ == "__main__":
    main()