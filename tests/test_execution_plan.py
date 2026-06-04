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
    expected = {
        "use role useradmin",
        "grant usage on warehouse bar to role foo",
        'grant role foo to role "SYSADMIN"',
    }
    result = set(execution_plan(config))
    print(result)
    assert result == expected


def test_grant_role_multiple_warehouses():
    config = {"grants": [{"role": "foo", "warehouses": ["bar", "baz"]}]}
    expected = {
        "use role useradmin",
        "grant usage on warehouse bar to role foo",
        "grant usage on warehouse baz to role foo",
        'grant role foo to role "SYSADMIN"',
    }
    result = set(execution_plan(config))
    print(result)
    assert result == expected


def test_grant_role_write_on_schema():
    config = {"grants": [{"role": "foo", "write_on_schemas": ["bar.baz"]}]}
    expected = {
        'grant role foo to role "SYSADMIN"',
        "grant create dynamic table on schema bar.baz to role foo",
        "grant create row access policy on schema bar.baz to role foo",
        "grant create alert on schema bar.baz to role foo",
        "grant create table on schema bar.baz to role foo",
        "grant create procedure on schema bar.baz to role foo",
        "grant create masking policy on schema bar.baz to role foo",
        "use role useradmin",
        "grant usage on database bar to role foo",
        "grant usage on schema bar.baz to role foo",
        "grant create task on schema bar.baz to role foo",
        "grant create view on schema bar.baz to role foo",
        "grant create semantic view on schema bar.baz to role foo",
    }
    result = set(execution_plan(config))
    print(result)
    assert result == expected


def test_grant_role_write_on_multiple_schemas():
    config = {"grants": [{"role": "foo", "write_on_schemas": ["bar.baz", "bar.qux"]}]}
    expected = {
        "grant create row access policy on schema bar.baz to role foo",
        "grant create procedure on schema bar.qux to role foo",
        "grant create table on schema bar.baz to role foo",
        "grant create table on schema bar.qux to role foo",
        "grant create semantic view on schema bar.baz to role foo",
        "grant create semantic view on schema bar.qux to role foo",
        "grant usage on schema bar.qux to role foo",
        "grant create row access policy on schema bar.qux to role foo",
        "grant create alert on schema bar.qux to role foo",
        "grant create dynamic table on schema bar.qux to role foo",
        "grant create view on schema bar.qux to role foo",
        "grant create masking policy on schema bar.qux to role foo",
        "grant create view on schema bar.baz to role foo",
        "grant usage on database bar to role foo",
        "use role useradmin",
        "grant usage on schema bar.baz to role foo",
        "grant create task on schema bar.baz to role foo",
        'grant role foo to role "SYSADMIN"',
        "grant create dynamic table on schema bar.baz to role foo",
        "grant create alert on schema bar.baz to role foo",
        "grant create masking policy on schema bar.baz to role foo",
        "grant create procedure on schema bar.baz to role foo",
        "grant create task on schema bar.qux to role foo",
    }
    result = set(execution_plan(config))
    print(result)
    assert result == expected


def test_grant_role_read_on_schema():
    config = {"grants": [{"role": "foo", "read_on_schemas": ["bar.baz"]}]}
    expected = {
        "use role useradmin",
        "grant usage on database bar to role foo",
        "grant usage on schema bar.baz to role foo",
        "grant select on all tables in schema bar.baz to role foo",
        "grant select on future tables in schema bar.baz to role foo",
        "grant select on all views in schema bar.baz to role foo",
        "grant select on future views in schema bar.baz to role foo",
        'grant role foo to role "SYSADMIN"',
        "grant select on all dynamic tables in schema bar.baz to role foo",
        "grant select on future dynamic tables in schema bar.baz to role foo",
        "grant select on all semantic views in schema bar.baz to role foo",
        "grant select on future semantic views in schema bar.baz to role foo",
    }
    result = set(execution_plan(config))
    print(result)
    assert result == expected


def test_grant_role_read_on_multiple_schemas():
    config = {"grants": [{"role": "foo", "read_on_schemas": ["bar.baz", "bar.qux"]}]}
    expected = {
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
        "grant select on all dynamic tables in schema bar.baz to role foo",
        "grant select on future dynamic tables in schema bar.baz to role foo",
        "grant select on all dynamic tables in schema bar.qux to role foo",
        "grant select on future dynamic tables in schema bar.qux to role foo",
        "grant select on all semantic views in schema bar.baz to role foo",
        "grant select on future semantic views in schema bar.baz to role foo",
        "grant select on all semantic views in schema bar.qux to role foo",
        "grant select on future semantic views in schema bar.qux to role foo",
    }
    result = set(execution_plan(config))
    print(result)
    assert result == expected


def test_grant_role_read_on_objects():
    config = {
        "grants": [
            {
                "role": "foo",
                "read_on_objects": [
                    "table:bar.baz.my_table",
                    "view:bar.baz.my_view",
                ],
            }
        ]
    }
    result = set(execution_plan(config))
    # Should grant usage on parent db and schema
    assert "grant usage on database bar to role foo" in result
    assert "grant usage on schema bar.baz to role foo" in result
    # Should grant select on specific objects
    assert "grant select on table bar.baz.my_table to role foo" in result
    assert "grant select on view bar.baz.my_view to role foo" in result
    # Should NOT grant select on all tables in schema (that's read_on_schemas)
    assert not any("grant select on all tables" in s for s in result)
    assert not any("grant select on future tables" in s for s in result)


def test_grant_role_read_on_objects_all_types():
    config = {
        "grants": [
            {
                "role": "foo",
                "read_on_objects": [
                    "table:db.sch.t1",
                    "view:db.sch.v1",
                    "dynamic_table:db.sch.dt1",
                    "semantic_view:db.sch.sv1",
                ],
            }
        ]
    }
    result = set(execution_plan(config))
    assert "grant select on table db.sch.t1 to role foo" in result
    assert "grant select on view db.sch.v1 to role foo" in result
    assert "grant select on dynamic table db.sch.dt1 to role foo" in result
    assert "grant select on semantic view db.sch.sv1 to role foo" in result


def test_read_on_objects_invalid_type_prefix_raises_error():
    config = {
        "grants": [
            {
                "role": "foo",
                "read_on_objects": ["invalid_type:db.sch.obj"],
            }
        ]
    }
    with pytest.raises(ValueError, match="Invalid input for object type"):
        execution_plan(config)


def test_read_on_objects_missing_type_prefix_raises_error():
    config = {
        "grants": [
            {
                "role": "foo",
                "read_on_objects": ["db.sch.obj"],
            }
        ]
    }
    with pytest.raises(
        ValueError,
        match="Invalid type_input, must contain exactly one colon between object type and name",
    ):
        execution_plan(config)


