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
