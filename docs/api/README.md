# API Reference

All public API calls go through Nginx at `http://localhost:8000`. Service ports are also exposed by Docker Compose for direct local debugging.

## Common Response Shapes

Most commerce services return:

```json
{ "status": "success", "data": {} }
```

Errors from those services use:

```json
{ "status": "error", "data": { "message": "..." } }
```

AI and RAG endpoints return direct JSON payloads without the `status/data` wrapper.

## Services

- [Product Service](01-product-service.md)
- [User Service](02-user-service.md)
- [Cart Service](03-cart-service.md)
- [Order Service](04-order-service.md)
- [Payment Service](05-payment-service.md)
- [Shipping Service](06-shipping-service.md)
- [AI Service](07-ai-service.md)
- [RAG Service](08-rag-service.md)

