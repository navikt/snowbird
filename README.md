# Snowbird

Snowbird is a terraform / permifrost like program for managing snowflake resources and grants

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

TODO...