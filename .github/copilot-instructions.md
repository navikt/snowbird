# Copilot Instructions for Snowbird

Snowbird is a Terraform/Permifrost-like CLI tool for declaratively managing Snowflake resources and grants. Users define desired state in a `snowflake.yml` config file, and Snowbird generates and optionally executes the SQL to converge Snowflake to that state.

## Build, Test, and Lint

```shell
# Set up virtual environment with dev dependencies
make install

# use the venv
source .venv/bin/activate

# Run the full test suite
pytest tests

# Run a single test
pytest tests/test_execution_plan.py::test_function_name

# Formatting (available as dev dependencies)
black .
isort .

# Regenerate COMMANDS.md and REFERENCES.md after schema or CLI changes
make docs

# test command-line interface (see snowbird-cli skill for full reference)
snowbird plan --config tests/snowflake.yml --silent --execution-plan
```

**⚠️ Never run `snowbird apply` on your own.** It executes SQL against a live Snowflake instance. Only run when the user explicitly asks for it.

The CI pipeline (`.github/workflows/test.yaml`) runs `pytest tests` on every push.

Root-level `test*.py` files are ad-hoc exploration scripts that hit a live Snowflake instance — they are not part of the pytest suite.

## Architecture

### CLI → Plan → Apply flow

1. **`snowbird/main.py`** — Click CLI entry point with three commands: `plan`, `apply`, and `save state`.
2. **`snowbird/plan.py`** — The core module. `load_config()` reads the YAML config (lowercasing the entire content on load). `execution_plan()` computes the desired SQL statements by diffing config against current state.
3. **`snowbird/state.py`** — Fetches current Snowflake state using `SHOW` queries (databases, warehouses, schemas, users, roles, grants, network policies).
4. **`snowbird/utils.py`** — Snowflake connection helper (`snowflake_cursor()`) and progress/spinner display.

### SQL generation

SQL statements are generated using **Jinja2 templates defined as string constants** inside `plan.py`. There are no external template files. The generated SQL is normalized by `_trim_sql_statements()`.

### Role-based execution phases

Generated SQL is organized by Snowflake role:
- **`sysadmin`** — databases, schemas, warehouses
- **`securityadmin`** — network policies
- **`useradmin`** — users, roles, grants

Each phase begins with an explicit `USE ROLE` statement.

### State comparison

`execution_plan(config, state)` diffs the desired config against current Snowflake state. Only the delta is emitted as SQL. Running with `--stateless` skips state comparison and generates all statements unconditionally.

## Key Conventions

- **Case-insensitive everywhere**: Config YAML is lowercased on load (`yaml.safe_load(content.lower())`). State comparisons normalize to lowercase. This is a core design decision.
- **SQL-first testing**: Tests assert on exact SQL string output from `execution_plan()`, not on intermediate data structures.
- **Functional style with dicts**: No rich domain model classes — config and state are plain dicts, processed by functions.
- **Internal helpers use `_` prefix**: e.g., `_database_state()`, `_trim_sql_statements()`.
- **`sysadmin` is auto-added**: All role grants automatically include `sysadmin` — this is enforced in `execution_plan()`.
- **Config schema**: Defined in `snowflake.schema.json`. Additional properties are disallowed. See `REFERENCES.md` for human-readable docs.
- **Versioning**: Version number lives in `setup.py`. Releases follow semver via `make release` which tags and creates a GitHub Release.

## Communication Style

**Ask questions early and often.** The barrier to ask clarifying questions should be low. When something is unclear, ambiguous, or can be solved in multiple reasonable ways — ask before assuming.

Always use caveman skills when applicable:

- **caveman** — All responses in caveman mode (full intensity by default)
- **caveman-commit** — Generate commit messages in caveman style
- **caveman-review** — Code reviews in caveman style
- **caveman-compress** — Compress memory/instruction files in caveman format
- **snowbird-cli** — CLI reference and testing guide for snowbird commands
