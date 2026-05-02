import re
from src.db.neo4j_client import Neo4jClient

SUBSCRIPT_MAP = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")

def normalize_formula(text: str) -> str:
    """
    统一化学式格式：
    - 下标数字转普通数字：₂ -> 2
    - 去掉空格
    """
    if not text:
        return ""
    text = text.translate(SUBSCRIPT_MAP)
    text = text.replace(" ", "")
    return text

def extract_formula_from_name(name: str) -> str:
    """
    从矿物名称中提取化学式。
    示例：
    - 辰砂（α-HgS） -> HgS
    - 赤铁矿（α-Fe2O3） -> Fe2O3
    - 孔雀石（Cu₂CO₃(OH)₂） -> Cu2CO3(OH)2
    """
    if not name:
        return ""

    # 取中文全角括号中的内容
    m = re.search(r'（([^）]+)）', name)
    if not m:
        return ""

    formula = m.group(1)
    formula = normalize_formula(formula)

    # 去掉前缀相标，如 α- β- γ-
    formula = re.sub(r'^[αβγδεζηθμ\-]+', '', formula)
    formula = re.sub(r'^[A-Za-zα-ωΑ-Ω]+-', '', formula)  # 再兜底去掉字母前缀-

    # 如果里面包含明显不是化学式的内容，可按需继续清洗
    return formula

def parse_elements(formula: str):
    """
    从化学式中提取元素符号（去重，保持顺序）
    示例：
    - HgS -> ['Hg', 'S']
    - Fe2O3 -> ['Fe', 'O']
    - Cu2CO3(OH)2 -> ['Cu', 'C', 'O', 'H']
    """
    if not formula:
        return []

    # 匹配元素符号：一个大写字母，后面可跟一个小写字母
    elems = re.findall(r'[A-Z][a-z]?', formula)

    # 去重并保持顺序
    result = []
    seen = set()
    for e in elems:
        if e not in seen:
            seen.add(e)
            result.append(e)
    return result

def main():
    client = Neo4jClient()

    try:
        # 读取所有矿物节点
        query = """
        MATCH (m:Mineral)
        RETURN m.name AS name
        """
        records = client.run_query(query)

        total = 0
        success = 0
        skipped = 0

        for row in records:
            name = row.get("name")
            total += 1

            formula = extract_formula_from_name(name)
            elements = parse_elements(formula)

            if not formula or not elements:
                print(f"[跳过] {name} -> 未提取到有效化学式")
                skipped += 1
                continue

            print(f"[处理] {name}")
            print(f"       化学式: {formula}")
            print(f"       元素: {elements}")

            for elem in elements:
                merge_query = """
                MATCH (m:Mineral {name:$mineral_name})
                MERGE (e:Element {name:$element_name})
                MERGE (m)-[:HAS_ELEMENT]->(e)
                """
                client.run_query(
                    merge_query,
                    {
                        "mineral_name": name,
                        "element_name": elem
                    }
                )

            success += 1

        print("\n========== 完成 ==========")
        print(f"矿物总数: {total}")
        print(f"成功补全: {success}")
        print(f"跳过数量: {skipped}")

    finally:
        client.close()

if __name__ == "__main__":
    main()