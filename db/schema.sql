-- MySQL dump 10.13  Distrib 8.4.6, for macos15.4 (arm64)
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
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

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
) ENGINE=InnoDB AUTO_INCREMENT=69085 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `report_bugzilla_meta_bugs`
--

DROP TABLE IF EXISTS `report_bugzilla_meta_bugs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `report_bugzilla_meta_bugs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `bugzilla_key` int NOT NULL,
  `bugzilla_summary` text,
  `bugzilla_bug_status` varchar(50) DEFAULT NULL,
  `bugzilla_bug_created_at` datetime DEFAULT NULL,
  `bugzilla_bug_resolution` varchar(50) DEFAULT NULL,
  `bugzilla_bug_severity` varchar(50) DEFAULT NULL,
  `bugzilla_bug_priority` varchar(50) DEFAULT NULL,
  `bugzilla_bug_assigned_to` varchar(100) DEFAULT NULL,
  `bugzilla_bug_keyword` varchar(100) DEFAULT NULL,
  `bugzilla_bug_resolved_at` datetime DEFAULT NULL,
  `bugzilla_bug_parent` varchar(100) DEFAULT NULL,
  `bugzilla_bug_product` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1137 DEFAULT CHARSET=utf8mb3;
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
) ENGINE=InnoDB AUTO_INCREMENT=297 DEFAULT CHARSET=utf8mb3;
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
) ENGINE=InnoDB AUTO_INCREMENT=92 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `report_bugzilla_query_by_keyword`
--

