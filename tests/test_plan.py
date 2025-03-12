from snowbird.plan import execution_plan


# TODO: Bør kanskje trimmes av execution_plan
def _trim_result(result):
    result_trimmed = []
    for line in result:
        line_trimmed_list = []
        for l in line.split("\n"):
            line_trimmed_list.append(l.strip()) if l.strip() else None
        line_trimmed = " ".join(line_trimmed_list)
        result_trimmed.append(line_trimmed)
    return result_trimmed


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
    result = _trim_result(execution_plan(config))
    print(result)
    assert result == expected


def test_create_database_with_transient():
    config = {
        "databases": [
            {"name": "foo", "transient": "true", "schemas": [{"name": "bar"}]},
        ]
    }
    expected = [
        "use role sysadmin",
        "create transient database if not exists foo",
        "create transient schema if not exists foo.bar",
    ]
    result = _trim_result(execution_plan(config))
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
    result = _trim_result(execution_plan(config))
    print(result)
    assert result == expected


def test_create_schema_with_transient():
    config = {
        "databases": [
            {
                "name": "foo",
                "schemas": [{"name": "bar", "transient": "true"}],
            },
        ]
    }
    expected = [
        "use role sysadmin",
        "create database if not exists foo",
        "alter database foo set data_retention_time_in_days = 7",
        "create transient schema if not exists foo.bar",
    ]
    result = _trim_result(execution_plan(config))
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
    result = _trim_result(execution_plan(config))
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
    result = _trim_result(execution_plan(config))
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
        "create warehouse if not exists foo with warehouse_size = xsmall auto_suspend = 30 initially_suspended = true",
        "alter warehouse foo set warehouse_size = xsmall",
    ]
    result = _trim_result(execution_plan(config))
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
        "create warehouse if not exists foo with warehouse_size = large auto_suspend = 30 initially_suspended = true",
        "alter warehouse foo set warehouse_size = large",
    ]
    result = _trim_result(execution_plan(config))
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
        "create warehouse if not exists foo with warehouse_size = xsmall auto_suspend = 30 initially_suspended = true",
        "alter warehouse foo set warehouse_size = xsmall",
        "create warehouse if not exists bar with warehouse_size = xsmall auto_suspend = 30 initially_suspended = true",
        "alter warehouse bar set warehouse_size = xsmall",
    ]
    result = _trim_result(execution_plan(config))
    print(result)
    assert result == expected


def test_create_user():
    config = {
        "users": [
            {"name": "foo", "type": "role"},
        ]
    }
    expected = [
        "use role useradmin",
        "create user if not exists foo type = role",
    ]
    result = _trim_result(execution_plan(config))
    print(result)
    assert result == expected


def test_create_multiple_users():
    config = {
        "users": [
            {"name": "foo", "type": "role"},
            {"name": "bar", "type": "another_role"},
        ]
    }
    expected = [
        "use role useradmin",
        "create user if not exists foo type = role",
        "create user if not exists bar type = another_role",
    ]
    result = _trim_result(execution_plan(config))
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
    result = _trim_result(execution_plan(config))
    print(result)
    assert result == expected
    assert result == expected


def test_grant_role_warehouse():
    config = {"grants": [{"role": "foo", "warehouses": ["bar"]}]}
    expected = [
        "use role useradmin",
        "grant usage on warehouse bar to role foo",
    ]
    result = _trim_result(execution_plan(config))
    print(result)
    assert result == expected


def test_grant_role_multiple_warehouses():
    config = {"grants": [{"role": "foo", "warehouses": ["bar", "baz"]}]}
    expected = [
        "use role useradmin",
        "grant usage on warehouse bar to role foo",
        "grant usage on warehouse baz to role foo",
    ]
    result = _trim_result(execution_plan(config))
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
    ]
    result = _trim_result(execution_plan(config))
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
        "grant usage on database bar to role foo",
        "grant usage on schema bar.qux to role foo",
        "grant create table on schema bar.qux to role foo",
        "grant create view on schema bar.qux to role foo",
    ]
    result = _trim_result(execution_plan(config))
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
    ]
    result = _trim_result(execution_plan(config))
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
        "grant usage on database bar to role foo",
        "grant usage on schema bar.qux to role foo",
        "grant select on all tables in schema bar.qux to role foo",
        "grant select on future tables in schema bar.qux to role foo",
    ]
    result = _trim_result(execution_plan(config))
    print(result)
    assert result == expected


def test_grant_role_to_role():
    config = {"grants": [{"role": "foo", "to_roles": ["bar"]}]}
    expected = [
        "use role useradmin",
        "grant role foo to role bar",
    ]
    result = _trim_result(execution_plan(config))
    print(result)
    assert result == expected


def test_grant_role_to_multiple_roles():
    config = {"grants": [{"role": "foo", "to_roles": ["bar", "baz"]}]}
    expected = [
        "use role useradmin",
        "grant role foo to role bar",
        "grant role foo to role baz",
    ]
    result = _trim_result(execution_plan(config))
    print(result)
    assert result == expected


def test_grant_role_to_user():
    config = {"grants": [{"role": "foo", "to_users": ["bar"]}]}
    expected = [
        "use role useradmin",
        "grant role foo to user bar",
    ]
    result = _trim_result(execution_plan(config))
    print(result)
    assert result == expected


def test_grant_role_to_multiple_users():
    config = {"grants": [{"role": "foo", "to_users": ["bar", "baz"]}]}
    expected = [
        "use role useradmin",
        "grant role foo to user bar",
        "grant role foo to user baz",
    ]
    result = _trim_result(execution_plan(config))
    print(result)
    assert result == expected
    assert result == expected
