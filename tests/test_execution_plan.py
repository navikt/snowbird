import pytest

from snowbird.plan import UnmodifiableStateError, execution_plan


def test_create_database():
    config = {
        "databases": [
            {"name": "foo", "schemas": [{"name": "bar"}]},
        ]
    }
    expected = [
        "use role sysadmin",
        "create database if not exists foo",
        "alter database foo set data_retention_time_in_days = 7",
        "create schema if not exists foo.bar",
        "alter schema foo.bar set data_retention_time_in_days = 7",
    ]
    result = execution_plan(config)
    print(result)
    assert result == expected


def test_create_database_with_transient():
    config = {
        "databases": [
            {"name": "foo", "transient": True, "schemas": [{"name": "bar"}]},
        ]
    }
    expected = [
        "use role sysadmin",
        "create transient database if not exists foo",
        "create transient schema if not exists foo.bar",
    ]
    result = execution_plan(config)
    print(result)
    assert result == expected


def test_create_database_with_transient_to_false():
    config = {
        "databases": [
            {"name": "foo", "transient": False, "schemas": [{"name": "bar"}]},
        ]
    }
    expected = [
        "use role sysadmin",
        "create database if not exists foo",
        "alter database foo set data_retention_time_in_days = 7",
        "create schema if not exists foo.bar",
        "alter schema foo.bar set data_retention_time_in_days = 7",
    ]
    result = execution_plan(config)
    print(result)
    assert result == expected


def test_create_database_with_data_retention_time_in_days():
    config = {
        "databases": [
            {
                "name": "foo",
                "data_retention_time_in_days": 30,
                "schemas": [{"name": "bar"}],
            },
        ]
    }
    expected = [
        "use role sysadmin",
        "create database if not exists foo",
        "alter database foo set data_retention_time_in_days = 30",
        "create schema if not exists foo.bar",
        "alter schema foo.bar set data_retention_time_in_days = 30",
    ]
    result = execution_plan(config)
    print(result)
    assert result == expected


def test_do_nothing_when_database_config_equals_state():
    config = {
        "databases": [
            {
                "name": "foo",
                "schemas": [{"name": "bar"}],
                "data_retention_time_in_days": 7,
            },
        ],
    }
    state = {
        "databases": [
            {
                "name": "FOO",
                "options": "",
                "retention_time": "7",
            },
        ],
        "schemas": [
            {
                "name": "BAR",
                "database_name": "FOO",
                "options": "",
                "retention_time": "7",
            },
        ],
    }
    expected = []
    result = execution_plan(config=config, state=state)
    print(result)
    assert result == expected


def test_do_nothing_when_database_transient_config_equals_state():
    config = {
        "databases": [
            {"name": "foo", "transient": True, "schemas": [{"name": "bar"}]},
        ],
    }
    state = {
        "databases": [
            {
                "name": "FOO",
                "options": "TRANSIENT",
                "retention_time": "1",
            },
        ],
        "schemas": [
            {
                "name": "BAR",
                "database_name": "FOO",
                "options": "TRANSIENT",
                "retention_time": "1",
            },
        ],
    }
    expected = []
    result = execution_plan(config=config, state=state)
    print(result)
    assert result == expected


def test_modifying_data_retention_time_in_days_on_database():
    config = {
        "databases": [
            {
                "name": "foo",
                "data_retention_time_in_days": 30,
                "schemas": [{"name": "bar"}],
            },
        ],
    }
    state = {
        "databases": [
            {
                "name": "FOO",
                "options": "",
                "retention_time": "7",
            },
        ],
        "schemas": [
            {
                "name": "BAR",
                "database_name": "FOO",
                "options": "",
                "retention_time": "7",
            },
        ],
    }
    expected = [
        "use role sysadmin",
        "alter database foo set data_retention_time_in_days = 30",
        "alter schema foo.bar set data_retention_time_in_days = 30",
    ]
    result = execution_plan(config=config, state=state)
    print(result)
    assert result == expected


def test_raise_exception_when_modifying_transient_state_of_database():
    config = {
        "databases": [
            {
                "name": "foo",
                "transient": False,
                "schemas": [{"name": "bar"}],
            },
        ],
    }
    state = {
        "databases": [
            {
                "name": "FOO",
                "options": "TRANSIENT",
                "retention_time": "1",
            },
        ],
        "schemas": [
            {
                "name": "BAR",
                "database_name": "FOO",
                "options": "TRANSIENT",
                "retention_time": "1",
            },
        ],
    }
    with pytest.raises(UnmodifiableStateError) as e:
        execution_plan(config=config, state=state)


