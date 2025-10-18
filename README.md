# 🌏 Hybrid RAG Travel Assistant

**Hybrid RAG (Retrieval-Augmented Generation) Travel Assistant** is an intelligent travel recommendation system designed to provide accurate, contextual, and personalized responses about destinations.  
It combines **semantic search** (using embeddings) and **graph-based reasoning** (using Neo4j) to deliver enriched, real-time travel information.  

---

## 🧭 Description

This project implements a **Hybrid RAG pipeline** that merges the power of **vector search (Pinecone)** and **knowledge graphs (Neo4j)** with **generative AI (OpenAI / Sentence Transformers)**.  
Users can ask travel-related queries, and the assistant retrieves semantically similar documents from a vector store, enriches them with graph relationships, and generates a context-aware response.

It’s optimized for **travel assistance**, but the architecture is generalizable for any **domain-specific RAG use case**.

---

## ⚙️ Installation

### 1. Clone the repository
```bash
git clone https://github.com/your-username/hybrid-rag-travel-assistant.git
cd hybrid-rag-travel-assistant
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
Create a `.env` file in the root directory and add your API keys:
```
OPENAI_API_KEY=your_openai_api_key
PINECONE_API_KEY=your_pinecone_api_key
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
```

### 5. Run the application
```bash
python hybrid_chat.py
```

---

## 🚀 Usage

Once the assistant is running, you can start chatting directly in your terminal:
```bash
🧭 Your question: What are the top attractions in Hanoi for 2 days?
✅ AI: You can explore the Old Quarter, Hoan Kiem Lake, and the Temple of Literature...
```

The model will:
1. Retrieve semantically relevant results from Pinecone.  
2. Enrich the query using connected data from Neo4j.  
3. Generate a contextual and concise response using OpenAI or Sentence Transformers.

---

## ✨ Features

- **Hybrid Retrieval** — Combines semantic vector search with graph-based reasoning.  
- **Neo4j Knowledge Graph** — Models entity relationships like cities, attractions, cuisines, etc.  
- **Context-Aware Generation** — Uses advanced LLM prompting for precise answers.  
- **Extensible Architecture** — Easy to adapt for other domains beyond travel.  
- **Fast & Efficient** — Uses optimized embedding and retrieval pipelines.




---

## 🧩 Tech Stack

- **Python 3.10+**
- **OpenAI / Sentence Transformers**
- **Pinecone (Vector Database)**
- **Neo4j (Graph Database)**
- **LangChain (for pipeline orchestration)**
- **TQDM, Dotenv, JSON, etc.**

---

## 🤝 Contributing

We welcome contributions!  
To contribute:
1. Fork the repository.  
2. Create a new branch (`feature/your-feature-name`).  
3. Commit your changes and open a pull request.

Please make sure your code follows PEP8 and includes proper documentation.

---

## 💎 Credits

Developed by **Dipankar Sethi** and Team  
Built as part of an advanced RAG research project integrating semantic search and knowledge graphs.  

Special thanks to:
- [Neo4j Aura](https://neo4j.com/cloud/aura/)
- [Pinecone.io](https://www.pinecone.io/)
- [OpenAI](https://platform.openai.com/)
- [Sentence Transformers](https://www.sbert.net/)

---

## 🏆 Achievements

🏅 Demonstrated cutting-edge Hybrid RAG architecture.  
🚀 Achieved top results in semantic and graph-based retrieval fusion.  
🎯 Built a modular, extensible architecture for AI-powered assistants.

---

## 📜 License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.
