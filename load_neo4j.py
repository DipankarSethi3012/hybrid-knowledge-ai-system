# load_to_neo4j.py (Updated Version)
import json
from neo4j import GraphDatabase
from tqdm import tqdm
import config

DATA_FILE = "vietnam_travel_dataset.json"

driver = GraphDatabase.driver(config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASSWORD))

def create_constraints(tx):
    """
    Generic uniqueness constraint on id for Entity nodes.
    You can add type-specific constraints here if needed.
    """
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE")

def upsert_node(tx, node):
    """
    Upsert a node into Neo4j.
    Adds both type label and Entity label.
    Skips nested 'connections' key.
    """
    labels = [node.get("type", "Unknown"), "Entity"]
    label_cypher = ":" + ":".join(labels)

    # Keep only simple properties (avoid storing nested objects)
    props = {k: v for k, v in node.items() if k not in ("connections",)}

    tx.run(
        f"MERGE (n{label_cypher} {{id: $id}}) "
        "SET n += $props",
        id=node["id"], props=props
    )

def create_relationship(tx, source_id, rel):
    """
    Create a relationship between source node and target node.
    Sanitize relationship type to avoid errors.
    """
    rel_type = rel.get("relation", "RELATED_TO")
    if not rel_type:
        rel_type = "RELATED_TO"

    # Make it safe: uppercase and replace spaces
    rel_type = rel_type.strip().replace(" ", "_").upper()

    target_id = rel.get("target")
    if not target_id:
        return

    cypher = (
        "MATCH (a:Entity {id: $source_id}), (b:Entity {id: $target_id}) "
        f"MERGE (a)-[r:{rel_type}]->(b) "
        "RETURN r"
    )
    tx.run(cypher, source_id=source_id, target_id=target_id)

def main():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            nodes = json.load(f)
    except Exception as e:
        print("Error reading JSON file:", e)
        return

    with driver.session() as session:
        print("Creating constraints...")
        session.execute_write(create_constraints)

        print("Upserting nodes...")
        for node in tqdm(nodes, desc="Creating nodes"):
            try:
                session.execute_write(upsert_node, node)
            except Exception as e:
                print(f"Error upserting node {node.get('id')}: {e}")

        print("Creating relationships...")
        for node in tqdm(nodes, desc="Creating relationships"):
            conns = node.get("connections", [])
            for rel in conns:
                try:
                    session.execute_write(create_relationship, node["id"], rel)
                except Exception as e:
                    print(f"Error creating relationship for node {node.get('id')}: {e}")

    print("Done loading into Neo4j.")
    driver.close()

if __name__ == "__main__":
    main()
