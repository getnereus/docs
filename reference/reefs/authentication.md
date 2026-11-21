# The authentication reef

Who the person is, and who the platform is towards the systems it acts on.

## Commands

- [`nereus login`](../../specs/cli/reefs/authentication.html#login) The browser opens, and the login comes back to the terminal
- [`nereus login`](../../specs/cli/reefs/authentication.html#login-device) A machine with no browser logs in from another device
- [`nereus login`](../../specs/cli/reefs/authentication.html#login-initial-admin) A new instance has one obvious way in: its initial admin
- [`nereus login`](../../specs/cli/reefs/authentication.html#login-refresh) A new token without the browser, with the groups read again
- [`nereus logout`](../../specs/cli/reefs/authentication.html#logout) Logging out ends the session at the identity provider too
- [`nereus whoami`](../../specs/cli/reefs/authentication.html#whoami) The Nereus API says who you are
- [`nereus authentication app-register`](../../specs/cli/reefs/authentication.html#app-register) With no App yet, the Nereid creates it in the browser
- [`nereus authentication token create catalog`](../../specs/cli/reefs/authentication.html#token-create) A Token lends one repository for an hour
- [`nereus authentication token list`](../../specs/cli/reefs/authentication.html#token-list) list shows each Token, never its value

## Examples

### login

Authorization code with PKCE, on a listener of 127.0.0.1.

```bash
nereus login
```

``` { .text .output title="output" }
Opening https://auth.example.com/realms/nereus/protocol/openid-connect/auth?... in the browser.
logged in as ana-silva (nereus-users), issuer https://auth.example.com/realms/nereus

Next steps:

  nereus whoami
  https://auth.example.com/realms/nereus/account/account-security/signing-in   (set a password, optional)
```

### login-device

The device grant: open the page elsewhere and type the code.

```bash
nereus login \
  --use-device-code
```

``` { .text .output title="output" }
Open https://auth.example.com/realms/nereus/device and enter ABCD-EFGH (expires in 10 minutes).
logged in as ana-silva (nereus-users), issuer https://auth.example.com/realms/nereus

Next steps:

  nereus whoami
  https://auth.example.com/realms/nereus/account/account-security/signing-in   (set a password, optional)
```

### login-initial-admin

The password goes to the clipboard, never to the terminal.

```bash
nereus login \
  --initial-admin
```

``` { .text .output title="output" }
The initial admin's password is in your clipboard (user nereus). Paste it on the login page.
Opening https://auth.example.com/realms/nereus/protocol/openid-connect/auth?... in the browser.
logged in as nereus (nereus-admins), issuer https://auth.example.com/realms/nereus

Next steps:

  nereus whoami
  https://auth.example.com/realms/nereus/account/account-security/signing-in   (set a password, optional)
```

### login-refresh

Renew the session, so a group joined since the last login shows.

```bash
nereus login \
  --refresh
```

``` { .text .output title="output" }
token refreshed for ana-silva, valid until 14:05
```

### logout

Revoke the session, then delete the credentials.

```bash
nereus logout
```

``` { .text .output title="output" }
logged out nereus@example.com: session revoked, ~/.config/nereus/credentials deleted
```

### whoami

GET /v1/me with the token of nereus login.

```bash
nereus whoami
```

``` { .text .output title="output" }
ana-silva (nereus-admins, nereus-users)
```

### app-register

An action the github Nereid publishes under the reef.

```bash
nereus authentication app-register \
  --mandate team \
  --org example-team
```

``` { .text .output title="output" }
→ opening the browser to create the GitHub App "nereus-prod"
✓ secrets/team-app-key stored by the Nereid (the key never reaches this machine)
✓ secrets/team-webhook-secret and secrets/team-oauth-client stored by the Nereid
✓ core/mandates/team configured (appId 900001, privateKey team-app-key, webhookSecret team-webhook-secret)

Next steps:

  Install it on the org: https://github.com/apps/nereus-prod/installations/new
  nereus mandate get team
```

### token-create

A token to read one repository, from the default Mandate.

```bash
nereus authentication token create catalog \
  --repository example/app \
  --permission contents=read
```

``` { .text .output title="output" }
✓ authentication/tokens/catalog created (expires in 1h, mandate github)

Next steps:

  nereus authentication token get catalog
```

### token-list

Every Token.

```bash
nereus authentication token list
```

``` { .text .output title="output" }
TOKEN    REPOSITORY   PERMISSIONS    MANDATE  EXPIRES  STATUS
catalog  example/app  contents=read  github   1h       Ready
```
