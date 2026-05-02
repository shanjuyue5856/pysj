import csv
from pathlib import Path
from neo4j import GraphDatabase

# =========================
# Neo4j 连接配置
# =========================
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "du645587"   # 改成你的密码

# =========================
# CSV 文件路径
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CSV_PATH = BASE_DIR / "data" / "pigment_entity.csv"

class PigmentEntityImporter:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    @staticmethod
    def clean_value(value):
        if value is None:
            return ""
        return str(value).strip()

    @staticmethod
    def split_multi_value(value, sep="/"):
        """
        把 common_regions 这类字段拆分成多个值
        例如：中国北方石窟/中原/西域 -> ["中国北方石窟", "中原", "西域"]
        """
        value = PigmentEntityImporter.clean_value(value)
        if not value:
            return []
        return [v.strip() for v in value.split(sep) if v.strip()]

    @staticmethod
    def split_elements(value):
        """
        main_elements: 'Fe O' -> ['Fe', 'O']
        """
        value = PigmentEntityImporter.clean_value(value)
        if not value:
            return []
        return [v.strip() for v in value.split() if v.strip()]

    def create_constraints(self):
        queries = [
            "CREATE CONSTRAINT pigment_id_unique IF NOT EXISTS FOR (p:Pigment) REQUIRE p.pigment_id IS UNIQUE",
            "CREATE CONSTRAINT pigment_name_unique IF NOT EXISTS FOR (p:Pigment) REQUIRE p.name_zh IS UNIQUE",
            "CREATE CONSTRAINT pigment_type_name_unique IF NOT EXISTS FOR (n:PigmentType) REQUIRE n.name IS UNIQUE",
            "CREATE CONSTRAINT color_name_unique IF NOT EXISTS FOR (n:Color) REQUIRE n.name IS UNIQUE",
            "CREATE CONSTRAINT mineral_source_name_unique IF NOT EXISTS FOR (n:MineralSource) REQUIRE n.name IS UNIQUE",
            "CREATE CONSTRAINT historical_period_name_unique IF NOT EXISTS FOR (n:HistoricalPeriod) REQUIRE n.name IS UNIQUE",
            "CREATE CONSTRAINT region_name_unique IF NOT EXISTS FOR (n:Region) REQUIRE n.name IS UNIQUE",
            "CREATE CONSTRAINT element_name_unique IF NOT EXISTS FOR (n:Element) REQUIRE n.name IS UNIQUE"
        ]
        with self.driver.session() as session:
            for q in queries:
                session.run(q)

    def import_csv(self, csv_path):
        with self.driver.session() as session:
            with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)

                for idx, row in enumerate(reader, start=1):
                    data = {
                        "pigment_id": self.clean_value(row.get("pigment_id")),
                        "name_zh": self.clean_value(row.get("name_zh")),
                        "name_en": self.clean_value(row.get("name_en")),
                        "alias": self.clean_value(row.get("alias")),
                        "chemical_formula": self.clean_value(row.get("chemical_formula")),
                        "pigment_type": self.clean_value(row.get("pigment_type")),
                        "mineral_source": self.clean_value(row.get("mineral_source")),
                        "main_elements": self.clean_value(row.get("main_elements")),
                        "main_elements_list": self.split_elements(row.get("main_elements")),
                        "color": self.clean_value(row.get("color")),
                        "mohs_hardness": self.clean_value(row.get("mohs_hardness")),
                        "refractive_index": self.clean_value(row.get("refractive_index")),
                        "particle_morphology": self.clean_value(row.get("particle_morphology")),
                        "raman_peaks": self.clean_value(row.get("raman_peaks")),
                        "xrd_phases": self.clean_value(row.get("xrd_phases")),
                        "sem_eds_features": self.clean_value(row.get("sem_eds_features")),
                        "historical_period": self.clean_value(row.get("historical_period")),
                        "common_regions": self.clean_value(row.get("common_regions")),
                        "common_regions_list": self.split_multi_value(row.get("common_regions"), sep="/"),
                        "stability_light": self.clean_value(row.get("stability_light")),
                        "stability_humidity": self.clean_value(row.get("stability_humidity")),
                        "stability_acid": self.clean_value(row.get("stability_acid")),
                        "stability_alkali": self.clean_value(row.get("stability_alkali")),
                        "stability_salt": self.clean_value(row.get("stability_salt")),
                        "toxicity": self.clean_value(row.get("toxicity")),
                        "remarks": self.clean_value(row.get("remarks")),
                    }

                    session.execute_write(self._merge_pigment, data)

                    if idx % 50 == 0:
                        print(f"已导入 {idx} 条颜料记录...")

        print("pigment_entity.csv 导入完成。")

    @staticmethod
    def _merge_pigment(tx, data):
        query = """
        // 1. 主颜料节点
        MERGE (p:Pigment {pigment_id: data.pigment_id})
        SET p.name_zh = data.name_zh,
            p.name_en = data.name_en,
            p.alias = data.alias,
            p.chemical_formula = data.chemical_formula,
            p.pigment_type = data.pigment_type,
            p.mineral_source = data.mineral_source,
            p.main_elements = data.main_elements,
            p.color = data.color,
            p.mohs_hardness = data.mohs_hardness,
            p.refractive_index = data.refractive_index,
            p.particle_morphology = data.particle_morphology,
            p.raman_peaks = data.raman_peaks,
            p.xrd_phases = data.xrd_phases,
            p.sem_eds_features = data.sem_eds_features,
            p.historical_period = data.historical_period,
            p.common_regions = data.common_regions,
            p.stability_light = data.stability_light,
            p.stability_humidity = data.stability_humidity,
            p.stability_acid = data.stability_acid,
            p.stability_alkali = data.stability_alkali,
            p.stability_salt = data.stability_salt,
            p.toxicity = data.toxicity,
            p.remarks = data.remarks

        // 2. 颜料类型节点与关系
        FOREACH (_ IN CASE WHEN data.pigment_type <> "" THEN [1] ELSE [] END |
            MERGE (pt:PigmentType {name: data.pigment_type})
            MERGE (p)-[:HAS_TYPE]->(pt)
        )

        // 3. 颜色节点与关系
        FOREACH (_ IN CASE WHEN data.color <> "" THEN [1] ELSE [] END |
            MERGE (c:Color {name: data.color})
            MERGE (p)-[:HAS_COLOR]->(c)
        )

        // 4. 来源节点与关系
        FOREACH (_ IN CASE WHEN data.mineral_source <> "" THEN [1] ELSE [] END |
            MERGE (ms:MineralSource {name: data.mineral_source})
            MERGE (p)-[:HAS_SOURCE]->(ms)
        )

        // 5. 历史时期节点与关系
        FOREACH (_ IN CASE WHEN data.historical_period <> "" THEN [1] ELSE [] END |
            MERGE (hp:HistoricalPeriod {name: data.historical_period})
            MERGE (p)-[:USED_IN_PERIOD]->(hp)
        )

        // 6. 区域节点与关系
        FOREACH (regionName IN data.common_regions_list |
            MERGE (r:Region {name: regionName})
            MERGE (p)-[:COMMON_IN_REGION]->(r)
        )

        // 7. 元素节点与关系
        FOREACH (el IN data.main_elements_list |
            MERGE (e:Element {name: el})
            MERGE (p)-[:HAS_ELEMENT]->(e)
        )
        """
        tx.run(query, data=data)

if __name__ == "__main__":
    print(f"准备导入文件: {CSV_PATH}")

    importer = PigmentEntityImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        print("正在创建约束...")
        importer.create_constraints()

        print("开始导入 pigment_entity.csv ...")
        importer.import_csv(CSV_PATH)

        print("全部完成。")
    finally:
        importer.close()