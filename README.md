# Snowbird

Snowbird helps configure Snowflake resources for dataproducts.

Snowbird builds on [Permifrost](https://about.gitlab.com/handbook/business-technology/data-team/platform/permifrost/).

In addition to the capabilities provided by permifrost snowbird also enables declarative configuration of databases, schemas, warehouses and stages.

## Installation

pip install snowbird (published version)

or 

pip install snowbird@git+https://github.com/navikt/snowbird.git (from this repo)

## Example

The default declaration file name is 'snowflake.yml' and the default location of the file is ./infrastructure

In this case you can simply run the command: $ snowbird run.
