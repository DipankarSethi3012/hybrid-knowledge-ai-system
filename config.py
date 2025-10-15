import os
from dotenv import load_dotenv
load_dotenv()

# Your keys and constants
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# Index configuration
PINECONE_INDEX_NAME = "vietnam-travel-index"
PINECONE_VECTOR_DIM = 1536  # for text-embedding-3-small
