# 🇻🇳 Hybrid RAG Travel Assistant Documentation

This document provides a professional, detailed overview of the Hybrid RAG (Retrieval-Augmented Generation) Travel Assistant project. The system leverages **Neo4j** (Knowledge Graph) and **Pinecone** (Vector Database) to provide accurate, context-rich travel advice for Vietnam, powered by a **Sentence-Transformers** embedding model and **OpenAI's GPT** for generation.

---

## 1. Project Overview and Technology Stack

The project implements a **Dual-Retriever RAG Architecture** to combine the strengths of structural, relational data with semantic similarity.

| Component | Technology/Library | Role in Project |
| :--- | :--- | :--- |
| **Knowledge Graph** | **Neo4j**, `neo4j` Python Driver | Stores structured entities and relationships for factual, multi-hop context retrieval. |
| **Vector Database** | **Pinecone**, `pinecone` Python Client | Stores vector embeddings of semantic text for fast, relevant, similarity-based retrieval. |
| **Embedding Model** | **Sentence-Transformers** (`all-MiniLM-L6-v2`) | Generates high-quality dense vectors (384 dimensions) for semantic search in Pinecone. |
| **Generative AI** | **OpenAI** (`gpt-3.5-turbo`), `openai` Python Client | Reasons over the retrieved hybrid context to formulate the final, structured answer. |
| **Caching/Logging** | **Custom Singleton** (`LoggerCacheSingleton`) | Manages centralized logging and implements in-memory (LRU) and persistent (disk) query caching. |
| **Data Source** | `vietnam_travel_dataset.json` | JSON dataset containing travel entities, descriptions, and connections. |

---

## 2. Architecture Overview and Data Flow

The architecture is designed to first prioritize speed via caching, then utilize the two distinct retrieval mechanisms to gather the most comprehensive context for the LLM.

### Architecture Diagram (Conceptual)


### Data Flow

1.  **User Query Input**: The user submits a question via the interactive CLI in `hybrid_chat.py`.
2.  **Cache Check**: The query is checked against the **Persistent Query Cache** (`logger.py`).
    * **Hit**: Return cached answer immediately.
    * **Miss**: Proceed to dual-retrieval.
3.  **Vector Retrieval (Pinecone)**: The query is embedded using `all-MiniLM-L6-v2` and used to query Pinecone for the **Top-K** semantically similar nodes.
4.  **Graph Retrieval (Neo4j)**: The IDs from the Pinecone matches are used in `fetch_graph_context` to query Neo4j for the **1-hop neighborhood** (related entities and their relationship types), providing crucial structural context.
5.  **Prompt Assembly**: The vector matches (with score/metadata) and graph facts (as triples) are structured into a detailed prompt message in `build_prompt`.
6.  **Generation (OpenAI)**: The prompt is sent to `gpt-3.5-turbo` to generate a final, grounded answer.
7.  **Final Answer**: The result is stored in the **Persistent Query Cache** and displayed to the user.

---

## 3. Design Decisions

| Decision | Rationale |
| :--- | :--- |
| **Hybrid RAG (Vector + Graph)** | Provides the best of both worlds: Pinecone handles semantic search (e.g., "Tell me about history"), while Neo4j ensures **factual, relational integrity** (e.g., "Which *city* is this *hotel in*?"). |
| **Free/Local Embedding Model** | The `SentenceTransformer('all-MiniLM-L6-v2')` model was chosen for **cost-efficiency** and easy local deployment, avoiding recurring costs associated with paid API embedding services. |
| **Singleton Cache/Logger** | The `LoggerCacheSingleton` centralizes both logging and caching logic. This simplifies code by providing a single, globally managed utility (`lc`) for thread-safe state management. |
| **Idempotent Data Loading** | `load_neo4j.py` uses `MERGE` with an `id` constraint to ensure the script can be run repeatedly without creating duplicate nodes, guaranteeing data integrity. |
| **Serverless Pinecone Spec** | The index is created with `ServerlessSpec(cloud="aws", region="us-east-1")`, the correct configuration for the free plan, ensuring high availability and managed infrastructure. |

