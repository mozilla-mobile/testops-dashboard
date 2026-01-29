import re


class PayloadUtils:

    def extract_testing_status(description):
        if isinstance(description, str):  # Check if description is a string
            match = re.search(r"TESTING_STATUS:\s*\[\s*([A-Za-z]+)\s*\]", description)
            if match:
                return match.group(1).upper()
        return None  # Return No

    def extract_testing_recommendation(description):
        if isinstance(description, str):  # Check if description is a string
            match = re.search(r"QA_RECOMMENDATION:\s*\[([^\]]+)\]", description) # noqa
            if match:
                return match.group(1)
        return None  # Return No

    def extract_build_name(name):
        if isinstance(name, str):  # Check if description is a string
            match = re.search(r"Build Validation sign-off - (.+)", name)
            if match:
                return match.group(1)
        return None

    def extract_build_version(build_name):
        if isinstance(build_name, str):  # Check if description is a string
            match = re.search(r"(\d+\.\d+\w*)", build_name)
            if match:
                return match.group(1)
        return None

    def extract_plan_info(plan):
        # Extracts and aggregates the counts and other info for a single plan.
        count_keys = ['passed_count', 'failed_count', 'untested_count', 'blocked_count', 'retest_count'] # noqa
        other_keys = ['id',
                      'project_id',
                      'name',
                      'created_on',
                      'completed_on']
        plan_info = {k: plan[k] for k in count_keys}
        plan_info['total_count'] = sum(plan_info.values())
        plan_info |= {k: plan[k] for k in other_keys}
        plan_info['plan_id'] = plan_info.pop('id')
        return plan_info
