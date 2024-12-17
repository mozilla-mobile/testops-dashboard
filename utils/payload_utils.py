import re


class PayloadUtils:

    def extract_testing_status(description):
        if isinstance(description, str):  # Check if description is a string
            match = re.search(r"TESTING_STATUS: \[([^\]]+)\]", description)
            if match:
                return match.group(1)
        return None  # Return No

    def extract_testing_recommendation(description):
        if isinstance(description, str):  # Check if description is a string
            match = re.search(r"QA_RECOMMENDATION: \[([^\]]+)\]", description)
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