---

## 4. Feature Breakdown

### Data Loading (`pinecone_upload.py`, `load_neo4j.py`)

* **Neo4j Schema**: Nodes are labeled with their `type` (e.g., `:Hotel`) and a generic `:Entity` label. A uniqueness constraint is applied to the `id` property on `:Entity` nodes.
* **Vector Content**: The semantic text is extracted from the `description` or `semantic_text` field of the JSON dataset, truncated to 1000 characters for manageable embedding size.
* **Relationship Sanitization**: Relationships are sanitized to be uppercase and use underscores (e.g., `RELATED TO` becomes `RELATED_TO`) to ensure valid Cypher syntax.

### Hybrid Chat Core (`hybrid_chat.py`)

* **Retrieval Orchestration**: The `interactive_chat` loop handles the sequential flow: Cache $\rightarrow$ Pinecone $\rightarrow$ Neo4j $\rightarrow$ LLM.
* **Prompt Construction**: `build_prompt` is critical, structuring the input data into distinct sections for the LLM: **Vector Matches** (with IDs and scores) and **Graph Facts** (as readable Cypher-like triples).
* **Graph Fact Limiting**: `fetch_graph_context` explicitly limits the relationship retrieval to **10 facts per matched node** to prevent excessive context window usage and slow query times.

### Caching and Logging (`logger.py`, `query_cache.py`)

* **Dual Cache Mechanism**:
    * **In-Memory**: An `OrderedDict` is used for **LRU eviction**, providing the fastest access for frequently used or recent queries.
    * **Persistent**: Disk caching uses `hashlib.md5` on the query string to create a unique pickle file path (`cache/queries/`). This preserves complex query results across sessions.
* **Thread Safety**: A `threading.RLock` is used to protect the shared in-memory cache and statistics in the `LoggerCacheSingleton`.

---

## 5. Code Structure and Dependencies

### Folder Layout
```
project/
├── cache/
│ └── queries/ # Persistent query cache files (.pkl)
├── logs/
│ └── app.log # Application log file
├── config.py # Configuration and API keys
├── hybrid_chat.py # Core application and RAG pipeline
├── load_neo4j.py # Script for populating Neo4j
├── logger.py # Logger and Caching Singleton class
├── pinecone_upload.py # Script for populating Pinecone
├── query_cache.py # Cache access wrapper
└── vietnam_travel_dataset.json # Source data
```

### Key Python Dependencies

* `pinecone-client`
* `neo4j`
* `openai`
* `sentence-transformers`
* `python-dotenv`
* `tqdm` (for loading scripts)

---

## 6. Performance and Limitations

### Performance Considerations

* **Latency Reduction**: The Caching mechanism is the most significant latency reduction technique, effectively bypassing the entire RAG pipeline for cached queries.
* **Query Optimization**: Neo4j queries are constrained by depth (1-hop) and limit the number of returned facts (10 per node) to ensure fast graph traversal.
* **Vector Dimension**: The use of a 384-dimensional vector from `all-MiniLM-L6-v2` is a trade-off for faster vector lookups and smaller memory footprint compared to larger models.

### Limitations and Trade-offs

| Limitation/Trade-off | Area for Improvement |
| :--- | :--- |
| **Fixed Graph Depth (1-hop)** | Complex, multi-hop queries (e.g., "Find a hotel near an attraction near a city center") will lack full context. |
| **Embedding Quality** | `all-MiniLM-L6-v2` may have lower semantic accuracy than cutting-edge proprietary models. |
| **Hardcoded Index Region** | Index creation is hardcoded to `us-east-1` to match the free-tier requirements, limiting regional flexibility. |
| **System Integrity Checks** | The system currently halts on initialization errors (e.g., Neo4j `AuthError` or `ServiceUnavailable`). | Implement a robust retry mechanism (e.g., using `tenacity`) for transient external service errors. |