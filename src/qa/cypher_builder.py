class CypherBuilder:
    def build(self, question_type, entity):
        if question_type == "mural_site":
            cypher = """
            MATCH (m:Mural {name:$name})-[:LOCATED_IN]->(s:Site)
            RETURN DISTINCT s.name AS answer
            """
            return cypher, {"name": entity}

        elif question_type == "mural_pigments":
            cypher = """
            MATCH (m:Mural {name:$name})-[:USES_PIGMENT]->(p:Pigment)
            RETURN DISTINCT p.name AS answer
            """
            return cypher, {"name": entity}

        elif question_type == "mural_methods":
            cypher = """
            MATCH (m:Mural {name:$name})-[:ANALYZED_BY]->(a:AnalysisMethod)
            RETURN DISTINCT a.name AS answer
            """
            return cypher, {"name": entity}

        elif question_type == "pigment_color":
            cypher = """
            MATCH (p:Pigment {name:$name})-[:HAS_COLOR]->(c:Color)
            RETURN DISTINCT c.name AS answer
            """
            return cypher, {"name": entity}

        elif question_type == "pigment_mineral":
            cypher = """
            MATCH (p:Pigment {name:$name})-[:DERIVED_FROM]->(m:Mineral)
            RETURN DISTINCT m.name AS answer
            """
            return cypher, {"name": entity}

        elif question_type == "pigment_type":
            cypher = """
            MATCH (p:Pigment {name:$name})-[:HAS_TYPE]->(t:PigmentType)
            RETURN DISTINCT t.name AS answer
            """
            return cypher, {"name": entity}

        elif question_type == "pigment_methods":
            cypher = """
            MATCH (p:Pigment {name:$name})-[:IDENTIFIED_BY]->(a:AnalysisMethod)
            RETURN DISTINCT a.name AS answer
            """
            return cypher, {"name": entity}

        elif question_type == "pigment_reference":
            cypher = """
            MATCH (r:Reference)-[:HAS_EVIDENCE]->(e:Evidence)-[:DESCRIBES]->(p:Pigment {name:$name})
            RETURN DISTINCT r.title AS title, r.year AS year, e.evidence_text AS evidence
            """
            return cypher, {"name": entity}

        elif question_type == "mineral_elements":
            cypher = """
            MATCH (m:Mineral {name:$name})-[:HAS_ELEMENT]->(e:Element)
            RETURN DISTINCT e.name AS answer
            """
            return cypher, {"name": entity}

        elif question_type == "mineral_pigments":
            cypher = """
            MATCH (p:Pigment)-[:DERIVED_FROM]->(m:Mineral {name:$name})
            RETURN DISTINCT p.name AS answer
            """
            return cypher, {"name": entity}

        elif question_type == "mineral_methods":
            cypher = """
            MATCH (p:Pigment)-[:DERIVED_FROM]->(m:Mineral {name:$name})
            MATCH (p)-[:IDENTIFIED_BY]->(a:AnalysisMethod)
            RETURN DISTINCT a.name AS answer
            """
            return cypher, {"name": entity}

        elif question_type == "site_pigments":
            cypher = """
            MATCH (m:Mural)-[:LOCATED_IN]->(s:Site {name:$name})
            MATCH (m)-[:USES_PIGMENT]->(p:Pigment)
            RETURN DISTINCT p.name AS answer
            """
            return cypher, {"name": entity}

        elif question_type == "element_murals":
            cypher = """
            MATCH (mu:Mural)-[:USES_PIGMENT]->(p:Pigment)-[:DERIVED_FROM]->(mi:Mineral)-[:HAS_ELEMENT]->(e:Element {name:$name})
            RETURN DISTINCT mu.name AS answer
            """
            return cypher, {"name": entity}

        return None, None