# Snowbird Snowflake Configuration

Schema for snowflake.yml configuration files used by Snowbird to manage Snowflake infrastructure.

### Type: `object`

> ⚠️ Additional properties are not allowed.

| Property | Type | Required | Possible values | Deprecated | Default | Description | Examples |
| -------- | ---- | -------- | --------------- | ---------- | ------- | ----------- | -------- |
| id | `string` | ✅ | string |  |  | Unique identifier for this configuration. |  |
| databases | `array` |  | object |  |  | List of Snowflake databases to manage. |  |
| databases[].name | `string` | ✅ | string |  |  | Name of the database. |  |
| databases[].transient | `boolean` |  | boolean |  | `false` | Whether the database is transient. Transient databases have a max data retention of 1 day. |  |
| databases[].data_retention_time_in_days | `integer` |  | `0 <= x ` |  |  | Time Travel data retention period in days. Default is 7 for non-transient databases, 1 for transient. |  |
| databases[].schemas | `array` | ✅ | object |  |  | List of schemas within this database. |  |
| databases[].schemas[].name | `string` | ✅ | string |  |  | Name of the schema. |  |
| databases[].schemas[].transient | `boolean` |  | boolean |  |  | Whether the schema is transient. Inherits from parent database if not specified. |  |
| databases[].schemas[].data_retention_time_in_days | `integer` |  | `0 <= x ` |  |  | Time Travel data retention period in days. Inherits from parent database if not specified. |  |
| warehouses | `array` |  | object |  |  | List of Snowflake warehouses to manage. |  |
| warehouses[].name | `string` | ✅ | string |  |  | Name of the warehouse. |  |
| warehouses[].size | `string` |  | `x-small` `small` `medium` `large` `x-large` `2x-large` `3x-large` `4x-large` `5x-large` `6x-large` |  | `"x-small"` | Size of the warehouse. Default is 'x-small'. |  |
| roles | `array` |  | object |  |  | List of Snowflake roles to manage. |  |
| roles[].name | `string` | ✅ | string |  |  | Name of the role. |  |
| users | `array` |  | object |  |  | List of Snowflake users to manage. |  |
| users[].name | `string` | ✅ | string |  |  | Name of the user. |  |
| users[].type | `string` | ✅ | `service` `legacy_service` |  |  | Type of user account. |  |
| users[].network_policy | `string` | ✅ | string |  |  | Name of the network policy to assign to this user. Must reference a network policy defined in this configuration or an existing one in Snowflake. |  |
| network_policies | `array` |  | object |  |  | List of Snowflake network policies to manage. |  |
| network_policies[].name | `string` | ✅ | string |  |  | Name of the network policy. |  |
| network_policies[].description | `string` |  | string |  |  | Description/comment for the network policy. |  |
| network_policies[].network_rules | `object` | ✅ | object |  |  | Network rules for this policy. At least one of 'allowed' or 'blocked' must be specified. |  |
| network_policies[].network_rules.allowed | `array` |  | string |  |  | List of allowed network rules. References fully qualified network rule names (e.g., 'database.schema.rule_name'). |  |
| network_policies[].network_rules.blocked | `array` |  | string |  |  | List of blocked network rules. References fully qualified network rule names (e.g., 'database.schema.rule_name'). |  |
| grants | `array` |  | object |  |  | List of grant configurations that define permissions for roles. |  |
| grants[].role | `string` | ✅ | string |  |  | The role to grant permissions to. |  |
| grants[].warehouses | `array` |  | string |  |  | Warehouses to grant USAGE on to this role. |  |
| grants[].read_on_schemas | `array` |  | [`^[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+$`](https://regex101.com/?regex=%5E%5Ba-zA-Z0-9_%5D%2B%5C.%5Ba-zA-Z0-9_%5D%2B%24) |  |  | Schemas to grant SELECT (read) access on. Grants select on all current and future tables, views, dynamic tables, and semantic views in the schema. Format: 'database.schema'. |  |
| grants[].write_on_schemas | `array` |  | [`^[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+$`](https://regex101.com/?regex=%5E%5Ba-zA-Z0-9_%5D%2B%5C.%5Ba-zA-Z0-9_%5D%2B%24) |  |  | Schemas to grant CREATE access on. Grants ability to create tables, views, dynamic tables, semantic views, tasks, alerts, masking policies, row access policies, and procedures. Format: 'database.schema'. |  |
| grants[].read_on_objects | `array` |  | [`^(table\|view\|dynamic_table\|semantic_view):[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+$`](https://regex101.com/?regex=%5E%28table%7Cview%7Cdynamic_table%7Csemantic_view%29%3A%5Ba-zA-Z0-9_%5D%2B%5C.%5Ba-zA-Z0-9_%5D%2B%5C.%5Ba-zA-Z0-9_%5D%2B%24) |  |  | Specific objects to grant SELECT access on. Format: 'type:database.schema.object_name'. Supported types: table, view, dynamic_table, semantic_view. |  |
| grants[].to_roles | `array` |  | string |  |  | Roles that this role should be granted to. Note: 'sysadmin' is automatically added if not present. |  |
| grants[].to_users | `array` |  | string |  |  | Users that this role should be granted to. Can be user names or UUIDs (for Entra ID users). |  |


---

Markdown generated with [jsonschema-markdown](https://github.com/elisiariocouto/jsonschema-markdown).
