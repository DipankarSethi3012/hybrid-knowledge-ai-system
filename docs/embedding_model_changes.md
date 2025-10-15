# Technical Documentation: Embedding Model Changes

## Overview
This document explains the recent change in the project’s embedding setup:

- **Old embedding model:** OpenAI embeddings (`text-embedding-3-small` / `text-embedding-3-large`)  
- **New embedding model:** Free embedding model (`Sentence-Transformers` / `all-MiniLM-L6-v2`)  

It includes the **changes made**, **why they were made**, and **how to use the new setup**.

---

## 1. Previous Setup (OpenAI Embeddings)

### How it worked:
- Embeddings were generated using OpenAI API.
- Required an API key stored in `.env`.
- Example:
```python
from openai import OpenAI
client = OpenAI(api_key="YOUR_OPENAI_KEY")
embedding = client.embeddings.create(input="Hello world", model="text-embedding-3-small")
```

### Limitations:
- **Costly:** Monthly usage could increase costs depending on dataset size.  
- **API dependency:** Required internet connection and valid OpenAI key.  
- **Limited control:** Could not customize model locally.

---

## 2. New Setup (Free Embedding Model)

### Model Used:
- `all-MiniLM-L6-v2` from [Sentence Transformers](https://www.sbert.net/)  
- Open-source, no API key required.

### How it works:
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embedding = model.encode("Hello world")
```

- Embeddings can be stored locally or in Pinecone for semantic search.
- Example with Pinecone:
```python
import pinecone

pinecone.init(api_key="YOUR_PINECONE_KEY", environment="us-west1-gcp")
index = pinecone.Index("my-index")
index.upsert([("1", embedding.tolist())])
```

---

## 3. Reasons for Change

| Reason | Details |
|--------|---------|
| **Cost Reduction** | Free model eliminates OpenAI API usage cost. |
| **Offline Capability** | Embeddings can now be generated locally without API dependency. |
| **Open-source Control** | Easy to update, customize, and maintain locally. |
| **Lightweight and Fast** | `all-MiniLM-L6-v2` is efficient for small/medium datasets. |

---

## 4. Impact on Project

- Embedding dimension may differ from OpenAI model. Ensure vector DB index matches dimension.  
- Slight change in semantic search accuracy may occur, but overall performance remains good for most use cases.  
- Faster experimentation since no API calls are needed.

---

## 5. How to Use

1. **Install dependencies**
```bash
pip install sentence-transformers
pip install pinecone-client
```

2. **Generate embeddings**
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
texts = ["Hello world", "This is a test sentence"]
embeddings = model.encode(texts)
```

3. **Store in vector DB (optional)**
```python
import pinecone

pinecone.init(api_key="YOUR_PINECONE_KEY", environment="us-west1-gcp")
index = pinecone.Index("my-index")
for i, emb in enumerate(embeddings):
    index.upsert([(str(i), emb.tolist())])
```

4. **Perform similarity search**
```python
query = "Hello"
query_emb = model.encode([query])
results = index.query(query_emb.tolist(), top_k=5)
print(results)
```

---

## 6. Notes & Recommendations

- Always check the embedding dimension compatibility with your vector database.  
- For large datasets, consider batching embedding generation.  
- Free model is ideal for development, POCs, or cost-sensitive projects.  

---

## References

- [Sentence Transformers](https://www.sbert.net/)  
- [Pinecone Vector Database](https://docs.pinecone.io/)  
- OpenAI Embeddings Documentation (for reference)

