# The database Reef

Every command of the database Reef: a PostgreSQL per Database, owned by a node of the tenancy tree.

## Commands

- [`nereus reef apply database`](../../specs/cli/reefs/database.html#reef-apply) The database Reef: one kind, Database
- [`nereus nereid apply cloudnative-pg`](../../specs/cli/reefs/database.html#nereid-apply) The cloudnative-pg Nereid makes the Reef's default Mandate
- [`nereus database create keycloak`](../../specs/cli/reefs/database.html#create) A Database names its owner in the tenancy tree
- [`nereus database get keycloak`](../../specs/cli/reefs/database.html#get) Ready, with its connection in a Secret
- [`nereus database create orders`](../../specs/cli/reefs/database.html#refused) An owner missing from the tree is refused
- [`nereus database delete keycloak`](../../specs/cli/reefs/database.html#delete) Delete removes the Secret, then the Cluster and its volume

## Examples

### reef-apply

The release Reef with flux comes first: the Nereid releases the operator through it.

```bash
nereus reef apply database
```

``` { .text .output title="output" }
✓ core/reefs/database 0.1.0 created (database.getnereus.dev/v1alpha1: databases)

Next steps:

  nereus database --help
  nereus nereid apply <nereid> --reef database
```

### nereid-apply

CloudNativePG's operator, its chart pinned by version and SHA-256.

```bash
nereus nereid apply cloudnative-pg \
  --reef database
```

``` { .text .output title="output" }
✓ core/nereids/cloudnative-pg created, Ready, pinned to sha256:4908bacf6ac8: see 'nereus database --help'
  core/mandates/cloudnative-pg created (reef: database, nereid: cloudnative-pg, default)

Next steps:

  nereus database create <name> --project <name> --engine postgres
```

### create

In nereus-system, for Keycloak.

```bash
nereus database create keycloak \
  --project nereids \
  --engine postgres
```

``` { .text .output title="output" }
✓ database/databases/keycloak created (mandate: cloudnative-pg, nereid: cloudnative-pg)

Next steps:

  nereus database get keycloak
```

### get

```bash
nereus database get keycloak
```

``` { .text .output title="output" }
Name:          keycloak
Organization:  getnereus
Project:       nereus/nereids
Engine:        postgres
Mandate:       cloudnative-pg
Nereid:        cloudnative-pg
Ready:         True
Connection:    secret nereus-system/keycloak-database (host, port, dbname, username, password, uri)
```

### refused

```bash
nereus database create orders \
  --project missing \
  --engine postgres
```

``` { .text .output title="output" }
✗ database/databases/orders: owner project/missing does not exist. To fix it, run:
  nereus tenancy project list
  Nothing was changed.
```

### delete

```bash
nereus database delete keycloak \
  --dry-run
```

``` { .text .output title="output" }
database/databases/keycloak deleted (dry run)
```
