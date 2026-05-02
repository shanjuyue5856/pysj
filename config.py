import os

class Config:
    # Flask
    DEBUG = True
    JSON_AS_ASCII = False

    # Neo4j
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "du645587")
    NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

    # QA
    ENTITY_MATCH_THRESHOLD = 80