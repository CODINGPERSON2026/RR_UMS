-- MySQL dump 10.13  Distrib 8.0.46, for Win64 (x86_64)
--
-- Host: localhost    Database: rr_ums
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `ai_company_readiness_history`
--

DROP TABLE IF EXISTS `ai_company_readiness_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_company_readiness_history` (
  `id` int NOT NULL AUTO_INCREMENT,
  `company` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `snapshot_date` date NOT NULL,
  `strength_score` float NOT NULL,
  `qualification_score` float NOT NULL,
  `course_score` float NOT NULL,
  `trade_score` float NOT NULL,
  `fitness_score` float NOT NULL,
  `medical_score` float NOT NULL,
  `availability_score` float NOT NULL,
  `overall_readiness` float NOT NULL,
  `main_gap_type` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `gap_count` int DEFAULT '0',
  `actual_strength` int DEFAULT '0',
  `required_strength` int DEFAULT '0',
  `available_strength` int DEFAULT '0',
  `unfit_count` int DEFAULT '0',
  `onleave_count` int DEFAULT '0',
  `detachment_count` int DEFAULT '0',
  `td_count` int DEFAULT '0',
  `oncourse_count` int DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_comp_date` (`company`,`snapshot_date`),
  KEY `idx_company_hist` (`company`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ai_company_readiness_history`
--

LOCK TABLES `ai_company_readiness_history` WRITE;
/*!40000 ALTER TABLE `ai_company_readiness_history` DISABLE KEYS */;
/*!40000 ALTER TABLE `ai_company_readiness_history` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ai_company_requirements`
--

DROP TABLE IF EXISTS `ai_company_requirements`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_company_requirements` (
  `id` int NOT NULL AUTO_INCREMENT,
  `company` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `requirement_type` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `requirement_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `required_count` int NOT NULL DEFAULT '0',
  `priority` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT 'Medium',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT 'Active',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_company` (`company`),
  KEY `idx_requirement_type` (`requirement_type`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ai_company_requirements`
--

LOCK TABLES `ai_company_requirements` WRITE;
/*!40000 ALTER TABLE `ai_company_requirements` DISABLE KEYS */;
INSERT INTO `ai_company_requirements` VALUES (1,'HQ COY','Strength','Total Personnel',100,'Critical','Active','2026-11-04 12:43:51','2026-11-04 12:43:51'),(2,'HQ COY','Trade','TTC',40,'High','Active','2026-11-04 12:43:51','2026-11-04 12:43:51'),(3,'HQ COY','Trade','LMN',20,'High','Active','2026-11-04 12:43:51','2026-11-04 12:43:51'),(4,'HQ COY','Trade','EFS',15,'Medium','Active','2026-11-04 12:43:51','2026-11-04 12:43:51'),(5,'HQ COY','Trade','OCC',10,'Medium','Active','2026-11-04 12:43:51','2026-11-04 12:43:51'),(6,'HQ COY','Trade','CLK SD',10,'High','Active','2026-11-04 12:43:51','2026-11-04 12:43:51'),(7,'HQ COY','Qualification','12th',80,'Medium','Active','2026-11-04 12:43:51','2026-11-04 12:43:51'),(8,'HQ COY','Qualification','Graduation',20,'Low','Active','2026-11-04 12:43:51','2026-11-04 12:43:51'),(9,'HQ COY','Course','TTC CL I',15,'High','Active','2026-11-04 12:43:51','2026-11-04 12:43:51'),(10,'HQ COY','Course','Signals',25,'Medium','Active','2026-11-04 12:43:51','2026-11-04 12:43:51'),(11,'COMN COY','Strength','Total Personnel',120,'Critical','Active','2026-11-04 12:43:51','2026-11-04 12:43:51'),(12,'COMN COY','Trade','TTC',50,'High','Active','2026-11-04 12:43:51','2026-11-04 12:43:51'),(13,'COMN COY','Trade','LMN',35,'High','Active','2026-11-04 12:43:51','2026-11-04 12:43:51'),(14,'COMN COY','Trade','EFS',20,'Medium','Active','2026-11-04 12:43:51','2026-11-04 12:43:51'),(15,'COMN COY','Trade','OCC',15,'Medium','Active','2026-11-04 12:43:51','2026-11-04 12:43:51'),(16,'COMN COY','Qualification','12th',90,'Medium','Active','2026-11-04 12:43:51','2026-11-04 12:43:51'),(17,'COMN COY','Course','TTC CL I',20,'High','Active','2026-11-04 12:43:51','2026-11-04 12:43:51'),(18,'COMN COY','Course','Signals',40,'High','Active','2026-11-04 12:43:51','2026-11-04 12:43:51'),(19,'3 COY','Strength','Total Personnel',110,'Critical','Active','2026-11-04 12:43:51','2026-11-04 12:43:51'),(20,'3 COY','Trade','TTC',45,'High','Active','2026-11-04 12:43:51','2026-11-04 12:43:51'),(21,'3 COY','Trade','LMN',25,'High','Active','2026-11-04 12:43:51','2026-11-04 12:43:51'),(22,'3 COY','Trade','EFS',15,'Medium','Active','2026-11-04 12:43:51','2026-11-04 12:43:51'),(23,'3 COY','Qualification','12th',85,'Medium','Active','2026-11-04 12:43:51','2026-11-04 12:43:51'),(24,'3 COY','Course','TTC CL I',15,'High','Active','2026-11-04 12:43:51','2026-11-04 12:43:51');
/*!40000 ALTER TABLE `ai_company_requirements` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ai_fitness_reports`
--

DROP TABLE IF EXISTS `ai_fitness_reports`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_fitness_reports` (
  `id` int NOT NULL AUTO_INCREMENT,
  `personnel_id` int DEFAULT NULL,
  `army_number` varchar(50) NOT NULL,
  `name` varchar(150) DEFAULT NULL,
  `rank` varchar(100) DEFAULT NULL,
  `company` varchar(100) DEFAULT NULL,
  `age` int DEFAULT NULL,
  `height_cm` decimal(6,2) DEFAULT NULL,
  `actual_weight_kg` decimal(6,2) DEFAULT NULL,
  `ideal_weight_kg` decimal(6,2) DEFAULT NULL,
  `bmi` decimal(6,2) DEFAULT NULL,
  `fitness_score` decimal(6,2) DEFAULT NULL,
  `fitness_status` varchar(100) DEFAULT NULL,
  `prediction_result` longtext,
  `recommendations` longtext,
  `diet_recommendations` longtext,
  `exercise_recommendations` longtext,
  `progression_prediction` longtext,
  `report_language` varchar(50) DEFAULT 'English',
  `report_generated` tinyint(1) DEFAULT '1',
  `pdf_path` varchar(500) DEFAULT NULL,
  `model_name` varchar(150) DEFAULT NULL,
  `model_version` varchar(100) DEFAULT NULL,
  `generated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_army_number` (`army_number`),
  KEY `idx_army_number` (`army_number`),
  KEY `idx_personnel_id` (`personnel_id`),
  KEY `idx_company` (`company`),
  KEY `idx_fitness_status` (`fitness_status`),
  KEY `idx_generated_at` (`generated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ai_fitness_reports`
--

LOCK TABLES `ai_fitness_reports` WRITE;
/*!40000 ALTER TABLE `ai_fitness_reports` DISABLE KEYS */;
/*!40000 ALTER TABLE `ai_fitness_reports` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ai_mess_menus`
--

DROP TABLE IF EXISTS `ai_mess_menus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_mess_menus` (
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
) ENGINE=InnoDB AUTO_INCREMENT=214 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ai_mess_menus`
--

LOCK TABLES `ai_mess_menus` WRITE;
/*!40000 ALTER TABLE `ai_mess_menus` DISABLE KEYS */;
INSERT INTO `ai_mess_menus` VALUES (1,'OR','Monday','Breakfast','Rice','g',130.00,2.70,28.20,0.30,0.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(2,'OR','Monday','Breakfast','Aloo Soyabeen / Aloo Rajma','g',125.00,8.00,16.00,3.50,3.80,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(3,'OR','Monday','Tea','Bread Pakoda & Tea','serving',240.00,5.50,32.00,10.00,2.00,1,0,1,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(4,'OR','Monday','Lunch','Rice','g',130.00,2.70,28.20,0.30,0.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(5,'OR','Monday','Lunch','Chapati','pieces',75.00,3.10,15.50,0.50,2.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(6,'OR','Monday','Lunch','Mix Dal','g',95.00,6.50,14.50,1.80,3.80,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(7,'OR','Monday','Lunch','Mix Veg','g',70.00,2.50,9.50,2.50,3.20,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(8,'OR','Monday','Lunch','Seasonal Veg','g',65.00,2.20,8.80,2.20,3.00,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(9,'OR','Monday','Lunch','Kheer','g',165.00,3.80,26.00,5.20,0.40,1,0,1,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(10,'OR','Monday','Dinner','Rice','g',130.00,2.70,28.20,0.30,0.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(11,'OR','Monday','Dinner','Roti','pieces',75.00,3.10,15.50,0.50,2.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(12,'OR','Monday','Dinner','Dal','g',90.00,6.00,14.00,1.50,3.50,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(13,'OR','Monday','Dinner','Chicken Curry','g',155.00,16.50,4.20,8.20,1.00,0,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(14,'OR','Monday','Dinner','Mutter Paneer','g',150.00,8.50,7.50,9.80,2.20,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(15,'OR','Tuesday','Breakfast','Namkeen Puri','pieces',115.00,2.40,14.50,5.80,1.10,1,0,1,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(16,'OR','Tuesday','Breakfast','Kheer','g',165.00,3.80,26.00,5.20,0.40,1,0,1,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(17,'OR','Tuesday','Tea','Pakoda & Tea','serving',210.00,4.50,26.00,9.50,2.20,1,0,1,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(18,'OR','Tuesday','Lunch','Rice','g',130.00,2.70,28.20,0.30,0.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(19,'OR','Tuesday','Lunch','Chapati','pieces',75.00,3.10,15.50,0.50,2.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(20,'OR','Tuesday','Lunch','Kadhi','g',85.00,3.50,8.50,4.00,1.00,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(21,'OR','Tuesday','Lunch','Mix Veg','g',70.00,2.50,9.50,2.50,3.20,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(22,'OR','Tuesday','Lunch','Salad','g',25.00,1.00,5.00,0.20,2.50,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(23,'OR','Tuesday','Dinner','Rice','g',130.00,2.70,28.20,0.30,0.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(24,'OR','Tuesday','Dinner','Chapati','pieces',75.00,3.10,15.50,0.50,2.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(25,'OR','Tuesday','Dinner','Dal','g',90.00,6.00,14.00,1.50,3.50,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(26,'OR','Tuesday','Dinner','Sahi Paneer','g',175.00,8.00,8.50,12.50,1.50,1,1,1,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(27,'OR','Wednesday','Breakfast','Plain Paratha','pieces',190.00,4.50,26.00,8.00,2.50,1,0,1,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(28,'OR','Wednesday','Breakfast','Dahi / Achar','g',65.00,3.20,4.50,3.50,0.20,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(29,'OR','Wednesday','Tea','Poha & Tea','serving',170.00,4.20,32.00,3.50,1.80,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(30,'OR','Wednesday','Lunch','Rice','g',130.00,2.70,28.20,0.30,0.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(31,'OR','Wednesday','Lunch','Chapati','pieces',75.00,3.10,15.50,0.50,2.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(32,'OR','Wednesday','Lunch','Mix Dal','g',95.00,6.50,14.50,1.80,3.80,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(33,'OR','Wednesday','Lunch','Mix Veg','g',70.00,2.50,9.50,2.50,3.20,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(34,'OR','Wednesday','Lunch','Seasonal Veg','g',65.00,2.20,8.80,2.20,3.00,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(35,'OR','Wednesday','Lunch','Kheer','g',165.00,3.80,26.00,5.20,0.40,1,0,1,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(36,'OR','Wednesday','Dinner','Rice','g',130.00,2.70,28.20,0.30,0.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(37,'OR','Wednesday','Dinner','Chapati','pieces',75.00,3.10,15.50,0.50,2.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(38,'OR','Wednesday','Dinner','Dal','g',90.00,6.00,14.00,1.50,3.50,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(39,'OR','Wednesday','Dinner','Chicken Curry','g',155.00,16.50,4.20,8.20,1.00,0,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(40,'OR','Wednesday','Dinner','Mutter Paneer','g',150.00,8.50,7.50,9.80,2.20,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(41,'OR','Thursday','Breakfast','Upma / Poha with Chutney','g',140.00,3.20,25.00,3.20,1.80,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(42,'OR','Thursday','Breakfast','Boiled Egg','pieces',75.00,6.30,0.60,5.00,0.00,0,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(43,'OR','Thursday','Tea','Chana Masala & Tea','serving',190.00,8.50,28.00,4.50,5.50,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(44,'OR','Thursday','Lunch','Rice','g',130.00,2.70,28.20,0.30,0.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(45,'OR','Thursday','Lunch','Chapati','pieces',75.00,3.10,15.50,0.50,2.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(46,'OR','Thursday','Lunch','Kadhi','g',85.00,3.50,8.50,4.00,1.00,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(47,'OR','Thursday','Lunch','Mix Veg','g',70.00,2.50,9.50,2.50,3.20,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(48,'OR','Thursday','Lunch','Seasonal Veg','g',65.00,2.20,8.80,2.20,3.00,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(49,'OR','Thursday','Dinner','Rice','g',130.00,2.70,28.20,0.30,0.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(50,'OR','Thursday','Dinner','Chapati','pieces',75.00,3.10,15.50,0.50,2.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(51,'OR','Thursday','Dinner','Dal','g',90.00,6.00,14.00,1.50,3.50,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(52,'OR','Thursday','Dinner','Palak Paneer','g',135.00,8.20,5.50,9.20,2.80,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(53,'OR','Thursday','Dinner','Egg Curry','g',140.00,11.50,4.50,8.50,0.80,0,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(54,'OR','Friday','Breakfast','Puri & Sabji','g',170.00,3.50,22.00,8.00,2.50,1,0,1,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(55,'OR','Friday','Tea','Aloo Bonda & Tea','serving',220.00,4.50,29.00,9.50,2.20,1,0,1,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(56,'OR','Friday','Lunch','Rice','g',130.00,2.70,28.20,0.30,0.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(57,'OR','Friday','Lunch','Chapati','pieces',75.00,3.10,15.50,0.50,2.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(58,'OR','Friday','Lunch','Mix Dal','g',95.00,6.50,14.50,1.80,3.80,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(59,'OR','Friday','Lunch','Mix Veg','g',70.00,2.50,9.50,2.50,3.20,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(60,'OR','Friday','Lunch','Seasonal Veg','g',65.00,2.20,8.80,2.20,3.00,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(61,'OR','Friday','Lunch','Kheer','g',165.00,3.80,26.00,5.20,0.40,1,0,1,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(62,'OR','Friday','Dinner','Rice','g',130.00,2.70,28.20,0.30,0.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(63,'OR','Friday','Dinner','Chapati','pieces',75.00,3.10,15.50,0.50,2.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(64,'OR','Friday','Dinner','Dal','g',90.00,6.00,14.00,1.50,3.50,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(65,'OR','Friday','Dinner','Chicken Curry','g',155.00,16.50,4.20,8.20,1.00,0,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(66,'OR','Friday','Dinner','Mutter Paneer','g',150.00,8.50,7.50,9.80,2.20,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(67,'OR','Saturday','Breakfast','Khichdi','g',120.00,4.20,22.00,2.00,2.20,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(68,'OR','Saturday','Breakfast','Dahi / Achar','g',65.00,3.20,4.50,3.50,0.20,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(69,'OR','Saturday','Tea','Dal Vada & Tea','serving',200.00,7.50,26.00,7.50,4.00,1,1,1,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(70,'OR','Saturday','Lunch','Rice','g',130.00,2.70,28.20,0.30,0.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(71,'OR','Saturday','Lunch','Chapati','pieces',75.00,3.10,15.50,0.50,2.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(72,'OR','Saturday','Lunch','Mix Dal','g',95.00,6.50,14.50,1.80,3.80,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(73,'OR','Saturday','Lunch','Mix Veg','g',70.00,2.50,9.50,2.50,3.20,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(74,'OR','Saturday','Lunch','Seasonal Veg','g',65.00,2.20,8.80,2.20,3.00,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(75,'OR','Saturday','Dinner','Rice','g',130.00,2.70,28.20,0.30,0.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(76,'OR','Saturday','Dinner','Chapati','pieces',75.00,3.10,15.50,0.50,2.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(77,'OR','Saturday','Dinner','Dal','g',90.00,6.00,14.00,1.50,3.50,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(78,'OR','Saturday','Dinner','Paneer Chilli','g',165.00,9.00,9.00,10.50,1.80,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(79,'OR','Saturday','Dinner','Egg Curry','g',140.00,11.50,4.50,8.50,0.80,0,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(80,'OR','Sunday','Breakfast','South Indian / Chinese / Pav Bhaji / Chhola Bhatura with Sweet','g',210.00,5.00,30.00,8.00,2.00,1,0,1,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(81,'OR','Sunday','Tea','Sunday','serving',120.00,3.00,18.00,4.00,1.50,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(82,'OR','Sunday','Lunch','Biryani / Jeera Rice','g',165.00,4.50,27.00,4.50,1.50,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(83,'OR','Sunday','Lunch','Shambhar / Sambar','g',65.00,3.20,10.00,1.20,2.50,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(84,'OR','Sunday','Lunch','Chicken Curry','g',155.00,16.50,4.20,8.20,1.00,0,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(85,'OR','Sunday','Lunch','Mutter Paneer','g',150.00,8.50,7.50,9.80,2.20,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(86,'OR','Sunday','Lunch','Papad','pieces',35.00,2.00,6.00,0.50,1.00,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(87,'OR','Sunday','Lunch','Salad','g',25.00,1.00,5.00,0.20,2.50,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(88,'OR','Sunday','Lunch','Puri','pieces',110.00,2.20,14.00,5.50,1.00,1,0,1,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(89,'OR','Sunday','Lunch','Kheer','g',165.00,3.80,26.00,5.20,0.40,1,0,1,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(90,'OR','Sunday','Dinner','Rice','g',130.00,2.70,28.20,0.30,0.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(91,'OR','Sunday','Dinner','Roti','pieces',75.00,3.10,15.50,0.50,2.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(92,'OR','Sunday','Dinner','Dal','g',90.00,6.00,14.00,1.50,3.50,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(93,'OR','Sunday','Dinner','Seasonal Veg','g',65.00,2.20,8.80,2.20,3.00,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(94,'JCO','Monday','Breakfast','Chapati','pieces',75.00,3.10,15.50,0.50,2.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(95,'JCO','Monday','Breakfast','Veg Curry','g',75.00,2.40,9.00,3.20,2.80,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(96,'JCO','Monday','Breakfast','Tea','ml',45.00,1.50,7.50,1.20,0.00,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(97,'JCO','Monday','Lunch','Lemon Rice','g',145.00,2.80,27.50,2.50,0.60,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(98,'JCO','Monday','Lunch','Roti','pieces',75.00,3.10,15.50,0.50,2.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(99,'JCO','Monday','Lunch','Dal Mix','g',95.00,6.50,14.50,1.80,3.80,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(100,'JCO','Monday','Lunch','2 x Veg','g',70.00,2.50,9.50,2.50,3.20,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(101,'JCO','Monday','Lunch','Mutter Paneer','g',150.00,8.50,7.50,9.80,2.20,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(102,'JCO','Monday','Lunch','Salad','g',25.00,1.00,5.00,0.20,2.50,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(103,'JCO','Monday','Lunch','Chutney','g',45.00,1.20,6.50,1.80,1.50,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(104,'JCO','Monday','Dinner','Rice','g',130.00,2.70,28.20,0.30,0.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(105,'JCO','Monday','Dinner','Roti','pieces',75.00,3.10,15.50,0.50,2.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(106,'JCO','Monday','Dinner','Dal Mashri','g',105.00,7.00,15.00,2.20,4.00,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(107,'JCO','Monday','Dinner','Chicken Curry','g',155.00,16.50,4.20,8.20,1.00,0,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(108,'JCO','Monday','Dinner','01 x Veg','g',70.00,2.50,9.50,2.50,3.20,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(109,'JCO','Monday','Dinner','01 x Normal Veg','g',65.00,2.20,8.80,2.20,3.00,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(110,'JCO','Monday','Dinner','Gajar Halwa / Kheer','g',185.00,3.50,28.00,7.00,1.20,1,0,1,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(111,'JCO','Tuesday','Breakfast','Aloo Paratha / Paneer Paratha / Muli Paratha','pieces',220.00,6.50,28.00,9.50,2.80,1,1,1,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(112,'JCO','Tuesday','Breakfast','Chutney','g',45.00,1.20,6.50,1.80,1.50,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(113,'JCO','Tuesday','Breakfast','Tea','ml',45.00,1.50,7.50,1.20,0.00,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(114,'JCO','Tuesday','Lunch','Jeera Rice','g',140.00,2.80,27.00,2.20,0.50,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(115,'JCO','Tuesday','Lunch','Roti','pieces',75.00,3.10,15.50,0.50,2.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(116,'JCO','Tuesday','Lunch','Kadhi','g',85.00,3.50,8.50,4.00,1.00,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(117,'JCO','Tuesday','Lunch','2 x Veg','g',70.00,2.50,9.50,2.50,3.20,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(118,'JCO','Tuesday','Lunch','Papad','pieces',35.00,2.00,6.00,0.50,1.00,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(119,'JCO','Tuesday','Lunch','Salad','g',25.00,1.00,5.00,0.20,2.50,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(120,'JCO','Tuesday','Lunch','Karela Chips','g',85.00,2.00,11.00,3.80,3.50,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(121,'JCO','Tuesday','Lunch','Mirchi Fry','g',60.00,1.50,7.00,3.00,2.00,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(122,'JCO','Tuesday','Dinner','Rice','g',130.00,2.70,28.20,0.30,0.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(123,'JCO','Tuesday','Dinner','Roti','pieces',75.00,3.10,15.50,0.50,2.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(124,'JCO','Tuesday','Dinner','Dal Mung','g',88.00,6.80,13.50,1.20,3.60,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(125,'JCO','Tuesday','Dinner','02 x Veg','g',70.00,2.50,9.50,2.50,3.20,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(126,'JCO','Tuesday','Dinner','01 x Special Paneer','g',160.00,8.50,8.00,11.00,1.80,1,1,1,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(127,'JCO','Tuesday','Dinner','Daliya Wheat','g',110.00,3.80,22.00,1.00,3.50,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(128,'JCO','Wednesday','Breakfast','Chola Bhatura','pieces',240.00,6.00,32.00,10.50,3.00,1,0,1,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(129,'JCO','Wednesday','Breakfast','Tea','ml',45.00,1.50,7.50,1.20,0.00,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(130,'JCO','Wednesday','Lunch','Rice Pulav','g',150.00,3.20,26.50,3.20,1.20,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(131,'JCO','Wednesday','Lunch','Rumali Roti','pieces',110.00,3.50,22.00,1.20,1.50,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(132,'JCO','Wednesday','Lunch','Dal Makhani','g',130.00,5.80,14.00,6.00,3.50,1,1,1,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(133,'JCO','Wednesday','Lunch','2 x Veg','g',70.00,2.50,9.50,2.50,3.20,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(134,'JCO','Wednesday','Lunch','Chutney','g',45.00,1.20,6.50,1.80,1.50,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(135,'JCO','Wednesday','Lunch','Salad','g',25.00,1.00,5.00,0.20,2.50,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(136,'JCO','Wednesday','Dinner','Rice','g',130.00,2.70,28.20,0.30,0.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(137,'JCO','Wednesday','Dinner','Butter Roti','pieces',105.00,3.20,15.50,3.80,2.40,1,0,1,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(138,'JCO','Wednesday','Dinner','Dal','g',90.00,6.00,14.00,1.50,3.50,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(139,'JCO','Wednesday','Dinner','Chicken Curry','g',155.00,16.50,4.20,8.20,1.00,0,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(140,'JCO','Wednesday','Dinner','Mutter Paneer','g',150.00,8.50,7.50,9.80,2.20,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(141,'JCO','Wednesday','Dinner','02 x Veg','g',70.00,2.50,9.50,2.50,3.20,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(142,'JCO','Wednesday','Dinner','Bombay Toast','pieces',130.00,4.00,18.00,4.80,1.20,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(143,'JCO','Thursday','Breakfast','Bread Omelet / Bread Cutlet','pieces',180.00,8.50,18.00,8.00,1.50,0,1,1,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(144,'JCO','Thursday','Breakfast','Tea','ml',45.00,1.50,7.50,1.20,0.00,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(145,'JCO','Thursday','Lunch','Veg Rice','g',140.00,3.00,26.00,2.50,1.50,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(146,'JCO','Thursday','Lunch','Roti','pieces',75.00,3.10,15.50,0.50,2.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(147,'JCO','Thursday','Lunch','Sambar','g',65.00,3.20,10.00,1.20,2.50,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(148,'JCO','Thursday','Lunch','02 x Veg','g',70.00,2.50,9.50,2.50,3.20,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(149,'JCO','Thursday','Lunch','Salad','g',25.00,1.00,5.00,0.20,2.50,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(150,'JCO','Thursday','Lunch','Papad','pieces',35.00,2.00,6.00,0.50,1.00,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(151,'JCO','Thursday','Lunch','Chutney','g',45.00,1.20,6.50,1.80,1.50,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(152,'JCO','Thursday','Dinner','Rice','g',130.00,2.70,28.20,0.30,0.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(153,'JCO','Thursday','Dinner','Roti','pieces',75.00,3.10,15.50,0.50,2.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(154,'JCO','Thursday','Dinner','Dal Mung','g',88.00,6.80,13.50,1.20,3.60,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(155,'JCO','Thursday','Dinner','Chicken Curry','g',155.00,16.50,4.20,8.20,1.00,0,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(156,'JCO','Thursday','Dinner','02 x Veg','g',70.00,2.50,9.50,2.50,3.20,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(157,'JCO','Thursday','Dinner','01 x Mutter Mushroom','g',80.00,4.20,9.00,3.00,2.80,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(158,'JCO','Thursday','Dinner','Kheer','g',165.00,3.80,26.00,5.20,0.40,1,0,1,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(159,'JCO','Thursday','Dinner','Sabudana','g',140.00,1.50,31.00,1.00,0.50,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(160,'JCO','Friday','Breakfast','Porota','pieces',190.00,4.50,26.00,8.00,2.50,1,0,1,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(161,'JCO','Friday','Breakfast','Chutney','g',45.00,1.20,6.50,1.80,1.50,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(162,'JCO','Friday','Breakfast','Egg Bhurji','g',150.00,10.50,3.00,10.50,0.50,0,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(163,'JCO','Friday','Breakfast','Tea','ml',45.00,1.50,7.50,1.20,0.00,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(164,'JCO','Friday','Lunch','Lemon Rice','g',145.00,2.80,27.50,2.50,0.60,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(165,'JCO','Friday','Lunch','Roti','pieces',75.00,3.10,15.50,0.50,2.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(166,'JCO','Friday','Lunch','Dal Rajmah','g',115.00,7.50,17.00,2.20,5.00,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(167,'JCO','Friday','Lunch','2 x Veg','g',70.00,2.50,9.50,2.50,3.20,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(168,'JCO','Friday','Lunch','Salad','g',25.00,1.00,5.00,0.20,2.50,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(169,'JCO','Friday','Lunch','Mirchi Fry','g',60.00,1.50,7.00,3.00,2.00,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(170,'JCO','Friday','Dinner','Rice','g',130.00,2.70,28.20,0.30,0.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(171,'JCO','Friday','Dinner','Roti','pieces',75.00,3.10,15.50,0.50,2.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(172,'JCO','Friday','Dinner','Dal Mix','g',95.00,6.50,14.50,1.80,3.80,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(173,'JCO','Friday','Dinner','02 x Veg','g',70.00,2.50,9.50,2.50,3.20,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(174,'JCO','Friday','Dinner','Chicken Egg Curry','g',160.00,15.50,4.00,9.00,0.80,0,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(175,'JCO','Friday','Dinner','Gulab Jamun','pieces',150.00,2.50,24.00,5.50,0.20,1,0,1,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(176,'JCO','Saturday','Breakfast','Fried Rice','g',160.00,3.50,28.00,4.00,1.00,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(177,'JCO','Saturday','Breakfast','Upma','g',135.00,3.50,24.00,3.00,1.80,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(178,'JCO','Saturday','Breakfast','Boiled Egg','pieces',75.00,6.30,0.60,5.00,0.00,0,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(179,'JCO','Saturday','Breakfast','Tea','ml',45.00,1.50,7.50,1.20,0.00,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(180,'JCO','Saturday','Lunch','Jeera Rice','g',140.00,2.80,27.00,2.20,0.50,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(181,'JCO','Saturday','Lunch','Missi Roti','pieces',115.00,5.20,18.00,2.50,3.20,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(182,'JCO','Saturday','Lunch','Dal Arhar','g',92.00,6.20,14.00,1.60,3.50,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(183,'JCO','Saturday','Lunch','Mutter Paneer','g',150.00,8.50,7.50,9.80,2.20,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(184,'JCO','Saturday','Lunch','1 x Veg Normal','g',65.00,2.20,8.80,2.20,3.00,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(185,'JCO','Saturday','Lunch','Salad','g',25.00,1.00,5.00,0.20,2.50,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(186,'JCO','Saturday','Lunch','Chutney','g',45.00,1.20,6.50,1.80,1.50,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(187,'JCO','Saturday','Lunch','Mirchi Fry','g',60.00,1.50,7.00,3.00,2.00,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(188,'JCO','Saturday','Dinner','Rice','g',130.00,2.70,28.20,0.30,0.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(189,'JCO','Saturday','Dinner','Butter Roti','pieces',105.00,3.20,15.50,3.80,2.40,1,0,1,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(190,'JCO','Saturday','Dinner','Dal','g',90.00,6.00,14.00,1.50,3.50,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(191,'JCO','Saturday','Dinner','Chicken Curry','g',155.00,16.50,4.20,8.20,1.00,0,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(192,'JCO','Saturday','Dinner','Omelet','pieces',140.00,9.50,2.00,10.00,0.40,0,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(193,'JCO','Saturday','Dinner','02 x Veg','g',70.00,2.50,9.50,2.50,3.20,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(194,'JCO','Saturday','Dinner','01 x Veg Normal','g',100.00,4.00,15.00,3.00,1.50,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(195,'JCO','Saturday','Dinner','Jeera Rice','g',140.00,2.80,27.00,2.20,0.50,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(196,'JCO','Sunday','Breakfast','Idli, Dosa, Uthappam','pieces',130.00,3.80,26.00,1.50,1.80,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(197,'JCO','Sunday','Breakfast','Sambar','g',65.00,3.20,10.00,1.20,2.50,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(198,'JCO','Sunday','Breakfast','Chutney','g',45.00,1.20,6.50,1.80,1.50,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(199,'JCO','Sunday','Breakfast','Gulab Jamun & Tea','serving',190.00,3.80,31.00,6.50,0.20,1,0,1,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(200,'JCO','Sunday','Lunch','Chicken Biryani','g',180.00,12.00,23.00,5.50,1.20,0,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(201,'JCO','Sunday','Lunch','Veg Biryani','g',155.00,4.00,26.00,4.00,2.00,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(202,'JCO','Sunday','Lunch','Fish Curry','g',135.00,15.00,3.50,6.80,0.80,0,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(203,'JCO','Sunday','Lunch','Roti','pieces',75.00,3.10,15.50,0.50,2.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(204,'JCO','Sunday','Lunch','Papad','pieces',35.00,2.00,6.00,0.50,1.00,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(205,'JCO','Sunday','Lunch','Salad','g',25.00,1.00,5.00,0.20,2.50,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(206,'JCO','Sunday','Lunch','Kachumber','g',28.00,1.20,5.50,0.20,2.60,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(207,'JCO','Sunday','Lunch','Chutney','g',45.00,1.20,6.50,1.80,1.50,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(208,'JCO','Sunday','Dinner','Rice','g',130.00,2.70,28.20,0.30,0.40,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(209,'JCO','Sunday','Dinner','Rumali Roti','pieces',110.00,3.50,22.00,1.20,1.50,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(210,'JCO','Sunday','Dinner','Dal','g',90.00,6.00,14.00,1.50,3.50,1,1,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(211,'JCO','Sunday','Dinner','02 x Veg','g',70.00,2.50,9.50,2.50,3.20,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(212,'JCO','Sunday','Dinner','01 x Normal Veg','g',65.00,2.20,8.80,2.20,3.00,1,0,0,'2026-11-04 12:42:28','2026-11-04 12:42:28'),(213,'JCO','Sunday','Dinner','Kheer','g',165.00,3.80,26.00,5.20,0.40,1,0,1,'2026-11-04 12:42:28','2026-11-04 12:42:28');
/*!40000 ALTER TABLE `ai_mess_menus` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ai_new_joinee_recommendations`
--

DROP TABLE IF EXISTS `ai_new_joinee_recommendations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_new_joinee_recommendations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `personnel_id` int DEFAULT NULL,
  `army_number` varchar(50) DEFAULT NULL,
  `name` varchar(150) DEFAULT NULL,
  `rank` varchar(50) DEFAULT NULL,
  `trade` varchar(100) DEFAULT NULL,
  `recommended_company` varchar(50) NOT NULL,
  `confidence_score` varchar(50) NOT NULL,
  `recommendation_percentage` decimal(5,2) NOT NULL,
  `probabilities_json` text,
  `match_reasons_json` text,
  `shap_json` text,
  `units_history_json` text,
  `final_company` varchar(50) DEFAULT NULL,
  `decision_type` varchar(50) DEFAULT 'AI Recommended',
  `decision_remarks` text,
  `decided_by` varchar(100) DEFAULT NULL,
  `decided_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `recommended_position` varchar(200) DEFAULT NULL,
  `position_confidence` varchar(50) DEFAULT NULL,
  `confidence_type` varchar(100) DEFAULT 'ml',
  `model_version` varchar(100) DEFAULT NULL,
  `final_position` varchar(200) DEFAULT NULL,
  `updated_by` varchar(200) DEFAULT NULL,
  `updated_by_role` varchar(100) DEFAULT NULL,
  `updated_by_user_id` varchar(100) DEFAULT NULL,
  `adjutant_action` varchar(50) DEFAULT NULL,
  `adjutant_company` varchar(100) DEFAULT NULL,
  `adjutant_section` varchar(100) DEFAULT NULL,
  `adjutant_position` varchar(200) DEFAULT NULL,
  `adjutant_remarks` text,
  `adjutant_by` varchar(200) DEFAULT NULL,
  `adjutant_at` datetime DEFAULT NULL,
  `two_ic_updated` int DEFAULT '0',
  `two_ic_message` text,
  `final_section` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_army_number` (`army_number`),
  KEY `idx_personnel_id` (`personnel_id`),
  KEY `idx_rec_coy` (`recommended_company`),
  KEY `idx_decision` (`decision_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ai_new_joinee_recommendations`
--

LOCK TABLES `ai_new_joinee_recommendations` WRITE;
/*!40000 ALTER TABLE `ai_new_joinee_recommendations` DISABLE KEYS */;
/*!40000 ALTER TABLE `ai_new_joinee_recommendations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `assigned_det`
--

DROP TABLE IF EXISTS `assigned_det`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `assigned_det` (
  `army_number` varchar(15) NOT NULL,
  `det_id` int DEFAULT NULL,
  `assigned_on` datetime DEFAULT CURRENT_TIMESTAMP,
  `det_removed_date` datetime DEFAULT NULL,
  `det_status` tinyint(1) DEFAULT '1',
  KEY `idx_assigned_det_status` (`det_status`,`army_number`),
  KEY `idx_assigned_det_id` (`det_id`),
  KEY `idx_assigned_det_status_army` (`det_status`,`army_number`,`det_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `assigned_det`
--

LOCK TABLES `assigned_det` WRITE;
/*!40000 ALTER TABLE `assigned_det` DISABLE KEYS */;
/*!40000 ALTER TABLE `assigned_det` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `assigned_personnel`
--

DROP TABLE IF EXISTS `assigned_personnel`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `assigned_personnel` (
  `army_number` varchar(15) NOT NULL,
  `det_id` int DEFAULT NULL,
  `assigned_on` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`army_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `assigned_personnel`
--

LOCK TABLES `assigned_personnel` WRITE;
/*!40000 ALTER TABLE `assigned_personnel` DISABLE KEYS */;
/*!40000 ALTER TABLE `assigned_personnel` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `assistant_test`
--

DROP TABLE IF EXISTS `assistant_test`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `assistant_test` (
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
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `assistant_test`
--

LOCK TABLES `assistant_test` WRITE;
/*!40000 ALTER TABLE `assistant_test` DISABLE KEYS */;
/*!40000 ALTER TABLE `assistant_test` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `board_members`
--

DROP TABLE IF EXISTS `board_members`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `board_members` (
  `id` int NOT NULL AUTO_INCREMENT,
  `order_no` varchar(50) DEFAULT NULL,
  `member_name` varchar(255) DEFAULT NULL,
  `army_number` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `board_members`
--

LOCK TABLES `board_members` WRITE;
/*!40000 ALTER TABLE `board_members` DISABLE KEYS */;
/*!40000 ALTER TABLE `board_members` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `boards`
--

DROP TABLE IF EXISTS `boards`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `boards` (
  `id` int NOT NULL AUTO_INCREMENT,
  `order_no` varchar(50) DEFAULT NULL,
  `entry_date` date DEFAULT NULL,
  `authority` varchar(255) DEFAULT NULL,
  `subject` varchar(255) DEFAULT NULL,
  `presiding_officer` varchar(255) DEFAULT NULL,
  `completion_date` date DEFAULT NULL,
  `remarks` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `boards`
--

LOCK TABLES `boards` WRITE;
/*!40000 ALTER TABLE `boards` DISABLE KEYS */;
/*!40000 ALTER TABLE `boards` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `candidate_on_courses`
--

DROP TABLE IF EXISTS `candidate_on_courses`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `candidate_on_courses` (
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
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `candidate_on_courses`
--

LOCK TABLES `candidate_on_courses` WRITE;
/*!40000 ALTER TABLE `candidate_on_courses` DISABLE KEYS */;
/*!40000 ALTER TABLE `candidate_on_courses` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `children`
--

DROP TABLE IF EXISTS `children`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `children` (
  `id` int NOT NULL AUTO_INCREMENT,
  `personnel_id` int NOT NULL,
  `army_number` varchar(100) NOT NULL,
  `sr_no` int DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  `date_of_birth` date DEFAULT NULL,
  `class` varchar(100) DEFAULT NULL,
  `part_ii_order` varchar(100) DEFAULT NULL,
  `uid_no` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_army_number` (`army_number`),
  KEY `idx_personnel_id_children` (`personnel_id`),
  CONSTRAINT `children_ibfk_1` FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `children`
--

LOCK TABLES `children` WRITE;
/*!40000 ALTER TABLE `children` DISABLE KEYS */;
/*!40000 ALTER TABLE `children` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `company_interview`
--

DROP TABLE IF EXISTS `company_interview`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `company_interview` (
  `id` int NOT NULL AUTO_INCREMENT,
  `army_number` varchar(45) NOT NULL,
  `interview_status` tinyint NOT NULL DEFAULT '0',
  `interview_done_on` date DEFAULT NULL,
  `remarks` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `co_interview_status` tinyint NOT NULL DEFAULT '0',
  `co_interview_done_on` date DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `company_interview`
--

LOCK TABLES `company_interview` WRITE;
/*!40000 ALTER TABLE `company_interview` DISABLE KEYS */;
/*!40000 ALTER TABLE `company_interview` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `courses`
--

DROP TABLE IF EXISTS `courses`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `courses` (
  `id` int NOT NULL AUTO_INCREMENT,
  `personnel_id` int NOT NULL,
  `army_number` varchar(100) NOT NULL,
  `sr_no` int DEFAULT NULL,
  `course` varchar(255) DEFAULT NULL,
  `from_date` date DEFAULT NULL,
  `to_date` date DEFAULT NULL,
  `institute` varchar(255) DEFAULT NULL,
  `grading` varchar(100) DEFAULT NULL,
  `remarks` text,
  PRIMARY KEY (`id`),
  KEY `idx_army_number` (`army_number`),
  KEY `idx_personnel_id_courses` (`personnel_id`),
  CONSTRAINT `courses_ibfk_1` FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `courses`
--

LOCK TABLES `courses` WRITE;
/*!40000 ALTER TABLE `courses` DISABLE KEYS */;
/*!40000 ALTER TABLE `courses` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `daily_events`
--

DROP TABLE IF EXISTS `daily_events`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `daily_events` (
  `id` int NOT NULL AUTO_INCREMENT,
  `event_date` date DEFAULT NULL,
  `event_name` varchar(255) DEFAULT NULL,
  `venue` varchar(255) DEFAULT NULL,
  `created_on` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `company` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `daily_events`
--

LOCK TABLES `daily_events` WRITE;
/*!40000 ALTER TABLE `daily_events` DISABLE KEYS */;
/*!40000 ALTER TABLE `daily_events` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `department_accounts`
--

DROP TABLE IF EXISTS `department_accounts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `department_accounts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `account_holder` varchar(100) NOT NULL,
  `current_balance` decimal(15,2) NOT NULL DEFAULT '0.00',
  `status` enum('ACTIVE','INACTIVE') DEFAULT 'ACTIVE',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `account_holder` (`account_holder`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `department_accounts`
--

LOCK TABLES `department_accounts` WRITE;
/*!40000 ALTER TABLE `department_accounts` DISABLE KEYS */;
/*!40000 ALTER TABLE `department_accounts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `department_transactions`
--

DROP TABLE IF EXISTS `department_transactions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `department_transactions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `department_account_id` int NOT NULL,
  `transaction_date` datetime DEFAULT CURRENT_TIMESTAMP,
  `old_balance` decimal(15,2) NOT NULL,
  `credit_amount` decimal(15,2) DEFAULT '0.00',
  `debit_amount` decimal(15,2) DEFAULT '0.00',
  `new_balance` decimal(15,2) NOT NULL,
  `transaction_type` enum('CREDIT','DEBIT') NOT NULL,
  `remarks` varchar(255) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `department_account_id` (`department_account_id`),
  CONSTRAINT `department_transactions_ibfk_1` FOREIGN KEY (`department_account_id`) REFERENCES `department_accounts` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `department_transactions`
--

LOCK TABLES `department_transactions` WRITE;
/*!40000 ALTER TABLE `department_transactions` DISABLE KEYS */;
/*!40000 ALTER TABLE `department_transactions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `det_td_alarm_days`
--

DROP TABLE IF EXISTS `det_td_alarm_days`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `det_td_alarm_days` (
  `alarm_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `days` int NOT NULL DEFAULT '90',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `updated_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`alarm_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `det_td_alarm_days`
--

LOCK TABLES `det_td_alarm_days` WRITE;
/*!40000 ALTER TABLE `det_td_alarm_days` DISABLE KEYS */;
INSERT INTO `det_td_alarm_days` VALUES ('attachment_alarm',80,'2026-11-04 12:13:00',NULL),('detachment_alarm',60,'2026-11-04 12:13:00',NULL);
/*!40000 ALTER TABLE `det_td_alarm_days` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `detailed_courses`
--

DROP TABLE IF EXISTS `detailed_courses`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `detailed_courses` (
  `id` int NOT NULL AUTO_INCREMENT,
  `personnel_id` int NOT NULL,
  `army_number` varchar(100) NOT NULL,
  `sr_no` int DEFAULT NULL,
  `course_name` varchar(255) DEFAULT NULL,
  `from_date` date DEFAULT NULL,
  `to_date` date DEFAULT NULL,
  `remarks` text,
  PRIMARY KEY (`id`),
  KEY `idx_army_number` (`army_number`),
  KEY `idx_personnel_id_detailed_courses` (`personnel_id`),
  CONSTRAINT `detailed_courses_ibfk_1` FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `detailed_courses`
--

LOCK TABLES `detailed_courses` WRITE;
/*!40000 ALTER TABLE `detailed_courses` DISABLE KEYS */;
/*!40000 ALTER TABLE `detailed_courses` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `dets`
--

DROP TABLE IF EXISTS `dets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dets` (
  `det_id` int NOT NULL AUTO_INCREMENT,
  `det_name` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`det_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dets`
--

LOCK TABLES `dets` WRITE;
/*!40000 ALTER TABLE `dets` DISABLE KEYS */;
/*!40000 ALTER TABLE `dets` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `doc_leave_details`
--

DROP TABLE IF EXISTS `doc_leave_details`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `doc_leave_details` (
  `id` int NOT NULL AUTO_INCREMENT,
  `army_number` varchar(50) DEFAULT NULL,
  `rank` varchar(50) DEFAULT NULL,
  `name` varchar(150) DEFAULT NULL,
  `company` varchar(100) DEFAULT NULL,
  `leave_type` varchar(50) DEFAULT NULL,
  `leave_days` int DEFAULT NULL,
  `from_date` date DEFAULT NULL,
  `to_date` date DEFAULT NULL,
  `onco_status` varchar(50) DEFAULT '',
  `doc_status` varchar(50) DEFAULT '',
  `action_status` varchar(100) DEFAULT '',
  `created_by` varchar(150) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `published_by` varchar(100) DEFAULT NULL,
  `published_role` varchar(100) DEFAULT NULL,
  `published_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_army_number` (`army_number`),
  KEY `idx_onco_status` (`onco_status`),
  KEY `idx_doc_status` (`doc_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `doc_leave_details`
--

LOCK TABLES `doc_leave_details` WRITE;
/*!40000 ALTER TABLE `doc_leave_details` DISABLE KEYS */;
/*!40000 ALTER TABLE `doc_leave_details` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `dues_in`
--

DROP TABLE IF EXISTS `dues_in`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dues_in` (
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
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dues_in`
--

LOCK TABLES `dues_in` WRITE;
/*!40000 ALTER TABLE `dues_in` DISABLE KEYS */;
/*!40000 ALTER TABLE `dues_in` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `dues_out`
--

DROP TABLE IF EXISTS `dues_out`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dues_out` (
  `id` int NOT NULL AUTO_INCREMENT,
  `army_number` varchar(50) NOT NULL,
  `rank` varchar(20) DEFAULT NULL,
  `trade` varchar(50) DEFAULT NULL,
  `name` varchar(100) DEFAULT NULL,
  `posted_to` varchar(100) DEFAULT NULL,
  `posting_order_no` varchar(100) DEFAULT NULL,
  `date_of_move` date DEFAULT NULL,
  `remarks` varchar(255) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dues_out`
--

LOCK TABLES `dues_out` WRITE;
/*!40000 ALTER TABLE `dues_out` DISABLE KEYS */;
/*!40000 ALTER TABLE `dues_out` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `expenditures`
--

DROP TABLE IF EXISTS `expenditures`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `expenditures` (
  `id` int NOT NULL AUTO_INCREMENT,
  `grant_id` int NOT NULL,
  `amount` decimal(15,2) NOT NULL,
  `remarks` text,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `financial_year` varchar(9) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `grant_id` (`grant_id`),
  CONSTRAINT `expenditures_ibfk_1` FOREIGN KEY (`grant_id`) REFERENCES `grants` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `expenditures`
--

LOCK TABLES `expenditures` WRITE;
/*!40000 ALTER TABLE `expenditures` DISABLE KEYS */;
/*!40000 ALTER TABLE `expenditures` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `family_members`
--

DROP TABLE IF EXISTS `family_members`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `family_members` (
  `id` int NOT NULL AUTO_INCREMENT,
  `personnel_id` int NOT NULL,
  `army_number` varchar(100) NOT NULL,
  `relation` varchar(100) DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  `date_of_birth` date DEFAULT NULL,
  `uid_no` varchar(50) DEFAULT NULL,
  `part_ii_order` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_army_number` (`army_number`),
  KEY `idx_personnel_id_family` (`personnel_id`),
  CONSTRAINT `family_members_ibfk_1` FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `family_members`
--

LOCK TABLES `family_members` WRITE;
/*!40000 ALTER TABLE `family_members` DISABLE KEYS */;
/*!40000 ALTER TABLE `family_members` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `gallery_settings`
--

DROP TABLE IF EXISTS `gallery_settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `gallery_settings` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(255) DEFAULT NULL,
  `subtitle` text,
  `image` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `gallery_settings`
--

LOCK TABLES `gallery_settings` WRITE;
/*!40000 ALTER TABLE `gallery_settings` DISABLE KEYS */;
/*!40000 ALTER TABLE `gallery_settings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `grant_allocations`
--

DROP TABLE IF EXISTS `grant_allocations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `grant_allocations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `grant_id` int NOT NULL,
  `amount` decimal(12,2) NOT NULL,
  `allocation_type` enum('Original','Additional') DEFAULT 'Additional',
  `remarks` varchar(255) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `financial_year` varchar(9) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `grant_id` (`grant_id`),
  CONSTRAINT `grant_allocations_ibfk_1` FOREIGN KEY (`grant_id`) REFERENCES `grants` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `grant_allocations`
--

LOCK TABLES `grant_allocations` WRITE;
/*!40000 ALTER TABLE `grant_allocations` DISABLE KEYS */;
/*!40000 ALTER TABLE `grant_allocations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `grants`
--

DROP TABLE IF EXISTS `grants`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `grants` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  `code_head` varchar(100) NOT NULL,
  `allotment` decimal(15,2) NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `financial_year` varchar(9) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `grants`
--

LOCK TABLES `grants` WRITE;
/*!40000 ALTER TABLE `grants` DISABLE KEYS */;
/*!40000 ALTER TABLE `grants` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `honours_board`
--

DROP TABLE IF EXISTS `honours_board`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `honours_board` (
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
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `honours_board`
--

LOCK TABLES `honours_board` WRITE;
/*!40000 ALTER TABLE `honours_board` DISABLE KEYS */;
/*!40000 ALTER TABLE `honours_board` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ideal_weights`
--

DROP TABLE IF EXISTS `ideal_weights`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ideal_weights` (
  `id` int NOT NULL AUTO_INCREMENT,
  `height_cm` int NOT NULL,
  `age_range` varchar(20) NOT NULL,
  `ideal_weight_kg` decimal(5,2) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ideal_weights`
--

LOCK TABLES `ideal_weights` WRITE;
/*!40000 ALTER TABLE `ideal_weights` DISABLE KEYS */;
/*!40000 ALTER TABLE `ideal_weights` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `jco_kunda_assignment`
--

DROP TABLE IF EXISTS `jco_kunda_assignment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `jco_kunda_assignment` (
  `id` int NOT NULL AUTO_INCREMENT,
  `army_number` varchar(50) NOT NULL,
  `additional_assigned_home_state` varchar(100) NOT NULL,
  `interview_status` enum('Pending','Done') DEFAULT 'Pending',
  `assigned_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `jco_kunda_assignment`
--

LOCK TABLES `jco_kunda_assignment` WRITE;
/*!40000 ALTER TABLE `jco_kunda_assignment` DISABLE KEYS */;
/*!40000 ALTER TABLE `jco_kunda_assignment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `leave_address`
--

DROP TABLE IF EXISTS `leave_address`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `leave_address` (
  `address_id` int NOT NULL AUTO_INCREMENT,
  `leave_request_id` int NOT NULL,
  `same_as_permanent` tinyint(1) DEFAULT '1',
  `address_line1` varchar(255) DEFAULT NULL,
  `address_line2` varchar(255) DEFAULT NULL,
  `city` varchar(100) DEFAULT NULL,
  `state` varchar(100) DEFAULT NULL,
  `pincode` varchar(20) DEFAULT NULL,
  `mobile` varchar(20) DEFAULT NULL,
  `alternate_contact` varchar(20) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`address_id`),
  KEY `leave_address_ibfk_1` (`leave_request_id`),
  CONSTRAINT `leave_address_ibfk_1` FOREIGN KEY (`leave_request_id`) REFERENCES `leave_status_info` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `leave_address`
--

LOCK TABLES `leave_address` WRITE;
/*!40000 ALTER TABLE `leave_address` DISABLE KEYS */;
/*!40000 ALTER TABLE `leave_address` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `leave_details`
--

DROP TABLE IF EXISTS `leave_details`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `leave_details` (
  `id` int NOT NULL AUTO_INCREMENT,
  `army_number` varchar(100) NOT NULL,
  `year` varchar(10) NOT NULL,
  `AL` int DEFAULT '0',
  `CL` int DEFAULT '0',
  `AAL` int DEFAULT '0',
  `PL` int DEFAULT '0',
  `remarks` text,
  `leave_start_date` date DEFAULT NULL,
  `leave_end_date` date DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `personnel_id` int DEFAULT NULL,
  `sr_no` int DEFAULT NULL,
  `Annual Leave` int DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `leave_details`
--

LOCK TABLES `leave_details` WRITE;
/*!40000 ALTER TABLE `leave_details` DISABLE KEYS */;
/*!40000 ALTER TABLE `leave_details` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `leave_history`
--

DROP TABLE IF EXISTS `leave_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `leave_history` (
  `id` int NOT NULL AUTO_INCREMENT,
  `leave_request_id` int NOT NULL,
  `army_number` varchar(50) NOT NULL,
  `name` varchar(50) NOT NULL,
  `leave_type` varchar(50) NOT NULL,
  `from_date` date NOT NULL,
  `to_date` date NOT NULL,
  `total_days` int NOT NULL,
  `recommended_by` varchar(100) NOT NULL,
  `status` varchar(50) NOT NULL DEFAULT 'Recommended by SEC NCO',
  `remarks` text,
  `recommended_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `reject_reason` text,
  `company` varchar(50) DEFAULT NULL,
  `star_remarks` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `leave_history`
--

LOCK TABLES `leave_history` WRITE;
/*!40000 ALTER TABLE `leave_history` DISABLE KEYS */;
/*!40000 ALTER TABLE `leave_history` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `leave_journey_legs`
--

DROP TABLE IF EXISTS `leave_journey_legs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `leave_journey_legs` (
  `leg_id` int NOT NULL AUTO_INCREMENT,
  `transport_id` int NOT NULL,
  `journey_type` enum('onward','return') NOT NULL,
  `leg_order` int NOT NULL,
  `from_station` varchar(100) NOT NULL,
  `to_station` varchar(100) NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`leg_id`),
  KEY `leave_journey_legs_ibfk_1` (`transport_id`),
  CONSTRAINT `leave_journey_legs_ibfk_1` FOREIGN KEY (`transport_id`) REFERENCES `leave_transport` (`transport_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `leave_journey_legs`
--

LOCK TABLES `leave_journey_legs` WRITE;
/*!40000 ALTER TABLE `leave_journey_legs` DISABLE KEYS */;
/*!40000 ALTER TABLE `leave_journey_legs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `leave_status_info`
--

DROP TABLE IF EXISTS `leave_status_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `leave_status_info` (
  `id` int NOT NULL AUTO_INCREMENT,
  `army_number` varchar(50) NOT NULL,
  `name` varchar(45) NOT NULL,
  `leave_type` varchar(50) NOT NULL,
  `leave_days` int NOT NULL,
  `from_date` date NOT NULL,
  `to_date` date NOT NULL,
  `request_sent_to` varchar(150) DEFAULT NULL,
  `request_status` varchar(50) DEFAULT 'Pending',
  `recommend_date` datetime DEFAULT NULL,
  `rejected_date` datetime DEFAULT NULL,
  `remarks` varchar(255) DEFAULT NULL,
  `leave_reason` text,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `reject_reason` text,
  `company` varchar(50) DEFAULT NULL,
  `prefix_date` date DEFAULT NULL,
  `suffix_date` date DEFAULT NULL,
  `prefix_days` int DEFAULT '0',
  `suffix_days` int DEFAULT '0',
  `rank` varchar(45) DEFAULT NULL,
  `reliever_army_number` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_leave_status_updated` (`request_status`,`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `leave_status_info`
--

LOCK TABLES `leave_status_info` WRITE;
/*!40000 ALTER TABLE `leave_status_info` DISABLE KEYS */;
/*!40000 ALTER TABLE `leave_status_info` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `leave_transport`
--

DROP TABLE IF EXISTS `leave_transport`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `leave_transport` (
  `transport_id` int NOT NULL AUTO_INCREMENT,
  `leave_request_id` int NOT NULL,
  `onward_mode` enum('Air','Train','') DEFAULT '',
  `onward_air_type` enum('Charter','Civil','') DEFAULT '',
  `onward_train_type` enum('CV Warrant','Free','') DEFAULT '',
  `return_mode` enum('Air','Train','') DEFAULT '',
  `return_air_type` enum('Charter','Civil','') DEFAULT '',
  `return_train_type` enum('CV Warrant','Free','') DEFAULT '',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`transport_id`),
  KEY `leave_transport_ibfk_1` (`leave_request_id`),
  CONSTRAINT `leave_transport_ibfk_1` FOREIGN KEY (`leave_request_id`) REFERENCES `leave_status_info` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `leave_transport`
--

LOCK TABLES `leave_transport` WRITE;
/*!40000 ALTER TABLE `leave_transport` DISABLE KEYS */;
/*!40000 ALTER TABLE `leave_transport` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `loans`
--

DROP TABLE IF EXISTS `loans`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `loans` (
  `id` int NOT NULL AUTO_INCREMENT,
  `personnel_id` int NOT NULL,
  `army_number` varchar(100) NOT NULL,
  `sr_no` int DEFAULT NULL,
  `loan_type` varchar(255) DEFAULT NULL,
  `total_amount` decimal(15,2) DEFAULT NULL,
  `bank_details` varchar(255) DEFAULT NULL,
  `emi_per_month` decimal(15,2) DEFAULT NULL,
  `pending` decimal(15,2) DEFAULT NULL,
  `remarks` text,
  PRIMARY KEY (`id`),
  KEY `idx_army_number` (`army_number`),
  KEY `idx_personnel_id_loans` (`personnel_id`),
  CONSTRAINT `loans_ibfk_1` FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `loans`
--

LOCK TABLES `loans` WRITE;
/*!40000 ALTER TABLE `loans` DISABLE KEYS */;
/*!40000 ALTER TABLE `loans` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `marital_discord_cases`
--

DROP TABLE IF EXISTS `marital_discord_cases`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `marital_discord_cases` (
  `id` int NOT NULL AUTO_INCREMENT,
  `personnel_id` int NOT NULL,
  `army_number` varchar(100) NOT NULL,
  `sr_no` int DEFAULT NULL,
  `case_no` varchar(100) DEFAULT NULL,
  `amount_to_pay` decimal(15,2) DEFAULT NULL,
  `sanction_letter_no` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_army_number` (`army_number`),
  KEY `idx_personnel_id_discord` (`personnel_id`),
  CONSTRAINT `marital_discord_cases_ibfk_1` FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `marital_discord_cases`
--

LOCK TABLES `marital_discord_cases` WRITE;
/*!40000 ALTER TABLE `marital_discord_cases` DISABLE KEYS */;
/*!40000 ALTER TABLE `marital_discord_cases` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `messages`
--

DROP TABLE IF EXISTS `messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `messages` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sender_id` int NOT NULL,
  `receiver_id` int NOT NULL,
  `message` text NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` enum('sent','read') DEFAULT 'sent',
  `file_type` varchar(255) DEFAULT NULL,
  `file_path` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `messages`
--

LOCK TABLES `messages` WRITE;
/*!40000 ALTER TABLE `messages` DISABLE KEYS */;
/*!40000 ALTER TABLE `messages` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `mobile_phones`
--

DROP TABLE IF EXISTS `mobile_phones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `mobile_phones` (
  `id` int NOT NULL AUTO_INCREMENT,
  `personnel_id` int NOT NULL,
  `army_number` varchar(100) NOT NULL,
  `sr_no` int DEFAULT NULL,
  `type` varchar(100) DEFAULT NULL,
  `number` varchar(50) DEFAULT NULL,
  `service_provider` varchar(100) DEFAULT NULL,
  `remarks` text,
  PRIMARY KEY (`id`),
  KEY `idx_army_number` (`army_number`),
  KEY `idx_personnel_id_mobiles` (`personnel_id`),
  CONSTRAINT `mobile_phones_ibfk_1` FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `mobile_phones`
--

LOCK TABLES `mobile_phones` WRITE;
/*!40000 ALTER TABLE `mobile_phones` DISABLE KEYS */;
/*!40000 ALTER TABLE `mobile_phones` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `monthly_medical_status`
--

DROP TABLE IF EXISTS `monthly_medical_status`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `monthly_medical_status` (
  `id` int NOT NULL AUTO_INCREMENT,
  `year` int NOT NULL,
  `month` tinyint NOT NULL,
  `unit` varchar(50) NOT NULL,
  `unfit_count` int DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_year_month_unit` (`year`,`month`,`unit`),
  KEY `idx_monthly_medical_unit` (`unit`,`year`,`month`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `monthly_medical_status`
--

LOCK TABLES `monthly_medical_status` WRITE;
/*!40000 ALTER TABLE `monthly_medical_status` DISABLE KEYS */;
INSERT INTO `monthly_medical_status` VALUES (1,2026,11,'All',0,'2026-11-04 12:43:51'),(2,2026,11,'COMN Company',0,'2026-11-04 12:43:51'),(3,2026,11,'3 Company',0,'2026-11-04 12:43:51'),(4,2026,11,'HQ company',0,'2026-11-04 12:43:51');
/*!40000 ALTER TABLE `monthly_medical_status` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `multi_leave_table`
--

DROP TABLE IF EXISTS `multi_leave_table`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `multi_leave_table` (
  `id` int NOT NULL AUTO_INCREMENT,
  `leave_request_id` int NOT NULL,
  `army_number` varchar(50) NOT NULL,
  `leave_type` varchar(20) NOT NULL,
  `leave_days` int NOT NULL,
  `from_date` date NOT NULL,
  `to_date` date NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `multi_leave_table`
--

LOCK TABLES `multi_leave_table` WRITE;
/*!40000 ALTER TABLE `multi_leave_table` DISABLE KEYS */;
/*!40000 ALTER TABLE `multi_leave_table` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `parade_state_daily`
--

DROP TABLE IF EXISTS `parade_state_daily`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `parade_state_daily` (
  `id` int NOT NULL AUTO_INCREMENT,
  `report_date` date NOT NULL,
  `company` varchar(100) NOT NULL,
  `offr_auth` int DEFAULT '0',
  `offr_hs` int DEFAULT '0',
  `offr_posted_str` int DEFAULT '0',
  `offr_lve` int DEFAULT '0',
  `offr_course` int DEFAULT '0',
  `offr_det` int DEFAULT '0',
  `offr_mh` int DEFAULT '0',
  `offr_sick_lve` int DEFAULT '0',
  `offr_ex` int DEFAULT '0',
  `offr_td` int DEFAULT '0',
  `offr_att` int DEFAULT '0',
  `offr_awl_osl_jc` int DEFAULT '0',
  `offr_trout_det` int DEFAULT '0',
  `offr_present_det` int DEFAULT '0',
  `offr_present_unit` int DEFAULT '0',
  `offr_dues_in` int DEFAULT '0',
  `offr_dues_out` int DEFAULT '0',
  `jco_auth` int DEFAULT '0',
  `jco_hs` int DEFAULT '0',
  `jco_posted_str` int DEFAULT '0',
  `jco_lve` int DEFAULT '0',
  `jco_course` int DEFAULT '0',
  `jco_det` int DEFAULT '0',
  `jco_mh` int DEFAULT '0',
  `jco_sick_lve` int DEFAULT '0',
  `jco_ex` int DEFAULT '0',
  `jco_td` int DEFAULT '0',
  `jco_att` int DEFAULT '0',
  `jco_awl_osl_jc` int DEFAULT '0',
  `jco_trout_det` int DEFAULT '0',
  `jco_present_det` int DEFAULT '0',
  `jco_present_unit` int DEFAULT '0',
  `jco_dues_in` int DEFAULT '0',
  `jco_dues_out` int DEFAULT '0',
  `jcoEre_auth` int DEFAULT '0',
  `jcoEre_hs` int DEFAULT '0',
  `jcoEre_posted_str` int DEFAULT '0',
  `jcoEre_lve` int DEFAULT '0',
  `jcoEre_course` int DEFAULT '0',
  `jcoEre_det` int DEFAULT '0',
  `jcoEre_mh` int DEFAULT '0',
  `jcoEre_sick_lve` int DEFAULT '0',
  `jcoEre_ex` int DEFAULT '0',
  `jcoEre_td` int DEFAULT '0',
  `jcoEre_att` int DEFAULT '0',
  `jcoEre_awl_osl_jc` int DEFAULT '0',
  `jcoEre_trout_det` int DEFAULT '0',
  `jcoEre_present_det` int DEFAULT '0',
  `jcoEre_present_unit` int DEFAULT '0',
  `jcoEre_dues_in` int DEFAULT '0',
  `jcoEre_dues_out` int DEFAULT '0',
  `or_auth` int DEFAULT '0',
  `or_hs` int DEFAULT '0',
  `or_posted_str` int DEFAULT '0',
  `or_lve` int DEFAULT '0',
  `or_course` int DEFAULT '0',
  `or_det` int DEFAULT '0',
  `or_mh` int DEFAULT '0',
  `or_sick_lve` int DEFAULT '0',
  `or_ex` int DEFAULT '0',
  `or_td` int DEFAULT '0',
  `or_att` int DEFAULT '0',
  `or_awl_osl_jc` int DEFAULT '0',
  `or_trout_det` int DEFAULT '0',
  `or_present_det` int DEFAULT '0',
  `or_present_unit` int DEFAULT '0',
  `or_dues_in` int DEFAULT '0',
  `or_dues_out` int DEFAULT '0',
  `orEre_auth` int DEFAULT '0',
  `orEre_hs` int DEFAULT '0',
  `orEre_posted_str` int DEFAULT '0',
  `orEre_lve` int DEFAULT '0',
  `orEre_course` int DEFAULT '0',
  `orEre_det` int DEFAULT '0',
  `orEre_mh` int DEFAULT '0',
  `orEre_sick_lve` int DEFAULT '0',
  `orEre_ex` int DEFAULT '0',
  `orEre_td` int DEFAULT '0',
  `orEre_att` int DEFAULT '0',
  `orEre_awl_osl_jc` int DEFAULT '0',
  `orEre_trout_det` int DEFAULT '0',
  `orEre_present_det` int DEFAULT '0',
  `orEre_present_unit` int DEFAULT '0',
  `orEre_dues_in` int DEFAULT '0',
  `orEre_dues_out` int DEFAULT '0',
  `firstTotal_auth` int DEFAULT '0',
  `firstTotal_hs` int DEFAULT '0',
  `firstTotal_posted_str` int DEFAULT '0',
  `firstTotal_lve` int DEFAULT '0',
  `firstTotal_course` int DEFAULT '0',
  `firstTotal_det` int DEFAULT '0',
  `firstTotal_mh` int DEFAULT '0',
  `firstTotal_sick_lve` int DEFAULT '0',
  `firstTotal_ex` int DEFAULT '0',
  `firstTotal_td` int DEFAULT '0',
  `firstTotal_att` int DEFAULT '0',
  `firstTotal_awl_osl_jc` int DEFAULT '0',
  `firstTotal_trout_det` int DEFAULT '0',
  `firstTotal_present_det` int DEFAULT '0',
  `firstTotal_present_unit` int DEFAULT '0',
  `firstTotal_dues_in` int DEFAULT '0',
  `firstTotal_dues_out` int DEFAULT '0',
  `oaOr_auth` int DEFAULT '0',
  `oaOr_hs` int DEFAULT '0',
  `oaOr_posted_str` int DEFAULT '0',
  `oaOr_lve` int DEFAULT '0',
  `oaOr_course` int DEFAULT '0',
  `oaOr_det` int DEFAULT '0',
  `oaOr_mh` int DEFAULT '0',
  `oaOr_sick_lve` int DEFAULT '0',
  `oaOr_ex` int DEFAULT '0',
  `oaOr_td` int DEFAULT '0',
  `oaOr_att` int DEFAULT '0',
  `oaOr_awl_osl_jc` int DEFAULT '0',
  `oaOr_trout_det` int DEFAULT '0',
  `oaOr_present_det` int DEFAULT '0',
  `oaOr_present_unit` int DEFAULT '0',
  `oaOr_dues_in` int DEFAULT '0',
  `oaOr_dues_out` int DEFAULT '0',
  `attSummary_auth` int DEFAULT '0',
  `attSummary_hs` int DEFAULT '0',
  `attSummary_posted_str` int DEFAULT '0',
  `attSummary_lve` int DEFAULT '0',
  `attSummary_course` int DEFAULT '0',
  `attSummary_det` int DEFAULT '0',
  `attSummary_mh` int DEFAULT '0',
  `attSummary_sick_lve` int DEFAULT '0',
  `attSummary_ex` int DEFAULT '0',
  `attSummary_td` int DEFAULT '0',
  `attSummary_att` int DEFAULT '0',
  `attSummary_awl_osl_jc` int DEFAULT '0',
  `attSummary_trout_det` int DEFAULT '0',
  `attSummary_present_det` int DEFAULT '0',
  `attSummary_present_unit` int DEFAULT '0',
  `attSummary_dues_in` int DEFAULT '0',
  `attSummary_dues_out` int DEFAULT '0',
  `attOffr_auth` int DEFAULT '0',
  `attOffr_hs` int DEFAULT '0',
  `attOffr_posted_str` int DEFAULT '0',
  `attOffr_lve` int DEFAULT '0',
  `attOffr_course` int DEFAULT '0',
  `attOffr_det` int DEFAULT '0',
  `attOffr_mh` int DEFAULT '0',
  `attOffr_sick_lve` int DEFAULT '0',
  `attOffr_ex` int DEFAULT '0',
  `attOffr_td` int DEFAULT '0',
  `attOffr_att` int DEFAULT '0',
  `attOffr_awl_osl_jc` int DEFAULT '0',
  `attOffr_trout_det` int DEFAULT '0',
  `attOffr_present_det` int DEFAULT '0',
  `attOffr_present_unit` int DEFAULT '0',
  `attOffr_dues_in` int DEFAULT '0',
  `attOffr_dues_out` int DEFAULT '0',
  `attJco_auth` int DEFAULT '0',
  `attJco_hs` int DEFAULT '0',
  `attJco_posted_str` int DEFAULT '0',
  `attJco_lve` int DEFAULT '0',
  `attJco_course` int DEFAULT '0',
  `attJco_det` int DEFAULT '0',
  `attJco_mh` int DEFAULT '0',
  `attJco_sick_lve` int DEFAULT '0',
  `attJco_ex` int DEFAULT '0',
  `attJco_td` int DEFAULT '0',
  `attJco_att` int DEFAULT '0',
  `attJco_awl_osl_jc` int DEFAULT '0',
  `attJco_trout_det` int DEFAULT '0',
  `attJco_present_det` int DEFAULT '0',
  `attJco_present_unit` int DEFAULT '0',
  `attJco_dues_in` int DEFAULT '0',
  `attJco_dues_out` int DEFAULT '0',
  `attOr_auth` int DEFAULT '0',
  `attOr_hs` int DEFAULT '0',
  `attOr_posted_str` int DEFAULT '0',
  `attOr_lve` int DEFAULT '0',
  `attOr_course` int DEFAULT '0',
  `attOr_det` int DEFAULT '0',
  `attOr_mh` int DEFAULT '0',
  `attOr_sick_lve` int DEFAULT '0',
  `attOr_ex` int DEFAULT '0',
  `attOr_td` int DEFAULT '0',
  `attOr_att` int DEFAULT '0',
  `attOr_awl_osl_jc` int DEFAULT '0',
  `attOr_trout_det` int DEFAULT '0',
  `attOr_present_det` int DEFAULT '0',
  `attOr_present_unit` int DEFAULT '0',
  `attOr_dues_in` int DEFAULT '0',
  `attOr_dues_out` int DEFAULT '0',
  `secondTotal_auth` int DEFAULT '0',
  `secondTotal_hs` int DEFAULT '0',
  `secondTotal_posted_str` int DEFAULT '0',
  `secondTotal_lve` int DEFAULT '0',
  `secondTotal_course` int DEFAULT '0',
  `secondTotal_det` int DEFAULT '0',
  `secondTotal_mh` int DEFAULT '0',
  `secondTotal_sick_lve` int DEFAULT '0',
  `secondTotal_ex` int DEFAULT '0',
  `secondTotal_td` int DEFAULT '0',
  `secondTotal_att` int DEFAULT '0',
  `secondTotal_awl_osl_jc` int DEFAULT '0',
  `secondTotal_trout_det` int DEFAULT '0',
  `secondTotal_present_det` int DEFAULT '0',
  `secondTotal_present_unit` int DEFAULT '0',
  `secondTotal_dues_in` int DEFAULT '0',
  `secondTotal_dues_out` int DEFAULT '0',
  `grandTotal_auth` int DEFAULT '0',
  `grandTotal_hs` int DEFAULT '0',
  `grandTotal_posted_str` int DEFAULT '0',
  `grandTotal_lve` int DEFAULT '0',
  `grandTotal_course` int DEFAULT '0',
  `grandTotal_det` int DEFAULT '0',
  `grandTotal_mh` int DEFAULT '0',
  `grandTotal_sick_lve` int DEFAULT '0',
  `grandTotal_ex` int DEFAULT '0',
  `grandTotal_td` int DEFAULT '0',
  `grandTotal_att` int DEFAULT '0',
  `grandTotal_awl_osl_jc` int DEFAULT '0',
  `grandTotal_trout_det` int DEFAULT '0',
  `grandTotal_present_det` int DEFAULT '0',
  `grandTotal_present_unit` int DEFAULT '0',
  `grandTotal_dues_in` int DEFAULT '0',
  `grandTotal_dues_out` int DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_company_date` (`company`,`report_date`),
  KEY `idx_company` (`company`),
  KEY `idx_date` (`report_date`),
  KEY `idx_company_date` (`company`,`report_date`),
  KEY `idx_parade_state_date_company` (`report_date`,`company`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `parade_state_daily`
--

LOCK TABLES `parade_state_daily` WRITE;
/*!40000 ALTER TABLE `parade_state_daily` DISABLE KEYS */;
/*!40000 ALTER TABLE `parade_state_daily` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pending_case_remarks`
--

DROP TABLE IF EXISTS `pending_case_remarks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pending_case_remarks` (
  `id` int NOT NULL AUTO_INCREMENT,
  `case_id` int NOT NULL,
  `remark` text NOT NULL,
  `remarked_by` varchar(150) DEFAULT NULL,
  `remarked_by_role` varchar(100) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_case_id` (`case_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pending_case_remarks`
--

LOCK TABLES `pending_case_remarks` WRITE;
/*!40000 ALTER TABLE `pending_case_remarks` DISABLE KEYS */;
/*!40000 ALTER TABLE `pending_case_remarks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pending_cases`
--

DROP TABLE IF EXISTS `pending_cases`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pending_cases` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type_of_case` varchar(100) NOT NULL,
  `pending_last_week` int DEFAULT '0',
  `recd_current_week` int DEFAULT '0',
  `pub_this_week` int DEFAULT '0',
  `total_cases` int DEFAULT '0',
  `under_prog` int DEFAULT '0',
  `remarks` text,
  `updated_by` varchar(100) DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `sort_order` int DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pending_cases`
--

LOCK TABLES `pending_cases` WRITE;
/*!40000 ALTER TABLE `pending_cases` DISABLE KEYS */;
INSERT INTO `pending_cases` VALUES (1,'Posting IN',0,0,0,0,0,NULL,NULL,'2026-11-04 18:13:51',1),(2,'Posting OUT',0,0,0,0,0,NULL,NULL,'2026-11-04 18:13:51',2),(3,'Pension Out',0,0,0,0,0,NULL,NULL,'2026-11-04 18:13:51',3),(4,'TPTL',0,0,0,0,0,NULL,NULL,'2026-11-04 18:13:51',4),(5,'Lve',0,0,0,0,0,NULL,NULL,'2026-11-04 18:13:51',5),(6,'TFRGTH',0,0,0,0,0,NULL,NULL,'2026-11-04 18:13:51',6),(7,'HRA',0,0,0,0,0,NULL,NULL,'2026-11-04 18:13:51',7),(8,'RUMCIG',0,0,0,0,0,NULL,NULL,'2026-11-04 18:13:51',8),(9,'PRPLVE/JRNYD',0,0,0,0,0,NULL,NULL,'2026-11-04 18:13:51',9),(10,'Medal',0,0,0,0,0,NULL,NULL,'2026-11-04 18:13:51',10),(11,'Med Cat',0,0,0,0,0,NULL,NULL,'2026-11-04 18:13:51',11),(12,'CEA',0,0,0,0,0,NULL,NULL,'2026-11-04 18:13:51',12),(13,'Marriage/Divorce',0,0,0,0,0,NULL,NULL,'2026-11-04 18:13:51',13),(14,'Change of Name',0,0,0,0,0,NULL,NULL,'2026-11-04 18:13:51',14),(15,'Birth',0,0,0,0,0,NULL,NULL,'2026-11-04 18:13:51',15),(16,'Demise',0,0,0,0,0,NULL,NULL,'2026-11-04 18:13:51',16),(17,'Civ Edn/MILEDN',0,0,0,0,0,NULL,NULL,'2026-11-04 18:13:51',17),(18,'ACCLVE',0,0,0,0,0,NULL,NULL,'2026-11-04 18:13:51',18),(19,'UID/PAN',0,0,0,0,0,NULL,NULL,'2026-11-04 18:13:51',19),(20,'Jt Acct',0,0,0,0,0,NULL,NULL,'2026-11-04 18:13:51',20),(21,'OPTFIX',0,0,0,0,0,NULL,NULL,'2026-11-04 18:13:51',21),(22,'PFWDL',0,0,0,0,0,NULL,NULL,'2026-11-04 18:13:51',22),(23,'Mobile No/Email',0,0,0,0,0,NULL,NULL,'2026-11-04 18:13:51',23),(24,'Change Address',0,0,0,0,0,NULL,NULL,'2026-11-04 18:13:51',24),(25,'Injury Report',0,0,0,0,0,NULL,NULL,'2026-11-04 18:13:51',25),(26,'Hosp Adm/Tfr/Disch',0,0,0,0,0,NULL,NULL,'2026-11-04 18:13:51',26),(27,'PROVFS',0,0,0,0,0,NULL,NULL,'2026-11-04 18:13:51',27),(28,'LTC',0,0,0,0,0,NULL,NULL,'2026-11-04 18:13:51',28),(29,'RISK',0,0,0,0,0,NULL,NULL,'2026-11-04 18:13:51',29),(30,'HAUCA',0,0,0,0,0,NULL,NULL,'2026-11-04 18:13:51',30);
/*!40000 ALTER TABLE `pending_cases` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pending_cases_company_recd`
--

DROP TABLE IF EXISTS `pending_cases_company_recd`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pending_cases_company_recd` (
  `id` int NOT NULL AUTO_INCREMENT,
  `case_id` int NOT NULL,
  `company` varchar(100) NOT NULL,
  `recd_count` int NOT NULL DEFAULT '0',
  `updated_by` varchar(100) DEFAULT NULL,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_case_company` (`case_id`,`company`),
  KEY `idx_company` (`company`),
  CONSTRAINT `fk_pccr_case` FOREIGN KEY (`case_id`) REFERENCES `pending_cases` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pending_cases_company_recd`
--

LOCK TABLES `pending_cases_company_recd` WRITE;
/*!40000 ALTER TABLE `pending_cases_company_recd` DISABLE KEYS */;
/*!40000 ALTER TABLE `pending_cases_company_recd` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pending_cases_weekly_history`
--

DROP TABLE IF EXISTS `pending_cases_weekly_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pending_cases_weekly_history` (
  `id` int NOT NULL AUTO_INCREMENT,
  `case_id` int DEFAULT NULL,
  `type_of_case` varchar(100) NOT NULL,
  `week_identifier` varchar(30) NOT NULL,
  `week_start_date` date NOT NULL,
  `week_end_date` date NOT NULL,
  `pending_last_week` int DEFAULT '0',
  `recd_current_week` int DEFAULT '0',
  `total_cases` int DEFAULT '0',
  `pub_this_week` int DEFAULT '0',
  `under_prog` int DEFAULT '0',
  `remarks` text,
  `rollover_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_case_week` (`type_of_case`,`week_identifier`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pending_cases_weekly_history`
--

LOCK TABLES `pending_cases_weekly_history` WRITE;
/*!40000 ALTER TABLE `pending_cases_weekly_history` DISABLE KEYS */;
/*!40000 ALTER TABLE `pending_cases_weekly_history` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `personnel`
--

DROP TABLE IF EXISTS `personnel`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `personnel` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `army_number` varchar(100) DEFAULT NULL,
  `rank` varchar(100) DEFAULT NULL,
  `trade` varchar(100) DEFAULT NULL,
  `date_of_enrollment` date NOT NULL,
  `date_of_birth` date NOT NULL,
  `date_of_tos` date DEFAULT NULL,
  `date_of_tors` date DEFAULT NULL,
  `blood_group` varchar(10) DEFAULT NULL,
  `religion` varchar(100) DEFAULT NULL,
  `food_preference` varchar(50) DEFAULT NULL,
  `drinker` varchar(10) DEFAULT NULL,
  `civ_qualifications` text,
  `decoration_awards` text,
  `lacking_qualifications` text,
  `willing_promotions` varchar(10) DEFAULT NULL,
  `i_card_no` varchar(100) DEFAULT NULL,
  `i_card_date` date DEFAULT NULL,
  `i_card_issued_by` varchar(255) DEFAULT NULL,
  `bpet_grading` varchar(50) DEFAULT NULL,
  `ppt_grading` varchar(50) DEFAULT NULL,
  `bpet_date` date DEFAULT NULL,
  `clothing_card` varchar(10) DEFAULT NULL,
  `pan_card_no` varchar(50) DEFAULT NULL,
  `pan_part_ii` varchar(100) DEFAULT NULL,
  `aadhar_card_no` varchar(20) DEFAULT NULL,
  `aadhar_part_ii` varchar(100) DEFAULT NULL,
  `joint_account_no` varchar(100) DEFAULT NULL,
  `joint_account_bank` varchar(255) DEFAULT NULL,
  `joint_account_ifsc` varchar(20) DEFAULT NULL,
  `home_house_no` varchar(255) DEFAULT NULL,
  `home_village` varchar(255) DEFAULT NULL,
  `home_phone` varchar(50) DEFAULT NULL,
  `home_to` varchar(255) DEFAULT NULL,
  `home_po` varchar(255) DEFAULT NULL,
  `home_ps` varchar(255) DEFAULT NULL,
  `home_teh` varchar(255) DEFAULT NULL,
  `home_nrs` varchar(255) DEFAULT NULL,
  `home_nmh` varchar(255) DEFAULT NULL,
  `home_district` varchar(255) DEFAULT NULL,
  `home_state` varchar(255) DEFAULT NULL,
  `border_area` varchar(50) DEFAULT NULL,
  `distance_from_ib` decimal(10,2) DEFAULT NULL,
  `height` decimal(10,2) DEFAULT NULL,
  `weight` decimal(10,2) DEFAULT NULL,
  `chest` decimal(10,2) DEFAULT NULL,
  `identification_marks` varchar(255) DEFAULT NULL,
  `court_cases` text,
  `loan` varchar(50) DEFAULT NULL,
  `total_leaves_encashed` int DEFAULT NULL,
  `participation_activities` text,
  `present_family_location` text,
  `prior_station` varchar(50) DEFAULT NULL,
  `prior_station_date` date DEFAULT NULL,
  `worked_it` varchar(50) DEFAULT NULL,
  `worked_unit_tenure` varchar(255) DEFAULT NULL,
  `med_cat` varchar(50) DEFAULT NULL,
  `last_recat_bd_date` date DEFAULT NULL,
  `last_recat_bd_at` varchar(255) DEFAULT NULL,
  `next_recat_due` date DEFAULT NULL,
  `medical_problem` text,
  `restrictions` text,
  `computer_knowledge` varchar(50) DEFAULT NULL,
  `it_literature` varchar(50) DEFAULT NULL,
  `kin_name` varchar(255) DEFAULT NULL,
  `kin_relation` varchar(100) DEFAULT NULL,
  `kin_marriage_date` date DEFAULT NULL,
  `kin_account_no` varchar(100) DEFAULT NULL,
  `kin_bank` varchar(255) DEFAULT NULL,
  `kin_ifsc` varchar(20) DEFAULT NULL,
  `kin_part_ii` varchar(100) DEFAULT NULL,
  `vehicle_reg_no` varchar(100) DEFAULT NULL,
  `vehicle_model` varchar(255) DEFAULT NULL,
  `vehicle_purchase_date` date DEFAULT NULL,
  `vehicle_agif` varchar(50) DEFAULT NULL,
  `driving_license_no` varchar(100) DEFAULT NULL,
  `license_issue_date` date DEFAULT NULL,
  `license_expiry_date` date DEFAULT NULL,
  `disability_child` varchar(50) DEFAULT NULL,
  `marital_discord` varchar(50) DEFAULT NULL,
  `counselling` text,
  `folder_prepared_on` date DEFAULT NULL,
  `folder_checked_by` varchar(255) DEFAULT NULL,
  `bring_family` varchar(50) DEFAULT NULL,
  `domestic_issues` text,
  `other_requests` text,
  `family_medical_issues` text,
  `quality_points` text,
  `strengths` text,
  `weaknesses` text,
  `detailed_course` varchar(255) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `company` varchar(100) DEFAULT NULL,
  `onleave_status` tinyint(1) DEFAULT '0',
  `detachment_status` tinyint(1) DEFAULT '0',
  `posting_status` tinyint(1) DEFAULT '0',
  `personnel_status` varchar(110) DEFAULT NULL,
  `personnel_remarks` varchar(100) DEFAULT NULL,
  `td_status` tinyint(1) DEFAULT '0',
  `interview_status` tinyint(1) DEFAULT '0',
  `batch` varchar(50) DEFAULT NULL,
  `section` varchar(100) DEFAULT NULL,
  `interview_remarks` varchar(345) DEFAULT NULL,
  `temp_interview_done_by` varchar(45) DEFAULT NULL,
  `oncourse_status` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `army_number` (`army_number`),
  KEY `idx_personnel_army_number` (`army_number`),
  KEY `idx_personnel_name` (`name`),
  KEY `idx_personnel_rank` (`rank`),
  KEY `idx_personnel_rank_category` (`rank`),
  KEY `idx_detachment_status` (`detachment_status`),
  KEY `idx_personnel_company_rank` (`company`,`rank`),
  KEY `idx_personnel_interview_status` (`interview_status`),
  KEY `idx_personnel_army_company` (`army_number`,`company`),
  KEY `idx_personnel_company` (`company`),
  KEY `idx_personnel_det_status` (`detachment_status`),
  KEY `idx_personnel_det_status_company` (`detachment_status`,`company`,`army_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `personnel`
--

LOCK TABLES `personnel` WRITE;
/*!40000 ALTER TABLE `personnel` DISABLE KEYS */;
/*!40000 ALTER TABLE `personnel` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `personnel_sports`
--

DROP TABLE IF EXISTS `personnel_sports`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `personnel_sports` (
  `id` int NOT NULL AUTO_INCREMENT,
  `personnel_id` int NOT NULL,
  `army_number` varchar(50) NOT NULL,
  `sport_type` varchar(50) NOT NULL,
  `sport_name` varchar(100) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `personnel_sports`
--

LOCK TABLES `personnel_sports` WRITE;
/*!40000 ALTER TABLE `personnel_sports` DISABLE KEYS */;
/*!40000 ALTER TABLE `personnel_sports` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `posting_details_table`
--

DROP TABLE IF EXISTS `posting_details_table`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `posting_details_table` (
  `id` int NOT NULL AUTO_INCREMENT,
  `army_number` varchar(15) NOT NULL,
  `location_posted_to` varchar(10) NOT NULL,
  `posting_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `army_number` (`army_number`),
  CONSTRAINT `posting_details_table_ibfk_1` FOREIGN KEY (`army_number`) REFERENCES `personnel` (`army_number`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `posting_details_table`
--

LOCK TABLES `posting_details_table` WRITE;
/*!40000 ALTER TABLE `posting_details_table` DISABLE KEYS */;
/*!40000 ALTER TABLE `posting_details_table` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `project_bill_of_materials`
--

DROP TABLE IF EXISTS `project_bill_of_materials`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `project_bill_of_materials` (
  `id` int NOT NULL AUTO_INCREMENT,
  `project_id` int DEFAULT NULL,
  `project_title` varchar(255) NOT NULL,
  `project_head` varchar(255) NOT NULL,
  `nomenclature` varchar(255) NOT NULL,
  `au` varchar(50) DEFAULT NULL,
  `qty` int DEFAULT '0',
  `rate` decimal(12,2) DEFAULT '0.00',
  `total_cost` decimal(12,2) DEFAULT '0.00',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `project_id` (`project_id`),
  CONSTRAINT `project_bill_of_materials_ibfk_1` FOREIGN KEY (`project_id`) REFERENCES `projects` (`project_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `project_bill_of_materials`
--

LOCK TABLES `project_bill_of_materials` WRITE;
/*!40000 ALTER TABLE `project_bill_of_materials` DISABLE KEYS */;
/*!40000 ALTER TABLE `project_bill_of_materials` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `project_heads`
--

DROP TABLE IF EXISTS `project_heads`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `project_heads` (
  `id` int NOT NULL AUTO_INCREMENT,
  `head_name` varchar(100) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `head_name` (`head_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `project_heads`
--

LOCK TABLES `project_heads` WRITE;
/*!40000 ALTER TABLE `project_heads` DISABLE KEYS */;
/*!40000 ALTER TABLE `project_heads` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `project_history`
--

DROP TABLE IF EXISTS `project_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `project_history` (
  `history_id` int NOT NULL AUTO_INCREMENT,
  `project_id` int NOT NULL,
  `stage` varchar(100) NOT NULL,
  `notes` text,
  `updated_by` varchar(200) DEFAULT NULL,
  `updated_date` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`history_id`),
  KEY `project_id` (`project_id`),
  CONSTRAINT `project_history_ibfk_1` FOREIGN KEY (`project_id`) REFERENCES `projects` (`project_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `project_history`
--

LOCK TABLES `project_history` WRITE;
/*!40000 ALTER TABLE `project_history` DISABLE KEYS */;
/*!40000 ALTER TABLE `project_history` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `projects`
--

DROP TABLE IF EXISTS `projects`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `projects` (
  `project_id` int NOT NULL AUTO_INCREMENT,
  `project_name` varchar(255) NOT NULL,
  `current_stage` varchar(255) DEFAULT NULL,
  `project_cost` varchar(255) DEFAULT NULL,
  `project_items` varchar(255) DEFAULT NULL,
  `quantity` int DEFAULT NULL,
  `project_description` text,
  `created_on` datetime DEFAULT CURRENT_TIMESTAMP,
  `head` varchar(100) NOT NULL,
  `company` varchar(50) DEFAULT NULL,
  `updated_date` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `updated_by` varchar(200) DEFAULT NULL,
  `deadline` date DEFAULT NULL,
  `status` varchar(50) DEFAULT 'Active',
  PRIMARY KEY (`project_id`),
  KEY `idx_projects_company` (`company`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `projects`
--

LOCK TABLES `projects` WRITE;
/*!40000 ALTER TABLE `projects` DISABLE KEYS */;
/*!40000 ALTER TABLE `projects` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `punishments`
--

DROP TABLE IF EXISTS `punishments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `punishments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `personnel_id` int NOT NULL,
  `army_number` varchar(100) NOT NULL,
  `sr_no` int DEFAULT NULL,
  `punishment_date` date DEFAULT NULL,
  `punishment` varchar(255) DEFAULT NULL,
  `aa_sec` varchar(100) DEFAULT NULL,
  `remarks` text,
  PRIMARY KEY (`id`),
  KEY `idx_army_number` (`army_number`),
  KEY `idx_personnel_id_punishments` (`personnel_id`),
  CONSTRAINT `punishments_ibfk_1` FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `punishments`
--

LOCK TABLES `punishments` WRITE;
/*!40000 ALTER TABLE `punishments` DISABLE KEYS */;
/*!40000 ALTER TABLE `punishments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `roll_call_points`
--

DROP TABLE IF EXISTS `roll_call_points`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `roll_call_points` (
  `id` int NOT NULL AUTO_INCREMENT,
  `category` varchar(20) NOT NULL,
  `point_title` varchar(100) NOT NULL,
  `point_description` text NOT NULL,
  `army_number` varchar(50) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(20) DEFAULT NULL,
  `remarks` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_rollcall_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `roll_call_points`
--

LOCK TABLES `roll_call_points` WRITE;
/*!40000 ALTER TABLE `roll_call_points` DISABLE KEYS */;
/*!40000 ALTER TABLE `roll_call_points` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sales`
--

DROP TABLE IF EXISTS `sales`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sales` (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL,
  `liquor_sale` int NOT NULL,
  `grocery_sale` int NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sales`
--

LOCK TABLES `sales` WRITE;
/*!40000 ALTER TABLE `sales` DISABLE KEYS */;
/*!40000 ALTER TABLE `sales` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sanction_orders`
--

DROP TABLE IF EXISTS `sanction_orders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sanction_orders` (
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
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sanction_orders`
--

LOCK TABLES `sanction_orders` WRITE;
/*!40000 ALTER TABLE `sanction_orders` DISABLE KEYS */;
/*!40000 ALTER TABLE `sanction_orders` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `schedules`
--

DROP TABLE IF EXISTS `schedules`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `schedules` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `location` varchar(255) DEFAULT NULL,
  `schedule_date` date NOT NULL,
  `start_time` time NOT NULL,
  `end_time` time DEFAULT NULL,
  `status` enum('upcoming','ongoing','completed','cancelled') DEFAULT 'upcoming',
  `priority` int DEFAULT '0',
  `created_by` varchar(100) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_schedules_date` (`schedule_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `schedules`
--

LOCK TABLES `schedules` WRITE;
/*!40000 ALTER TABLE `schedules` DISABLE KEYS */;
/*!40000 ALTER TABLE `schedules` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sensitive_marking`
--

DROP TABLE IF EXISTS `sensitive_marking`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sensitive_marking` (
  `id` int NOT NULL AUTO_INCREMENT,
  `army_number` varchar(100) DEFAULT NULL,
  `reason` text,
  `marked_on` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_sensitive_marking_army` (`army_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sensitive_marking`
--

LOCK TABLES `sensitive_marking` WRITE;
/*!40000 ALTER TABLE `sensitive_marking` DISABLE KEYS */;
/*!40000 ALTER TABLE `sensitive_marking` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sensitive_reason_log`
--

DROP TABLE IF EXISTS `sensitive_reason_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sensitive_reason_log` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `army_number` varchar(50) NOT NULL,
  `reason` text NOT NULL,
  `added_by` varchar(100) NOT NULL,
  `added_by_role` varchar(50) DEFAULT NULL,
  `added_on` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  KEY `idx_sensitive_log_army_date` (`army_number`,`added_on`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sensitive_reason_log`
--

LOCK TABLES `sensitive_reason_log` WRITE;
/*!40000 ALTER TABLE `sensitive_reason_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `sensitive_reason_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `store_items`
--

DROP TABLE IF EXISTS `store_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `store_items` (
  `item_id` int NOT NULL AUTO_INCREMENT,
  `store_id` int DEFAULT NULL,
  `qlp_no` varchar(50) DEFAULT NULL,
  `slp_no` varchar(50) DEFAULT NULL,
  `nomenclature` varchar(200) DEFAULT NULL,
  `au` varchar(20) DEFAULT NULL,
  `quantity` int DEFAULT NULL,
  PRIMARY KEY (`item_id`),
  KEY `store_id` (`store_id`),
  CONSTRAINT `store_items_ibfk_1` FOREIGN KEY (`store_id`) REFERENCES `stores` (`store_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `store_items`
--

LOCK TABLES `store_items` WRITE;
/*!40000 ALTER TABLE `store_items` DISABLE KEYS */;
/*!40000 ALTER TABLE `store_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `stores`
--

DROP TABLE IF EXISTS `stores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `stores` (
  `store_id` int NOT NULL AUTO_INCREMENT,
  `store_name` varchar(100) NOT NULL,
  `place` varchar(100) DEFAULT NULL,
  `incharge_name` varchar(100) DEFAULT NULL,
  `total_items` int DEFAULT '0',
  PRIMARY KEY (`store_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stores`
--

LOCK TABLES `stores` WRITE;
/*!40000 ALTER TABLE `stores` DISABLE KEYS */;
/*!40000 ALTER TABLE `stores` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `system_settings`
--

DROP TABLE IF EXISTS `system_settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `system_settings` (
  `id` int NOT NULL AUTO_INCREMENT,
  `setting_key` varchar(100) NOT NULL,
  `setting_value` text,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `setting_key` (`setting_key`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `system_settings`
--

LOCK TABLES `system_settings` WRITE;
/*!40000 ALTER TABLE `system_settings` DISABLE KEYS */;
INSERT INTO `system_settings` VALUES (1,'last_part2_rollover_week','2026-W45','2026-11-04 12:43:51');
/*!40000 ALTER TABLE `system_settings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tasks`
--

DROP TABLE IF EXISTS `tasks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tasks` (
  `id` int NOT NULL AUTO_INCREMENT,
  `task_name` varchar(200) NOT NULL,
  `description` text,
  `priority` varchar(10) DEFAULT 'medium',
  `assigned_to` varchar(255) DEFAULT NULL,
  `assigned_by` varchar(255) DEFAULT NULL,
  `due_date` date DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `task_status` varchar(40) DEFAULT 'Pending',
  `remarks` varchar(100) DEFAULT 'No Remarks',
  `range_status` tinyint DEFAULT '0',
  `remark_updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_tasks_assigned_status` (`assigned_to`,`task_status`),
  CONSTRAINT `tasks_chk_1` CHECK ((`priority` in (_utf8mb4'low',_utf8mb4'medium',_utf8mb4'high',_utf8mb4'urgent')))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tasks`
--

LOCK TABLES `tasks` WRITE;
/*!40000 ALTER TABLE `tasks` DISABLE KEYS */;
/*!40000 ALTER TABLE `tasks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `td_table`
--

DROP TABLE IF EXISTS `td_table`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `td_table` (
  `id` int NOT NULL AUTO_INCREMENT,
  `army_number` varchar(50) NOT NULL,
  `remarks` text,
  `td_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `company` varchar(50) DEFAULT NULL,
  `authority` varchar(50) DEFAULT NULL,
  `location` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_td_army_number` (`army_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `td_table`
--

LOCK TABLES `td_table` WRITE;
/*!40000 ALTER TABLE `td_table` DISABLE KEYS */;
/*!40000 ALTER TABLE `td_table` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `trade_manpower_daily`
--

DROP TABLE IF EXISTS `trade_manpower_daily`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `trade_manpower_daily` (
  `id` int NOT NULL AUTO_INCREMENT,
  `report_date` date NOT NULL,
  `op_ciph_auth` int DEFAULT '0',
  `op_ciph_hs` int DEFAULT '0',
  `op_ciph_held` int DEFAULT '0',
  `op_ciph_av` int DEFAULT '0',
  `op_ciph_dist_hq` int DEFAULT '0',
  `op_ciph_dist_1` int DEFAULT '0',
  `op_ciph_dist_2` int DEFAULT '0',
  `op_ciph_dist_3` int DEFAULT '0',
  `op_ciph_state_hq` int DEFAULT '0',
  `op_ciph_state_1` int DEFAULT '0',
  `op_ciph_state_2` int DEFAULT '0',
  `op_ciph_state_3` int DEFAULT '0',
  `op_ciph_present_hq` int DEFAULT '0',
  `op_ciph_present_1` int DEFAULT '0',
  `op_ciph_present_2` int DEFAULT '0',
  `op_ciph_present_3` int DEFAULT '0',
  `oss_auth` int DEFAULT '0',
  `oss_hs` int DEFAULT '0',
  `oss_held` int DEFAULT '0',
  `oss_av` int DEFAULT '0',
  `oss_dist_hq` int DEFAULT '0',
  `oss_dist_1` int DEFAULT '0',
  `oss_dist_2` int DEFAULT '0',
  `oss_dist_3` int DEFAULT '0',
  `oss_state_hq` int DEFAULT '0',
  `oss_state_1` int DEFAULT '0',
  `oss_state_2` int DEFAULT '0',
  `oss_state_3` int DEFAULT '0',
  `oss_present_hq` int DEFAULT '0',
  `oss_present_1` int DEFAULT '0',
  `oss_present_2` int DEFAULT '0',
  `oss_present_3` int DEFAULT '0',
  `occ_auth` int DEFAULT '0',
  `occ_hs` int DEFAULT '0',
  `occ_held` int DEFAULT '0',
  `occ_av` int DEFAULT '0',
  `occ_dist_hq` int DEFAULT '0',
  `occ_dist_1` int DEFAULT '0',
  `occ_dist_2` int DEFAULT '0',
  `occ_dist_3` int DEFAULT '0',
  `occ_state_hq` int DEFAULT '0',
  `occ_state_1` int DEFAULT '0',
  `occ_state_2` int DEFAULT '0',
  `occ_state_3` int DEFAULT '0',
  `occ_present_hq` int DEFAULT '0',
  `occ_present_1` int DEFAULT '0',
  `occ_present_2` int DEFAULT '0',
  `occ_present_3` int DEFAULT '0',
  `ttc_auth` int DEFAULT '0',
  `ttc_hs` int DEFAULT '0',
  `ttc_held` int DEFAULT '0',
  `ttc_av` int DEFAULT '0',
  `ttc_dist_hq` int DEFAULT '0',
  `ttc_dist_1` int DEFAULT '0',
  `ttc_dist_2` int DEFAULT '0',
  `ttc_dist_3` int DEFAULT '0',
  `ttc_state_hq` int DEFAULT '0',
  `ttc_state_1` int DEFAULT '0',
  `ttc_state_2` int DEFAULT '0',
  `ttc_state_3` int DEFAULT '0',
  `ttc_present_hq` int DEFAULT '0',
  `ttc_present_1` int DEFAULT '0',
  `ttc_present_2` int DEFAULT '0',
  `ttc_present_3` int DEFAULT '0',
  `lmn_auth` int DEFAULT '0',
  `lmn_hs` int DEFAULT '0',
  `lmn_held` int DEFAULT '0',
  `lmn_av` int DEFAULT '0',
  `lmn_dist_hq` int DEFAULT '0',
  `lmn_dist_1` int DEFAULT '0',
  `lmn_dist_2` int DEFAULT '0',
  `lmn_dist_3` int DEFAULT '0',
  `lmn_state_hq` int DEFAULT '0',
  `lmn_state_1` int DEFAULT '0',
  `lmn_state_2` int DEFAULT '0',
  `lmn_state_3` int DEFAULT '0',
  `lmn_present_hq` int DEFAULT '0',
  `lmn_present_1` int DEFAULT '0',
  `lmn_present_2` int DEFAULT '0',
  `lmn_present_3` int DEFAULT '0',
  `efs_auth` int DEFAULT '0',
  `efs_hs` int DEFAULT '0',
  `efs_held` int DEFAULT '0',
  `efs_av` int DEFAULT '0',
  `efs_dist_hq` int DEFAULT '0',
  `efs_dist_1` int DEFAULT '0',
  `efs_dist_2` int DEFAULT '0',
  `efs_dist_3` int DEFAULT '0',
  `efs_state_hq` int DEFAULT '0',
  `efs_state_1` int DEFAULT '0',
  `efs_state_2` int DEFAULT '0',
  `efs_state_3` int DEFAULT '0',
  `efs_present_hq` int DEFAULT '0',
  `efs_present_1` int DEFAULT '0',
  `efs_present_2` int DEFAULT '0',
  `efs_present_3` int DEFAULT '0',
  `dvr_mt_auth` int DEFAULT '0',
  `dvr_mt_hs` int DEFAULT '0',
  `dvr_mt_held` int DEFAULT '0',
  `dvr_mt_av` int DEFAULT '0',
  `dvr_mt_dist_hq` int DEFAULT '0',
  `dvr_mt_dist_1` int DEFAULT '0',
  `dvr_mt_dist_2` int DEFAULT '0',
  `dvr_mt_dist_3` int DEFAULT '0',
  `dvr_mt_state_hq` int DEFAULT '0',
  `dvr_mt_state_1` int DEFAULT '0',
  `dvr_mt_state_2` int DEFAULT '0',
  `dvr_mt_state_3` int DEFAULT '0',
  `dvr_mt_present_hq` int DEFAULT '0',
  `dvr_mt_present_1` int DEFAULT '0',
  `dvr_mt_present_2` int DEFAULT '0',
  `dvr_mt_present_3` int DEFAULT '0',
  `dr_auth` int DEFAULT '0',
  `dr_hs` int DEFAULT '0',
  `dr_held` int DEFAULT '0',
  `dr_av` int DEFAULT '0',
  `dr_dist_hq` int DEFAULT '0',
  `dr_dist_1` int DEFAULT '0',
  `dr_dist_2` int DEFAULT '0',
  `dr_dist_3` int DEFAULT '0',
  `dr_state_hq` int DEFAULT '0',
  `dr_state_1` int DEFAULT '0',
  `dr_state_2` int DEFAULT '0',
  `dr_state_3` int DEFAULT '0',
  `dr_present_hq` int DEFAULT '0',
  `dr_present_1` int DEFAULT '0',
  `dr_present_2` int DEFAULT '0',
  `dr_present_3` int DEFAULT '0',
  `dtmn_auth` int DEFAULT '0',
  `dtmn_hs` int DEFAULT '0',
  `dtmn_held` int DEFAULT '0',
  `dtmn_av` int DEFAULT '0',
  `dtmn_dist_hq` int DEFAULT '0',
  `dtmn_dist_1` int DEFAULT '0',
  `dtmn_dist_2` int DEFAULT '0',
  `dtmn_dist_3` int DEFAULT '0',
  `dtmn_state_hq` int DEFAULT '0',
  `dtmn_state_1` int DEFAULT '0',
  `dtmn_state_2` int DEFAULT '0',
  `dtmn_state_3` int DEFAULT '0',
  `dtmn_present_hq` int DEFAULT '0',
  `dtmn_present_1` int DEFAULT '0',
  `dtmn_present_2` int DEFAULT '0',
  `dtmn_present_3` int DEFAULT '0',
  `skt_auth` int DEFAULT '0',
  `skt_hs` int DEFAULT '0',
  `skt_held` int DEFAULT '0',
  `skt_av` int DEFAULT '0',
  `skt_dist_hq` int DEFAULT '0',
  `skt_dist_1` int DEFAULT '0',
  `skt_dist_2` int DEFAULT '0',
  `skt_dist_3` int DEFAULT '0',
  `skt_state_hq` int DEFAULT '0',
  `skt_state_1` int DEFAULT '0',
  `skt_state_2` int DEFAULT '0',
  `skt_state_3` int DEFAULT '0',
  `skt_present_hq` int DEFAULT '0',
  `skt_present_1` int DEFAULT '0',
  `skt_present_2` int DEFAULT '0',
  `skt_present_3` int DEFAULT '0',
  `artsn_auth` int DEFAULT '0',
  `artsn_hs` int DEFAULT '0',
  `artsn_held` int DEFAULT '0',
  `artsn_av` int DEFAULT '0',
  `artsn_dist_hq` int DEFAULT '0',
  `artsn_dist_1` int DEFAULT '0',
  `artsn_dist_2` int DEFAULT '0',
  `artsn_dist_3` int DEFAULT '0',
  `artsn_state_hq` int DEFAULT '0',
  `artsn_state_1` int DEFAULT '0',
  `artsn_state_2` int DEFAULT '0',
  `artsn_state_3` int DEFAULT '0',
  `artsn_present_hq` int DEFAULT '0',
  `artsn_present_1` int DEFAULT '0',
  `artsn_present_2` int DEFAULT '0',
  `artsn_present_3` int DEFAULT '0',
  `w_man_auth` int DEFAULT '0',
  `w_man_hs` int DEFAULT '0',
  `w_man_held` int DEFAULT '0',
  `w_man_av` int DEFAULT '0',
  `w_man_dist_hq` int DEFAULT '0',
  `w_man_dist_1` int DEFAULT '0',
  `w_man_dist_2` int DEFAULT '0',
  `w_man_dist_3` int DEFAULT '0',
  `w_man_state_hq` int DEFAULT '0',
  `w_man_state_1` int DEFAULT '0',
  `w_man_state_2` int DEFAULT '0',
  `w_man_state_3` int DEFAULT '0',
  `w_man_present_hq` int DEFAULT '0',
  `w_man_present_1` int DEFAULT '0',
  `w_man_present_2` int DEFAULT '0',
  `w_man_present_3` int DEFAULT '0',
  `steward_auth` int DEFAULT '0',
  `steward_hs` int DEFAULT '0',
  `steward_held` int DEFAULT '0',
  `steward_av` int DEFAULT '0',
  `steward_dist_hq` int DEFAULT '0',
  `steward_dist_1` int DEFAULT '0',
  `steward_dist_2` int DEFAULT '0',
  `steward_dist_3` int DEFAULT '0',
  `steward_state_hq` int DEFAULT '0',
  `steward_state_1` int DEFAULT '0',
  `steward_state_2` int DEFAULT '0',
  `steward_state_3` int DEFAULT '0',
  `steward_present_hq` int DEFAULT '0',
  `steward_present_1` int DEFAULT '0',
  `steward_present_2` int DEFAULT '0',
  `steward_present_3` int DEFAULT '0',
  `dresser_auth` int DEFAULT '0',
  `dresser_hs` int DEFAULT '0',
  `dresser_held` int DEFAULT '0',
  `dresser_av` int DEFAULT '0',
  `dresser_dist_hq` int DEFAULT '0',
  `dresser_dist_1` int DEFAULT '0',
  `dresser_dist_2` int DEFAULT '0',
  `dresser_dist_3` int DEFAULT '0',
  `dresser_state_hq` int DEFAULT '0',
  `dresser_state_1` int DEFAULT '0',
  `dresser_state_2` int DEFAULT '0',
  `dresser_state_3` int DEFAULT '0',
  `dresser_present_hq` int DEFAULT '0',
  `dresser_present_1` int DEFAULT '0',
  `dresser_present_2` int DEFAULT '0',
  `dresser_present_3` int DEFAULT '0',
  `hkeeper_auth` int DEFAULT '0',
  `hkeeper_hs` int DEFAULT '0',
  `hkeeper_held` int DEFAULT '0',
  `hkeeper_av` int DEFAULT '0',
  `hkeeper_dist_hq` int DEFAULT '0',
  `hkeeper_dist_1` int DEFAULT '0',
  `hkeeper_dist_2` int DEFAULT '0',
  `hkeeper_dist_3` int DEFAULT '0',
  `hkeeper_state_hq` int DEFAULT '0',
  `hkeeper_state_1` int DEFAULT '0',
  `hkeeper_state_2` int DEFAULT '0',
  `hkeeper_state_3` int DEFAULT '0',
  `hkeeper_present_hq` int DEFAULT '0',
  `hkeeper_present_1` int DEFAULT '0',
  `hkeeper_present_2` int DEFAULT '0',
  `hkeeper_present_3` int DEFAULT '0',
  `mkeeper_auth` int DEFAULT '0',
  `mkeeper_hs` int DEFAULT '0',
  `mkeeper_held` int DEFAULT '0',
  `mkeeper_av` int DEFAULT '0',
  `mkeeper_dist_hq` int DEFAULT '0',
  `mkeeper_dist_1` int DEFAULT '0',
  `mkeeper_dist_2` int DEFAULT '0',
  `mkeeper_dist_3` int DEFAULT '0',
  `mkeeper_state_hq` int DEFAULT '0',
  `mkeeper_state_1` int DEFAULT '0',
  `mkeeper_state_2` int DEFAULT '0',
  `mkeeper_state_3` int DEFAULT '0',
  `mkeeper_present_hq` int DEFAULT '0',
  `mkeeper_present_1` int DEFAULT '0',
  `mkeeper_present_2` int DEFAULT '0',
  `mkeeper_present_3` int DEFAULT '0',
  `chef_mess_auth` int DEFAULT '0',
  `chef_mess_hs` int DEFAULT '0',
  `chef_mess_held` int DEFAULT '0',
  `chef_mess_av` int DEFAULT '0',
  `chef_mess_dist_hq` int DEFAULT '0',
  `chef_mess_dist_1` int DEFAULT '0',
  `chef_mess_dist_2` int DEFAULT '0',
  `chef_mess_dist_3` int DEFAULT '0',
  `chef_mess_state_hq` int DEFAULT '0',
  `chef_mess_state_1` int DEFAULT '0',
  `chef_mess_state_2` int DEFAULT '0',
  `chef_mess_state_3` int DEFAULT '0',
  `chef_mess_present_hq` int DEFAULT '0',
  `chef_mess_present_1` int DEFAULT '0',
  `chef_mess_present_2` int DEFAULT '0',
  `chef_mess_present_3` int DEFAULT '0',
  `chef_com_auth` int DEFAULT '0',
  `chef_com_hs` int DEFAULT '0',
  `chef_com_held` int DEFAULT '0',
  `chef_com_av` int DEFAULT '0',
  `chef_com_dist_hq` int DEFAULT '0',
  `chef_com_dist_1` int DEFAULT '0',
  `chef_com_dist_2` int DEFAULT '0',
  `chef_com_dist_3` int DEFAULT '0',
  `chef_com_state_hq` int DEFAULT '0',
  `chef_com_state_1` int DEFAULT '0',
  `chef_com_state_2` int DEFAULT '0',
  `chef_com_state_3` int DEFAULT '0',
  `chef_com_present_hq` int DEFAULT '0',
  `chef_com_present_1` int DEFAULT '0',
  `chef_com_present_2` int DEFAULT '0',
  `chef_com_present_3` int DEFAULT '0',
  `er_auth` int DEFAULT '0',
  `er_hs` int DEFAULT '0',
  `er_held` int DEFAULT '0',
  `er_av` int DEFAULT '0',
  `er_dist_hq` int DEFAULT '0',
  `er_dist_1` int DEFAULT '0',
  `er_dist_2` int DEFAULT '0',
  `er_dist_3` int DEFAULT '0',
  `er_state_hq` int DEFAULT '0',
  `er_state_1` int DEFAULT '0',
  `er_state_2` int DEFAULT '0',
  `er_state_3` int DEFAULT '0',
  `er_present_hq` int DEFAULT '0',
  `er_present_1` int DEFAULT '0',
  `er_present_2` int DEFAULT '0',
  `er_present_3` int DEFAULT '0',
  `tlr_auth` int DEFAULT '0',
  `tlr_hs` int DEFAULT '0',
  `tlr_held` int DEFAULT '0',
  `tlr_av` int DEFAULT '0',
  `tlr_dist_hq` int DEFAULT '0',
  `tlr_dist_1` int DEFAULT '0',
  `tlr_dist_2` int DEFAULT '0',
  `tlr_dist_3` int DEFAULT '0',
  `tlr_state_hq` int DEFAULT '0',
  `tlr_state_1` int DEFAULT '0',
  `tlr_state_2` int DEFAULT '0',
  `tlr_state_3` int DEFAULT '0',
  `tlr_present_hq` int DEFAULT '0',
  `tlr_present_1` int DEFAULT '0',
  `tlr_present_2` int DEFAULT '0',
  `tlr_present_3` int DEFAULT '0',
  `clk_sd_auth` int DEFAULT '0',
  `clk_sd_hs` int DEFAULT '0',
  `clk_sd_held` int DEFAULT '0',
  `clk_sd_av` int DEFAULT '0',
  `clk_sd_dist_hq` int DEFAULT '0',
  `clk_sd_dist_1` int DEFAULT '0',
  `clk_sd_dist_2` int DEFAULT '0',
  `clk_sd_dist_3` int DEFAULT '0',
  `clk_sd_state_hq` int DEFAULT '0',
  `clk_sd_state_1` int DEFAULT '0',
  `clk_sd_state_2` int DEFAULT '0',
  `clk_sd_state_3` int DEFAULT '0',
  `clk_sd_present_hq` int DEFAULT '0',
  `clk_sd_present_1` int DEFAULT '0',
  `clk_sd_present_2` int DEFAULT '0',
  `clk_sd_present_3` int DEFAULT '0',
  `ere_auth` int DEFAULT '0',
  `ere_hs` int DEFAULT '0',
  `ere_held` int DEFAULT '0',
  `ere_av` int DEFAULT '0',
  `ere_dist_hq` int DEFAULT '0',
  `ere_dist_1` int DEFAULT '0',
  `ere_dist_2` int DEFAULT '0',
  `ere_dist_3` int DEFAULT '0',
  `ere_state_hq` int DEFAULT '0',
  `ere_state_1` int DEFAULT '0',
  `ere_state_2` int DEFAULT '0',
  `ere_state_3` int DEFAULT '0',
  `ere_present_hq` int DEFAULT '0',
  `ere_present_1` int DEFAULT '0',
  `ere_present_2` int DEFAULT '0',
  `ere_present_3` int DEFAULT '0',
  `total_auth` int DEFAULT '0',
  `total_hs` int DEFAULT '0',
  `total_held` int DEFAULT '0',
  `total_av` int DEFAULT '0',
  `total_dist_hq` int DEFAULT '0',
  `total_dist_1` int DEFAULT '0',
  `total_dist_2` int DEFAULT '0',
  `total_dist_3` int DEFAULT '0',
  `total_state_hq` int DEFAULT '0',
  `total_state_1` int DEFAULT '0',
  `total_state_2` int DEFAULT '0',
  `total_state_3` int DEFAULT '0',
  `total_present_hq` int DEFAULT '0',
  `total_present_1` int DEFAULT '0',
  `total_present_2` int DEFAULT '0',
  `total_present_3` int DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `report_date` (`report_date`),
  KEY `idx_report_date` (`report_date`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `trade_manpower_daily`
--

LOCK TABLES `trade_manpower_daily` WRITE;
/*!40000 ALTER TABLE `trade_manpower_daily` DISABLE KEYS */;
/*!40000 ALTER TABLE `trade_manpower_daily` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `units_served`
--

DROP TABLE IF EXISTS `units_served`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `units_served` (
  `id` int NOT NULL AUTO_INCREMENT,
  `personnel_id` int NOT NULL,
  `army_number` varchar(100) NOT NULL,
  `sr_no` int DEFAULT NULL,
  `unit` varchar(255) DEFAULT NULL,
  `from_date` date DEFAULT NULL,
  `to_date` date DEFAULT NULL,
  `duty_performed` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_army_number` (`army_number`),
  KEY `idx_personnel_id_units` (`personnel_id`),
  CONSTRAINT `units_served_ibfk_1` FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `units_served`
--

LOCK TABLES `units_served` WRITE;
/*!40000 ALTER TABLE `units_served` DISABLE KEYS */;
/*!40000 ALTER TABLE `units_served` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_messages`
--

DROP TABLE IF EXISTS `user_messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_messages` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sender_id` int NOT NULL,
  `receiver_id` int NOT NULL,
  `message` text,
  `sent_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `is_read` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `sender_id` (`sender_id`),
  KEY `receiver_id` (`receiver_id`),
  CONSTRAINT `user_messages_ibfk_1` FOREIGN KEY (`sender_id`) REFERENCES `users` (`id`),
  CONSTRAINT `user_messages_ibfk_2` FOREIGN KEY (`receiver_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_messages`
--

LOCK TABLES `user_messages` WRITE;
/*!40000 ALTER TABLE `user_messages` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_messages` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(100) NOT NULL,
  `email` varchar(150) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` varchar(50) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `company` varchar(50) DEFAULT '1 company',
  `army_number` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=119 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'COL M S DILAWRI','co','123','CO','2025-11-19 06:28:38','Admin',NULL),(3,'LT AMEYA A','adjt','123','ADJUTANT','2025-11-19 06:45:22','Admin',NULL),(11,'Lt Col Tamanna Bhasin','oc_comn','123','OC','2025-12-16 01:40:20','COMN Company',NULL),(19,'Lt Col Mamta Samant','2ic','123','2IC','2025-12-31 06:48:12','Admin',NULL),(20,'Mahesh Kumar','ocennco','123','O CENTRE NCO','2026-01-10 06:00:29','Center','15712365w'),(26,'NK D SAIKIA','comn_onco','123','ONCO','2026-01-12 07:27:53','COMN Company',NULL),(27,'MITHUN KARMAKER','3coyonco','123','ONCO','2026-01-12 07:27:53','3 company',NULL),(28,'PATIL AASHITOSH','hqcoyonco','15CESR','ONCO','2026-01-12 07:27:53','HQ company',NULL),(29,'R K TOMAR','trgjco','123','TRGJCO','2026-01-16 06:20:50','HQ company',NULL),(30,'john.doe','acctoffr','123','ACCOUNT OFFICER','2026-01-19 08:43:14','HQ company','ARMY12345'),(31,'CAPT VIPUL','projoffr','123','PROJECT OFFICER','2026-01-19 08:47:14','HQ company','ARMY1254345'),(32,'Nb Sub Y Naidu R','projjco','123','PROJECT JCO','2026-01-19 19:52:57','HQ company','123456099'),(33,'JOGE G G','sm','123','Subedar Major','2026-01-19 20:21:49','HQ company',NULL),(34,'Nb Sub Payang','acctjco','123','ACCOUNT JCO','2026-01-19 20:49:44','HQ company','98965565'),(36,'Sub R K SAHOO','sjcohq','PATIL','S/JCO','2026-01-20 00:00:56','HQ company','JC390178N'),(37,'Sub Major Mohan Lal ','sjco_comn','123','S/JCO','2026-01-20 02:12:21','COMN Company','JC379951P'),(38,'Nb Sub HANSRAM GURJAR','hans','1993','JCO','2026-01-20 02:12:21','COMN Company','JC393919L'),(40,'CHM Amit Ranjan','ncochq_comn','123','NCO CHQ','2026-01-21 06:08:12','COMN Company','15720931K'),(41,'Hav Rajesh Babu','ncoit','123','NCO IT','2026-01-21 06:08:12','COMN Company','15715911M'),(42,'Hav PINTU KUMAR','nco_sigcen','123','NCO SIGCEN','2026-01-21 06:08:12','COMN Company',''),(43,'Hav Pintu Kumar','nco_fault_repair','123','NCO FAULTREPAIR','2026-01-21 06:08:12','COMN Company','15714930L'),(44,'nco_op_c1','nco_comn','123','NCO COMN','2026-01-21 06:08:12','COMN Company','C1-1006'),(45,'Hav HARIOM BAGHEL','ncomccs','123','NCO MCCS','2026-01-21 06:09:34','COMN Company','15715965N'),(47,'nco_rhq_c3','ncorhq','123','NCO RHQ','2026-01-21 06:10:42','HQ company','C3-3001'),(48,'nco_chq_c3','ncochqhq','123','NCO CHQ','2026-01-21 06:10:42','HQ company','C3-3002'),(49,'HAV PAPU DATTA','ncolrw','123','NCO LRW','2026-01-21 06:10:42','HQ company','14671509K'),(50,'nco_qm_c3','ncoqm','123','NCO QM','2026-01-21 06:10:42','HQ company','C3-3004'),(51,'nco_mt_c3','ncomt','123','NCO MT','2026-01-21 06:10:42','HQ company','C3-3005'),(52,'Hav Sarath','ncotm','123','NCO TM','2026-01-21 06:10:42','HQ company','15719444X'),(53,'CHM SAKIA','ncorpna','123','NCO RPNA','2026-01-21 06:10:42','HQ company','15684675M'),(57,'Sub Major Mohan Lal','jcochq_comn','123','JCO CHQ','2026-01-21 07:12:15','COMN Company','JC379951P'),(58,'Nb Sub Hansram Gurjar','jcoit','123','JCO IT','2026-01-21 07:12:15','COMN Company','JC393919L'),(60,'Sub Major Mohan Lal','jco_fault_repair','123','JCO FAULTREPAIR','2026-01-21 07:12:15','COMN Company','JC379951P'),(61,'Nb Sub hansram','jco_sigcen','123','JCO SIGCEN','2026-01-21 07:12:15','COMN Company','JC394037W'),(62,'Sub Anuj Kumar','jcomccs','123','JCO MCCS','2026-01-21 07:41:45','COMN Company','JC389181F'),(64,'jco_chq_hq','jcochqhq','123','JCO CHQ','2026-01-21 07:41:45','HQ company','JC391303Y'),(65,'SUB MUKESH KUMAR','jcorhq','123','JCO RHQ','2026-01-21 07:41:45','HQ company','JC388417Y'),(66,'Nb Sub JOSHI','jcotm','123','JCO TM','2026-01-21 07:41:45','HQ company','JC393792N'),(67,'sub sahoo','jcomt','123','JCO MT','2026-01-21 07:41:45','HQ company','JC391303Y'),(69,'sub sahoo ','jcolrw','123','JCO LRW','2026-01-21 07:41:45','HQ company','JC391303Y'),(71,'sub maj s r kumar','jcoqm','123','JCO QM','2026-01-21 07:41:45','HQ company','JC394251Y'),(72,'SUB MUKESH KUMAR','hclk','123','HEAD CLK','2026-02-09 03:35:12','HQ company','JC388417Y'),(73,'PUSPENDRA KUMAR','PA','123','PA','2026-02-09 03:35:53','COMN Company','15756452P'),(74,'Lt Col Mamta Samant','ochq','123','OC','2026-02-09 03:36:54','HQ company',''),(75,'KANADE KISHOR','ncoqrt','123','NCO QRT','2026-03-23 10:13:11','HQ company','15724505N'),(76,'AV MOHAN SARMA','o2','123','O2','2026-03-30 06:15:34','HQ company','A4354471Y'),(77,'Nb sub JOSHI','jcoqrt','123','JCO QRT','2026-03-31 15:37:10','HQ company','JC393792N'),(79,'Lt Col SATISH GUPTA','oc3','123','OC','2026-04-08 11:43:28','3 Company','IC-123'),(80,'Sub Srijeeth','sjco3','123','S/JCO','2026-04-08 11:44:45','3 Company','JC381703X'),(81,'Sub Hari','hari','123','JCO','2026-04-08 11:56:09','3 Company','JC386411Y'),(82,'Nb Sub Suresh','qwe','123','rty','2026-04-08 11:56:09','3 Company',NULL),(83,'Nb Sub Binay','VCJCO','123','JCO','2026-04-08 11:56:09','3 Company','JC394687K'),(84,'ROHIT KUMAR','chmhq','123','CHM','2026-04-08 11:56:09','HQ Company','15714583X'),(85,'S K SINGH','chm_comn','123','CHM','2026-04-08 12:03:55','COMN Company','15681641N'),(87,'Guruvelli Dharma Rao','chm3','123','CHM','2026-04-08 12:03:55','3 Company','15677524L'),(88,'Hav Devendan','ncochq3','123','NCO CHQ','2026-04-10 11:11:10','3 Company','15687626P'),(89,'Sub Maj Lakshman Kumar G','jcochq3','123','JCO CHQ','2026-04-10 11:12:45','3 Company','JC381703X'),(90,'Hav Arun Kumar P G','ncosys','123','NCO SYSTEM','2026-04-10 11:14:43','3 Company','15706979M'),(91,'Sub Amit Manhas','jcosys','123','JCO SYSTEM','2026-04-10 11:14:43','3 Company','JC384513W'),(92,'Hav Rakesh Chauhan','ncodet','123','NCO DET','2026-04-10 11:16:55','3 Company','15704421Y'),(93,'Sub Hari Prasad','jcodet','123','JCO DET','2026-04-10 11:16:55','3 Company','JC386411Y'),(95,'Binay Chnader','mtjcobb','123','JCO MT','2026-04-10 11:20:30','3 Company','1236543231'),(96,'Sub Tomar','tomar','123','JCO','2026-04-11 13:54:41','HQ Company','JC389351A'),(97,'Sub Maj Mohan lal','mohan','123','JCO','2026-04-11 13:54:41','COMN Company','JC379951P'),(98,'SUB MUKESH KUMAR','mukesh','123','JCO','2026-04-11 13:58:58','HQ Company','JC388417Y'),(99,'Nb Sub G manjhi','majji','123','JCO','2026-04-11 13:59:53','COMN Company','JC394652N'),(100,'Sub Anuj Kumar','anuj','123','JCO','2026-04-11 14:01:05','COMN Company','JC389181F'),(101,'Nb Sub Y Naidu','naidu','123','JCO','2026-04-11 14:01:05','COMN Company','JC390543K'),(102,'Nb Sub Bala','bala','123','JCO','2026-04-11 14:01:37','HQ Company','JC394251Y'),(103,'Nb Sub Maharathi','maha','123','JCO','2026-04-11 14:02:19','COMN Company','JC394251Y'),(104,'sub Sahoo','sahoo','123','JCO','2026-04-11 14:02:57','COMN Company','JC391303Y'),(105,'Sub Satendra','satendra','123','JCO','2026-04-12 04:25:23','HQ Company','JC390178N'),(106,'Nb Sub Kamal Kishor','kamal','123','JCO','2026-04-12 04:25:23','HQ Company','JC392405f'),(107,'Nb Sub JOSHI','joshi','123','JCO','2026-05-01 02:48:24','HQ company','JC393792N'),(108,'Sub Maj Lakshmana','laksha','123','JCO','2026-05-01 07:29:27','3 Company','JC381703X'),(109,'Sub Sam Denial','sam','123','JCO','2026-05-01 08:31:15','COMN Company','JC386601L'),(110,'MT NCO BB CANTT','mtncobbcantt','123','NCO MT','2026-05-02 15:58:33','3 Company','123456'),(111,'JP SHRAMA','jpsharma','123','JCO','2026-05-05 14:38:32','COMN Company','JC393217M'),(112,'NB SUB JOSHI','jcorpna','123','JCO RPNA','2026-05-18 07:58:15','HQ company','JC393792N'),(113,'Nb Sub vignesh m','tnjco','123','JCO','2026-07-07 07:58:15','COMN Company','JC394989W'),(114,'Nb sub A J Mulla','mmjco','123','JCO MM','2026-08-25 12:06:28','COMN Company',NULL),(115,'NK KARTHICK','mmnco','123','NCO MM','2026-08-25 12:07:13','COMN Company','15717788X'),(116,'SUB A K MAHARATHI','jcochqcomn','123','JCO CHQ','2026-08-27 09:51:36','COMN Company',NULL),(117,'SUB','jco_comn','123','JCO COMN','2026-09-03 16:11:06','COMN Company',NULL),(118,'DOCJC','docjc@gmail.com','123','DOCJC','2026-10-29 15:59:52','HQ Company','JC-12345XZ');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vehicle_detail`
--

DROP TABLE IF EXISTS `vehicle_detail`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vehicle_detail` (
  `vehicle_no` varchar(20) NOT NULL,
  `type` varchar(30) DEFAULT NULL,
  `class` varchar(10) DEFAULT NULL,
  `detailment` varchar(100) DEFAULT NULL,
  `dist_travelled` int DEFAULT NULL,
  `quantity` int DEFAULT '1',
  `bullet_proof` enum('Y','N') DEFAULT NULL,
  PRIMARY KEY (`vehicle_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vehicle_detail`
--

LOCK TABLES `vehicle_detail` WRITE;
/*!40000 ALTER TABLE `vehicle_detail` DISABLE KEYS */;
/*!40000 ALTER TABLE `vehicle_detail` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `weight_info`
--

DROP TABLE IF EXISTS `weight_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `weight_info` (
  `troop_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) DEFAULT NULL,
  `rank` varchar(50) DEFAULT NULL,
  `army_number` varchar(50) DEFAULT NULL,
  `actual_weight` float DEFAULT NULL,
  `age` int DEFAULT NULL,
  `height` float DEFAULT NULL,
  `company` varchar(100) DEFAULT NULL,
  `status_type` varchar(10) NOT NULL DEFAULT 'shape',
  `category_type` varchar(10) DEFAULT NULL,
  `restrictions` text,
  PRIMARY KEY (`troop_id`),
  UNIQUE KEY `army_number` (`army_number`),
  UNIQUE KEY `army_number_2` (`army_number`),
  KEY `idx_weight_info_company` (`company`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `weight_info`
--

LOCK TABLES `weight_info` WRITE;
/*!40000 ALTER TABLE `weight_info` DISABLE KEYS */;
/*!40000 ALTER TABLE `weight_info` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-11-04 19:37:35
