# 0008. Portal: the first slice, a PWA that says who you are

**Status:** Proposed (2026-10-31)

From the owner's session of 2026-10-31 (refining #46, the web portal, with a clickable prototype on the phone). Raw data in the session's Pontos log.

## Intent

The walking skeleton of the portal (#46): open `https://portal.getnereus.dev` on the phone, install it on the home screen, sign in with Google, see who is signed in, sign out, and sign in again. Nothing else. Every later screen (Reefs, Nereids, commands as forms, push for #278) grows on top of this slice.

The portal is installed the way every capability is: a Reef, `portal`, and a Nereid that implements it, `nereus-portal`, applied from the CLI. Without it the platform works from the CLI alone; with it, the platform gains a graphical client (#46, the owner's comment: the portal itself is swappable).

## The scene that ends the slice

```bash
# Apply the portal reef (with no kinds of its own, as authentication)
nereus reef apply portal

# Install its Nereid, published at the portal's public address
nereus nereid apply nereus-portal \
  --reef portal

nereus mandate apply nereus-portal \
  --reef portal \
  --nereid nereus-portal \
  --param publicUrl=https://portal.getnereus.dev

# The portal answers, and so does the API behind it
curl https://portal.getnereus.dev/healthz
curl --include https://portal.getnereus.dev/v1/me
```

```text
ok
HTTP/2 401
```

Then, on the phone:

1. Open `https://portal.getnereus.dev`: the start screen ("Entre com a sua conta para continuar.", **Entrar**). The browser offers "Add to Home screen"; the icon is the honeycomb, the name Nereus.
2. **Entrar** goes to the realm's login (`auth.getnereus.dev`, always dark), where **Entrar com Google** signs in.
3. Back on the portal: name, e-mail, groups, "entrou com Google · auth.getnereus.dev", and **Sair**.
4. **Sair** ends the session in the portal and in Keycloak, and shows "Você saiu" with **Entrar de novo**, which shows the login again (not a silent return).

Steps 1 to 4 also work from the installed app, opened from the home screen.

## The screens

The reference is the canvas of the session (dark and light rows, and a clickable prototype): the start screen, the login, the signed-in screen, the signed-out screen. In words:

- **The mark appears once per screen:** the honeycomb with "Nereus" beside it. No title repeats the name (the same change made the login card say only "Entrar", #734, the login page says Nereus twice).
- **Theme follows the device** (`prefers-color-scheme`), with no switch in this slice. Dark: the login theme's palette (#598: page `#000`, card `#0c0c0c`, lines `#262626`, text `#f5f5f5`, primary button white on black). Light: its mirror (page `#fafafa`, card `#fff`, lines `#e5e5e5`, text `#0a0a0a`, primary button black on white).
- **The login stays dark** in both themes: it is Keycloak's theme (#598), out of this slice.
- **Languages:** pt-BR and en, from the browser's language, the login's texts style (no gendered words).
- **Touch targets** of at least 44 px; text contrast of at least 4.5:1.

## The `portal` Reef

`portal.getnereus.dev/v1alpha1`, the capability of a graphical client of the platform. In this slice it has **no kinds of its own**: the Mandate's parameters carry what the Nereid needs (`publicUrl`, and `gateway`, the `<namespace>/<name>` of the Gateway its route attaches to, `istio-system/ingress` by default). `nereus reef apply portal` takes no flag: a Reef the CLI pins no contract for is created with no kinds, as `authentication` is. A kind comes when the portal has state of its own (a theme, a menu); [Open questions](#open-questions).

It requires the `authentication` Reef (its login), and reaches the Nereus API (ADR 0018, the API is the one door) for everything it shows.

## The `nereus-portal` Nereid

One image, `nereus-portal-controller`, under `controllers/nereus-portal/`, the shape of the other local Nereids (`server.py`, `/contract`, a `Dockerfile`, tests), listed in `NEREIDS` (`Makefile`) and `TOOLS` (`cli/src/nereus/local_nereids.py`), so `make nereids` builds it and `nereus nereid apply nereus-portal` needs no `--image`.

- **It serves the portal's files:** a static single-page app, no build step, no framework: `index.html`, one script, one stylesheet, the web app manifest, the service worker and the icons. A small app with no build keeps the slice cheap; a framework comes when a screen needs one.
- **It forwards `/v1/*` to the Nereus API** (`http://nereus-api.nereus-system.svc:8080`), on the same origin, so the browser needs no CORS and the API no public hostname of its own. The forward adds nothing and decides nothing: the API checks the token on every request. It is not a backend of the portal (#46: the portal must not grow one the API later replaces).
- **It serves `/config.json`**, from the Mandates: the issuer (the authentication Reef's default Mandate's `status.oidc`), the client id (`nereus-portal`, a constant on both sides while the client is a stand-in) and its own Mandate's `publicUrl`. The page reads it at start, so no address is baked into the files.
- **Its Content Security Policy is built from the same issuer**, so `connect-src` names `https://auth.getnereus.dev` on the kept cluster and the Environment's own issuer elsewhere.
- **`/healthz`** answers `ok`.

## Login

- **Authorization Code with PKCE (S256)**, a public client, through [oidc-client-ts](https://github.com/authts/oidc-client-ts) (Apache-2.0), vendored as one file (open source first).
- **The client `nereus-portal`** in the realm `nereus`: public, standard flow only, redirect `https://portal.getnereus.dev/callback`, post-logout redirect `https://portal.getnereus.dev/signed-out`, web origin `https://portal.getnereus.dev`, the `nereus-api` audience and the `groups` claim (as `nereus-cli` has them).
- **Who registers it:** the keycloak Nereid, beside `nereus-cli`, `claude` and `triton`. It reads the `publicUrl` of every Mandate of the `portal` Reef (every Nereid may read Mandates) and sets the client's redirects from them, so nobody repeats the portal's address on the keycloak Mandate (`mandate apply` replaces a Mandate's whole spec, and would drop the Google parameters). With no portal Mandate, the client exists with no redirect. This is a stand-in: a Reef asking the authentication Reef for a client of its own is the feature that retires it (#535, the authentication Reef's `Client` kind).
- **Tokens live in memory** only, never in `localStorage`. Reopening the app finds no token and goes through the login again by itself, a redirect with `prompt=none` that shows nothing (#1256): while Keycloak's session lasts it returns at once to the signed-in screen, else Keycloak answers `login_required` and the start screen shows **Entrar**, with no error line. One attempt per tab (a `sessionStorage` flag, cleared by a login that works), never on `/signed-out`, never offline. A hidden iframe (`signinSilent`) was turned down: it needs Keycloak's cookie as a third-party cookie, which Safari and Chrome's tracking protection block. While signed in, the access token is renewed with the refresh token (#1758): a minute before it expires, and at once when the API answers 401, then the call is sent again once; one renew at a time, since Keycloak rotates refresh tokens. `signinSilent` uses the refresh token here, never the iframe.
- **Sign out** is the RP-initiated logout of OpenID Connect: the end-session endpoint with `id_token_hint` and the post-logout redirect, so the next **Entrar** shows the login for real.

## What `GET /v1/me` answers

The signed-in screen shows the name and how the person signed in, so the API grows two fields (owner, 2026-10-31), both read from the token it already checks:

```json
{"sub": "…", "email": "maria@example.com", "name": "Maria Silva", "groups": ["nereus-users"], "identityProvider": "google"}
```

- `name` from the `name` claim (Keycloak's `profile` scope).
- `identityProvider` from an `identity_provider` claim, which the keycloak Nereid adds to the clients `nereus-portal` and `nereus-cli` with a *User Session Note* mapper of the session note Keycloak sets on a brokered login (`identity_provider`). A login with a local user has no such note: the field is absent, and the screen shows only the issuer's host.
- `nereus whoami` keeps its output; showing the provider there is a later choice.

## The PWA

- A **web app manifest**: name and short name "Nereus", the honeycomb icons (192, 512 and maskable), `display: standalone`, theme and background colours of the dark palette, `start_url: /`.
- A **service worker** that caches only the app's shell (the static files), never `/v1/*`, `/config.json` or the login. It is what the browsers ask for before offering to install; offline use and Web Push are out of this slice (#278).
- **iOS:** the `apple-touch-icon` and `apple-mobile-web-app-*` tags. The login leaves the app for `auth.getnereus.dev` and must come back to it: the slice proves this on the owner's iPhone or Android, and if the return opens in the browser instead, that is recorded on the issue before widening.

## Reaching the internet

The Nereid publishes `portal.getnereus.dev` with a Gateway API `HTTPRoute` on the entrance's `Gateway` (#727, #728), to the portal's own port (8081), so its controller endpoints (port 8080, `/contract`, `/metrics`) stay inside the cluster. The named Cloudflare tunnel (`deploy/edge/cloudflared.yaml`) lists each hostname it sends to the gateway, `portal.getnereus.dev` among them (#732); the owner runs one DNS route once (`cloudflared tunnel route dns nereus portal.getnereus.dev`). The DNS route by hand is a stand-in for the edge Reef (#470), which retires it.

## Security (OWASP)

- **A01 Broken Access Control:** the portal shows only what `GET /v1/me` answers for the token; the forward passes the `Authorization` header unchanged and nothing else.
- **A02 Cryptographic Failures:** HTTPS only (Cloudflare's edge); tokens never stored by the page.
- **A05 Security Misconfiguration:** a strict Content Security Policy (`default-src 'self'`, `connect-src 'self' https://auth.getnereus.dev`, `frame-ancestors 'none'`), `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`.
- **A07 Identification and Authentication Failures:** PKCE S256, exact redirect URIs, `state` and `nonce` checked by the library, the logout ending the Keycloak session.
- **A08 Software and Data Integrity Failures:** the vendored library pinned by version and hash, served from the portal itself (no CDN).

## From zero

The owner's direction (2026-10-31): a fresh Nereus, in a new Environment (today a vcluster inside the k3d cluster, #568), must be able to stand the portal up with Nereus's own commands, from nothing. So:

- **Everything the portal needs is a command of the scene above**, run against a cluster with only `nereus init` and the authentication Reef: no file edited by hand, no `kubectl apply` of the portal's own manifests.
- **What still needs a hand is listed** as a stand-in below, with the feature that retires it: today the client in the realm (decided by the keycloak Nereid's code) and the public hostname (the tunnel). An Environment reaches the portal through its own entrance, never a port-forward (owner, 2026-10-31): a port of the k3d load balancer, opened when the cluster is created, to an ingress gateway (Istio's, once an Environment installs the mesh) that routes by hostname to the portal. The portal then publishes its route as a Gateway API `HTTPRoute`, which Istio and other gateways implement alike, so the portal never names the gateway. The entrance comes first (owner, 2026-10-31): #727 installs Istio's ingress gateway through the release Reef behind a k3d port, and #728 sends `auth.` and `triton.` through it; the portal then only adds its `HTTPRoute`.
- The review of everything else a fresh instance needs is its own issue (#726, Nereus from zero, with #24, #61 and #568).

## Stand-ins

- The client `nereus-portal` registered by the keycloak Nereid; retired by a Reef asking for its own client (#535).
- The DNS route by hand; retired by the edge Reef (#470).

## Delivered by

#729 (the slice, part of #46), in three sub-issues: #730 (`GET /v1/me` answers `name` and `identityProvider`), #731 (the keycloak Nereid registers `nereus-portal`), #732 (the Reef and the Nereid). Depends on #727 (the entrance).

## Done when

- `make lint test deck-test docs-build shellcheck` passes, with tests for the Nereid (files served, `/config.json` from the Mandates, the `/v1` forward, the headers) and for the keycloak Nereid's new client.
- On the kept cluster, the scene above prints what it shows, and on the owner's phone steps 1 to 4 work in the browser and from the installed app, in the dark and the light theme.
- The portal Reef's deck (`docs/specs/cli/reefs/portal.yaml`) has every command above; `README.md` has the Nereid's row; `docs/features.md` lists the two stand-ins.

## Open questions

- **Kinds of the `portal` Reef:** none in this slice; whether a `Portal` kind (hostname, theme) comes next, or the Mandate keeps carrying it.
- **The Nereid's name:** `nereus-portal` (our own portal), leaving room for a `backstage` Nereid of the same Reef.

## What is left to other issues

Push notifications (#278), the Reefs' and Nereids' screens and commands as forms (#46), a light login theme, a theme switch, offline use, a public `api.getnereus.dev`.

## Learn more

- [Progressive Web Apps](https://web.dev/explore/progressive-web-apps) (web.dev): the manifest, the service worker and installability.
- [OAuth 2.0 for Browser-Based Applications](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-browser-based-apps) (IETF draft): Authorization Code with PKCE for a public client, tokens kept out of storage.
- [OpenID Connect RP-Initiated Logout 1.0](https://openid.net/specs/openid-connect-rpinitiated-1_0.html): the sign-out.
- [oidc-client-ts](https://github.com/authts/oidc-client-ts): the library the page uses.
- Walking skeleton (Alistair Cockburn, *Crystal Clear*): the thinnest slice that runs end to end.
