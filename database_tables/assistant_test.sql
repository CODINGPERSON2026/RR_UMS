-- Table schema for `assistant_test`
-- Auto-created if not exists at runtime

CREATE TABLE IF NOT EXISTS `assistant_test` (
  `id` int NOT NULL AUTO_INCREMENT,
  `batch` varchar(45) NOT NULL,
  `asst_test1` datetime DEFAULT NULL,
  `asst_test2` datetime DEFAULT NULL,
  `asst_test3` datetime DEFAULT NULL,
  `asst_test4` datetime DEFAULT NULL,
  `test1_status` tinyint(1) DEFAULT '0',
  `test2_status` tinyint(1) DEFAULT '0',
  `test3_status` tinyint(1) DEFAULT '0',
  `test4_status` tinyint(1) DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `DOE` date DEFAULT NULL,
  `TOE` date DEFAULT NULL,
  `TOS` date DEFAULT NULL,
  `END_OF_TENURE` varchar(50) DEFAULT NULL,
  `emergency_test1` date DEFAULT NULL,
  `emergency_test2` date DEFAULT NULL,
  `emergency_test3` date DEFAULT NULL,
  `emergency_test4` date DEFAULT NULL,
  `emergency_test1_type` varchar(20) DEFAULT NULL,
  `emergency_test2_type` varchar(20) DEFAULT NULL,
  `emergency_test3_type` varchar(20) DEFAULT NULL,
  `emergency_test4_type` varchar(20) DEFAULT NULL,
  `str` int DEFAULT NULL,
  `remarks` varchar(1000) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
