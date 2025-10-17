# Neo4j Aura Setup Guide for Hybrid Knowledge AI System

## Overview
This document explains how Neo4j Aura is used in the Hybrid Knowledge AI System and provides step‑by‑step instructions to set up, connect, and load data into Neo4j.

---

## Why Neo4j Aura
Neo4j Aura is a fully managed graph database service providing:
- High performance and scalability
- Automatic management and backups
- Easy integration with cloud services
This makes Aura a good fit for storing structured graph data alongside vector stores (Pinecone).

---

## System Role
In the Hybrid Knowledge AI System:
- Nodes represent entities (cities, landmarks, facts).
- Relationships represent connections (located_in, connected_to, famous_for).
Neo4j handles logical/relational reasoning; Pinecone + embeddings handle semantic search.

---

## Create an Aura Instance & Get Credentials
1. Go to https://console.neo4j.io and sign in.
2. Create an AuraDB Free instance (or a paid plan).
3. After provisioning, click **Connect → Python** to see the connection info:
   - URI (starts with `neo4j+s://`)
   - Username (usually `neo4j`)
   - Password (auto-generated)

Save these values to your project `.env` file (example below).

---

## Store Credentials (example .env)
Do NOT commit `.env` to git. Example format:

```text
NEO4J_URI=neo4j+s://<your-instance>.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=<your-password>
NEO4J_DATABASE=neo4j
```

---

## Install Dependencies
Activate your virtual environment and install:
```bash
pip install neo4j tqdm python-dotenv
```

---

## Connect from Python (example)
Use sanitized values from `config.py` or environment:

```python
from neo4j import GraphDatabase
import config

driver = GraphDatabase.driver(
    config.NEO4J_URI,
    auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
)

# Verify connectivity and a simple query
driver.verify_connectivity()
with driver.session(database=config.NEO4J_DATABASE) as session:
    result = session.run("RETURN 1 AS ok")
    print("Connectivity OK" if result.single()["ok"] == 1 else "Connection failed")
driver.close()
```

---

## Loading Data
Run your loader script (example):
```bash
python load_neo4j.py
```
Expected progress:
- Creating constraints...
- Upserting nodes... (progress bar)
- Creating relationships...

---

## Verify Data in Neo4j Browser
Open the Aura Console → Open Browser and run queries:
```cypher
MATCH (n) RETURN n LIMIT 5;
MATCH (a)-[r]->(b) RETURN a, r, b LIMIT 10;
```

---

## Troubleshooting

- Issue: Authentication / Unauthorized  
  Cause: Wrong username/password or misformatted `.env`  
  Fix: Ensure `.env` has no quotes or extra spaces and matches Aura credentials. Restart terminal/IDE.

- Issue: Connection timeout / Cannot reach host  
  Cause: Wrong URI or network restrictions  
  Fix: Use the exact `neo4j+s://...` URI from Aura and ensure network allows outbound TLS.

- Issue: SSL/Handshake errors  
  Cause: Missing `neo4j+s://` prefix or invalid URI  
  Fix: Always use the full TLS-enabled URI from the Aura Connect dialog.

- Issue: Empty results after load  
  Cause: Loader failed or used wrong database  
  Fix: Check loader logs, ensure `NEO4J_DATABASE` is set and the loader uses it.

---

## Summary
1. Create Neo4j Aura instance and copy credentials.  
2. Store credentials in `.env` (do not commit).  
3. Install dependencies and confirm connectivity.  
4. Run `load_neo4j.py` to populate the graph.  
5. Verify in the Neo4j Browser.

---

## Next Steps
After Neo4j is populated, proceed to Hybrid Chat integration — use Neo4j for graph context and Pinecone for semantic retrieval.

---

Author: Dipankar Sethi  
Project: Hybrid Knowledge AI System  
Version: 1.0 — Last updated: October 2025