def test_create_schema_with_transient():
    config = {
        "databases": [
            {
                "name": "foo",
                "schemas": [{"name": "bar", "transient": True}],
            },
        ]
    }
    expected = [
        "use role sysadmin",
        "create database if not exists foo",
        "alter database foo set data_retention_time_in_days = 7",
        "create transient schema if not exists foo.bar",
    ]
    result = execution_plan(config)
    print(result)
    assert result == expected


def test_create_schema_with_data_retention_time_in_days():
    config = {
        "databases": [
            {
                "name": "foo",
                "schemas": [{"name": "bar", "data_retention_time_in_days": 30}],
            },
        ]
    }
    expected = [
        "use role sysadmin",
        "create database if not exists foo",
        "alter database foo set data_retention_time_in_days = 7",
        "create schema if not exists foo.bar",
        "alter schema foo.bar set data_retention_time_in_days = 30",
    ]
    result = execution_plan(config)
    print(result)
    assert result == expected


def test_create_multiple_schemas():
    config = {
        "databases": [
            {
                "name": "foo",
                "schemas": [{"name": "bar"}, {"name": "baz"}],
            },
        ]
    }
    expected = [
        "use role sysadmin",
        "create database if not exists foo",
        "alter database foo set data_retention_time_in_days = 7",
        "create schema if not exists foo.bar",
        "alter schema foo.bar set data_retention_time_in_days = 7",
        "create schema if not exists foo.baz",
        "alter schema foo.baz set data_retention_time_in_days = 7",
    ]
    result = execution_plan(config)
    print(result)
    assert result == expected


def test_create_warehouse():
    config = {
        "warehouses": [
            {"name": "foo"},
        ]
    }
    expected = [
        "use role sysadmin",
        "create warehouse if not exists foo with warehouse_size = 'x-small' auto_suspend = 30 initially_suspended = true",
        "alter warehouse foo set warehouse_size = 'x-small'",
    ]
    result = execution_plan(config)
    print(result)
    assert result == expected


def test_create_warehouse_with_size():
    config = {
        "warehouses": [
            {"name": "foo", "size": "large"},
        ]
    }
    expected = [
        "use role sysadmin",
        "create warehouse if not exists foo with warehouse_size = 'large' auto_suspend = 30 initially_suspended = true",
        "alter warehouse foo set warehouse_size = 'large'",
    ]
    result = execution_plan(config)
    print(result)
    assert result == expected


def test_create_multiple_warehouses():
    config = {
        "warehouses": [
            {"name": "foo"},
            {"name": "bar"},
        ]
    }
    expected = [
        "use role sysadmin",
        "create warehouse if not exists foo with warehouse_size = 'x-small' auto_suspend = 30 initially_suspended = true",
        "alter warehouse foo set warehouse_size = 'x-small'",
        "create warehouse if not exists bar with warehouse_size = 'x-small' auto_suspend = 30 initially_suspended = true",
        "alter warehouse bar set warehouse_size = 'x-small'",
    ]
    result = execution_plan(config)
    print(result)
    assert result == expected


def test_do_nothing_when_warehouse_config_equals_state():
    config = {
        "warehouses": [
            {"name": "foo"},
        ]
    }
    state = {
        "warehouses": [
            {
                "name": "FOO",
                "size": "X-SMALL",
            }
        ]
    }
    expected = []
    result = execution_plan(config=config, state=state)
    print(result)
    assert result == expected


def test_modifying_warehouse_size():
    config = {
        "warehouses": [
            {"name": "foo", "size": "large"},
        ]
    }
    state = {
        "warehouses": [
            {
                "name": "FOO",
                "size": "X-SMALL",
            }
        ]
    }
    expected = [
        "use role sysadmin",
        "alter warehouse foo set warehouse_size = 'large'",
    ]
    result = execution_plan(config=config, state=state)
    print(result)
    assert result == expected


def test_create_user():
    config = {
        "users": [
            {"name": "foo", "type": "role", "network_policy": "foo_policy"},
        ]
    }
    expected = [
        "use role useradmin",
        "create user if not exists foo type = role network_policy = foo_policy",
        "alter user foo set type = role network_policy = foo_policy",
    ]
    result = execution_plan(config)
    print(result)
    assert result == expected


def test_create_multiple_users():
    config = {
        "users": [
            {"name": "foo", "type": "role", "network_policy": "foo_policy"},
            {"name": "bar", "type": "another_role", "network_policy": "bar_policy"},
        ]
    }
    expected = [
        "use role useradmin",
        "create user if not exists foo type = role network_policy = foo_policy",
        "alter user foo set type = role network_policy = foo_policy",
        "create user if not exists bar type = another_role network_policy = bar_policy",
        "alter user bar set type = another_role network_policy = bar_policy",
    ]
    result = execution_plan(config)
    print(result)
    assert result == expected


