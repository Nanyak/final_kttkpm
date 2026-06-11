# Order Service API

> Updated to match the current project structure: React frontend, Nginx gateway, Django REST microservices, RabbitMQ events, MySQL/PostgreSQL data stores, Neo4j graph recommendations, and FAISS/OpenAI-backed RAG.


Base path: `/api` through `order_service:8004`.

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/orders/` | Bearer | List current user's orders. |
| POST | `/api/orders/` | Bearer | Create order from active cart. |
| GET | `/api/orders/{id}/` | Owner/admin | Get order detail. |
| POST | `/api/orders/{id}/cancel/` | Owner | Cancel order unless already shipped, delivered, or cancelled. |
| PATCH | `/api/orders/{id}/status/` | Internal token | Update `status` and/or `payment_status`. |
| GET | `/api/orders/admin/` | Admin | List all orders. |

Create body: `shipping_address`, `payment_method`, optional `notes`, `shipping_fee`, and `discount_amount`.

Order creation fetches the active cart, copies items, reduces product stock, marks the cart converted, and publishes `order.created`.

