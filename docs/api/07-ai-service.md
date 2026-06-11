# AI Service API

> Updated to match the current project structure: React frontend, Nginx gateway, Django REST microservices, RabbitMQ events, MySQL/PostgreSQL data stores, Neo4j graph recommendations, and FAISS/OpenAI-backed RAG.


Base path: `/api/ai` through `ai_service:8007`.

| Method | Path | Description |
|---|---|---|
| POST | `/api/ai/track/` | Ingest one behavior event. |
| GET | `/api/ai/recommend/?user_id={id}` | Return hybrid product recommendations. |

## Track Behavior

Request:

```json
{
  "user_id": 42,
  "product_id": 10,
  "action": "view",
  "timestamp": "2026-06-11T10:30:00Z"
}
```

`action` must be one of `view`, `click`, `add_to_cart`, or `purchase`. The service maps these to weights 1.0, 2.0, 3.0, and 4.0.

## Recommend

Query parameters:

| Name | Required | Description |
|---|---|---|
| `user_id` | Yes | User id used for sequence and graph recommendations. |
| `query` | No | Text query for RAG; falls back to recent behavior categories/products. |
| `top_n` | No | Number of results. Default: `TOP_N`. |
| `w1`, `w2`, `w3` | No | Weight overrides for sequence, graph, and RAG signals. |

Response includes `final_score`, `lstm_score`, `graph_score`, `rag_score`, and product metadata.

