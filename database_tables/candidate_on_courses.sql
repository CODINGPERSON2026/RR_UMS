-- Table schema for `candidate_on_courses`
-- Auto-created if not exists at runtime

CREATE TABLE IF NOT EXISTS `candidate_on_courses` (
  `id` int NOT NULL AUTO_INCREMENT,
  `army_number` varchar(50) NOT NULL,
  `course_starting_date` date NOT NULL,
  `course_end_date` date NOT NULL,
  `course_name` varchar(150) NOT NULL,
  `institute_name` varchar(150) NOT NULL,
  `status` varchar(50) NOT NULL DEFAULT 'Upcoming',
  `course_status` varchar(50) NOT NULL DEFAULT 'Confirmed',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_courses_army_number` (`army_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
