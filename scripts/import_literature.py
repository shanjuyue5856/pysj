# -*- coding: utf-8 -*-
"""
import_literature.py

用于将 evidence_enriched.csv 导入 Neo4j
适配 Evidence 节点版古代壁画矿物颜料知识图谱

核心结构：
(:Reference)-[:HAS_EVIDENCE]->(:Evidence)-[:DESCRIBES]->(:Pigment)-[:DERIVED_FROM]->(:Mineral)

推荐 CSV 字段：
reference,pigment,mineral,evidence_text,source_ref,page_pdf,table_or_fig,color,site,mural,analysis_method,notes

运行：
python import_literature.py

首次全量重建：
python import_literature.py --clear

依赖：
pip install neo4j pandas python-dotenv
"""

import os
import sys
import math
import hashlib
import argparse
import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase

DEFAULT_CSV_PATH = "data/evidence_enriched.csv"
DEFAULT_URI = "bolt://localhost:7687"
DEFAULT_USER = "neo4j"
DEFAULT_PASSWORD = "du645587"

REQUIRED_COLUMNS = ["reference", "pigment", "mineral", "evidence_text"]

OPTIONAL_COLUMNS = [
    "source_ref",
    "page_pdf",
    "table_or_fig",
    "color",
    "site",
    "mural",
    "analysis_method",
    "notes",
]

def clean_value(v):
    if v is None:
        return ""
    if isinstance(v, float) and math.isnan(v):
        return ""
    v = str(v).strip()
    if v.lower() in ["nan", "none", "null"]:
        return ""
    return v

def safe_int(v):
    v = clean_value(v)
    if not v:
        return None
    try:
        return int(float(v))
    except Exception:
        return None

def split_multi_values(v):
    v = clean_value(v)
    if not v:
        return []

    values = [v]
    for sep in ["；", ";", "，", ",", "/", "|"]:
        temp = []
        for item in values:
            temp.extend(item.split(sep))
        values = temp

    return [x.strip() for x in values if x.strip()]

def make_evidence_id(reference, pigment, mineral, evidence_text, source_ref="", page_pdf="", table_or_fig=""):
    raw = "|".join([
        clean_value(reference),
        clean_value(pigment),
        clean_value(mineral),
        clean_value(evidence_text),
        clean_value(source_ref),
        clean_value(page_pdf),
        clean_value(table_or_fig),
    ])
    return hashlib.md5(raw.encode("utf-8")).hexdigest()

def read_csv_smart(csv_path):
    encodings = ["utf-8-sig", "utf-8", "gbk", "gb18030"]
    last_error = None

    for enc in encodings:
        try:
            df = pd.read_csv(csv_path, encoding=enc)
            print(f"✅ CSV 读取成功，编码：{enc}")
            return df
        except Exception as e:
            last_error = e

    raise RuntimeError(f"CSV 读取失败：{last_error}")

def normalize_dataframe(df):
    df.columns = [str(c).strip() for c in df.columns]

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            f"CSV 缺少必需字段：{missing}\n"
            f"当前字段：{list(df.columns)}"
        )

    for col in OPTIONAL_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    for col in df.columns:
        df[col] = df[col].apply(clean_value)

    before = len(df)
    df = df[
        (df["reference"] != "") &
        (df["pigment"] != "") &
        (df["mineral"] != "") &
        (df["evidence_text"] != "")
    ].copy()
    after = len(df)

    if before != after:
        print(f"⚠️ 已跳过 {before - after} 行关键字段为空的数据")

    df["page_pdf_int"] = df["page_pdf"].apply(safe_int)

    df["evidence_id"] = df.apply(
        lambda row: make_evidence_id(
            row["reference"],
            row["pigment"],
            row["mineral"],
            row["evidence_text"],
            row.get("source_ref", ""),
            row.get("page_pdf", ""),
            row.get("table_or_fig", "")
        ),
        axis=1
    )

    return df

def extract_year(reference):
    import re
    m = re.search(r"(19|20)\d{2}", clean_value(reference))
    if m:
        return int(m.group(0))
    return None

