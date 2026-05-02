import re
from rapidfuzz import fuzz
from config import Config

class EntityMatcher:
    def __init__(self, neo4j_client):
        self.neo4j_client = neo4j_client
        self.entity_dict = self.neo4j_client.get_all_entity_names()

    def refresh(self):
        self.entity_dict = self.neo4j_client.get_all_entity_names()

    def normalize_text(self, text):
        """
        文本标准化：
        1. 去空格
        2. 统一小括号/中文括号
        3. 去掉括号及其中内容后的简称
        """
        if not text:
            return ""

        text = text.strip()
        text = text.replace("(", "（").replace(")", "）")
        return text

    def remove_brackets_content(self, text):
        """
        辰砂（α-HgS） -> 辰砂
        赤铁矿（α-Fe2O3） -> 赤铁矿
        """
        if not text:
            return ""
        text = re.sub(r'（.*?）', '', text)
        return text.strip()

    def _match_element_pattern(self, question):
        pattern = r'([A-Z][a-z]?)元素|含([A-Z][a-z]?)'
        match = re.search(pattern, question)
        if match:
            element = match.group(1) or match.group(2)
            return {
                "entity": element,
                "type": "Element",
                "score": 100
            }
        return None

    def _direct_match(self, question):
        question_norm = self.normalize_text(question)
        matches = []

        for entity_type, names in self.entity_dict.items():
            for name in names:
                if not name:
                    continue

                name_norm = self.normalize_text(name)
                short_name = self.remove_brackets_content(name_norm)

                # 1. 完整名称匹配
                if name_norm in question_norm:
                    matches.append({
                        "entity": name,
                        "type": entity_type,
                        "score": 100
                    })
                    continue

                # 2. 简称匹配
                if short_name and short_name in question_norm:
                    matches.append({
                        "entity": name,
                        "type": entity_type,
                        "score": 95
                    })
                    continue

        return matches

    def _fuzzy_match(self, question):
        question_norm = self.normalize_text(question)
        best_match = None
        threshold = Config.ENTITY_MATCH_THRESHOLD

        for entity_type, names in self.entity_dict.items():
            for name in names:
                if not name:
                    continue

                name_norm = self.normalize_text(name)
                short_name = self.remove_brackets_content(name_norm)

                score1 = fuzz.partial_ratio(name_norm, question_norm)
                score2 = fuzz.partial_ratio(short_name, question_norm) if short_name else 0
                score = max(score1, score2)

                if score >= threshold:
                    if best_match is None or score > best_match["score"]:
                        best_match = {
                            "entity": name,
                            "type": entity_type,
                            "score": score
                        }

        return best_match

    def match(self, question):
        question = question.strip()

        # 1. 元素特殊处理
        element_match = self._match_element_pattern(question)
        if element_match:
            return element_match

        # 2. 直接/简称匹配
        direct_matches = self._direct_match(question)
        if direct_matches:
            direct_matches.sort(
                key=lambda x: (x["score"], len(x["entity"])),
                reverse=True
            )
            return direct_matches[0]

        # 3. 模糊匹配
        fuzzy_match = self._fuzzy_match(question)
        if fuzzy_match:
            return fuzzy_match

        return None