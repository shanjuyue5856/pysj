from neo4j import GraphDatabase
from config import Config

class Neo4jClient:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            Config.NEO4J_URI,
            auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD)
        )
        self.database = Config.NEO4J_DATABASE

    def close(self):
        if self.driver:
            self.driver.close()

    def run_query(self, cypher, params=None):
        params = params or {}
        with self.driver.session(database=self.database) as session:
            result = session.run(cypher, params)
            return [record.data() for record in result]

    def get_all_entity_names(self):
        """
        自动从图数据库中拉取实体词典
        """
        queries = {
            "Mural": "MATCH (n:Mural) RETURN DISTINCT n.name AS name",
            "Pigment": "MATCH (n:Pigment) RETURN DISTINCT n.name AS name",
            "Mineral": "MATCH (n:Mineral) RETURN DISTINCT n.name AS name",
            "Color": "MATCH (n:Color) RETURN DISTINCT n.name AS name",
            "Site": "MATCH (n:Site) RETURN DISTINCT n.name AS name",
            "AnalysisMethod": "MATCH (n:AnalysisMethod) RETURN DISTINCT n.name AS name",
            "Reference": "MATCH (n:Reference) RETURN DISTINCT n.title AS name",
            "PigmentType": "MATCH (n:PigmentType) RETURN DISTINCT n.name AS name",
            "MineralSource": "MATCH (n:MineralSource) RETURN DISTINCT n.name AS name",
            "HistoricalPeriod": "MATCH (n:HistoricalPeriod) RETURN DISTINCT n.name AS name",
            "Region": "MATCH (n:Region) RETURN DISTINCT n.name AS name",
            "Element": "MATCH (n:Element) RETURN DISTINCT n.name AS name"
        }

        entity_dict = {}
        for label, cypher in queries.items():
            try:
                rows = self.run_query(cypher)
                entity_dict[label] = [row["name"] for row in rows if row.get("name")]
            except Exception:
                entity_dict[label] = []
        return entity_dict