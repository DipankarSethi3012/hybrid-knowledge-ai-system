import os
from dotenv import load_dotenv
load_dotenv()

# NEO4J + Neo4j Driver
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

# open AI + Pinecone Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# Index configurationik 
PINECONE_INDEX_NAME = "vietnam-travel-index-1"
PINECONE_VECTOR_DIM = 384   # for 'all-MiniLM-L6-v2' model
# PINECONE_VECTOR_DIM = 1536  # for text-embedding-3-small openai