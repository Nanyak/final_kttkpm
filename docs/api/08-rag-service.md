# RAG Service API

> Updated to match the current project structure: React frontend, Nginx gateway, Django REST microservices, RabbitMQ events, MySQL/PostgreSQL data stores, Neo4j graph recommendations, and FAISS/OpenAI-backed RAG.


Public chatbot base path: `/api/ai/chatbot/` through `rag_service:8008`.
Internal score base path: `/api/rag/scores/` on `rag_service:8008`.

| Method | Path | Description |
|---|---|---|
| POST | `/api/ai/chatbot/` | Answer product questions using hybrid RAG context. |
| GET | `/api/rag/scores/?query=&top_k=&user_id=` | Internal score endpoint called by AI Service. |

## Chatbot Request

```json
{
  "query": "tai nghe chong on",
  "user_id": 42,
  "history": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ]
}
```

Response fields: `query`, `answer`, `context_used`, and `recommended`. Retrieval uses RRF over dense FAISS semantic hits and sparse TF-IDF lexical hits, then merges that retrieval signal with Neo4j user/product graph scores and product metadata from Product Service.
