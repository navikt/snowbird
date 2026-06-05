from queue import Queue
from unittest.mock import MagicMock, patch

import pytest
import snowflake.connector.errors

from snowbird.state import (
    _async_fetch_all,
    _execute_query,
    _get_database_grants,
    _get_future_schema_grants,
    _get_network_policies,
    _get_object_grants,
    _get_object_privileges,
    _get_role_grants,
    _get_schema_grants,
    _get_schemas_state,
    _get_users_state,
    _get_warehouse_grants,
    current_state,
)
from snowbird.utils import ConnectionPool


class MockPool:
    """Fake ConnectionPool that uses a single mock connection."""

    def __init__(self, mock_cursor):
        self._cursor = mock_cursor

    def get_cursor(self):
        from contextlib import contextmanager

        @contextmanager
        def _ctx():
            yield self._cursor

        return _ctx()

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def _make_cursor(execute_results=None, async_results=None):
    """Create a mock cursor with configurable results.

    execute_results: dict mapping SQL prefix -> fetchall/fetchone result
    async_results: dict mapping query_id -> fetchall/fetchone result
    """
    cursor = MagicMock()
    cursor._qid_counter = 0
    cursor._async_results = async_results or {}
    cursor._execute_results = execute_results or {}

    def execute_side_effect(sql):
        for prefix, result in cursor._execute_results.items():
            if prefix.lower() in sql.lower():
                cursor.fetchall.return_value = result
                cursor.fetchone.return_value = result[0] if result else None
                return cursor
        cursor.fetchall.return_value = []
        cursor.fetchone.return_value = None
        return cursor

    def execute_async_side_effect(sql):
        cursor._qid_counter += 1
        qid = f"qid_{cursor._qid_counter}"
        cursor.sfqid = qid
        # Store the sql associated with this qid for result lookup
        cursor._async_results[qid] = sql

    def get_results_side_effect(qid):
        sql = cursor._async_results.get(qid, "")
        for prefix, result in cursor._execute_results.items():
            if prefix.lower() in sql.lower():
                cursor.fetchall.return_value = result
                cursor.fetchone.return_value = result[0] if result else None
                return
        cursor.fetchall.return_value = []
        cursor.fetchone.return_value = None

    cursor.execute.side_effect = execute_side_effect
    cursor.execute_async.side_effect = execute_async_side_effect
    cursor.get_results_from_sfqid.side_effect = get_results_side_effect

    return cursor


# --- ConnectionPool tests ---


