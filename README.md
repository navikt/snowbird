# Snowbird

Snowbird helps configure Snowflake resources for dataproducts.

Snowbird builds on [Permifrost](https://about.gitlab.com/handbook/business-technology/data-team/platform/permifrost/).

In addition to the capabilities provided by permifrost snowbird also enables declarative configuration of databases, schemas, warehouses and stages.

## Installation

```shell
pip install snowbird@git+https://github.com/navikt/snowbird.git
```
## Release

Vi bruker [GitHub Release](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository) til versjonering og bygg av nytt docker-image. Versjonsnummereringen skal følge [semver](https://semver.org): `<major>.<minor>.<patch>` Eks: `0.1.0`. Siden vi enda ikke er på versjon 1 kan `minor` inkrementeres med 1 ved breaking changes i apiet og `patch` ved nye features eller bug fiks.

For å release en ny versjon må en gjøre følgende:
* Merge koden til main
* Oppdatere `version` i [setup.py](setup.py)
* Opprett/oppdater `<major>.<minor>` tag. Eks: `git tag -f v0.2`
* Opprett `<major>.<minor>.<patch>` tag. Eks: `git tag v0.2.0` (tagen skal ikke eksistere fra før)
* Push tags til github med: `git push -f origin v0.2 v0.2.0`
* Opprett ny release på [github](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)
    * Steg 1: Velg den nye `<major>.<minor>.<patch>` taggen.
    * Steg 2: Trykk Generate release notes for å få utfylt relevant informasjon
    * Steg 3: Trykk Publish release.

## Actions

### Create resources and configure grants

The default declaration file name is 'snowflake.yml' and the default location of the file is ./infrastructure

In this case you can simply run the command: $ snowbird run.

**Command**

```shell
snowbird run
```

### Cloning

You can clone a database by running the commnad $ snowbird clone. The destination db will be replaced if it's already exists and refresh of dynamic tables will be suspended. Optionally give a role usage to the new database with --usage

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
