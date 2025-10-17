# hybrid_chat.py (Updated: Sentence-Transformers for embeddings)
import json
from typing import List
# from openai import OpenAI  # Commented out since we use Sentence-Transformers for embeddings
from pinecone import Pinecone, ServerlessSpec
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from neo4j.exceptions import ServiceUnavailable, AuthError
import config

# -----------------------------
# Config
# -----------------------------
EMBED_MODEL = "all-MiniLM-L6-v2"  # Sentence-Transformers model
# CHAT_MODEL = "gpt-4o-mini"
TOP_K = 5

INDEX_NAME = config.PINECONE_INDEX_NAME

# -----------------------------
# Initialize Clients
# -----------------------------
# try:
#     client = OpenAI(api_key=config.OPENAI_API_KEY)
#     print("✅ OpenAI client initialized.")
# except Exception as e:
#     print("❌ Error initializing OpenAI client:", e)
#     raise

try:
    pc = Pinecone(api_key=config.PINECONE_API_KEY)
    print("✅ Pinecone client initialized.")
except Exception as e:
    print("❌ Error initializing Pinecone client:", e)
    raise

# Ensure Pinecone index exists
if INDEX_NAME not in [i.name for i in pc.list_indexes()]:
    print(f"🛠 Creating Pinecone index: {INDEX_NAME}")
    pc.create_index(
        name=INDEX_NAME,
        dimension=config.PINECONE_VECTOR_DIM,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east1-gcp")
    )

index = pc.Index(INDEX_NAME)
print(f"✅ Connected to Pinecone index: {INDEX_NAME}")

# Connect to Neo4j
try:
    driver = GraphDatabase.driver(
        config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )
    with driver.session() as s:
        s.run("RETURN 1")
    print("✅ Connected to Neo4j Aura.")
except AuthError:
    print("❌ Neo4j authentication failed. Check username/password.")
    raise
except ServiceUnavailable:
    print("❌ Neo4j connection failed. Check your URI or network.")
    raise

# -----------------------------
# Load Sentence-Transformer
# -----------------------------
try:
    embed_model = SentenceTransformer(EMBED_MODEL)
    print("✅ Sentence-Transformer model loaded.")
except Exception as e:
    print("❌ Error loading Sentence-Transformer:", e)
    raise

# -----------------------------
# Helper Functions
# -----------------------------
def embed_text(text: str) -> List[float]:
    """Generate embeddings using sentence-transformers."""
    vec = embed_model.encode(text, normalize_embeddings=True)
    return vec.tolist() if hasattr(vec, "tolist") else list(vec)


def pinecone_query(query_text: str, top_k=TOP_K):
    """Query Pinecone for similar items."""
    try:
        vec = embed_text(query_text)
        res = index.query(
            vector=vec,
            top_k=top_k,
            include_metadata=True
        )
        matches = res.matches if hasattr(res, "matches") else res["matches"]
        print(f"DEBUG: Pinecone returned {len(matches)} matches.")
        return matches
    except Exception as e:
        print("❌ Pinecone query failed:", e)
        return []


def fetch_graph_context(node_ids: List[str], neighborhood_depth=1):
    """Fetch neighboring entities from Neo4j."""
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
                print(f"⚠️ Error fetching graph facts for node {nid}: {e}")
    print(f"DEBUG: Retrieved {len(facts)} graph facts.")
    return facts


def build_prompt(user_query, pinecone_matches, graph_facts):
    """Combine semantic and graph info into a single prompt."""
    system_msg = (
        "You are a travel assistant AI. Use the provided search results and "
        "graph data to answer the user's query clearly and helpfully. "
        "Reference node IDs where possible."
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
         "Based on this, answer the query briefly with itinerary tips or recommendations. Mention node IDs where relevant."}
    ]


def call_chat(prompt_messages):
    """Call OpenAI ChatCompletion API (still optional)."""
    # Uncomment if you want OpenAI chat
    # try:
    #     resp = client.chat.completions.create(
    #         model=CHAT_MODEL,
    #         messages=prompt_messages,
    #         max_tokens=600,
    #         temperature=0.3
    #     )
    #     return resp.choices[0].message.content
    # except Exception as e:
    #     print("❌ Chat API error:", e)
    #     return "Sorry, there was an issue generating the answer."
    return "💡 Chat answer feature is disabled. Only embeddings and retrieval are active."


# -----------------------------
# Interactive CLI
# -----------------------------
def interactive_chat():
    print("\n🤖 Hybrid AI Travel Assistant")
    print("Type 'exit' to quit.\n")
    while True:
        query = input("🧭 Your question: ").strip()
        if not query or query.lower() in ("exit", "quit"):
            print("👋 Exiting. Have a great day!")
            break

        matches = pinecone_query(query, top_k=TOP_K)
        match_ids = [getattr(m, "id", m.get("id")) for m in matches]
        graph_facts = fetch_graph_context(match_ids)
        prompt = build_prompt(query, matches, graph_facts)
        answer = call_chat(prompt)

        print("\n=== ✈️ Assistant Answer ===\n")
        print(answer)
        print("\n===========================\n")


if __name__ == "__main__":
    interactive_chat()
