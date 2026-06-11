# Shipping Service API

> Updated to match the current project structure: React frontend, Nginx gateway, Django REST microservices, RabbitMQ events, MySQL/PostgreSQL data stores, Neo4j graph recommendations, and FAISS/OpenAI-backed RAG.


Base path: `/api` through `shipping_service:8006`.

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/shipping/` | Bearer | List current user's shipments. |
| POST | `/api/shipping/` | Internal token | Create shipment and publish `shipment.created`. |
| GET | `/api/shipping/admin/` | Admin | List all shipments. |
| POST | `/api/shipping/calculate-fee/` | No | Calculate fee by weight, origin, destination, and service type. |
| GET | `/api/shipping/track/{tracking_number}/` | No | Public tracking lookup. |
| GET | `/api/shipping/{id}/` | Owner/admin | Shipment detail. |
| PATCH | `/api/shipping/{id}/status/` | Admin/internal | Update shipment status and create tracking event. |

Supported carriers: `ghn`, `ghtk`, `vnpost`, `jt`. Service types: `standard`, `express`, `same_day`.

