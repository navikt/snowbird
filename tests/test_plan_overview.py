from snowbird.plan import overview


def test_create_database_overview():
    plan = [
        "create database if not exists foo",
    ]
    expected = ["foo"]
    plan_overview = overview(execution_plan=plan)
    print(plan_overview)
    result = plan_overview.get("create_databases")
    assert result == expected


def test_create_transient_database_overview():
    plan = [
        "create transient database if not exists foo",
    ]
    expected = ["foo"]
    plan_overview = overview(execution_plan=plan)
    print(plan_overview)
    result = plan_overview.get("create_databases")
    assert result == expected


def test_create_database_overview_when_alter_exists():
    plan = [
        "create database if not exists foo",
        "alter database foo set comment='bar'",
    ]
    expected = ["foo"]
    plan_overview = overview(execution_plan=plan)
    print(plan_overview)
    result = plan_overview.get("create_databases")
    assert result == expected


def test_modify_database_overview():
    plan = [
        "alter database foo set comment='bar'",
    ]
    expected = ["foo"]
    plan_overview = overview(execution_plan=plan)
    print(plan_overview)
    result = plan_overview.get("modify_databases")
    assert result == expected


def test_no_modify_database_overview_when_create_exists():
    plan = [
        "create database if not exists foo",
        "alter database foo set comment='bar'",
    ]
    expected = []
    plan_overview = overview(execution_plan=plan)
    print(plan_overview)
    result = plan_overview.get("modify_databases")
    assert result == expected


def test_create_schema_overview():
    plan = [
        "create schema if not exists foo",
    ]
    expected = ["foo"]
    plan_overview = overview(execution_plan=plan)
    print(plan_overview)
    result = plan_overview.get("create_schemas")
    assert result == expected


def test_create_transient_schema_overview():
    plan = [
        "create transient schema if not exists foo",
    ]
    expected = ["foo"]
    plan_overview = overview(execution_plan=plan)
    print(plan_overview)
    result = plan_overview.get("create_schemas")
    assert result == expected


def test_create_schema_overview_when_alter_exists():
    plan = [
        "create schema if not exists foo",
        "alter schema foo set comment='bar'",
    ]
    expected = ["foo"]
    plan_overview = overview(execution_plan=plan)
    print(plan_overview)
    result = plan_overview.get("create_schemas")
    assert result == expected


def test_modify_schema_overview():
    plan = [
        "alter schema foo set comment='bar'",
    ]
    expected = ["foo"]
    plan_overview = overview(execution_plan=plan)
    print(plan_overview)
    result = plan_overview.get("modify_schemas")
    assert result == expected


def test_no_modify_schema_overview_when_create_exists():
    plan = [
        "create schema if not exists foo",
        "alter schema foo set comment='bar'",
    ]
    expected = []
    plan_overview = overview(execution_plan=plan)
    print(plan_overview)
    result = plan_overview.get("modify_schemas")
    assert result == expected


def test_create_role_overview():
    plan = [
        "create role if not exists foo",
    ]
    expected = ["foo"]
    plan_overview = overview(execution_plan=plan)
    print(plan_overview)
    result = plan_overview.get("create_roles")
    assert result == expected


def test_create_role_overview_when_alter_exists():
    plan = [
        "create role if not exists foo",
        "alter role foo set comment='bar'",
    ]
    expected = ["foo"]
    plan_overview = overview(execution_plan=plan)
    print(plan_overview)
    result = plan_overview.get("create_roles")
    assert result == expected


def test_modify_role_overview():
    plan = [
        "alter role foo set comment='bar'",
    ]
    expected = ["foo"]
    plan_overview = overview(execution_plan=plan)
    print(plan_overview)
    result = plan_overview.get("modify_roles")
    assert result == expected


def test_no_modify_role_overview_when_create_exists():
    plan = [
        "create role if not exists foo",
        "alter role foo set comment='bar'",
    ]
    expected = []
    plan_overview = overview(execution_plan=plan)
    print(plan_overview)
    result = plan_overview.get("modify_roles")
    assert result == expected


def test_create_user_overview():
    plan = [
        "create user if not exists foo",
    ]
    expected = ["foo"]
    plan_overview = overview(execution_plan=plan)
    print(plan_overview)
    result = plan_overview.get("create_users")
    assert result == expected


def test_create_user_overview_when_alter_exists():
    plan = [
        "create user if not exists foo",
        "alter user foo set comment='bar'",
    ]
    expected = ["foo"]
    plan_overview = overview(execution_plan=plan)
    print(plan_overview)
    result = plan_overview.get("create_users")
    assert result == expected


