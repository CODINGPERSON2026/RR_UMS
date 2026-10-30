-- Table schema for `dues_in`
-- Auto-created if not exists at runtime

CREATE TABLE IF NOT EXISTS `dues_in` (
  `id` int NOT NULL AUTO_INCREMENT,
  `army_number` varchar(50) NOT NULL,
  `rank` varchar(20) DEFAULT NULL,
  `trade` varchar(50) DEFAULT NULL,
  `name` varchar(100) DEFAULT NULL,
  `unit` varchar(100) DEFAULT NULL,
  `posting_order_no` varchar(100) DEFAULT NULL,
  `date_of_move` date DEFAULT NULL,
  `dor` varchar(100) DEFAULT NULL,
  `remarks` varchar(255) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
