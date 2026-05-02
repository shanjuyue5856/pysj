from flask import Blueprint, jsonify, request
from src.db.neo4j_client import Neo4jClient
from src.qa.qa_service import QAService
from src.qa.schema_loader import QUESTION_SCHEMA

api_bp = Blueprint("api", __name__)

neo4j_client = Neo4jClient()
qa_service = QAService(neo4j_client)

@api_bp.route("/health", methods=["GET"])
def health():
    try:
        result = neo4j_client.run_query("RETURN 1 AS ok")
        return jsonify({
            "code": 200,
            "msg": "success",
            "data": {
                "service": "kgqa-backend",
                "neo4j": "connected" if result else "unknown"
            }
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"Neo4j连接失败: {str(e)}",
            "data": None
        })

@api_bp.route("/schema", methods=["GET"])
def schema():
    return jsonify({
        "code": 200,
        "msg": "success",
        "data": QUESTION_SCHEMA
    })

@api_bp.route("/examples", methods=["GET"])
def examples():
    examples = []
    for key, value in QUESTION_SCHEMA.items():
        for ex in value.get("examples", []):
            examples.append({
                "type": key,
                "question": ex
            })

    return jsonify({
        "code": 200,
        "msg": "success",
        "data": examples
    })

@api_bp.route("/refresh_entities", methods=["POST"])
def refresh_entities():
    qa_service.refresh_entities()
    return jsonify({
        "code": 200,
        "msg": "实体词典已刷新",
        "data": None
    })

@api_bp.route("/qa", methods=["POST"])
def qa():
    data = request.get_json(silent=True) or {}
    question = data.get("question", "")
    result = qa_service.answer_question(question)
    print("问题：", question)
    print("返回：", result)
    return jsonify(result)