# 0006. Authentication is a reef: the person signs in through OIDC, the platform proves itself through a Mandate, and the User belongs to core

!!! note "In short"
    `authentication` is a reef: logins are always OIDC, the platform proves itself outwards through a Mandate per identity, and the User belongs to core. Status: Proposed (2026-10-17, rewritten 2026-10-25, 2026-11-09 and 2026-11-12, amended 2026-11-15).

**Status:** Proposed (2026-10-17, rewritten 2026-10-25, 2026-11-09 and 2026-11-12, amended 2026-11-15)

## Context

The first swap to prove is authentication: the same login and the same API working with Keycloak or with Auth0, side by side or one after the other, without losing anything (ownership, credentials, teams, authorship). Two things get in the way when a platform relies on one identity provider: the person is identified by the provider's `sub`, which changes with the provider, and teams are groups inside the provider.

The platform needs an identity too, towards the systems it acts on: a GitHub App to read a private repository (#927, the catalog Nereid's `SourceUnreachable` of #904), to clone one for a build (#1070) or to publish a package (#1250). #234 (the platform's own identity towards external systems) asked where it sits in the model. The first version of ADR 0024 (the scm reef) put the App in the scm reef; the owner moved it here on 2026-11-09, since a token for ghcr.io is not a source host's concern.

## Decision

**`authentication` is a reef**, API group `authentication.getnereus.dev/v1alpha1` (ADR 0009). It answers two questions: who the person is (inwards, OIDC), and who the platform is towards an external system (outwards, a Mandate per identity).

**The contract of a login is always OIDC.** The API and the CLI only speak OIDC: a bearer token the API validates against a JWKS, plus authorization code with PKCE, device code and refresh for the CLI. Each authentication Nereid that serves login publishes in `status`: `issuer`, `jwksUrl`, `audience`, `cliClientId`, `authorizeParams` and `emailClaim`. The contract binds only those Nereids (owner, 2026-11-10): one that publishes no `status.oidc`, as `github`, serves `Token` only and never takes part in a login.

The first one, the local `keycloak` Nereid (#407), writes them in its Mandate's `status.oidc`: `issuer`, `jwksUrl`, `audience` (`nereus-mcp`), `clientId` (`claude`, the claude.ai connector's public client, with PKCE S256), `cliClientId` (`nereus-cli`, the public client of `nereus login`, #605: PKCE S256 on a loopback callback, or the device flow), `authorizeParams`, `emailClaim`, and `storage: memory` while Keycloak runs in dev mode.

Two optional fields name the client a coding agent logs in to `/mcp` with (#1880): `mcpClientId` (`claude-code`, PKCE S256, `aud: nereus-mcp`) and `mcpCallbackPort` (`33418`), the one loopback port its redirect `http://localhost:<port>/callback` allows. The Nereus API publishes them at `/.well-known/nereus-configuration` beside `cliClientId`, and `nereus mcp client add claude-code` passes them to `claude mcp add`; a Nereid that leaves them out serves no coding agent.

**The protocol with the person's origin belongs to the Nereid.** Google, a corporate SAML IdP or GitHub are sources the Nereid brokers: a SAML IdP is an identity provider in a Keycloak realm or an enterprise connection in Auth0. There is no "SAML Nereid"; a lighter broker (Dex) would be another Nereid that still issues OIDC.

**Several Nereids at once, one default** (owner, 2026-11-10, #1311). The reef takes keycloak, auth0, an Entra ID one and github side by side. Each Mandate binds the reef to one Nereid with its parameters, and a request picks its Mandate by ADR 0017's selection rule (the Nereids that serve the request, then `match` on the nearest `owner`, then the default, then the only one). The credentials a Nereid needs are secrets, named in a parameter (`credentials=secret:google-sso`):

```bash
# The default Mandate: the platform's login
nereus nereid apply keycloak --reef authentication
nereus mandate create corporate \
  --reef authentication \
  --nereid keycloak \
  --param identityProvider=google \
  --param credentials=secret:google-sso \
  --default

# An Organization overrides it with another Nereid, for itself and its Projects
nereus nereid apply auth0 --reef authentication
nereus mandate create acme-auth0 \
  --reef authentication \
  --nereid auth0 \
  --match owner=organization/acme
```

- **The default Mandate** is the platform's login.
- **An Organization overrides it** with a Mandate whose `match` names it; the Mandate covers its Projects.
- **A Project, or several, may pick another Mandate** to compare two Nereids side by side (the comparator, #1316). The tenancy has no Team kind: "a team" is a `match` on its Projects (ADR 0015).
- **The e-mail domain is not a Mandate parameter:** the `matchEmailDomain` of the first versions is gone, and a domain belongs to an Organization (below).

**Identifier-first login, by e-mail domain only** (owner, 2026-11-10). The domain of the address points to the Organization that verified it (its `domains`, ADR 0015), and the Organization to its Mandate by `match`; a domain no Organization verified gets the default. Never per person: telling, before any password, whether an address exists or where it sits is user enumeration (OWASP A07). The address goes to the Nereid's issuer as OIDC's `login_hint`.

**`nereus login` asks nothing** (owner, 2026-11-10):

```bash
# The default Mandate, or the one used last
nereus login

# The Mandate of the address's domain; the address goes on as login_hint
nereus login --email maria@example.com

# One Mandate, by name
nereus login --mandate acme-auth0
```

**The API accepts the token of any Ready login Mandate, told apart by `iss`** (owner, 2026-11-10). The API reads the token's `iss`, finds the Mandate whose `status.oidc.issuer` equals it, and validates the token against that Mandate's `jwksUrl` and `audience`; any other issuer is refused.

- **An Organization may require its own Mandate** (`requireMandate: true`, ADR 0015): an e-mail of its verified domains then enters only with a token of the Mandate that matches the Organization ("enforce SSO").
- **Never per resource owner:** a person who works in two Projects with two Nereids keeps working with one token.

**A machine is the one exception to OIDC** (owner, 2026-11-14): a `Machine` of core signs in with a key pair it made itself, and the Nereus API checks its assertion against the public key, with no login Nereid involved, so it holds the same on every installation. [The metrics intake ADR](0025-metrics-intake.md) holds the details.

**The person is a `User` of core, not a `sub`, and no authentication Nereid owns it.** `User` is a kind of `core.getnereus.dev/v1alpha1` (ADR 0009), like `Reef`, `Nereid` and `Mandate`: the person exists in the platform before, and independently of, any authentication Nereid. The platform generates the User's id. An authentication Nereid only links an external identity (its issuer and the token's `sub`) to a User; it never creates, keys or deletes the User, and the User is not keyed by a Nereid's name (the API never names a Nereid):

```yaml
apiVersion: core.getnereus.dev/v1alpha1
kind: User
metadata:
  name: u-7f3k2p
spec:
  name: maria
  email: maria@example.com
  identities:
    - {issuer: "http://localhost:8180/realms/nereus", sub: 3f2a9c1e-...}
    - {issuer: "https://example.us.auth0.com/", sub: "google-oauth2|1088..."}
```

The reason: a company changes its authentication tool far more often than its e-mail domain. Moving from Keycloak to Auth0, or to any other tool, must keep every User, and with it what each person owns. Owners, authorship and team members store the User's id, never a `sub`. Teams belong to the platform, not to the identity provider.

The tests sign in with a real Google account through single sign-on (SSO), brokered by the `keycloak` Nereid and then by an Auth0 one: the same User must come out of both.

**A new `sub` is linked only after an e-mail code.** The first login of any `sub` sends a single-use code to the token's verified e-mail, through a notification reef whose Nereid can be a real mail server or a local one that writes the message where only an admin can read it. The code never appears in the API response or on the screen of the person logging in. A `sub` is never linked to an existing User because the e-mail matches: whoever controls an IdP that issues that e-mail would take the account.

**Two stand-ins in the first slice of teams and authorization** (owner, 2026-11-15, ADR 0027, spec 0011), until the notification reef exists:

- **The first identity is linked by the token's verified e-mail.** An administrator creates the User with its e-mail (`nereus user create maria --email maria@example.com`); the first sign-in of a token with `email_verified: true` and that e-mail links its `{issuer, sub}` to the User. It trusts the `email_verified` claim of the instance's own issuer, also when that issuer brokered another identity provider. A token whose e-mail is not verified links nothing, and a second identity on the same User is not linked at all. The e-mail code above replaces it.
- **The User's id is the object's name** (`core/users/maria`), not an id the platform generates; `spec.email` is required and unique, `spec.displayName` optional, and the identities are written only by the Nereus API. A generated id, with the name kept as a field, replaces it.

**The platform's identity towards an external system is a Mandate** (owner, 2026-11-09, #234). A GitHub App is a Mandate of the `github` Nereid: its id and its private key are Mandate parameters, the key a plain secret of the secrets reef, read by the Nereid through a `SecretBinding` (ADR 0023's pattern). There is no `--vendor` and no `Application` kind: the model of ADR 0011 holds, and the CLI never names an implementation (`cli/tests/test_boundaries.py::test_the_cli_never_names_an_implementation`); `github` appears only in `nereid apply` and `mandate create`:

```bash
nereus secrets create github-app-key --from-env GITHUB_APP_KEY
nereus nereid apply github --reef authentication --reef scm
nereus mandate create github \
  --reef authentication \
  --nereid github \
  --param appId=123456 \
  --param privateKey=github-app-key
```

The `github` Mandate sits next to the login ones and is never the default (owner, 2026-11-10): a `Token` picks it as the only Nereid that mints tokens.

- **The App's status is the Mandate's status:** `Ready`, `NotInstalled`, `InvalidCredentials`, `NotRegistered` (neither `appId` nor `privateKey`: no App yet, run `app-register`, #1291) or `MissingParam` (only one of the two), with the App's installations and the permissions granted (`nereus mandate get github`). There is no `verify` command.
- **A second App is a second Mandate,** chosen with `--mandate` wherever a command needs the platform's identity, or by its `match`; with none, ADR 0017's selection rule among the Mandates that mint tokens.
- **The App has one webhook:** its secret is a Mandate parameter (`webhookSecret`), and its URL points at the scm reef's receiver, which checks the signature (ADR 0024).
- **Creating the App from a manifest, in the browser,** is an action of the `github` Nereid (ADR 0010, Nereid actions; ADR 0004, the commands a Nereid publishes), not a flag of `mandate create`; the key goes from GitHub to the Nereid, never through the person's machine. The Nereid answers with the App's id and the key's secret name, and the CLI, as the person's client, writes them to the Mandate's `spec` (owner, 2026-11-09): one shape of Mandate for a new App and an existing one, and ADR 0005 holds (#1275).
- **The App stands for this installation of Nereus towards GitHub, not for an org** (owner, 2026-11-10): `app-register` names it `nereus-<installation>`, after the one Installation of the nereus namespace, without repeating the prefix and within GitHub's 34 characters; `--name` names it when that name is taken, since a name is unique across GitHub (#1291).
- **One `github` Nereid serves the authentication and the scm reefs, opt-in:** the `internal-developer-platform` profile does not install it, since it needs an App the person owns.
- **The same App can broker a person's GitHub login** through the keycloak Nereid (#1282); the person stays a User of core.

**A consumer gets a short-lived credential as a `Token`, the reef's first kind** (owner, 2026-11-09). A person or a Nereid asks it; the Nereid of the Mandate mints an installation token narrowed to one repository and to permissions no wider than the App's, writes it to a Secret in the requester's namespace, and refreshes it before its hour ends while the `Token` exists. A consumer never holds the App's key. The catalog Nereid is the first consumer (#1274); the build (#1070) and the publish copy (#1250) follow.

| Kind | `spec` (the person, or a Nereid as a client) | `status` (the Nereid only) |
|---|---|---|
| `Token` | `repository`, `permissions`, `mandate` (empty: ADR 0017's selection rule) | `observedGeneration`, `conditions`, `mandate`, `secretRef` (namespace and name), `expiresAt` |

```bash
nereus authentication token create catalog \
  --repository example/app \
  --permission contents=read
# ✓ authentication/tokens/catalog created (expires in 1h, mandate github)
```

## Prior art

- OpenID Connect Core 1.0, [Authentication Request](https://openid.net/specs/openid-connect-core-1_0.html#AuthRequest) and [ID Token Validation](https://openid.net/specs/openid-connect-core-1_0.html#IDTokenValidation): `login_hint` is a "hint to the Authorization Server about the login identifier the End-User might use to log in", and the issuer "MUST exactly match the value of the iss (issuer) Claim"; the address of `--email` and the way the API tells one Mandate's token from another's.
- OWASP, [Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html), "Authentication and Error Messages": "an application should respond (both HTTP and HTML) in a generic manner", whether or not the account exists; the reason the discovery looks at the domain, never at the person.
- Slack, [Set up SAML single sign-on for Slack](https://slack.com/help/articles/203772216-SAML-single-sign-on): "choose whether SSO is required for all members, required for all members excluding guests, or optional"; the shape of an Organization's `requireMandate`.
- GitHub, [Generating an installation access token for a GitHub App](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-an-installation-access-token-for-a-github-app): a token that expires after an hour, narrowed to repositories and permissions, the shape of `Token`.
- GitHub, [Registering a GitHub App from a manifest](https://docs.github.com/en/apps/sharing-github-apps/registering-a-github-app-from-a-manifest): the browser flow and the one-time code exchanged for the App's key.
- Flux, [GitRepository](https://fluxcd.io/flux/components/source/gitrepositories/), and Argo CD, [Private repositories](https://argo-cd.readthedocs.io/en/stable/user-guide/private-repositories/): both reach GitHub with a GitHub App's credential held by the controller, never by the person.

## Consequences

- Swapping Keycloak for Auth0 costs each person one login and one code; nothing they own changes hands, since the User stays in core and only gets one more identity.
- The `User` kind joins core next to the kinds of ADR 0014 (profiles: core is only the engine); the issue that builds it decides its exact fields.
- Each authentication Nereid must deliver a verified e-mail in the access token, under the claim it publishes in `emailClaim` (Auth0 needs a post-login Action for this).
- Authorization (who is admin, which teams) is the platform's job, outside the identity provider.
- The github Nereid sits next to keycloak, which unblocks #1282 (keycloak brokers a GitHub login through the App) and #91 (the auth0 Nereid). The order of that work: #1313 (several Nereids per reef and the selection rule), #1314 (the API accepts several issuers, and `requireMandate`), #1315 (identifier-first login by e-mail domain).
- A login by e-mail tells which Nereid an Organization's domain uses, and nothing about a person: the answer is the same for every address of a domain (OWASP A07, user enumeration).
- The authentication reef gains its first kind, `Token`: it leaves `contracts.REEFS_WITHOUT_KINDS` (#794) when #1274 builds it.
- The order of the work: #1273 (the github Nereid's Mandate proves a GitHub App installed), #1274 (the `Token`), #1275 (the App from a manifest); ADR 0024's Connection follows (#1281).
- OWASP A01 (broken access control: one repository per token, a Secret only in the requester's namespace), A02 (cryptographic failures: the App's key sealed on the client, never outside openbao in clear) and A07 (identification and authentication failures: an hour-long token instead of a personal one) are the categories the platform's identity touches.

## Open questions

- The workload identity of each Nereid towards a cloud (federation, no stored secret) stays with spec 0005 for the cloud reef; a system that accepts no federation, as a GitHub App, gets a Mandate of this reef. Whether an Entra ID app registration or a Slack app also becomes a Mandate here waits for its first use.
- **How the Nereid writes a `Token`'s Secret in the requester's namespace.** Recommendation for #1274: a Role on Secrets granted per namespace that asks a `Token`, never a ClusterRole, held by an admission policy to the Secrets the Nereid owns.
- **How a login learns the Project, when a Project has its own Mandate** (the comparator, #1316). A login has no `owner`, and the address's domain leads only to the Organization. Until #1316 decides, `--mandate` is the way.

*Rewritten 2026-10-25 from voice session; raw data in Drive #pontos/raw/2026-10-25.*

*Rewritten 2026-10-26 from order 20261026-0508 (divergence 3 of the idea timeline of 2026-10-25): the User belongs to core, independent of the authentication Nereid; raw data in Drive #pontos/raw/2026-10-25 (voice files 27, 28, 32 and 90).*

*Rewritten 2026-11-09 from the owner's decisions on #927 and #234 (the platform's identity towards an external system is a Mandate of this reef, the `Token` is its kind; #1280); raw data in Drive `#pontos/raw/2026-11-09/`.*

*Rewritten 2026-11-12 from the owner's decisions of 2026-11-10 (#1311: several Nereids at once, login by e-mail domain, the tokens the API accepts); raw data in Drive `#pontos/raw/2026-11-10/` and `#pontos/raw/2026-10-24/0000-voice-07-platform-landscape-api-groups-controllers.md`.*

*Amended 2026-11-15 from the owner's decisions refining #897 into spec 0011 (decision 4: the first identity linked by verified e-mail, the User's name as its id, both stand-ins; ADR 0027); raw data in Drive `#pontos/raw/2026-11-15/`.*
