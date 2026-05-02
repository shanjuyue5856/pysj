import csv
import os
from neo4j import GraphDatabase

# Neo4j 连接配置
URI = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "du645587"  # 这里改成你自己的密码

# CSV 文件路径
CSV_PATH = "data/raw/pigments.csv"

driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)

def check_csv_file():
    """
    检查 CSV 文件是否存在
    """
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"找不到 CSV 文件：{CSV_PATH}")

    print(f"找到 CSV 文件：{CSV_PATH}")

def clear_database():
    """
    清空 Neo4j 数据库，方便重复测试
    """
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    print("已清空 Neo4j 数据库")

def create_constraints():
    """
    创建唯一约束，避免重复节点
    """
    constraints = [
        "CREATE CONSTRAINT mural_name IF NOT EXISTS FOR (m:Mural) REQUIRE m.name IS UNIQUE",
        "CREATE CONSTRAINT pigment_name IF NOT EXISTS FOR (p:Pigment) REQUIRE p.name IS UNIQUE",
        "CREATE CONSTRAINT mineral_name IF NOT EXISTS FOR (mi:Mineral) REQUIRE mi.name IS UNIQUE",
        "CREATE CONSTRAINT color_name IF NOT EXISTS FOR (c:Color) REQUIRE c.name IS UNIQUE",
        "CREATE CONSTRAINT site_name IF NOT EXISTS FOR (s:Site) REQUIRE s.name IS UNIQUE",
        "CREATE CONSTRAINT dynasty_name IF NOT EXISTS FOR (d:Dynasty) REQUIRE d.name IS UNIQUE",
        "CREATE CONSTRAINT method_name IF NOT EXISTS FOR (am:AnalysisMethod) REQUIRE am.name IS UNIQUE"
    ]

    with driver.session() as session:
        for cypher in constraints:
            session.run(cypher)

    print("唯一约束创建完成")

def import_data():
    """
    从 CSV 导入数据到 Neo4j
    """
    count = 0

    with driver.session() as session:
        with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)

            print("CSV 表头字段：", reader.fieldnames)

            for row in reader:
                # 跳过空行
                if not row or not row.get("mural"):
                    continue

                session.run(
                    """
                    MERGE (m:Mural {name: $mural})
                    MERGE (p:Pigment {name: $pigment})
                    MERGE (mi:Mineral {name: $mineral})
                    MERGE (c:Color {name: $color})
                    MERGE (s:Site {name: $site})
                    MERGE (d:Dynasty {name: $dynasty})
                    MERGE (am:AnalysisMethod {name: $method})

                    MERGE (m)-[:USES_PIGMENT]->(p)
                    MERGE (p)-[:DERIVED_FROM]->(mi)
                    MERGE (p)-[:HAS_COLOR]->(c)
                    MERGE (m)-[:LOCATED_IN]->(s)
                    MERGE (m)-[:BELONGS_TO]->(d)
                    MERGE (m)-[:ANALYZED_BY]->(am)
                    """,
                    mural=row["mural"],
                    pigment=row["pigment"],
                    mineral=row["mineral"],
                    color=row["color"],
                    site=row["site"],
                    dynasty=row["dynasty"],
                    method=row["method"]
                )

                count += 1
                print(f"已导入第 {count} 行：{row['mural']} - {row['pigment']}")

    print(f"数据导入完成，共导入 {count} 行")

def show_statistics():
    """
    显示导入后的节点和关系数量
    """
    with driver.session() as session:
        node_count = session.run(
            "MATCH (n) RETURN count(n) AS count"
        ).single()["count"]

        relation_count = session.run(
            "MATCH ()-[r]->() RETURN count(r) AS count"
        ).single()["count"]

    print("当前数据库统计：")
    print(f"节点数量：{node_count}")
    print(f"关系数量：{relation_count}")

def main():
    try:
        check_csv_file()

        # 如果你不想每次清空数据库，可以把下一行注释掉
        clear_database()

        create_constraints()
        import_data()
        show_statistics()

    except Exception as e:
        print("程序运行失败")
        print("错误信息：", e)

    finally:
        driver.close()

if __name__ == "__main__":
    main()