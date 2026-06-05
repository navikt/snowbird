---
name: snowbird-cli
description: >
  Snowbird CLI reference and testing guide. Shows all commands, flags, and how to test
  against tests/snowflake.yml. Use when working with snowbird commands, testing CLI changes,
  debugging output, or verifying state changes. Triggers: "snowbird commands", "how to test",
  "test cli", "cli reference", "snowbird help", or invokes /snowbird-cli.
---

# Snowbird CLI Reference & Testing Guide

## Testing Against tests/snowflake.yml

Use `tests/snowflake.yml` as config to test CLI changes without a live Snowflake connection.

```shell
# Generate execution plan (stateless — no Snowflake connection needed)
snowbird plan --config tests/snowflake.yml --silent --stateless --execution-plan

# Generate SQL output (stateless)
snowbird plan --config tests/snowflake.yml --silent --stateless

# Generate execution plan with state comparison (needs state file or Snowflake connection)
snowbird plan --config tests/snowflake.yml --silent --execution-plan

# Save current Snowflake state to file (requires Snowflake connection)
snowbird save state --config tests/snowflake.yml --file state.json

# Diff against a saved state file
snowbird plan --config tests/snowflake.yml --state state.json --silent --execution-plan
```

Use `snowbird save state` to capture state snapshots and verify changes to the state object structure.

## CLI Command Reference

```
snowbird plan         Generate SQL to converge Snowflake to desired state
  --config TEXT         Path to config file
  --silent              Suppress console output (useful for piping)
  --state TEXT          Path to state file to compare against
  --stateless           Skip state comparison, generate all statements
  --execution-plan      Print execution plan instead of raw SQL

snowbird apply        Execute generated SQL against Snowflake
  --config TEXT         Path to config file
  --silent              Suppress console output
  --state TEXT          Path to state file to compare against
  --stateless           Skip state comparison

snowbird save state   Save current Snowflake state to a file
  --file TEXT           Path to write state file
  --config TEXT         Path to config file
```

## Useful Patterns

- **Quick smoke test after code change**: `snowbird plan --config tests/snowflake.yml --silent --stateless --execution-plan`
- **Compare before/after state**: Save state with `snowbird save state`, make changes, save again, diff files
- **Pipe SQL to file**: `snowbird plan --config tests/snowflake.yml --silent --stateless > output.sql`
- **Verify schema changes**: Run plan after modifying `snowflake.schema.json` to catch validation errors

## ⚠️ Safety

**Never run `snowbird apply` without explicit user request.** It executes SQL against a live Snowflake instance.
