import logging
import yaml
from click.testing import CliRunner

from snowbird.command import cli
from snowbird.models import SnowbirdModel
from snowbird.resources import _grant_extra_writes_to_roles_execution_plan

test_spec = """
databases:
    - snowbird_integration_test:
        shared: no
        schemas:
            - test
roles:
    - snowbird_integration_test_role:
        privileges:
            databases:
                read:
                    - snowbird_integration_test
                write:
                    - snowbird_integration_test
            schemas:
                read:
                    - snowbird_integration_test.test
                write:
                    - snowbird_integration_test.test
            tables:
                read:
                    - snowbird_integration_test.test.*
                write:
                    - snowbird_integration_test.test.*
"""


def test_extra_write_grants():
    test = """
roles:
    - snowbird_integration_test_role:
        privileges:
            schemas:
                write:
                    - snowbird_integration_test.test
"""

    test_d = yaml.safe_load(test)
    print(test_d)
    spec = SnowbirdModel(**test_d)
    result = _grant_extra_writes_to_roles_execution_plan(spec.roles)
    expects = [
        "use role securityadmin",
        "grant create dynamic table on schema snowbird_integration_test.test to role snowbird_integration_test_role",
        "grant create masking policy on schema snowbird_integration_test.test to role snowbird_integration_test_role",
        "grant create row access policy on schema snowbird_integration_test.test to role snowbird_integration_test_role",
    ]
    print(result)
    assert result == expects

def test_role_is_not_granted_extra_write_privileges_if_privileges_not_specified():
    test_spec = """
roles:
    - snowbird_integration_test_role: {}
"""
    test_d = yaml.safe_load(test_spec)
    logging.error(test_d)
    spec = SnowbirdModel(**test_d)
    result = _grant_extra_writes_to_roles_execution_plan(spec.roles)
    expected = []
    assert result == expected
    