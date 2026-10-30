-- Table schema for `sanction_orders`
-- Auto-created if not exists at runtime

CREATE TABLE IF NOT EXISTS `sanction_orders` (
  `id` int NOT NULL AUTO_INCREMENT,
  `grant_id` int NOT NULL,
  `so_number` varchar(100) NOT NULL,
  `so_amount` decimal(15,2) NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `financial_year` varchar(9) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `grant_id` (`grant_id`),
  CONSTRAINT `sanction_orders_ibfk_1` FOREIGN KEY (`grant_id`) REFERENCES `grants` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
