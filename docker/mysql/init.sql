-- MySQL init: create all 3 databases for MySQL-backed services
CREATE DATABASE IF NOT EXISTS products_db   CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS users_db      CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS carts_db      CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS ai_service_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

GRANT ALL PRIVILEGES ON products_db.*   TO 'root'@'%';
GRANT ALL PRIVILEGES ON users_db.*      TO 'root'@'%';
GRANT ALL PRIVILEGES ON carts_db.*      TO 'root'@'%';
GRANT ALL PRIVILEGES ON ai_service_db.* TO 'root'@'%';
FLUSH PRIVILEGES;
