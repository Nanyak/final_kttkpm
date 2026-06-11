"""
All Cypher queries used by the AI service.
"""
from typing import Dict, List, Tuple
from .client import get_driver


# ── Schema bootstrap ─────────────────────────────────────────

def create_constraints(tx):
    tx.run("CREATE CONSTRAINT user_id    IF NOT EXISTS FOR (u:User)    REQUIRE u.user_id    IS UNIQUE")
    tx.run("CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.product_id IS UNIQUE")
    tx.run("CREATE INDEX product_category IF NOT EXISTS FOR (p:Product) ON (p.category)")


# ── Upsert helpers ────────────────────────────────────────────

def upsert_product(tx, product_id: int, name: str, category: str,
                   price: float, description: str):
    tx.run("""
        MERGE (p:Product {product_id: $pid})
        SET p.name        = $name,
            p.category    = $category,
            p.price       = $price,
            p.description = $description
    """, pid=product_id, name=name, category=category,
         price=price, description=description)


def upsert_user(tx, user_id: int):
    tx.run("MERGE (:User {user_id: $uid})", uid=user_id)


ACTION_REL = {
    'view':        'VIEW',
    'click':       'CLICK',
    'add_to_cart': 'ADD_CART',
    'purchase':    'BUY',
}


def record_behavior(tx, user_id: int, product_id: int, action: str):
    rel = ACTION_REL.get(action, 'VIEW')
    tx.run(f"""
        MERGE (u:User    {{user_id:    $uid}})
        MERGE (p:Product {{product_id: $pid}})
        MERGE (u)-[r:{rel}]->(p)
        ON CREATE SET r.count = 1, r.last_seen = datetime()
        ON MATCH  SET r.count = r.count + 1, r.last_seen = datetime()
    """, uid=user_id, pid=product_id)


def create_similar_edge(tx, pid_a: int, pid_b: int, score: float, reason: str = 'same_category'):
    tx.run("""
        MERGE (a:Product {product_id: $pa})
        MERGE (b:Product {product_id: $pb})
        MERGE (a)-[r:SIMILAR]->(b)
        SET r.score = $score, r.reason = $reason
    """, pa=pid_a, pb=pid_b, score=score, reason=reason)


# ── Recommendation queries ────────────────────────────────────

SIMILAR_PRODUCTS_QUERY = """
    MATCH (p:Product {product_id: $pid})-[r:SIMILAR]->(s:Product)
    RETURN s.product_id AS product_id, r.score AS score
    ORDER BY score DESC
    LIMIT $limit
"""

USER_BEHAVIOR_RECS_QUERY = """
    MATCH (u:User {user_id: $uid})-[r]->(p:Product)
    WHERE type(r) IN ['VIEW', 'CLICK', 'ADD_CART', 'BUY']
    WITH p,
         SUM(
           CASE type(r)
             WHEN 'BUY'      THEN 4.0
             WHEN 'ADD_CART' THEN 3.0
             WHEN 'CLICK'    THEN 2.0
             ELSE                 1.0
           END * r.count
         ) AS interaction_score
    ORDER BY interaction_score DESC
    LIMIT 5
    MATCH (p)-[:SIMILAR]->(rec:Product)
    WHERE NOT EXISTS {
        MATCH (u2:User {user_id: $uid})-[:BUY]->(rec)
    }
    RETURN DISTINCT rec.product_id AS product_id,
           MAX(interaction_score)  AS score
    ORDER BY score DESC
    LIMIT $limit
"""

COLLAB_FILTER_QUERY = """
    MATCH (u:User {user_id: $uid})-[:BUY|ADD_CART]->(p:Product)
          <-[:BUY|ADD_CART]-(other:User)
          -[:BUY|ADD_CART]->(rec:Product)
    WHERE NOT EXISTS {
        MATCH (u2:User {user_id: $uid})-[]->(rec)
    }
    RETURN rec.product_id AS product_id,
           COUNT(DISTINCT other) AS score
    ORDER BY score DESC
    LIMIT $limit
"""


def get_similar_products(product_id: int, limit: int = 10) -> List[Tuple[int, float]]:
    with get_driver().session() as session:
        result = session.run(SIMILAR_PRODUCTS_QUERY, pid=product_id, limit=limit)
        return [(r['product_id'], r['score']) for r in result]


def get_user_behavior_recs(user_id: int, limit: int = 10) -> List[Tuple[int, float]]:
    with get_driver().session() as session:
        result = session.run(USER_BEHAVIOR_RECS_QUERY, uid=user_id, limit=limit)
        return [(r['product_id'], float(r['score'])) for r in result]


def get_collab_filter_recs(user_id: int, limit: int = 10) -> List[Tuple[int, float]]:
    with get_driver().session() as session:
        result = session.run(COLLAB_FILTER_QUERY, uid=user_id, limit=limit)
        return [(r['product_id'], float(r['score'])) for r in result]


def combine_graph_scores(user_id: int, limit: int = 10) -> Dict[int, float]:
    """
    Merge behavior-based recs + collaborative filtering into one normalised score dict.
    """
    scores: Dict[int, float] = {}

    behavior_recs = get_user_behavior_recs(user_id, limit * 2)
    collab_recs   = get_collab_filter_recs(user_id, limit * 2)

    for pid, score in behavior_recs:
        scores[pid] = scores.get(pid, 0.0) + score * 0.6

    for pid, score in collab_recs:
        scores[pid] = scores.get(pid, 0.0) + score * 0.4

    # normalise to [0, 1]
    if scores:
        max_s = max(scores.values())
        if max_s > 0:
            scores = {k: v / max_s for k, v in scores.items()}

    return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit])