def test_do_nothing_when_user_config_equals_state():
    config = {
        "users": [
            {"name": "foo", "type": "role", "network_policy": "foo_policy"},
        ]
    }
    state = {
        "users": [
            {
                "name": "FOO",
                "type": "ROLE",
                "network_policy": "FOO_POLICY",
            }
        ]
    }
    expected = []
    result = execution_plan(config=config, state=state)
    print(result)
    assert result == expected


def test_modifying_user_type():
    config = {
        "users": [
            {"name": "foo", "type": "bar", "network_policy": "foo_policy"},
        ]
    }
    state = {
        "users": [
            {
                "name": "FOO",
                "type": "ROLE",
                "network_policy": "FOO_POLICY",
            }
        ]
    }
    expected = [
        "use role useradmin",
        "alter user foo set type = bar network_policy = foo_policy",
    ]
    result = execution_plan(config=config, state=state)
    print(result)
    assert result == expected


def test_modifying_user_network_policy():
    config = {
        "users": [
            {"name": "foo", "type": "foo", "network_policy": "bar"},
        ]
    }
    state = {
        "users": [
            {
                "name": "FOO",
                "type": "FOO",
                "network_policy": "FOO_POLICY",
            }
        ]
    }
    expected = [
        "use role useradmin",
        "alter user foo set type = foo network_policy = bar",
    ]
    result = execution_plan(config=config, state=state)
    print(result)
    assert result == expected


def test_create_role():
    config = {
        "roles": [
            {"name": "foo"},
        ]
    }
    expected = [
        "use role useradmin",
        "create role if not exists foo",
    ]
    result = execution_plan(config)
    print(result)
    assert result == expected


def test_do_nothing_when_role_config_equals_state():
    config = {
        "roles": [
            {"name": "foo"},
        ]
    }
    state = {
        "roles": [
            {
                "name": "FOO",
            }
        ],
        "grants": {
            "of_roles": {
                "foo": [
                    {
                        "grantee_name": "SYSADMIN",
                        "granted_to": "ROLE",
                    }
                ]
            }
        },
    }
    expected = []
    result = execution_plan(config=config, state=state)
    print(result)
    assert result == expected


def test_create_network_policy():
    config = {
        "network_policies": [
            {
                "name": "foo_policy",
                "network_rules": {
                    "allowed": ["snowbird_test.staging.snowbird_test_network_rule"]
                },
            }
        ]
    }
    expected = [
        "use role securityadmin",
        "create network policy if not exists foo_policy allowed_network_rule_list = ( 'snowbird_test.staging.snowbird_test_network_rule' ) blocked_network_rule_list = ( ) comment = ''",
        "alter network policy foo_policy set allowed_network_rule_list = ( 'snowbird_test.staging.snowbird_test_network_rule' ) blocked_network_rule_list = ( ) comment = ''",
    ]
    result = execution_plan(config)
    print(result)
    assert result == expected


def test_do_nothing_when_network_policy_config_equals_state():
    config = {
        "network_policies": [
            {
                "name": "foo_policy",
                "network_rules": {"allowed": ["foo.bar.baz"]},
            }
        ]
    }
    state = {
        "network_policies": {
            "foo_policy": {
                "allowed_network_rule_list": [
                    {"fullyQualifiedRuleName": "FOO.BAR.BAZ"},
                ],
                "blocked_network_rule_list": [],
                "comment": "",
            }
        }
    }
    expected = []
    result = execution_plan(config=config, state=state)
    print(result)
    assert result == expected


def test_modifying_network_policy_comment():
    config = {
        "network_policies": [
            {
                "name": "foo_policy",
                "description": "new comment",
                "network_rules": {"allowed": ["foo"]},
            }
        ]
    }
    state = {
        "network_policies": {
            "foo_policy": {
                "allowed_network_rule_list": [{"fullyQualifiedRuleName": "FOO"}],
                "blocked_network_rule_list": [],
                "comment": "old comment",
            }
        }
    }
    expected = [
        "use role securityadmin",
        "alter network policy foo_policy set allowed_network_rule_list = ( 'foo' ) blocked_network_rule_list = ( ) comment = 'new comment'",
    ]
    result = execution_plan(config=config, state=state)
    print(result)
    assert result == expected