class LiteratureImporter:
    def __init__(self, uri, user, password, database=None):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database

    def close(self):
        self.driver.close()

    def run_write(self, query, params=None):
        with self.driver.session(database=self.database) as session:
            return session.execute_write(lambda tx: list(tx.run(query, params or {})))

    def run_read(self, query, params=None):
        with self.driver.session(database=self.database) as session:
            return session.execute_read(lambda tx: list(tx.run(query, params or {})))

    def test_connection(self):
        try:
            result = self.run_read("RETURN 1 AS ok")
            if result and result[0]["ok"] == 1:
                print("✅ Neo4j 连接成功")
        except Exception as e:
            print("❌ Neo4j 连接失败")
            print(e)
            sys.exit(1)

    def clear_database(self):
        print("⚠️ 正在清空数据库...")
        self.run_write("MATCH (n) DETACH DELETE n")
        print("✅ 数据库已清空")

    def create_constraints(self):
        queries = [
            """
            CREATE CONSTRAINT reference_title_unique IF NOT EXISTS
            FOR (n:Reference) REQUIRE n.title IS UNIQUE
            """,
            """
            CREATE CONSTRAINT pigment_name_unique IF NOT EXISTS
            FOR (n:Pigment) REQUIRE n.name IS UNIQUE
            """,
            """
            CREATE CONSTRAINT mineral_name_unique IF NOT EXISTS
            FOR (n:Mineral) REQUIRE n.name IS UNIQUE
            """,
            """
            CREATE CONSTRAINT evidence_id_unique IF NOT EXISTS
            FOR (n:Evidence) REQUIRE n.id IS UNIQUE
            """,
            """
            CREATE CONSTRAINT color_name_unique IF NOT EXISTS
            FOR (n:Color) REQUIRE n.name IS UNIQUE
            """,
            """
            CREATE CONSTRAINT site_name_unique IF NOT EXISTS
            FOR (n:Site) REQUIRE n.name IS UNIQUE
            """,
            """
            CREATE CONSTRAINT mural_name_unique IF NOT EXISTS
            FOR (n:Mural) REQUIRE n.name IS UNIQUE
            """,
            """
            CREATE CONSTRAINT method_name_unique IF NOT EXISTS
            FOR (n:AnalysisMethod) REQUIRE n.name IS UNIQUE
            """
        ]

        print("🔧 创建约束中...")
        for q in queries:
            try:
                self.run_write(q)
            except Exception as e:
                print(f"⚠️ 约束创建提示：{str(e)[:120]}")
        print("✅ 约束处理完成")

    def import_batch(self, rows):
        query = """
        UNWIND $rows AS row

        MERGE (ref:Reference {title: row.reference})
        SET ref.year = row.reference_year,
            ref.raw = row.reference

        MERGE (p:Pigment {name: row.pigment})
        MERGE (m:Mineral {name: row.mineral})

        MERGE (ev:Evidence {id: row.evidence_id})
        SET ev.reference = row.reference,
            ev.pigment = row.pigment,
            ev.mineral = row.mineral,
            ev.evidence_text = row.evidence_text,
            ev.source_ref = row.source_ref,
            ev.page_pdf = row.page_pdf_int,
            ev.table_or_fig = row.table_or_fig,
            ev.notes = row.notes

        MERGE (ref)-[:HAS_EVIDENCE]->(ev)
        MERGE (ev)-[:DESCRIBES]->(p)
        MERGE (p)-[:DERIVED_FROM]->(m)

        FOREACH (_ IN CASE WHEN row.color <> "" THEN [1] ELSE [] END |
            MERGE (c:Color {name: row.color})
            MERGE (p)-[:HAS_COLOR]->(c)
        )

        FOREACH (_ IN CASE WHEN row.mural <> "" THEN [1] ELSE [] END |
            MERGE (mu:Mural {name: row.mural})
            MERGE (mu)-[:USES_PIGMENT]->(p)
        )

        FOREACH (_ IN CASE WHEN row.site <> "" AND row.mural <> "" THEN [1] ELSE [] END |
            MERGE (mu2:Mural {name: row.mural})
            MERGE (s:Site {name: row.site})
            MERGE (mu2)-[:LOCATED_IN]->(s)
        )
        """
        self.run_write(query, {"rows": rows})

    def import_methods_batch(self, rows):
        method_rows = []

        for row in rows:
            methods = split_multi_values(row.get("analysis_method", ""))
            for method in methods:
                method_rows.append({
                    "evidence_id": row["evidence_id"],
                    "method": method,
                    "mural": row.get("mural", ""),
                    "pigment": row.get("pigment", ""),
                })

        if not method_rows:
            return

        query = """
        UNWIND $rows AS row

        MERGE (am:AnalysisMethod {name: row.method})

        WITH row, am
        MATCH (ev:Evidence {id: row.evidence_id})
        MERGE (ev)-[:SUPPORTED_BY_METHOD]->(am)

        WITH row, am
        OPTIONAL MATCH (mu:Mural {name: row.mural})
        FOREACH (_ IN CASE WHEN mu IS NOT NULL THEN [1] ELSE [] END |
            MERGE (mu)-[:ANALYZED_BY]->(am)
        )

        WITH row, am
        OPTIONAL MATCH (p:Pigment {name: row.pigment})
        FOREACH (_ IN CASE WHEN p IS NOT NULL THEN [1] ELSE [] END |
            MERGE (p)-[:IDENTIFIED_BY]->(am)
        )
        """
        self.run_write(query, {"rows": method_rows})

    def import_dataframe(self, df, batch_size=100):
        total = len(df)
        print(f"🚀 开始导入，共 {total} 条记录")

        rows_all = []
        for _, row in df.iterrows():
            rows_all.append({
                "reference": clean_value(row["reference"]),
                "reference_year": extract_year(row["reference"]),
                "pigment": clean_value(row["pigment"]),
                "mineral": clean_value(row["mineral"]),
                "evidence_text": clean_value(row["evidence_text"]),
                "source_ref": clean_value(row.get("source_ref", "")),
                "page_pdf": clean_value(row.get("page_pdf", "")),
                "page_pdf_int": row.get("page_pdf_int", None),
                "table_or_fig": clean_value(row.get("table_or_fig", "")),
                "color": clean_value(row.get("color", "")),
                "site": clean_value(row.get("site", "")),
                "mural": clean_value(row.get("mural", "")),
                "analysis_method": clean_value(row.get("analysis_method", "")),
                "notes": clean_value(row.get("notes", "")),
                "evidence_id": clean_value(row["evidence_id"]),
            })

        for start in range(0, total, batch_size):
            batch = rows_all[start:start + batch_size]
            self.import_batch(batch)
            self.import_methods_batch(batch)
            print(f"✅ 已导入 {min(start + batch_size, total)}/{total}")

        print("🎉 导入完成")

    def print_summary(self):
        print("\n📊 节点统计")
        stats = {
            "Reference": "MATCH (n:Reference) RETURN count(n) AS cnt",
            "Evidence": "MATCH (n:Evidence) RETURN count(n) AS cnt",
            "Pigment": "MATCH (n:Pigment) RETURN count(n) AS cnt",
            "Mineral": "MATCH (n:Mineral) RETURN count(n) AS cnt",
            "Color": "MATCH (n:Color) RETURN count(n) AS cnt",
            "Mural": "MATCH (n:Mural) RETURN count(n) AS cnt",
            "Site": "MATCH (n:Site) RETURN count(n) AS cnt",
            "AnalysisMethod": "MATCH (n:AnalysisMethod) RETURN count(n) AS cnt",
        }

        for label, query in stats.items():
            try:
                result = self.run_read(query)
                print(f"- {label}: {result[0]['cnt']}")
            except Exception:
                pass

        print("\n🔗 关系统计")
        result = self.run_read("""
        MATCH ()-[r]->()
        RETURN type(r) AS rel, count(r) AS cnt
        ORDER BY cnt DESC
        """)
        for r in result:
            print(f"- {r['rel']}: {r['cnt']}")

        print("\n✅ 验证查询：")
        print("""
MATCH (ref:Reference)-[:HAS_EVIDENCE]->(ev:Evidence)-[:DESCRIBES]->(p:Pigment)-[:DERIVED_FROM]->(m:Mineral)
RETURN ref.title AS 文献, p.name AS 颜料, m.name AS 矿物, ev.evidence_text AS 证据, ev.page_pdf AS 页码
LIMIT 10;
""")

