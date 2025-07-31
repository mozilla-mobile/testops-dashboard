#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from sqlalchemy import Table

from lib.database_conn import Session, Base


class Projects(Base):
    __table__ = Table('projects', Base.metadata, autoload=True)


class TestAutomationStatus(Base):
    __table__ = Table('test_automation_status', Base.metadata, autoload=True)


class TestAutomationCoverage(Base):
    __table__ = Table('test_automation_coverage', Base.metadata, autoload=True)


class TestSuites(Base):
    __table__ = Table('test_suites', Base.metadata, autoload=True)


class TestSubSuites(Base):
    __table__ = Table('test_sub_suites', Base.metadata, autoload=True)


class ReportTestCaseCoverage(Base):
    __table__ = Table('report_test_case_coverage', Base.metadata, autoload=True)  # noqa


# class ReportTestRunCounts(Base):
#    __table__ = Table('report_test_run_counts', Base.metadata, autoload=True)

class ReportTestRailTestPlans(Base):
    __table__ = Table('report_testrail_test_plans', Base.metadata, autoload=True)


class ReportTestRailTestRuns(Base):
    __table__ = Table('report_testrail_test_runs', Base.metadata, autoload=True)


class ReportGithubIssues(Base):
    __table__ = Table('report_github_issues', Base.metadata, autoload=True)


class ReportJiraQARequests(Base):
    __table__ = Table('report_jira_qa_requests', Base.metadata, autoload=True)  # noqa


class ReportJiraQANeeded(Base):
    __table__ = Table('report_jira_qa_needed', Base.metadata, autoload=True)  # noqa


class ReportBugzillaQENeeded(Base):
    __table__ = Table('report_bugzilla_qe_needed', Base.metadata, autoload=True)  # noqa


class ReportBugzillaQEVerifyCount(Base):
    __table__ = Table('report_bugzilla_qe_needed_count', Base.metadata, autoload=True)  # noqa


class ReportTestRailMilestones(Base):
    __table__ = Table('report_testrail_milestones', Base.metadata, autoload=True)  # noqa


class ReportTestRailUsers(Base):
    __table__ = Table('report_testrail_users', Base.metadata, autoload=True)  # noqa


class ReportJiraSoftvisionWorklogs(Base):
    __table__ = Table('report_jira_softvision_worklogs', Base.metadata, autoload=True)  # noqa


class ReportBitriseBuildsCount(Base):
    __table__ = Table('report_bitrise_builds_count', Base.metadata, autoload=True)  # noqa


class ReportSentryIssues(Base):
    __table__ = Table('report_sentry_issues', Base.metadata, autoload=True)  # noqa


class ReportSentryRates(Base):
    __table__ = Table('report_sentry_rates', Base.metadata, autoload=True)  # noqa


class ReportBugzillaSoftvisionBugs(Base):
    __table__ = Table('report_bugzilla_softvision_bugs', Base.metadata, autoload=True)  # noqa


class ReportTestRailTestResults(Base):
    __table__ = Table('report_testrail_test_results', Base.metadata, autoload=True)  # noqa


class ReportBugzillaMetaBugs(Base):
    __table__ = Table('report_bugzilla_meta_bugs', Base.metadata, autoload=True) # noqa


class Database:
    def __init__(self):
        self.session = Session()

    def clean_table(self, table):
        self.session.query(table).delete()
        self.session.commit()