def test_modifying_network_policy_allowed_network_rules():
    config = {
        "network_policies": [
            {
                "name": "foo_policy",
                "network_rules": {"allowed": ["new_rule"]},
            }
        ]
    }
    state = {
        "network_policies": {
            "foo_policy": {
                "allowed_network_rule_list": [{"fullyQualifiedRuleName": "OLD_RULE"}],
                "blocked_network_rule_list": [],
                "comment": "",
            }
        }
    }
    expected = [
        "use role securityadmin",
        "alter network policy foo_policy set allowed_network_rule_list = ( 'new_rule' ) blocked_network_rule_list = ( ) comment = ''",
    ]
    result = execution_plan(config=config, state=state)
    print(result)
    assert result == expected


def test_modifying_network_policy_blocked_network_rules():
    config = {
        "network_policies": [
            {
                "name": "foo_policy",
                "network_rules": {"blocked": ["new_blocked_rule"]},
            }
        ]
    }
    state = {
        "network_policies": {
            "foo_policy": {
                "allowed_network_rule_list": [],
                "blocked_network_rule_list": [
                    {"fullyQualifiedRuleName": "OLD_BLOCKED_RULE"}
                ],
                "comment": "",
            }
        }
    }
    expected = [
        "use role securityadmin",
        "alter network policy foo_policy set allowed_network_rule_list = ( ) blocked_network_rule_list = ( 'new_blocked_rule' ) comment = ''",
    ]
    result = execution_plan(config=config, state=state)
    print(result)
    assert result == expected


def test_grant_role_warehouse():
    config = {"grants": [{"role": "foo", "warehouses": ["bar"]}]}
    expected = [
        "use role useradmin",
        "grant usage on warehouse bar to role foo",
        'grant role foo to role "SYSADMIN"',
    ]
    result = execution_plan(config)
    print(result)
    assert result == expected


def test_grant_role_multiple_warehouses():
    config = {"grants": [{"role": "foo", "warehouses": ["bar", "baz"]}]}
    expected = [
        "use role useradmin",
        "grant usage on warehouse bar to role foo",
        "grant usage on warehouse baz to role foo",
        'grant role foo to role "SYSADMIN"',
    ]
    result = execution_plan(config)
    print(result)
    assert result == expected


def test_grant_role_write_on_schema():
    config = {"grants": [{"role": "foo", "write_on_schemas": ["bar.baz"]}]}
    expected = [
        "use role useradmin",
        "grant usage on database bar to role foo",
        "grant usage on schema bar.baz to role foo",
        "grant create table on schema bar.baz to role foo",
        "grant create view on schema bar.baz to role foo",
        "grant create dynamic table on schema bar.baz to role foo",
        "grant create task on schema bar.baz to role foo",
        "grant create alert on schema bar.baz to role foo",
        'grant role foo to role "SYSADMIN"',
    ]
    result = execution_plan(config)
    print(result)
    assert result == expected


def test_grant_role_write_on_multiple_schemas():
    config = {"grants": [{"role": "foo", "write_on_schemas": ["bar.baz", "bar.qux"]}]}
    expected = [
        "use role useradmin",
        "grant usage on database bar to role foo",
        "grant usage on schema bar.baz to role foo",
        "grant create table on schema bar.baz to role foo",
        "grant create view on schema bar.baz to role foo",
        "grant create dynamic table on schema bar.baz to role foo",
        "grant create task on schema bar.baz to role foo",
        "grant create alert on schema bar.baz to role foo",
        "grant usage on database bar to role foo",
        "grant usage on schema bar.qux to role foo",
        "grant create table on schema bar.qux to role foo",
        "grant create view on schema bar.qux to role foo",
        "grant create dynamic table on schema bar.qux to role foo",
        "grant create task on schema bar.qux to role foo",
        "grant create alert on schema bar.qux to role foo",
        'grant role foo to role "SYSADMIN"',
    ]
    result = execution_plan(config)
    print(result)
    assert result == expected


def test_grant_role_read_on_schema():
    config = {"grants": [{"role": "foo", "read_on_schemas": ["bar.baz"]}]}
    expected = [
        "use role useradmin",
        "grant usage on database bar to role foo",
        "grant usage on schema bar.baz to role foo",
        "grant select on all tables in schema bar.baz to role foo",
        "grant select on future tables in schema bar.baz to role foo",
        "grant select on all views in schema bar.baz to role foo",
        "grant select on future views in schema bar.baz to role foo",
        'grant role foo to role "SYSADMIN"',
    ]
    result = execution_plan(config)
    print(result)
    assert result == expected