def parse_args():
    parser = argparse.ArgumentParser(description="导入古代壁画矿物颜料知识图谱")
    parser.add_argument("--csv", default=DEFAULT_CSV_PATH, help="CSV 文件路径")
    parser.add_argument("--uri", default=None, help="Neo4j URI")
    parser.add_argument("--user", default=None, help="Neo4j 用户名")
    parser.add_argument("--password", default=None, help="Neo4j 密码")
    parser.add_argument("--database", default=None, help="数据库名")
    parser.add_argument("--clear", action="store_true", help="导入前清空数据库")
    parser.add_argument("--batch-size", type=int, default=100, help="批量大小")
    return parser.parse_args()

def main():
    load_dotenv()
    args = parse_args()

    csv_path = args.csv
    uri = args.uri or os.getenv("NEO4J_URI") or DEFAULT_URI
    user = args.user or os.getenv("NEO4J_USER") or DEFAULT_USER
    password = args.password or os.getenv("NEO4J_PASSWORD") or DEFAULT_PASSWORD
    database = args.database or os.getenv("NEO4J_DATABASE") or None

    if not os.path.exists(csv_path):
        print(f"❌ 找不到 CSV 文件：{csv_path}")
        sys.exit(1)

    print("=" * 60)
    print("Evidence 节点版知识图谱导入程序")
    print("=" * 60)
    print(f"CSV: {csv_path}")
    print(f"URI: {uri}")
    print(f"USER: {user}")
    print(f"DATABASE: {database or '默认数据库'}")
    print("=" * 60)

    df = read_csv_smart(csv_path)
    df = normalize_dataframe(df)

    if len(df) == 0:
        print("❌ 没有可导入的数据")
        sys.exit(1)

    print(f"✅ 有效记录数：{len(df)}")

    importer = LiteratureImporter(uri, user, password, database)

    try:
        importer.test_connection()

        if args.clear:
            confirm = input("⚠️ 你正在使用 --clear，这会删除全部数据。确认请输入 YES：")
            if confirm.strip() == "YES":
                importer.clear_database()
            else:
                print("已取消清空数据库，继续导入。")

        importer.create_constraints()
        importer.import_dataframe(df, batch_size=args.batch_size)
        importer.print_summary()

    finally:
        importer.close()

if __name__ == "__main__":
    main()