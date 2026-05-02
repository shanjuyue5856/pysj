from neo4j import GraphDatabase

# =========================
# 1. 修改成你的 Neo4j 连接信息
# =========================
URI = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "du645587"

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def run_query(cypher, params=None):
    with driver.session() as session:
        result = session.run(cypher, params or {})
        return [record.data() for record in result]

def print_title(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def main():
    try:
        # 1. 所有标签
        print_title("1. 所有标签（Labels）")
        labels = run_query("CALL db.labels()")
        for item in labels:
            print(item)

        # 2. 所有关系类型
        print_title("2. 所有关系类型（Relationship Types）")
        rels = run_query("CALL db.relationshipTypes()")
        for item in rels:
            print(item)

        # 提取标签名
        label_list = []
        for item in labels:
            # Neo4j 不同版本返回字段名可能不一样
            value = list(item.values())[0]
            label_list.append(value)

        # 3. 每个标签的示例节点
        for label in label_list:
            print_title(f"3. 标签 {label} 的示例节点")
            cypher = f"MATCH (n:`{label}`) RETURN n LIMIT 3"
            try:
                rows = run_query(cypher)
                if rows:
                    for row in rows:
                        print(row)
                else:
                    print("无数据")
            except Exception as e:
                print(f"查询失败: {e}")

        # 4. 每个标签的属性名
        for label in label_list:
            print_title(f"4. 标签 {label} 的属性名")
            cypher = f"MATCH (n:`{label}`) RETURN keys(n) AS property_keys LIMIT 5"
            try:
                rows = run_query(cypher)
                if rows:
                    for row in rows:
                        print(row)
                else:
                    print("无数据")
            except Exception as e:
                print(f"查询失败: {e}")

        # 5. 查看关系结构
        print_title("5. 节点之间的关系结构")
        cypher = """
        MATCH (a)-[r]->(b)
        RETURN labels(a) AS from_labels, type(r) AS rel_type, labels(b) AS to_labels
        LIMIT 50
        """
        rows = run_query(cypher)
        if rows:
            for row in rows:
                print(row)
        else:
            print("无关系数据")

        # 6. 查看关系的完整示例
        print_title("6. 关系完整示例（含节点内容）")
        cypher = """
        MATCH (a)-[r]->(b)
        RETURN a, type(r) AS rel_type, b
        LIMIT 10
        """
        rows = run_query(cypher)
        if rows:
            for row in rows:
                print(row)
        else:
            print("无关系示例数据")

    except Exception as e:
        print("\n程序运行出错：", e)

    finally:
        driver.close()

if __name__ == "__main__":
    main()