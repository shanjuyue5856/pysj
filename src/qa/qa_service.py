from src.qa.question_classifier import QuestionClassifier
from src.qa.cypher_builder import CypherBuilder
from src.qa.answer_generator import AnswerGenerator
from src.qa.entity_matcher import EntityMatcher

class QAService:
    def __init__(self, neo4j_client):
        self.neo4j_client = neo4j_client
        self.entity_matcher = EntityMatcher(neo4j_client)
        self.classifier = QuestionClassifier()
        self.cypher_builder = CypherBuilder()
        self.answer_generator = AnswerGenerator()

    def refresh_entities(self):
        self.entity_matcher.refresh()

    def answer_question(self, question):
        question = (question or "").strip()
        if not question:
            return {
                "code": 400,
                "msg": "问题不能为空",
                "data": None
            }

        entity_info = self.entity_matcher.match(question)
        if not entity_info:
            return {
                "code": 404,
                "msg": "未识别到问题中的实体",
                "data": {
                    "question": question,
                    "answer": "抱歉，我暂时无法识别你问题中的核心实体，请尝试使用图谱中的标准名称重新提问。"
                }
            }

        question_type = self.classifier.classify(question, entity_info)
        if question_type == "unknown":
            return {
                "code": 405,
                "msg": "未识别到问题类型",
                "data": {
                    "question": question,
                    "entity": entity_info,
                    "answer": "抱歉，我暂时无法理解这个问题的查询意图。"
                }
            }

        cypher, params = self.cypher_builder.build(question_type, entity_info["entity"])
        if not cypher:
            return {
                "code": 500,
                "msg": "Cypher 生成失败",
                "data": None
            }

        try:
            results = self.neo4j_client.run_query(cypher, params)
            answer = self.answer_generator.generate(question_type, entity_info["entity"], results)

            return {
                "code": 200,
                "msg": "success",
                "data": {
                    "question": question,
                    "entity": entity_info,
                    "question_type": question_type,
                    "cypher": cypher.strip(),
                    "params": params,
                    "results": results,
                    "answer": answer
                }
            }
        except Exception as e:
            return {
                "code": 500,
                "msg": f"查询异常：{str(e)}",
                "data": None
            }