-- MySQL dump 10.13  Distrib 8.3.0, for macos14 (arm64)
--
-- Host: 127.0.0.1    Database: staging
-- ------------------------------------------------------
-- Server version	8.0.31-google

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
SET @MYSQLDUMP_TEMP_LOG_BIN = @@SESSION.SQL_LOG_BIN;
SET @@SESSION.SQL_LOG_BIN= 0;

--
-- GTID state at the beginning of the backup 
--

SET @@GLOBAL.GTID_PURGED=/*!80000 '+'*/ 'c8ec8c69-6014-11eb-824f-42010a8a0052:1-19087392';

--
-- Current Database: `staging`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `staging` /*!40100 DEFAULT CHARACTER SET utf8mb3 */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `staging`;

--
-- Table structure for table `github_issue_types`
--

DROP TABLE IF EXISTS `github_issue_types`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `github_issue_types` (
  `id` int NOT NULL AUTO_INCREMENT,
  `issue_type` varchar(75) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `projects`
--

DROP TABLE IF EXISTS `projects`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `projects` (
  `id` int NOT NULL AUTO_INCREMENT,
  `testrail_project_id` int NOT NULL,
  `project_name_abbrev` varchar(25) NOT NULL,
  `project_name` varchar(75) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `report_bitrise_builds_count`
--

DROP TABLE IF EXISTS `report_bitrise_builds_count`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `report_bitrise_builds_count` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `total_builds` int DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7802 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `report_bugzilla_qe_needed`
--

DROP TABLE IF EXISTS `report_bugzilla_qe_needed`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `report_bugzilla_qe_needed` (
  `id` int NOT NULL AUTO_INCREMENT,
  `bugzilla_key` varchar(25) NOT NULL,
  `bugzilla_summary` varchar(500) NOT NULL,
  `buzilla_modified_at` timestamp NOT NULL,
  `bugzilla_tag_name` varchar(50) NOT NULL,
  `bugzilla_created_at` timestamp NOT NULL,
  `bugzilla_tag_status` varchar(25) NOT NULL,
  `bugzilla_tag_setter` varchar(100) NOT NULL,
  `bugzilla_bug_severity` varchar(25) DEFAULT NULL,
  `bugzilla_bug_priority` varchar(25) DEFAULT NULL,
  `bugzilla_bug_status` varchar(25) NOT NULL,
  `bugzilla_bug_resolution` varchar(25) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=208 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `report_bugzilla_qe_needed_count`
--

DROP TABLE IF EXISTS `report_bugzilla_qe_needed_count`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `report_bugzilla_qe_needed_count` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `bugzilla_total_qa_needed` int DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=37 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `report_github_issues`
--

DROP TABLE IF EXISTS `report_github_issues`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `report_github_issues` (
  `id` int NOT NULL AUTO_INCREMENT,
  `projects_id` int NOT NULL,
  `issue_id` int NOT NULL,
  `issue_title` varchar(75) DEFAULT NULL,
  `issue_types_id` int DEFAULT '1',
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `report_jira_qa_needed`
--

DROP TABLE IF EXISTS `report_jira_qa_needed`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `report_jira_qa_needed` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `jira_total_qa_needed` int DEFAULT NULL,
  `jira_qa_needed_verified_nightly` int DEFAULT NULL,
  `jira_qa_needed_not_verified` int DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `report_jira_qa_requests`
--

DROP TABLE IF EXISTS `report_jira_qa_requests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `report_jira_qa_requests` (
  `id` int NOT NULL AUTO_INCREMENT,
  `jira_key` varchar(25) NOT NULL,
  `jira_summary` varchar(500) NOT NULL,
  `jira_created_at` timestamp NOT NULL,
  `jira_firefox_release_train` varchar(50) NOT NULL,
  `jira_engineering_team` varchar(50) NOT NULL,
  `jira_story_points` int DEFAULT NULL,
  `jira_status` varchar(100) NOT NULL,
  `jira_assignee_username` varchar(100) DEFAULT NULL,
  `jira_labels` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11492 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `report_jira_qa_requests_new_issue_types`
--

DROP TABLE IF EXISTS `report_jira_qa_requests_new_issue_types`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `report_jira_qa_requests_new_issue_types` (
  `id` int NOT NULL AUTO_INCREMENT,
  `jira_key` varchar(25) NOT NULL,
  `jira_summary` varchar(500) NOT NULL,
  `jira_created_at` timestamp NOT NULL,
  `jira_firefox_release_train` varchar(50) DEFAULT NULL,
  `jira_engineering_team` varchar(50) DEFAULT NULL,
  `jira_story_points` int DEFAULT NULL,
  `jira_status` varchar(100) NOT NULL,
  `jira_assignee_username` varchar(100) DEFAULT NULL,
  `jira_labels` varchar(100) DEFAULT NULL,
  `jira_tested_train` varchar(100) DEFAULT NULL,
  `jira_issue_type` varchar(50) NOT NULL,
  `jira_parent_link` varchar(25) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6871 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `report_jira_softvision_worklogs`
--

DROP TABLE IF EXISTS `report_jira_softvision_worklogs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `report_jira_softvision_worklogs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `parent_key` varchar(75) NOT NULL,
  `child_key` varchar(75) NOT NULL,
  `author` varchar(175) NOT NULL,
  `time_spent` varchar(175) NOT NULL,
  `started_date` timestamp NOT NULL,
  `comment` varchar(3000) DEFAULT NULL,
  `time_spent_seconds` int NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9707 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `report_test_case_coverage`
--

DROP TABLE IF EXISTS `report_test_case_coverage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `report_test_case_coverage` (
  `id` int NOT NULL AUTO_INCREMENT,
  `projects_id` int NOT NULL,
  `testrail_test_suites_id` int NOT NULL,
  `test_sub_suites_id` int NOT NULL DEFAULT '1',
  `test_automation_status_id` int NOT NULL,
  `test_automation_coverage_id` int NOT NULL,
  `test_count` int NOT NULL DEFAULT '0',
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
) ENGINE=InnoDB AUTO_INCREMENT=17245 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `report_testrail_milestones`
--

DROP TABLE IF EXISTS `report_testrail_milestones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `report_testrail_milestones` (
  `id` int NOT NULL AUTO_INCREMENT,
  `testrail_milestone_id` int NOT NULL,
  `projects_id` int NOT NULL,
  `name` varchar(250) DEFAULT NULL,
  `started_on` date DEFAULT NULL,
  `is_completed` varchar(50) DEFAULT NULL,
  `description` varchar(5000) DEFAULT NULL,
  `completed_on` timestamp NULL DEFAULT NULL,
  `url` varchar(250) DEFAULT NULL,
  `testing_status` varchar(25) DEFAULT NULL,
  `testing_recommendation` varchar(250) DEFAULT NULL,
  `build_name` varchar(250) DEFAULT NULL,
  `build_version` varchar(150) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_projects` (`projects_id`),
  CONSTRAINT `fk_projects` FOREIGN KEY (`projects_id`) REFERENCES `projects` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9598 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `test_automation_coverage`
--

DROP TABLE IF EXISTS `test_automation_coverage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `test_automation_coverage` (
  `id` int NOT NULL AUTO_INCREMENT,
  `testrail_id` int NOT NULL,
  `coverage` varchar(75) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `test_automation_status`
--

DROP TABLE IF EXISTS `test_automation_status`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `test_automation_status` (
  `id` int NOT NULL AUTO_INCREMENT,
  `testrail_id` int NOT NULL,
  `status` varchar(75) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `test_run_result_types`
--

DROP TABLE IF EXISTS `test_run_result_types`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `test_run_result_types` (
  `id` int NOT NULL AUTO_INCREMENT,
  `testrail_id` int NOT NULL,
  `result_type_abbrev` varchar(25) NOT NULL,
  `result_type` varchar(50) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `test_sub_suites`
--

DROP TABLE IF EXISTS `test_sub_suites`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `test_sub_suites` (
  `id` int NOT NULL AUTO_INCREMENT,
  `testrail_id` int NOT NULL,
  `test_sub_suite_abbrev` varchar(25) NOT NULL,
  `test_sub_suite` varchar(75) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `test_suites`
--

DROP TABLE IF EXISTS `test_suites`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `test_suites` (
  `id` int NOT NULL AUTO_INCREMENT,
  `testrail_project_id` int NOT NULL,
  `testrail_test_suites_id` int NOT NULL,
  `test_suite_name` varchar(250) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8461 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;
SET @@SESSION.SQL_LOG_BIN = @MYSQLDUMP_TEMP_LOG_BIN;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-03-24 16:53:33

--
-- Table structure for table `report_bitrise_builds_count`
--

DROP TABLE IF EXISTS `report_bitrise_builds_count`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `report_bitrise_builds_count` (
  `id` int NOT NULL AUTO_INCREMENT,
  `build_number` int NOT NULL,
  `branch` varchar(250) DEFAULT NULL,
  `status` int DEFAULT NULL,
  `status_text` varchar(250) DEFAULT NULL,
  `triggered_workflow` varchar(250) DEFAULT NULL,
  `triggered_by` varchar(250) DEFAULT NULL,
  `triggered_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8461 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

