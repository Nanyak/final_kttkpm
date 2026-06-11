# Cart Service API

> Updated to match the current project structure: React frontend, Nginx gateway, Django REST microservices, RabbitMQ events, MySQL/PostgreSQL data stores, Neo4j graph recommendations, and FAISS/OpenAI-backed RAG.


Base path: `/api` through `cart_service:8003`.

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/carts/me/` | Bearer | Get or create the active cart for the current user. |
| DELETE | `/api/carts/me/` | Bearer | Clear active cart items. |
| POST | `/api/carts/me/items/` | Bearer | Add item. Body: `product_id`, optional `quantity`. |
| PATCH | `/api/carts/me/items/{id}/` | Bearer | Update quantity; quantity <= 0 deletes the item. |
| DELETE | `/api/carts/me/items/{id}/` | Bearer | Delete item. |
| GET | `/api/carts/{id}/` | Bearer/internal | Read cart by id. |
| PATCH | `/api/carts/{id}/` | Internal token | Update cart `status` to `active`, `converted`, or `abandoned`. |

Adding an item calls Product Service and stores product name and price snapshots on the cart item.

