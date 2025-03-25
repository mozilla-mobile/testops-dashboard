-- MySQL dump 10.13  Distrib 8.0.33, for macos13.3 (x86_64)
--
-- Host: 127.0.0.1    Database: production
-- ------------------------------------------------------
-- Server version	5.7.43-google-log

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
-- Current Database: `production`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `production` /*!40100 DEFAULT CHARACTER SET utf8 */;

USE `production`;

--
-- Table structure for table `github_issue_types`
--

DROP TABLE IF EXISTS `github_issue_types`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `github_issue_types` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `issue_type` varchar(75) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `github_issue_types`
--

LOCK TABLES `github_issue_types` WRITE;
/*!40000 ALTER TABLE `github_issue_types` DISABLE KEYS */;
INSERT INTO `github_issue_types` VALUES (1,'issue'),(2,'pr');
/*!40000 ALTER TABLE `github_issue_types` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `projects`
--

DROP TABLE IF EXISTS `projects`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `projects` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `testrail_project_id` int(11) NOT NULL,
  `project_name_abbrev` varchar(25) NOT NULL,
  `project_name` varchar(75) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `projects`
--

LOCK TABLES `projects` WRITE;
/*!40000 ALTER TABLE `projects` DISABLE KEYS */;
INSERT INTO `projects` VALUES (1,59,'fenix','Fenix Browser'),(2,48,'focus-android','Focus for Android'),(3,14,'firefox-ios','Firefox for iOS'),(4,27,'focus-ios','Focus for iOS'),(5,58,'reference-browser','Reference Browser');
/*!40000 ALTER TABLE `projects` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `report_github_issues`
--

DROP TABLE IF EXISTS `report_github_issues`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `report_github_issues` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `projects_id` int(11) NOT NULL,
  `issue_id` int(11) NOT NULL,
  `issue_title` varchar(75) DEFAULT NULL,
  `issue_types_id` int(11) DEFAULT '1',
  `github_created_at` date NOT NULL,
  `github_updated_at` date DEFAULT NULL,
  `github_closed_at` date DEFAULT NULL,
  `github_merged_at` date DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `projects_id` (`projects_id`),
  KEY `issue_types_id` (`issue_types_id`),
  CONSTRAINT `report_github_issues_ibfk_1` FOREIGN KEY (`projects_id`) REFERENCES `projects` (`id`),
  CONSTRAINT `report_github_issues_ibfk_2` FOREIGN KEY (`issue_types_id`) REFERENCES `github_issue_types` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `report_github_issues`
--

LOCK TABLES `report_github_issues` WRITE;
/*!40000 ALTER TABLE `report_github_issues` DISABLE KEYS */;
/*!40000 ALTER TABLE `report_github_issues` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `report_test_case_coverage`
--

DROP TABLE IF EXISTS `report_test_case_coverage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `report_test_case_coverage` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `projects_id` int(11) NOT NULL,
  `testrail_test_suites_id` int(11) NOT NULL,
  `test_sub_suites_id` int(11) NOT NULL DEFAULT '1',
  `test_automation_status_id` int(11) NOT NULL,
  `test_automation_coverage_id` int(11) NOT NULL,
  `test_count` int(11) NOT NULL DEFAULT '0',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `projects_id` (`projects_id`),
  KEY `test_sub_suites_id` (`test_sub_suites_id`),
  KEY `test_automation_status_id` (`test_automation_status_id`),
  KEY `test_automation_coverage_id` (`test_automation_coverage_id`),
  CONSTRAINT `report_test_case_coverage_ibfk_1` FOREIGN KEY (`projects_id`) REFERENCES `projects` (`id`),
  CONSTRAINT `report_test_case_coverage_ibfk_2` FOREIGN KEY (`test_sub_suites_id`) REFERENCES `test_sub_suites` (`id`),
  CONSTRAINT `report_test_case_coverage_ibfk_3` FOREIGN KEY (`test_automation_status_id`) REFERENCES `test_automation_status` (`id`),
  CONSTRAINT `report_test_case_coverage_ibfk_4` FOREIGN KEY (`test_automation_coverage_id`) REFERENCES `test_automation_coverage` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10695 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;


--
-- Table structure for table `test_automation_coverage`
--

DROP TABLE IF EXISTS `test_automation_coverage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `test_automation_coverage` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `testrail_id` int(11) NOT NULL,
  `coverage` varchar(75) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_automation_coverage`
--

LOCK TABLES `test_automation_coverage` WRITE;
/*!40000 ALTER TABLE `test_automation_coverage` DISABLE KEYS */;
INSERT INTO `test_automation_coverage` VALUES (1,1,'None'),(2,2,'Partial'),(3,3,'Full');
/*!40000 ALTER TABLE `test_automation_coverage` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `test_automation_status`
--

DROP TABLE IF EXISTS `test_automation_status`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `test_automation_status` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `testrail_id` int(11) NOT NULL,
  `status` varchar(75) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_automation_status`
--

LOCK TABLES `test_automation_status` WRITE;
/*!40000 ALTER TABLE `test_automation_status` DISABLE KEYS */;
INSERT INTO `test_automation_status` VALUES (1,1,'Untriaged'),(2,2,'Suitable'),(3,3,'Unsuitable'),(4,4,'Completed'),(5,5,'Disabled');
/*!40000 ALTER TABLE `test_automation_status` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `test_run_result_types`
--

DROP TABLE IF EXISTS `test_run_result_types`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `test_run_result_types` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `testrail_id` int(11) NOT NULL,
  `result_type_abbrev` varchar(25) NOT NULL,
  `result_type` varchar(50) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_run_result_types`
--

LOCK TABLES `test_run_result_types` WRITE;
/*!40000 ALTER TABLE `test_run_result_types` DISABLE KEYS */;
INSERT INTO `test_run_result_types` VALUES (1,1,'passed_count','Passed'),(2,2,'blocked_count','Blocked'),(3,3,'untested_count','Untested'),(4,4,'retest_count','Failed (known)'),(5,5,'failed_count','Failed (new)'),(6,6,'untested_count','Not Applicable'),(7,7,'untested_count','Not Available');
/*!40000 ALTER TABLE `test_run_result_types` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `test_sub_suites`
--

DROP TABLE IF EXISTS `test_sub_suites`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `test_sub_suites` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `testrail_id` int(11) NOT NULL,
  `test_sub_suite_abbrev` varchar(25) NOT NULL,
  `test_sub_suite` varchar(75) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_sub_suites`
--

LOCK TABLES `test_sub_suites` WRITE;
/*!40000 ALTER TABLE `test_sub_suites` DISABLE KEYS */;
INSERT INTO `test_sub_suites` VALUES (1,0,'functional','Functional'),(2,1,'smoke','Smoke & Sanity'),(3,2,'accessibility','Accessibility'),(4,3,'l10n','L10n'),(5,4,'security','Security'),(6,6,'fxa','FxA & Sync'),(7,7,'other','Other');
/*!40000 ALTER TABLE `test_sub_suites` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `test_suites`
--

DROP TABLE IF EXISTS `test_suites`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `test_suites` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `testrail_project_id` int(11) NOT NULL,
  `testrail_test_suites_id` int(11) NOT NULL,
  `test_suite_name` varchar(150) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2759 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2023-11-06 17:32:32
