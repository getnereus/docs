# Keep a secret

Keep a secret in a vault of the installation: each value is encrypted on your machine before it leaves it, and no command prints it back.

## Before you start

- A cluster from [Prepare the cluster](../../start/init.md) with `--profile internal-developer-platform`: it brings the secrets Reef, the Nereid `openbao` and the vault `default`.
- The values in environment variables or files, never on the command line, where the shell history keeps them.

## Steps

### 1. Create a secret from environment variables

[`nereus secrets create`](../../specs/cli/reefs/secrets.html#create) encrypts each value with the key of the vault's Mandate, then stores it.

```bash
nereus secrets create google-oauth \
  --from-env GOOGLE_CLIENT_ID \
  --from-env GOOGLE_CLIENT_SECRET
```

``` { .text .output title="output" }
✓ secrets/vaults/default/secrets/google-oauth created (key SHA256:GQ8TrJ9h6ZrNYHItBycWK+tXkURjowfJWcjEyabRIKI)
Stored encrypted; a Kubernetes Secret is made only when a binding asks for it (#532).
```

### 2. Take a key from a file

`--from-file KEY=PATH` takes the file's bytes, for a private key or a certificate.

```bash
nereus secrets create github-app \
  --from-file private-key=key.pem \
  --from-env APP_ID
```

``` { .text .output title="output" }
✓ secrets/vaults/default/secrets/github-app created (key SHA256:GQ8TrJ9h6ZrNYHItBycWK+tXkURjowfJWcjEyabRIKI)
Stored encrypted; a Kubernetes Secret is made only when a binding asks for it (#532).
```

### 3. Change it from a file

`create` refuses a secret that exists. Write the encrypted secret to a file, safe to keep, then [`nereus secrets apply`](../../specs/cli/reefs/secrets.html#apply) it; each change is a new version.

```bash
nereus secrets create google-oauth \
  --from-env GOOGLE_CLIENT_ID \
  --from-env GOOGLE_CLIENT_SECRET \
  --dry-run --output yaml > google-oauth.yaml
nereus secrets apply --from-file google-oauth.yaml
```

``` { .text .output title="output" }
✓ secrets/vaults/default/secrets/google-oauth configured
```

## Check it worked

[`nereus secrets list`](../../specs/cli/reefs/secrets.html#list) shows the keys' names, never a value.

```bash
nereus secrets list
```

``` { .text .output title="output" }
VAULT    NAME          KEYS                  STATUS  AGE
default  github-app    APP_ID, +1            Ready   9s
default  google-oauth  GOOGLE_CLIENT_ID, +1  Ready   10s
```

## Clean up

!!! warning "Deleted for good"
    Deleting a secret destroys every version of it in OpenBao.

```bash
nereus secrets delete default/google-oauth
nereus secrets delete github-app
```

``` { .text .output title="output" }
✓ secrets/vaults/default/secrets/google-oauth deleted
✓ secrets/vaults/default/secrets/github-app deleted
```

## Next

- [Use a secret in a namespace](secret-binding.md): a binding makes the Kubernetes Secret an app reads.
- [Release a chart](release.md) that reads a secret through a binding.

## Learn more

- [The secrets Reef](../../reference/reefs/secrets.md): vaults, secrets and bindings, every command.
- [ADR 0013](../../adr/0013-command-conventions.md): `create` builds from flags, `apply` takes files.
