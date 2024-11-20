import yaml

from snowbird.models import SnowbirdModel
from snowbird.resources import _create_roles_execution_plan

test_spec = """
roles:
    - snowbird_integration_test_role: {}
"""


def test_role_is_created_with_no_privileges():
    test_d = yaml.safe_load(test_spec)
    spec = SnowbirdModel(**test_d)
    result = _create_roles_execution_plan(spec.roles)
    expected = [
        "USE ROLE USERADMIN",
        "CREATE ROLE IF NOT EXISTS snowbird_integration_test_role",
        "GRANT ROLE snowbird_integration_test_role TO ROLE SYSADMIN",
    ]
    assert result == expected
