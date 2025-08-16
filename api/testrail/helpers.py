from database import (
    Database,
    Projects,
)


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

	db = _db()

	# Query with filtering

	if isinstance(project, list):
		q = (
			db.session.query(Projects)
			.filter(Projects.project_name_abbrev.in_(project))
		)
	else:
		q = (
			db.session.query(Projects)
			.filter(Projects.project_name_abbrev == project)
		)

	# Fetch results
	results = q.all()
	project_ids_list = [
		[project.id, project.testrail_project_id] for project in results
	]

	print(project_ids_list)
	return project_ids_list