class TestConnectionPool:
    @patch("snowbird.utils.snowflake.connector.connect")
    def test_creates_connections(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        pool = ConnectionPool(size=3, config={"account": "test"})
        assert mock_connect.call_count == 3
        pool.close()

    @patch("snowbird.utils.snowflake.connector.connect")
    def test_get_cursor_returns_and_recycles(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        pool = ConnectionPool(size=1, config={"account": "test"})

        with pool.get_cursor() as cur:
            assert cur == mock_cursor

        # Connection returned to pool — can get another cursor
        with pool.get_cursor() as cur2:
            assert cur2 is not None

        pool.close()

    @patch("snowbird.utils.snowflake.connector.connect")
    def test_cursor_closed_on_exception(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        pool = ConnectionPool(size=1, config={"account": "test"})

        with pytest.raises(RuntimeError):
            with pool.get_cursor() as cur:
                raise RuntimeError("boom")

        mock_cursor.close.assert_called_once()
        # Connection still returned to pool
        with pool.get_cursor() as cur:
            assert cur is not None

        pool.close()

    @patch("snowbird.utils.snowflake.connector.connect")
    def test_close_all_connections(self, mock_connect):
        mock_conns = [MagicMock() for _ in range(3)]
        mock_connect.side_effect = mock_conns

        pool = ConnectionPool(size=3, config={"account": "test"})
        pool.close()

        for conn in mock_conns:
            conn.close.assert_called_once()

    @patch("snowbird.utils.snowflake.connector.connect")
    def test_context_manager(self, mock_connect):
        mock_connect.return_value = MagicMock()

        with ConnectionPool(size=1, config={"account": "test"}) as pool:
            assert pool is not None

        mock_connect.return_value.close.assert_called_once()


# --- _async_fetch_all tests ---


class TestAsyncFetchAll:
    def test_submits_and_collects(self):
        cursor = _make_cursor(
            execute_results={
                "show grants of role admin": [{"role": "admin", "grantee": "user1"}],
                "show grants of role dev": [{"role": "dev", "grantee": "user2"}],
            }
        )

        items = [
            ("admin", "show grants of role admin"),
            ("dev", "show grants of role dev"),
        ]
        result = _async_fetch_all(cursor, items)

        assert "admin" in result
        assert "dev" in result
        assert result["admin"] == [{"role": "admin", "grantee": "user1"}]
        assert cursor.execute_async.call_count == 2
        assert cursor.get_results_from_sfqid.call_count == 2

    def test_handles_programming_error_on_submit(self):
        cursor = _make_cursor()
        cursor.execute_async.side_effect = snowflake.connector.errors.ProgrammingError(
            "nope"
        )

        result = _async_fetch_all(cursor, [("key", "bad sql")])
        assert result == {}

    def test_handles_programming_error_on_fetch(self):
        cursor = _make_cursor()
        cursor.execute_async.side_effect = None
        cursor.sfqid = "qid_1"
        cursor.get_results_from_sfqid.side_effect = (
            snowflake.connector.errors.ProgrammingError("fetch fail")
        )

        result = _async_fetch_all(cursor, [("key", "some sql")])
        assert result == {}

    def test_empty_items(self):
        cursor = _make_cursor()
        result = _async_fetch_all(cursor, [])
        assert result == {}


# --- _get_role_grants tests ---


class TestGetRoleGrants:
    def test_fetches_grants_for_roles(self):
        cursor = _make_cursor(
            execute_results={
                "show grants of role analyst": [
                    {"role": "analyst", "granted_to": "user1"}
                ],
            }
        )
        pool = MockPool(cursor)
        result = _get_role_grants([{"name": "analyst"}], pool)

        assert "analyst" in result
        assert len(result["analyst"]) == 1

    def test_empty_roles(self):
        pool = MockPool(MagicMock())
        assert _get_role_grants([], pool) == {}


# --- _get_warehouse_grants tests ---


class TestGetWarehouseGrants:
    def test_fetches_grants(self):
        cursor = _make_cursor(
            execute_results={
                "show grants on warehouse dev_xs": [
                    {"privilege": "USAGE", "grantee_name": "analyst"}
                ],
            }
        )
        pool = MockPool(cursor)
        result = _get_warehouse_grants([{"name": "DEV_XS"}], pool)

        assert "dev_xs" in result

    def test_empty_config(self):
        pool = MockPool(MagicMock())
        assert _get_warehouse_grants([], pool) == {}


# --- _get_database_grants tests ---


class TestGetDatabaseGrants:
    def test_fetches_grants(self):
        cursor = _make_cursor(
            execute_results={
                "show grants on database mydb": [{"privilege": "USAGE"}],
            }
        )
        pool = MockPool(cursor)
        result = _get_database_grants([{"name": "MYDB"}], pool)

        assert "mydb" in result

    def test_empty_config(self):
        pool = MockPool(MagicMock())
        assert _get_database_grants([], pool) == {}


# --- _get_schemas_state tests ---


class TestGetSchemasState:
    def test_fetches_scoped_per_database(self):
        cursor = _make_cursor(
            execute_results={
                "show schemas in database mydb": [
                    {"name": "public", "database_name": "mydb"}
                ],
                "show schemas in database other": [
                    {"name": "raw", "database_name": "other"}
                ],
            }
        )
        pool = MockPool(cursor)
        config = [{"name": "mydb"}, {"name": "other"}]
        result = _get_schemas_state(config, pool)

        assert len(result) == 2
        names = {s["name"] for s in result}
        assert names == {"public", "raw"}

    def test_empty_config(self):
        pool = MockPool(MagicMock())
        assert _get_schemas_state([], pool) == []

    def test_single_database(self):
        cursor = _make_cursor(
            execute_results={
                "show schemas in database mydb": [
                    {"name": "public", "database_name": "mydb"},
                    {"name": "raw", "database_name": "mydb"},
                ],
            }
        )
        pool = MockPool(cursor)
        config = [{"name": "mydb"}]
        result = _get_schemas_state(config, pool)

        assert len(result) == 2


# --- _get_schema_grants tests ---


class TestGetSchemaGrants:
    def test_fetches_grants(self):
        cursor = _make_cursor(
            execute_results={
                "show grants on schema mydb.public": [{"privilege": "USAGE"}],
            }
        )
        pool = MockPool(cursor)
        config = [{"name": "mydb", "schemas": [{"name": "public"}]}]
        result = _get_schema_grants(config, pool)

        assert "mydb.public" in result

    def test_empty_config(self):
        pool = MockPool(MagicMock())
        assert _get_schema_grants([], pool) == {}


# --- _get_future_schema_grants tests ---


class TestGetFutureSchemaGrants:
    def test_fetches_grants(self):
        cursor = _make_cursor(
            execute_results={
                "show future grants in schema mydb.public": [{"privilege": "SELECT"}],
            }
        )
        pool = MockPool(cursor)
        config = [{"name": "mydb", "schemas": [{"name": "public"}]}]
        result = _get_future_schema_grants(config, pool)

        assert "mydb.public" in result

    def test_empty_config(self):
        pool = MockPool(MagicMock())
        assert _get_future_schema_grants([], pool) == {}


# --- _get_object_privileges tests ---


class TestGetObjectPrivileges:
    def test_fetches_privileges(self):
        cursor = _make_cursor(
            execute_results={
                "object_privileges": [
                    {
                        "GRANTEE": "analyst",
                        "PRIVILEGE_TYPE": "SELECT",
                        "OBJECT_TYPE": "TABLE",
                        "OBJECT_NAME": "t1",
                        "OBJECT_SCHEMA": "public",
                    }
                ],
            }
        )
        pool = MockPool(cursor)
        result = _get_object_privileges([{"name": "mydb"}], pool)

        assert "mydb" in result

    def test_empty_config(self):
        pool = MockPool(MagicMock())
        assert _get_object_privileges([], pool) == {}


# --- _get_object_grants tests ---


class TestGetObjectGrants:
    def test_fetches_grants(self):
        cursor = _make_cursor(
            execute_results={
                "show grants on table mydb.public.t1": [{"privilege": "SELECT"}],
            }
        )
        pool = MockPool(cursor)
        config = [{"read_on_objects": ["table:mydb.public.t1"]}]
        result = _get_object_grants(config, pool)

        assert "table:mydb.public.t1" in result

    def test_deduplicates_objects(self):
        cursor = _make_cursor(
            execute_results={
                "show grants on table mydb.public.t1": [{"privilege": "SELECT"}],
            }
        )
        pool = MockPool(cursor)
        config = [
            {"read_on_objects": ["table:mydb.public.t1"]},
            {"read_on_objects": ["table:mydb.public.t1"]},
        ]
        result = _get_object_grants(config, pool)

        # Only one query submitted despite duplicate
        assert cursor.execute_async.call_count == 1

    def test_empty_config(self):
        pool = MockPool(MagicMock())
        assert _get_object_grants([], pool) == {}


# --- _get_users_state tests ---


class TestGetUsersState:
    def test_fetches_user_details_and_policy(self):
        cursor = _make_cursor(
            execute_results={
                "show users like 'alice'": [{"name": "alice", "type": "PERSON"}],
                "network_policy' for user alice": [{"value": "my_policy"}],
            }
        )
        pool = MockPool(cursor)
        result = _get_users_state([{"name": "alice"}], pool)

        assert len(result) == 1
        assert result[0]["name"] == "alice"
        assert result[0]["type"] == "PERSON"
        assert result[0]["network_policy"] == "my_policy"
        # Uses _execute_query (sync), not execute_async
        cursor.execute_async.assert_not_called()

    def test_skips_missing_user(self):
        cursor = _make_cursor(execute_results={})
        pool = MockPool(cursor)
        result = _get_users_state([{"name": "ghost"}], pool)

        assert result == []

    def test_empty_users(self):
        pool = MockPool(MagicMock())
        assert _get_users_state([], pool) == []


# --- _get_network_policies tests ---


class TestGetNetworkPolicies:
    def test_fetches_policy_with_rules(self):
        cursor = _make_cursor(
            execute_results={
                "show network policies like 'np1'": [
                    {"name": "np1", "comment": "test policy"}
                ],
                "describe network policy np1": [
                    {
                        "name": "ALLOWED_NETWORK_RULE_LIST",
                        "value": '["rule1", "rule2"]',
                    },
                    {
                        "name": "BLOCKED_NETWORK_RULE_LIST",
                        "value": '["rule3"]',
                    },
                ],
            }
        )
        pool = MockPool(cursor)
        result = _get_network_policies([{"name": "np1"}], pool)

        assert "np1" in result
        assert result["np1"]["comment"] == "test policy"
        assert result["np1"]["allowed_network_rule_list"] == ["rule1", "rule2"]
        assert result["np1"]["blocked_network_rule_list"] == ["rule3"]
        # Uses _execute_query (sync), not execute_async
        cursor.execute_async.assert_not_called()

    def test_skips_nonexistent_policy(self):
        cursor = _make_cursor(execute_results={})
        pool = MockPool(cursor)
        result = _get_network_policies([{"name": "ghost"}], pool)

        assert result == {}

    def test_empty_policies(self):
        pool = MockPool(MagicMock())
        assert _get_network_policies([], pool) == {}


# --- _execute_query tests ---


class TestExecuteQuery:
    def test_returns_results(self):
        cursor = _make_cursor(
            execute_results={"show databases": [{"name": "db1"}, {"name": "db2"}]}
        )
        pool = MockPool(cursor)
        result = _execute_query(pool, "show databases")

        assert len(result) == 2

    def test_returns_empty_on_error(self):
        cursor = MagicMock()
        cursor.execute.side_effect = snowflake.connector.errors.ProgrammingError("fail")
        pool = MockPool(cursor)
        result = _execute_query(pool, "bad query")

        assert result == []


# --- current_state integration test ---


class TestCurrentState:
    @patch("snowbird.state.ConnectionPool")
    def test_assembles_state_dict(self, mock_pool_cls):
        cursor = _make_cursor(
            execute_results={
                "show databases": [{"name": "db1"}],
                "show warehouses": [{"name": "wh1"}],
                "show schemas in database db1": [
                    {"name": "public", "database_name": "db1"}
                ],
                "show roles": [{"name": "sysadmin"}],
            }
        )
        mock_pool = MockPool(cursor)
        mock_pool_cls.return_value = mock_pool

        config = {
            "roles": [],
            "users": [],
            "network_policies": [],
            "databases": [{"name": "db1"}],
            "warehouses": [],
            "grants": [],
        }
        result = current_state(config, pool_size=2)

        assert "databases" in result
        assert "warehouses" in result
        assert "schemas" in result
        assert "roles" in result
        assert "users" in result
        assert "grants" in result
        assert "network_policies" in result
        assert result["databases"] == [{"name": "db1"}]
        assert result["schemas"] == [{"name": "public", "database_name": "db1"}]
