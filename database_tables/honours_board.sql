-- Table schema for `honours_board`
-- Auto-created if not exists at runtime

CREATE TABLE IF NOT EXISTS `honours_board` (
  `id` int NOT NULL AUTO_INCREMENT,
  `army_number` varchar(50) NOT NULL,
  `medal_icon` varchar(255) DEFAULT NULL,
  `comments` text,
  `commendation` text,
  `appreciation_type` enum('Leadership','Bravery','Discipline','Innovation','Service','Teamwork','Excellence') NOT NULL,
  `appreciation_date` date NOT NULL,
  `image` varchar(45) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_hb_army_number` (`army_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
