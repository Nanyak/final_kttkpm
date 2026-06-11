-- Product Service schema (MySQL)
CREATE TABLE categories (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  slug VARCHAR(255) NOT NULL UNIQUE,
  description LONGTEXT NULL,
  parent_id BIGINT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  CONSTRAINT fk_categories_parent FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE SET NULL
);

CREATE TABLE products (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  slug VARCHAR(255) NOT NULL UNIQUE,
  description LONGTEXT NULL,
  base_price DECIMAL(12,2) NOT NULL,
  stock_quantity INT NOT NULL DEFAULT 0,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  image_url VARCHAR(500) NULL,
  category_id BIGINT NOT NULL,
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  CONSTRAINT fk_products_category FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT
);

CREATE TABLE books (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  product_id BIGINT NOT NULL UNIQUE,
  author VARCHAR(255) NOT NULL,
  isbn VARCHAR(20) NOT NULL UNIQUE,
  publisher VARCHAR(255) NOT NULL,
  publication_year INT NOT NULL,
  page_count INT NOT NULL,
  language VARCHAR(50) NOT NULL,
  genre VARCHAR(100) NOT NULL,
  CONSTRAINT fk_books_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE electronics (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  product_id BIGINT NOT NULL UNIQUE,
  brand VARCHAR(100) NOT NULL,
  model_number VARCHAR(100) NOT NULL,
  warranty_period VARCHAR(50) NOT NULL,
  voltage_requirement VARCHAR(50) NOT NULL,
  connectivity VARCHAR(255) NOT NULL,
  technical_specs JSON NOT NULL,
  CONSTRAINT fk_electronics_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE fashion (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  product_id BIGINT NOT NULL UNIQUE,
  brand VARCHAR(100) NOT NULL,
  size VARCHAR(20) NOT NULL,
  color VARCHAR(50) NOT NULL,
  material VARCHAR(100) NOT NULL,
  gender VARCHAR(1) NOT NULL,
  season VARCHAR(50) NOT NULL,
  CONSTRAINT fk_fashion_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);
