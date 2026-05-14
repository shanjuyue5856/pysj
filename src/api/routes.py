from flask import Blueprint, request, jsonify
import math

from src.db.neo4j_client import Neo4jClient
from src.qa.qa_service import QAService

api_bp = Blueprint("api", __name__)

neo4j_client = Neo4jClient()
qa_service = QAService(neo4j_client)

def call_qa_service(question):
    """
    兼容不同命名的 QAService 方法。
    """
    possible_methods = [
        "ask",
        "query",
        "answer",
        "answer_question",
        "process",
        "process_question",
        "get_answer",
        "handle"
    ]

    for method_name in possible_methods:
        if hasattr(qa_service, method_name):
            method = getattr(qa_service, method_name)
            return method(question)

    raise AttributeError(
        "QAService 中未找到可调用的问答方法，请检查 qa_service.py 中的方法名。"
    )

def run_cypher(cypher, params=None):
    """
    兼容不同命名的 Neo4jClient 查询方法。
    """
    params = params or {}

    possible_methods = [
        "run_query",
        "query",
        "execute",
        "run",
        "execute_query"
    ]

    for method_name in possible_methods:
        if hasattr(neo4j_client, method_name):
            method = getattr(neo4j_client, method_name)
            return method(cypher, params)

    raise AttributeError(
        "Neo4jClient 中未找到可用的查询方法，请检查 neo4j_client.py 中的方法名。"
    )

def clean_json_value(value):
    """
    清洗 Neo4j 返回的数据，避免 NaN、Infinity、Neo4j 特殊对象导致 jsonify 或前端 JSON.parse 失败。

    重点解决：
    {
        "page_pdf": NaN
    }

    标准 JSON 不支持 NaN，因此需要转成 None/null。
    """

    if value is None:
        return None

    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value

    if isinstance(value, dict):
        return {
            str(k): clean_json_value(v)
            for k, v in value.items()
        }

    if isinstance(value, list):
        return [clean_json_value(v) for v in value]

    if isinstance(value, tuple):
        return [clean_json_value(v) for v in value]

    if isinstance(value, set):
        return [clean_json_value(v) for v in value]

    if isinstance(value, (str, int, bool)):
        return value

    try:
        return str(value)
    except Exception:
        return None

def normalize_qa_result(result):
    """
    统一问答接口返回格式，避免前端拿不到 data。
    如果 qa_service 已经返回标准格式，则原样返回。
    """
    if not isinstance(result, dict):
        return {
            "code": 200,
            "msg": "success",
            "data": {
                "answer": str(result),
                "entity": None,
                "question_type": None,
                "cypher": None,
                "results": []
            }
        }

    if "code" in result and "data" in result:
        return result

    return {
        "code": result.get("code", 200),
        "msg": result.get("msg", "success"),
        "data": result
    }

@api_bp.route("/qa", methods=["POST"])
def qa():
    """
    问答接口

    请求示例：
    POST /api/qa
    {
        "question": "辰砂是什么颜色"
    }
    """
    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()

    if not question:
        return jsonify({
            "code": 400,
            "msg": "问题不能为空",
            "data": {
                "answer": "问题不能为空",
                "entity": None,
                "question_type": None,
                "cypher": None,
                "results": []
            }
        })

    try:
        result = call_qa_service(question)
        result = normalize_qa_result(result)
        result = clean_json_value(result)
        return jsonify(result)

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"问答接口异常：{str(e)}",
            "data": {
                "answer": f"问答接口异常：{str(e)}",
                "entity": None,
                "question_type": None,
                "cypher": None,
                "results": []
            }
        })

@api_bp.route("/graph", methods=["GET"])
def graph():
    """
    根据实体名称查询其附近节点和关系，用于前端知识图谱可视化。

    示例：
    /api/graph?entity=石绿&depth=2
    /api/graph?entity=敦煌&depth=2
    """
    entity = request.args.get("entity", "").strip()
    depth = request.args.get("depth", "2").strip()

    if not entity:
        return jsonify({
            "code": 400,
            "msg": "缺少 entity 参数",
            "data": {
                "nodes": [],
                "links": []
            }
        })

    try:
        depth = int(depth)
    except ValueError:
        depth = 2

    if depth < 1:
        depth = 1
    if depth > 3:
        depth = 3

    cypher = f"""
    MATCH (center)
    WHERE center.name = $entity
       OR center.title = $entity
       OR center.id = $entity
       OR center.`名称` = $entity
       OR center.label = $entity
    CALL {{
        WITH center
        OPTIONAL MATCH p = (center)-[*1..{depth}]-(n)
        RETURN collect(p) AS paths
    }}
    WITH center, paths
    WITH
        [center] + reduce(ns = [], p IN paths |
            CASE
                WHEN p IS NULL THEN ns
                ELSE ns + nodes(p)
            END
        ) AS allNodes,
        reduce(rs = [], p IN paths |
            CASE
                WHEN p IS NULL THEN rs
                ELSE rs + relationships(p)
            END
        ) AS allRels
    UNWIND allNodes AS node
    WITH collect(DISTINCT node) AS nodes, allRels
    UNWIND CASE
        WHEN size(allRels) = 0 THEN [null]
        ELSE allRels
    END AS rel
    WITH nodes, collect(DISTINCT rel) AS rels
    RETURN
        [n IN nodes | {{
            id: toString(id(n)),
            name: coalesce(n.name, n.title, n.`名称`, n.label, toString(id(n))),
            labels: labels(n),
            category: CASE
                WHEN size(labels(n)) > 0 THEN labels(n)[0]
                ELSE 'Unknown'
            END,
            properties: properties(n)
        }}] AS nodes,
        [r IN rels WHERE r IS NOT NULL | {{
            id: toString(id(r)),
            source: toString(id(startNode(r))),
            target: toString(id(endNode(r))),
            type: type(r),
            properties: properties(r)
        }}] AS links
    """

    try:
        result = run_cypher(cypher, {"entity": entity})

        if not result:
            return jsonify({
                "code": 404,
                "msg": f"未查询到“{entity}”相关图谱数据",
                "data": {
                    "nodes": [],
                    "links": []
                }
            })

        graph_data = result[0] or {}

        nodes = graph_data.get("nodes", [])
        links = graph_data.get("links", [])

        # 关键修复：清洗 NaN / Infinity / Neo4j 特殊对象
        nodes = clean_json_value(nodes)
        links = clean_json_value(links)

        return jsonify({
            "code": 200,
            "msg": "success",
            "data": {
                "nodes": nodes,
                "links": links
            }
        })

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"图谱查询失败：{str(e)}",
            "data": {
                "nodes": [],
                "links": []
            }
        })

@api_bp.route("/health", methods=["GET"])
def health():
    """
    健康检查接口
    """
    return jsonify({
        "code": 200,
        "msg": "api is running",
        "data": None
    })