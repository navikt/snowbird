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