def test_read_on_objects_invalid_path_raises_error():
    config = {
        "grants": [
            {
                "role": "foo",
                "read_on_objects": ["table:db.obj"],
            }
        ]
    }
    with pytest.raises(
        ValueError,
        match="Invalid object path db.obj, must be in the format database.schema.object",
    ):
        execution_plan(config)


def test_grant_role_to_role():
    config = {"grants": [{"role": "foo", "to_roles": ["bar"]}]}
    expected = {
        "use role useradmin",
        'grant role foo to role "BAR"',
        'grant role foo to role "SYSADMIN"',
    }
    result = set(execution_plan(config))
    print(result)
    assert result == expected


def test_grant_role_to_multiple_roles():
    config = {"grants": [{"role": "foo", "to_roles": ["bar", "baz"]}]}
    expected = {
        "use role useradmin",
        'grant role foo to role "BAR"',
        'grant role foo to role "BAZ"',
        'grant role foo to role "SYSADMIN"',
    }
    result = set(execution_plan(config))
    print(result)
    assert result == expected


def test_grant_role_to_user():
    config = {"grants": [{"role": "foo", "to_users": ["bar"]}]}
    expected = {
        "use role useradmin",
        'grant role foo to role "SYSADMIN"',
        'grant role foo to user "BAR"',
    }
    result = set(execution_plan(config))
    print(result)
    assert result == expected


def test_grant_role_to_multiple_users():
    config = {"grants": [{"role": "foo", "to_users": ["bar", "baz"]}]}
    expected = {
        "use role useradmin",
        'grant role foo to role "SYSADMIN"',
        'grant role foo to user "BAR"',
        'grant role foo to user "BAZ"',
    }
    result = set(execution_plan(config))
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
    expected = {
        "use role useradmin",
        'revoke role foo from user "BAR"',
        'grant role foo to role "SYSADMIN"',
    }
    result = set(execution_plan(config=config, state=state))
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
    expected = {
        "use role useradmin",
        'grant role foo to role "SYSADMIN"',
        'revoke role foo from role "BAR"',
    }
    result = set(execution_plan(config=config, state=state))
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


def test_grant_warehouse_skipped_when_already_exists():
    config = {"grants": [{"role": "foo", "warehouses": ["bar"]}]}
    state = {
        "grants": {
            "on_warehouses": {
                "bar": [
                    {"privilege": "USAGE", "grantee_name": "FOO"},
                ]
            }
        },
    }
    expected = {
        "use role useradmin",
        'grant role foo to role "SYSADMIN"',
    }
    result = set(execution_plan(config=config, state=state))
    print(result)
    assert result == expected


def test_grant_warehouse_when_not_in_state():
    config = {"grants": [{"role": "foo", "warehouses": ["bar"]}]}
    state = {
        "grants": {"on_warehouses": {"bar": []}},
    }
    expected = {
        "use role useradmin",
        "grant usage on warehouse bar to role foo",
        'grant role foo to role "SYSADMIN"',
    }
    result = set(execution_plan(config=config, state=state))
    print(result)
    assert result == expected


def test_revoke_warehouse_from_unlisted_role():
    config = {"grants": [{"role": "foo", "warehouses": ["bar"]}]}
    state = {
        "grants": {
            "on_warehouses": {
                "bar": [
                    {"privilege": "USAGE", "grantee_name": "FOO"},
                    {"privilege": "USAGE", "grantee_name": "ROGUE_ROLE"},
                ]
            }
        },
    }
    expected = {
        "use role useradmin",
        'grant role foo to role "SYSADMIN"',
        'revoke usage on warehouse bar from role "ROGUE_ROLE"',
    }
    result = set(execution_plan(config=config, state=state))
    print(result)
    assert result == expected


def test_revoke_warehouse_when_not_in_config():
    config = {"grants": [{"role": "foo", "warehouses": ["bar"]}]}
    state = {
        "grants": {
            "on_warehouses": {
                "bar": [
                    {"privilege": "USAGE", "grantee_name": "BAZ"},
                ]
            }
        },
    }
    expected = {
        "use role useradmin",
        "grant usage on warehouse bar to role foo",
        'revoke usage on warehouse bar from role "BAZ"',
        'grant role foo to role "SYSADMIN"',
    }
    result = set(execution_plan(config=config, state=state))
    print(result)
    assert result == expected


def test_grant_and_revoke_warehouse_mixed():
    config = {
        "grants": [
            {"role": "foo", "warehouses": ["wh1", "wh2"]},
        ]
    }
    state = {
        "grants": {
            "on_warehouses": {
                "wh1": [
                    {"privilege": "USAGE", "grantee_name": "FOO"},
                    {"privilege": "USAGE", "grantee_name": "OLD_ROLE"},
                ],
                "wh2": [],
            }
        },
    }
    expected = {
        "use role useradmin",
        "grant usage on warehouse wh2 to role foo",
        'revoke usage on warehouse wh1 from role "OLD_ROLE"',
        'grant role foo to role "SYSADMIN"',
    }
    result = set(execution_plan(config=config, state=state))
    print(result)
    assert result == expected


