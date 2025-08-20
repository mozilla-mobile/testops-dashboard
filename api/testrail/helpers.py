#! /usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


from database import (
    Database,
    Projects,
)


_DB = None


def _db() -> Database():
    global _DB
    if _DB is None:
        _DB = Database()
    return _DB


"""
TODO: this function was removed from ./database.py in 2021.  i
It is still invoked by: api/testrail/api_testrail.py testrail_run_counts_update

Could possibly be replaced by testrail_project_ids

def testrail_identity_ids(project):
        # Return the ids needed to be able to query the TestRail API for
        # a specific test suite from a specific project
        # projects.id = projects table id
        # testrail_id = id of project in testrail
        # testrail_functional_test_suite_id = Full Functional Tests Suite id
        # Note:
        #  As these will never change, we store them in db for convenience
        q = self.session.query(Projects)
        p = q.filter_by(project_name_abbrev=project).first()
        return p.id, p.testrail_id, p.testrail_functional_test_suite_id
"""


def testrail_project_ids(project):
    """ Return the ids needed to be able to query the TestRail API for
    a specific test suite from a specific project

    [0]. projects.id = id of project in database table: projects
    [1]. testrail_id = id of project in testrail

    Note:
     - Testrail project ids will never change, so we store them
       in DB for convenience and use them to query test suites
       from each respective project
    """

    print("-------------------------")
    print("HELPERS")
    print("-------------------------")
    print(f"project: {project}")

    db = _db()

    # Query with filtering

    if isinstance(project, list):
        print("IS instance project")
        q = (
            db.session.query(Projects)
            .filter(Projects.project_name_abbrev.in_(project))
        )
    else:
        print("IS NOT instance project")
        q = (
            db.session.query(Projects)
            .filter(Projects.project_name_abbrev == project)
        )

    # Fetch results
    results = q.all()
    project_ids_list = [
        [project.id, project.testrail_project_id] for project in results
    ]

    print(f"project_ids_list: {project_ids_list}")

    return project_ids_list
