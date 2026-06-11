# Product Service API

> Updated to match the current project structure: React frontend, Nginx gateway, Django REST microservices, RabbitMQ events, MySQL/PostgreSQL data stores, Neo4j graph recommendations, and FAISS/OpenAI-backed RAG.


Base path: `/api` through `product_service:8001`.

| Method | Path | Description |
|---|---|---|
| GET | `/api/categories/` | List categories. Query: `is_active`, `parent_id`. |
| POST | `/api/categories/` | Create category. |
| GET | `/api/categories/{id}/` | Get category detail. |
| PATCH | `/api/categories/{id}/` | Update category. |
| DELETE | `/api/categories/{id}/` | Delete category. |
| GET | `/api/products/` | List products. Query: `category_id`, `is_active`, `search`, `ids=1,2,3`. |
| POST | `/api/products/` | Create product with optional `book`, `electronics`, or `fashion` object. |
| GET | `/api/products/{id}/` | Get product detail. |
| PATCH | `/api/products/{id}/` | Update product and subtype details. |
| DELETE | `/api/products/{id}/` | Delete product. |
| PATCH | `/api/products/{id}/reduce-stock/` | Internal stock decrement. Body: `{"quantity": 2}`. |

Product fields include `name`, `description`, `base_price`, `stock_quantity`, `is_active`, `image_url`, `category`, `category_name`, `product_type`, and subtype payloads.

