# Use a secret in a namespace

Give a namespace a Kubernetes Secret made from a secret of the installation, under the key names its app expects: a binding asks for it, and the vault says which namespaces may.

## Before you start

- A secret `google-oauth` in the vault `default`, from [Keep a secret](secrets.md).
- The namespace `identity`, such as from `kubectl create namespace identity`.

## Steps

### 1. Allow the namespace

A vault lists the namespaces that may bind its secrets in `spec.allowedNamespaces`. Write the vault as a file with [`nereus secrets vault get`](../../specs/cli/reefs/secrets.html#binding-refused), add `identity` there, then apply the file.

```bash
nereus secrets vault get default \
  --output yaml > default.yaml
```

```bash
nereus secrets vault apply \
  --from-file default.yaml
```

``` { .text .output title="output" }
✓ secrets/vaults/default configured
```

### 2. Bind the secret

[`nereus secrets binding create`](../../specs/cli/reefs/secrets.html#binding-create) makes the Kubernetes Secret in the namespace from the secret's current version; each `--key NAME=KEY` renames a key, and without any, every key keeps its own name. A namespace the vault does not allow, or a key the secret lacks, is refused before anything is written.

```bash
nereus secrets binding create keycloak-google \
  --secret default/google-oauth \
  --namespace identity \
  --key client-id=GOOGLE_CLIENT_ID \
  --key client-secret=GOOGLE_CLIENT_SECRET
```

``` { .text .output title="output" }
✓ secrets/vaults/default/secrets/google-oauth/secretbindings/identity/keycloak-google created
Secret keycloak-google ready in namespace identity.

Next steps:

  nereus secrets binding get keycloak-google --namespace identity
```

A chart asks the same way, with a SecretBinding among its templates, as `test/charts/binding-demo` does; `helm uninstall` removes it and its Kubernetes Secret. A [release](release.md) asks with `--secret`.

## Check it worked

[`nereus secrets binding list`](../../specs/cli/reefs/secrets.html#binding-list) shows each binding with `FOR`, who asked: a release, a chart from its Helm labels, or the CLI user.

```bash
nereus secrets binding list
```

``` { .text .output title="output" }
NAME             SECRET                NAMESPACE  FOR                 STATUS  AGE
keycloak-google  default/google-oauth  identity   system:admin        Ready   12s
binding-demo     default/google-oauth  tools      chart binding-demo  Ready   4s
```

A secret is not deleted while bindings use it: [`nereus secrets get`](../../specs/cli/reefs/secrets.html#binding-used) lists them.

## Clean up

[`nereus secrets binding delete`](../../specs/cli/reefs/secrets.html#binding-delete) deletes the Kubernetes Secret first, then the binding.

```bash
nereus secrets binding delete keycloak-google \
  --namespace identity
```

``` { .text .output title="output" }
✓ secrets/vaults/default/secrets/google-oauth/secretbindings/identity/keycloak-google deleted

Next steps:

  nereus secrets binding list --namespace identity
```

## Next

- [Release a chart](release.md) that reads the secret through a binding.
- Give a team a vault of its own with [`nereus secrets vault create --allow-namespace`](../../specs/cli/reefs/secrets.html#vault-create).

## Learn more

- [The secrets reef](../../reference/reefs/secrets.md): vaults, secrets and bindings, every command.
