import csv
from pathlib import Path
from neo4j import GraphDatabase

# =========================
# Neo4j 连接配置
# =========================
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "du645587"   # 改成你的 Neo4j 密码

# =========================
# 项目路径与 CSV 路径
# 假设当前脚本位置：D:/bysj/py/scripts/import_pigment_entity.py
# CSV 文件位置：D:/bysj/py/data/pigment_entity.csv
# =========================
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = PROJECT_ROOT / "data" / "pigment_entity.csv"

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
        处理类似：
        中国北方石窟/中原/西域
        -> ["中国北方石窟", "中原", "西域"]
        """
        value = PigmentEntityImporter.clean_value(value)
        if not value:
            return []
        return [v.strip() for v in value.split(sep) if v.strip()]

    @staticmethod
    def split_elements(value):
        """
        处理 main_elements:
        'Fe O' -> ['Fe', 'O']
        'Cu Al P O H' -> ['Cu', 'Al', 'P', 'O', 'H']
        """
        value = PigmentEntityImporter.clean_value(value)
        if not value:
            return []
        return [v.strip() for v in value.split() if v.strip()]

    def create_constraints(self):
        queries = [
            "CREATE CONSTRAINT pigment_id_unique IF NOT EXISTS FOR (p:Pigment) REQUIRE p.pigment_id IS UNIQUE",
            "CREATE CONSTRAINT pigment_name_zh_unique IF NOT EXISTS FOR (p:Pigment) REQUIRE p.name_zh IS UNIQUE",
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
        print("CSV路径:", csv_path)
        print("CSV是否存在:", csv_path.exists())

        if not csv_path.exists():
            raise FileNotFoundError(f"找不到 CSV 文件: {csv_path}")

        with self.driver.session() as session:
            with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)

                for idx, row in enumerate(reader, start=1):
                    data = {
                        "pigment_id": self.clean_value(row.get("pigment_id")),
                        "name_zh": self.clean_value(row.get("name_zh")),
                        "name_en": self.clean_value(row.get("name_en")),
                        "alias_text": self.clean_value(row.get("alias")),
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

                    try:
                        # 1. 导入 Pigment 主节点及单值关系
                        session.execute_write(self._merge_pigment_basic, data)

                        # 2. 导入元素关系
                        for element_name in data["main_elements_list"]:
                            session.execute_write(
                                self._merge_element_relation,
                                data["pigment_id"],
                                element_name
                            )

                        # 3. 导入区域关系
                        for region_name in data["common_regions_list"]:
                            session.execute_write(
                                self._merge_region_relation,
                                data["pigment_id"],
                                region_name
                            )

                    except Exception as e:
                        print(f"\n第 {idx} 条记录导入失败")
                        print("失败数据：")
                        for k, v in data.items():
                            print(f"  {k}: {v}")
                        raise e

                    if idx % 20 == 0:
                        print(f"已导入 {idx} 条颜料记录...")

        print("pigment_entity.csv 导入完成。")

    @staticmethod
    def _merge_pigment_basic(tx, data):
        query = """
        MERGE (p:Pigment {pigment_id: $pigment_id})
        SET p.name_zh = $name_zh,
            p.name_en = $name_en,
            p.alias_text = $alias_text,
            p.chemical_formula = $chemical_formula,
            p.pigment_type = $pigment_type,
            p.mineral_source = $mineral_source,
            p.main_elements = $main_elements,
            p.color = $color,
            p.mohs_hardness = $mohs_hardness,
            p.refractive_index = $refractive_index,
            p.particle_morphology = $particle_morphology,
            p.raman_peaks = $raman_peaks,
            p.xrd_phases = $xrd_phases,
            p.sem_eds_features = $sem_eds_features,
            p.historical_period = $historical_period,
            p.common_regions = $common_regions,
            p.stability_light = $stability_light,
            p.stability_humidity = $stability_humidity,
            p.stability_acid = $stability_acid,
            p.stability_alkali = $stability_alkali,
            p.stability_salt = $stability_salt,
            p.toxicity = $toxicity,
            p.remarks = $remarks

        FOREACH (_ IN CASE WHEN $pigment_type <> "" THEN [1] ELSE [] END |
            MERGE (pt:PigmentType {name: $pigment_type})
            MERGE (p)-[:HAS_TYPE]->(pt)
        )

        FOREACH (_ IN CASE WHEN $color <> "" THEN [1] ELSE [] END |
            MERGE (c:Color {name: $color})
            MERGE (p)-[:HAS_COLOR]->(c)
        )

        FOREACH (_ IN CASE WHEN $mineral_source <> "" THEN [1] ELSE [] END |
            MERGE (ms:MineralSource {name: $mineral_source})
            MERGE (p)-[:HAS_SOURCE]->(ms)
        )

        FOREACH (_ IN CASE WHEN $historical_period <> "" THEN [1] ELSE [] END |
            MERGE (hp:HistoricalPeriod {name: $historical_period})
            MERGE (p)-[:USED_IN_PERIOD]->(hp)
        )
        """
        tx.run(query, **data)

    @staticmethod
    def _merge_element_relation(tx, pigment_id, element_name):
        query = """
        MATCH (p:Pigment {pigment_id: $pigment_id})
        MERGE (e:Element {name: $element_name})
        MERGE (p)-[:HAS_ELEMENT]->(e)
        """
        tx.run(query, pigment_id=pigment_id, element_name=element_name)

    @staticmethod
    def _merge_region_relation(tx, pigment_id, region_name):
        query = """
        MATCH (p:Pigment {pigment_id: $pigment_id})
        MERGE (r:Region {name: $region_name})
        MERGE (p)-[:COMMON_IN_REGION]->(r)
        """
        tx.run(query, pigment_id=pigment_id, region_name=region_name)

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