DROP TABLE IF EXISTS `report_bugzilla_query_by_keyword`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `report_bugzilla_query_by_keyword` (
  `id` int NOT NULL AUTO_INCREMENT,
  `bugzilla_key` int NOT NULL,
  `bugzilla_summary` text,
  `bugzilla_product` varchar(100) DEFAULT NULL,
  `bugzilla_qa_whiteboard` varchar(255) DEFAULT NULL,
  `bugzilla_bug_severity` varchar(50) DEFAULT NULL,
  `bugzilla_bug_priority` varchar(50) DEFAULT NULL,
  `bugzilla_bug_status` varchar(50) DEFAULT NULL,
  `bugzilla_bug_resolution` varchar(50) DEFAULT NULL,
  `bugzilla_bug_created_at` datetime DEFAULT NULL,
  `bugzilla_bug_last_change_time` datetime DEFAULT NULL,
  `bugzilla_bug_whiteboard` varchar(255) DEFAULT NULL,
  `bugzilla_bug_keyword` varchar(255) DEFAULT NULL,
  `bugzilla_bug_resolved_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_bugzilla_key` (`bugzilla_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `report_bugzilla_softvision_bugs`
--

DROP TABLE IF EXISTS `report_bugzilla_softvision_bugs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `report_bugzilla_softvision_bugs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `bugzilla_key` int NOT NULL,
  `bugzilla_summary` text,
  `bugzilla_product` varchar(255) DEFAULT NULL,
  `bugzilla_qa_whiteboard` varchar(100) DEFAULT NULL,
  `bugzilla_bug_severity` varchar(50) DEFAULT NULL,
  `bugzilla_bug_priority` varchar(50) DEFAULT NULL,
  `bugzilla_bug_status` varchar(50) DEFAULT NULL,
  `bugzilla_bug_resolution` varchar(50) DEFAULT NULL,
  `bugzilla_bug_created_at` datetime DEFAULT NULL,
  `bugzilla_bug_last_change_time` datetime DEFAULT NULL,
  `bugzilla_bug_whiteboard` varchar(100) DEFAULT NULL,
  `bugzilla_bug_keyword` varchar(100) DEFAULT NULL,
  `bugzilla_bug_resolved_at` datetime DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `bugzilla_key` (`bugzilla_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `report_bugzilla_softvision_bugs_sync`
--

DROP TABLE IF EXISTS `report_bugzilla_softvision_bugs_sync`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `report_bugzilla_softvision_bugs_sync` (
  `bugzilla_key` int NOT NULL,
  `bugzilla_summary` text,
  `bugzilla_product` varchar(255) DEFAULT NULL,
  `bugzilla_qa_whiteboard` varchar(100) DEFAULT NULL,
  `bugzilla_bug_severity` varchar(50) DEFAULT NULL,
  `bugzilla_bug_priority` varchar(50) DEFAULT NULL,
  `bugzilla_bug_status` varchar(50) DEFAULT NULL,
  `bugzilla_bug_resolution` varchar(50) DEFAULT NULL,
  `bugzilla_bug_created_at` datetime DEFAULT NULL,
  `bugzilla_bug_last_change_time` datetime DEFAULT NULL,
  `bugzilla_bug_whiteboard` varchar(100) DEFAULT NULL,
  `bugzilla_bug_keyword` varchar(100) DEFAULT NULL,
  `bugzilla_bug_resolved_at` datetime DEFAULT NULL,
  PRIMARY KEY (`bugzilla_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
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
) ENGINE=InnoDB AUTO_INCREMENT=109 DEFAULT CHARSET=utf8mb3;
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
) ENGINE=InnoDB AUTO_INCREMENT=68327 DEFAULT CHARSET=utf8mb3;
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
) ENGINE=InnoDB AUTO_INCREMENT=25619 DEFAULT CHARSET=utf8mb3;
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
  `child_key` varchar(75) DEFAULT NULL,
  `author` varchar(175) NOT NULL,
  `time_spent` varchar(175) NOT NULL,
  `started_date` timestamp NOT NULL,
  `comment` varchar(3000) DEFAULT NULL,
  `time_spent_seconds` int NOT NULL DEFAULT '0',
  `parent_name` varchar(2000) DEFAULT NULL,
  `child_name` varchar(2000) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=652343 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `report_sentry_crash_free_rate_session`
--

DROP TABLE IF EXISTS `report_sentry_crash_free_rate_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `report_sentry_crash_free_rate_session` (
  `id` int NOT NULL AUTO_INCREMENT,
  `crash_free_rate_user` float NOT NULL,
  `crash_free_rate_session` float NOT NULL,
  `release_version` varchar(10) NOT NULL,
  `created_at` timestamp NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8500 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `report_sentry_crash_free_rate_user`
--

DROP TABLE IF EXISTS `report_sentry_crash_free_rate_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `report_sentry_crash_free_rate_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `release_version` varchar(10) NOT NULL,
  `crash_free_rate` float NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8461 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `report_sentry_issues`
--

DROP TABLE IF EXISTS `report_sentry_issues`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `report_sentry_issues` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sentry_id` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `culprit` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `count` int NOT NULL,
  `user_count` int NOT NULL,
  `release_version` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `permalink` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13455 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `report_sentry_rates`
--

DROP TABLE IF EXISTS `report_sentry_rates`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `report_sentry_rates` (
  `id` int NOT NULL AUTO_INCREMENT,
  `crash_free_rate_user` float NOT NULL,
  `crash_free_rate_session` float NOT NULL,
  `adoption_rate_user` float NOT NULL,
  `release_version` varchar(250) NOT NULL,
  `created_at` timestamp NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8617 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
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
) ENGINE=InnoDB AUTO_INCREMENT=63962 DEFAULT CHARSET=utf8mb3;
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
) ENGINE=InnoDB AUTO_INCREMENT=10775 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `report_testrail_test_plans`
--

DROP TABLE IF EXISTS `report_testrail_test_plans`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `report_testrail_test_plans` (
  `id` int NOT NULL AUTO_INCREMENT,
  `testrail_plan_id` int NOT NULL,
  `projects_id` int NOT NULL,
  `name` varchar(75) NOT NULL,
  `test_case_passed_count` int NOT NULL DEFAULT '0',
  `test_case_retest_count` int NOT NULL DEFAULT '0',
  `test_case_failed_count` int NOT NULL DEFAULT '0',
  `test_case_blocked_count` int NOT NULL DEFAULT '0',
  `test_case_total_count` int NOT NULL DEFAULT '0',
  `testrail_created_on` date DEFAULT NULL,
  `testrail_completed_on` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `test_run_projects` (`projects_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1147 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `report_testrail_test_results`
--

DROP TABLE IF EXISTS `report_testrail_test_results`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `report_testrail_test_results` (
  `id` int NOT NULL AUTO_INCREMENT,
  `testrail_result_id` int NOT NULL,
  `run_id` int NOT NULL,
  `test_id` int NOT NULL,
  `elapsed` float(5,2) NOT NULL,
  `status_id` int NOT NULL,
  `testrail_created_on` date DEFAULT NULL,
  `testrail_completed_on` timestamp NULL DEFAULT NULL,
  `type` varchar(55) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `report_testrail_test_results` (`run_id`)
) ENGINE=InnoDB AUTO_INCREMENT=28294 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `report_testrail_test_results_beta`
--

DROP TABLE IF EXISTS `report_testrail_test_results_beta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `report_testrail_test_results_beta` (
  `id` int NOT NULL AUTO_INCREMENT,
  `testrail_result_id` int NOT NULL,
  `run_id` int NOT NULL,
  `test_id` int NOT NULL,
  `elapsed` int NOT NULL,
  `status_id` int NOT NULL,
  `testrail_created_on` date DEFAULT NULL,
  `testrail_completed_on` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `test_result_runs_beta` (`run_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `report_testrail_test_results_l10n`
--

DROP TABLE IF EXISTS `report_testrail_test_results_l10n`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `report_testrail_test_results_l10n` (
  `id` int NOT NULL AUTO_INCREMENT,
  `testrail_result_id` int NOT NULL,
  `run_id` int NOT NULL,
  `test_id` int NOT NULL,
  `elapsed` int NOT NULL,
  `status_id` int NOT NULL,
  `testrail_created_on` date DEFAULT NULL,
  `testrail_completed_on` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `test_result_runs_l10n` (`run_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `report_testrail_test_runs`
--

DROP TABLE IF EXISTS `report_testrail_test_runs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `report_testrail_test_runs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `testrail_run_id` int NOT NULL,
  `plan_id` int NOT NULL,
  `suite_id` int NOT NULL,
  `name` varchar(75) NOT NULL,
  `config` varchar(55) NOT NULL,
  `test_case_passed_count` int NOT NULL DEFAULT '0',
  `test_case_retest_count` int NOT NULL DEFAULT '0',
  `test_case_failed_count` int NOT NULL DEFAULT '0',
  `test_case_blocked_count` int NOT NULL DEFAULT '0',
  `test_case_total_count` int NOT NULL DEFAULT '0',
  `testrail_created_on` date DEFAULT NULL,
  `testrail_completed_on` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `test_run_plans` (`plan_id`)
) ENGINE=InnoDB AUTO_INCREMENT=68923 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `report_testrail_users`
--

DROP TABLE IF EXISTS `report_testrail_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `report_testrail_users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `status` varchar(50) NOT NULL,
  `role` varchar(100) NOT NULL,
  `created_at` timestamp NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13015 DEFAULT CHARSET=utf8mb3;
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
-- Table structure for table `test_plans`
--

DROP TABLE IF EXISTS `test_plans`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `test_plans` (
  `id` int NOT NULL AUTO_INCREMENT,
  `testrail_plan_id` int NOT NULL,
  `projects_id` int NOT NULL,
  `name` varchar(75) NOT NULL,
  `test_case_passed_count` int NOT NULL DEFAULT '0',
  `test_case_retest_count` int NOT NULL DEFAULT '0',
  `test_case_failed_count` int NOT NULL DEFAULT '0',
  `test_case_blocked_count` int NOT NULL DEFAULT '0',
  `test_case_total_count` int NOT NULL DEFAULT '0',
  `testrail_created_on` date DEFAULT NULL,
  `testrail_completed_on` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `test_run_projects` (`projects_id`),
  CONSTRAINT `test_run_projects` FOREIGN KEY (`projects_id`) REFERENCES `projects` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=56 DEFAULT CHARSET=utf8mb3;
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
-- Table structure for table `test_runs`
--

DROP TABLE IF EXISTS `test_runs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `test_runs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `testrail_run_id` int NOT NULL,
  `plan_id` int NOT NULL,
  `suite_id` int NOT NULL,
  `name` varchar(75) NOT NULL,
  `config` varchar(55) NOT NULL,
  `test_case_passed_count` int NOT NULL DEFAULT '0',
  `test_case_retest_count` int NOT NULL DEFAULT '0',
  `test_case_failed_count` int NOT NULL DEFAULT '0',
  `test_case_blocked_count` int NOT NULL DEFAULT '0',
  `test_case_total_count` int NOT NULL DEFAULT '0',
  `testrail_created_on` date DEFAULT NULL,
  `testrail_completed_on` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `test_run_plans` (`plan_id`),
  CONSTRAINT `test_run_plans` FOREIGN KEY (`plan_id`) REFERENCES `test_plans` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2805 DEFAULT CHARSET=utf8mb3;
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
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb3;
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
) ENGINE=InnoDB AUTO_INCREMENT=26073 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

--
-- Table structure for table `report_bugzilla_query_release_flags_for_bugs`
--

DROP TABLE IF EXISTS `report_bugzilla_query_release_flags_for_bugs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `report_bugzilla_query_release_flags_for_bugs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `bugzilla_key` int NOT NULL,
  `bugzilla_release_version` int NOT NULL,
  `bugzilla_bug_status` varchar(100) DEFAULT NULL,
  `bugzilla_bug_keywords` varchar(250) DEFAULT NULL,
  `bugzilla_bug_severity` varchar(100) DEFAULT NULL,
  `bugzilla_bug_qa_found_in` varchar(500) DEFAULT NULL,
  `bugzilla_bug_resolution` varchar(100) DEFAULT NULL,
  `bugzilla_bug_flag_fixed_at` datetime DEFAULT NULL,
  `bugzilla_bug_type` varchar(100) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6441 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `report_bugzilla_overall_bugs`
--

DROP TABLE IF EXISTS `report_bugzilla_overall_bugs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `report_bugzilla_overall_bugs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `bugzilla_key` int NOT NULL,
  `bugzilla_summary` text,
  `bugzilla_product` varchar(255) DEFAULT NULL,
  `bugzilla_qa_whiteboard` varchar(500) DEFAULT NULL,
  `bugzilla_bug_severity` varchar(50) DEFAULT NULL,
  `bugzilla_bug_priority` varchar(50) DEFAULT NULL,
  `bugzilla_bug_status` varchar(50) DEFAULT NULL,
  `bugzilla_bug_resolution` varchar(50) DEFAULT NULL,
  `bugzilla_bug_created_at` datetime DEFAULT NULL,
  `bugzilla_bug_last_change_time` datetime DEFAULT NULL,
  `bugzilla_bug_whiteboard` varchar(500) DEFAULT NULL,
  `bugzilla_bug_keyword` varchar(500) DEFAULT NULL,
  `bugzilla_bug_resolved_at` datetime DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `bugzilla_key` (`bugzilla_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;


DROP TABLE IF EXISTS `report_new_github_issues`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `report_new_github_issues` (
  `id` int NOT NULL AUTO_INCREMENT,
  `number` int NOT NULL,
  `title` varchar(250) DEFAULT NULL,
  `url` varchar(250) DEFAULT NULL,
  `state` varchar(50) DEFAULT NULL,
  `issue_created_at` datetime DEFAULT NULL,
  `issue_updated_at` datetime DEFAULT NULL,
  `issue_closed_at` datetime DEFAULT NULL,
  `user` varchar(250) DEFAULT NULL,
  `author_association` varchar(100) DEFAULT NULL,
  `project` varchar(250) DEFAULT NULL,
  `created_timestamp` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;