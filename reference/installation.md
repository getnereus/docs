# The installation

Every installation has a name, an id and an alias, held by one `Installation` object in `nereus-system` that the first `nereus init` creates ([spec 0006](../specs/0006-installation-identity.md)).

See it with [`nereus config installation show`](../specs/cli/core.html#installation-show).

## Name

The object's name; it never changes. It prefixes every name the platform creates outside itself, such as the Azure resource group `<installation>-platform` ([spec 0005](../specs/0005-cloud-reef.md)).

It defaults to the cluster name; `--installation-name` sets another on the first `init`. A name is lowercase letters, digits and `-`, starts with a letter, at most 63 characters.

A second `init` with another name keeps the installation, and its `installation` line says `kept nereus-local, not acme-dev: the name of an installation never changes; another name is another installation`.

## Id

A random UUID; it never changes. Cloud resources can carry it, so they trace back to this installation. The API refuses a change, even by hand:

```bash
kubectl patch installations nereus-local \
  --namespace nereus-system \
  --type merge \
  --patch '{"spec":{"id":"00000000-0000-4000-8000-000000000000"}}'
```

``` { .text .output title="output" }
The Installation "nereus-local" is invalid: spec.id: Invalid value: "00000000-0000-4000-8000-000000000000": the id of an installation never changes
```

The [settings file](settings.md) also holds the id, so a cluster recreated from it is the same installation. A cluster recreated without it is a new installation with a new id.

## Alias

What listings show; free text, at most 63 characters, no control characters. It may change; the name and id stay, and the settings file follows: [`nereus config installation set --alias "Acme Prod"`](../specs/cli/core.html#installation-set).

## Naming overrides

When a generated cloud name is taken, a naming override sets it: `issuer.storage`, `state.storage` or `secrets.vault`, each checked against its resource's rules, with `nereus config installation set --naming-override issuer.storage=acmeissuers01`. See [A name is taken](../guides/troubleshoot/name-taken.md).

## With Helm

The object belongs to the Helm release `nereus` and is kept on `helm uninstall`.

The chart creates it from `installation.name`, which it requires, and keeps the id and alias the cluster holds, so a plain `helm upgrade --install` gives the same identity as `init`.

Another name on the same cluster is refused, since the name never changes:

``` { .text .output title="output" }
Error: UPGRADE FAILED: execution error at (nereus/templates/installation.yaml:10:4): the installation of this cluster is nereus-local, not acme: the name of an installation never changes; another name is another installation
```

## One per namespace

A namespace holds one installation; a second is an error naming both. The undercloud and the overcloud are one installation: the pivot moves the object ([Undercloud and overcloud](../concepts/undercloud-overcloud.md)).
