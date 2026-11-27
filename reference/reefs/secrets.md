# The secrets Reef

Every command of the secrets Reef: vaults, and the secrets in them, encrypted before they leave the machine.

## Commands

- [`nereus init`](../../specs/cli/reefs/secrets.html#init) The profile brings the secrets Reef ready to use, with its key and the vault default
- [`nereus secrets create google-oauth`](../../specs/cli/reefs/secrets.html#create) A secret is encrypted on your machine, before it leaves it
- [`nereus secrets create google-oauth`](../../specs/cli/reefs/secrets.html#create-exists) Creating it again is refused, with how to change it
- [`nereus secrets create github-app`](../../specs/cli/reefs/secrets.html#create-file) A key can come from a file, such as a private key
- [`nereus secrets create google-oauth`](../../specs/cli/reefs/secrets.html#apply) Apply takes a folder of secrets, and the second apply changes nothing
- [`nereus secrets list`](../../specs/cli/reefs/secrets.html#list) The list shows every secret with its keys, never a value
- [`nereus secrets get default/google-oauth`](../../specs/cli/reefs/secrets.html#get) One secret, by its vault and name
- [`nereus secrets get google-oauth`](../../specs/cli/reefs/secrets.html#get-yaml) As YAML, the object shows the names of its keys instead of the envelopes
- [`nereus secrets vault list`](../../specs/cli/reefs/secrets.html#vault-list) The list shows every vault, its Nereid and how many secrets it holds
- [`nereus secrets vault create team-a`](../../specs/cli/reefs/secrets.html#vault-create) A vault for a team, with the namespaces allowed to bind its secrets
- [`nereus secrets vault delete default`](../../specs/cli/reefs/secrets.html#vault-delete-held) A vault that holds secrets is refused, with what to delete first
- [`nereus secrets delete default/google-oauth`](../../specs/cli/reefs/secrets.html#delete) A secret goes by its full name, or by its name in the vault default
- [`nereus secrets vault delete team-a`](../../specs/cli/reefs/secrets.html#vault-delete) An empty vault goes
- [`nereus secrets binding create keycloak-google`](../../specs/cli/reefs/secrets.html#binding-create) A binding makes a Kubernetes Secret from a secret, in a namespace the vault allows
- [`nereus secrets binding create payments`](../../specs/cli/reefs/secrets.html#binding-refused) A namespace the vault does not allow, or a key the secret does not have, is refused before anything is written
- [`cat test/charts/binding-demo/templates/secretbinding.yaml`](../../specs/cli/reefs/secrets.html#binding-chart) A chart asks for its secret with a SecretBinding among its templates
- [`nereus secrets binding list`](../../specs/cli/reefs/secrets.html#binding-list) Every binding, with who asked for it
- [`nereus secrets get default/google-oauth`](../../specs/cli/reefs/secrets.html#binding-used) A secret says where it is used, and is not deleted while it is
- [`nereus secrets binding delete keycloak-google`](../../specs/cli/reefs/secrets.html#binding-delete) A binding goes, and its Kubernetes Secret with it

## Examples

### init

Install core and the internal developer platform profile.

```bash
nereus init \
  --profile internal-developer-platform
```

``` { .text .output title="output" }
✓ reef secrets              0.0s  core/reefs/secrets 0.1.0 created (secrets.getnereus.dev/v1alpha1: secrets, secretbindings, vaults)
✓ nereid openbao           21.5s  core/nereids/openbao created, Ready
✓ mandate default           0.0s  core/mandates/default created (reef: secrets, nereid: openbao, default)
✓ public key                5.0s  rsa-4096, SHA256:yJi61pETATOGjDo6b6B2y5+V8jiPPDruqOUYp2CtPFs, version 1
✓ vault default             0.1s  secrets/vaults/default created (mandate: default)
```

### create

Two keys, each from an environment variable.

```bash
nereus secrets create google-oauth \
  --from-env GOOGLE_CLIENT_ID \
  --from-env GOOGLE_CLIENT_SECRET
```

``` { .text .output title="output" }
✓ secrets/vaults/default/secrets/google-oauth created (key SHA256:GQ8TrJ9h6ZrNYHItBycWK+tXkURjowfJWcjEyabRIKI)
Stored encrypted; a Kubernetes Secret is made only when a binding asks for it (#532).

Next steps:

  nereus secrets get default/google-oauth
```

### create-exists

Create it again.

```bash
nereus secrets create google-oauth \
  --from-env GOOGLE_CLIENT_ID
```

``` { .text .output title="output" }
✗ secrets/vaults/default/secrets/google-oauth already exists. To change it, write it as a file, then apply the file:
  nereus secrets create google-oauth --from-env GOOGLE_CLIENT_ID --dry-run --output yaml > google-oauth.yaml
  nereus secrets apply --from-file google-oauth.yaml
```

### create-file

A private key from a file, and an id from the environment.

```bash
nereus secrets create github-app \
  --vault default \
  --from-file private-key=key.pem \
  --from-env APP_ID
```

``` { .text .output title="output" }
✓ secrets/vaults/default/secrets/github-app created (key SHA256:GQ8TrJ9h6ZrNYHItBycWK+tXkURjowfJWcjEyabRIKI)
Stored encrypted; a Kubernetes Secret is made only when a binding asks for it (#532).

Next steps:

  nereus secrets get default/github-app
```

### apply

Apply the folder.

```bash
nereus secrets apply \
  --from-file secrets
```

``` { .text .output title="output" }
✓ secrets/vaults/default/secrets/github-app configured
✓ secrets/vaults/default/secrets/google-oauth configured

Next steps:

  nereus secrets list
```

### list

Every secret.

```bash
nereus secrets list
```

``` { .text .output title="output" }
VAULT    NAME          KEYS                  STATUS  AGE
default  github-app    APP_ID, +1            Ready   4s
default  google-oauth  GOOGLE_CLIENT_ID, +1  Ready   5s
```

### get

One secret.

```bash
nereus secrets get default/google-oauth
```

``` { .text .output title="output" }
Vault     default
Name      google-oauth
Keys      GOOGLE_CLIENT_ID
          GOOGLE_CLIENT_SECRET
Version   2
Location  openbao: secret/nereus/default/google-oauth
Bindings  -
Status    Ready
Age       10s
```

### get-yaml

The object, without its values.

```bash
nereus secrets get google-oauth \
  --output yaml
```

``` { .text .output title="output" }
apiVersion: secrets.getnereus.dev/v1alpha1
kind: Secret
metadata:
  name: default.google-oauth
  namespace: nereus-system
spec:
  vault: default
  keys:
  - GOOGLE_CLIENT_ID
  - GOOGLE_CLIENT_SECRET
status:
  location: 'openbao: secret/nereus/default/google-oauth'
  mandate: default
  nereid: openbao
  phase: Ready
  version: '2'
```

### vault-list

Every vault.

```bash
nereus secrets vault list
```

``` { .text .output title="output" }
NAME     NEREID   NAMESPACES     SECRETS  STATUS  AGE
default  openbao  nereus-system  2        Ready   4m
```

### vault-create

A vault the identity and tools namespaces may bind.

```bash
nereus secrets vault create team-a \
  --allow-namespace identity \
  --allow-namespace tools
```

``` { .text .output title="output" }
✓ secrets/vaults/team-a created

Next steps:

  nereus secrets create <secret> --vault team-a --from-env <VAR>
```

### vault-delete-held

The vault default still holds two secrets.

```bash
nereus secrets vault delete default
```

``` { .text .output title="output" }
✗ secrets/vaults/default holds secrets github-app, google-oauth. Delete them first:
  nereus secrets delete default/github-app
  nereus secrets delete default/google-oauth
```

### delete

By vault and name.

```bash
nereus secrets delete default/google-oauth
```

``` { .text .output title="output" }
✓ secrets/vaults/default/secrets/google-oauth deleted

Next steps:

  nereus secrets list
```

### vault-delete

Delete the vault team-a.

```bash
nereus secrets vault delete team-a
```

``` { .text .output title="output" }
✓ secrets/vaults/team-a deleted

Next steps:

  nereus secrets vault list
```

### binding-create

Keycloak, in the namespace identity, reads the Google client under its own key names.

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

### binding-refused

The vault default does not allow the namespace payments.

```bash
nereus secrets binding create payments \
  --secret default/google-oauth \
  --namespace payments
```

``` { .text .output title="output" }
✗ secrets/vaults/default does not allow namespace payments (it allows: nereus-system, identity, tools).
  Allow it: write the vault as a file, add payments to spec.allowedNamespaces, then apply the file:
  nereus secrets vault get default --output yaml > default.yaml
  nereus secrets vault apply --from-file default.yaml
```

### binding-chart

The template of test/charts/binding-demo.

```bash
cat test/charts/binding-demo/templates/secretbinding.yaml
```

``` { .text .output title="output" }
apiVersion: {{ .Values.apiGroup }}/v1alpha1
kind: SecretBinding
metadata:
  name: {{ .Release.Name }}
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "binding-demo.labels" . | nindent 4 }}
spec:
  secret: {{ required "secret is <vault>/<secret>" .Values.secret | quote }}
```

### binding-list

In every namespace.

```bash
nereus secrets binding list
```

``` { .text .output title="output" }
NAME             SECRET                NAMESPACE  FOR                 STATUS  AGE
keycloak-google  default/google-oauth  identity   system:admin        Ready   12s
binding-demo     default/google-oauth  tools      chart binding-demo  Ready   4s
```

### binding-used

The secret lists its bindings.

```bash
nereus secrets get default/google-oauth
```

``` { .text .output title="output" }
Vault     default
Name      google-oauth
Keys      GOOGLE_CLIENT_ID
          GOOGLE_CLIENT_SECRET
Version   2
Location  openbao: secret/nereus/default/google-oauth
Bindings  identity/keycloak-google  by system:admin        Ready
          tools/binding-demo        by chart binding-demo  Ready
Status    Ready
Age       30s
```

### binding-delete

The binding keycloak-google.

```bash
nereus secrets binding delete keycloak-google \
  --namespace identity
```

``` { .text .output title="output" }
✓ secrets/vaults/default/secrets/google-oauth/secretbindings/identity/keycloak-google deleted

Next steps:

  nereus secrets binding list --namespace identity
```
