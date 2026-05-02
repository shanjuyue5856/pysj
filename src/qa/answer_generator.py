class AnswerGenerator:
    def _deduplicate(self, items):
        seen = set()
        result = []
        for item in items:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result

    def generate(self, question_type, entity, results):
        if not results:
            return f"未查询到与“{entity}”相关的结果。"

        if question_type == "mural_site":
            answers = self._deduplicate([r["answer"] for r in results if r.get("answer")])
            return f"{entity}位于：{'、'.join(answers)}。"

        elif question_type == "mural_pigments":
            answers = self._deduplicate([r["answer"] for r in results if r.get("answer")])
            return f"{entity}使用的颜料包括：{'、'.join(answers)}。"

        elif question_type == "mural_methods":
            answers = self._deduplicate([r["answer"] for r in results if r.get("answer")])
            return f"{entity}采用的分析方法包括：{'、'.join(answers)}。"

        elif question_type == "pigment_color":
            answers = self._deduplicate([r["answer"] for r in results if r.get("answer")])
            return f"{entity}对应的颜色为：{'、'.join(answers)}。"

        elif question_type == "pigment_mineral":
            answers = self._deduplicate([r["answer"] for r in results if r.get("answer")])
            return f"{entity}来源于以下矿物：{'、'.join(answers)}。"

        elif question_type == "pigment_type":
            answers = self._deduplicate([r["answer"] for r in results if r.get("answer")])
            return f"{entity}属于：{'、'.join(answers)}。"

        elif question_type == "pigment_methods":
            answers = self._deduplicate([r["answer"] for r in results if r.get("answer")])
            return f"{entity}可通过以下方法识别：{'、'.join(answers)}。"

        elif question_type == "pigment_reference":
            lines = []
            for idx, r in enumerate(results, 1):
                title = r.get("title", "未知文献")
                year = r.get("year", "")
                evidence = r.get("evidence", "")
                if year and evidence:
                    lines.append(f"{idx}. {title}（{year}）；证据：{evidence}")
                elif year:
                    lines.append(f"{idx}. {title}（{year}）")
                elif evidence:
                    lines.append(f"{idx}. {title}；证据：{evidence}")
                else:
                    lines.append(f"{idx}. {title}")
            return f"与“{entity}”相关的文献和证据如下：\n" + "\n".join(lines)

        elif question_type == "mineral_elements":
            answers = self._deduplicate([r["answer"] for r in results if r.get("answer")])
            return f"{entity}包含的元素有：{'、'.join(answers)}。"

        elif question_type == "mineral_pigments":
            answers = self._deduplicate([r["answer"] for r in results if r.get("answer")])
            return f"由{entity}衍生的颜料包括：{'、'.join(answers)}。"

        elif question_type == "site_pigments":
            answers = self._deduplicate([r["answer"] for r in results if r.get("answer")])
            return f"{entity}地区壁画中常见的颜料包括：{'、'.join(answers)}。"

        elif question_type == "element_murals":
            answers = self._deduplicate([r["answer"] for r in results if r.get("answer")])
            return f"含有{entity}元素相关颜料的壁画包括：{'、'.join(answers)}。"
        elif question_type == "mineral_methods":
            answers = self._deduplicate([r["answer"] for r in results if r.get("answer")])
            return f"{entity}相关颜料可通过以下方法识别：{'、'.join(answers)}。"
        return "已完成查询，但暂未定义该问题类型的答案生成规则。"