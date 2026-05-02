from neo4j import GraphDatabase

uri = "bolt://localhost:7687"
username = "neo4j"
password = "du645587"

driver = GraphDatabase.driver(uri, auth=(username, password))

def test_connection():
    with driver.session() as session:
        result = session.run("RETURN 'Neo4j连接成功' AS message")
        for record in result:
            print(record["message"])

if __name__ == "__main__":
    test_connection()
    driver.close()