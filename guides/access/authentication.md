# Turn on authentication

Turn on sign-in for an installation: the authentication Reef and its Nereid `keycloak` run the realm `nereus`, and every person logs in with `nereus login`, never with a kubeconfig.

## Before you start

- A cluster from [Prepare the cluster](../../start/init.md). With `--profile internal-developer-platform` the Reef and the Nereid are already there, and step 1 reports `unchanged`.
- After a plain `nereus init`, Nereids for the secrets and release Reefs, the release one with a default Mandate: Keycloak runs as a Release.
- [Tenancy and access](../../concepts/tenancy-and-access.md) explains who the initial admin is and what `nereus-admins` can do.

## Steps

### 1. Install the Reef and its Nereid

[`nereus reef apply`](../../specs/cli/core.html#reef-apply) adds the Reef; [`nereus nereid apply`](../../specs/cli/core.html#nereid-apply) runs Keycloak and makes the default Mandate `keycloak`.

```bash
nereus reef apply authentication
```

``` { .text .output title="output" }
✓ core/reefs/authentication 0.1.0 created (authentication.getnereus.dev/v1alpha1: tokens)

Next steps:

  nereus authentication --help
  nereus nereid apply <nereid> --reef authentication
```

```bash
nereus nereid apply keycloak \
  --reef authentication
```

``` { .text .output title="output" }
✓ core/nereids/keycloak created, Ready, pinned to sha256:e8731e3fb833: see 'nereus authentication --help'
  release/releases/keycloak created by core/nereids/keycloak, Ready (codecentric/keycloakx 7.0.1 in namespace nereus-system)
  core/mandates/keycloak created (reef: authentication, nereid: keycloak, default)
  issuer  http://localhost:8180/realms/nereus (dev mode, kept in the Database keycloak)
  client  claude (public, PKCE S256, redirect https://claude.ai/api/mcp/auth_callback)
  user    nereus (password: kubectl --namespace nereus-system get secret keycloak-user --output jsonpath='{.data.password}' | base64 --decode)

Next steps:

  kubectl --namespace nereus-system port-forward service/keycloak-server-http 8180:8180
```

Until its Release is Ready the Nereid reports `WaitingForRelease`; with no default release Mandate it reports `NoReleaseNereid`. On a cluster with an ingress address the realm is served at `http://auth.localhost:8080` and needs no port-forward.

### 2. Log in as the initial admin

The realm's user `nereus` is the instance's initial admin, in `nereus-admins`. [`nereus login --initial-admin`](../../specs/cli/reefs/authentication.html#login-initial-admin) reads its generated password with your kubeconfig and copies it to the clipboard, never printed. Paste it on the login page.

```bash
nereus login --initial-admin
```

``` { .text .output title="output" }
The initial admin's password is in your clipboard (user nereus). Paste it on the login page.
Opening http://auth.localhost:8080/realms/nereus/protocol/openid-connect/auth?... in the browser.
logged in as nereus (nereus-admins), issuer http://auth.localhost:8080/realms/nereus
```

### 3. Give the realm a public host

[`nereus mandate apply`](../../specs/cli/core.html#mandate-apply) replaces every param, so name them all. The API trusts one issuer at a time: after the change every person runs `nereus login` again.

```bash
nereus mandate apply keycloak \
  --reef authentication \
  --nereid keycloak \
  --default \
  --param publicUrl=https://auth.example.com
```

### 4. Log in from another machine

[`nereus login`](../../specs/cli/reefs/authentication.html#login) with the instance's address asks the instance for its identity provider, so no kubeconfig is needed. The address is kept for the next commands.

```bash
KUBECONFIG=/nonexistent nereus login https://nereus.example.com
```

``` { .text .output title="output" }
Opening https://auth.example.com/realms/nereus/protocol/openid-connect/auth?... in the browser.
instance https://nereus.example.com saved in ~/.config/nereus/config.yaml
logged in as ana-silva (nereus-users), issuer https://auth.example.com/realms/nereus
```

On a machine with no browser, add `--use-device-code` and type the code on another device.

## Check it worked

[`nereus whoami`](../../specs/cli/reefs/authentication.html#whoami) asks the Nereus API who you are.

```bash
nereus whoami
```

``` { .text .output title="output" }
ana-silva (nereus-admins, nereus-users)
```

[`nereus status`](../../specs/cli/core.html#status) now reads through the API with your token, and lists the Reef:

```bash
nereus status
```

``` { .text .output title="output" }
REEF            NEREID      VERSION  STATUS  AGE
authentication  keycloak    0.1.0    Ready   2m
core            nereus-api  0.1.0    Ready   4m
                thetis      0.1.0    Ready   4m
release         flux        0.1.0    Ready   3m
secrets         openbao     0.1.0    Ready   4m
tenancy         -           -        Ready   4m

Registry  localhost:5111
```

## Next

- [Grant access](grant-access.md) to the people of your team.

## Learn more

- [The authentication Reef](../../reference/reefs/authentication.md): every command, and the realm's clients.
- [ADR 0006](../../adr/0006-authentication-reef.md): the OIDC contract the default Mandate publishes.