def test_grant_role_read_on_multiple_schemas():
    config = {"grants": [{"role": "foo", "read_on_schemas": ["bar.baz", "bar.qux"]}]}
    expected = [
        "use role useradmin",
        "grant usage on database bar to role foo",
        "grant usage on schema bar.baz to role foo",
        "grant select on all tables in schema bar.baz to role foo",
        "grant select on future tables in schema bar.baz to role foo",
        "grant select on all views in schema bar.baz to role foo",
        "grant select on future views in schema bar.baz to role foo",
        "grant usage on database bar to role foo",
        "grant usage on schema bar.qux to role foo",
        "grant select on all tables in schema bar.qux to role foo",
        "grant select on future tables in schema bar.qux to role foo",
        "grant select on all views in schema bar.qux to role foo",
        "grant select on future views in schema bar.qux to role foo",
        'grant role foo to role "SYSADMIN"',
    ]
    result = execution_plan(config)
    print(result)
    assert result == expected


def test_grant_role_to_role():
    config = {"grants": [{"role": "foo", "to_roles": ["bar"]}]}
    expected = [
        "use role useradmin",
        'grant role foo to role "BAR"',
        'grant role foo to role "SYSADMIN"',
    ]
    result = execution_plan(config)
    print(result)
    assert result == expected


def test_grant_role_to_multiple_roles():
    config = {"grants": [{"role": "foo", "to_roles": ["bar", "baz"]}]}
    expected = [
        "use role useradmin",
        'grant role foo to role "BAR"',
        'grant role foo to role "BAZ"',
        'grant role foo to role "SYSADMIN"',
    ]
    result = execution_plan(config)
    print(result)
    assert result == expected


def test_grant_role_to_user():
    config = {"grants": [{"role": "foo", "to_users": ["bar"]}]}
    expected = [
        "use role useradmin",
        'grant role foo to role "SYSADMIN"',
        'grant role foo to user "BAR"',
    ]
    result = execution_plan(config)
    print(result)
    assert result == expected


def test_grant_role_to_multiple_users():
    config = {"grants": [{"role": "foo", "to_users": ["bar", "baz"]}]}
    expected = [
        "use role useradmin",
        'grant role foo to role "SYSADMIN"',
        'grant role foo to user "BAR"',
        'grant role foo to user "BAZ"',
    ]
    result = execution_plan(config)
    print(result)
    assert result == expected


def test_revoke_role_from_user():
    config = {
        "grants": [{"role": "foo"}],
    }
    state = {
        "grants": {
            "of_roles": {
                "foo": [
                    {
                        "grantee_name": "BAR",
                        "granted_to": "USER",
                    },
                ]
            }
        },
    }
    expected = [
        "use role useradmin",
        'revoke role foo from user "BAR"',
        'grant role foo to role "SYSADMIN"',
    ]
    result = execution_plan(config=config, state=state)
    print(result)
    assert result == expected


def test_revoke_role_from_role():
    config = {
        "grants": [{"role": "foo"}],
    }
    state = {
        "grants": {
            "of_roles": {
                "foo": [
                    {
                        "grantee_name": "BAR",
                        "granted_to": "ROLE",
                    },
                ]
            }
        },
    }
    expected = [
        "use role useradmin",
        'grant role foo to role "SYSADMIN"',
        'revoke role foo from role "BAR"',
    ]
    result = execution_plan(config=config, state=state)
    print(result)
    assert result == expected


def test_not_revoking_role_from_sysadmin_when_not_explicily_defined():
    config = {
        "grants": [{"role": "foo"}],
    }
    state = {
        "grants": {
            "of_roles": {
                "foo": [
                    {
                        "grantee_name": "SYSADMIN",
                        "granted_to": "ROLE",
                    },
                ]
            }
        },
    }
    expected = []
    result = execution_plan(config=config, state=state)
    print(result)
    assert result == expected


def test_explicit_granting_role_to_sysadmin_should_only_yield_one_grant_statement():
    config = {
        "grants": [{"role": "foo", "to_roles": ["sysadmin"]}],
    }
    expected = ["use role useradmin", 'grant role foo to role "SYSADMIN"']
    result = execution_plan(config=config)
    print(result)
    assert result == expected


def test_switching_executer_role():
    config = {
        "databases": [{"name": "foo", "schemas": [{"name": "bar"}]}],
        "roles": [{"name": "baz"}],
    }
    expected = [
        "use role sysadmin",
        "create database if not exists foo",
        "alter database foo set data_retention_time_in_days = 7",
        "create schema if not exists foo.bar",
        "alter schema foo.bar set data_retention_time_in_days = 7",
        "use role useradmin",
        "create role if not exists baz",
    ]
    result = execution_plan(config)
    print(result)
    assert result == expected
