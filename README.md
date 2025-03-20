# Snowbird

Snowbird is a terraform / permifrost like program for managing snowflake resources and grants.

For documentation on how to use snowbird see [commands](./COMMANDS.md) or  use the command `snowbird --help` in the terminal.

## Installation

```shell
pip install "snowbird @ git+https://github.com/navikt/snowbird@<version>"
```

Example:

```shell
pip install "snowbird @ git+https://github.com/navikt/snowbird@v0.3"
```

## Upgrading

For upgrading to a new major or minor version, see installation

```shell
pip install --upgrade snowbird
```

## Release

Vi bruker [GitHub Release](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository) til versjonering. Versjonsnummereringen skal følge [semver](https://semver.org): `<major>.<minor>.<patch>` Eks: `0.1.0`. Siden vi enda ikke er på versjon 1 kan `minor` inkrementeres med 1 ved breaking changes i apiet og `patch` ved nye features eller bug fiks. Versjonsnr hentes fra [setup.py](setup.py)

Pass på at du har gjort følgende før du kjører `make release`:

* Koden er merget til `main`
* `version` i [setup.py](setup.py) er oppdatert. (Husk commit)

```shell
make release
```
