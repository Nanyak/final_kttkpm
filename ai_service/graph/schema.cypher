// ═══════════════════════════════════════════════════════════
//  Knowledge Graph Schema — E-Commerce AI Service
// ═══════════════════════════════════════════════════════════

// ── Constraints (uniqueness + implicit index) ───────────────
CREATE CONSTRAINT user_id    IF NOT EXISTS FOR (u:User)    REQUIRE u.user_id    IS UNIQUE;
CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.product_id IS UNIQUE;

// ── Node indexes ────────────────────────────────────────────
CREATE INDEX product_category IF NOT EXISTS FOR (p:Product) ON (p.category);
CREATE INDEX product_name     IF NOT EXISTS FOR (p:Product) ON (p.name);

// ═══════════════════════════════════════════════════════════
//  Node definitions (documented)
// ═══════════════════════════════════════════════════════════

// User node
// MERGE (:User {user_id: <int>})

// Product node
// MERGE (:Product {
//   product_id:  <int>,
//   name:        <string>,
//   category:    <string>,
//   price:       <float>,
//   description: <string>
// })

// ═══════════════════════════════════════════════════════════
//  Relationship definitions
// ═══════════════════════════════════════════════════════════

// (:User)-[:VIEW    {count: int, last_seen: datetime}]->(:Product)
// (:User)-[:CLICK   {count: int, last_seen: datetime}]->(:Product)
// (:User)-[:ADD_CART{count: int, last_seen: datetime}]->(:Product)
// (:User)-[:BUY     {count: int, last_seen: datetime}]->(:Product)
// (:Product)-[:SIMILAR {score: float, reason: string}]->(:Product)
