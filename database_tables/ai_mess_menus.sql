-- Table schema for `ai_mess_menus`
-- Auto-created if not exists at runtime

CREATE TABLE IF NOT EXISTS `ai_mess_menus` (
  `id` int NOT NULL AUTO_INCREMENT,
  `mess_type` varchar(20) NOT NULL COMMENT 'OR or JCO',
  `day_of_week` varchar(20) NOT NULL COMMENT 'Monday to Sunday',
  `meal_type` varchar(20) NOT NULL COMMENT 'Breakfast, Tea, Lunch, Dinner',
  `food_item` varchar(150) NOT NULL,
  `default_serving_unit` varchar(50) DEFAULT 'g',
  `calories_per_100g` decimal(6,2) DEFAULT '0.00',
  `protein_per_100g` decimal(6,2) DEFAULT '0.00',
  `carb_per_100g` decimal(6,2) DEFAULT '0.00',
  `fat_per_100g` decimal(6,2) DEFAULT '0.00',
  `fiber_per_100g` decimal(6,2) DEFAULT '0.00',
  `is_vegetarian` tinyint(1) DEFAULT '1',
  `is_protein_rich` tinyint(1) DEFAULT '0',
  `is_calorie_dense` tinyint(1) DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_mess_day_meal` (`mess_type`,`day_of_week`,`meal_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
