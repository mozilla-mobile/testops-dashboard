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
    __table__ = Table('report_test_case_coverage', Base.metadata, autoload=True) # noqa


# class ReportTestRunCounts(Base):
#    __table__ = Table('report_test_run_counts', Base.metadata, autoload=True)


class ReportGithubIssues(Base):
    __table__ = Table('report_github_issues', Base.metadata, autoload=True)


class ReportJiraQARequests(Base):
    __table__ = Table('report_jira_qa_requests', Base.metadata, autoload=True) # noqa


class ReportJiraQANeeded(Base):
    __table__ = Table('report_jira_qa_needed', Base.metadata, autoload=True) # noqa


class ReportBugzillaQENeeded(Base):
    __table__ = Table('report_bugzilla_qe_needed', Base.metadata, autoload=True) # noqa


class ReportBugzillaQEVerifyCount(Base):
    __table__ = Table('report_bugzilla_qe_needed_count', Base.metadata, autoload=True) # noqa


class ReportMilestones(Base):
    __table__ = Table('report_milestones', Base.metadata, autoload=True) # noqa


class Database:

    def __init__(self):
        self.session = Session()