def test_warehouse_grants_aggregated_across_entries():
    config = {
        "grants": [
            {"role": "foo", "warehouses": ["wh1"]},
            {"role": "bar", "warehouses": ["wh1"]},
        ]
    }
    state = {
        "grants": {
            "on_warehouses": {
                "wh1": [
                    {"privilege": "USAGE", "grantee_name": "OLD_ROLE"},
                ]
            }
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert "grant usage on warehouse wh1 to role foo" in result
    assert "grant usage on warehouse wh1 to role bar" in result
    assert 'revoke usage on warehouse wh1 from role "OLD_ROLE"' in result


def test_warehouse_ownership_not_revoked():
    config = {"grants": [{"role": "foo", "warehouses": ["bar"]}]}
    state = {
        "grants": {
            "on_warehouses": {
                "bar": [
                    {"privilege": "OWNERSHIP", "grantee_name": "SYSADMIN"},
                    {"privilege": "USAGE", "grantee_name": "FOO"},
                ]
            }
        },
    }
    expected = {
        "use role useradmin",
        'grant role foo to role "SYSADMIN"',
    }
    result = set(execution_plan(config=config, state=state))
    print(result)
    assert result == expected


# ===== Database USAGE stateful tests =====


def test_database_usage_skipped_when_already_exists():
    config = {"grants": [{"role": "foo", "read_on_schemas": ["db1.sch1"]}]}
    state = {
        "grants": {
            "on_databases": {
                "db1": [
                    {"privilege": "USAGE", "grantee_name": "FOO"},
                ]
            },
            "on_schemas": {
                "db1.sch1": [
                    {"privilege": "USAGE", "grantee_name": "FOO"},
                ]
            },
            "future_in_schemas": {
                "db1.sch1": [
                    {"privilege": "SELECT", "grant_on": "TABLE", "grantee_name": "FOO"},
                    {"privilege": "SELECT", "grant_on": "VIEW", "grantee_name": "FOO"},
                    {
                        "privilege": "SELECT",
                        "grant_on": "DYNAMIC TABLE",
                        "grantee_name": "FOO",
                    },
                    {
                        "privilege": "SELECT",
                        "grant_on": "SEMANTIC VIEW",
                        "grantee_name": "FOO",
                    },
                ]
            },
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert "grant usage on database db1 to role foo" not in result
    assert 'revoke usage on database db1 from role "FOO"' not in result


def test_database_usage_granted_when_missing():
    config = {"grants": [{"role": "foo", "read_on_schemas": ["db1.sch1"]}]}
    state = {
        "grants": {
            "on_databases": {"db1": []},
            "on_schemas": {"db1.sch1": []},
            "future_in_schemas": {"db1.sch1": []},
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert "grant usage on database db1 to role foo" in result


def test_database_usage_revoked_from_unlisted_role():
    config = {"grants": [{"role": "foo", "read_on_schemas": ["db1.sch1"]}]}
    state = {
        "grants": {
            "on_databases": {
                "db1": [
                    {"privilege": "USAGE", "grantee_name": "FOO"},
                    {"privilege": "USAGE", "grantee_name": "ROGUE"},
                ]
            },
            "on_schemas": {"db1.sch1": []},
            "future_in_schemas": {"db1.sch1": []},
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert "grant usage on database db1 to role foo" not in result
    assert 'revoke usage on database db1 from role "ROGUE"' in result


def test_database_usage_aggregated_across_read_and_write():
    config = {
        "grants": [
            {"role": "reader", "read_on_schemas": ["db1.sch1"]},
            {"role": "writer", "write_on_schemas": ["db1.sch2"]},
        ]
    }
    state = {
        "grants": {
            "on_databases": {
                "db1": [
                    {"privilege": "USAGE", "grantee_name": "OLD_ROLE"},
                ]
            },
            "on_schemas": {"db1.sch1": [], "db1.sch2": []},
            "future_in_schemas": {"db1.sch1": []},
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert "grant usage on database db1 to role reader" in result
    assert "grant usage on database db1 to role writer" in result
    assert 'revoke usage on database db1 from role "OLD_ROLE"' in result


# ===== Schema USAGE stateful tests =====


def test_schema_usage_skipped_when_already_exists():
    config = {"grants": [{"role": "foo", "read_on_schemas": ["db1.sch1"]}]}
    state = {
        "grants": {
            "on_databases": {"db1": []},
            "on_schemas": {
                "db1.sch1": [
                    {"privilege": "USAGE", "grantee_name": "FOO"},
                ]
            },
            "future_in_schemas": {"db1.sch1": []},
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert "grant usage on schema db1.sch1 to role foo" not in result


def test_schema_usage_revoked_from_unlisted_role():
    config = {"grants": [{"role": "foo", "read_on_schemas": ["db1.sch1"]}]}
    state = {
        "grants": {
            "on_databases": {"db1": []},
            "on_schemas": {
                "db1.sch1": [
                    {"privilege": "USAGE", "grantee_name": "FOO"},
                    {"privilege": "USAGE", "grantee_name": "ROGUE"},
                ]
            },
            "future_in_schemas": {"db1.sch1": []},
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert 'revoke usage on schema db1.sch1 from role "ROGUE"' in result


def test_schema_usage_aggregated_across_read_and_write():
    config = {
        "grants": [
            {"role": "reader", "read_on_schemas": ["db1.sch1"]},
            {"role": "writer", "write_on_schemas": ["db1.sch1"]},
        ]
    }
    state = {
        "grants": {
            "on_databases": {"db1": []},
            "on_schemas": {
                "db1.sch1": [
                    {"privilege": "USAGE", "grantee_name": "OLD_ROLE"},
                ]
            },
            "future_in_schemas": {"db1.sch1": []},
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert "grant usage on schema db1.sch1 to role reader" in result
    assert "grant usage on schema db1.sch1 to role writer" in result
    assert 'revoke usage on schema db1.sch1 from role "OLD_ROLE"' in result


def test_schema_usage_aggregated_from_read_on_objects():
    config = {
        "grants": [
            {"role": "obj_reader", "read_on_objects": ["table:db1.sch1.t1"]},
        ]
    }
    state = {
        "grants": {
            "on_databases": {"db1": []},
            "on_schemas": {
                "db1.sch1": [
                    {"privilege": "USAGE", "grantee_name": "ROGUE"},
                ]
            },
            "on_objects": {"table:db1.sch1.t1": []},
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert "grant usage on schema db1.sch1 to role obj_reader" in result
    assert 'revoke usage on schema db1.sch1 from role "ROGUE"' in result


# ===== Future read grants stateful tests =====


def test_future_read_skipped_when_already_exists():
    config = {"grants": [{"role": "foo", "read_on_schemas": ["db1.sch1"]}]}
    state = {
        "grants": {
            "on_databases": {"db1": []},
            "on_schemas": {"db1.sch1": []},
            "future_in_schemas": {
                "db1.sch1": [
                    {"privilege": "SELECT", "grant_on": "TABLE", "grantee_name": "FOO"},
                    {"privilege": "SELECT", "grant_on": "VIEW", "grantee_name": "FOO"},
                    {
                        "privilege": "SELECT",
                        "grant_on": "DYNAMIC TABLE",
                        "grantee_name": "FOO",
                    },
                    {
                        "privilege": "SELECT",
                        "grant_on": "SEMANTIC VIEW",
                        "grantee_name": "FOO",
                    },
                ]
            },
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert "grant select on future tables in schema db1.sch1 to role foo" not in result
    assert "grant select on future views in schema db1.sch1 to role foo" not in result
    assert (
        "grant select on future dynamic tables in schema db1.sch1 to role foo"
        not in result
    )
    assert (
        "grant select on future semantic views in schema db1.sch1 to role foo"
        not in result
    )


def test_future_read_granted_when_missing():
    config = {"grants": [{"role": "foo", "read_on_schemas": ["db1.sch1"]}]}
    state = {
        "grants": {
            "on_databases": {"db1": []},
            "on_schemas": {"db1.sch1": []},
            "future_in_schemas": {"db1.sch1": []},
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert "grant select on future tables in schema db1.sch1 to role foo" in result
    assert "grant select on future views in schema db1.sch1 to role foo" in result
    assert (
        "grant select on future dynamic tables in schema db1.sch1 to role foo" in result
    )
    assert (
        "grant select on future semantic views in schema db1.sch1 to role foo" in result
    )


def test_future_read_revoked_from_unlisted_role():
    config = {"grants": [{"role": "foo", "read_on_schemas": ["db1.sch1"]}]}
    state = {
        "grants": {
            "on_databases": {"db1": []},
            "on_schemas": {"db1.sch1": []},
            "future_in_schemas": {
                "db1.sch1": [
                    {"privilege": "SELECT", "grant_on": "TABLE", "grantee_name": "FOO"},
                    {
                        "privilege": "SELECT",
                        "grant_on": "TABLE",
                        "grantee_name": "ROGUE",
                    },
                    {"privilege": "SELECT", "grant_on": "VIEW", "grantee_name": "FOO"},
                    {
                        "privilege": "SELECT",
                        "grant_on": "VIEW",
                        "grantee_name": "ROGUE",
                    },
                    {
                        "privilege": "SELECT",
                        "grant_on": "DYNAMIC TABLE",
                        "grantee_name": "FOO",
                    },
                    {
                        "privilege": "SELECT",
                        "grant_on": "DYNAMIC TABLE",
                        "grantee_name": "ROGUE",
                    },
                    {
                        "privilege": "SELECT",
                        "grant_on": "SEMANTIC VIEW",
                        "grantee_name": "FOO",
                    },
                    {
                        "privilege": "SELECT",
                        "grant_on": "SEMANTIC VIEW",
                        "grantee_name": "ROGUE",
                    },
                ]
            },
        },
    }
    result = set(execution_plan(config=config, state=state))
    # Should revoke future grants for rogue
    assert (
        'revoke select on future tables in schema db1.sch1 from role "ROGUE"' in result
    )
    assert (
        'revoke select on future views in schema db1.sch1 from role "ROGUE"' in result
    )
    assert (
        'revoke select on future dynamic tables in schema db1.sch1 from role "ROGUE"'
        in result
    )
    assert (
        'revoke select on future semantic views in schema db1.sch1 from role "ROGUE"'
        in result
    )
    # Should also revoke ALL grants to clean up existing objects
    assert 'revoke select on all tables in schema db1.sch1 from role "ROGUE"' in result
    assert 'revoke select on all views in schema db1.sch1 from role "ROGUE"' in result
    assert (
        'revoke select on all dynamic tables in schema db1.sch1 from role "ROGUE"'
        in result
    )
    assert (
        'revoke select on all semantic views in schema db1.sch1 from role "ROGUE"'
        in result
    )
    # Should NOT revoke foo
    assert not any("revoke" in s and "foo" in s for s in result)


def test_all_grants_skipped_when_future_grants_already_exist():
    """ALL grants are skipped when all future grants already exist in state."""
    config = {"grants": [{"role": "foo", "read_on_schemas": ["db1.sch1"]}]}
    state = {
        "grants": {
            "on_databases": {
                "db1": [
                    {"privilege": "USAGE", "grantee_name": "FOO"},
                ]
            },
            "on_schemas": {
                "db1.sch1": [
                    {"privilege": "USAGE", "grantee_name": "FOO"},
                ]
            },
            "future_in_schemas": {
                "db1.sch1": [
                    {"privilege": "SELECT", "grant_on": "TABLE", "grantee_name": "FOO"},
                    {"privilege": "SELECT", "grant_on": "VIEW", "grantee_name": "FOO"},
                    {
                        "privilege": "SELECT",
                        "grant_on": "DYNAMIC TABLE",
                        "grantee_name": "FOO",
                    },
                    {
                        "privilege": "SELECT",
                        "grant_on": "SEMANTIC VIEW",
                        "grantee_name": "FOO",
                    },
                ]
            },
        },
    }
    result = set(execution_plan(config=config, state=state))
    # ALL grants should NOT be emitted when future grants are already in place
    assert "grant select on all tables in schema db1.sch1 to role foo" not in result
    assert "grant select on all views in schema db1.sch1 to role foo" not in result
    assert (
        "grant select on all dynamic tables in schema db1.sch1 to role foo"
        not in result
    )
    assert (
        "grant select on all semantic views in schema db1.sch1 to role foo"
        not in result
    )


def test_all_grants_skipped_with_underscored_grant_on():
    """Snowflake returns DYNAMIC_TABLE/SEMANTIC_VIEW with underscores — must still match."""
    config = {"grants": [{"role": "foo", "read_on_schemas": ["db1.sch1"]}]}
    state = {
        "grants": {
            "on_databases": {"db1": [{"privilege": "USAGE", "grantee_name": "FOO"}]},
            "on_schemas": {"db1.sch1": [{"privilege": "USAGE", "grantee_name": "FOO"}]},
            "future_in_schemas": {
                "db1.sch1": [
                    {"privilege": "SELECT", "grant_on": "TABLE", "grantee_name": "FOO"},
                    {"privilege": "SELECT", "grant_on": "VIEW", "grantee_name": "FOO"},
                    {
                        "privilege": "SELECT",
                        "grant_on": "DYNAMIC_TABLE",
                        "grantee_name": "FOO",
                    },
                    {
                        "privilege": "SELECT",
                        "grant_on": "SEMANTIC_VIEW",
                        "grantee_name": "FOO",
                    },
                ]
            },
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert (
        "grant select on future dynamic tables in schema db1.sch1 to role foo"
        not in result
    )
    assert (
        "grant select on future semantic views in schema db1.sch1 to role foo"
        not in result
    )
    assert (
        "grant select on all dynamic tables in schema db1.sch1 to role foo"
        not in result
    )
    assert (
        "grant select on all semantic views in schema db1.sch1 to role foo"
        not in result
    )


def test_all_grants_emitted_when_future_grants_missing():
    """ALL grants are emitted when future grants are being newly added."""
    config = {"grants": [{"role": "foo", "read_on_schemas": ["db1.sch1"]}]}
    state = {
        "grants": {
            "on_databases": {"db1": []},
            "on_schemas": {"db1.sch1": []},
            "future_in_schemas": {"db1.sch1": []},
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert "grant select on all tables in schema db1.sch1 to role foo" in result
    assert "grant select on all views in schema db1.sch1 to role foo" in result
    assert "grant select on all dynamic tables in schema db1.sch1 to role foo" in result
    assert "grant select on all semantic views in schema db1.sch1 to role foo" in result


# ===== CREATE grants stateful tests =====


def test_create_grants_skipped_when_already_exists():
    config = {"grants": [{"role": "foo", "write_on_schemas": ["db1.sch1"]}]}
    state = {
        "grants": {
            "on_databases": {"db1": []},
            "on_schemas": {
                "db1.sch1": [
                    {"privilege": "CREATE TABLE", "grantee_name": "FOO"},
                    {"privilege": "CREATE VIEW", "grantee_name": "FOO"},
                    {"privilege": "CREATE DYNAMIC TABLE", "grantee_name": "FOO"},
                    {"privilege": "CREATE SEMANTIC VIEW", "grantee_name": "FOO"},
                    {"privilege": "CREATE TASK", "grantee_name": "FOO"},
                    {"privilege": "CREATE ALERT", "grantee_name": "FOO"},
                    {"privilege": "CREATE MASKING POLICY", "grantee_name": "FOO"},
                    {"privilege": "CREATE ROW ACCESS POLICY", "grantee_name": "FOO"},
                    {"privilege": "CREATE PROCEDURE", "grantee_name": "FOO"},
                ]
            },
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert not any("grant create" in s for s in result)


def test_create_grants_granted_when_missing():
    config = {"grants": [{"role": "foo", "write_on_schemas": ["db1.sch1"]}]}
    state = {
        "grants": {
            "on_databases": {"db1": []},
            "on_schemas": {"db1.sch1": []},
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert "grant create table on schema db1.sch1 to role foo" in result
    assert "grant create view on schema db1.sch1 to role foo" in result
    assert "grant create dynamic table on schema db1.sch1 to role foo" in result
    assert "grant create procedure on schema db1.sch1 to role foo" in result


def test_create_grants_revoked_from_unlisted_role():
    config = {"grants": [{"role": "foo", "write_on_schemas": ["db1.sch1"]}]}
    state = {
        "grants": {
            "on_databases": {"db1": []},
            "on_schemas": {
                "db1.sch1": [
                    {"privilege": "CREATE TABLE", "grantee_name": "FOO"},
                    {"privilege": "CREATE TABLE", "grantee_name": "ROGUE"},
                    {"privilege": "CREATE VIEW", "grantee_name": "FOO"},
                    {"privilege": "CREATE VIEW", "grantee_name": "ROGUE"},
                ]
            },
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert 'revoke create table on schema db1.sch1 from role "ROGUE"' in result
    assert 'revoke create view on schema db1.sch1 from role "ROGUE"' in result
    assert not any("revoke create" in s and "foo" in s for s in result)


def test_create_grants_partial_missing():
    """Some CREATE types exist, some don't — only grants the missing ones."""
    config = {"grants": [{"role": "foo", "write_on_schemas": ["db1.sch1"]}]}
    state = {
        "grants": {
            "on_databases": {"db1": []},
            "on_schemas": {
                "db1.sch1": [
                    {"privilege": "CREATE TABLE", "grantee_name": "FOO"},
                ]
            },
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert "grant create table on schema db1.sch1 to role foo" not in result
    assert "grant create view on schema db1.sch1 to role foo" in result
    assert "grant create procedure on schema db1.sch1 to role foo" in result


# ===== Object SELECT stateful tests =====


def test_object_select_skipped_when_already_exists():
    config = {"grants": [{"role": "foo", "read_on_objects": ["table:db1.sch1.t1"]}]}
    state = {
        "grants": {
            "on_databases": {"db1": []},
            "on_schemas": {"db1.sch1": []},
            "on_objects": {
                "table:db1.sch1.t1": [
                    {"privilege": "SELECT", "grantee_name": "FOO"},
                ]
            },
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert "grant select on table db1.sch1.t1 to role foo" not in result


def test_object_select_granted_when_missing():
    config = {"grants": [{"role": "foo", "read_on_objects": ["table:db1.sch1.t1"]}]}
    state = {
        "grants": {
            "on_databases": {"db1": []},
            "on_schemas": {"db1.sch1": []},
            "on_objects": {"table:db1.sch1.t1": []},
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert "grant select on table db1.sch1.t1 to role foo" in result


def test_object_select_revoked_from_unlisted_role():
    config = {"grants": [{"role": "foo", "read_on_objects": ["table:db1.sch1.t1"]}]}
    state = {
        "grants": {
            "on_databases": {"db1": []},
            "on_schemas": {"db1.sch1": []},
            "on_objects": {
                "table:db1.sch1.t1": [
                    {"privilege": "SELECT", "grantee_name": "FOO"},
                    {"privilege": "SELECT", "grantee_name": "ROGUE"},
                ]
            },
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert 'revoke select on table db1.sch1.t1 from role "ROGUE"' in result
    assert not any("revoke" in s and "foo" in s for s in result)


def test_object_select_not_revoked_when_covered_by_read_on_schemas():
    """A role with read_on_schemas should not have its object SELECT revoked."""
    config = {
        "grants": [
            {"role": "analyst", "read_on_schemas": ["db1.sch1"]},
            {"role": "special", "read_on_objects": ["table:db1.sch1.t1"]},
        ]
    }
    state = {
        "grants": {
            "on_databases": {"db1": []},
            "on_schemas": {"db1.sch1": []},
            "future_in_schemas": {"db1.sch1": []},
            "on_objects": {
                "table:db1.sch1.t1": [
                    {"privilege": "SELECT", "grantee_name": "ANALYST"},
                    {"privilege": "SELECT", "grantee_name": "SPECIAL"},
                ]
            },
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert not any(
        "revoke" in s and "analyst" in s and "db1.sch1.t1" in s for s in result
    )
    assert not any(
        "revoke" in s and "special" in s and "db1.sch1.t1" in s for s in result
    )


def test_object_select_revoked_when_not_covered_by_schema_or_object():
    """A role not in read_on_schemas or read_on_objects should be revoked."""
    config = {
        "grants": [
            {"role": "analyst", "read_on_schemas": ["db1.sch1"]},
            {"role": "special", "read_on_objects": ["table:db1.sch1.t1"]},
        ]
    }
    state = {
        "grants": {
            "on_databases": {"db1": []},
            "on_schemas": {"db1.sch1": []},
            "future_in_schemas": {"db1.sch1": []},
            "on_objects": {
                "table:db1.sch1.t1": [
                    {"privilege": "SELECT", "grantee_name": "ANALYST"},
                    {"privilege": "SELECT", "grantee_name": "SPECIAL"},
                    {"privilege": "SELECT", "grantee_name": "ROGUE"},
                ]
            },
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert 'revoke select on table db1.sch1.t1 from role "ROGUE"' in result


# ===== Stateless mode compatibility =====


def test_stateless_mode_grants_unconditionally():
    """When no state is provided, all grants are emitted unconditionally."""
    config = {
        "grants": [
            {
                "role": "foo",
                "read_on_schemas": ["db1.sch1"],
                "write_on_schemas": ["db1.sch2"],
                "read_on_objects": ["table:db1.sch1.t1"],
                "warehouses": ["wh1"],
            }
        ]
    }
    result = set(execution_plan(config=config))
    assert "grant usage on database db1 to role foo" in result
    assert "grant usage on schema db1.sch1 to role foo" in result
    assert "grant usage on schema db1.sch2 to role foo" in result
    assert "grant usage on warehouse wh1 to role foo" in result
    assert "grant select on future tables in schema db1.sch1 to role foo" in result
    assert "grant create table on schema db1.sch2 to role foo" in result
    assert "grant select on table db1.sch1.t1 to role foo" in result
    assert not any("revoke" in s for s in result)


# ===== Ownership transfer tests =====


def test_database_ownership_transferred_when_wrong_owner():
    config = {
        "databases": [{"name": "db1", "schemas": [{"name": "sch1"}]}],
    }
    state = {
        "databases": [
            {
                "name": "db1",
                "retention_time": "7",
                "options": "",
                "owner": "ACCOUNTADMIN",
            }
        ],
        "schemas": [
            {
                "name": "sch1",
                "database_name": "db1",
                "retention_time": "7",
                "options": "",
                "owner": "SYSADMIN",
            }
        ],
    }
    result = set(execution_plan(config=config, state=state))
    assert (
        "grant ownership on database db1 to role sysadmin copy current grants" in result
    )


def test_database_ownership_not_checked_when_new():
    """New objects have no state, so ownership should not be checked."""
    config = {
        "databases": [{"name": "db1", "schemas": [{"name": "sch1"}]}],
    }
    result = set(execution_plan(config=config))
    assert not any("ownership" in s for s in result)


def test_schema_ownership_transferred_when_wrong_owner():
    config = {
        "databases": [{"name": "db1", "schemas": [{"name": "sch1"}]}],
    }
    state = {
        "databases": [
            {
                "name": "db1",
                "retention_time": "7",
                "options": "",
                "owner": "SYSADMIN",
            }
        ],
        "schemas": [
            {
                "name": "sch1",
                "database_name": "db1",
                "retention_time": "7",
                "options": "",
                "owner": "ACCOUNTADMIN",
            }
        ],
    }
    result = set(execution_plan(config=config, state=state))
    assert (
        "grant ownership on schema db1.sch1 to role sysadmin copy current grants"
        in result
    )


def test_warehouse_ownership_transferred_when_wrong_owner():
    config = {"warehouses": [{"name": "wh1", "size": "xsmall"}]}
    state = {
        "warehouses": [{"name": "wh1", "size": "XSMALL", "owner": "ACCOUNTADMIN"}],
    }
    result = set(execution_plan(config=config, state=state))
    assert (
        "grant ownership on warehouse wh1 to role sysadmin copy current grants"
        in result
    )


def test_role_ownership_transferred_when_wrong_owner():
    config = {"roles": [{"name": "myrole"}]}
    state = {
        "roles": [{"name": "myrole", "owner": "ACCOUNTADMIN"}],
    }
    result = set(execution_plan(config=config, state=state))
    assert (
        "grant ownership on role myrole to role useradmin copy current grants" in result
    )


def test_role_ownership_not_transferred_when_correct():
    config = {"roles": [{"name": "myrole"}]}
    state = {
        "roles": [{"name": "myrole", "owner": "USERADMIN"}],
    }
    result = set(execution_plan(config=config, state=state))
    assert not any("ownership" in s for s in result)


# ===== Revoke unmanaged privileges tests =====


def test_unmanaged_privilege_revoked_on_database():
    config = {"grants": [{"role": "foo", "read_on_schemas": ["db1.sch1"]}]}
    state = {
        "grants": {
            "on_databases": {
                "db1": [
                    {"privilege": "USAGE", "grantee_name": "FOO"},
                    {"privilege": "MODIFY", "grantee_name": "BAR"},
                    {"privilege": "MONITOR", "grantee_name": "BAZ"},
                    {"privilege": "OWNERSHIP", "grantee_name": "SYSADMIN"},
                ]
            },
            "on_schemas": {},
            "future_in_schemas": {},
            "on_objects": {},
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert 'revoke modify on database db1 from role "BAR"' in result
    assert 'revoke monitor on database db1 from role "BAZ"' in result
    assert not any("revoke ownership" in s for s in result)
    assert 'revoke usage on database db1 from role "FOO"' not in result


def test_unmanaged_privilege_revoked_on_warehouse():
    config = {"grants": [{"role": "foo", "warehouses": ["wh1"]}]}
    state = {
        "grants": {
            "on_warehouses": {
                "wh1": [
                    {"privilege": "USAGE", "grantee_name": "FOO"},
                    {"privilege": "OPERATE", "grantee_name": "FOO"},
                    {"privilege": "MODIFY", "grantee_name": "BAR"},
                    {"privilege": "OWNERSHIP", "grantee_name": "SYSADMIN"},
                ]
            },
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert 'revoke operate on warehouse wh1 from role "FOO"' in result
    assert 'revoke modify on warehouse wh1 from role "BAR"' in result
    assert not any("revoke ownership" in s for s in result)
    assert 'revoke usage on warehouse wh1 from role "FOO"' not in result


def test_unmanaged_privilege_revoked_on_schema():
    config = {
        "grants": [
            {"role": "foo", "read_on_schemas": ["db1.sch1"]},
            {"role": "bar", "write_on_schemas": ["db1.sch1"]},
        ]
    }
    state = {
        "grants": {
            "on_databases": {},
            "on_schemas": {
                "db1.sch1": [
                    {"privilege": "USAGE", "grantee_name": "FOO"},
                    {"privilege": "USAGE", "grantee_name": "BAR"},
                    {"privilege": "CREATE TABLE", "grantee_name": "BAR"},
                    {"privilege": "MODIFY", "grantee_name": "BAZ"},
                    {"privilege": "OWNERSHIP", "grantee_name": "SYSADMIN"},
                ]
            },
            "future_in_schemas": {},
            "on_objects": {},
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert 'revoke modify on schema db1.sch1 from role "BAZ"' in result
    assert not any("revoke ownership" in s for s in result)
    assert 'revoke usage on schema db1.sch1 from role "FOO"' not in result
    assert 'revoke create table on schema db1.sch1 from role "BAR"' not in result


def test_unmanaged_privilege_not_revoked_without_state():
    """When no state is available, nothing should be revoked."""
    config = {"grants": [{"role": "foo", "warehouses": ["wh1"]}]}
    result = set(execution_plan(config=config))
    assert not any("revoke" in s for s in result)


# ===== User grantee handling tests =====


def test_revoke_warehouse_usage_from_user_grantee():
    """User-level resource grants are unmanaged and should be revoked with proper SQL."""
    config = {"grants": [{"role": "foo", "warehouses": ["bar"]}]}
    state = {
        "grants": {
            "on_warehouses": {
                "bar": [
                    {"privilege": "USAGE", "grantee_name": "FOO", "granted_to": "ROLE"},
                    {
                        "privilege": "USAGE",
                        "grantee_name": "SOME_USER",
                        "granted_to": "USER",
                    },
                ]
            }
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert 'revoke usage on warehouse bar from user "SOME_USER"' in result
    assert not any('from role "SOME_USER"' in s for s in result)


def test_revoke_database_usage_from_user_grantee():
    config = {"grants": [{"role": "foo", "read_on_schemas": ["db1.sch1"]}]}
    state = {
        "grants": {
            "on_databases": {
                "db1": [
                    {"privilege": "USAGE", "grantee_name": "FOO", "granted_to": "ROLE"},
                    {
                        "privilege": "USAGE",
                        "grantee_name": "ROGUE_USER",
                        "granted_to": "USER",
                    },
                ]
            },
            "on_schemas": {"db1.sch1": []},
            "future_in_schemas": {"db1.sch1": []},
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert 'revoke usage on database db1 from user "ROGUE_USER"' in result
    assert not any('from role "ROGUE_USER"' in s for s in result)


def test_revoke_schema_usage_from_user_grantee():
    config = {"grants": [{"role": "foo", "read_on_schemas": ["db1.sch1"]}]}
    state = {
        "grants": {
            "on_databases": {"db1": []},
            "on_schemas": {
                "db1.sch1": [
                    {"privilege": "USAGE", "grantee_name": "FOO", "granted_to": "ROLE"},
                    {
                        "privilege": "USAGE",
                        "grantee_name": "ROGUE_USER",
                        "granted_to": "USER",
                    },
                ]
            },
            "future_in_schemas": {"db1.sch1": []},
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert 'revoke usage on schema db1.sch1 from user "ROGUE_USER"' in result
    assert not any('from role "ROGUE_USER"' in s for s in result)


def test_user_grantee_not_included_in_role_diff():
    """User grantees should not interfere with role grant/revoke diffing."""
    config = {"grants": [{"role": "foo", "warehouses": ["bar"]}]}
    state = {
        "grants": {
            "on_warehouses": {
                "bar": [
                    {"privilege": "USAGE", "grantee_name": "FOO", "granted_to": "ROLE"},
                    {
                        "privilege": "USAGE",
                        "grantee_name": "SOME_USER",
                        "granted_to": "USER",
                    },
                ]
            }
        },
    }
    result = set(execution_plan(config=config, state=state))
    # foo should NOT be granted again (already exists as role grantee)
    assert "grant usage on warehouse bar to role foo" not in result
    # some_user should be revoked as user, not as role
    assert 'revoke usage on warehouse bar from user "SOME_USER"' in result


def test_unmanaged_privilege_revoked_with_correct_grantee_type():
    """Unmanaged privileges should use correct grantee type from state."""
    config = {"grants": [{"role": "foo", "warehouses": ["wh1"]}]}
    state = {
        "grants": {
            "on_warehouses": {
                "wh1": [
                    {"privilege": "USAGE", "grantee_name": "FOO", "granted_to": "ROLE"},
                    {
                        "privilege": "OPERATE",
                        "grantee_name": "SOME_USER",
                        "granted_to": "USER",
                    },
                ]
            },
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert 'revoke operate on warehouse wh1 from user "SOME_USER"' in result
    assert not any('from role "SOME_USER"' in s for s in result)


def test_schema_single_pass_revokes_mixed_privileges():
    """Schema diff revokes usage, create, and unmanaged privs in a single pass."""
    config = {
        "grants": [
            {"role": "reader", "read_on_schemas": ["db1.sch1"]},
        ]
    }
    state = {
        "grants": {
            "on_databases": {},
            "on_schemas": {
                "db1.sch1": [
                    {
                        "privilege": "USAGE",
                        "grantee_name": "READER",
                        "granted_to": "ROLE",
                    },
                    {
                        "privilege": "USAGE",
                        "grantee_name": "ROGUE",
                        "granted_to": "ROLE",
                    },
                    {
                        "privilege": "CREATE TABLE",
                        "grantee_name": "ROGUE",
                        "granted_to": "ROLE",
                    },
                    {
                        "privilege": "MODIFY",
                        "grantee_name": "ROGUE",
                        "granted_to": "ROLE",
                    },
                    {
                        "privilege": "MONITOR",
                        "grantee_name": "SOME_USER",
                        "granted_to": "USER",
                    },
                    {
                        "privilege": "OWNERSHIP",
                        "grantee_name": "SYSADMIN",
                        "granted_to": "ROLE",
                    },
                ]
            },
            "future_in_schemas": {},
            "on_objects": {},
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert 'revoke usage on schema db1.sch1 from role "ROGUE"' in result
    assert 'revoke create table on schema db1.sch1 from role "ROGUE"' in result
    assert 'revoke modify on schema db1.sch1 from role "ROGUE"' in result
    assert 'revoke monitor on schema db1.sch1 from user "SOME_USER"' in result
    assert not any("revoke ownership" in s for s in result)
    assert 'revoke usage on schema db1.sch1 from role "READER"' not in result


def test_object_select_revokes_non_select_privileges():
    """Object diff revokes non-select privileges dynamically from state."""
    config = {
        "grants": [
            {"role": "reader", "read_on_objects": ["table:db1.sch1.tbl1"]},
        ]
    }
    state = {
        "grants": {
            "on_databases": {},
            "on_schemas": {},
            "future_in_schemas": {},
            "on_objects": {
                "table:db1.sch1.tbl1": [
                    {
                        "privilege": "SELECT",
                        "grantee_name": "READER",
                        "granted_to": "ROLE",
                    },
                    {
                        "privilege": "INSERT",
                        "grantee_name": "WRITER",
                        "granted_to": "ROLE",
                    },
                    {
                        "privilege": "DELETE",
                        "grantee_name": "SOME_USER",
                        "granted_to": "USER",
                    },
                    {
                        "privilege": "OWNERSHIP",
                        "grantee_name": "SYSADMIN",
                        "granted_to": "ROLE",
                    },
                ]
            },
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert 'revoke insert on table db1.sch1.tbl1 from role "WRITER"' in result
    assert 'revoke delete on table db1.sch1.tbl1 from user "SOME_USER"' in result
    assert not any("revoke ownership" in s for s in result)
    assert not any("READER" in s and "revoke" in s for s in result)


def test_future_grants_revokes_non_select_privileges():
    """Future grants diff revokes non-select privileges dynamically from state."""
    config = {
        "grants": [
            {"role": "reader", "read_on_schemas": ["db1.sch1"]},
        ]
    }
    state = {
        "grants": {
            "on_databases": {},
            "on_schemas": {},
            "future_in_schemas": {
                "db1.sch1": [
                    {
                        "privilege": "SELECT",
                        "grant_on": "TABLE",
                        "grantee_name": "READER",
                    },
                    {
                        "privilege": "SELECT",
                        "grant_on": "VIEW",
                        "grantee_name": "READER",
                    },
                    {
                        "privilege": "SELECT",
                        "grant_on": "DYNAMIC_TABLE",
                        "grantee_name": "READER",
                    },
                    {
                        "privilege": "SELECT",
                        "grant_on": "SEMANTIC_VIEW",
                        "grantee_name": "READER",
                    },
                    {
                        "privilege": "INSERT",
                        "grant_on": "TABLE",
                        "grantee_name": "ROGUE",
                    },
                ]
            },
            "on_objects": {},
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert (
        'revoke insert on future tables in schema db1.sch1 from role "ROGUE"' in result
    )
    assert 'revoke insert on all tables in schema db1.sch1 from role "ROGUE"' in result
    assert not any("READER" in s and "revoke" in s for s in result)


def test_future_read_revoked_when_only_write_on_schemas():
    """Future read grants must be revoked when schema is only in write_on_schemas."""
    config = {"grants": [{"role": "writer", "write_on_schemas": ["db1.sch1"]}]}
    state = {
        "grants": {
            "on_databases": {"db1": []},
            "on_schemas": {"db1.sch1": []},
            "future_in_schemas": {
                "db1.sch1": [
                    {
                        "privilege": "SELECT",
                        "grant_on": "TABLE",
                        "grantee_name": "STALE_READER",
                    },
                    {
                        "privilege": "SELECT",
                        "grant_on": "VIEW",
                        "grantee_name": "STALE_READER",
                    },
                    {
                        "privilege": "SELECT",
                        "grant_on": "DYNAMIC TABLE",
                        "grantee_name": "STALE_READER",
                    },
                    {
                        "privilege": "SELECT",
                        "grant_on": "SEMANTIC VIEW",
                        "grantee_name": "STALE_READER",
                    },
                ]
            },
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert (
        'revoke select on future tables in schema db1.sch1 from role "STALE_READER"'
        in result
    )
    assert (
        'revoke select on future views in schema db1.sch1 from role "STALE_READER"'
        in result
    )
    assert (
        'revoke select on future dynamic tables in schema db1.sch1 from role "STALE_READER"'
        in result
    )
    assert (
        'revoke select on future semantic views in schema db1.sch1 from role "STALE_READER"'
        in result
    )
    # Also clean up existing objects
    assert (
        'revoke select on all tables in schema db1.sch1 from role "STALE_READER"'
        in result
    )
    assert (
        'revoke select on all views in schema db1.sch1 from role "STALE_READER"'
        in result
    )
    assert (
        'revoke select on all dynamic tables in schema db1.sch1 from role "STALE_READER"'
        in result
    )
    assert (
        'revoke select on all semantic views in schema db1.sch1 from role "STALE_READER"'
        in result
    )


def test_future_read_revoked_when_only_read_on_objects():
    """Future read grants must be revoked when schema is only in read_on_objects."""
    config = {
        "grants": [
            {"role": "obj_reader", "read_on_objects": ["table:db1.sch1.t1"]}
        ]
    }
    state = {
        "grants": {
            "on_databases": {"db1": []},
            "on_schemas": {"db1.sch1": []},
            "future_in_schemas": {
                "db1.sch1": [
                    {
                        "privilege": "SELECT",
                        "grant_on": "TABLE",
                        "grantee_name": "STALE_READER",
                    },
                    {
                        "privilege": "SELECT",
                        "grant_on": "VIEW",
                        "grantee_name": "STALE_READER",
                    },
                ]
            },
            "on_objects": {"table:db1.sch1.t1": []},
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert (
        'revoke select on future tables in schema db1.sch1 from role "STALE_READER"'
        in result
    )
    assert (
        'revoke select on future views in schema db1.sch1 from role "STALE_READER"'
        in result
    )


def test_future_read_no_regression_with_read_and_write():
    """Schema in both read_on_schemas and write_on_schemas: future reads preserved."""
    config = {
        "grants": [
            {"role": "reader", "read_on_schemas": ["db1.sch1"]},
            {"role": "writer", "write_on_schemas": ["db1.sch1"]},
        ]
    }
    state = {
        "grants": {
            "on_databases": {"db1": []},
            "on_schemas": {"db1.sch1": []},
            "future_in_schemas": {
                "db1.sch1": [
                    {
                        "privilege": "SELECT",
                        "grant_on": "TABLE",
                        "grantee_name": "READER",
                    },
                    {
                        "privilege": "SELECT",
                        "grant_on": "VIEW",
                        "grantee_name": "READER",
                    },
                    {
                        "privilege": "SELECT",
                        "grant_on": "DYNAMIC TABLE",
                        "grantee_name": "READER",
                    },
                    {
                        "privilege": "SELECT",
                        "grant_on": "SEMANTIC VIEW",
                        "grantee_name": "READER",
                    },
                ]
            },
        },
    }
    result = set(execution_plan(config=config, state=state))
    # reader's future grants should NOT be revoked
    assert not any("revoke" in s and "reader" in s.lower() for s in result)
    # writer should NOT get future read grants
    assert not any(
        "grant select on future" in s and "writer" in s for s in result
    )


def test_future_read_writer_role_revoked_on_write_only_schema():
    """Writer role's stale future read grants revoked on write-only schema."""
    config = {"grants": [{"role": "writer", "write_on_schemas": ["db1.sch1"]}]}
    state = {
        "grants": {
            "on_databases": {"db1": []},
            "on_schemas": {"db1.sch1": []},
            "future_in_schemas": {
                "db1.sch1": [
                    {
                        "privilege": "SELECT",
                        "grant_on": "TABLE",
                        "grantee_name": "WRITER",
                    },
                ]
            },
        },
    }
    result = set(execution_plan(config=config, state=state))
    # Even though writer is the configured role, write != future read
    assert (
        'revoke select on future tables in schema db1.sch1 from role "WRITER"' in result
    )


def test_future_grants_does_not_revoke_ownership():
    """Future grants diff must never revoke OWNERSHIP."""
    config = {
        "grants": [
            {"role": "reader", "read_on_schemas": ["db1.sch1"]},
        ]
    }
    state = {
        "grants": {
            "on_databases": {},
            "on_schemas": {},
            "future_in_schemas": {
                "db1.sch1": [
                    {
                        "privilege": "SELECT",
                        "grant_on": "TABLE",
                        "grantee_name": "READER",
                    },
                    {
                        "privilege": "SELECT",
                        "grant_on": "VIEW",
                        "grantee_name": "READER",
                    },
                    {
                        "privilege": "SELECT",
                        "grant_on": "DYNAMIC_TABLE",
                        "grantee_name": "READER",
                    },
                    {
                        "privilege": "SELECT",
                        "grant_on": "SEMANTIC_VIEW",
                        "grantee_name": "READER",
                    },
                    {
                        "privilege": "OWNERSHIP",
                        "grant_on": "TABLE",
                        "grantee_name": "SYSADMIN",
                    },
                ]
            },
            "on_objects": {},
        },
    }
    result = set(execution_plan(config=config, state=state))
    assert not any("revoke ownership" in s for s in result)