def test_modify_user_overview():
    plan = [
        "alter user foo set comment='bar'",
    ]
    expected = ["foo"]
    plan_overview = overview(execution_plan=plan)
    print(plan_overview)
    result = plan_overview.get("modify_users")
    assert result == expected


def test_create_network_policy_overview():
    plan = [
        "create network policy if not exists foo",
    ]
    expected = ["foo"]
    plan_overview = overview(execution_plan=plan)
    print(plan_overview)
    result = plan_overview.get("create_network_policies")
    assert result == expected


def test_create_network_policy_overview_when_alter_exists():
    plan = [
        "create network policy if not exists foo",
        "alter network policy foo set comment='bar'",
    ]
    expected = ["foo"]
    plan_overview = overview(execution_plan=plan)
    print(plan_overview)
    result = plan_overview.get("create_network_policies")
    assert result == expected


def test_modify_network_policy_overview():
    plan = [
        "alter network policy foo set comment='bar'",
    ]
    expected = ["foo"]
    plan_overview = overview(execution_plan=plan)
    print(plan_overview)
    result = plan_overview.get("modify_network_policies")
    assert result == expected


def test_no_modify_network_policy_overview_when_create_exists():
    plan = [
        "create network policy if not exists foo",
        "alter network policy foo set comment='bar'",
    ]
    expected = []
    plan_overview = overview(execution_plan=plan)
    print(plan_overview)
    result = plan_overview.get("modify_network_policies")
    assert result == expected


def test_no_modify_user_overview_when_create_exists():
    plan = [
        "create user if not exists foo",
        "alter user foo set comment='bar'",
    ]
    expected = []
    plan_overview = overview(execution_plan=plan)
    print(plan_overview)
    result = plan_overview.get("modify_users")
    assert result == expected


def test_create_warehouse_overview():
    plan = [
        "create warehouse if not exists foo",
    ]
    expected = ["foo"]
    plan_overview = overview(execution_plan=plan)
    print(plan_overview)
    result = plan_overview.get("create_warehouses")
    assert result == expected


def test_create_warehouse_overview_when_alter_exists():
    plan = [
        "create warehouse if not exists foo",
        "alter warehouse foo set comment='bar'",
    ]
    expected = ["foo"]
    plan_overview = overview(execution_plan=plan)
    print(plan_overview)
    result = plan_overview.get("create_warehouses")
    assert result == expected


def test_modify_warehouse_overview():
    plan = [
        "alter warehouse foo set comment='bar'",
    ]
    expected = ["foo"]
    plan_overview = overview(execution_plan=plan)
    print(plan_overview)
    result = plan_overview.get("modify_warehouses")
    assert result == expected


def test_no_modify_warehouse_overview_when_create_exists():
    plan = [
        "create warehouse if not exists foo",
        "alter warehouse foo set comment='bar'",
    ]
    expected = []
    plan_overview = overview(execution_plan=plan)
    print(plan_overview)
    result = plan_overview.get("modify_warehouses")
    assert result == expected


def test_grant_select_overview():
    plan = [
        "grant select on all tables in schema foo to role bar",
    ]
    expected = plan
    plan_overview = overview(execution_plan=plan)
    print(plan_overview)
    result = plan_overview.get("grant_selects")
    assert result == expected


def test_grant_create_overview():
    plan = [
        "grant create table on schema foo to role bar",
    ]
    expected = plan
    plan_overview = overview(execution_plan=plan)
    print(plan_overview)
    result = plan_overview.get("grant_create")
    assert result == expected


def test_grant_roles_overview():
    plan = [
        "grant role bar to role foo",
    ]
    expected = plan
    plan_overview = overview(execution_plan=plan)
    print(plan_overview)
    result = plan_overview.get("grant_roles")
    assert result == expected


def test_grant_users_overview():
    plan = [
        "grant role bar to user foo",
    ]
    expected = plan
    plan_overview = overview(execution_plan=plan)
    print(plan_overview)
    result = plan_overview.get("grant_users")
    assert result == expected


def test_revoke_roles_overview():
    plan = [
        "revoke role bar from role foo",
    ]
    expected = plan
    plan_overview = overview(execution_plan=plan)
    print(plan_overview)
    result = plan_overview.get("revoke_roles")
    assert result == expected


def test_revoke_users_overview():
    plan = [
        "revoke role bar from user foo",
    ]
    expected = plan
    plan_overview = overview(execution_plan=plan)
    print(plan_overview)
    result = plan_overview.get("revoke_users")
    assert result == expected
