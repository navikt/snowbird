# Snowbird

Snowbird helps configure Snowflake resources for dataproducts.

Snowbird builds on [Permifrost](https://about.gitlab.com/handbook/business-technology/data-team/platform/permifrost/).

In addition to the capabilities provided by permifrost snowbird also enables declarative configuration of databases, schemas, warehouses and stages.

## Installation

```shell
pip install snowbird@git+https://github.com/navikt/snowbird.git
```

## Actions

### Create resources and configure grants

The default declaration file name is 'snowflake.yml' and the default location of the file is ./infrastructure

In this case you can simply run the command: $ snowbird run.

**Command**

```shell
snowbird run
```

### Cloning

You can clone a database by running the commnad $ snowbird clone. Optionally give a role usage to the new database with --usage

**Command**

```shell
snowbird clone <source_db> <destination_db>
```

**Options**

```shell
--usage <role>
```

**Example**

```shell
snowbird clone my_db my_db_clone --usage supreme_leader
```
