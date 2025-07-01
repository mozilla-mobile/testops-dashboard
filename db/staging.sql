-- MySQL dump 10.13  Distrib 9.3.0, for macos15.2 (arm64)
--
-- Host: 127.0.0.1    Database: staging
-- ------------------------------------------------------
-- Server version	9.3.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `staging`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `staging` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `staging`;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;



CREATE TABLE `test_plans` (
  `id` int NOT NULL AUTO_INCREMENT,
  `testrail_plan_id` int NOT NULL,
  `projects_id` int NOT NULL,
  `name` varchar(75) NOT NULL,
  `test_case_passed_count` int(11) NOT NULL DEFAULT '0',
  `test_case_retest_count` int(11) NOT NULL DEFAULT '0',
  `test_case_failed_count` int(11) NOT NULL DEFAULT '0',
  `test_case_blocked_count` int(11) NOT NULL DEFAULT '0',
  `test_case_total_count` int(11) NOT NULL DEFAULT '0',
  `testrail_created_on` date DEFAULT NULL,
  `testrail_completed_on` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `test_run_projects` FOREIGN KEY (`projects_id`) REFERENCES `projects` (`id`)
);

CREATE TABLE `test_runs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `testrail_run_id` int NOT NULL,
  `plan_id` int NOT NULL,
  `suite_id` int NOT NULL,
  `name` varchar(75) NOT NULL,
  `config` varchar(55) NOT NULL,
  `test_case_passed_count` int(11) NOT NULL DEFAULT '0',
  `test_case_retest_count` int(11) NOT NULL DEFAULT '0',
  `test_case_failed_count` int(11) NOT NULL DEFAULT '0',
  `test_case_blocked_count` int(11) NOT NULL DEFAULT '0',
  `test_case_total_count` int(11) NOT NULL DEFAULT '0',
  `testrail_created_on` date DEFAULT NULL,
  `testrail_completed_on` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `test_run_plans` FOREIGN KEY (`plan_id`) REFERENCES `test_plans` (`id`)
);

-- Dump completed on 2025-06-27 15:33:59
