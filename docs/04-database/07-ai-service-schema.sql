-- AI Service schema (MySQL)
CREATE TABLE ai_products (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  product_id INT NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  description LONGTEXT NOT NULL,
  category VARCHAR(100) NOT NULL,
  price DOUBLE NOT NULL DEFAULT 0,
  encoded_id INT NULL
);

CREATE TABLE ai_user_behavior (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  product_id INT NOT NULL,
  action VARCHAR(20) NOT NULL,
  timestamp DATETIME(6) NOT NULL,
  weight DOUBLE NOT NULL DEFAULT 1,
  INDEX idx_ai_behavior_user_timestamp (user_id, timestamp),
  CONSTRAINT fk_ai_behavior_product FOREIGN KEY (product_id) REFERENCES ai_products(product_id) ON DELETE CASCADE
);

-- Neo4j complements these tables with User, Product, INTERACTED_WITH, and SIMILAR graph relationships.
-- RAG Service has no relational database; it uses FAISS files and product metadata fetched from Product Service.
