import json
from typing import List
from pinecone import Pinecone, ServerlessSpec
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import config
from query_cache import run_query, lc  # Modular cache import
from logs.logger import LoggerCacheSingleton  # Logger + Cache singleton

# -----------------------------
# Config
# -----------------------------
EMBED_MODEL = "all-MiniLM-L6-v2"
CHAT_MODEL = "gpt-3.5-turbo"
TOP_K = 5
INDEX_NAME = config.PINECONE_INDEX_NAME

# -----------------------------
# Load Models & Clients
# -----------------------------
try:
    embed_model = SentenceTransformer(EMBED_MODEL)
    lc.info(f"Loaded embedding model: {EMBED_MODEL}")
except Exception as e:
    lc.error(f"Error loading Sentence-Transformer: {e}")
    raise

try:
    pc = Pinecone(api_key=config.PINECONE_API_KEY)
    lc.info("Pinecone client initialized.")
except Exception as e:
    lc.error(f"Error initializing Pinecone client: {e}")
    raise

if INDEX_NAME not in [i.name for i in pc.list_indexes()]:
    lc.info(f"Creating Pinecone index: {INDEX_NAME}")
    pc.create_index(
        name=INDEX_NAME,
        dimension=config.PINECONE_VECTOR_DIM,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )

index = pc.Index(INDEX_NAME)
lc.info(f"Connected to Pinecone index: {INDEX_NAME}")

try:
    driver = GraphDatabase.driver(
        config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )
    with driver.session() as s:
        s.run("RETURN 1")
    lc.info("Connected to Neo4j Aura.")
except AuthError:
    lc.error("Neo4j authentication failed. Check username/password.")
    raise
except ServiceUnavailable:
    lc.error("Neo4j connection failed. Check your URI or network.")
    raise

try:
    openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
    lc.info("OpenAI client initialized.")
except Exception as e:
    lc.error(f"Error initializing OpenAI client: {e}")
    openai_client = None

# -----------------------------
# Helper Functions
# -----------------------------
def embed_text(text: str) -> List[float]:
    vec = embed_model.encode(text, normalize_embeddings=True)
    return vec.tolist() if hasattr(vec, "tolist") else list(vec)

def pinecone_query(query_text: str, top_k=TOP_K):
    try:
        vec = embed_text(query_text)
        res = index.query(
            vector=vec,
            top_k=top_k,
            include_metadata=True
        )
        matches = res.matches if hasattr(res, "matches") else res["matches"]
        lc.info(f"Pinecone returned {len(matches)} matches.")
        return matches
    except Exception as e:
        lc.error(f"Pinecone query failed: {e}")
        return []

def fetch_graph_context(node_ids: List[str], neighborhood_depth=1):
    facts = []
    with driver.session() as session:
        for nid in node_ids:
            try:
                q = (
                    "MATCH (n:Entity {id:$nid})-[r]-(m:Entity) "
                    "RETURN type(r) AS rel, labels(m) AS labels, m.id AS id, "
                    "m.name AS name, m.type AS type, m.description AS description "
                    "LIMIT 10"
                )
                recs = session.run(q, nid=nid)
                for r in recs:
                    facts.append({
                        "source": nid,
                        "rel": r["rel"],
                        "target_id": r["id"],
                        "target_name": r["name"],
                        "target_desc": (r["description"] or "")[:400],
                        "labels": r["labels"]
                    })
            except Exception as e:
                lc.error(f"Error fetching graph facts for node {nid}: {e}")
    lc.info(f"Retrieved {len(facts)} graph facts.")
    return facts

def build_prompt(user_query, pinecone_matches, graph_facts):
    system_msg = (
        "You are a highly knowledgeable and professional AI Travel Assistant. "
        "Provide accurate, structured travel advice using ONLY the provided data.\n"
        "Reference node IDs where possible. Keep tone professional, friendly, helpful."
    )

    vec_context = []
    for m in pinecone_matches:
        meta = m.metadata if hasattr(m, "metadata") else m["metadata"]
        score = getattr(m, "score", m.get("score", None))
        snippet = f"- id: {getattr(m, 'id', m.get('id'))}, name: {meta.get('name','')}, type: {meta.get('type','')}, score: {score}"
        if meta.get("city"):
            snippet += f", city: {meta['city']}"
        vec_context.append(snippet)

    graph_context = [
        f"- ({f['source']}) -[{f['rel']}]-> ({f['target_id']}) {f['target_name']}: {f['target_desc']}"
        for f in graph_facts
    ]

    return [
        {"role": "system", "content": system_msg},
        {"role": "user", "content":
         f"User query: {user_query}\n\n"
         "Top vector matches:\n" + "\n".join(vec_context[:10]) + "\n\n"
         "Graph facts:\n" + "\n".join(graph_context[:20]) + "\n\n"
         "Based on this, answer briefly with itinerary tips or recommendations. Mention node IDs where relevant."}
    ]

def call_chat(prompt_messages):
    if openai_client is None:
        lc.error("OpenAI client not initialized.")
        return "OpenAI client not initialized."
    try:
        resp = openai_client.chat.completions.create(
            model=CHAT_MODEL,
            messages=prompt_messages,
            max_tokens=600,
            temperature=0.3
        )
        return resp.choices[0].message.content
    except Exception as e:
        lc.error(f"Chat API error: {e}")
        return "Sorry, there was an issue generating the answer."

# -----------------------------
# Interactive CLI
# -----------------------------
def interactive_chat():
    lc.info("Hybrid AI Travel Assistant started.")
    print("\nHybrid AI Travel Assistant")
    print("Type 'exit' to quit.\n")

    while True:
        query = input("Your question: ").strip()
        if not query or query.lower() in ("exit", "quit"):
            lc.info("Exiting. Have a great day!")
            print("Exiting. Have a great day!")
            break

        # ----- Check cache first -----
        cached_answer = lc.get_persistent_query(query)
        if cached_answer is not None:
            print("\n=== Assistant Answer (from cache) ===\n")
            print(cached_answer)
            print("\n===========================\n")
            lc.info(f"User question (cache hit): {query}\nAssistant answer: {cached_answer}")
            continue

        # ----- Run query pipeline -----
        matches = pinecone_query(query, top_k=TOP_K)
        match_ids = [getattr(m, "id", m.get("id")) for m in matches]
        graph_facts = fetch_graph_context(match_ids)
        prompt = build_prompt(query, matches, graph_facts)
        answer = call_chat(prompt)

        # ----- Store answer in cache -----
        lc.put_persistent_query(query, answer)

        # ----- Show answer -----
        print("\n=== Assistant Answer ===\n")
        print(answer)
        print("\n===========================\n")
        lc.info(f"User question: {query}\nAssistant answer: {answer}")

if __name__ == "__main__":
    interactive_chat()
