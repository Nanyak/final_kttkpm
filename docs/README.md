# E-Commerce Microservices Documentation

This folder documents the current project: a containerized e-commerce platform with a React frontend, Nginx API gateway, Django REST microservices, RabbitMQ event flow, MySQL/PostgreSQL persistence, Redis support, Neo4j graph recommendations, and a separate hybrid RAG service.

## System Modules

| Area | Runtime | Port | Main responsibility | Data store |
|---|---:|---:|---|---|
| Frontend | React + Vite, served by Nginx | via 8000 | Product browsing, cart, checkout, auth, orders, chatbot UI | Browser state |
| API Gateway | Nginx | 8000 | Routes public API and frontend traffic | None |
| Product Service | Django REST | 8001 | Categories, products, polymorphic product details, stock reduction | MySQL `products_db` |
| User Service | Django REST | 8002 | JWT auth, profiles, addresses, admin user lookup | MySQL `users_db` |
| Cart Service | Django REST | 8003 | Active carts and cart items | MySQL `carts_db`, Redis available |
| Order Service | Django REST + worker | 8004 | Order creation from cart, cancellation, payment/shipping status updates | PostgreSQL `orders_db` |
| Payment Service | Django REST | 8005 | Simulated payment gateway, receipts, refunds, VNPay webhook | PostgreSQL `payments_db` |
| Shipping Service | Django REST + worker | 8006 | Shipment creation, tracking, status history, fee calculation | PostgreSQL `shipping_db` |
| AI Service | Django REST | 8007 | Behavior tracking and hybrid product recommendations | MySQL `ai_service_db`, Neo4j |
| RAG Service | Django REST | 8008 | Chatbot and RAG scores using dense FAISS + sparse TF-IDF + Neo4j + optional OpenAI | Retrieval index volume, Neo4j |

## Documentation Map

- [Architecture](01-architecture/system-architecture.md)
- [Class diagrams](02-class-diagrams/)
- [Purchase process flow](03-process-flow/purchase-flow.md)
- [Database schemas](04-database/)
- [Design principles](05-design-principles/principles.md)
- [AI recommendation and RAG](06-ai-recommendation-and-rag.md)
- [API reference](api/README.md)
- [Testing accounts](testing/testing-accounts.md)

## Image Sources

All diagrams in [images](images/) are stored as Mermaid source files (`.mmd`) with generated PNG exports. Update the Mermaid source first, then regenerate PNGs with:

```bash
mmdc -i docs/images/01-system-architecture.mmd -o docs/images/01-system-architecture.png
```
